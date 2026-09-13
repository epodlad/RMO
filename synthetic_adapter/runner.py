"""No network service. Explicit local invocation only; strict request/result association."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from . import VERSION
from .checks import check_packet
from .input import CONTRACT, PROFILE, ROOT, OUTPUT_LIMIT, encode, unpack, eligibility, strict_load

WORKER = ROOT/"synthetic_adapter/worker.py"


def utc(): return datetime.now(timezone.utc).isoformat()


def source_records():
    paths = sorted((ROOT/"synthetic_adapter").glob("*.py")) + sorted((ROOT/"implementation/rmo").glob("*.py"))
    paths += [ROOT/"RMO/RMO_benchmark_manifest_v1_1.yaml", ROOT/"specification/quicklook_input/request_schema_draft_0_1_0.json"]
    return [{"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]


def worker_command(mode="solve"):
    # A fixed local path, never selected by request contents.
    return [sys.executable,"-B",str(WORKER if mode == "solve" else ROOT/"synthetic_adapter/check_worker.py")]


def run_worker(request, policy, seconds, cancel=None, *, validation_job=None):
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    begun = time.monotonic()
    report = dict(policy=policy,status="FAILED",solver_call_count=0,raw_packet=None,
                  allocated_seconds=seconds,started_utc=utc(),errors=[])
    command=worker_command("solve" if validation_job is None else "validate")
    report["worker_command"]=command
    proc = subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                            env=env,start_new_session=True)
    selector = selectors.DefaultSelector()
    buffers = {"stdout":bytearray(),"stderr":bytearray()}
    try:
        payload=encode(dict(request=request,policy=policy) if validation_job is None else validation_job).encode()
        if len(payload)>OUTPUT_LIMIT: raise ValueError("Validation handoff exceeds size limit")
        os.set_blocking(proc.stdin.fileno(),False)
        selector.register(proc.stdin,selectors.EVENT_WRITE,"stdin")
        sent=0
        for stream,name in ((proc.stdout,"stdout"),(proc.stderr,"stderr")):
            os.set_blocking(stream.fileno(),False); selector.register(stream,selectors.EVENT_READ,name)
        reason, size = None, 0
        while selector.get_map():
            if cancel is not None and cancel.is_set(): reason="CANCELLED"; break
            if time.monotonic()-begun >= seconds: reason="TIME_LIMIT"; break
            for key,_ in selector.select(min(.02,max(0,seconds-(time.monotonic()-begun)))):
                if key.data == "stdin":
                    try: sent += os.write(proc.stdin.fileno(),payload[sent:sent+65536])
                    except BrokenPipeError: sent=len(payload)
                    if sent == len(payload): selector.unregister(proc.stdin); proc.stdin.close()
                    continue
                data = os.read(key.fileobj.fileno(),65536)
                if not data: selector.unregister(key.fileobj); continue
                size += len(data)
                if size > OUTPUT_LIMIT: reason="OUTPUT_LIMIT"; break
                buffers[key.data].extend(data)
            if reason: break
        if reason:
            if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
            proc.wait(timeout=2)
        else:
            try: proc.wait(timeout=max(.001,seconds-(time.monotonic()-begun)))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL); proc.wait(timeout=2); reason="TIME_LIMIT"
        packet = None
        for line in bytes(buffers["stdout"]).splitlines():
            try:
                event = strict_load(line.decode(),OUTPUT_LIMIT)
                if event.get("event") == "solver_entered": report["solver_call_count"] += 1
                elif event.get("event") == "result":
                    if packet is not None: raise ValueError("Duplicate result packet")
                    packet=event["packet"]
                elif event.get("event") == "failure": report["errors"].append(event)
                else: raise ValueError("Unknown worker event")
            except (ValueError,UnicodeError,KeyError,TypeError) as exc:
                report["errors"].append({"protocol":str(exc)})
        report["status"] = reason or ("FINISHED" if proc.returncode == 0 and packet is not None and not report["errors"] else "FAILED")
        report["returncode"] = proc.returncode
        report["stderr"] = bytes(buffers["stderr"]).decode(errors="replace")[:2000]
        # Killed/oversized/failed workers do not certify partially serialized objects.
        if report["status"] == "FINISHED": report["raw_packet"] = packet
    finally:
        selector.close()
        if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL); proc.wait(timeout=2)
        for stream in (proc.stdout,proc.stderr): stream.close()
        if not proc.stdin.closed: proc.stdin.close()
    report.update(elapsed_seconds=time.monotonic()-begun,ended_utc=utc())
    return report


def outcome(response):
    runs = response["policy_runs"]
    solutions = [s for r in runs for s in r.get("validation",{}).get("checked_solutions",[])]
    notices = [r for r in runs if r.get("validation",{}).get("status") == "CHECKED_DOMAIN_NOTICE"]
    profile = response["capability"].get("profile")
    if solutions:
        labels = {"CONSTANT":"A constant-state solution", "CONTACT":"A contact-discontinuity solution",
                  "ROTATION_FIXTURE":"A rotational-discontinuity solution", "TANGENTIAL_FIXTURE":"A tangential-discontinuity solution",
                  "HYDRO":"A zero-field Euler solution"}
        sentence = labels[profile]+" was calculated and passed the listed independent checks for these synthetic inputs."
        if any(r.get("validation",{}).get("status") not in ("PASS","CHECKED_DOMAIN_NOTICE") for r in runs): sentence += " Some requested policy checks did not finish or pass."
        next_action = "Inspect the states, wave speeds and check table; then compare a deliberately edited eligible input."
    elif notices:
        sentence="The zero-field vacuum-formation criterion is satisfied; no finite-state vacuum fan was reconstructed."
        next_action="Inspect the velocity-gap criterion. Do not treat this notice as a computed vacuum profile."
    elif response["input"]["status"] != "VALID":
        sentence="No calculation: input is "+response["input"]["status"].lower()+"."
        next_action="Read the named input errors or keep unknown values explicitly unknown."
    elif profile == "OTHER":
        sentence="These inputs are valid, but this calculation route cannot yet solve this case."
        next_action="Keep the request. A saved reference, if viewed separately, is not a new solution of this input."
    else:
        sentence="No checked solution is available from this attempt."
        next_action="Inspect the execution and failed-check records; this does not exclude a physical family."
    return dict(sentence=sentence,next_action=next_action,units="normalized synthetic; not observed km/s",
                limits=["Only the declared special-case route was tested; full MHD branch coverage is not established.",
                        "This is not a solar observation, shock detection or unique physical classification.",
                        "No uncertainty propagation or dynamical stability test was performed."])


def run(text, *, cancel=None, seconds=30.):
    """Trusted Python caller may shorten the budget/cancel; user JSON cannot expand it."""
    if not 0 < seconds <= 30: raise ValueError("Local budget must be in (0,30] seconds")
    start = time.monotonic()
    response = dict(adapter_version=VERSION,adapter_contract=CONTRACT,identity={},
                    input={"status":"INVALID","errors":[]},capability={"profile":"OTHER"},
                    execution={"status":"NOT_STARTED","solver_call_count":0,"started_utc":utc()},policy_runs=[],
                    coverage={"full_mhd_coverage":"NOT_ESTABLISHED","capability_profile":PROFILE},
                    observer_assessment={"feature_identity":"SYNTHETIC_INPUT", "model_domain":"NOT_ASSESSED_FOR_SOLAR_PLASMA",
                                         "mathematical_structure":"NOT_ASSESSED", "mhd_family":"NOT_ASSESSED",
                                         "sequence_identifiability":"FULL_SET_NOT_ESTABLISHED", "evidence_strength":"NO_OBSERVATIONAL_INFERENCE"},
                    source_records=source_records())
    lock = None
    try:
        envelope,request,validation = unpack(text)
        response["identity"] = envelope
        response["input"] = validation
        response["input"]["parsed_snapshot"] = request
        if validation["status"] == "VALID":
            profile,why = eligibility(request)
            response["capability"] = dict(profile=profile,reason=why)
            response["policy_runs"] = [dict(policy=p,status="NOT_STARTED",solver_call_count=0) for p in request["policies"]]
            if profile != "OTHER":
                import fcntl
                import resource
                if not hasattr(resource,"RLIMIT_AS"): raise RuntimeError("Required memory limit unavailable")
                key = hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
                lock = open(Path(tempfile.gettempdir())/("rmo-adapter-"+key+".lock"),"a")
                try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: raise RuntimeError("BUSY: one active local request allowed")
                for i,policy in enumerate(request["policies"]):
                    remaining = seconds-(time.monotonic()-start)
                    allocation = min(seconds/len(request["policies"]),remaining)
                    if (cancel is not None and cancel.is_set()) or allocation <= 0:
                        response["policy_runs"][i]["status"] = "CANCELLED" if cancel is not None and cancel.is_set() else "TIME_LIMIT"
                        continue
                    policy_start=time.monotonic()
                    r = run_worker(request,policy,allocation,cancel)
                    response["policy_runs"][i] = r
                    if r["status"] == "FINISHED":
                        check_budget=min(allocation-(time.monotonic()-policy_start),seconds-(time.monotonic()-start))
                        if check_budget <= 0:
                            r["status"]="TIME_LIMIT"
                            r["validation"]={"status":"TIME_LIMIT","checked_solutions":[],"reason":"Check exceeded total request deadline"}
                        else:
                            checked=run_worker(request,policy,check_budget,cancel,validation_job=dict(packet=r["raw_packet"],request=request,policy=policy,profile=profile))
                            r["validation_execution"]={k:v for k,v in checked.items() if k != "raw_packet"}
                            r["validation"]=checked["raw_packet"] if checked["status"] == "FINISHED" else {"status":checked["status"],"checked_solutions":[],"reason":"Independent check did not finish"}
                            if checked["status"] != "FINISHED": r["status"]=checked["status"]
                response["execution"]["solver_call_count"] = sum(r["solver_call_count"] for r in response["policy_runs"])
                statuses = [r["status"] for r in response["policy_runs"]]
                response["execution"]["status"] = "FINISHED" if all(s=="FINISHED" for s in statuses) else "PARTIAL_OR_FAILED"
                if any(r.get("validation",{}).get("checked_solutions") for r in response["policy_runs"]):
                    response["observer_assessment"]["mathematical_structure"]="CHECKED_SYNTHETIC_SOLUTION_ONLY"
                    response["observer_assessment"]["mhd_family"]="SEE_CHECKED_MATHEMATICAL_WAVES_NOT_OBSERVATIONAL_CLASSIFICATION"
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError) as exc:
        if response["identity"] and response["input"]["status"] == "VALID":
            response["execution"].update(status="FAILED",reason=str(exc))
        else:
            response["input"]={"status":"INVALID","errors":[{"path":"/","message":str(exc)}]}
    except (RuntimeError,OSError,ImportError) as exc:
        response["execution"].update(status="UNAVAILABLE",reason=str(exc))
    finally:
        if lock is not None: lock.close()
    response["execution"]["solver_call_count"] = sum(r.get("solver_call_count",0) for r in response["policy_runs"])
    response["execution"].update(elapsed_seconds=time.monotonic()-start,ended_utc=utc(),total_budget_seconds=seconds)
    response["presentation"]=outcome(response)
    serialized=encode(response)
    if len(serialized.encode())>OUTPUT_LIMIT:
        # Do not promote a result that cannot be preserved within the declared envelope.
        return dict(adapter_version=VERSION,execution={"status":"OUTPUT_LIMIT","solver_call_count":response["execution"]["solver_call_count"]},
                    identity=response["identity"],checked_solutions=[],presentation={"sentence":"Response exceeds the output limit; no checked-result card is available."})
    return response


def matches_input(response, execution_id, body_sha256, revision):
    """Association predicate only; no browser/async UI integration is implemented."""
    ident=response.get("identity",{})
    return ident.get("execution_id")==execution_id and ident.get("request_body_sha256")==body_sha256 and ident.get("input_revision")==revision
