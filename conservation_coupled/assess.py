"""RMO81: a sufficient entropy bound on the conservation-compatible subset.

No fitting or input modification. The previous assessor retains all other gates.
"""
from copy import deepcopy
from perpendicular_uncertainty.assess import assess as previous_assess, transverse_squared
from uncertainty_diagnosis.assess import interval_states
from uncertainty_diagnosis.interval import I, D


def entropy_at(r, k, gamma):
    """Outward enclosure at a point or box; monotonic use is in joint_entropy."""
    n=(gamma+1)*r-(gamma-1)
    den=(gamma+1)-(gamma-1)*r
    h=r-1
    return ((n+(gamma-1)*k*h*h*h)/den).ln()-gamma*r.ln()


def joint_entropy(states, upstream, downstream, gamma):
    g=I(gamma)
    if not D(1)<D(gamma)<D(2):
        raise ValueError('Fixed gamma must lie strictly between 1 and 2.')
    a,b=states[upstream],states[downstream]
    if any(s['B'][0].lo!=0 or s['B'][0].hi!=0 for s in (a,b)):
        raise ValueError('Normal magnetic field must be fixed exactly to zero.')
    r=b['rho']/a['rho']
    den=(g+1)-(g-1)*r
    if r.lo<=1 or den.lo<=0:
        raise ValueError('The full ratio bound must lie in the compressive Hugoniot domain.')
    k=transverse_squared(a)/(2*a['p'])
    # Exact nonnegative magnetic pressure, not a change to an input interval.
    k=I(max(D(0),k.lo),k.hi)
    lo=entropy_at(I(r.lo),I(k.lo),g)
    hi=entropy_at(I(r.hi),I(k.hi),g)
    entropy=I(lo.lo,hi.hi)
    return {'bounds':entropy.floats(),'decimal_bounds':entropy.exact(),
            'strictly_positive':entropy.lo>0,
            'compression_decimal_bounds':r.exact(),
            'magnetic_to_gas_pressure_decimal_bounds':k.exact(),
            'domain_denominator_decimal_bounds':den.exact(),
            'applies_to':'Exact RH-compatible states within the supplied box; fixed B_n=0.',
            'uses_entropy_as_input_constraint':False}


def assess(env):
    out=previous_assess(env)
    if (out.get('integration')!='RMO79-fixed-perpendicular-bounds'
        or out['status']!='NOT_CERTIFIED'
        or out.get('unresolved_checks')!=['entropy increase']):
        return out
    # Redundant explicit anchor gate protects this new route from future changes.
    if (out.get('independent_check',{}).get('status')!='PASS'
        or out.get('nominal',{}).get('status')!='SUPPORTED_LOCAL_CLASS'
        or out['nominal'].get('family')!='fast_shock'):
        return out
    try:
        _,states=interval_states(env['nominal'],env['half_widths'])
        sides=out['flow_sides']
        joint=joint_entropy(states,sides['upstream'],sides['downstream'],env['nominal']['gamma'])
    except (ValueError,ArithmeticError,OverflowError):
        return out
    result=deepcopy(out)
    result['joint_entropy_check']=joint
    result['previous_test']={'checkpoint':'RMO79','status':out['status'],
        'entropy_margin':deepcopy(out['margins']['fast_shock']['entropy increase'])}
    if not joint['strictly_positive']:
        return result
    result.update(integration='RMO81-conservation-coupled-perpendicular',
        status='CONDITIONAL_ROBUST_CLASS',family='fast_shock',
        sufficient_inequalities=['fast_shock'],unresolved_checks=[],
        result_sentence='Fast shock remains supported within these error ranges when conservation links the states, with exactly perpendicular geometry.',
        next_action='Inspect the conservation-linked entropy bound and unchanged speed checks. Uncertain field angle and observational identification still require separate constraints.')
    result['margins']['fast_shock']['entropy increase']=joint
    result['limitations'].append('The joint bound uses exact RH equations; nominal decimal feasibility remains checked numerically to tolerance. No full feasible-set search is performed.')
    return result
