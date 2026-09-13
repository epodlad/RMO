/* Request association and lifecycle only. Does not classify physics. */
"use strict";
(function(root,factory){const api=factory();if(typeof module==="object"&&module.exports)module.exports=api;else root.RMOLocalClient=api;})(globalThis,function(){
  function envelope(C,snapshot,id){
    const text=JSON.stringify(snapshot.request);
    return {adapter_contract:"rmo-synthetic-adapter-draft-0.1.0",action:"run_synthetic_special_case",
      execution_id:id,request_json:text,request_body_sha256:C.sha256(text),input_revision:snapshot.revision,
      capability_profile:"R6B_SPECIAL_CASES_0_1_0_DRAFT"};
  }
  function matches(C,response,env,snapshot){
    const i=response&&response.identity;
    return !!i&&["execution_id","request_json","request_body_sha256","input_revision"].every(k=>i[k]===env[k])&&
      C.sha256(i.request_json)===i.request_body_sha256&&snapshot.revision===env.input_revision&&
      snapshot.report.input_status==="VALID"&&JSON.stringify(snapshot.request)===env.request_json;
  }
  function controller({C,bridge,send,notify,makeId}){
    let active=null;
    async function cancel(){
      if(!active)return;
      const job=active;job.cancelled=true;
      notify("cancelling",{});
      const e=job.env;
      try{await send("/api/cancel",{execution_id:e.execution_id,request_body_sha256:e.request_body_sha256,input_revision:e.input_revision});}
      catch(err){notify("cancel_error",{message:String(err.message)});}
    }
    bridge.subscribe(()=>{
      notify("stale",{});
      if(active){active.stale=true;void cancel();}
    });
    async function run(){
      if(active)return false;
      const s=bridge.snapshot();
      if(s.report.input_status!=="VALID") {notify("input_blocked",{status:s.report.input_status});return false;}
      if(s.request.uncertainty.mode!=="exact_synthetic") {notify("input_blocked",{status:"Covariance is metadata only; this route requires exact synthetic inputs."});return false;}
      const job={env:envelope(C,s,makeId()),stale:false,cancelled:false};active=job;
      notify("running",{envelope:job.env});
      try{
        const reply=await send("/api/run",job.env), result=reply.result;
        const current=bridge.snapshot();
        if(!job.stale&&!job.cancelled&&matches(C,result,job.env,current))notify("result",reply);
        else notify("history",{...reply,reason:"Not a result for the current input: edited, cancelled or response identity mismatch."});
      }catch(err){notify("error",{message:String(err.message)});}
      finally{active=null;notify("idle",{});}
      return true;
    }
    return Object.freeze({run,cancel,isRunning:()=>active!==null});
  }
  return {envelope,matches,controller};
});
