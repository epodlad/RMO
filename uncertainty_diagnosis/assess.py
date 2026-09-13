"""Interval sufficient tests around a checked nominal local discontinuity.

No expected-family input, reference lookup, noise fitting or full-fan solve.
"""
import copy
from decimal import Decimal, localcontext
import importlib.util
import json
import math
from pathlib import Path
from local_diagnosis.diagnose import diagnose, finite
from .interval import I, D, characteristics

ROOT=Path(__file__).resolve().parents[1]
FIELDS=['front_speed']+[s+'.'+k for s in ('left','right') for k in ('rho','p','u.0','u.1','u.2','B.0','B.1','B.2')]

def get(req,path):
    obj=req
    for k in path.split('.'):
        if obj is None:return None
        obj=obj[int(k)] if isinstance(obj,list) else obj.get(k)
    return obj

def put(req,path,val):
    parts=path.split('.'); obj=req
    for k in parts[:-1]:obj=obj[int(k)] if isinstance(obj,list) else obj[k]
    k=parts[-1];obj[int(k) if isinstance(obj,list) else k]=val

def example_request(req,f):
    widths={k:abs(get(req,k))*f if k.endswith(('.rho','.p')) else max(1,abs(get(req,k)))*f for k in FIELDS}
    return {'schema_version':'rmo-bounded-local-0.1','nominal':copy.deepcopy(req),
            'half_widths':widths,'bounds_kind':'deterministic_box','fixed_geometry_and_gamma':True}

def independent(req,out):
    spec=importlib.util.spec_from_file_location('rmo75_decimal',ROOT/'verification/decimal_checks.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    with localcontext() as c:
        c.prec=70
        a,b=mod.state(req['left']),mod.state(req['right'])
        residual,_=mod.residual(a,b,mod.D(req['front_speed']),mod.D(req['gamma']))
        refs={k:mod.speeds(s,mod.D(req['gamma'])) for k,s in [('left',a),('right',b)]}
        diffs=[abs(float(x)-out['checks']['characteristics'][side][name]) for side,vals in refs.items() for name,x in zip(('fast','alfven_n','slow'),vals)]
        return {'status':'PASS' if residual<=Decimal('1e-10') and max(diffs)<1e-11 else 'FAIL',
                'method':'Independent 70-digit lab-frame Decimal conservation and characteristic arithmetic',
                'rh_scaled_inf':str(residual),'max_characteristic_difference':max(diffs)}

def interval_states(req,widths):
    iv={}
    for k in FIELDS:
        v=I(get(req,k));w=I(widths[k])
        iv[k]=I((v-w).lo,(v+w).hi) if widths[k] else v
    # Physical single-discontinuity model requires the same normal field.
    a,b=iv['left.B.0'],iv['right.B.0']
    bn=I(max(a.lo,b.lo),min(a.hi,b.hi))
    iv['left.B.0']=iv['right.B.0']=bn
    states={}
    for side in ('left','right'):
        states[side]={'rho':iv[side+'.rho'],'p':iv[side+'.p'],
                      'B':[iv[f'{side}.B.{i}'] for i in range(3)],
                      'u':[iv[f'{side}.u.{i}'] for i in range(3)]}
    return iv,states

def assess(env):
    out={'schema_version':'rmo-bounded-assessment-0.1','status':'NOT_CERTIFIED','family':None,
         'scope':'Single planar ideal-MHD discontinuity; fixed geometry and gamma',
         'global_uniqueness':False,'probability':None,'full_riemann_solve':False,
         'limitations':['A box is a deterministic bound, not a confidence level.',
                        'Failure to certify does not prove another feasible solution exists.',
                        'A conservation witness is not a best estimate, posterior or exhaustive search.',
                        'No geometry uncertainty or covariance inference.',
                        'No classification of EUV images, smooth waves or non-wave alternatives.']}
    def stop(status,text,next_):
        out.update(status=status,result_sentence=text,next_action=next_);return out
    allowed={'schema_version','nominal','half_widths','bounds_kind','fixed_geometry_and_gamma'}
    if not isinstance(env,dict) or set(env)-{'missing_reasons'}!=allowed or env.get('schema_version')!='rmo-bounded-local-0.1' or env.get('bounds_kind')!='deterministic_box' or env.get('fixed_geometry_and_gamma') is not True:
        return stop('INVALID_INPUT','Use the bounded local-input schema with fixed geometry and gamma.','Load a model input or export its example JSON.')
    reasons=env.get('missing_reasons',{})
    if not isinstance(reasons,dict) or any(k not in FIELDS or not isinstance(v,str) or len(v)>200 for k,v in reasons.items()):
        return stop('INVALID_INPUT','Missing-value explanations must refer to local input fields.','Use a short explanation for each unknown value.')
    req=env['nominal'];w=env['half_widths']
    if not isinstance(req,dict) or not isinstance(w,dict) or set(w)!=set(FIELDS) or not all(finite(x) and 0<=x<=1e12 for x in w.values()):
        return stop('INVALID_INPUT','Supply a finite nonnegative half-width for every input quantity.','Correct the indicated input or uncertainty width.')
    try:
        nominal=diagnose(req)
    except (TypeError,ValueError,KeyError,IndexError,OverflowError):
        return stop('INVALID_INPUT','The local-state input has an invalid structure.','Load an example to inspect the required fields.')
    out['nominal']=nominal
    if nominal['status']=='INSUFFICIENT_DATA':
        out['missing']=nominal['missing']
        return stop('MISSING_MEASUREMENTS','The local type is not determined: required measurements are missing.','Supply or constrain '+', '.join(nominal['missing'])+'. Unknown values remain unknown.')
    if 'characteristics' not in nominal['checks']:
        return stop(nominal['status'],nominal['result_sentence'],nominal['next_action'])
    out['independent_check']=independent(req,nominal)
    try:
        iv,states=interval_states(req,w)
        if any(s[k].lo<=D('1e-12') for s in states.values() for k in ('rho','p')):
            return stop('INVALID_BOUNDS','A density or pressure interval reaches zero or the numerical floor.','Use positive physical bounds; do not silently clip the interval.')
        cs={side:characteristics(s,I(req['gamma'])) for side,s in states.items()}
        out['characteristic_bounds']={side:{k:v.floats() for k,v in c.items()} for side,c in cs.items()}
        vel={side:s['u'][0]-iv['front_speed'] for side,s in states.items()}
        out['relative_speed_bounds']={k:v.floats() for k,v in vel.items()}
        out['input_bounds']={k:v.exact() for k,v in iv.items()}
        if not any(w.values()):
            if nominal['family'] and out['independent_check']['status']=='PASS':
                out['family']=nominal['family']
                return stop('EXACT_LOCAL_CLASS',nominal['result_sentence'],'Inspect the physical checks, then add bounded errors to test the classification.')
            return stop('NOMINAL_NOT_CHECKED',nominal['result_sentence'],'Review the model and inputs; no admissible nominal witness was established.')
        anchor=nominal
        if nominal['status']!='SUPPORTED_LOCAL_CLASS' or out['independent_check']['status']!='PASS':
            from .witness import search
            candidate,search_record=search(req,w,FIELDS,get,put)
            out['witness_search']=search_record
            if candidate is not None:
                inside=all(iv[k].contains(get(candidate,k)) for k in FIELDS)
                checked=diagnose(candidate)
                audit=independent(candidate,checked) if 'characteristics' in checked['checks'] else {'status':'NOT_CHECKED'}
                out['witness']={'input':candidate,'inside_box':inside,'diagnosis':checked,'independent_check':audit}
                if inside and checked['status']=='SUPPORTED_LOCAL_CLASS' and audit['status']=='PASS':
                    anchor=checked
                    out['witness_search']['status']='CHECKED_NUMERICAL_WITNESS'
        direction=1 if all(v.lo>0 for v in vel.values()) else (-1 if all(v.hi<0 for v in vel.values()) else 0)
        if not direction:
            return stop('NOT_CERTIFIED','The nominal result is available, but these bounds do not fix a nonzero mass-flow direction.','Constrain plasma normal velocity relative to the front. Contact equalities need a constrained uncertainty model.')
        up,down=('left','right') if direction==1 else ('right','left')
        a,b=states[up],states[down];vu=direction*vel[up];vd=direction*vel[down]
        cu,cd=cs[up],cs[down]
        r=b['rho']/a['rho']; ent=(b['p']/a['p']).ln()-I(req['gamma'])*r.ln()
        bt=lambda s:sum(x.square() for x in s['B'][1:]).sqrt()
        common={'compression - 1':r-1,'entropy increase':ent,
                'field alignment':sum(x*y for x,y in zip(a['B'][1:],b['B'][1:])),
                'nonzero upstream transverse field':bt(a),'nonzero downstream transverse field':bt(b),
                'nonzero normal field':a['B'][0].square().sqrt()}
        # For a²>0, Bn²>0 and Bt²>0, the magnetosonic polynomial at ca²
        # equals -ca²*Bt²/rho < 0: cs < ca < cf follows without subtracting
        # mutually dependent speed intervals.
        margins={
          'fast_shock':dict(common,**{'upstream flow - fast':vu-cu['fast'],
              'downstream fast - flow':cd['fast']-vd,'downstream flow - Alfven':vd-cd['alfven_n'],
              'transverse-field increase':bt(b)-bt(a)}),
          'slow_shock':dict(common,**{'upstream Alfven - flow':cu['alfven_n']-vu,
              'upstream flow - slow':vu-cu['slow'],'downstream slow - flow':cd['slow']-vd,
              'transverse-field decrease':bt(a)-bt(b)})}
        out['margins']={family:{k:{'bounds':v.floats(),'decimal_bounds':v.exact(),'strictly_positive':v.lo>0} for k,v in rows.items()} for family,rows in margins.items()}
        certified=[f for f,rows in margins.items() if all(v.lo>0 for v in rows.values())]
        out['sufficient_inequalities']=certified
        nf=anchor['family']
        out['unresolved_checks']=[k for k,v in margins.get(nf,{}).items() if v.lo<=0]
        has_anchor=(nominal['status']=='SUPPORTED_LOCAL_CLASS' and out['independent_check']['status']=='PASS') or out.get('witness_search',{}).get('status')=='CHECKED_NUMERICAL_WITNESS'
        if not has_anchor:
            return stop('SEARCH_INCOMPLETE','No checked conservation-compatible witness was obtained in this bounded search; the wave type remains unresolved.','Review the bounds and model. Exact equalities are sensitive to errors; search failure is not physical exclusion.')
        if len(certified)==1 and certified[0]==nf:
            out['family']=nf
            return stop('CONDITIONAL_ROBUST_CLASS',nf.replace('_',' ').capitalize()+' remains certified by the sufficient interval tests, conditional on a single conservation-compatible ideal-MHD discontinuity.','Inspect the bounds and assumptions. This is a local type certificate, not full-fan uniqueness or an observed EUV classification.')
        if nf in ('contact','rotational_discontinuity'):
            return stop('NOT_CERTIFIED','A '+nf.replace('_',' ')+' anchor is checked; a free error box does not establish its required equalities.','Use a constrained uncertainty model for equal density/pressure and Alfvenic relations, or normal mass flux for a contact.')
        return stop('NOT_CERTIFIED','A '+str(nf).replace('_',' ')+' anchor is checked, but these error bounds do not certify its type.','Tighten or jointly constrain: '+', '.join(out['unresolved_checks'])+'. This does not establish a competing feasible branch.')
    except (ValueError,ArithmeticError,OverflowError) as exc:
        return stop('INVALID_BOUNDS','The bounds could not be evaluated: '+str(exc),'Review physical ranges and the shared normal field.')

if __name__=='__main__':
    import sys
    print(json.dumps(assess(json.loads(Path(sys.argv[1]).read_text())),indent=2,allow_nan=False))
