"""Local Linux worker with memory/CPU limits, no network or file mutation."""
import resource
import sys
resource.setrlimit(resource.RLIMIT_CPU,(12,12))
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
sys.dont_write_bytecode=True
import base64
import json
from conservation_coupled.assess import assess
from .pdf_report import make_pdf
from synthetic_adapter.input import strict_load
data=sys.stdin.read(50001)
req=strict_load(data,50000)
out=assess(req)
print(json.dumps({'assessment':out,'pdf_base64':base64.b64encode(make_pdf(req,out)).decode()},allow_nan=False))
