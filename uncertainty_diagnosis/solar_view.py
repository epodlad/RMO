"""Plot already checked published geometry arithmetic; no shock diagnosis."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent

def build():
    out = ROOT / 'results/uncertainty_diagnosis'
    solar = json.loads((out / 'study.json').read_text())['solar']
    arithmetic = json.loads((ROOT / 'science_readiness/published_arithmetic_check.json').read_text())
    rows = solar['rows']
    assert len(rows) == len(arithmetic['rows']) == 3
    for row, source in zip(rows, arithmetic['rows']):
        assert row['point'] == source['point']
        assert row['apparent_speed_km_s'] == source['apparent_pattern_speed_km_s']
        assert row['surface_pattern_speed_km_s'] == source['surface_pattern_speed_km_s']
        assert source['uncertainty'] is None
    fig, ax = plt.subplots(figsize=(9.6, 5.0), facecolor='white')
    fig.subplots_adjust(left=.17, right=.94, top=.75, bottom=.28)
    fig.text(.06, .93, 'Same EUV front: geometry changes the inferred speed', fontsize=16, weight='bold')
    fig.text(.06, .865, '13 February 2009 | Podladchikova et al. (2019), Tables 4–5', fontsize=11)
    for i, row in enumerate(rows):
        y = 2 - i
        corrected, apparent = row['surface_pattern_speed_km_s'], row['apparent_speed_km_s']
        ax.plot([corrected, apparent], [y, y], color='#c5d2d1', linewidth=3, zorder=1)
        ax.scatter(corrected, y, color='#237668', s=70, label='3D-corrected surface pattern' if i == 0 else None, zorder=3)
        ax.scatter(apparent, y, color='#287dab', s=70, label='Apparent image pattern' if i == 0 else None, zorder=3)
        ax.text(corrected-2.2, y+.13, f'{corrected:.1f}', ha='right', fontsize=11, color='#18564b')
        ax.text(apparent+2.2, y+.13, f'{apparent:.1f}', ha='left', fontsize=11, color='#215f85')
    ax.set_yticks([2, 1, 0], ['Point 1', 'Point 2', 'Point 3'])
    ax.set_xlim(185, 280); ax.set_ylim(-.4, 2.5)
    ax.set_xlabel('Inferred pattern speed (km/s)', fontsize=11)
    ax.grid(axis='x', color='#e6eceb'); ax.set_axisbelow(True)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower left', bbox_to_anchor=(.055, .11), ncol=2, frameon=False, fontsize=10)
    fig.text(.06, .072, 'Published central values; observational error bars are unavailable in this extraction.', fontsize=10)
    fig.text(.06, .03, 'Pattern motion alone does not identify the shock type. DOI: 10.3847/1538-4357/ab1b3a', fontsize=10)
    for ext in ['svg', 'png']:
        fig.savefig(out / f'RMO_EUV_2009_geometry.{ext}', dpi=150)
    plt.close(fig)
    (out / 'RMO_EUV_2009_geometry.json').write_text(json.dumps(solar, indent=2)+'\n')
    print('Published values verified; solar geometry SVG/PNG/JSON written. No new solar classification.')

if __name__ == '__main__':
    build()
