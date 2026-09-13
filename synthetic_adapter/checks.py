"""Independent scalar checks from RMO-16/17/21. No imports from the RMO solver."""
import math
from .input import equal, mapped, numeric, primitives

RH_TOL, VALUE_TOL, ORDER_TOL, DOMAIN = 1e-10, 5e-9, 1e-9, 1e-12


def finite_tree(x):
    if isinstance(x, float) and not math.isfinite(x): raise ValueError("Nonfinite result")
    if isinstance(x, dict):
        for v in x.values(): finite_tree(v)
    if isinstance(x, list):
        for v in x: finite_tree(v)


def close(a, b):
    return abs(a - b) <= VALUE_TOL * max(1., abs(a), abs(b))


def pt(s): return s["p"] + .5 * sum(b*b for b in s["B"])


def qflux(s, gamma):
    rho, p = s["rho"], s["p"]
    un, v, w = s["u"]
    bn, by, bz = s["B"]
    energy = p/(gamma-1) + .5*rho*(un*un+v*v+w*w) + .5*(bn*bn+by*by+bz*bz)
    pressure = pt(s)
    q = [rho, rho*un, rho*v, rho*w, by, bz, energy]
    f = [rho*un, rho*un*un+pressure-bn*bn, rho*un*v-bn*by,
         rho*un*w-bn*bz, un*by-v*bn, un*bz-w*bn,
         (energy+pressure)*un-bn*(un*bn+v*by+w*bz)]
    if not all(math.isfinite(x) for x in q+f): raise ValueError("Derived conservative/flux arithmetic nonfinite")
    return q, f


def rh(l, r, speed, gamma):
    ql, fl = qflux(l, gamma)
    qr, fr = qflux(r, gamma)
    residual = [(b-a-speed*(d-c))/max(1., abs(a), abs(b)) for a,b,c,d in zip(fl,fr,ql,qr)]
    if not all(math.isfinite(x) for x in residual): raise ValueError("RH arithmetic nonfinite")
    return max(map(abs, residual))


def entropy(s, gamma): return math.log(s["p"])-gamma*math.log(s["rho"])
def sound(s, gamma): return math.sqrt(gamma*s["p"]/s["rho"])


def check_packet(packet, request, policy, profile):
    """Return check records; failed raw candidates are never discarded or promoted."""
    records, accepted = [], []
    def test(code, passed, value=None, tolerance=None):
        records.append(dict(check=code, status="PASS" if passed else "FAIL", value=value, tolerance=tolerance))
        if not passed: raise ValueError(code)
    try:
        finite_tree(packet)
        left, right = mapped(request)
        gamma = float(request["physics"]["gamma"])
        test("identity.policy", packet["policy"] == policy)
        test("identity.gamma", equal(packet["gamma"], gamma))
        test("identity.initial_states", equal(packet["initial_states"], [left, right]))
        raw = packet["raw"]
        test("result.shape", type(raw) is dict and raw.keys() == {"specification_id", "policy", "solutions", "rejected_candidates", "domain_codes", "complete"})
        test("result.specification", raw["specification_id"] == "RMO-R6A-SPEC-1.0.0")
        test("result.policy", raw["policy"] == policy)
        test("result.types", type(raw["complete"]) is bool and type(raw["solutions"]) is list and type(raw["rejected_candidates"]) is list and type(raw["domain_codes"]) is list)
        if raw["domain_codes"] == ["VACUUM_FORMED"]:
            gap = right["u"][0]-left["u"][0]
            threshold = 2*(sound(left,gamma)+sound(right,gamma))/(gamma-1)
            test("vacuum.exact_hydro_domain", profile == "HYDRO")
            test("vacuum.independent_criterion", gap >= threshold, {"velocity_gap": gap, "threshold": threshold})
            test("vacuum.no_finite_fan", not raw["solutions"])
            return dict(status="CHECKED_DOMAIN_NOTICE", checks=records, checked_solutions=[], notice="VACUUM_FORMED", stability="NOT_ASSESSED")
        test("result.domain_codes", raw["domain_codes"] == ["OK"], raw["domain_codes"])
        test("result.nonempty", bool(raw["solutions"]))
        ids = [s["id"] for s in raw["solutions"]]
        test("solution.unique_ids", all(isinstance(x,str) for x in ids) and len(ids) == len(set(ids)))
    except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        return dict(status="FAILED_CHECKS", checks=records, checked_solutions=[], error=str(exc), stability="NOT_ASSESSED")

    for solution in raw["solutions"]:
        begin = len(records)
        try:
            test("solution.shape", solution.keys() == {"id","policy","waves","intermediate_states","domain_codes","root_provenance"})
            test("solution.policy", solution["policy"] == policy)
            test("solution.codes", solution["domain_codes"] == ["OK"])
            test("solution.arrays", type(solution["waves"]) is list and type(solution["intermediate_states"]) is list)
            states = {"X_L0": left, "X_R0": right}
            for s in solution["intermediate_states"]:
                test("state.shape", type(s) is dict and s.keys() == {"id","role","frame","units","rho","p","u","B"})
                test("state.id", isinstance(s["id"],str) and s["id"] not in states)
                test("state.role", s["role"] == "intermediate")
                states[s["id"]] = s
            for s in states.values():
                test("state.vector_shape", type(s["u"]) is list and len(s["u"]) == 3 and type(s["B"]) is list and len(s["B"]) == 3)
                test("state.numeric", all(numeric(x) for x in primitives(s)))
                test("state.domain", s["rho"] > DOMAIN and s["p"] > DOMAIN)
                test("state.units_frame", s["units"] == "normalized_mu0_1" and s["frame"] == "RIEMANN_COMPUTATIONAL")
                # Bn is not numerically evolved in this adapter's domain: exact preservation.
                test("state.Bn", s["B"][0] == left["B"][0])
                qflux(s,gamma)
            waves = solution["waves"]
            if profile == "CONSTANT":
                test("constant.exact_input", primitives(left) == primitives(right))
                test("constant.no_waves_or_intermediates", not waves and len(states) == 2)
            else:
                test("nonconstant.has_waves", bool(waves))
                if profile in ("CONTACT","ROTATION_FIXTURE","TANGENTIAL_FIXTURE"):
                    wanted = {"CONTACT":"contact", "ROTATION_FIXTURE":"rotation", "TANGENTIAL_FIXTURE":"tangential"}[profile]
                    test("profile.structure", len(waves) == 1 and waves[0]["structure"] == wanted)
                cursor, last_speed, used = "X_L0", None, {"X_L0", "X_R0"}
                for i, wave in enumerate(waves):
                    test("wave.shape", wave.keys() == {"order","structure","family","speed","left_state_ref","right_state_ref","checks"})
                    test("wave.order_index", type(wave["order"]) is int and wave["order"] == i)
                    a, b = wave["left_state_ref"], wave["right_state_ref"]
                    test("wave.connected_refs", a == cursor and a in states and b in states and b != a and (b not in used or b == "X_R0" and i == len(waves)-1))
                    used.update((a,b)); cursor = b
                    l,r = states[a],states[b]
                    kind, family, speed = wave["structure"],wave["family"],wave["speed"]
                    interval = speed if type(speed) is list else [speed,speed]
                    test("wave.speed_shape", len(interval) == 2 and all(numeric(x) for x in interval))
                    lo, hi = interval
                    slack = ORDER_TOL * max(1., abs(lo), abs(hi), abs(last_speed or 0))
                    test("wave.interval_order", lo <= hi + slack)
                    if last_speed is not None: test("wave.sequence_order", last_speed <= lo + slack, {"previous":last_speed,"next":lo},slack)
                    last_speed = hi
                    if kind == "rarefaction":
                        test("rarefaction.domain", profile == "HYDRO" and all(x == 0 for s in (l,r) for x in (*s["B"],*s["u"][1:])))
                        test("rarefaction.branch", family in ("fast_minus","fast_plus") and type(speed) is list)
                        sign = -1 if family == "fast_minus" else 1
                        al,ar = sound(l,gamma),sound(r,gamma)
                        expected = [l["u"][0]+sign*al,r["u"][0]+sign*ar]
                        test("rarefaction.characteristic_interval", all(close(x,y) for x,y in zip(speed,expected)), {"returned":speed,"expected":expected},VALUE_TOL)
                        ds = entropy(r,gamma)-entropy(l,gamma)
                        test("rarefaction.isentropy", abs(ds) <= 1e-10, ds, 1e-10)
                        inv_l,inv_r = l["u"][0]-sign*2*al/(gamma-1),r["u"][0]-sign*2*ar/(gamma-1)
                        test("rarefaction.integral_relation", close(inv_l,inv_r), inv_r-inv_l, VALUE_TOL)
                        test("rarefaction.expansion", expected[0] <= expected[1]+slack)
                        continue  # no fictitious RH jump across a continuous rarefaction
                    test("wave.discontinuity_speed", numeric(speed))
                    residual = rh(l,r,speed,gamma)
                    test("wave.RH_scaled_inf", residual <= RH_TOL,residual,RH_TOL)
                    if kind == "contact":
                        test("contact.family", family == "entropy")
                        test("contact.invariants", close(l["p"],r["p"]) and all(close(x,y) for x,y in zip(l["u"]+l["B"],r["u"]+r["B"])) and close(speed,l["u"][0]) and close(speed,r["u"][0]))
                    elif kind == "tangential":
                        test("tangential.family", family == "entropy")
                        test("tangential.invariants", l["B"][0] == r["B"][0] == 0 and close(pt(l),pt(r)) and close(speed,l["u"][0]) and close(speed,r["u"][0]))
                    elif kind == "rotation":
                        test("rotation.branch", profile == "ROTATION_FIXTURE" and family in ("alfven_minus","alfven_plus"))
                        test("rotation.invariants", close(l["rho"],r["rho"]) and close(l["p"],r["p"]) and close(l["u"][0],r["u"][0]) and close(sum(x*x for x in l["B"][1:]),sum(x*x for x in r["B"][1:])))
                        sign = 1 if family == "alfven_plus" else -1
                        expected = l["u"][0]+sign*abs(l["B"][0])/math.sqrt(l["rho"])
                        test("rotation.characteristic", close(speed,expected),speed-expected,VALUE_TOL)
                        rel = [(l["u"][0]-speed)*(r["B"][j]-l["B"][j])-l["B"][0]*(r["u"][j]-l["u"][j]) for j in (1,2)]
                        test("rotation.alfvenic_relation", all(abs(x) <= RH_TOL for x in rel), rel,RH_TOL)
                    elif kind == "shock":
                        test("shock.reduced_hydro_domain", profile == "HYDRO" and all(x == 0 for s in (l,r) for x in (*s["B"],*s["u"][1:])) and family in ("fast_minus","fast_plus"))
                        mass = l["rho"]*(l["u"][0]-speed)
                        upstream,downstream = (l,r) if mass > 0 else (r,l)
                        test("shock.nonzero_mass", mass != 0)
                        test("shock.compression", downstream["rho"] > upstream["rho"] and downstream["p"] > upstream["p"])
                        ds = entropy(downstream,gamma)-entropy(upstream,gamma)
                        test("shock.entropy", ds >= -1e-10,ds,-1e-10)
                        sign = -1 if family == "fast_minus" else 1
                        ll,lr = l["u"][0]+sign*sound(l,gamma),r["u"][0]+sign*sound(r,gamma)
                        test("shock.Lax_characteristic", ll > speed and speed > lr,{"lambda_left":ll,"speed":speed,"lambda_right":lr})
                        evl = [l["u"][0]-sound(l,gamma),l["u"][0],l["u"][0]+sound(l,gamma)]
                        evr = [r["u"][0]-sound(r,gamma),r["u"][0],r["u"][0]+sound(r,gamma)]
                        incoming = sum(x>speed for x in evl)+sum(x<speed for x in evr)
                        test("shock.Euler_incoming_characteristics", incoming == 4,incoming)
                    else: test("wave.known_structure",False,kind)
                test("fan.right_endpoint", cursor == "X_R0")
                test("fan.no_unused_states", used == set(states))
            accepted.append({"id":solution["id"], "policy":policy, "waves":solution["waves"],
                             "intermediate_states":solution["intermediate_states"], "checks":records[begin:]})
        except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
            records.append(dict(check="candidate.validation_error",status="FAIL",value=str(exc),candidate=solution.get("id")))
    return dict(status="PASS" if len(accepted)==len(raw["solutions"]) else "FAILED_CHECKS",
                checks=records, checked_solutions=accepted, stability="NOT_ASSESSED")
