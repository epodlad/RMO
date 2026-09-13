"""Build scientific vector figure, explanation and scientific explanation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .assess import ROOT
from .pdf_report import make_pdf

def build():
    out = ROOT / 'results/uncertainty_diagnosis'
    data = json.loads((out / 'study.json').read_text())
    fig = plt.figure(figsize=(11, 8.2), facecolor='white')
    fig.suptitle('RMO | Does the local shock type survive input uncertainty?', fontsize=17, x=0.07, ha='left', y=0.97)
    fig.text(0.07, 0.918, 'Two checked synthetic shocks. Fixed normal geometry and gamma = 5/3. No observed event is classified here.', fontsize=10)
    gs = fig.add_gridspec(1, 2, left=0.16, right=0.94, bottom=0.4, top=0.835, wspace=0.5)
    for col, key in enumerate(['A63', 'A17']):
        ax = fig.add_subplot(gs[0, col])
        r = next((r for r in data['cases'] if r['id'] == key and r['factor'] == 0.01))
        o = r['output']
        labels = []
        yy = 0
        colours = {'slow': '#247668', 'alfven_n': '#80519a', 'fast': '#287dab', 'flow': '#202b2c'}
        for side in ['left', 'right']:
            for k in ['slow', 'alfven_n', 'fast', 'flow']:
                val = o['characteristic_bounds'][side][k] if k != 'flow' else o['relative_speed_bounds'][side]
                if k == 'flow':
                    val = sorted(map(abs, val))
                ax.plot(val, [yy, yy], lw=5, color=colours[k], solid_capstyle='round')
                ax.plot([sum(val) / 2], [yy], 'o', ms=4, color=colours[k])
                labels.append(side + ' ' + {'slow': 'slow', 'alfven_n': 'Alfven', 'fast': 'fast', 'flow': '|u_n - S|'}[k])
                yy += 1
        ax.set_yticks(range(8), labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(left=0)
        ax.set_xlabel('Speed (normalized units)', fontsize=10)
        ax.grid(axis='x', alpha=0.18)
        ax.set_title(key + ' | ' + o['family'].replace('_', ' ') + ' | f = 0.01', fontsize=11, pad=15)
        for s in ['top', 'right']:
            ax.spines[s].set_visible(False)
    ax = fig.add_axes([0.07, 0.16, 0.87, 0.19])
    ax.axis('off')
    tbl = ax.table(cellText=[['Fast shock A63', 'Certified', 'Certified', 'Not certified'], ['Slow shock A17', 'Certified', 'Not certified', 'Not certified'], ['Contact A42 / rotation A88', 'Equality model needed', 'Equality model needed', 'Equality model needed']], colLabels=['Conditional interval test', 'f = 0.01', 'f = 0.05', 'f = 0.10'], loc='center', cellLoc='left', colWidths=[0.3, 0.23, 0.235, 0.235])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.7)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor('#cbdad9')
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor('#e7f1ef')
            cell.set_text_props(weight='bold')
    fig.text(0.07, 0.092, 'Half-widths: f |q| for density/pressure; f max(1, |q|) for velocity, field components and front speed.', fontsize=9)
    fig.text(0.07, 0.068, 'Bars are deterministic enclosures, not confidence intervals. Certification assumes a conservation-compatible local discontinuity.', fontsize=9)
    fig.text(0.07, 0.044, 'Not certified means the sufficient test is inconclusive. It does not establish a competing feasible branch or exclude a wave.', fontsize=9)
    for ext in ['pdf', 'svg', 'png']:
        fig.savefig(out / f'RMO_uncertainty_diagnosis.{ext}', dpi=170)
    plt.close(fig)
    sample = next((r for r in data['cases'] if r['id'] == 'A63' and r['factor'] == 0.01))
    (out / 'RMO_fast_bounded_report.pdf').write_bytes(make_pdf(sample['input'], sample['output']))
    rows = '\n'.join((f"| {r['id']} | {r['factor']:g} | {r['output']['status']} | {r['output'].get('family') or 'No certified type'} |" for r in data['cases']))
    solar = '\n'.join((f"| {r['point']} | {r['apparent_speed_km_s']:.2f} | {r['surface_pattern_speed_km_s']:.2f} | {r['reduction_relative_to_apparent_percent']:.2f}% |" for r in data['solar']['rows']))
    noisy = [r for r in data['controls'] if 'shifted' in r['control']]
    nrows = '\n'.join((f"| {r['id']} | {r['output']['nominal']['checks']['rh_scaled_inf']:.3g} | {float(r['output']['witness']['independent_check']['rh_scaled_inf']):.3g} | {r['output']['family']} |" for r in noisy))
    text = f"# RMO-75: input errors and local MHD diagnosis\n\n## Result in one sentence\n\nThe two synthetic shock types remain conditionally identifiable for some finite\ninput bounds, although noisy central values fail the tight exact-conservation check.\nThese are model demonstrations, not classifications of solar observations.\n\n## What was found\n\n- Fast shock A63 passes the sufficient interval certificate at factors 0.01 and 0.05.\n- Slow shock A17 passes at 0.01. At 0.05, entropy and the downstream slow-speed crossing are not certified.\n- At 0.10 neither shock passes the initial sufficient test; this is not evidence for a second feasible solution.\n- At 0.10 for A63, tightening only pressure half-widths to 1% restores the certificate. This demonstrates a useful additional constraint, not a globally optimal observing strategy.\n- Exact contact and rotational-discontinuity diagnoses are retained. Their equality constraints are not certified by a free, independently varied error box.\n- Missing field, front speed or pressure produces an explicit missing-measurement result. No missing value is replaced by zero or a coronal mean.\n\nThe shared speed and field correlations required by a single front are retained.\nJoint covariance inference, geometry uncertainty and dynamical stability are outside\nthis test. The four inputs are known test fixtures with separate historical scoring\nlabels, not an external unseen validation set or a measured success-rate sample.\n\n## What the percentages mean\n\nFor density and thermal pressure, half-width = f times the absolute central value.\nFor each velocity/field component and front speed, half-width = f times max(1,\nabsolute central value), in the declared normalized units. Zero vector components\ntherefore have nonzero uncertainty. Factors 0.01, 0.05 and 0.10 are illustrative\nbounded input designs; they are **not instrument errors, standard deviations,\nconfidence levels or universal accuracy requirements**. Gamma and normal geometry\nare fixed. Inspect every half-width in the exported request.\n\n## Exact equalities versus measured data\n\nRankine-Hugoniot conservation is tested at scaled tolerance 1e-10 for an exact\nsupplied pair. Measurements generally have much larger errors. Failure of that\nexact-pair check does not itself exclude a shock interpretation.\n\nIn two controls the downstream-pressure centre was shifted upward by 0.25%, with\nthe same 1% box design. The original exact point lies within the box. A bounded\nleast-squares search using conservation alone found a numerical witness; no type\nlabel or saved solution was passed to the search. Every adjustment is recorded.\nIndependent 70-digit lab-frame arithmetic checked each witness. The witness is\n**not** a unique reconstruction, maximum-likelihood estimate or posterior sample.\n\n| Model | Noisy-centre scaled RH | Witness independent scaled RH | Certified local type |\n|---|---:|---:|---|\n{nrows}\n\n## Full model outcomes\n\n| Model | Factor f | Outcome | Type |\n|---|---:|---|---|\n{rows}\n\nCertification combines a checked numerical anchor with outward-rounded interval\nbounds for compression, entropy increase, field trend and characteristic ordering.\nIt is conditional on a **single conservation-compatible planar ideal-MHD\ndiscontinuity** within the supplied box. The interval tests are sufficient, not\nnecessary: failing a bound is NOT CERTIFIED, not proof of ambiguity between two\nconstructed physical solutions. No complete Riemann-fan uniqueness is inferred.\n\n## Existing EUV example: what geometry tells us\n\nT. Podladchikova et al. (2019), ApJ 877, 68, Tables 4-5,\n[source DOI](https://doi.org/10.3847/1538-4357/ab1b3a). Event: 13 February 2009.\nThe same selected front patch is used, as identified in the source record by a study author.\n\n| Point | Apparent pattern speed (km/s) | Corrected surface pattern speed (km/s) | Reduction relative to apparent |\n|---|---:|---:|---:|\n{solar}\n\nThus the already published geometry changes the inferred surface pattern speed by\nabout 19-21%. This is a reproducibility/application check of published values, **not\na new discovery or shock-type determination**. Local normal geometry, shock-frame\nplasma velocities, co-spatial thermomagnetic states and their joint errors are absent\nfrom these extracted tables. Pattern speed and crest-height change cannot simply be\ninserted as plasma normal velocity and shock-normal speed. No assumed beta or\nunreported field was substituted to manufacture a solar classification.\n\n## Verification and interface\n\nThe study passed {data['test_count']} assertions, including anonymous-input scoring,\nmissing/invalid input controls, fixed shared Galilean offsets and normal reversal.\nIndependent 80-digit arithmetic checked characteristic enclosures at\n{data['independent_enclosure_points']} deterministic box points. This checks the\nimplementation; it is not exhaustive validation or a probabilistic accuracy claim.\n\nQuickLook offers the saved study offline, editable local-state inputs and exports.\nThe added Python diagnosis action uses the existing protected local service and\npreserves the exact request, result, adjustments and source hashes. It is separate\nfrom a full Riemann solve and from the preserved Brio-Wu viewer. Native Chrome,\naccessibility and public hosting acceptance remain unverified.\n\n"
    (out / 'RMO_uncertainty_report.md').write_text(text)
    print(json.dumps({'figure': 'RMO_uncertainty_diagnosis.pdf', 'report': 'RMO_uncertainty_report.md'}))
if __name__ == '__main__':
    build()
