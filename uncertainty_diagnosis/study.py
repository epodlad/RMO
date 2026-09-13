"""Reproducible RMO-75 bounded study. Run from project root with -m."""
import copy
from decimal import localcontext
import hashlib
import importlib.util
import json
import random
from pathlib import Path
from .assess import ROOT,FIELDS,get,put,example_request,assess,interval_states
from .interval import I,D,characteristics

OUT=ROOT/'results/uncertainty_diagnosis'
def run():
    tests=[]
    def check(name,ok):
        tests.append({'name':name,'status':'PASS' if ok else 'FAIL'})
        if not ok:raise AssertionError(name)
    inputs={p.stem:json.loads(p.read_text()) for p in sorted((ROOT/'local_diagnosis/inputs').glob('*.json'))}
    cases=[]
    # All output is computed before a historical expected-family file is opened.
    for key,req in inputs.items():
        for f in [0,.01,.05,.10]:
            env=example_request(req,f);out=assess(env)
            cases.append({'id':key,'factor':f,'input':env,'output':out})
    reference=json.loads((ROOT/'local_diagnosis/scoring_reference.json').read_text())
    labelmap={'slow':'slow_shock','fast':'fast_shock','contact':'contact','alfven_plus':'rotational_discontinuity'}
    expected={r['case_id']:labelmap[r['reference_family']] for r in reference}
    for row in cases:
        o=row['output'];key=row['id']
        check(key+f" factor {row['factor']}: no unsupported certified label",o['family'] in (None,expected[key]))
        check(key+f" factor {row['factor']}: independent nominal arithmetic",o['independent_check']['status']=='PASS')
        if row['factor']==0:check(key+' exact reference',o['family']==expected[key])
    # Independent point arithmetic validates enclosures, not statistical accuracy.
    spec=importlib.util.spec_from_file_location('r75_verify_decimal',ROOT/'verification/decimal_checks.py')
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    rng=random.Random(750019);sample_count=0
    for row in cases:
        if row['factor']==0:continue
        env=row['input'];iv,states=interval_states(env['nominal'],env['half_widths'])
        c={s:characteristics(state,I(env['nominal']['gamma'])) for s,state in states.items()}
        with localcontext() as ctx:
            ctx.prec=80
            for _ in range(32):
                point=copy.deepcopy(env['nominal'])
                for k in FIELDS:
                    t=D(rng.randrange(0,1000001))/D(1000000)
                    put(point,k,str(iv[k].lo+(iv[k].hi-iv[k].lo)*t))
                point['right']['B'][0]=point['left']['B'][0]
                for s in ['left','right']:
                    vals=ref.speeds(ref.state(point[s]),ref.D(point['gamma']))
                    if not all(c[s][name].contains(v) for name,v in zip(['fast','alfven_n','slow'],vals)):
                        raise AssertionError('Characteristic enclosure failure')
                sample_count+=1
        check(f"{row['id']} {row['factor']}: independent 80-digit sample enclosures",True)
    controls=[]
    for key,req in inputs.items():
        for k in ['front_speed','left.B.0','right.p']:
            env=example_request(req,.01);put(env['nominal'],k,None);o=assess(env)
            check(key+' missing '+k,o['status']=='MISSING_MEASUREMENTS' and o['family'] is None)
            controls.append({'id':key,'control':'missing '+k,'input':env,'output':o})
    for key in ['A17','A63']:
        req=inputs[key];env=example_request(req,.01)
        env['nominal']['right']['p']*=1.0025
        o=assess(env)
        check(key+' noisy centre fails exact equality',o['nominal']['status']=='INCONSISTENT_SINGLE_DISCONTINUITY')
        check(key+' witness independently checked',o.get('witness',{}).get('independent_check',{}).get('status')=='PASS')
        check(key+' noisy bounded certificate',o['status']=='CONDITIONAL_ROBUST_CLASS' and o['family']==expected[key])
        controls.append({'id':key,'control':'pressure centre shifted +0.25%; width 1%','input':env,'output':o})
        for kind in ['shared_boost','normal_reversal']:
            env=example_request(req,.01)
            if kind=='shared_boost':
                env['nominal']['front_speed']+=2
                for side in ['left','right']:env['nominal'][side]['u'][0]+=2
            else:
                a=env['nominal'];a['left'],a['right']=a['right'],a['left'];a['front_speed']*=-1
                a['basis']={'normal':[-1,0,0],'t1':[0,1,0],'t2':[0,0,-1]}
                old=env['half_widths'].copy()
                for side,other in [('left','right'),('right','left')]:
                    for v in ['u','B']:a[side][v]=[-a[side][v][0],a[side][v][1],-a[side][v][2]]
                    for k in FIELDS:
                        if k.startswith(side+'.'):env['half_widths'][k]=old[other+k[len(side):]]
            o=assess(env);check(key+' '+kind,o['family']==expected[key] and o['status']=='CONDITIONAL_ROBUST_CLASS')
    env=example_request(inputs['A17'],.01);env['half_widths']['left.p']=-1
    check('Negative width rejected',assess(env)['status']=='INVALID_INPUT')
    env=example_request(inputs['A17'],.01);env['half_widths']['left.p']=1
    check('Nonpositive pressure range rejected',assess(env)['status']=='INVALID_BOUNDS')
    env=example_request(inputs['A63'],.01);env['nominal']['expected_family']='fast'
    check('Reference label injection rejected',assess(env)['status']=='INVALID_INPUT')
    env=example_request(inputs['A63'],0);env['nominal']['right']['p']*=1.01
    check('No-width inconsistent input not repaired',assess(env)['status']=='NOMINAL_NOT_CHECKED')
    # Pressure information sensitivity: tighten only pressure widths, holding all
    # other widths fixed. A useful sufficient improvement, not a global optimum.
    for key in ['A17','A63']:
        env=example_request(inputs[key],.05 if key=='A17' else .10)
        for s in ['left','right']:env['half_widths'][s+'.p']=.01*inputs[key][s]['p']
        o=assess(env);controls.append({'id':key,'control':'pressure widths tightened to 1%, others unchanged','input':env,'output':o})
    solar=json.loads((ROOT/'science_readiness/published_arithmetic_check.json').read_text())
    sr=[]
    for r in solar['rows']:
        sr.append({'point':r['point'],'apparent_speed_km_s':r['apparent_pattern_speed_km_s'],
                   'surface_pattern_speed_km_s':r['surface_pattern_speed_km_s'],
                   'reduction_relative_to_apparent_percent':100*(1-r['surface_pattern_speed_km_s']/r['apparent_pattern_speed_km_s'])})
    solar_output={'event':'2009-02-13','source':'T. Podladchikova et al. (2019), ApJ 877, 68',
        'doi':'10.3847/1538-4357/ab1b3a','same_selected_patch_confirmed_by_author':True,
        'rows':sr,'result_sentence':'Geometry changes the inferred surface pattern speed; these tables alone do not determine an MHD shock type.',
        'family':None,'missing':['local front normal and its uncertainty','normal front speed in the selected local frame',
        'co-spatial density and thermal pressure on both sides','plasma velocities and vector magnetic fields on both sides','joint observational uncertainty'],
        'limits':'Pattern motion is not plasma normal velocity; height change is not an independently recovered shock-normal speed. No new raw observations or assumed plasma state.'}
    report={'checkpoint':'RMO-75','status':'PASS','tests':tests,'test_count':len(tests),'independent_enclosure_points':sample_count,
        'design':'Four development fixtures; deterministic boxes, not probabilities or an external blind validation sample.',
        'cases':cases,'controls':controls,'solar':solar_output}
    report['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'uncertainty_diagnosis').glob('*.py'))+[ROOT/'uncertainty_diagnosis/PROTOCOL.md']}
    (OUT/'study.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for row in cases:
        (OUT/f"{row['id']}_{int(row['factor']*100):02d}_request.json").write_text(json.dumps(row['input'],indent=2)+'\n')
    print(json.dumps({'status':'PASS','tests':len(tests),'enclosure_points':sample_count,
        'cases':[(r['id'],r['factor'],r['output']['status']) for r in cases],
        'pressure_controls':[(r['id'],r['output']['status'],r['output'].get('unresolved_checks')) for r in controls if 'tightened' in r['control']]}))

if __name__=='__main__':run()
