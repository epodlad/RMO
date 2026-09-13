"""Use: python3 -m synthetic_adapter < execution-envelope.json > result.json"""
import sys
from .input import OUTER_LIMIT, encode
from .runner import run

data=sys.stdin.buffer.read(OUTER_LIMIT+1)
try:
    if len(data)>OUTER_LIMIT: raise ValueError("Envelope exceeds byte limit")
    result=run(data.decode("utf-8"))
except (ValueError,UnicodeError) as exc:
    result={"execution":{"status":"NOT_STARTED","solver_call_count":0},"input":{"status":"INVALID","errors":[str(exc)]}}
print(encode(result))
