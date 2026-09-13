"""Bound independent result validation as well as the numerical calculation."""
import json
from pathlib import Path
import resource
import sys


def main():
    limit=512*1024*1024
    resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
    resource.setrlimit(resource.RLIMIT_CPU,(30,31))
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from synthetic_adapter.input import strict_load,OUTPUT_LIMIT
    from synthetic_adapter.checks import check_packet
    job=strict_load(sys.stdin.read(OUTPUT_LIMIT+1),OUTPUT_LIMIT)
    result=check_packet(job["packet"],job["request"],job["policy"],job["profile"])
    print(json.dumps({"event":"result","packet":result},allow_nan=False,separators=(",",":")),flush=True)


if __name__ == "__main__": main()
