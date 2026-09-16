/* DOM integration checks for the shipped page, with an isolated real Python API.
   Not a rendering test: focus/scroll calls are recorded; no browser is controlled.
   npm install --prefix /tmp/rmo-ui-tests jsdom@26.1.0
   NODE_PATH=/tmp/rmo-ui-tests/node_modules RMO_PYTHON=python3 node verification/ui_workflow_smoke.cjs
*/
'use strict';
const {JSDOM,VirtualConsole}=require('jsdom');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto'),{spawn}=require('node:child_process'),net=require('node:net'),os=require('node:os');
const root=path.resolve(__dirname,'..'),checks=[],errors=[],windows=[];
const check=(name,yes)=>{checks.push({name,pass:!!yes});assert.ok(yes,name);};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let i=0;i<2000;i++){if(await fn())return;await pause(20);}throw Error('Timed out: '+label);}
async function main(){
 const listener=net.createServer();await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
 const origin='http://127.0.0.1:'+port,temp=fs.mkdtempSync(path.join(os.tmpdir(),'rmo-ui-'));
 const service=spawn(process.env.RMO_PYTHON||'python3',['-B','-m','local_app.server','--port',String(port)],{cwd:root,env:{...process.env,RMO_RESULTS_DIR:temp,OPENBLAS_NUM_THREADS:'1',OMP_NUM_THREADS:'1'},stdio:'ignore'});
 let exitCode=0;
 try{
  await until(asyncReady,'server startup');
  async function page(online){
   let cookie='';let html=fs.readFileSync(path.join(root,'public/index.html'),'utf8');
   if(online){const r=await fetch(origin);cookie=r.headers.get('set-cookie').split(';')[0];html=await r.text();}
   const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(e.type!=='css parsing'&&e.type!=='not implemented')errors.push(e.message);});
   const calls=[],downloads=[],blobs=new Map();let gate=null;
   const dom=new JSDOM(html,{url:origin,runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
    w.TextEncoder=TextEncoder;w.TextDecoder=TextDecoder;w.Blob=Blob;w.AbortController=AbortController;
    Object.defineProperty(w.crypto,'subtle',{value:webcrypto.subtle});w.crypto.randomUUID=()=>webcrypto.randomUUID();
    w.HTMLElement.prototype.scrollIntoView=function(){w.lastScrolled=this.id;};w.scrollTo=()=>{};
    w.URL.createObjectURL=b=>{const u='blob:rmo-test-'+blobs.size;blobs.set(u,b);return u;};w.URL.revokeObjectURL=()=>{};
    w.HTMLAnchorElement.prototype.click=function(){downloads.push({name:this.download,href:this.href,blob:blobs.get(this.href)});};
    w.fetch=async(url,opts={})=>{
     const absolute=new URL(url,origin);if(absolute.origin!==origin)throw Error('External network not part of this test');
     calls.push({path:absolute.pathname,body:opts.body});
     if(!online)throw Error('Offline test');
     const response=await fetch(absolute,{...opts,headers:{...opts.headers,Origin:origin,Cookie:cookie}});
     if(gate&&absolute.pathname==='/api/diagnose')await gate;
     return response;
    };
   }});windows.push(dom.window);await pause(50);
   return {w:dom.window,d:dom.window.document,calls,downloads,delay(p){gate=p;}};
  }
  const ui=await page(true),{w,d,calls}=ui,$=id=>d.getElementById(id),click=id=>{$(id).click();},input=(id,v)=>{$(id).value=String(v);$(id).dispatchEvent(new w.Event('input',{bubbles:true}));},select=(id,v)=>{$(id).value=String(v);$(id).dispatchEvent(new w.Event('change',{bubbles:true}));};
  check('all inline modules initialise without JavaScript exceptions',errors.length===0);
  const ids=[...d.querySelectorAll('[id]')].map(x=>x.id);check('no duplicate element IDs',new Set(ids).size===ids.length);
  const steps=['guided-examples','advanced-input','input-report','live-panel','r63-results'];check('input, check, calculation and references follow reading order',steps.every((id,i)=>!i||!!($(steps[i-1]).compareDocumentPosition($(id))&4)));
  check('empty inputs cannot start either calculation',$('live-run').disabled&&$('r75-run').disabled);
  await until(()=>$('live-status').textContent.includes('connected'),'connection');
  click('live-load-contact');check('contact load opens check and its collapsed ancestors',w.lastScrolled==='input-report'&&$('r73-tools-workspace').open);
  check('contact is ready to calculate beside report',!$('live-run').disabled&&$('input-report').textContent.includes('Your input is ready'));
  click('live-edit');check('editing opens and focuses parameters',w.lastScrolled==='advanced-input'&&d.activeElement.id==='advanced-input');
  input('value-p_R','-1');click('check-input-after-edit');check('invalid manual input has named error and no calculation',$('input-report').textContent.includes('RIGHT')&&$('value-p_R').getAttribute('aria-invalid')==='true'&&$('live-run').disabled);
  input('value-p_R','');input('reason-p_R','Not measured');click('check-input-after-edit');check('unknown value stays incomplete and keeps its reason',$('input-report').textContent.includes('INCOMPLETE')&&$('input-report').textContent.includes('Not measured')&&$('live-run').disabled);
  click('live-load-contact');click('live-run');await until(()=>$('live-output').textContent.includes('Density across')||$('live-output').textContent.includes('No current result:'),'contact calculation');
  check('real contact calculation displays current result and focuses it',w.lastScrolled==='live-output'&&$('live-output').textContent.includes('Density across'));
  check('computed result can be saved',!![...$('live-output').querySelectorAll('button')].find(b=>b.textContent.includes('Save this input')));
  input('value-u_n_L','.45');input('value-u_n_R','.45');check('editing removes former computed result',!$('live-output').textContent.includes('Density across'));
  click('check-input-after-edit');click('live-run');await until(()=>$('live-output').textContent.includes('contact: 0.45'),'edited contact');check('edited contact computes the entered speed, not the saved speed',$('live-output').textContent.includes('contact: 0.45'));
  click('live-run');await pause(80);click('live-cancel');await until(()=>!$('live-history').hidden&&$('live-cancel').disabled,'cancelled attempt');
  check('cancelled response stays in history and does not become current',$('live-output').textContent.includes('No current result')&&!$('live-history').hidden);
  check('calculation controls recover after cancellation',!$('live-run').disabled&&$('live-cancel').disabled);
  const cfg=JSON.parse($('r75-config').textContent);
  for(const row of cfg.cases){select('r75-model',row.id);select('r75-factor',row.factor);click('r75-load');const json=JSON.parse($('r75-json').textContent);assert.equal(JSON.stringify(json.assessment),JSON.stringify(row.output));check('saved local model '+row.id+' / '+row.factor+' shown explicitly as saved',!$('r75-result').hidden&&$('r75-source').textContent.includes('no new calculation')&&w.lastScrolled==='r75-result');}
  click('r75-edit-result');check('saved result offers direct return to parameters',$('r75-inputs').open&&w.lastScrolled==='r75-inputs');
  select('r75-model','A63');select('r75-factor','0.01');click('r75-load');input('r75-left-rho-width','-1');const before=calls.length;click('r75-run');check('invalid error bound is labelled beside calculate and not sent',calls.length===before&&$('r75-action-status').textContent.includes('half-width')&&$('r75-left-rho-width').getAttribute('aria-invalid')==='true');
  click('r75-load');click('r75-run');await until(()=>$('r75-source').textContent.startsWith('New calculation')&&!$('r75-result').hidden,'A63 new');check('new local result is focused automatically',w.lastScrolled==='r75-result'&&d.activeElement.id==='r75-result');
  click('r75-save-result');click('r75-save-pdf');const resultFile=ui.downloads.find(x=>x.name==='RMO_local_result.json'),pdfFile=ui.downloads.find(x=>x.name==='RMO_local_result.pdf');check('new result JSON and PDF export correctly',JSON.parse(await resultFile.blob.text()).assessment.status==='CONDITIONAL_ROBUST_CLASS'&&(await pdfFile.blob.text()).startsWith('%PDF'));
  let release;ui.delay(new Promise(r=>release=r));click('r75-run');await pause(100);input('r75-left-rho','1.1');release();await until(()=>$('r75-action-status').textContent.includes('older response'),'stale response');ui.delay(null);check('input change during calculation cannot display or export stale result',$('r75-result').hidden&&$('r75-save-result').disabled);
  click('r75-blank-inputs');click('r75-export-input');const blank=JSON.parse(await ui.downloads.at(-1).blob.text());check('own-input route has no fabricated model measurements',blank.nominal.case_id==='user_input'&&blank.nominal.left.rho===null&&blank.nominal.right.rho===null&&blank.half_widths['left.rho']===0);
  async function importLocal(text){Object.defineProperty($('r75-import'),'files',{configurable:true,value:[{name:'input.json',size:text.length,text:async()=>text}]});$('r75-import').dispatchEvent(new w.Event('change',{bubbles:true}));await pause(30);}
  const saved=cfg.cases.find(r=>r.id==='A63'&&r.factor===.01).input;await importLocal(JSON.stringify(saved));check('manual file import opens fields and explains next action',w.lastScrolled==='r75-inputs'&&$('r75-action-status').textContent.startsWith('Imported')&&$('r75-result').hidden);
  click('r75-blank-inputs');
  for(const k of cfg.fields){const value=k.split('.').reduce((o,n)=>o[n],saved.nominal);input('r75-'+k.replaceAll('.','-'),value);input('r75-'+k.replaceAll('.','-')+'-width',saved.half_widths[k]);}
  click('r75-run');await until(()=>!$('r75-result').hidden&&$('r75-source').textContent.startsWith('New calculation'),'fully manual input');
  check('parameters entered by hand produce their own new assessment',JSON.parse($('r75-json').textContent).input.nominal.case_id==='user_input'&&JSON.parse($('r75-json').textContent).assessment.status==='CONDITIONAL_ROBUST_CLASS');
  const keep=$('r75-left-rho').value;await importLocal('{bad json');check('bad import leaves current values intact',$('r75-left-rho').value===keep&&$('r75-action-status').textContent.startsWith('Import failed'));
  await importLocal(JSON.stringify({...saved,nominal:{...saved.nominal,gamma:0}}));check('invalid gamma rejected before replacing fields',$('r75-left-rho').value===keep&&$('r75-action-status').textContent.includes('gamma'));
  const lit=JSON.parse($('r67-config').textContent),postBefore=calls.filter(x=>x.path.startsWith('/api/')).length;
  for(const card of lit.cards){select('r67-choice',card.id);click('r67-load');check('solar card '+card.id+' loads source and visible fields',!$('r67-literature').hidden&&$('r67-event-title').textContent.includes(card.title)&&w.lastScrolled==='r67-event-title');click('r67-review-top');check('solar card '+card.id+' review follows controls',w.lastScrolled==='r67-review-output'&&$('r67-review-status').textContent.length>0);}
  check('solar literature review never starts a solver',calls.filter(x=>x.path.startsWith('/api/')).length===postBefore);
  select('r67-choice','E05');click('r67-load');click('r67-check');click('r67-save');await pause(80);const litDownload=ui.downloads.filter(x=>x.name==='RMO_E05_working_draft.json').at(-1);check('reviewed solar draft can be saved',!!litDownload);const litText=await litDownload.blob.text();
  input('r67-row-0-value','-999');check('edited solar draft cannot save an old review',$('r67-save').disabled&&$('r67-review-status').textContent.includes('Edited'));
  Object.defineProperty($('r67-import'),'files',{configurable:true,value:[{name:'solar.json',size:litText.length,text:async()=>litText}]});$('r67-import').dispatchEvent(new w.Event('change',{bubbles:true}));await pause(50);check('solar draft import opens its event and requires review',w.lastScrolled==='r67-event-title'&&$('r70-import-status').textContent.includes('Imported')&&$('r67-save').disabled);
  click('r67-edit-reviewed');check('solar review has a direct edit route',w.lastScrolled==='r67-values');
  const analysisLinks=[...d.querySelectorAll('a[href^="#"]')].filter(a=>a.textContent.trim());check('navigation includes the full analysis collection',analysisLinks.length>=38);for(const a of analysisLinks){const target=d.getElementById(a.getAttribute('href').slice(1));check('analysis target exists: '+a.getAttribute('href'),!!target);a.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true}));check('analysis target ancestors open: '+target.id,[...ancestors(target)].filter(n=>n.tagName==='DETAILS').every(n=>n.open));}
  function* ancestors(n){while(n){yield n;n=n.parentElement;}}
  for(const group of ['r120','r117','r116','r115','r107']){
   const slider=$(group+'-slider')||$(group+'-range');if(!slider)throw Error('Missing viewer slider: '+group);
   slider.value='0';slider.dispatchEvent(new w.Event('input',{bubbles:true}));click(group+'-next');check(group+' next frame advances',Number(slider.value)===1);click(group+'-prev');check(group+' previous frame returns',Number(slider.value)===0);
  }
  for(const b of d.querySelectorAll('button[id$="-play"]')){const before=b.textContent;b.click();check(b.id+' exposes playback state',b.textContent!==before||b.getAttribute('aria-pressed')==='true');b.click();}
  const offline=await page(false);offline.d.getElementById('r75-load').click();check('offline saved result works and live calculation explains unavailability',!offline.d.getElementById('r75-result').hidden&&offline.d.getElementById('r75-run').disabled&&offline.d.getElementById('r75-run-help').textContent.includes('offline'));
  check('all exercised UI handlers complete without JavaScript exceptions',errors.length===0);
  console.log(JSON.stringify({checks,all_recorded_checks_pass:true,analysis_links:analysisLinks.length,scope:'DOM integration plus real isolated HTTP calculations. No browser rendering, mobile layout or production deployment verification.'},null,2));
 }catch(e){exitCode=1;console.error(e.stack);console.log(JSON.stringify({checks,errors,all_recorded_checks_pass:false},null,2));}
 finally{for(const w of windows)w.document.querySelectorAll('details[open]').forEach(n=>n.open=false);await pause(200);windows.forEach(w=>w.close());service.kill('SIGTERM');fs.rmSync(temp,{recursive:true,force:true});}
 process.exitCode=exitCode;
 async function asyncReady(){try{const r=await fetch(origin+'/healthz');return r.ok;}catch{return false;}}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
