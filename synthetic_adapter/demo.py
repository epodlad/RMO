"""Generate a read-only worked example from a fresh, independently checked local run."""
from html import escape
import base64
import json
from pathlib import Path
from .input import ROOT, fixture_request, make_envelope, encode
from .runner import run
from .report_format import cell, LEGEND


def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    request=fixture_request("B01_contact")
    envelope=make_envelope(request,execution_id="worked_contact_B01",revision=0)
    result=run(envelope)
    for p in result["policy_runs"]:
        if p.get("validation",{}).get("status") != "PASS":raise RuntimeError("Worked example requires checked results for both policies")
    (out/"contact_request.json").write_text(encode(request)+"\n")
    (out/"contact_execution_envelope.json").write_text(envelope+"\n")
    (out/"contact_result.json").write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)+"\n")
    packet=result["policy_runs"][0]["raw_packet"]
    left,right=packet["initial_states"]
    wave=result["policy_runs"][0]["validation"]["checked_solutions"][0]["waves"][0]
    speed=wave["speed"]
    make_plot(out,left,right,speed)
    tests=result["policy_runs"][0]["validation"]["checks"]
    inputs=[("Mass density",left["rho"],right["rho"]),("Thermal pressure",left["p"],right["p"]),
            ("Velocity (normal, transverse 1, transverse 2)",left["u"],right["u"]),
            ("Magnetic field (normal, transverse 1, transverse 2)",left["B"],right["B"])]
    rows="".join(f"<tr><th>{escape(k)}</th><td>{escape(str(l))}</td><td>{escape(str(r))}</td></tr>" for k,l,r in inputs)
    request_link="data:application/json;base64,"+base64.b64encode((encode(request)+"\n").encode()).decode()
    envelope_link="data:application/json;base64,"+base64.b64encode((envelope+"\n").encode()).decode()
    checks="".join(f"<tr><td>{escape(c['check'])}</td><td>{c['status']}</td><td>{cell(c.get('value'))}</td><td>{cell(c.get('tolerance'), tolerance=True)}</td></tr>" for c in tests)
    svg=(out/"contact_solution.svg").read_text();svg=svg[svg.index("<svg"):]
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; base-uri 'none'; form-action 'none'">
<title>RMO — computed contact example</title><style>
body{{font:17px/1.6 system-ui,sans-serif;color:#193035;background:#f4f7f6;margin:0}}main{{max-width:1100px;margin:30px auto;padding:24px}}h1,h2{{line-height:1.2}}.answer{{background:#e4f1ed;border-left:5px solid #1c7165;padding:18px 24px}}.limit{{background:#fff2d9;padding:14px 20px;border-left:4px solid #9d6a13}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{text-align:left;border-bottom:1px solid #c9d6d3;padding:10px}}svg{{width:100%;height:auto;background:white}}details{{border-top:1px solid #c9d6d3;padding:16px 0}}summary{{cursor:pointer;font-weight:650}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;max-height:500px;overflow:auto}}.small{{font-size:14px}}.scroll{{overflow:auto}}
</style></head><body><main>
<p>RIEMANN MAPS FOR SOLAR OBSERVERS · SYNTHETIC WORKED EXAMPLE · RMO-62</p>
<h1>A calculated contact discontinuity</h1>
<p>RMO is being developed for EUV wave fronts. This first example tests the calculation path with prescribed plasma states, not solar observations.</p>
<section class="answer"><h2>Result in one sentence</h2><p>A contact discontinuity was calculated and checked: the density boundary moves at <strong>{speed:g}</strong> in normalized units, while pressure, velocity and magnetic field remain continuous.</p>
<p><strong>For this solution:</strong> a contact, not a shock. This does not establish the complete set of MHD solutions for these inputs.</p></section>
<p class="small">This is a read-only report of a fresh local Python calculation. Opening this HTML does not run the solver. The separate QuickLook input page is unchanged and is not yet connected to Python.</p>
<h2>1. What was entered?</h2><p>Two neighbouring uniform plasma regions at the start. Both move at the same normal velocity. Density differs: 1 on the LEFT, 0.5 on the RIGHT. Gamma = {packet['gamma']:.8g}; all quantities use the fixed synthetic normalization.</p>
<div class="scroll"><table><thead><tr><th>Quantity</th><th>Initial LEFT</th><th>Initial RIGHT</th></tr></thead><tbody>{rows}</tbody></table></div>
<p><a download="contact_request.json" href="{request_link}">Download example request JSON — input only</a></p>
<details><summary>Use this JSON example with the local Python adapter</summary><p>This page does not upload or execute JSON. The input example is editable; it is not a result. For a local run, a separate execution envelope records the exact input text and its checksum. If you edit the request, create a new envelope; do not reuse the old checksum.</p><p><a download="contact_execution_envelope.json" href="{envelope_link}">Download matching execution envelope — local Python only</a></p><p>See synthetic_adapter/README.md in the full bundle for the two local commands. Downloading either file does not run a calculation.</p></details>
<h2>2. Where is the checked solution?</h2>{svg}
<p>The left panel is an <strong>analytic contact-family slice</strong>: pressure, velocity and magnetic field are fixed while density may differ. The markers are the prescribed states joined by the calculated contact; they are not measurements fitted to the line. The line is not a numerical scan of all Riemann branches. The right panel shows the density profile of the checked solution versus x/t.</p>
<div class="limit"><strong>Checked solution:</strong> contact discontinuity.<br><strong>Other branches:</strong> not fully searched.<br><strong>Uniqueness:</strong> not established. An unsearched branch is neither demonstrated nor excluded.</div>
<h2>3. Why does it pass?</h2><p>The boundary speed equals the plasma normal speed on both sides. No plasma crosses the boundary in its rest frame. The independent checks confirm continuity of pressure, velocity and magnetic field, consistent initial states, and the conservation jump conditions. The density difference alone is not a shock-compression measurement.</p>
<p>Both requested admissibility policies returned the same contact here and passed these checks. That agreement is not proof of complete branch enumeration, dynamical stability or a solar interpretation.</p>
<h2>What next?</h2><p>The code also tests an edited input with both normal velocities increased by 0.25: the calculated contact speed changes from 0.2 to 0.45. This confirms that an eligible new input is calculated, not replaced by the saved example. Browser-to-Python integration is a separate next step.</p>
<details><summary>Independent checks — first policy</summary>{LEGEND}<div class="scroll"><table><thead><tr><th>Check</th><th>Status</th><th>Value</th><th>Tolerance, when used</th></tr></thead><tbody>{checks}</tbody></table></div></details>
<details><summary>Exact input, result, provenance and both policy records</summary><pre>{escape(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2))}</pre></details>
<p class="small">No observations, physical unit conversion, uncertainty propagation, coronal magnetic-field inference, full-MHD completeness proof or dynamical stability analysis. No public hosting. New HTML rendering has not been tested in an actual browser in this environment.</p>
</main></body></html>'''
    (out/"RMO_computed_contact_example.html").write_text(html)
    return result


def make_plot(out,l,r,speed):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context({"font.size":11,"svg.fonttype":"none","axes.spines.top":False,"axes.spines.right":False}):
        fig,axes=plt.subplots(1,2,figsize=(11,4.7))
        a,b=axes
        a.plot([.2,1.2],[l["p"],l["p"]],color="#28766f",lw=2)
        a.scatter([l["rho"]],[l["p"]],s=65,color="#315b88",zorder=3)
        a.scatter([r["rho"]],[r["p"]],s=85,color="#b85b24",marker="D",zorder=3)
        a.annotate("Initial LEFT",(l["rho"],l["p"]),xytext=(0,25),textcoords="offset points",ha="center",color="#315b88")
        a.annotate("Initial RIGHT\njoined by checked contact",(r["rho"],r["p"]),xytext=(0,-45),textcoords="offset points",ha="center",color="#9b4419")
        a.set(xlim=(.15,1.25),ylim=(.72,1.28),xlabel="Mass density (normalized)",ylabel="Thermal pressure (normalized)",title="Analytic contact-family slice")
        a.text(.5,.9,"Fixed pressure, velocity and magnetic field",ha="center",transform=a.transAxes,fontsize=9)
        b.plot([-.4,speed,speed,.8],[l["rho"],l["rho"],r["rho"],r["rho"]],color="#28766f",lw=2.5)
        b.axvline(speed,color="#b85b24",lw=1.5,ls="--")
        b.annotate(f"Contact speed = {speed:g}",(speed,.75),xytext=(18,20),textcoords="offset points",color="#9b4419")
        b.text(-.3,1.06,"LEFT",color="#315b88");b.text(.55,.56,"RIGHT",color="#9b4419")
        b.set(xlim=(-.4,.8),ylim=(.35,1.2),xlabel="x/t (normalized speed coordinate)",ylabel="Mass density (normalized)",title="Computed and checked density profile")
        for ax in axes:ax.grid(alpha=.15)
        fig.suptitle("One checked synthetic solution — not a complete MHD branch map",fontsize=14,y=.97)
        fig.text(.5,.045,"Checked: contact   |   Other branches: not fully searched   |   Uniqueness: not established",ha="center",fontsize=10,color="#765512")
        fig.subplots_adjust(left=.08,right=.98,bottom=.2,top=.82,wspace=.3)
        fig.savefig(out/"contact_solution.png",dpi=160,metadata={"Software":"Python / Matplotlib"})
        fig.savefig(out/"contact_solution.svg",metadata={"Creator":"Python / Matplotlib","Date":None})
        plt.close(fig)
    (out/"contact_plot_data.json").write_text(json.dumps({"kind":"analytic_slice_plus_computed_solution_not_all_branch_map","left":l,"right":r,"computed_contact_speed":speed,"line":"p_R=p_L at fixed velocity and magnetic field; analytic invariant, not a branch scan","xi_density":[[-.4,l['rho']],[speed,l['rho']],[speed,r['rho']],[.8,r['rho']]],"full_mhd_coverage":"NOT_ESTABLISHED"},indent=2)+"\n")


if __name__=="__main__":build(ROOT/"results/synthetic_adapter/worked_contact")
