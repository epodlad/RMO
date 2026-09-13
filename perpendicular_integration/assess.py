"""RMO78 exact-perpendicular dispatch; the RMO75 assessor stays unchanged."""
from uncertainty_diagnosis.assess import assess as previous_assess, FIELDS, interval_states, independent
from uncertainty_diagnosis.interval import D
from local_diagnosis.diagnose import finite
from perpendicular_diagnosis.diagnose import diagnose


def assess(env):
    # Route only a genuinely supplied zero normal field, never None or a label.
    try:
        bn=[env['nominal'][s]['B'][0] for s in ('left','right')]
        eligible=all(finite(v) and v==0 for v in bn)
    except (TypeError,KeyError,IndexError):
        eligible=False
    if not eligible:
        return previous_assess(env)
    out={'schema_version':'rmo-bounded-assessment-0.1','status':'NOT_ASSESSED','family':None,
         'scope':'Single planar ideal-MHD discontinuity; exact perpendicular extension',
         'integration':'RMO78-exact-perpendicular','global_uniqueness':False,
         'probability':None,'full_riemann_solve':False,'uncertainty_evaluated':False,
         'limitations':['Exact model inputs only for the perpendicular extension.',
                        'Nonzero error widths are retained but their type is not certified.',
                        'No geometry uncertainty, covariance, stability or observed EUV identification.',
                        'A local class does not establish a complete Riemann fan.']}
    def stop(status,sentence,next_action):
        out.update(status=status,result_sentence=sentence,next_action=next_action)
        return out
    # Same declared outer contract as RMO75, without invoking its interval speed
    # calculator at a degenerate zero field component. The scalar diagnostic
    # owns all physical-state validation and never receives an expected label.
    allowed={'schema_version','nominal','half_widths','bounds_kind','fixed_geometry_and_gamma'}
    if (set(env)-{'missing_reasons'}!=allowed or env.get('schema_version')!='rmo-bounded-local-0.1'
        or env.get('bounds_kind')!='deterministic_box' or env.get('fixed_geometry_and_gamma') is not True):
        return stop('INVALID_INPUT','Use the bounded local-input schema with fixed geometry and gamma.','Load or export a local model input.')
    reasons=env.get('missing_reasons',{})
    if not isinstance(reasons,dict) or any(k not in FIELDS or not isinstance(v,str) or len(v)>200 for k,v in reasons.items()):
        return stop('INVALID_INPUT','Missing-value explanations must refer to local input fields.','Use a short explanation for each unknown value.')
    req=env['nominal'];widths=env['half_widths']
    if not isinstance(widths,dict) or set(widths)!=set(FIELDS) or not all(finite(v) and 0<=v<=1e12 for v in widths.values()):
        return stop('INVALID_INPUT','Supply a finite nonnegative half-width for every input quantity.','Correct the indicated input or uncertainty width.')
    nominal=diagnose(req);out['nominal']=nominal
    if nominal['status']=='INSUFFICIENT_DATA':
        out['missing']=nominal['missing']
        return stop('MISSING_MEASUREMENTS',nominal['result_sentence'],'Supply or constrain the listed quantities. Unknown values remain unknown.')
    if 'characteristics' not in nominal.get('checks',{}):
        return stop(nominal['status'],nominal['result_sentence'],nominal.get('next_action','Review the supplied model fields.'))
    out['independent_check']=independent(req,nominal)
    try:
        iv,states=interval_states(req,widths)
        out['input_bounds']={k:v.exact() for k,v in iv.items()}
        if any(s[k].lo<=D('1e-12') for s in states.values() for k in ('rho','p')):
            raise ValueError('A density or pressure bound reaches zero or the numerical floor.')
    except (ValueError,ArithmeticError,TypeError,KeyError,IndexError,OverflowError) as exc:
        return stop('INVALID_BOUNDS','The stated physical bounds are invalid: '+str(exc),'Correct the ranges; the input is not silently clipped.')
    if any(widths.values()):
        return stop('PERPENDICULAR_UNCERTAINTY_NOT_SUPPORTED',
          'These inputs include nonzero error bounds. The perpendicular extension has not yet evaluated whether the type survives those errors.',
          'Keep the measured errors. Inspect the nominal checks, but do not set real measurement errors to zero to obtain a classification. Exact values are appropriate only for an exact model test.')
    # A point display of evaluated exact-input speeds is not an interval claim.
    out['characteristic_values']=nominal['checks']['characteristics']
    out['relative_speed_values']=nominal['checks']['front_relative_normal_velocity']
    out['plot_kind']='nominal_points'
    if nominal.get('status')=='SUPPORTED_LOCAL_CLASS' and nominal.get('family') and out['independent_check']['status']=='PASS':
        out['family']=nominal['family']
        return stop('EXACT_LOCAL_CLASS',nominal['result_sentence'],
          'Inspect the conservation, entropy and speed checks. This is an exact model result; perpendicular uncertainty and observed-front identification remain to be assessed.')
    if nominal.get('family') and out['independent_check']['status']!='PASS':
        return stop('INDEPENDENT_CHECK_FAILED','The nominal class was not confirmed by the independent conservation and speed calculation.',
                    'Inspect the disagreement before accepting a type. No checked family is assigned.')
    return stop(nominal['status'],nominal['result_sentence'],nominal.get('next_action','Review the exact model inputs and the stated limit. No type is assigned.'))
