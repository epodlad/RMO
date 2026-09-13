(function(){
  'use strict';
  const $=id=>document.getElementById(id);
  const fields=['area','example','steps','expected','actual','browser','nickname'];
  let prepared=null;
  function values(){return fields.map(k=>$('r74-'+k).value.trim());}
  function invalidate(){prepared=null;$('r74-save').disabled=true;$('r74-report-preview').hidden=true;$('r74-report-status').textContent='Report changed. Preview it before saving.';}
  for(const k of fields){$('r74-'+k).addEventListener('input',invalidate);$('r74-'+k).addEventListener('change',invalidate);}
  function prepare(){
    const v=values();
    if(!v[3]||!v[4]){
      prepared=null;$('r74-save').disabled=true;$('r74-report-preview').hidden=true;
      $('r74-report-status').textContent='Please describe what you expected and what happened instead.';
      $('r74-'+(!v[3]?'expected':'actual')).focus();return false;
    }
    const labels=['Area','Event or example','Steps','Expected behaviour','What happened','Browser / operating system','Name or nickname'];
    const content='RMO QuickLook problem report\nInterface 0.4.6 · RMO-74\n\n'+labels.map((s,i)=>s+':\n'+(v[i]||'Not supplied')).join('\n\n')+'\n';
    prepared={values:JSON.stringify(v),text:content};
    $('r74-report-preview').textContent=content;$('r74-report-preview').hidden=false;
    $('r74-save').disabled=false;$('r74-report-status').textContent='Report ready to save. Nothing has been sent.';
    return true;
  }
  $('r74-preview').addEventListener('click',prepare);
  $('r74-save').addEventListener('click',()=>{
    if(!prepared||prepared.values!==JSON.stringify(values())){invalidate();return;}
    const blob=new Blob([prepared.text],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='RMO_problem_report.txt';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('r74-report-status').textContent='Download requested. Share the saved file if you choose; nothing has been sent.';
  });
  const config=$('local-config');
  if(config){try{if(JSON.parse(config.textContent).enabled){$('r74-connection-note').textContent='This page was opened through a calculation service. Check its connection status in the calculation controls below.';}}catch(_){/* Existing controls report connection issues. */}}
})();
