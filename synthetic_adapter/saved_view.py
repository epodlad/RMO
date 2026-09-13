"""Plot three preserved Brio-Wu records. No numerical solve and no branch interpolation."""
import hashlib
from html import escape
import json
from pathlib import Path
import re
from .input import ROOT, equal

TAGS=("regular","intermediate","compound")
TITLES=("Regular rotational fan","Intermediate-containing fan","Attached compound fan")


def records():
    rows=[]
    for tag,title in zip(TAGS,TITLES):
        path=ROOT/f"results/r6d_final/RMO_R6d_schema_{tag}.json"
        data=json.loads(path.read_text());s=data["solutions"][0]
        contact=next(w for w in s["waves"] if w["structure"]=="contact")
        state=next(x for x in s["intermediate_states"] if x["id"]==contact["left_state_ref"])
        rows.append(dict(tag=tag,title=title,record=data,solution=s,pressure=state["p"],velocity=state["u"][0],
                         coordinate_state_ref=state["id"],source=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for row in rows[1:]:
        for k in ("initial_states","geometry","normalization"):
            if not equal(row["record"][k],rows[0]["record"][k]):raise ValueError("Cannot compare unlike inputs")
        for k in ("model","gamma","mu0_normalized"):
            if not equal(row["record"]["physics"][k],rows[0]["record"]["physics"][k]):raise ValueError("Different physical problem")
    return rows


def svg_embed(path,prefix):
    text=path.read_text();text=text[text.index("<svg"):]
    ids=re.findall(r'\bid="([^"]+)"',text)
    for old in ids:
        text=text.replace(f'id="{old}"',f'id="{prefix}{old}"')
        text=text.replace(f'url(#{old})',f'url(#{prefix}{old})')
        text=text.replace(f'href="#{old}"',f'href="#{prefix}{old}"')
    return text


def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=records()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors=["#315b88","#b06024","#267262"]
    with plt.rc_context({"font.size":11,"svg.fonttype":"none","axes.spines.top":False,"axes.spines.right":False}):
        fig,ax=plt.subplots(figsize=(10,5.1))
        offsets=[(18,-12),(-120,0),(18,28)]
        for row,col,offset in zip(rows,colors,offsets):
            x,y=row["velocity"],row["pressure"]
            ax.scatter([x],[y],s=75,color=col,zorder=3)
            halo=ax.scatter([x],[y],s=270,facecolors="none",edgecolors="#cf2162",linewidths=2.5,zorder=4)
            halo.set_gid("highlight_"+row["tag"])
            ax.annotate(row["title"],(x,y),xytext=offset,textcoords="offset points",fontsize=10,
                        color=col,ha="left" if offset[0]>0 else "right",arrowprops=dict(arrowstyle="-",color=col,lw=.8))
        ax.set(xlim=(.5898,.6020),ylim=(.511,.5172),xlabel="Normal velocity at the contact (normalized)",ylabel="Thermal pressure at the contact (normalized)")
        ax.grid(alpha=.18)
        fig.suptitle("Three saved Brio–Wu solutions: locations in one state-plane projection",fontsize=13,y=.97)
        fig.text(.5,.905,"Same initial states and gamma = 2; policies are shown separately below",ha="center",fontsize=10)
        fig.text(.5,.045,"Three found solutions, not all admissible solutions. No interpolated branch curves.",ha="center",fontsize=10,color="#765512")
        fig.subplots_adjust(left=.12,right=.97,bottom=.19,top=.85)
        fig.savefig(out/"saved_BrioWu_locations.svg",metadata={"Creator":"Python / Matplotlib","Date":None})
        # Static PNG shows all three points without suggesting one is preferred.
        for collection in ax.collections:
            if collection.get_gid():collection.set_visible(False)
        fig.savefig(out/"saved_BrioWu_locations.png",dpi=160,metadata={"Software":"Python / Matplotlib"})
        plt.close(fig)
        for row in rows:
            fig,(a,b)=plt.subplots(1,2,figsize=(10,3.9),gridspec_kw={"width_ratios":[1.4,1]})
            for ax in (a,b):
                for w in row["solution"]["waves"]:
                    family=w["family"];kind=w["structure"];s=w["speed"]
                    col="#347daf" if family.startswith("fast") else "#267262" if family.startswith("slow") else "#774998" if family.startswith("alfven") else "#b06024" if family=="intermediate" else "#333333"
                    if isinstance(s,list):
                        ax.fill([0,s[0],s[1]],[0,1,1],color=col,alpha=.18)
                        for v in s:ax.plot([0,v],[0,1],color=col,lw=1)
                    else:
                        ax.plot([0,s],[0,1],color=col,lw=2,ls="--" if kind=="contact" else "-." if kind=="rotation" else "-")
                        ax.scatter([s],[1],color=col,s=22,zorder=3)
                ax.grid(alpha=.12);ax.set_xlabel("x (normalized)")
            a.set(xlim=(-2,4),ylim=(0,1.06),ylabel="t (normalized)",title="Saved wave fan: x = speed × t")
            b.set(xlim=(-.34,.015),ylim=(.4,1.06),title="Inner left-going structures: zoom")
            b.tick_params(axis="both",labelsize=9)
            fig.suptitle(row["title"],fontsize=13,y=.98)
            fig.text(.5,.10,"Blue: fast  ·  Green: slow  ·  Purple: rotation  ·  Brown: intermediate  ·  Dashed: contact",ha="center",fontsize=9)
            fig.text(.5,.035,"Shaded regions: rarefactions. Labels come from preserved calculations; no new solve or completeness claim.",ha="center",fontsize=9,color="#765512")
            fig.subplots_adjust(left=.075,right=.97,bottom=.26,top=.8,wspace=.28)
            fig.savefig(out/f"saved_{row['tag']}_fan.svg",metadata={"Creator":"Python / Matplotlib","Date":None})
            fig.savefig(out/f"saved_{row['tag']}_fan.png",dpi=150,metadata={"Software":"Python / Matplotlib"})
            plt.close(fig)
    plotdata=[{k:v for k,v in row.items() if k not in ("record","solution")} for row in rows]
    (out/"saved_locations_and_sources.json").write_text(json.dumps(plotdata,indent=2)+"\n")
    cards=[]
    for row in rows:
        table="".join(f"<tr><td>{w['order']}</td><td>{escape(w['structure'])}</td><td>{escape(w['family'])}</td><td>{escape(str(w['speed']))}</td></tr>" for w in row["solution"]["waves"])
        cards.append(f'''<section class="solution" id="solution-{row['tag']}"><h2>{row['title']}</h2><p>Policy: {escape(row['solution']['policy'])}. Contact-state coordinate: u = {row['velocity']:.10f}, p = {row['pressure']:.10f}.</p>{svg_embed(out/f"saved_{row['tag']}_fan.svg",row['tag']+'-')}
<details><summary>Exact saved wave sequence and source</summary><div class="scroll"><table><thead><tr><th>Order</th><th>Structure</th><th>Family</th><th>Speed / interval</th></tr></thead><tbody>{table}</tbody></table></div><p>Source: {row['source']}<br>SHA-256: <code>{row['sha256']}</code></p></details></section>''')
    script='''"use strict";const selector=document.getElementById("saved-choice");function selectSaved(){const choice=selector.value;for(const tag of ["regular","intermediate","compound"]){document.getElementById("map-highlight_"+tag).style.display=choice===tag?"":"none";document.getElementById("solution-"+tag).hidden=choice!=="all"&&choice!==tag;}document.getElementById("selection-status").textContent=choice==="all"?"All three saved solutions are shown. No preference or completeness is implied.":"Highlighted: "+selector.options[selector.selectedIndex].text+". This selects a saved record; it does not calculate or identify a preferred physical solution.";}selector.addEventListener("change",selectSaved);selectSaved();'''
    (out/"saved_selection.js").write_text(script+"\n")
    page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>RMO — three saved Brio–Wu solutions</title><style>
body{{font:17px/1.6 system-ui,sans-serif;color:#193035;background:#f4f7f6}}main{{max-width:1100px;margin:auto;padding:24px}}svg{{width:100%;height:auto;background:white}}select{{font:inherit;padding:12px;max-width:100%;border:1px solid #a9bfba}}.notice{{background:#fff2d9;border-left:4px solid #9d6a13;padding:16px}}.solution{{border-top:1px solid #b4c7c2;margin-top:28px}}summary{{cursor:pointer;font-weight:650}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #b4c7c2}}.scroll{{overflow:auto}}code{{overflow-wrap:anywhere}}[hidden]{{display:none!important}}
</style></head><body><main><h1>Open a saved solution and see its location</h1>
<p>These are three earlier synthetic Brio–Wu calculations for the same initial states, with gamma = 2. No solver runs on this page. They are separate from the newly calculated contact example and from any edited QuickLook input.</p>
<label for="saved-choice">Choose a saved solution</label><br><select id="saved-choice"><option value="all">All three saved solutions</option><option value="regular">Regular rotational fan</option><option value="intermediate">Intermediate-containing fan</option><option value="compound">Attached compound fan</option></select><p id="selection-status" role="status" aria-live="polite"></p>
{svg_embed(out/'saved_BrioWu_locations.svg','map-')}
<p><strong>What is a point?</strong> One saved solution, represented by thermal pressure and normal velocity at its contact. A full Riemann solution contains several waves; the point is not itself a shock. Other state components are not displayed, so this projection can hide differences.</p>
<div class="notice"><strong>Found solutions:</strong> three saved examples.<br><strong>Complete solution set:</strong> not established.<br><strong>Preferred physical interpretation:</strong> not selected.<br>No lines are drawn between points because no continuous branch curve is reconstructed by this viewer.</div>
<p>For exactly matching inputs, a saved checked calculation may be reused with its provenance. Locating a different input near one of these points does not validate that input or select its MHD family. New calculations need their own checks.</p>
{''.join(cards)}<p>Saved numerical results and their original evidence levels are unchanged. This is a geometric display, not a new scientific validation. The local Python adapter does not yet rerun these targeted non-regular procedures. Browser execution and accessibility of this new selector remain to be checked in a real browser.</p>
<noscript>JavaScript is disabled. All three saved solutions remain visible; interactive highlighting is unavailable.</noscript>
</main><script>{script}</script></body></html>'''
    (out/"RMO_saved_BrioWu_solutions.html").write_text(page)
    return plotdata


if __name__=="__main__":build(ROOT/"results/synthetic_adapter/saved_BrioWu")
