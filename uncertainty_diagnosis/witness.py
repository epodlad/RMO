"""Bounded numerical conservation witness; no family objective or reference lookup."""
import copy
import numpy as np
from scipy.optimize import least_squares
from local_diagnosis.diagnose import flux

def search(req,widths,fields,get,put):
    widths=dict(widths)
    widths['left.B.0']=min(widths['left.B.0'],widths['right.B.0'])
    active=[k for k in fields if widths[k]>0 and k!='right.B.0']
    note={'method':'bounded conservation least-squares from supplied centre',
          'max_function_evaluations':400,'not_a_best_estimate':True,'search_complete':False}
    if not active:
        return None,dict(note,status='NO_FREE_PARAMETERS')
    centre=copy.deepcopy(req)
    boost=[req['front_speed'],(req['left']['u'][1]+req['right']['u'][1])/2,(req['left']['u'][2]+req['right']['u'][2])/2]
    def stationary(r):
        states=copy.deepcopy([r['left'],r['right']])
        for s in states:s['u']=[s['u'][0]-r['front_speed'],s['u'][1]-boost[1],s['u'][2]-boost[2]]
        return states
    a,b=stationary(req);fa,fb=flux(a,req['gamma']),flux(b,req['gamma'])
    scales=np.array([max(1,abs(x),abs(y)) for x,y in zip(fa,fb)]+[max(1,abs(a['B'][0]),abs(b['B'][0]))])
    def unpack(z):
        r=copy.deepcopy(centre)
        for k,x in zip(active,z):put(r,k,get(centre,k)+widths[k]*float(x))
        r['right']['B'][0]=r['left']['B'][0]
        return r
    def residual(z):
        r=unpack(z);a,b=stationary(r)
        return np.array([y-x for x,y in zip(flux(a,r['gamma']),flux(b,r['gamma']))]+[b['B'][0]-a['B'][0]])/scales
    opt=least_squares(residual,np.zeros(len(active)),bounds=(-np.ones(len(active)),np.ones(len(active))),
                      method='trf',gtol=1e-14,xtol=1e-14,ftol=1e-14,max_nfev=400)
    candidate=unpack(opt.x)
    return candidate,dict(note,status='CANDIDATE_REQUIRES_INDEPENDENT_CHECK',nfev=opt.nfev,
        termination=str(opt.message),max_scaled_objective=float(np.max(np.abs(opt.fun))),
        adjustments={k:get(candidate,k)-get(req,k) for k in active})
