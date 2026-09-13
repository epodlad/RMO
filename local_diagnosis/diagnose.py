"""Local ideal-MHD discontinuity diagnosis from two states; no Riemann solve.

No fixture, expected label, scoring record or production solver is imported.
All vector components refer to the supplied oriented orthonormal local basis.
"""
import copy
import json
import math
from pathlib import Path
import sys

RH_TOL = 1e-10
VALUE_TOL = 5e-9
BN_TOL = 1e-12
SPEED_TOL = 1e-9
ENTROPY_ALLOWANCE = -1e-10
FAMILIES = ('fast_shock', 'slow_shock', 'rotational_discontinuity', 'contact')

def dot(a, b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def close(a,b,tol=VALUE_TOL): return abs(a-b) <= tol*max(1,abs(a),abs(b))
def vector_close(a,b): return all(close(x,y) for x,y in zip(a,b))
def finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def speeds(s,g):
    a2=g*s['p']/s['rho']; b2=dot(s['B'],s['B'])/s['rho']
    ca2=s['B'][0]**2/s['rho']
    cf2=(a2+b2+math.sqrt(max(0,(a2+b2)**2-4*a2*ca2)))/2
    return {'slow':math.sqrt(a2*ca2/cf2), 'alfven_n':math.sqrt(ca2), 'fast':math.sqrt(cf2)}

def flux(s,g):
    rho,p,u,B=s['rho'],s['p'],s['u'],s['B']
    pt=p+dot(B,B)/2; E=p/(g-1)+rho*dot(u,u)/2+dot(B,B)/2
    return [rho*u[0], rho*u[0]**2+pt-B[0]**2,
            rho*u[0]*u[1]-B[0]*B[1],rho*u[0]*u[2]-B[0]*B[2],
            u[0]*B[1]-u[1]*B[0],u[0]*B[2]-u[2]*B[0],
            (E+pt)*u[0]-B[0]*dot(u,B)]

def region(v,c):
    t=SPEED_TOL*max(1,v,*c.values())
    if any(abs(v-x)<=t for x in c.values()):return 'boundary'
    if v>c['fast']:return 1
    if v>c['alfven_n']:return 2
    if v>c['slow']:return 3
    return 4

def diagnose(req):
    out={'case_id':req.get('case_id'), 'status':'NOT_ASSESSED', 'family':None,
         'scope':'one planar discontinuity, ideal MHD, exact supplied states',
         'candidates':{k:{'status':'NOT_ASSESSED','reason':'Required checks not completed.'} for k in FAMILIES},
         'coverage':{'intermediate_switch_limits':'NOT_IMPLEMENTED; never automatically excluded',
                     'full_fan_and_compound':'NOT_TESTED by a two-state discontinuity check',
                     'smooth_waves_and_image_alternatives':'NOT_TESTED; require their own spatial/observational model'},
         'global_uniqueness':False,'uncertainty_propagated':False,'checks':{}}
    def stop(status,reason):
        out.update(status=status,result_sentence=reason,next_action=reason);return out
    allowed={'schema_version','case_id','model','units','gamma','basis','frame','front_speed','left','right','uncertainty'}
    if set(req)-allowed:return stop('INVALID_INPUT','Unexpected input fields; family labels and reference metadata are not diagnostic inputs.')
    if req.get('schema_version')!='rmo-local-discontinuity-0.1' or req.get('model')!='ideal_mhd_single_planar_discontinuity' or req.get('units')!='normalized_mu0_1' or req.get('frame')!='common_inertial_local_basis':
        return stop('UNSUPPORTED_INPUT','Use the declared ideal-MHD local-state schema, common frame and normalized units.')
    missing=[]
    if req.get('gamma') is None:missing.append('gamma')
    if req.get('front_speed') is None:missing.append('front_speed')
    for side in ('left','right'):
        s=req.get(side)
        if not isinstance(s,dict):missing.append(side);continue
        if set(s)-{'rho','p','u','B'}:return stop('INVALID_INPUT','States must contain only rho, p, u and B.')
        for k in ('rho','p'):
            if s.get(k) is None:missing.append(side+'.'+k)
        for k in ('u','B'):
            v=s.get(k)
            if v is None:missing.append(side+'.'+k)
            elif not isinstance(v,list) or len(v)!=3:return stop('INVALID_INPUT','Velocity and magnetic field each require three components.')
            else:missing.extend(side+'.'+k+f'[{i}]' for i,x in enumerate(v) if x is None)
    if missing:
        out['missing']=missing
        return stop('INSUFFICIENT_DATA','Supply or constrain: '+', '.join(missing)+'. Missing values were not replaced by zero.')
    L,R=copy.deepcopy(req['left']),copy.deepcopy(req['right']);g=req['gamma'];S=req['front_speed']
    values=[g,S]+[x for s in (L,R) for x in [s['rho'],s['p'],*s['u'],*s['B']]]
    if not all(finite(x) for x in values) or g<=1 or any(s['rho']<=0 or s['p']<=0 for s in (L,R)):
        return stop('INVALID_INPUT','Finite states with positive density and pressure and gamma > 1 are required.')
    if any(s['rho']<=1e-12 or s['p']<=1e-12 for s in (L,R)) or max(map(abs,values))>1e12:
        return stop('OUTSIDE_NUMERIC_DOMAIN','State scales are outside the declared numerical range.')
    basis=req.get('basis',{});vectors=[basis.get(k) for k in ('normal','t1','t2')]
    if any(not isinstance(v,list) or len(v)!=3 or not all(finite(x) for x in v) for v in vectors):
        return stop('INVALID_INPUT','Supply all three vectors of the oriented local basis.')
    n,t1,t2=vectors;cross=[n[1]*t1[2]-n[2]*t1[1],n[2]*t1[0]-n[0]*t1[2],n[0]*t1[1]-n[1]*t1[0]]
    if any(not close(dot(a,b),int(i==j),1e-10) for i,a in enumerate(vectors) for j,b in enumerate(vectors)) or not vector_close(cross,t2):
        return stop('INVALID_INPUT','The local basis must be orthonormal and right handed.')
    if req.get('uncertainty',{}).get('mode')!='exact_synthetic':
        return stop('UNCERTAINTY_NOT_IMPLEMENTED','This diagnostic does not yet propagate measurement errors or covariance.')
    if not close(L['B'][0],R['B'][0],BN_TOL):
        return stop('INCONSISTENT_BN','The two normal magnetic fields disagree beyond the declared tolerance.')
    # Stationary-front frame, with shared tangential boost removed for conditioning.
    boost=[S,(L['u'][1]+R['u'][1])/2,(L['u'][2]+R['u'][2])/2]
    for s in (L,R):s['u']=[x-v for x,v in zip(s['u'],boost)]
    fL,fR=flux(L,g),flux(R,g)
    residual=[(b-a)/max(1,abs(a),abs(b)) for a,b in zip(fL,fR)]
    rh=max(map(abs,residual));cL,cR=speeds(L,g),speeds(R,g)
    out['checks']={'front_speed':S,'evaluation_boost':boost,'rh_scaled_inf':rh,
                   'rh_components':dict(zip(('mass','normal_momentum','t1_momentum','t2_momentum','t1_induction','t2_induction','energy'),residual)),
                   'characteristics':{'left':cL,'right':cR},
                   'front_relative_normal_velocity':{'left':L['u'][0],'right':R['u'][0]}}
    if rh>RH_TOL:return stop('INCONSISTENT_SINGLE_DISCONTINUITY','The supplied states and speed fail conservation for one stationary planar discontinuity; no wave family is assigned.')
    speedscale=max(1,abs(L['u'][0]),abs(R['u'][0]),*cL.values(),*cR.values())
    zero_flux=max(abs(L['u'][0]),abs(R['u'][0]))<=SPEED_TOL*speedscale
    bt=[norm(s['B'][1:]) for s in (L,R)]
    if abs(L['B'][0])<=SPEED_TOL*max(1,norm(L['B']),norm(R['B'])):
        return stop('DEGENERATE_NOT_CLASSIFIED','The normal field vanishes or is too small for this diagnostic; tangential and degenerate limits need separate treatment.')
    thermo=close(L['rho'],R['rho']) and close(L['p'],R['p'])
    contact=zero_flux and close(L['p'],R['p']) and vector_close(L['u'],R['u']) and vector_close(L['B'],R['B']) and not close(L['rho'],R['rho'])
    same=thermo and vector_close(L['u'],R['u']) and vector_close(L['B'],R['B'])
    if same:return stop('NO_RESOLVED_JUMP','The supplied states are equal within tolerance; no finite discontinuity is resolved.')
    mL,mR=L['rho']*L['u'][0],R['rho']*R['u'][0]
    m=(mL+mR)/2
    rotation=(not zero_flux and thermo and close(L['u'][0],R['u'][0]) and close(bt[0],bt[1])
              and not vector_close(L['B'][1:],R['B'][1:]) and close(m*m,L['rho']*L['B'][0]**2)
              and all(close(m*(R['u'][i]-L['u'][i]),L['B'][0]*(R['B'][i]-L['B'][i])) for i in (1,2)))
    fast=slow=False
    if not zero_flux:
        if L['u'][0]*R['u'][0]<=0:return stop('UNRESOLVED_FLOW_ORDER','The mass-flow direction is not resolved consistently on both sides.')
        up,down=(L,R) if m>0 else (R,L)
        cu,cd=(cL,cR) if m>0 else (cR,cL)
        compression=down['rho']/up['rho'];entropy=math.log(down['p']/up['p'])-g*math.log(compression)
        ru,rd=region(abs(up['u'][0]),cu),region(abs(down['u'][0]),cd)
        out['checks'].update(upstream_side='left' if m>0 else 'right',characteristic_transition=[ru,rd],compression=compression,
                             pressure_ratio=down['p']/up['p'],entropy_over_cv=entropy,
                             tangential_field_ratio=norm(down['B'][1:])/norm(up['B'][1:]) if norm(up['B'][1:]) else None)
        degenerate=any(abs(c['fast']-c['alfven_n'])<=SPEED_TOL*speedscale or abs(c['alfven_n']-c['slow'])<=SPEED_TOL*speedscale for c in (cu,cd)) or min(bt)<=SPEED_TOL*max(1,*bt)
        if not rotation and (degenerate or ru=='boundary' or rd=='boundary'):
            return stop('DEGENERATE_NOT_CLASSIFIED','A characteristic boundary or switch limit needs separate treatment; no ordinary shock family is assigned.')
        compressed=compression>1+VALUE_TOL;entropy_ok=entropy>=ENTROPY_ALLOWANCE
        aligned=dot(up['B'][1:],down['B'][1:])>0
        fast=compressed and entropy_ok and (ru,rd)==(1,2) and aligned and norm(down['B'][1:])>norm(up['B'][1:])
        slow=compressed and entropy_ok and (ru,rd)==(3,4) and aligned and norm(down['B'][1:])<norm(up['B'][1:])
    else:out['checks']['upstream_side']=None
    flags={'fast_shock':fast,'slow_shock':slow,'rotational_discontinuity':rotation,'contact':contact}
    reasons={'fast_shock':'Requires compression, nondecreasing entropy and the 1 to 2 characteristic transition.',
             'slow_shock':'Requires compression, nondecreasing entropy and the 3 to 4 characteristic transition.',
             'rotational_discontinuity':'Requires unchanged density/pressure and Alfvenic field/velocity rotation.',
             'contact':'Requires zero normal mass flux, continuous pressure/velocity/field and a density jump.'}
    for name,ok in flags.items():out['candidates'][name]={'status':'SUPPORTED' if ok else 'INCOMPATIBLE_FOR_EXACT_PAIR','reason':reasons[name]}
    selected=[x for x,ok in flags.items() if ok]
    if len(selected)!=1:return stop('OTHER_OR_UNRESOLVED','No single supported family among the four implemented local classes; other structures are not excluded.')
    family=selected[0];out.update(status='SUPPORTED_LOCAL_CLASS',family=family)
    sentences={'fast_shock':'For these supplied states and front speed, a fast shock passes the local ideal-MHD checks.',
               'slow_shock':'For these supplied states and front speed, a slow shock passes the local ideal-MHD checks.',
               'rotational_discontinuity':'For these supplied states and front speed, an Alfvenic rotational discontinuity passes the local checks.',
               'contact':'For these supplied states, a contact moves with the plasma while density changes and pressure, velocity and field remain continuous.'}
    out['result_sentence']=sentences[family]
    out['next_action']='Next assess uncertainty and unresolved spatial structure; this exact-state result does not classify an EUV image or establish full-fan uniqueness.'
    return out

if __name__=='__main__':
    request=json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(diagnose(request),indent=2,allow_nan=False))
