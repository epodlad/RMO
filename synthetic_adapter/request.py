"""Create an inert execution envelope from stdin. This command never runs the solver."""
import sys
import uuid
from .input import INNER_LIMIT,strict_load,check_request,make_envelope

data=sys.stdin.buffer.read(INNER_LIMIT+1)
if len(data)>INNER_LIMIT:raise SystemExit("Input exceeds 64 KiB")
try:
    body=data.decode("utf-8");request=strict_load(body,INNER_LIMIT)
    check=check_request(request)
    if check["status"]=="INVALID":raise ValueError(str(check["errors"]))
    print(make_envelope(request,execution_id="local-"+uuid.uuid4().hex,request_json=body))
except (ValueError,UnicodeError) as exc:raise SystemExit(str(exc))
