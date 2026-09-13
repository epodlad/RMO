"""RMO runtime smoke checks using an isolated local HTTP service."""
import tempfile,shutil
import base64,hashlib,http.cookiejar,io,json,os,re,socket,subprocess,sys,threading,time,urllib.error,urllib.request
from pathlib import Path
from pypdf import PdfReader
W=Path(__file__).resolve().parents[1];P=W;E=Path(tempfile.mkdtemp(prefix='rmo-smoke-'))
sys.path.insert(0,str(P))
from synthetic_adapter.input import make_envelope

def opener():
 return urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
origin=f'http://127.0.0.1:{port}'
proc=subprocess.Popen([sys.executable,'-B','-m','web_app.server','--local','--port',str(port)],cwd=P,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',RMO_RESULTS_DIR=str(E/'local_runtime_checks')))
checks=[];metrics={};peak=[0];finished=threading.Event()
def sample():
 while not finished.wait(.02):
  rows={}
  for f in Path('/proc').glob('[0-9]*/status'):
   try:
    text=f.read_text();pid=int(f.parent.name);parent=int(re.search(r'^PPid:\s*(\d+)',text,re.M).group(1));rss=re.search(r'^VmRSS:\s*(\d+)',text,re.M)
    rows[pid]=(parent,int(rss.group(1))*1024 if rss else 0)
   except (OSError,AttributeError):pass
  family={pid for pid,(parent,_) in rows.items() if parent==int(Path("/proc/self").resolve().name)}
  while True:
   new={pid for pid,(parent,_) in rows.items() if parent in family}
   if new<=family:break
   family|=new
  peak[0]=max(peak[0],sum(rows.get(pid,(0,0))[1] for pid in family))
thread=threading.Thread(target=sample,daemon=True);thread.start()
def get(op,path='/',headers=None):
 try:
  r=op.open(urllib.request.Request(origin+path,headers=headers or {}),timeout=40);return r.status,r.read(),dict(r.headers)
 except urllib.error.HTTPError as e:return e.code,e.read(),dict(e.headers)
def post(op,path,envelope,token,extra=None):
 h={'Content-Type':'application/json','Origin':origin,'X-RMO-Token':token};h.update(extra or {})
 try:
  r=op.open(urllib.request.Request(origin+path,data=json.dumps(envelope).encode(),headers=h),timeout=40);return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.load(e)
def check(name,yes):
 checks.append({'name':name,'pass':bool(yes)});assert yes,name
try:
 a=opener();b=opener()
 for _ in range(100):
  try:
   if get(a,'/healthz')[0]==200:break
  except OSError:time.sleep(.05)
 else:raise RuntimeError('Service did not start')
 status,page,h=get(a);check('application HTTP',status==200)
 cfg=json.loads(re.search(rb'<script id="local-config" type="application/json">(.*?)</script>',page).group(1))
 _,page2,_=get(b);cfg2=json.loads(re.search(rb'<script id="local-config" type="application/json">(.*?)</script>',page2).group(1))
 check('separate browser-session tokens',cfg['token']!=cfg2['token'])
 check('cookie protections','HttpOnly' in h['Set-Cookie'] and 'SameSite=Strict' in h['Set-Cookie'])
 check('foreign Host rejected',get(a,'/',{'Host':'attacker.invalid'})[0]==403)
 for path in ['/private-record.txt','/results/local_runs','/local_app/server.py','/assets/../index.html','/assets/'+('0'*64)+'.png']:
  check('no undeclared resource '+path,get(a,path)[0]==404)
 name=re.search(rb'/assets/([0-9a-f]{64}\.[a-z]+)',page).group(1).decode()
 status,content,_=get(a,'/assets/'+name)
 check('public asset delivery',status==200 and content==(P/'public/assets'/name).read_bytes())
 request_text=(P/'results/uncertainty_diagnosis/A63_01_request.json').read_text()
 envelope={'execution_id':'acceptance-a63','input_revision':1,'request_body':request_text,'request_sha256':hashlib.sha256(request_text.encode()).hexdigest()}
 check('another session token rejected',post(b,'/api/diagnose',envelope,cfg['token'])[0]==403)
 check('foreign Origin rejected',post(a,'/api/diagnose',envelope,cfg['token'],{'Origin':'https://attacker.invalid'})[0]==403)
 started=time.monotonic();status,result=post(a,'/api/diagnose',envelope,cfg['token']);metrics['A63_seconds']=time.monotonic()-started
 check('A63 HTTP and input association',status==200 and result['identity']==envelope)
 assessment=result['assessment'];check('A63 conditional result',assessment['status']=='CONDITIONAL_ROBUST_CLASS')
 reference=json.loads((P/'results/uncertainty_diagnosis/study.json').read_text())
 row=next(x for x in reference['cases'] if x['id']=='A63' and x['factor']==.01)
 check('A63 exact saved assessment',assessment==row['output'])
 pdf=base64.b64decode(result['pdf_base64']);reader=PdfReader(io.BytesIO(pdf));pdftext='\n'.join(p.extract_text() for p in reader.pages)
 check('A63 PDF contains result and limits','CONDITIONAL_ROBUST_CLASS' in pdftext and 'No global Riemann uniqueness' in pdftext)
 (E/'A63_api_result.json').write_text(json.dumps(result,indent=2));(E/'A63_api_result.pdf').write_bytes(pdf)
 check('repeat execution ID rejected',post(a,'/api/diagnose',envelope,cfg['token'])[0]==409)
 mutated=dict(envelope,execution_id='invalid-checksum',request_sha256='0'*64)
 check('invalid input checksum rejected',post(a,'/api/diagnose',mutated,cfg['token'])[0]==400)
 contact=json.loads((P/'results/synthetic_adapter/worked_contact/contact_request.json').read_text())
 env=json.loads(make_envelope(contact,execution_id='acceptance-contact'))
 started=time.monotonic();status,reply=post(a,'/api/run',env,cfg['token']);metrics['B01_seconds']=time.monotonic()-started
 check('B01 HTTP and identity',status==200 and reply['result']['identity']==env)
 r=reply['result'];check('B01 checked contact',r['execution']['status']=='FINISHED' and r['capability']['profile']=='CONTACT' and all(x['validation']['status']=='PASS' for x in r['policy_runs']))
 check('no private runtime paths or worker commands','worker_command' not in json.dumps(reply) and str(P) not in json.dumps(reply['result']))
 (E/'B01_api_result.json').write_text(json.dumps(reply,indent=2))
finally:
 finished.set();thread.join(timeout=2);proc.terminate()
 try:stdout,stderr=proc.communicate(timeout=40)
 except subprocess.TimeoutExpired:proc.kill();stdout,stderr=proc.communicate()
 metrics['peak_process_tree_rss_bytes']=peak[0]
 (E/'runtime_acceptance.json').write_text(json.dumps({'checks':checks,'metrics':metrics,'browser_acceptance':'NOT_PERFORMED','all_recorded_checks_pass':all(x['pass'] for x in checks)},indent=2))
 report={'checks':checks,'metrics':metrics,'all_recorded_checks_pass':all(x['pass'] for x in checks)}
 if os.environ.get('RMO_SMOKE_REPORT'):Path(os.environ['RMO_SMOKE_REPORT']).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2));shutil.rmtree(E)
