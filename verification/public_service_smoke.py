"""Exercise the HTTPS-origin policy at the internal HTTP proxy boundary."""
import asyncio,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aiohttp import ClientSession,web
from web_app.server import create_app,STATE
from synthetic_adapter.input import make_envelope
P=Path(__file__).resolve().parents[1]
async def main():
 origin='https://rmo.example';app=create_app([origin]);runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start();port=site._server.sockets[0].getsockname()[1];url=f'http://127.0.0.1:{port}';checks=[]
 def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
 try:
  async with ClientSession() as client:
   async def session():
    async with client.get(url+'/',headers={'Host':'rmo.example'}) as r:
     text=await r.text();cfg=json.loads(re.search(r'<script id="local-config" type="application/json">(.*?)</script>',text).group(1));cookie=r.headers['Set-Cookie']
     check('public Secure/HttpOnly cookie',all(s in cookie for s in ['Secure','HttpOnly','SameSite=Strict']))
     check('HTTPS origin and HSTS',cfg['origin']==origin and 'Strict-Transport-Security' in r.headers)
     return {'Host':'rmo.example','Origin':origin,'X-RMO-Token':cfg['token'],'Cookie':cookie.split(';',1)[0]}
   a=await session();b=await session()
   async with client.get(url+'/',headers={'Host':'bad.example','X-Forwarded-Host':'rmo.example'}) as r:check('forwarded Host cannot grant origin',r.status==403)
   body=(P/'results/uncertainty_diagnosis/A63_01_request.json').read_text();env={'execution_id':'public-a63','input_revision':1,'request_body':body,'request_sha256':hashlib.sha256(body.encode()).hexdigest()}
   async with client.post(url+'/api/diagnose',json=env,headers=a) as r:
    result=await r.json();check('public A63 association',r.status==200 and result['identity']==env)
    check('public result omits execution paths','saved_directory' not in result and str(P) not in json.dumps(result) and 'worker_command' not in json.dumps(result))
   request=json.loads((P/'results/synthetic_adapter/worked_contact/contact_request.json').read_text());env=json.loads(make_envelope(request,execution_id='public-b01'))
   async def contact():
    async with client.post(url+'/api/run',json=env,headers=a) as r:return r.status,await r.json()
   task=asyncio.create_task(contact())
   for _ in range(100):
    if app[STATE].busy:break
    await asyncio.sleep(.01)
   check('calculation becomes active',app[STATE].busy)
   retry_env=dict(env,execution_id='public-busy')
   async with client.post(url+'/api/run',json=retry_env,headers=b) as r:
    busy_reply=await r.json()
    check('single calculation capacity',r.status==409)
    check('busy response identifies a temporary wait without exposing another request',set(busy_reply)=={'code','error'} and busy_reply['code']=='CALCULATION_BUSY' and 'input values are unchanged' in busy_reply['error'])
   identity={k:env[k] for k in ['execution_id','request_body_sha256','input_revision']}
   async with client.post(url+'/api/cancel',json=identity,headers=b) as r:check('other session cancellation remains local',r.status==200 and (await r.json())['status']=='EARLY_CANCELLATION_RECORDED')
   status,value=await task;check('other session cannot cancel active result',status==200 and value['result']['execution']['status']=='FINISHED')
   async with client.post(url+'/api/run',json=retry_env,headers=b) as r:
    retried=await r.json()
    check('busy attempt can retry unchanged after the first calculation finishes',r.status==200 and retried['result']['identity']==retry_env and retried['result']['execution']['status']=='FINISHED')
   check('public calculation files disabled',app[STATE].output is None and 'saved_directory' not in value)
  print(json.dumps({'checks':checks,'all_recorded_checks_pass':all(x['pass'] for x in checks)},indent=2))
 finally:await runner.cleanup()
if __name__=='__main__':asyncio.run(main())
