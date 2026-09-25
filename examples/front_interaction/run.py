"""Connected two-front interaction benchmark. No solar-state inversion.

Incoming: L | fast+ shock | M | slow+ shock | R.
At their meeting, solve the NEW Riemann problem with the SAME exterior L/R.
All seven regular families are available; outgoing strengths are solved.
Units: mu0=1, gamma=5/3; no solar speed/deprojection scale is assigned.
"""
from pathlib import Path
from dataclasses import replace
import os, sys, json, math, hashlib
import numpy as np

ROOT = Path(__file__).resolve().parent
IMPL = Path(os.environ.get('RMO_IMPLEMENTATION', str(ROOT.parents[1] / 'implementation')))
sys.path.insert(0, str(IMPL))
from rmo.models import State
from rmo.physics import characteristic_speeds, conservative, flux
from rmo.wave_curves import (solve_magnetosonic_to_pressure, solve_rarefaction_to_pressure,
    analytic_pressure_tangent, primitive_vector, state_from_primitive)
from rmo.regular_fan import search_regular_fans_stabilized

GAMMA = 5/3
OUT = ROOT/'results'
OUT.mkdir(exist_ok=True, parents=True)

def vec(s):
    return np.array([s.rho, *s.u, s.B[1], s.B[2], s.p])

def qf(z, bn):
    """Independent vectorized conservative variables/flux, no RMO call."""
    rho=z[...,0]; u=z[...,1:4]; bt=z[...,4:6]; p=z[...,6]
    b=np.concatenate([np.full(rho.shape+(1,),bn),bt],axis=-1)
    b2=np.sum(b*b,axis=-1); pt=p+b2/2
    e=p/(GAMMA-1)+rho*np.sum(u*u,axis=-1)/2+b2/2
    q=np.concatenate([rho[...,None],rho[...,None]*u,bt,e[...,None]],axis=-1)
    f=np.empty_like(q)
    f[...,0]=rho*u[...,0]
    f[...,1:4]=rho[...,None]*u[...,0,None]*u-bn*b
    f[...,1]+=pt
    f[...,4:6]=u[...,0,None]*bt-bn*u[...,1:3]
    f[...,6]=(e+pt)*u[...,0]-bn*np.sum(u*b,axis=-1)
    return q,f

def from_q(q,bn):
    rho=q[...,0]; u=q[...,1:4]/rho[...,None]; bt=q[...,4:6]
    p=(GAMMA-1)*(q[...,6]-rho*np.sum(u*u,axis=-1)/2-(bn*bn+np.sum(bt*bt,axis=-1))/2)
    return np.concatenate([rho[...,None],u,bt,p[...,None]],axis=-1)

def cf(z,bn):
    a2=GAMMA*z[...,6]/z[...,0]
    b2=(bn*bn+np.sum(z[...,4:6]**2,axis=-1))/z[...,0]
    return np.sqrt(.5*(a2+b2+np.sqrt(np.maximum(0,(a2+b2)**2-4*a2*bn*bn/z[...,0]))))

def jump_audit(left,right,speed,structure,family):
    ql,fl=qf(vec(left),left.B[0]); qr,fr=qf(vec(right),right.B[0])
    a=fl-speed*ql; b=fr-speed*qr
    scale=np.maximum(1,np.maximum(abs(a),abs(b)))
    j=left.rho*(left.u[0]-speed)
    entropy_lr=math.log(right.p/left.p)-GAMMA*math.log(right.rho/left.rho)
    out={'flux_minus_speed_q_left':a.tolist(),'flux_minus_speed_q_right':b.tolist(),
         'rh_max_scaled':float(max(abs(b-a)/scale)),
         'entropy_right_minus_left_over_cv':entropy_lr,
         'entropy_flux_production_over_cv':float(j*entropy_lr),
         'mass_flux':float(j), 'density_jump_right_minus_left':right.rho-left.rho}
    if structure=='shock':
        k={'fast_minus':0,'slow_minus':2,'slow_plus':4,'fast_plus':6}[family]
        el=np.array(characteristic_speeds(left,GAMMA)['eigenvalues'])
        er=np.array(characteristic_speeds(right,GAMMA)['eigenvalues'])
        margins=[el[k]-speed,speed-er[k]]
        if k>0:margins.append(speed-el[k-1])
        if k<6:margins.append(er[k+1]-speed)
        out['lax_margins']=list(map(float,margins));out['strict_lax_pass']=bool(min(margins)>1e-9)
        up,down=(left,right) if j>0 else (right,left)
        out['entropy_down_minus_up_over_cv']=math.log(down.p/up.p)-GAMMA*math.log(down.rho/up.rho)
        out['compression']=down.rho/up.rho
        assert out['strict_lax_pass'] and out['compression']>1 and out['entropy_flux_production_over_cv']>0
    if structure=='contact':
        out['contact_matching_max']=max(abs(left.p-right.p),*abs(np.array(left.u)-right.u),*abs(np.array(left.B)-right.B))
        out['entropy_jump_is_not_shock_production']=True
        assert abs(j)<1e-10 and out['contact_matching_max']<1e-10
    assert out['rh_max_scaled']<1e-10
    return out

def rare_samples(w):
    direction=-1 if w.family.endswith('minus') else 1
    family=w.family.split('_')[0]
    up,down=(w.left_state,w.right_state) if direction<0 else (w.right_state,w.left_state)
    samples=[];ent=[];errs=[]
    for pressure in np.linspace(up.p,down.p,81):
        s=solve_rarefaction_to_pressure(up,float(pressure),GAMMA,family,direction).downstream
        xi=s.u[0]+direction*characteristic_speeds(s,GAMMA)[family]
        z=vec(s); tangent=np.r_[s.rho/(GAMMA*s.p),analytic_pressure_tangent(s,GAMMA,family,direction),1.]
        residual=np.zeros(7)
        for k in range(7):
            h=1e-6*max(1,abs(z[k])); dz=np.zeros(7);dz[k]=h
            qp,fp=qf(z+dz,s.B[0]);qm,fm=qf(z-dz,s.B[0])
            residual+=(fp-fm-xi*(qp-qm))/(2*h)*tangent[k]
        errs.append(float(max(abs(residual))))
        ent.append(abs(math.log(s.p/up.p)-GAMMA*math.log(s.rho/up.rho)))
        samples.append({'xi':float(xi),'primitive':z.tolist()})
    samples.sort(key=lambda s:s['xi'])
    assert np.all(np.diff([s['xi'] for s in samples])>0)
    assert max(errs)<1e-8 and max(ent)<1e-12
    return samples,{'isentropic_max_error':max(ent),'fd_characteristic_max_error':max(errs),
                    'monotonic_characteristic_speed':True,'sample_count':len(samples)}

def sample_after(xi,solution,rare):
    a=np.tile(vec(solution.waves[0].left_state),(len(xi),1))
    for w in solution.waves:
        if w.structure=='rarefaction':
            lo,hi=w.speed; mask=(xi>=lo)&(xi<=hi)
            r=rare[w.family];sx=[s['xi'] for s in r];sz=np.array([s['primitive'] for s in r])
            for k in range(7):a[mask,k]=np.interp(xi[mask],sx,sz[:,k])
            a[xi>hi]=vec(w.right_state)
        else:a[xi>w.speed]=vec(w.right_state)
    return a

def finite_volume(n,tend,L,M,R,collision_time,collision_position,solution,rare):
    """MUSCL minmod + HLL + SSPRK2. Initial states are L/M/R, not post-fan."""
    bn=R.B[0]; xmin,xmax=-3.,4.;dx=(xmax-xmin)/n
    x=xmin+(np.arange(n)+.5)*dx
    z=np.where((x<-1)[:,None],vec(L),np.where((x<0)[:,None],vec(M),vec(R)))
    q,_=qf(z,bn); t=0.;count=0
    total0=q.sum(axis=0)*dx; integrated_flux=np.zeros(7)
    minrho=float(z[:,0].min());minp=float(z[:,6].min())
    def rhs(q):
        z=from_q(q,bn)
        assert z[:,0].min()>0 and z[:,6].min()>0
        z=np.pad(z,((2,2),(0,0)),mode='edge')
        dl=z[1:-1]-z[:-2];dr=z[2:]-z[1:-1]
        slopes=np.where(dl*dr>0,np.sign(dl)*np.minimum(abs(dl),abs(dr)),0)
        zl=z[1:-2]+slopes[:-1]/2;zr=z[2:-1]-slopes[1:]/2
        ql,fl=qf(zl,bn);qr,fr=qf(zr,bn)
        sl=np.minimum(0,np.minimum(zl[:,1]-cf(zl,bn),zr[:,1]-cf(zr,bn)))
        sr=np.maximum(0,np.maximum(zl[:,1]+cf(zl,bn),zr[:,1]+cf(zr,bn)))
        f=(sr[:,None]*fl-sl[:,None]*fr+(sl*sr)[:,None]*(qr-ql))/(sr-sl)[:,None]
        return -(f[1:]-f[:-1])/dx,f[0]-f[-1]
    while t<tend-1e-14:
        z=from_q(q,bn); dt=min(.35*dx/np.max(abs(z[:,1])+cf(z,bn)),tend-t)
        r1,b1=rhs(q); stage=q+dt*r1;r2,b2=rhs(stage)
        q=.5*q+.5*(stage+dt*r2);integrated_flux+=.5*dt*(b1+b2)
        t+=dt;count+=1
        z=from_q(q,bn);minrho=min(minrho,float(z[:,0].min()));minp=min(minp,float(z[:,6].min()))
    exact=sample_after((x-collision_position)/(tend-collision_time),solution,rare)
    conservation=max(abs(q.sum(axis=0)*dx-total0-integrated_flux))
    l1=np.mean(abs(z-exact),axis=0)
    return {'cells':n,'steps':count,'final_time':t,'mean_L1_primitive_errors':l1.tolist(),
            'max_mean_L1':float(max(l1)), 'conservation_balance_max_absolute':float(conservation),
            'minimum_density':minrho,'minimum_pressure':minp}, x,z,exact

def main():
    R=State(1.,.6,(0.,0.,0.),(.7871875397721321,.6913872842586856,0.),id='RIGHT',role='initial_right')
    slow=solve_magnetosonic_to_pressure(R,.66,GAMMA,'slow',1,search_starts=True)
    M=replace(slow.downstream,id='MIDDLE',role='initial_middle')
    fast=solve_magnetosonic_to_pressure(M,.726,GAMMA,'fast',1,search_starts=True)
    L=replace(fast.downstream,id='LEFT',role='initial_left')
    assert fast.speed>slow.speed>0
    tc=1/(fast.speed-slow.speed);xc=slow.speed*tc
    incoming=[{'family':'fast_plus','structure':'shock','speed':fast.speed,'initial_position':-1.,
               'left_state':'LEFT','right_state':'MIDDLE','audit':jump_audit(L,M,fast.speed,'shock','fast_plus')},
              {'family':'slow_plus','structure':'shock','speed':slow.speed,'initial_position':0.,
               'left_state':'MIDDLE','right_state':'RIGHT','audit':jump_audit(M,R,slow.speed,'shock','slow_plus')}]
    search=search_regular_fans_stabilized(L,R,GAMMA,base_starts=4,wall_time_seconds=45.)
    assert search.solutions,'No admissible solution in tested starts'
    solution=search.solutions[0]; rare={};audits=[]
    for w in solution.waves:
        strength=float(max(abs(vec(w.right_state)-vec(w.left_state))))
        if w.structure=='rarefaction':rare[w.family],a=rare_samples(w)
        else:a=jump_audit(w.left_state,w.right_state,float(w.speed),w.structure,w.family)
        audits.append({'family':w.family,'structure':w.structure,'max_primitive_jump':strength,
                       'nonzero_above_1e_9':strength>1e-9,'checks':a})
    tend=tc+.6; reports=[]
    for n in [1200,2400]:
        report,x,z,exact=finite_volume(n,tend,L,M,R,tc,xc,solution,rare)
        reports.append(report);print('FV',json.dumps(report),flush=True)
    assert reports[-1]['max_mean_L1']<reports[0]['max_mean_L1']
    assert reports[-1]['conservation_balance_max_absolute']<1e-10
    np.savez_compressed(OUT/'finite_volume_comparison.npz',x=x,numerical=z,exact=exact)
    record={'format':'RMO-connected-interaction-0.1','scientific_status':'DIMENSIONLESS_INTERACTION_BENCHMARK',
      'event_reconstructed':False,
      'gamma':GAMMA,'mu0':1.,'primitive_order':['rho','un','ut1','ut2','Bt1','Bt2','p'],
      'normal_axis':'x','common_Bn':R.B[0],
      'normalization':{'rho_scale':1.,'velocity_scale':1.,'length_scale':1.,'solar_units_assigned':False},
      'assumptions':['One planar normal, ideal isotropic MHD, no conduction, gravity or continuing driver.',
        'Prescribed dimensionless ambient density, pressure, velocity and magnetic field; no solar calibration.',
        'Two incoming right-going shocks and pressure ratios 1.1 are prescribed hypotheses, not observed classifications.',
        'Initially coplanar u and B; zero outgoing rotations are a result for these boundary states.',
        'Finite jump separation is one arbitrary length unit; no observational collision fit has been made.'],
      'before_interaction_IVP':{'time':0.,'states_left_to_right':[s.serializable() for s in [L,M,R]],
         'discontinuity_positions':[-1.,0.],'incoming_waves':incoming},
      'collision':{'time':tc,'position':xc},
      'after_interaction_IVP':{'local_time_origin':tc,'local_position_origin':xc,
         'LEFT':L.serializable(),'RIGHT':R.serializable(),'middle_state_is_consumed':True,
         'exterior_states_are_unchanged':True},
      'search':{'starts_attempted':search.starts_attempted,'root_set_stable':search.root_set_stable,
         'complete':search.complete,'domain_codes':list(search.domain_codes),
         'regular_fans_found':len(search.solutions),'rejected':list(search.rejected),
         'scope':'Regular evolutionary ideal-MHD fans; no exhaustive intermediate/compound/degenerate branch enumeration.'},
      'outgoing_solutions':[s.serializable() for s in search.solutions],
      'separate_wave_audits':audits,'rarefaction_samples':rare,
      'finite_volume_check':{'method':'Independent in-package HLL/MUSCL-minmod/SSPRK2; not an external community solver',
         'initialization':'Three incoming states at x=-1 and x=0; evolves through collision',
         'runs':reports,'limitations':'Bulk profiles converge; these grids do not separately resolve the tiny contact and narrow rarefactions.'},
      'observational_limitations':['These are prescribed model states, not measurements of a solar event.', 'No solar-unit or viewing-geometry conversion is assigned.', 'A comparison with EUV observations requires independent plasma constraints and a temperature-response/line-of-sight model.'],
      'solver_sha256':{p:hashlib.sha256((IMPL/p).read_bytes()).hexdigest() for p in ['rmo/regular_fan.py','rmo/wave_curves.py','rmo/physics.py']}}
    (OUT/'connected_interaction.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
    print('SUMMARY',json.dumps({'collision':record['collision'],'roots':len(search.solutions),
        'stable':search.root_set_stable,'codes':search.domain_codes,'waves':[(a['family'],a['structure'],a['max_primitive_jump']) for a in audits]}),flush=True)

if __name__=='__main__':main()
