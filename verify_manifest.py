"""Check the distributed file hashes without running any calculation."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parent
m=json.loads((root/'FILE_MANIFEST.json').read_text())
failed=[]
for r in m['files']:
 p=root/r['path']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:failed.append(r['path'])
print(json.dumps({'files_checked':len(m['files']),'failed':failed},indent=2))
sys.exit(bool(failed))
