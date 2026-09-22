/* RMO-75: render saved or fresh Python assessments; never infer a class in JS. */
(()=>{'use strict';
const el=id=>document.getElementById(id), cfg=JSON.parse(el('r75-config').textContent), connection=JSON.parse(el('local-config').textContent);
const clone=x=>JSON.parse(JSON.stringify(x)), fields=cfg.fields, id=k=>'r75-'+k.replaceAll('.','-');
let current=null, revision=0, latest=null, busy=false;
const labelNames=Object.fromEntries([...el('r75-inputs').querySelectorAll('label[for]')].map(n=>[n.htmlFor,n.textContent.trim()]));
function setStatus(note){el('r75-status').textContent=note;el('r75-action-status').textContent=note;}
function visit(target){for(let n=target;n;n=n.parentElement)if(n.tagName==='DETAILS')n.open=true;target.setAttribute('tabindex','-1');target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'auto'});}
function syncRun(){el('r75-run').disabled=busy||!connection.enabled||!current;}
const get=(o,k)=>k.split('.').reduce((a,b)=>a[b],o);
const put=(o,k,v)=>{const a=k.split('.');let p=o;for(const n of a.slice(0,-1))p=p[n];p[a.at(-1)]=v;};
const safe=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function reason(k){const known=el(id(k)).value.trim()!=='';el(id(k)+'-reason').hidden=known;el(id(k)+'-reason-other').hidden=known||el(id(k)+'-reason').value!=='__other__';}
function invalidate(note){revision++;latest=null;el('r75-result').hidden=true;for(const k of ['result','svg','pdf'])el('r75-save-'+k).disabled=true;if(note)setStatus(note);}
function number(s,unknown=false){if(s.trim()===''){if(unknown)return null;throw Error('Every half-width needs a number; use 0 for an exact model quantity.');}const n=Number(s);if(!Number.isFinite(n))throw Error('Use finite decimal numbers.');return n;}
function fieldNumber(input,label,unknown=false){
 try{const n=number(input.value,unknown);input.removeAttribute('aria-invalid');return n;}
 catch(e){input.setAttribute('aria-invalid','true');throw Error(label+': '+e.message);}
}
function read(){
 if(!current)throw Error('Load or import a local input first, or choose Enter my own parameters.');
 const r=clone(current);r.missing_reasons={};r.nominal.gamma=fieldNumber(el('r75-gamma'),'Gamma');
 if(r.nominal.gamma<=1){el('r75-gamma').setAttribute('aria-invalid','true');throw Error('Gamma must be greater than 1.');}
 for(const k of fields){
  const name=labelNames[id(k)]||el(id(k)).getAttribute('aria-label')||k;
  const v=fieldNumber(el(id(k)),name,true),w=fieldNumber(el(id(k)+'-width'),name+' half-width');
  if(w<0){el(id(k)+'-width').setAttribute('aria-invalid','true');throw Error(name+': half-width must be 0 or greater.');}
  put(r.nominal,k,v);r.half_widths[k]=w;
  if(v===null&&el(id(k)+'-reason').value)r.missing_reasons[k]=el(id(k)+'-reason').value==='__other__'?el(id(k)+'-reason-other').value.trim():el(id(k)+'-reason').value;
 }
 r.nominal.right.B[0]=r.nominal.left.B[0];r.half_widths['right.B.0']=r.half_widths['left.B.0'];
 if(r.nominal.right.B[0]===null&&r.missing_reasons['left.B.0'])r.missing_reasons['right.B.0']=r.missing_reasons['left.B.0'];
 if(!Object.keys(r.missing_reasons).length)delete r.missing_reasons;
 return r;
}
function fill(r){
 if(r.schema_version!=='rmo-bounded-local-0.1'||r.bounds_kind!=='deterministic_box'||r.fixed_geometry_and_gamma!==true||!r.nominal||!r.half_widths)throw Error('This is not a bounded local-diagnosis request. Use the matching import control for a literature draft or Riemann request.');
 // Validate before replacing any visible values.
 if(typeof r.nominal.gamma!=='number'||!Number.isFinite(r.nominal.gamma)||r.nominal.gamma<=1)throw Error('Imported gamma must be a finite number greater than 1.');
 for(const k of [...fields,'right.B.0']){const v=get(r.nominal,k),w=r.half_widths[k];if(!(v===null||typeof v==='number'&&Number.isFinite(v))||typeof w!=='number'||!Number.isFinite(w)||w<0)throw Error('Invalid local value or width: '+k);}
 if(r.nominal.left.B[0]!==r.nominal.right.B[0]||r.half_widths['left.B.0']!==r.half_widths['right.B.0'])throw Error('This editor requires one shared normal field and width. Separate normal fields are not silently merged.');
 current=clone(r);el('r75-gamma').value=String(r.nominal.gamma);
 for(const k of fields){const v=get(r.nominal,k);el(id(k)).value=v===null?'':String(v);el(id(k)+'-width').value=String(r.half_widths[k]);const why=r.missing_reasons?.[k]||'';el(id(k)+'-reason').value=['','Not measured','Not reported in the source','Measurement unreliable','Geometry not known','Deliberately withheld for this test'].includes(why)?why:'__other__';el(id(k)+'-reason-other').value=why;reason(k);}
 invalidate();syncRun();
}
function plot(out){
 if(!out.characteristic_bounds&&!out.characteristic_values)return '';
 const points=out.plot_kind==='nominal_points';
 const bounds=points?Object.fromEntries(Object.entries(out.characteristic_values).map(([side,v])=>[side,Object.fromEntries(Object.entries(v).map(([k,x])=>[k,[x,x]]))])):out.characteristic_bounds;
 const flows=points?Object.fromEntries(Object.entries(out.relative_speed_values).map(([k,v])=>[k,[v,v]])):out.relative_speed_bounds;
 const rows=[];
 for(const s of ['left','right']){for(const k of ['slow','alfven_n','fast'])rows.push([s+' '+k,bounds[s][k],k]);const v=flows[s];rows.push([s+' |u_n - S|',[v[0]<=0&&v[1]>=0?0:Math.min(...v.map(Math.abs)),Math.max(...v.map(Math.abs))],'flow']);}
 const xmax=Math.max(...rows.map(x=>x[1][1]))*1.08||1,x=v=>190+v/xmax*590;
 let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 410" role="img" aria-label="Characteristic speed ranges and front-relative plasma flow"><rect width="820" height="410" fill="white"/><text x="22" y="30" font-size="18" font-family="sans-serif">Speed ranges for this input (normalized units)</text>';
 for(let i=0;i<=4;i++){const xx=190+i*590/4;svg+=`<line x1="${xx}" x2="${xx}" y1="48" y2="332" stroke="#e4eae9"/><text x="${xx}" y="358" text-anchor="middle" font-size="13" font-family="sans-serif">${(xmax*i/4).toPrecision(3)}</text>`;}
 rows.forEach(([name,v,key],i)=>{const y=67+i*36,colour={slow:'#247668',alfven_n:'#80519a',fast:'#287dab',flow:'#202b2c'}[key];svg+=`<text x="20" y="${y+5}" font-size="14" font-family="sans-serif">${safe(name)}</text><line x1="${x(v[0])}" x2="${x(v[1])}" y1="${y}" y2="${y}" stroke="${colour}" stroke-width="6" stroke-linecap="round"/><circle cx="${x((v[0]+v[1])/2)}" cy="${y}" r="3" fill="${colour}"/>`;});
 if(points)svg=svg.replace('Speed ranges for this input (normalized units)','Speeds for exact model inputs (normalized units)').replace('Characteristic speed ranges and front-relative plasma flow','Exact-input characteristic speeds and front-relative plasma flow');
 return svg+'<text x="20" y="392" font-size="13" font-family="sans-serif">'+(points?'Points are evaluated model speeds, not observational error bars.':'Bars enclose bounded input ranges. They are not confidence intervals.')+'</text></svg>';
}
function show(request,out,source,pdf=null){
 const signature=JSON.stringify(read());latest={request:clone(request),assessment:out,source,pdf,signature};
 const summary=globalThis.RMOPlainResult.local(out);
 el('r75-result').hidden=false;el('r75-sentence').textContent=summary;el('r75-technical-sentence').textContent=out.result_sentence;el('r75-next').textContent=out.next_action;el('r75-source').textContent=source;
 const fixedPerpendicular=['RMO79-fixed-perpendicular-bounds','RMO81-conservation-coupled-perpendicular'].includes(out.integration);
 el('r79-assumptions').hidden=!fixedPerpendicular;
 el('r79-assumptions').textContent=fixedPerpendicular?'Model condition: B_n is fixed at zero (field along the front surface). Only the other supplied ranges are tested. The complete range of independent inputs does not satisfy the conservation laws; the type statement applies to states that do.':'';
 setStatus(source+'. Result, plot and checks are below.');
 el('r75-plot').innerHTML=plot(out)||(out.status==='PERPENDICULAR_UNCERTAINTY_NOT_SUPPORTED'?'<p>No uncertainty plot is shown: the perpendicular error ranges have not been evaluated. The exact central-state checks are available below.</p>':'');
 const rows=[['Nominal exact-state check',out.nominal?.status||'Not evaluated'],['Independent nominal conservation',out.independent_check?.status||'Not evaluated'],['Conservation witness',out.witness?.independent_check?.status||'No separate witness required or obtained'],['Bounded type test',out.status],['Complete Riemann-fan uniqueness','Not established']];
 if(out.joint_entropy_check)rows.push(['Entropy check','Uses the conservation relation between the states']);
 const perpendicular=out.nominal?.checks?.perpendicular;
 if(perpendicular){rows.push(['Nominal field geometry','Perpendicular: field along the front surface; 90 degrees to its normal'],['Nominal entropy change / c_v',Number(perpendicular.entropy_over_cv).toPrecision(6)],['Nominal upstream flow above fast speed',perpendicular.upstream_superfast?'Pass':'Not passed'],['Nominal downstream flow below fast speed',perpendicular.downstream_subfast?'Pass':'Not passed']);}
 for(const [name,v] of Object.entries(out.margins?.[out.family||out.nominal?.family]||{}))rows.push([name,(v.strictly_positive?'Positive throughout':'Not certified')+' ['+v.bounds.map(x=>Number(x).toPrecision(5)).join(', ')+']']);
 el('r75-check-table').innerHTML='<table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>'+rows.map(([a,b])=>'<tr><td>'+safe(a)+'</td><td>'+safe(b)+'</td></tr>').join('')+'</tbody></table>';
 el('r75-json').textContent=JSON.stringify({source,input:request,assessment:out},null,2);
 el('r75-save-result').disabled=false;el('r75-save-svg').disabled=!(out.characteristic_bounds||out.characteristic_values);el('r75-save-pdf').disabled=false;
 el('r75-save-pdf').textContent=pdf?'Save this result report PDF':'Save complete study PDF';
}
function load(viewResult=false){try{const row=cfg.cases.find(r=>r.id===el('r75-model').value&&r.factor===Number(el('r75-factor').value));if(!row)throw Error('Saved example is unavailable.');fill(row.input);show(read(),row.output,'Saved checked model '+row.id+'; no new calculation',row.pdf_base64||null);if(viewResult)visit(el('r75-result'));}catch(e){setStatus(e.message);}}
function save(name,blob){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function checkedLatest(){if(!latest||JSON.stringify(read())!==latest.signature){invalidate('Inputs changed. Calculate these inputs or reload a checked example before saving a result.');throw Error('The previous result does not belong to the current inputs.');}return latest;}
function decode(b64){const s=atob(b64);return Uint8Array.from(s,c=>c.charCodeAt(0));}
async function run(){
 if(busy||!connection.enabled)return;
 let r;try{r=read();}catch(e){setStatus(e.message);visit(el('r75-action-status'));return;}
 invalidate();const rev=revision,body=JSON.stringify(r);busy=true;el('r75-run').disabled=true;setStatus('Calculating these parameters… The new result will open below.');
 try{
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body));
  const sha=Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,'0')).join('');
  const env={execution_id:'diagnosis_'+crypto.randomUUID().replaceAll('-',''),input_revision:rev,request_body:body,request_sha256:sha};
  const response=await fetch('/api/diagnose',{method:'POST',headers:{'Content-Type':'application/json','X-RMO-Token':connection.token},body:JSON.stringify(env)});
  const result=await response.json();
  if(revision!==rev||JSON.stringify(read())!==body){setStatus('Inputs changed during calculation. The older response was not displayed as a current result.');return;}
  if(response.status===409&&result.code==='CALCULATION_BUSY'){setStatus(result.error);visit(el('r75-action-status'));return;}
  if(!response.ok||result.error)throw Error(result.error||'The local diagnosis service did not complete.');
  const identity=result.identity;
  if(!identity||identity.execution_id!==env.execution_id||identity.input_revision!==rev||identity.request_sha256!==sha||identity.request_body!==body)throw Error('Response/input identity mismatch; result was not displayed.');
  show(r,result.assessment,'New calculation for these parameters; exact input and result preserved',result.pdf_base64);visit(el('r75-result'));
 }catch(e){setStatus('Calculation unavailable: '+e.message);visit(el('r75-action-status'));}finally{busy=false;syncRun();}
}

for(const k of ['r75-edit-inputs','r75-edit-result'])el(k).addEventListener('click',()=>visit(el('r75-inputs')));
el('r75-blank-inputs').addEventListener('click',()=>{
 const r=clone(cfg.cases[0].input);r.missing_reasons={};r.nominal.case_id='user_input';r.nominal.uncertainty={mode:'exact_synthetic',note:'User-entered normalized model inputs; inspect the supplied deterministic half-widths.'};
 for(const k of [...fields,'right.B.0']){put(r.nominal,k,null);r.half_widths[k]=0;}
 fill(r);setStatus('Blank input opened. Enter normalized values in the stated frame. Blank means unknown; give its reason. Half-width 0 means an exact model value. Gamma starts at 5/3; review this assumption. Calculate below when ready.');visit(el('r75-inputs'));
});
el('r75-load').addEventListener('click',()=>load(true));
el('r75-demo-top').addEventListener('click',()=>{el('r75-model').value='A63';el('r75-factor').value='0.01';el('r75-workspace').open=true;load();el('r75-tool').scrollIntoView({behavior:'smooth',block:'start'});});
el('r78-demo').addEventListener('click',()=>{el('r75-model').value='P01';el('r75-factor').value='0';el('r75-workspace').open=true;load(true);});
el('r79-demo').addEventListener('click',()=>{el('r75-model').value='P02';el('r75-factor').value='0.01';el('r75-workspace').open=true;load(true);});
el('r75-solar-top').addEventListener('click',()=>{el('r75-workspace').open=true;el('r75-solar-example').open=true;el('r75-solar-view').scrollIntoView({behavior:'smooth',block:'start'});});
for(const k of fields)for(const suffix of ['','-width','-reason','-reason-other'])el(id(k)+suffix).addEventListener(suffix==='-reason'?'change':'input',()=>{el(id(k)+suffix).removeAttribute('aria-invalid');reason(k);invalidate('Inputs edited. The saved result is no longer current; calculate or export this request.');});
el('r75-gamma').addEventListener('input',()=>invalidate('Gamma changed; the previous result is no longer current.'));
for(const k of ['model','factor'])el('r75-'+k).addEventListener('change',()=>{setStatus('Selection changed. Click Open saved model result to replace the current parameters and result.');});
el('r75-run').addEventListener('click',run);
el('r75-import').addEventListener('change',async()=>{const f=el('r75-import').files?.[0];if(!f)return;try{if(f.size>50000)throw Error('Input file exceeds 50 kB.');const r=JSON.parse(await f.text());fill(r);setStatus('Imported '+f.name+'. Inspect the values, then press Calculate these parameters below.');visit(el('r75-inputs'));}catch(e){setStatus('Import failed: '+e.message);}});
el('r75-export-input').addEventListener('click',()=>{try{save('RMO_local_input.json',new Blob([JSON.stringify(read(),null,2)],{type:'application/json'}));}catch(e){setStatus(e.message);}});
el('r75-save-result').addEventListener('click',()=>{try{const r=checkedLatest();save('RMO_local_result.json',new Blob([JSON.stringify({source:r.source,input:r.request,assessment:r.assessment},null,2)],{type:'application/json'}));}catch(e){setStatus(e.message);}});
el('r75-save-svg').addEventListener('click',()=>{try{const r=checkedLatest();save('RMO_local_speed_bounds.svg',new Blob([plot(r.assessment)],{type:'image/svg+xml'}));}catch(e){setStatus(e.message);}});
el('r75-save-pdf').addEventListener('click',()=>{try{const r=checkedLatest(),b64=r.pdf||cfg.study_pdf.split(',')[1];save(r.pdf?'RMO_local_result.pdf':'RMO_uncertainty_diagnosis.pdf',new Blob([decode(b64)],{type:'application/pdf'}));}catch(e){setStatus(e.message);}});
syncRun();
el('r75-run').textContent=connection.enabled?'3 · Calculate these parameters':'Calculation unavailable — offline file';
el('r75-run-help').textContent=connection.enabled?'Load a saved model, import a matching input file, or choose Enter my own parameters. After editing, calculate here; the new result opens below.':'This downloaded page is offline, so a new Python calculation is unavailable here. Use Open saved model result above to explore the saved models and error ranges.';
el('r75-connection').textContent=connection.enabled?'This page was served with the Python calculation service. Calculate these inputs runs the local diagnosis; it is not a full Riemann solve.':'Offline page: checked demos, parameters and downloads work here. A fresh diagnosis requires the Python service; editing alone does not recalculate the result.';
})();
