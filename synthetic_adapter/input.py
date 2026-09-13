"""Independent Python validation of the frozen preflight request. No solver imports."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "rmo-synthetic-adapter-draft-0.1.0"
PROFILE = "R6B_SPECIAL_CASES_0_1_0_DRAFT"
POLICIES = ["REGULAR_EVOLUTIONARY_1.0", "ENUMERATE_NONREGULAR_1.0"]
SCHEMA = json.loads((ROOT / "specification/quicklook_input/request_schema_draft_0_1_0.json").read_text())
TEMPLATE = json.loads((ROOT / "specification/quicklook_input/request_examples_and_acceptance_design.json").read_text())["request"]
INNER_LIMIT, OUTER_LIMIT, OUTPUT_LIMIT = 65536, 524288, 2097152
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
FIELDS = [f"/initial_states/{side}/{field}" for side in ("left", "right")
          for field in ("rho", "p", "u/0", "u/1", "u/2", "B_t/0", "B_t/1")]
FIELDS += ["/shared_Bn", "/physics/gamma"]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def strict_load(text, limit=OUTER_LIMIT):
    if not isinstance(text, str) or len(text.encode("utf-8")) > limit:
        raise ValueError("JSON size/type limit")

    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("Duplicate JSON key: " + k)
            out[k] = v
        return out

    def number(token):
        if len(token) > 128:
            raise ValueError("Numeric token too long")
        val = float(token)
        if not math.isfinite(val) or (val == 0 and Decimal(token) != 0):
            raise ValueError("Nonfinite number or underflow-to-zero")
        # Preserve exact integer revisions; binary64 mapping of physics occurs explicitly later.
        return int(token) if not any(c in token for c in ".eE") else val

    def constant(token):
        raise ValueError("Nonfinite JSON constant: " + token)
    return json.loads(text, object_pairs_hook=pairs, parse_float=number,
                      parse_int=number, parse_constant=constant)


def numeric(x):
    return type(x) in (int, float) and math.isfinite(x)


def equal(a, b):
    # JSON numeric equality without Python's True == 1 equivalence.
    if numeric(a) and numeric(b):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def ptr(obj, path):
    for key in path.lstrip("/").split("/"):
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj


def shape(value, rule=SCHEMA, path=""):
    errors = []
    def fail(msg): errors.append({"path": path, "code": "REQUEST_SHAPE_INVALID", "message": msg})
    if "$ref" in rule:
        errors += shape(value, ptr(SCHEMA, rule["$ref"][1:]), path)
    for r in rule.get("allOf", []): errors += shape(value, r, path)
    if "oneOf" in rule and sum(not shape(value, r, path) for r in rule["oneOf"]) != 1:
        fail("Expected one supported representation")
    if "const" in rule and not equal(value, rule["const"]): fail("Fixed value mismatch")
    if "enum" in rule and not any(equal(value, x) for x in rule["enum"]): fail("Unknown value")
    if "type" in rule:
        types = rule["type"] if isinstance(rule["type"], list) else [rule["type"]]
        checks = {"number": numeric(value), "object": type(value) is dict,
                  "array": type(value) is list, "string": type(value) is str, "null": value is None}
        if not any(checks.get(t, False) for t in types):
            fail("Wrong type; booleans are not numbers")
            return errors
    if isinstance(value, str) and len(value) < rule.get("minLength", 0): fail("Empty text")
    if isinstance(value, list):
        if not rule.get("minItems", 0) <= len(value) <= rule.get("maxItems", float("inf")): fail("Array length")
        if rule.get("uniqueItems") and any(any(equal(x, y) for y in value[:i]) for i, x in enumerate(value)): fail("Duplicate entry")
        if "items" in rule:
            for i, x in enumerate(value): errors += shape(x, rule["items"], path + "/" + str(i))
    if isinstance(value, dict):
        for k in rule.get("required", []):
            if k not in value: errors.append({"path": path + "/" + k, "code": "MISSING_KEY", "message": "Required key"})
        for k, v in value.items():
            if k in rule.get("properties", {}): errors += shape(v, rule["properties"][k], path + "/" + k)
            elif rule.get("additionalProperties") is False: fail("Unexpected field: " + k)
            elif isinstance(rule.get("additionalProperties"), dict): errors += shape(v, rule["additionalProperties"], path + "/" + k)
    return errors


def check_request(request):
    errors = shape(request)
    if errors: return {"status": "INVALID", "errors": errors}
    def fail(path, msg): errors.append({"path": path, "code": "INPUT_INVALID", "message": msg})
    if not ID.fullmatch(request["request_id"]): fail("/request_id", "Invalid request name")
    missing = 0
    for path in FIELDS:
        v = ptr(request, path)
        if v is None:
            missing += 1
            if not request["missing_reasons"].get(path, "").strip(): fail(path, "Unknown value needs a reason")
        elif path.endswith(("/rho", "/p")) and v <= 1e-12: fail(path, "Density/pressure must exceed 1e-12; no clipping")
        elif path == "/physics/gamma" and v <= 1: fail(path, "Gamma must exceed one")
    for path, reason in request["missing_reasons"].items():
        if path not in FIELDS or ptr(request, path) is not None: fail(path, "Reason must refer to a null physical scalar")
        if not reason.strip() or len(reason.encode("utf-16-le")) // 2 > 1024: fail(path, "Nonblank reason of at most 1024 UTF-16 units required")
    unc = request["uncertainty"]
    if unc["mode"] != "exact_synthetic":
        try:
            C, n = unc["covariance"], len(unc["parameters"])
            if len(C) != n or any(len(row) != n for row in C): raise ValueError("Covariance shape")
            if any(C[i][i] <= 0 for i in range(n)): raise ValueError("Variance must be positive")
            if any(C[i][j] != C[j][i] for i in range(n) for j in range(n)): raise ValueError("Covariance must be symmetric")
            d = [math.sqrt(C[i][i]) for i in range(n)]
            L = [[0.] * n for _ in range(n)]
            for i in range(n):
                for j in range(i + 1):
                    v = C[i][j] / d[i] / d[j] - sum(L[i][k] * L[j][k] for k in range(j))
                    if not math.isfinite(v): raise ValueError("Covariance arithmetic overflow")
                    if i == j:
                        if v <= 64 * sys.float_info.epsilon * n: raise ValueError("Positive definiteness unresolved; no repair")
                        L[i][j] = math.sqrt(v)
                    else: L[i][j] = v / L[j][j]
        except (ValueError, OverflowError, ZeroDivisionError) as exc: fail("/uncertainty/covariance", str(exc))
    return {"status": "INVALID" if errors else "INCOMPLETE" if missing else "VALID", "errors": errors,
            "uncertainty": "EXACT_SYNTHETIC" if unc["mode"] == "exact_synthetic" else "METADATA_ONLY_NOT_PROPAGATED"}


def unpack(text):
    envelope = strict_load(text)
    keys = {"adapter_contract", "action", "execution_id", "request_json", "request_body_sha256", "input_revision", "capability_profile"}
    if type(envelope) is not dict or envelope.keys() != keys: raise ValueError("Invalid envelope keys")
    if envelope["adapter_contract"] != CONTRACT or envelope["action"] != "run_synthetic_special_case" or envelope["capability_profile"] != PROFILE:
        raise ValueError("Unknown contract/action/capability")
    if not isinstance(envelope["execution_id"], str) or not ID.fullmatch(envelope["execution_id"]): raise ValueError("Invalid execution ID")
    rev = envelope["input_revision"]
    if type(rev) is not int or not 0 <= rev <= 2**53 - 1: raise ValueError("Revision must be a nonnegative safe integer")
    request = strict_load(envelope["request_json"], INNER_LIMIT)
    if envelope["request_body_sha256"] != digest(envelope["request_json"]): raise ValueError("Request-body hash mismatch")
    return envelope, request, check_request(request)


def make_envelope(request, execution_id="local-test", revision=0, request_json=None):
    body = encode(request) if request_json is None else request_json
    return encode(dict(adapter_contract=CONTRACT, action="run_synthetic_special_case", execution_id=execution_id,
                       request_json=body, request_body_sha256=digest(body), input_revision=revision, capability_profile=PROFILE))


def mapped(request):
    out = []
    for side in ("left", "right"):
        state = deepcopy(request["initial_states"][side])
        state["B"] = [float(request["shared_Bn"]), *map(float, state.pop("B_t"))]
        state["u"] = list(map(float, state["u"]))
        state["rho"], state["p"] = float(state["rho"]), float(state["p"])
        out.append(state)
    return out


def primitives(s): return [s["rho"], s["p"], *s["u"], *s["B"]]


def manifest():
    import yaml  # already available; frozen local input, never a remote schema
    return yaml.safe_load((ROOT / "RMO/RMO_benchmark_manifest_v1_1.yaml").read_text())


def fixture_request(identifier):
    spec = next(b for b in manifest()["benchmarks"] if b["id"] == identifier)
    r = deepcopy(TEMPLATE)
    r["request_id"], r["physics"]["gamma"] = identifier, spec["gamma"]
    r["shared_Bn"] = spec["left"]["B"][0]
    if spec["right"]["B"][0] != r["shared_Bn"]: raise ValueError("Fixture cannot map to shared Bn")
    for side in ("left", "right"):
        s = r["initial_states"][side]
        s.update({k: deepcopy(spec[side][k]) for k in ("rho", "p", "u")})
        s["B_t"] = deepcopy(spec[side]["B"][1:])
    return r


def eligibility(r):
    if r["uncertainty"]["mode"] != "exact_synthetic": return "OTHER", "Uncertainty metadata retained; numerical propagation is not implemented"
    l, q = mapped(r)
    if primitives(l) == primitives(q): return "CONSTANT", "Exactly equal binary64 states"
    if l["p"] == q["p"] and l["u"] == q["u"] and l["B"] == q["B"] and abs(l["B"][0]) > 1e-12: return "CONTACT", "Exact contact input domain"
    if all(x == 0 for x in (*l["B"], *q["B"], *l["u"][1:], *q["u"][1:])): return "HYDRO", "Exactly zero magnetic field and transverse velocity"
    for identifier, profile in (("B02_rotation_right", "ROTATION_FIXTURE"), ("B07_tangential_Bn0", "TANGENTIAL_FIXTURE")):
        f = fixture_request(identifier)
        if r["physics"]["gamma"] == f["physics"]["gamma"] and all(primitives(a) == primitives(b) for a, b in zip((l,q), mapped(f))):
            return profile, "Exact frozen fixture " + identifier
    return "OTHER", "This first route does not solve arbitrary MHD pairs or Brio-Wu; no saved fallback"
