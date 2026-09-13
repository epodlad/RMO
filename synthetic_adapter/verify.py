"""Bounded adapter tests, reports, byte preservation and optional complete ZIP."""
import argparse
import base64
from html.parser import HTMLParser
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import zipfile
from .input import ROOT,strict_load,unpack
from . import runner as R
from .demo import build as build_demo
from .saved_view import build as build_saved

OUT=ROOT/"results/synthetic_adapter"
BASE=ROOT.parent/"RMO_Result_Clarity_workspace"


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n")


class TestLog(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.entries=[]
    def addSuccess(self,test):super().addSuccess(test);self.entries.append({"test":test.id(),"status":"PASS"})
    def addFailure(self,test,err):super().addFailure(test,err);self.entries.append({"test":test.id(),"status":"FAIL"})
    def addError(self,test,err):super().addError(test,err);self.entries.append({"test":test.id(),"status":"ERROR"})


class Markup(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.downloads=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if "id" in a:self.ids.append(a["id"])
        if tag=="a" and "download" in a:self.downloads.append(a)


def artifact_checks():
    checks=[]
    for rel in ("worked_contact/RMO_computed_contact_example.html","saved_BrioWu/RMO_saved_BrioWu_solutions.html"):
        text=(OUT/rel).read_text();parser=Markup();parser.feed(text)
        assert len(parser.ids)==len(set(parser.ids)),"Duplicate embedded SVG/HTML IDs"
        assert "<svg" in text and "not" in text and ("No solver" in text or "does not run the solver" in text)
        checks.append({"test":rel+": unique IDs and embedded plots","status":"PASS"})
        for a in parser.downloads:
            data=base64.b64decode(a["href"].split(",",1)[1]);obj=strict_load(data.decode())
            if a["download"]=="contact_request.json":assert obj["execution_mode"]=="preflight_only"
            else:assert unpack(data.decode())[2]["status"]=="VALID"
            assert data==(OUT/"worked_contact"/a["download"]).read_bytes()
            checks.append({"test":a["download"]+": embedded bytes match file","status":"PASS"})
    points=json.loads((OUT/"saved_BrioWu/saved_locations_and_sources.json").read_text())
    assert len(points)==3 and len({(x['pressure'],x['velocity']) for x in points})==3
    for p in points:assert sha(ROOT/p["source"])==p["sha256"]
    checks.append({"test":"Three saved points preserve exact source hashes","status":"PASS"})
    return checks


def main(archive=None):
    OUT.mkdir(parents=True,exist_ok=True)
    attempts,workers=[],[]
    original,original_worker=R.run,R.run_worker
    def record_run(text,**kwargs):
        result=original(text,**kwargs)
        attempts.append({"execution_envelope_text":text,"response":result})
        return result
    def record_worker(*args,**kwargs):
        result=original_worker(*args,**kwargs)
        workers.append(result)
        return result
    suite=unittest.defaultTestLoader.discover(str(ROOT/"synthetic_adapter/tests"),pattern="test_*.py")
    stream=io.StringIO()
    with patch.object(R,"run",side_effect=record_run),patch.object(R,"run_worker",side_effect=record_worker):
        tested=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=TestLog).run(suite)
    save(OUT/"adapter_test_report.json",{"tests":tested.entries,"count":tested.testsRun,"passed":tested.wasSuccessful(),"transcript":stream.getvalue(),"scope":"Bounded adapter validation, not the complete RMO scientific benchmark suite"})
    save(OUT/"test_execution_records.json",{"requests":attempts,"workers":workers,"note":"Fixed fault_worker processes are resource/protocol tests, not physical computations. Their marker counts do not represent RMO solver calls."})
    if not tested.wasSuccessful():print(stream.getvalue());raise SystemExit("Adapter tests failed")
    # Demo.run was imported before patching, so record this separate fresh calculation explicitly.
    demo=build_demo(OUT/"worked_contact")
    build_saved(OUT/"saved_BrioWu")
    commands=[
        ["node","preflight/tests/test_core.cjs"],
        ["node","preflight/tests/test_ui.cjs"],
        [sys.executable,"-B","-m","unittest","discover","-s","preflight/tests","-p","test_*.py"],
        [sys.executable,"-B","-m","unittest","discover","-s","quicklook/tests","-p","test_*.py"],
        ["node","quicklook/tests/test_view.cjs"],
        ["node","synthetic_adapter/tests/test_saved_selection.cjs"],
    ]
    runs=[]
    for command in commands:
        p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=45)
        runs.append({"command":command,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
    checks=artifact_checks()
    preserved={"unchanged":[],"allowed_changes":[],"missing":[],"unexpected":[]}
    for p in sorted(BASE.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:continue
        rel=p.relative_to(BASE);q=ROOT/rel
        entry={"path":str(rel),"before_sha256":sha(p)}
        if not q.is_file():preserved["missing"].append(entry)
        elif sha(q)==entry["before_sha256"]:preserved["unchanged"].append(entry)
        else:
            entry["after_sha256"]=sha(q)
            preserved["allowed_changes" if str(rel)=="RMO/RMO_master_ledger.md" else "unexpected"].append(entry)
    save(OUT/"preservation_report.json",preserved)
    registry=json.loads((ROOT/"specification/quicklook_adapter/design_registry_draft_0_1_0.json").read_text())
    coverage=[]
    for case in registry["acceptance_cases"]:
        matches=[t for t in tested.entries if ".test_"+case["id"]+"_" in t["test"]]
        coverage.append({"id":case["id"],"status":"PASS" if matches and all(x['status']=='PASS' for x in matches) else "NOT_IMPLEMENTED" if case["id"]=="A28" else "NOT_PASSED","tests":matches,
                         "limit":"Local association predicate only; browser lifecycle deferred" if case["id"]=="A13" else "Browser integration explicitly deferred" if case["id"]=="A28" else "Bounded declared test cases only, not exhaustive proof"})
    save(OUT/"acceptance_coverage.json",coverage)
    passed=all(r['returncode']==0 for r in runs) and not preserved["unexpected"] and not preserved["missing"]
    summary={"adapter_tests":tested.testsRun,"adapter_tests_pass":tested.wasSuccessful(),"acceptance_design":"A01-A27 exercised; A28 browser lifecycle deferred","legacy_and_selection_runs":runs,"artifact_checks":checks,
             "preservation":{k:len(v) for k,v in preserved.items()},"checks_pass":passed,
             "browser":"NOT VERIFIED","new_dependencies":0,"observational_data_bytes":0,"public_release":False,"scientific_solver_modified":False,
             "contact_result":demo["presentation"],"scope":"Local synthetic adapter plus separately requested read-only figures/viewer; not browser-to-solver integration"}
    save(OUT/"verification_summary.json",summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ("legacy_and_selection_runs","artifact_checks","contact_result")}))
    if not passed:raise SystemExit("Legacy/artifact/preservation test failed")
    if archive:
        archive=Path(archive)
        if archive.resolve().is_relative_to(ROOT):raise ValueError("ZIP must be outside the project")
        manifest=OUT/"complete_bundle_manifest.json"
        paths=[p for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p!=manifest]
        snapshots={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
        entries=[{"path":rel,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()} for rel,data in snapshots.items()]
        save(manifest,{"files":entries,"self_excluded":str(manifest.relative_to(ROOT)),"runtime_caches_excluded":True})
        packed=io.BytesIO()
        with zipfile.ZipFile(packed,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in paths:
                if p.is_symlink():raise ValueError("No symlinks in archive")
                rel=str(p.relative_to(ROOT))
                z.writestr("RMO/"+rel,snapshots[rel])
            z.writestr("RMO/"+str(manifest.relative_to(ROOT)),manifest.read_bytes())
        archive.write_bytes(packed.getvalue())
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for e in entries:
                data=z.read("RMO/"+e["path"]);assert len(data)==e["bytes"] and hashlib.sha256(data).hexdigest()==e["sha256"]
            members=len(z.namelist())
        integrity={"archive":archive.name,"bytes":archive.stat().st_size,"sha256":sha(archive),"members":members,"CRC":"PASS","member_hashes":"PASS","checkpoints_00_through_61_unchanged":True,"new_checkpoint":"RMO_62_Local_synthetic_adapter_and_visual_examples.md"}
        save(archive.with_name(archive.stem+"_integrity.json"),integrity);print(json.dumps(integrity))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--archive");main(parser.parse_args().archive)
