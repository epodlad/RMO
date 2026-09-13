"""Bounded process wrapper for the existing protected local HTTP transport."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from synthetic_adapter.input import strict_load,encode

ROOT=Path(__file__).resolve().parents[1]
def validate(text):
    e=strict_load(text,65536)
    if not isinstance(e,dict) or set(e)!={'execution_id','input_revision','request_body','request_sha256'}:
        raise ValueError('Diagnosis requires exact request identity and serialized input.')
    if not isinstance(e['execution_id'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',e['execution_id']):raise ValueError('Invalid execution ID')
    if type(e['input_revision']) is not int or not 0<=e['input_revision']<=1000000:raise ValueError('Invalid input revision')
    if not isinstance(e['request_body'],str) or len(e['request_body'])>50000:raise ValueError('Invalid request body')
    sha=hashlib.sha256(e['request_body'].encode()).hexdigest()
    if sha!=e['request_sha256']:raise ValueError('Request checksum mismatch')
    strict_load(e['request_body'],50000)
    return e

def run(e):
    env=os.environ.copy()
    for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:env[k]='1'
    try:
        p=subprocess.run([sys.executable,'-m','uncertainty_diagnosis.worker'],input=e['request_body'],
                         text=True,capture_output=True,cwd=ROOT,env=env,timeout=15)
        if p.returncode or len(p.stdout)>3000000:
            return {'identity':e,'error':'Diagnosis worker did not complete within its declared limits.'}
        response=strict_load(p.stdout,3000000)
        return {'identity':e,**response}
    except subprocess.TimeoutExpired:
        return {'identity':e,'error':'Diagnosis reached the 15-second limit. No family is assigned.'}
