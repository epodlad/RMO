"""Additive RMO77 exact perpendicular class; original diagnostic is unchanged.

No solver, reference input, case-name dispatch or expected label is imported.
This module is intentionally separate from the existing service and QuickLook.
"""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from local_diagnosis.diagnose import (
    diagnose as original_diagnose, close, vector_close, norm,
    VALUE_TOL, SPEED_TOL, ENTROPY_ALLOWANCE,
)


def diagnose(req):
    if not isinstance(req,dict):
        return {'status':'INVALID_INPUT','family':None,
                'result_sentence':'A local-discontinuity request object is required.'}
    try:
        original=original_diagnose(req)
    except (TypeError,AttributeError,ValueError,OverflowError) as error:
        return {'case_id':req.get('case_id'),'status':'INVALID_INPUT','family':None,
                'result_sentence':'Malformed fields or numerical values prevented input validation.',
                'error_type':type(error).__name__}
    # Successful oblique cases and all original validation failures are delegated
    # without changing their result or numerical criteria.
    if original['status']!='DEGENERATE_NOT_CLASSIFIED':
        return original
    if req['left']['B'][0]!=0 or req['right']['B'][0]!=0:
        return original
    out=deepcopy(original)
    out['diagnostic_extension']='RMO-exact-perpendicular-0.1'
    out['scope']='one exact planar ideal-MHD discontinuity; Bn=0, Bt nonzero, 1<gamma<2'
    out['geometry']='Bn=0 supplied; a field-to-normal angle requires a nonzero magnetic field'
    out['baseline_status']=original['status']
    out['solar_identification']=False
    out['uncertainty_propagated']=False
    out['global_uniqueness']=False
    out['stability_tested']=False

    def stop(status,sentence):
        out.update(status=status,family=None,result_sentence=sentence,
                   next_action='Inspect the stated limit or input failure; no full-fan or observational conclusion follows.')
        return out

    g=req['gamma']
    if not 1<g<2:
        return stop('UNSUPPORTED_PERPENDICULAR_GAMMA','This extension has been scoped to 1 < gamma < 2.')
    L,R=req['left'],req['right']
    if (close(L['rho'],R['rho']) and close(L['p'],R['p']) and
        vector_close(L['u'],R['u']) and vector_close(L['B'],R['B'])):
        return stop('NO_RESOLVED_JUMP','The supplied states have no resolved discontinuity.')
    un=[s['u'][0]-req['front_speed'] for s in (L,R)]
    c=out['checks']['characteristics']
    scale=max(1,*map(abs,un),c['left']['fast'],c['right']['fast'])
    tol=SPEED_TOL*scale
    if un==[0,0]:
        out['candidates']['fast_shock']={
            'status':'INCOMPATIBLE_FOR_EXACT_PAIR',
            'reason':'No mass crosses this exact boundary.'}
        return stop('TANGENTIAL_OR_CONTACT_LIMIT','No plasma crosses the supplied boundary; inspect the contact/tangential limit separately.')
    if min(map(abs,un))<=tol or un[0]*un[1]<=0:
        return stop('UNRESOLVED_MASS_FLOW','The flow direction is zero, too small or inconsistent for this shock test.')
    bt=[norm(s['B'][1:]) for s in (L,R)]
    if max(bt)==0:
        return stop('UNMAGNETIZED_LIMIT','The magnetic field is zero; this magnetic-shock extension does not assign a gas-shock class.')
    if min(bt)<=SPEED_TOL*max(1,*bt):
        return stop('UNRESOLVED_TANGENTIAL_FIELD','A resolved nonzero tangential field is required on both sides.')
    out['geometry']='exactly perpendicular as supplied: field along the front surface; not inferred from observations'
    out['field_to_normal_angle_degrees']={'left':90.0,'right':90.0}
    up,down,cu,cd,vu,vd=(L,R,c['left'],c['right'],un[0],un[1]) if un[0]>0 else (
        R,L,c['right'],c['left'],-un[1],-un[0])
    ratio=down['rho']/up['rho']
    entropy=math.log(down['p']/up['p'])-g*math.log(ratio)
    induction=vector_close([x/up['rho'] for x in up['B'][1:]],
                           [x/down['rho'] for x in down['B'][1:]])
    tangential_flow=vector_close(up['u'][1:],down['u'][1:])
    field_ratio=norm(down['B'][1:])/norm(up['B'][1:])
    checks={'upstream_side':'left' if un[0]>0 else 'right',
            'compression':ratio,'entropy_over_cv':entropy,
            'tangential_field_ratio':field_ratio,
            'Bt_over_rho_continuous':induction,'tangential_velocity_continuous':tangential_flow,
            'compressed':ratio>1+VALUE_TOL,
            'entropy_accepted':entropy>=ENTROPY_ALLOWANCE,
            'field_amplified':field_ratio>1+VALUE_TOL,
            'upstream_superfast':vu>cu['fast']+tol,
            'downstream_subfast':vd<cd['fast']-tol,
            'fast_margin_upstream':vu-cu['fast'],
            'fast_margin_downstream':cd['fast']-vd,
            'normal_slow_and_alfven_speeds':[cu['slow'],cu['alfven_n'],cd['slow'],cd['alfven_n']],
            'speed_tolerance':tol,'entropy_allowance':ENTROPY_ALLOWANCE}
    out['checks']['perpendicular']=checks
    if not (induction and tangential_flow):
        return stop('UNRESOLVED_PERPENDICULAR_INVARIANTS','The perpendicular mass-flow invariants do not resolve within tolerance.')
    admissible=all(checks[k] for k in ('compressed','entropy_accepted','field_amplified',
                                      'upstream_superfast','downstream_subfast'))
    if not admissible:
        out['candidates']['fast_shock']={
            'status':'INCOMPATIBLE_OR_UNRESOLVED_FOR_EXACT_PAIR',
            'reason':'Compression, entropy or the separated fast-speed crossing failed; inspect the individual checks.'}
        return stop('NO_SUPPORTED_PERPENDICULAR_FAST_SHOCK','The supplied pair does not pass all perpendicular fast-shock tests; other interpretations have not been evaluated.')
    out['candidates']['fast_shock']={
        'status':'SUPPORTED',
        'reason':'Full RH, compression, nondecreasing entropy and super-fast to sub-fast normal-flow transition pass.'}
    out.update(status='SUPPORTED_LOCAL_CLASS',family='fast_shock',
               geometry_subtype='perpendicular',
               result_sentence='A fast shock passes conservation, entropy and characteristic-speed checks for these exact states; the field lies along the front surface (90 degrees to its normal).',
               next_action='Assess measurement errors and geometry before applying this local result to an observed front.')
    return out


if __name__=='__main__':
    request=json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(diagnose(request),indent=2,allow_nan=False))
