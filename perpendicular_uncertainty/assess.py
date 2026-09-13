"""RMO79: sufficient bounds for fixed B_n=0, with a checked nominal anchor.

Protocol and limits are in protocol.md. No fitting, lookup or answer-label input.
"""
from perpendicular_integration.assess import assess as previous_assess
from uncertainty_diagnosis.assess import interval_states, example_request
from uncertainty_diagnosis.interval import I, D


def fixed_perpendicular_example(req, factor):
    """A declared synthetic constraint; never used to preprocess user input."""
    env = example_request(req, factor)
    env['half_widths']['left.B.0'] = env['half_widths']['right.B.0'] = 0
    return env


def transverse_squared(state):
    value = sum(x.square() for x in state['B'][1:])
    # Exact sum-of-squares domain, not clipping a measured input or signed margin.
    return I(max(D(0), value.lo), value.hi)


def perpendicular_speeds(state, gamma):
    if state['B'][0].lo != 0 or state['B'][0].hi != 0:
        raise ValueError('Perpendicular speeds require an exactly fixed zero normal field.')
    return {'fast': ((gamma * state['p'] + transverse_squared(state)) / state['rho']).sqrt(),
            'alfven_n': I(0), 'slow': I(0)}


def assess(env):
    # Previous dispatch owns strict input validation and the independent nominal
    # check. Preserve every earlier response outside this explicitly new scope.
    out = previous_assess(env)
    if out['status'] != 'PERPENDICULAR_UNCERTAINTY_NOT_SUPPORTED':
        return out
    w, req = env['half_widths'], env['nominal']
    if w['left.B.0'] != 0 or w['right.B.0'] != 0:
        return out
    out.update(integration='RMO79-fixed-perpendicular-bounds',
               scope='Single planar ideal-MHD discontinuity; B_n fixed exactly to zero',
               uncertainty_evaluated=False,
               assumptions=['Both normal-field values and widths equal zero by model assumption.',
                            'Fixed normal direction, frame basis and gamma; 1 < gamma < 2.',
                            'Type statement applies only to conservation-compatible discontinuities.'],
               limitations=['Deterministic bounds are not confidence levels or a noise distribution.',
                            'The full Cartesian box does not satisfy conservation equalities.',
                            'Nominal conservation is numerical, checked to the stated tolerance.',
                            'No search for a conservation witness around an inconsistent centre.',
                            'Failure to certify does not demonstrate another feasible family.',
                            'No uncertain angle, covariance, stability, full Riemann fan or observed EUV identification.'])

    def stop(status, sentence, next_action):
        out.update(status=status, result_sentence=sentence, next_action=next_action)
        return out

    if not 1 < req['gamma'] < 2:
        return stop('PERPENDICULAR_MODEL_OUT_OF_SCOPE',
                    'This bounded perpendicular test requires 1 < gamma < 2.',
                    'Keep the chosen physical model; this test does not cover its gamma.')
    if out['nominal']['status'] != 'SUPPORTED_LOCAL_CLASS' or out['nominal'].get('family') != 'fast_shock' or out['independent_check']['status'] != 'PASS':
        return stop('NOMINAL_NOT_CHECKED',
                    'The supplied centre does not provide a checked perpendicular shock anchor; these bounds have not been certified.',
                    'Review the conservation checks. This module does not fit noisy measurements or search for a different state; failure is not physical exclusion.')
    try:
        iv, states = interval_states(req, w)
        cs = {s: perpendicular_speeds(v, I(req['gamma'])) for s, v in states.items()}
        vel = {s: v['u'][0] - iv['front_speed'] for s, v in states.items()}
        out['characteristic_bounds'] = {s: {k: v.floats() for k, v in c.items()} for s, c in cs.items()}
        out['characteristic_decimal_bounds'] = {s: {k: v.exact() for k, v in c.items()} for s, c in cs.items()}
        out['relative_speed_bounds'] = {s: v.floats() for s, v in vel.items()}
        out['relative_speed_decimal_bounds'] = {s: v.exact() for s, v in vel.items()}
        out['uncertainty_evaluated'] = True
        out['plot_kind'] = 'bounded_ranges'
        direction = 1 if all(v.lo > 0 for v in vel.values()) else (-1 if all(v.hi < 0 for v in vel.values()) else 0)
        if not direction:
            out['unresolved_checks'] = ['nonzero common mass-flow direction']
            return stop('NOT_CERTIFIED',
                        'The bounds do not fix a nonzero mass-flow direction, so this perpendicular type test cannot certify a shock.',
                        'Constrain plasma normal velocity relative to the front. A failed sufficient test does not prove a competing solution.')
        up, down = ('left', 'right') if direction == 1 else ('right', 'left')
        a, b = states[up], states[down]
        ratio = b['rho'] / a['rho']
        bt_u, bt_d = transverse_squared(a).sqrt(), transverse_squared(b).sqrt()
        rows = {'compression - 1': ratio - 1,
                'entropy increase': (b['p'] / a['p']).ln() - I(req['gamma']) * ratio.ln(),
                'nonzero upstream transverse field': bt_u,
                'nonzero downstream transverse field': bt_d,
                'field alignment': sum(x*y for x, y in zip(a['B'][1:], b['B'][1:])),
                'transverse-field increase': bt_d - bt_u,
                'upstream flow - fast': direction*vel[up] - cs[up]['fast'],
                'downstream fast - flow': cs[down]['fast'] - direction*vel[down]}
        out['flow_sides'] = {'upstream': up, 'downstream': down}
        out['margins'] = {'fast_shock': {k: {'bounds': v.floats(), 'decimal_bounds': v.exact(),
                                            'strictly_positive': v.lo > 0} for k, v in rows.items()}}
        out['unresolved_checks'] = [k for k, v in rows.items() if v.lo <= 0]
        out['sufficient_inequalities'] = [] if out['unresolved_checks'] else ['fast_shock']
        if not out['unresolved_checks']:
            out['family'] = 'fast_shock'
            return stop('CONDITIONAL_ROBUST_CLASS',
                        'Fast-shock inequalities hold throughout these bounds, conditional on a conservation-compatible single ideal-MHD discontinuity with B_n fixed exactly to zero.',
                        'Inspect the fixed perpendicular geometry and each error range. The nominal conservation check passed independently; uncertain angle and real-event identification require separate work.')
        return stop('NOT_CERTIFIED',
                    'The nominal perpendicular fast shock is checked, but these bounds do not certify its type.',
                    'The sufficient test could not establish: '+', '.join(out['unresolved_checks'])+'. Joint physical constraints may help; this does not prove another feasible family.')
    except (ValueError, ArithmeticError, OverflowError) as exc:
        return stop('INVALID_BOUNDS', 'These bounds could not be evaluated: '+str(exc),
                    'Review the supplied physical ranges; no input range is silently changed.')
