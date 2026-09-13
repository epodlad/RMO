/* One interface: saved references remain separate from newly computed results. */
"use strict";
(function(){
  const byId=id=>document.getElementById(id), C=globalThis.RMOPreflight, bridge=globalThis.RMOInputBridge;
  const cfg=JSON.parse(byId("local-config").textContent), preset=JSON.parse(byId("local-contact-input").textContent);
  const status=byId("live-status"), output=byId("live-output"), history=byId("live-history"), runButton=byId("live-run"), cancelButton=byId("live-cancel");
  let available=false,last=null;
  function el(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;}
  function focusOutput(){output.setAttribute("tabindex","-1");output.focus({preventScroll:true});output.scrollIntoView({block:"start"});}
  function details(title,node){const d=el("details");d.append(el("summary",title),node);return d;}
  function exportJSON(data,name){
    const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)+"\n"],{type:"application/json"}));
    const a=el("a");a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function rows(headers,values){
    const table=el("table"),head=el("tr");headers.forEach(x=>{const h=el("th",x);h.setAttribute("scope","col");head.append(h);});
    table.append(head);
    values.forEach(row=>{const tr=el("tr");row.forEach(x=>tr.append(el("td",x==null?"—":typeof x==="object"?JSON.stringify(x):x)));table.append(tr);});
    return table;
  }
  function svgNode(tag,attrs={},text){
    const n=document.createElementNS("http://www.w3.org/2000/svg",tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));
    if(text!==undefined)n.textContent=String(text);return n;
  }
  function fanPlot(waves){
    const speeds=waves.flatMap(w=>Array.isArray(w.speed)?w.speed:[w.speed]);
    if(!speeds.length||speeds.some(x=>typeof x!=="number"||!Number.isFinite(x)))return el("p","No finite wave-speed plot is available for this result.");
    let low=Math.min(0,...speeds),high=Math.max(0,...speeds),pad=Math.max((high-low)*.15,.1);low-=pad;high+=pad;
    const X=x=>60+600*(x-low)/(high-low),svg=svgNode("svg",{viewBox:"0 0 760 335",role:"img","aria-label":"Newly calculated wave fan. Horizontal position x and vertical time t, normalized."});
    svg.append(svgNode("rect",{width:760,height:335,fill:"white"}));
    svg.append(svgNode("path",{d:"M60 40 V255 H660",fill:"none",stroke:"#263c40"}));
    svg.append(svgNode("text",{x:62,y:20,"font-size":15},"New calculation: wave fan (x = speed × t)"));
    svg.append(svgNode("text",{x:10,y:43,"font-size":13},"t = 1"),svgNode("text",{x:15,y:260,"font-size":13},"t = 0"));
    for(let i=0;i<=4;i++){const v=low+(high-low)*i/4;svg.append(svgNode("text",{x:X(v),y:278,"text-anchor":"middle","font-size":12},Number(v.toPrecision(4))));}
    svg.append(svgNode("text",{x:340,y:304,"text-anchor":"middle","font-size":14},"x (normalized)"));
    const legend=[];
    waves.forEach((w,i)=>{
      const color=w.structure==="contact"?"#37434a":w.structure==="rarefaction"?"#276aa0":"#197267";
      if(Array.isArray(w.speed))svg.append(svgNode("polygon",{points:`${X(0)},255 ${X(w.speed[0])},45 ${X(w.speed[1])},45`,fill:color,"fill-opacity":.15,stroke:color}));
      else svg.append(svgNode("line",{x1:X(0),y1:255,x2:X(w.speed),y2:45,stroke:color,"stroke-width":3,"stroke-dasharray":w.structure==="contact"?"7 4":"none"}));
      legend.push(`${i+1}: ${w.structure} (${w.family})`);
    });
    const box=el("div");box.append(svg,el("p",legend.join(" · ")),el("p","Shading represents a rarefaction interval, not a discontinuity. Wave labels come from the checked synthetic result; this is not a complete branch map."));return box;
  }
  function contactPlot(request,speed){
    const left=request.initial_states.left.rho,right=request.initial_states.right.rho;
    if(![left,right,speed].every(Number.isFinite))return el("p","Density plot unavailable.");
    const span=Math.max(.5,Math.abs(speed)*.5),lo=speed-span,hi=speed+span;
    const X=x=>65+585*(x-lo)/(hi-lo),Y=r=>225-165*r/Math.max(left,right);
    const svg=svgNode("svg",{viewBox:"0 0 740 295",role:"img","aria-label":"Calculated contact density profile: a step at the newly calculated contact speed."});
    svg.append(svgNode("rect",{width:740,height:295,fill:"white"}),svgNode("text",{x:65,y:24,"font-size":16},"Density across the calculated contact"));
    svg.append(svgNode("path",{d:"M65 40 V225 H650",stroke:"#263c40",fill:"none"}));
    svg.append(svgNode("path",{d:`M${X(lo)} ${Y(left)} H${X(speed)} V${Y(right)} H${X(hi)}`,stroke:"#197267","stroke-width":3,fill:"none"}));
    svg.append(svgNode("text",{x:80,y:Y(left)-9,"font-size":14},"LEFT ρ = "+left),svgNode("text",{x:440,y:Y(right)-9,"font-size":14},"RIGHT ρ = "+right));
    svg.append(svgNode("text",{x:X(speed),y:250,"text-anchor":"middle","font-size":14},"contact: "+Number(speed.toPrecision(8))));
    svg.append(svgNode("text",{x:350,y:279,"text-anchor":"middle","font-size":14},"x/t (normalized)"));return svg;
  }
  function render(reply){
    const r=reply.result;last=r;output.replaceChildren(el("h3","Result in one sentence"));
    const checked=(r.policy_runs||[]).flatMap(p=>(p.validation?.checked_solutions||[]).map(s=>({policy:p.policy,solution:s})));
    const first=checked[0], waves=first?.solution.waves||[], contact=r.capability?.profile==="CONTACT"&&waves.length===1&&waves[0].structure==="contact";
    const s=contact?waves[0].speed:null;
    const sentence=contact?`A contact discontinuity was calculated and checked: the density boundary moves at ${Number(s.toPrecision(8))} in normalized units, while pressure, velocity and magnetic field remain continuous.`:r.presentation.sentence;
    output.append(el("p",contact?"Contact: a density boundary travels with the plasma.":checked.length?"A model solution passed the checks; complete branch coverage is not established.":"No checked new solution is available for these inputs."));
    output.append(details("Physical explanation",el("p",sentence)));
    if(contact)output.append(el("p","For this solution: a contact, not a shock."));
    if(checked.length)output.append(el("p","Only the returned, independently checked solution(s) are described. Full MHD coverage, stability and a solar interpretation have not been established."));
    output.append(el("p","What next? "+(r.presentation.next_action||"Inspect the attempt details.")));
    output.append(el("p","Actual solver calls: "+r.execution.solver_call_count+". Execution: "+r.execution.status+". Requested policies are reported separately below."));
    if(contact)output.append(contactPlot(r.input.parsed_snapshot,s));
    for(const item of checked){
      const box=el("div");box.append(fanPlot(item.solution.waves),rows(["Order","Structure","Family","Speed / interval"],item.solution.waves.map(w=>[w.order,w.structure,w.family,w.speed])));
      output.append(details("Calculated wave fan — "+item.policy,box));
    }
    const checkBox=el("div");
    for(const p of r.policy_runs||[])checkBox.append(el("h4",p.policy+": "+p.status),rows(["Check","Status","Value","Tolerance"],(p.validation?.checks||[]).map(c=>[c.check,c.status,c.value,c.tolerance])));
    checkBox.append(el("p","— means no separate numerical value or tolerance was reported; it does not mean zero."));
    output.append(details("Independent checks and policy outcomes",checkBox));
    output.append(el("p",reply.saved_directory ? "Saved on the calculation machine: "+reply.saved_directory : "Save the input and result JSON to keep this calculation."));
    const download=el("button","Export computed result JSON (not just the request)");download.type="button";download.addEventListener("click",()=>exportJSON(r,"RMO_computed_"+r.identity.execution_id+".json"));output.append(download);
    output.append(details("Exact input, result and provenance",el("pre",JSON.stringify(r,null,2))));
    focusOutput();
  }
  async function send(path,payload){
    if(!available)throw new Error("Python connection is not available.");
    const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),path==="/api/run"?40000:6000);
    try{
      const response=await fetch(path,{method:payload===undefined?"GET":"POST",credentials:"same-origin",cache:"no-store",signal:abort.signal,
        headers:{"Content-Type":"application/json","X-RMO-Token":cfg.token},...(payload===undefined?{}:{body:JSON.stringify(payload)})});
      if(Number(response.headers.get("Content-Length"))>3*1024*1024)throw new Error("Response exceeds display limit.");
      const text=await response.text();if(text.length>3*1024*1024)throw new Error("Response exceeds display limit.");
      const data=JSON.parse(text);if(!response.ok)throw new Error(data.error||"Local service error "+response.status);return data;
    }finally{clearTimeout(timer);}
  }
  function notify(event,data){
    if(event==="running"){last=null;output.replaceChildren(el("p","Calculating this exact input. No saved result is used as a fallback."));runButton.disabled=true;cancelButton.disabled=false;status.textContent="Running; total adapter budget: 30 seconds.";}
    if(event==="input_blocked"){status.textContent="No calculation: "+data.status+". Use Check input to see details.";bridge.check();}
    if(event==="stale"){last=null;output.replaceChildren(el("p","Input changed. No previous computed result is current. Calculate again when ready."));}
    if(event==="cancelling")status.textContent="Cancellation requested. Waiting for the attempt to finish; any returned result will be history only.";
    if(event==="cancel_error")status.textContent="Cancellation could not be confirmed. The 30-second server budget still applies. "+data.message;
    if(event==="result"){render(data);status.textContent="Attempt finished. Read the short answer and its limits below.";}
    if(event==="history"){
      history.hidden=false;history.open=true;history.replaceChildren(el("summary","Previous attempt — not the current input"),el("p",data.reason));
      const b=el("button","Export previous attempt JSON");b.addEventListener("click",()=>exportJSON(data,"RMO_previous_attempt.json"));history.append(b,details("Exact previous response",el("pre",JSON.stringify(data,null,2))));
      output.replaceChildren(el("p","No current result. A late or cancelled response was kept separately, not applied to the edited fields."));
      status.textContent="Previous response retained as history only.";
    }
    if(event==="error"){last=null;output.replaceChildren(el("p","No current result: "+data.message),el("p","No physical family is excluded by a connection failure. Completed attempts, if any, remain on the calculation machine. Reload before retrying if the server stopped."));status.textContent="Attempt unavailable; no saved-result fallback.";}
    if(event==="idle"){runButton.disabled=!available;cancelButton.disabled=true;}
  }
  const controller=globalThis.RMOLocalClient.controller({C,bridge,send,notify,makeId:()=>"rmo_"+crypto.randomUUID()});
  byId("live-load-contact").addEventListener("click",()=>{bridge.load(preset);bridge.check();status.textContent=available?"Contact values loaded. Click Calculate new synthetic solution.":"Contact values loaded for inspection. This offline file cannot run Python.";});
  byId("live-edit").addEventListener("click",()=>bridge.showParameters());
  runButton.addEventListener("click",()=>void controller.run());cancelButton.addEventListener("click",()=>void controller.cancel());
  if(cfg.enabled===true&&location.origin===cfg.origin){
    available=true;
    status.textContent="Checking the Python calculation connection…";
    send("/api/status").then(data=>{
      if(data.ready!==true)throw new Error("Service not ready");
      runButton.disabled=false;status.textContent="Python connected on the calculation machine. Load contact → Calculate. Your browser's operating system does not select the solver.";
    }).catch(err=>{available=false;runButton.disabled=true;status.textContent="Connection unavailable: "+err.message;});
  }else{
    runButton.disabled=true;cancelButton.disabled=true;
    status.textContent="Offline preview: saved examples and input checks work, but this file does not run Python. A hosted calculation URL is not available yet. No installation is needed just to view this page.";
  }
})();
