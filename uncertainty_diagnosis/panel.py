"""Additive full-QuickLook integration. All older scripts and workspaces retained."""
import base64
import html
import json
from pathlib import Path
from uncertainty_diagnosis.assess import FIELDS

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def data_url(p,mime):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()

def add_to_page(page):
    out=ROOT/'results/uncertainty_diagnosis';study=json.loads((out/'study.json').read_text())
    titles={'front_speed':'Front normal speed S','rho':'Mass density rho','p':'Thermal gas pressure p',
      'u.0':'Plasma normal velocity u_n','u.1':'Tangential velocity u_t1','u.2':'Tangential velocity u_t2',
      'B.0':'Shared normal field B_n','B.1':'Tangential field B_t1','B.2':'Tangential field B_t2'}
    rows=[]
    for k in FIELDS:
        if k=='right.B.0':continue
        name=titles[k] if k=='front_speed' else titles[k.split('.',1)[1]]
        if k.startswith(('left.','right.')) and not k.endswith('B.0'):name=k.split('.')[0].upper()+' - '+name
        id_='r75-'+k.replace('.','-')
        options='<option value="">Choose if unknown</option><option value="__other__">Other reason</option>'+''.join('<option>'+t+'</option>' for t in ['Not measured','Not reported in the source','Measurement unreliable','Geometry not known','Deliberately withheld for this test'])
        rows.append(f'<tr><th scope="row"><label for="{id_}">{html.escape(name)}</label></th><td><input id="{id_}" data-r75-field="{k}" inputmode="decimal" aria-describedby="r75-units" /><select id="{id_}-reason" aria-label="Reason for unknown {html.escape(name)}" hidden>{options}</select><input id="{id_}-reason-other" maxlength="200" aria-label="Other reason for unknown {html.escape(name)}" placeholder="Short explanation" hidden /></td><td><input id="{id_}-width" inputmode="decimal" aria-label="Absolute half-width for {html.escape(name)}" /></td></tr>')
    panel=(HERE/'panel.html').read_text().replace('__ROWS__','\n'.join(rows))
    panel=panel.replace('__FIGURE__',data_url(out/'RMO_uncertainty_diagnosis.png','image/png')).replace('__PDF__',data_url(out/'RMO_uncertainty_diagnosis.pdf','application/pdf'))
    panel=panel.replace('__REPORT__',html.escape((out/'RMO_uncertainty_report.md').read_text()))
    solar=(HERE/'solar.html').read_text()
    for ext,mime in [('png','image/png'),('svg','image/svg+xml'),('json','application/json')]:
        solar=solar.replace('__SOLAR_'+ext.upper()+'__',data_url(out/f'RMO_EUV_2009_geometry.{ext}',mime))
    solar=solar.replace('__SOLAR_ROWS__',''.join(f'<tr><td>{r["point"]}</td><td>{r["apparent_speed_km_s"]:.1f}</td><td>{r["surface_pattern_speed_km_s"]:.1f}</td><td>{r["reduction_relative_to_apparent_percent"]:.1f}%</td></tr>' for r in study['solar']['rows']))
    panel=panel.replace('__SOLAR_EXAMPLE__',solar)
    # Preserve full old page, inserting the new workspace before the existing models.
    marker='<details id="r73-model-workspace"'
    assert page.count(marker)==1
    page=page.replace(marker,panel+'\n'+marker,1)
    faq=(HERE/'faq.html').read_text()
    faq=faq.replace('__PDF__',data_url(out/'RMO_uncertainty_diagnosis.pdf','application/pdf'))
    faq=faq.replace('__REPORT_FILE__',data_url(out/'RMO_uncertainty_report.md','text/markdown;charset=utf-8'))
    help_marker='<details id="help-panel"><summary>Help — terms, examples and status messages</summary>'
    assert page.count(help_marker)==1
    page=page.replace(help_marker,help_marker.replace('Help —','Help / FAQ —')+'\n'+faq,1)
    top='<p><button type="button" id="r75-demo-top" class="primary">Try a model demo</button> One click: load known parameters and see a checked result, a plot and the explanation.</p>'
    top+='<p><button type="button" id="r75-solar-top">Explore a real EUV example</button> Published motion and 3D geometry from 13 February 2009; the shock type is not yet determined.</p>'
    assert '<h1>RMO QuickLook</h1>' in page
    page=page.replace('<h1>RMO QuickLook</h1>','<h1>RMO QuickLook</h1>'+top,1)
    # Keep the full main introduction and visit guide. Compact presentation
    # is confined to the model Demo, as requested by the user.
    # Old guide text stays as historical first-visit guidance; this note states
    # the fresh local action availability without claiming a public server.
    config={'cases':study['cases'],'controls':[x for x in study['controls'] if 'shifted' in x['control']],
        'solar':study['solar'],'fields':[x for x in FIELDS if x!='right.B.0'],
        'study_pdf':data_url(out/'RMO_uncertainty_diagnosis.pdf','application/pdf')}
    payload=json.dumps(config,separators=(',',':')).replace('<','\\u003c')
    script=(HERE/'client.js').read_text();assert '</script' not in script.lower()
    page=page.replace('The current connection supports a limited set of synthetic cases: uniform states, contacts, zero-field Euler problems and two exact rotation/tangential fixtures. It does not rerun the three Brio–Wu fans or the saved fast/slow diagnostic examples. A general MHD solve and an observed-event classification are not available through this connection.',
        'The Riemann-solver action retains its limited synthetic cases: uniform states, contacts, zero-field Euler problems and two exact rotation/tangential fixtures. The added <a href="#r75-tool">local-diagnosis action</a> checks edited two-state inputs, including fast/slow examples and bounded errors. It is a single-discontinuity diagnostic, not a full Riemann solve. The three Brio–Wu fans remain saved views; observed-event classification is not supplied by either action.',1)
    page=page.replace('</body>',f'<script id="r75-config" type="application/json">{payload}</script><script id="r75-client">{script}</script></body>',1)
    page=page.replace('Interface 0.4.6 · RMO-74', 'Interface 0.4.7 · RMO-75')
    page=page.replace('</style>',(HERE/'style.css').read_text()+'</style>',1)
    page=page.replace('RMO QuickLook — full workspace 0.4.6','RMO QuickLook — full workspace 0.4.7',1)
    page=page.replace('<footer>','<footer><p><strong>RMO-75 · Interface 0.4.7.</strong> Bounded local diagnosis, saved study, editable requests and optional Python calculation. The complete earlier workspace follows. Native browser acceptance remains open.</p>',1)
    return page
