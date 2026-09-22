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
   const calls=[],downloads=[],blobs=new Map();let gate=null,busyNext=false;
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
     if(busyNext&&['/api/run','/api/diagnose'].includes(absolute.pathname)){busyNext=false;return new Response(JSON.stringify({code:'CALCULATION_BUSY',error:'The calculation service is busy with another request. Please wait a moment, then click Calculate again. Your input values are unchanged.'}),{status:409,headers:{'Content-Type':'application/json'}});}
     const response=await fetch(absolute,{...opts,headers:{...opts.headers,Origin:origin,Cookie:cookie}});
     if(gate&&absolute.pathname==='/api/diagnose')await gate;
     return response;
    };
   }});windows.push(dom.window);await pause(50);
   return {w:dom.window,d:dom.window.document,calls,downloads,delay(p){gate=p;},busyOnce(){busyNext=true;}};
  }
  const ui=await page(true),{w,d,calls}=ui,$=id=>d.getElementById(id),click=id=>{$(id).click();},input=(id,v)=>{$(id).value=String(v);$(id).dispatchEvent(new w.Event('input',{bubbles:true}));},select=(id,v)=>{$(id).value=String(v);$(id).dispatchEvent(new w.Event('change',{bubbles:true}));};
  check('all inline modules initialise without JavaScript exceptions',errors.length===0);
  const ids=[...d.querySelectorAll('[id]')].map(x=>x.id);check('no duplicate element IDs',new Set(ids).size===ids.length);
  check('welcome has three direct task routes',$('rmo-main-navigation').querySelectorAll('a').length===3&&$('rmo-main-navigation').closest('header'));
  check('solar selection precedes optional import help and event preview',!!($('r67-choice').compareDocumentPosition($('r67-import-panel'))&4)&&!!($('r67-choice').compareDocumentPosition($('solar2017-case'))&4)&&!$('r67-import-panel').open);
  check('2017 description states absence of event diagnosis without implying a running job',!$('solar2017-case').textContent.includes('diagnosis pending')&&$('solar2017-case').textContent.includes('not available for this event'));
  const steps=['guided-examples','advanced-input','input-report','live-panel','r63-results'];check('input, check, calculation and references follow reading order',steps.every((id,i)=>!i||!!($(steps[i-1]).compareDocumentPosition($(id))&4)));
  check('empty inputs cannot start either calculation',$('live-run').disabled&&$('r75-run').disabled);
  await until(()=>$('live-status').textContent.includes('connected'),'connection');
  click('live-load-contact');check('contact load opens check and its collapsed ancestors',w.lastScrolled==='input-report'&&$('r73-tools-workspace').open);
  check('contact is ready to calculate beside report',!$('live-run').disabled&&$('input-report').textContent.includes('Your input is ready'));
  check('ready report offers an enabled calculate action with connection feedback',!$('report-calculate').disabled&&$('report-calculation-status').textContent.includes('checked'));
  check('request fingerprint is available inside collapsed details',$('input-report').querySelector('.fingerprint').closest('details')&&!$('input-report').querySelector('.fingerprint').closest('details').open);
  const waitingInput=$('value-u_n_L').value;ui.busyOnce();click('report-calculate');await until(()=>!$('report-calculate').disabled,'contact busy recovery');
  check('busy contact displays wait guidance beside retry and preserves inputs',$('live-output').textContent.includes('Your calculation has not started')&&$('live-status').textContent.includes('Please wait')&&$('report-calculation-status').textContent.includes('Please wait')&&$('value-u_n_L').value===waitingInput&&!$('live-output').textContent.includes('connection failure'));
  click('live-edit');check('editing opens and focuses parameters',w.lastScrolled==='advanced-input'&&d.activeElement.id==='advanced-input');
  input('value-p_R','-1');click('check-input-after-edit');check('invalid manual input has named error and no calculation',$('input-report').textContent.includes('RIGHT')&&$('value-p_R').getAttribute('aria-invalid')==='true'&&$('live-run').disabled);
  input('value-p_R','');input('reason-p_R','Not measured');click('check-input-after-edit');check('unknown value stays incomplete and keeps its reason',$('input-report').textContent.includes('INCOMPLETE')&&$('input-report').textContent.includes('Not measured')&&$('live-run').disabled);
  click('live-load-contact');const runsBefore=calls.filter(x=>x.path==='/api/run').length;click('report-calculate');click('report-calculate');click('live-run');
  check('both calculate controls block duplicate clicks during the same attempt',$('report-calculate').disabled&&$('live-run').disabled&&calls.filter(x=>x.path==='/api/run').length===runsBefore+1);
  await until(()=>$('live-output').textContent.includes('Density across')||$('live-output').textContent.includes('No current result:'),'contact calculation');
  check('real contact calculation displays current result and focuses it',w.lastScrolled==='live-output'&&$('live-output').textContent.includes('Density across'));
  check('computed result can be saved',!![...$('live-output').querySelectorAll('button')].find(b=>b.textContent.includes('Save this input')));
  const saveContact=$('live-output').querySelector('button');check('computed save is before detailed explanations and plots',saveContact.textContent.includes('Save this input')&&!!(saveContact.compareDocumentPosition($('live-output').querySelector('details'))&4));
  input('value-u_n_L','.45');input('value-u_n_R','.45');check('editing removes former computed result',!$('live-output').textContent.includes('Density across'));
  click('check-input-after-edit');check('edited input review gives the current next step beside calculate',$('report-calculation-status').textContent.includes('Input checked.'));click('report-calculate');await until(()=>$('live-output').textContent.includes('contact: 0.45'),'edited contact');check('edited contact computes the entered speed, not the saved speed',$('live-output').textContent.includes('contact: 0.45'));
  check('contact speed is shown in the short answer',$('live-output').querySelector('p').textContent.includes('0.45'));
  $('live-output').querySelector('button').click();const computedExport=JSON.parse(await ui.downloads.at(-1).blob.text());check('prominent contact save exports the newly entered velocity',computedExport.input.parsed_snapshot.initial_states.left.u[0]===.45&&computedExport.input.parsed_snapshot.initial_states.right.u[0]===.45);
  click('live-run');await pause(80);click('live-cancel');await until(()=>!$('live-history').hidden&&$('live-cancel').disabled,'cancelled attempt');
  check('cancelled response stays in history and does not become current',$('live-output').textContent.includes('No current result')&&!$('live-history').hidden);
  check('calculation controls recover after cancellation',!$('live-run').disabled&&$('live-cancel').disabled);
  const cfg=JSON.parse($('r75-config').textContent);
  const modelFamilies={A63:'fast_shock',A17:'slow_shock',A42:'contact',A88:'rotational_discontinuity'};
  const shortcutCalls=calls.length;
  for(const place of ['top','inner'])for(const [model,family] of Object.entries(modelFamilies)){
   $('r75-workspace').open=false;click('rmo-'+place+'-model-'+model);
   const saved=JSON.parse($('r75-json').textContent);
   check(place+' '+model+' shortcut opens the exact saved family with focus',
    $('r75-model').value===model&&$('r75-factor').value==='0'&&saved.input.nominal.case_id===model&&
    saved.assessment.status==='EXACT_LOCAL_CLASS'&&saved.assessment.family===family&&
    $('r75-workspace').open&&!$('r75-result').hidden&&d.activeElement.id==='r75-result'&&w.lastScrolled==='r75-result'&&
    $('r75-source').textContent.includes('Saved checked model '+model+'; no new calculation'));
  }
  check('opening model shortcuts never starts an API calculation',calls.length===shortcutCalls);
  check('input-check action is clear and step number stays in the report heading',
   $('check-input-after-edit').textContent==='Check input values'&&$('report-title').textContent.startsWith('3'));

  for(const row of cfg.cases){select('r75-model',row.id);select('r75-factor',row.factor);click('r75-load');const json=JSON.parse($('r75-json').textContent);assert.equal(JSON.stringify(json.assessment),JSON.stringify(row.output));check('saved local model '+row.id+' / '+row.factor+' shown explicitly as saved',!$('r75-result').hidden&&$('r75-source').textContent.includes('no new calculation')&&w.lastScrolled==='r75-result');}
  click('r75-edit-result');check('saved result offers direct return to parameters',$('r75-inputs').open&&w.lastScrolled==='r75-inputs');
  select('r75-model','A63');select('r75-factor','0.01');click('r75-load');input('r75-left-rho-width','-1');const before=calls.length;click('r75-run');check('invalid error bound is labelled beside calculate and not sent',calls.length===before&&$('r75-action-status').textContent.includes('half-width')&&$('r75-left-rho-width').getAttribute('aria-invalid')==='true');
  click('r75-load');const waitingBound=$('r75-left-rho-width').value;ui.busyOnce();click('r75-run');await until(()=>!$('r75-run').disabled,'diagnosis busy recovery');
  check('busy diagnosis preserves input and shows waiting guidance with retry enabled',$('r75-action-status').textContent.includes('Please wait')&&$('r75-left-rho-width').value===waitingBound&&$('r75-result').hidden&&$('r75-save-result').disabled&&!$('r75-action-status').textContent.includes('Calculation unavailable'));
  click('r75-run');await until(()=>$('r75-source').textContent.startsWith('New calculation')&&!$('r75-result').hidden,'A63 new');check('new local result is focused automatically',w.lastScrolled==='r75-result'&&d.activeElement.id==='r75-result');
  click('r75-save-result');click('r75-save-pdf');const resultFile=ui.downloads.find(x=>x.name==='RMO_local_result.json'),pdfFile=ui.downloads.find(x=>x.name==='RMO_local_result.pdf');check('new result JSON and PDF export correctly',JSON.parse(await resultFile.blob.text()).assessment.status==='CONDITIONAL_ROBUST_CLASS'&&(await pdfFile.blob.text()).startsWith('%PDF'));
  let release;ui.delay(new Promise(r=>release=r));click('r75-run');await pause(100);input('r75-left-rho','1.1');release();await until(()=>$('r75-action-status').textContent.includes('older response'),'stale response');ui.delay(null);check('input change during calculation cannot display or export stale result',$('r75-result').hidden&&$('r75-save-result').disabled);
  click('rmo-inner-model-A63');let finishOld;ui.delay(new Promise(r=>finishOld=r));click('r75-run');await pause(100);
  click('rmo-top-model-A88');const selectedRotation=$('r75-json').textContent;finishOld();
  await until(()=>!$('r75-run').disabled,'shortcut during calculation');ui.delay(null);
  check('late calculation cannot replace a model selected through a shortcut',
   !$('r75-result').hidden&&$('r75-json').textContent===selectedRotation&&$('r75-source').textContent.includes('Saved checked model A88'));
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
  select('r67-choice','E05');click('r67-load');input('r67-row-0-value','600');click('r67-check');
  check('E05 report shows source 590 and edited 600 together',$('r67-changes').textContent.includes('590 km/s')&&$('r67-changes').textContent.includes('600 km/s')&&$('r67-event-title').textContent.startsWith('E05'));
  check('E05 next action does not confuse original speed with working speed',!$('r67-next').textContent.includes('590')&&$('r67-next').textContent.includes('Image-pattern speed'));
  check('save stays inside the report reached after review',$('r67-review-output').contains($('r67-save'))&&!$('r67-save').disabled);
  click('r67-save');await pause(80);const litDownload=ui.downloads.filter(x=>x.name==='RMO_E05_working_draft.json').at(-1);check('reviewed solar draft can be saved',!!litDownload);const litText=await litDownload.blob.text();
  const record=JSON.parse(litText);check('solar export preserves published values and reviewed edits separately',Number(record.draft.rows[0].value)===600&&record.source_snapshot.values[0].value===590&&record.review.rows[0].value===600&&record.calculation.status==='NOT_RUN');
  check('download feedback is next to the solar save control',$('r67-save-status').textContent.includes('download offered'));
  const downloadCount=ui.downloads.length;click('r67-save');await pause(80);check('identical draft download feedback and retry remain visible beside result',ui.downloads.length===downloadCount&&$('r67-save-status').textContent.includes('already offered')&&!$('r67-save-again').hidden);
  input('r67-row-0-value','-999');check('edited solar draft cannot save an old review',$('r67-save').disabled&&$('r67-review-status').textContent.includes('Edited'));
  Object.defineProperty($('r67-import'),'files',{configurable:true,value:[{name:'solar.json',size:litText.length,text:async()=>litText}]});$('r67-import').dispatchEvent(new w.Event('change',{bubbles:true}));await pause(50);check('solar draft import opens its event and requires review',w.lastScrolled==='r67-event-title'&&$('r70-import-status').textContent.includes('Imported')&&$('r67-save').disabled);
  click('r67-review-top');check('imported 600 survives re-review with unchanged source 590',$('r67-row-0-value').value==='600'&&$('r67-changes').textContent.includes('590 km/s')&&$('r67-changes').textContent.includes('600 km/s')&&!$('r67-save').disabled);
  click('r67-edit-reviewed');check('solar review has a direct edit route',w.lastScrolled==='r67-values');
  const analysisLinks=[...d.querySelectorAll('a[href^="#"]')].filter(a=>a.textContent.trim());check('navigation includes the full analysis collection',analysisLinks.length>=38);for(const a of analysisLinks){const target=d.getElementById(a.getAttribute('href').slice(1));check('analysis target exists: '+a.getAttribute('href'),!!target);a.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true}));check('analysis target ancestors open: '+target.id,[...ancestors(target)].filter(n=>n.tagName==='DETAILS').every(n=>n.open));}
  function* ancestors(n){while(n){yield n;n=n.parentElement;}}
  for(const group of ['r120','r117','r116','r115','r107']){
   const slider=$(group+'-slider')||$(group+'-range');if(!slider)throw Error('Missing viewer slider: '+group);
   slider.value='0';slider.dispatchEvent(new w.Event('input',{bubbles:true}));click(group+'-next');check(group+' next frame advances',Number(slider.value)===1);click(group+'-prev');check(group+' previous frame returns',Number(slider.value)===0);
  }
  for(const b of d.querySelectorAll('button[id$="-play"]')){const before=b.textContent;b.click();check(b.id+' exposes playback state',b.textContent!==before||b.getAttribute('aria-pressed')==='true');b.click();}
  const offline=await page(false);offline.d.getElementById('r75-load').click();check('offline saved result works and live calculation explains unavailability',!offline.d.getElementById('r75-result').hidden&&offline.d.getElementById('r75-run').disabled&&offline.d.getElementById('r75-run-help').textContent.includes('offline'));
  offline.d.getElementById('live-load-contact').click();check('offline report cannot enable a calculation shortcut',offline.d.getElementById('report-calculate').disabled&&offline.d.getElementById('report-calculation-status').textContent.includes('cannot run Python'));
  offline.d.getElementById('load-preset').click();check('Brio-Wu load gives immediate feedback and a saved-view action',offline.w.lastScrolled==='example-context'&&offline.d.getElementById('example-context').textContent.includes('Loaded:')&&offline.d.getElementById('loaded-brio-view'));
  offline.d.getElementById('loaded-brio-view').click();check('Brio-Wu view opens the saved solution without running Python',offline.w.lastScrolled==='r63-results'&&offline.d.getElementById('r63-result-choice').value==='brio'&&offline.calls.length===0);
  check('all exercised UI handlers complete without JavaScript exceptions',errors.length===0);
  console.log(JSON.stringify({checks,all_recorded_checks_pass:true,analysis_links:analysisLinks.length,scope:'DOM integration plus real isolated HTTP calculations. No browser rendering, mobile layout or production deployment verification.'},null,2));
 }catch(e){exitCode=1;console.error(e.stack);console.log(JSON.stringify({checks,errors,all_recorded_checks_pass:false},null,2));}
 finally{for(const w of windows)w.document.querySelectorAll('details[open]').forEach(n=>n.open=false);await pause(200);windows.forEach(w=>w.close());service.kill('SIGTERM');fs.rmSync(temp,{recursive:true,force:true});}
 process.exitCode=exitCode;
 async function asyncReady(){try{const r=await fetch(origin+'/healthz');return r.ok;}catch{return false;}}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
