"""One trusted local solve, isolated in a process with enforced resource limits."""
import json
import os
from pathlib import Path
import resource
import sys
import time


def emit(value):
    text = json.dumps(value,allow_nan=False,separators=(",", ":"))
    if len(text.encode()) > 2*1024*1024: raise ValueError("OUTPUT_LIMIT")
    print(text,flush=True)


def main():
    # Apply limits before NumPy/SciPy or scientific code is imported.
    ceiling = 512*1024*1024
    resource.setrlimit(resource.RLIMIT_AS,(ceiling,ceiling))
    resource.setrlimit(resource.RLIMIT_CPU,(30,31))
    if resource.getrlimit(resource.RLIMIT_AS) != (ceiling,ceiling): raise RuntimeError("Memory limit unavailable")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root)); sys.path.insert(0,str(root/"implementation"))
    from synthetic_adapter.input import strict_load, mapped, check_request, eligibility
    job = strict_load(sys.stdin.read(524289))
    request, policy = job["request"],job["policy"]
    if check_request(request)["status"] != "VALID" or eligibility(request)[0] == "OTHER" or policy not in request["policies"]:
        raise ValueError("Worker input independently declined")
    import numpy
    import scipy
    from rmo.models import State
    from rmo.solver import RiemannSolver
    left,right = mapped(request)
    gamma = float(request["physics"]["gamma"])
    states = [State.from_mapping(x) for x in (left,right)]
    calls = 0
    def trace(frame,event,arg):
        nonlocal calls
        if event == "call" and frame.f_code is RiemannSolver.solve.__code__:
            calls += 1
            emit({"event":"solver_entered","count":calls})
        return None
    sys.setprofile(trace)
    try:
        result = RiemannSolver().solve(*states,gamma,policy)
    finally:
        sys.setprofile(None)
    packet = dict(policy=policy,gamma=gamma,initial_states=[left,right],raw=result.serializable(),
                  versions={"python":sys.version.split()[0],"numpy":numpy.__version__,"scipy":scipy.__version__},
                  limits={"address_space_bytes":ceiling,"cpu_seconds":30},solver_call_count=calls)
    emit({"event":"result","packet":packet})


if __name__ == "__main__":
    try: main()
    except BaseException as exc:
        try: emit({"event":"failure","error_type":type(exc).__name__,"message":str(exc)[:2000]})
        except BaseException: pass
        sys.exit(1)
