/* Editable synthetic request UI; all effects are local and no solver is called. */
"use strict";
(function () {
  const C=globalThis.RMOPreflight, cfg=JSON.parse(document.getElementById("preflight-config").textContent);
  const engine=C.createEngine(cfg.schema,cfg.preset), editor=document.getElementById("input-editor");
  const reportNode=document.getElementById("input-report"), reference=document.getElementById("saved-reference-note");
  const context=document.getElementById("example-context");
  const fields={}, reasonFields={}, changeListeners=[];let revision=0,ready=null;
  const connectionNode=document.getElementById("local-config");
  const connected=connectionNode&&JSON.parse(connectionNode.textContent).enabled===true;
  function el(tag,text,cls) {const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;}
  function control(tag,id,type) {const x=el(tag);x.id=id;if(type)x.type=type;return x;}
  function button(id,text,fn) {const x=control("button",id,"button");x.textContent=text;x.addEventListener("click",fn);return x;}
  function labelled(parent,text,input) {const label=el("label",text);label.htmlFor=input.id;parent.append(label,input);}
  function visit(id,parents=[]) {
    for(const parent of parents) document.getElementById(parent).open=true;
    const target=document.getElementById(id);
    for(let n=target;n;n=n.parentElement) if(n.tagName.toLowerCase()==="details") n.open=true;
    target.setAttribute("tabindex","-1");
    if(typeof target.focus==="function") target.focus({preventScroll:true});
    if(typeof target.scrollIntoView==="function") target.scrollIntoView({block:"start",behavior:"auto"});
  }
  function showParameters() {visit("advanced-input");}
  function resetReport(message) {
    revision++;ready=null;exportButton.disabled=true;
    reportNode.replaceChildren(el("p",message,"muted"));
    reference.textContent="Saved reference only — does not correspond to the current edited request. No new solution has been calculated.";
    Object.values(fields).forEach(x=>x.removeAttribute("aria-invalid"));
    context.textContent="Input changed or cleared. A tutorial expectation does not apply until the current request is checked.";
    changeListeners.forEach(fn=>fn(revision));
  }
  const idInput=control("input","request-id","text");idInput.maxLength=80;idInput.value="synthetic-request";
  idInput.addEventListener("input",()=>resetReport("Request changed — check the input again."));
  const idWrap=el("div",undefined,"input-id");labelled(idWrap,"Request name (letters, digits, dot, underscore or hyphen)",idInput);editor.append(idWrap);
  const stateGrid=el("div",undefined,"state-grid");
  const labels={rho:"Mass density ρ",p:"Thermal gas pressure p",u_n:"Normal velocity u_n",u_t1:"Tangential velocity u_t1",u_t2:"Tangential velocity u_t2",B_t1:"Tangential field B_t1",B_t2:"Tangential field B_t2",B_n:"Shared normal field B_n",gamma:"Ratio of specific heats γ"};
  const groups={};
  for(const [side,title] of [["left","Initial LEFT state · X_L0"],["right","Initial RIGHT state · X_R0"],["shared","Shared settings"]]) {
    const box=el("fieldset");box.append(el("legend",title));groups[side]=box;
    if(side==="shared") editor.append(box);else stateGrid.append(box);
  }
  editor.append(stateGrid);
  function reasonVisibility(f) {
    const isBlank=!fields[f.name].value.trim();reasonFields[f.name].parentNode.hidden=!isBlank;
  }
  for(const f of C.FIELD_LIST) {
    const wrap=el("div",undefined,"scalar-field"), x=control("input","value-"+f.name,"text");
    x.inputMode="decimal";x.autocomplete="off";x.maxLength=128;x.placeholder="Blank = unknown";
    labelled(wrap,labels[f.key],x);fields[f.name]=x;
    if(f.key==="gamma") {
      const help=el("p","For Brio–Wu, keep 2. Gamma sets the ideal-gas pressure–energy relation; it is not a temperature.","help-small");
      help.id="gamma-field-help";wrap.append(help);
      wrap.append(button("explain-gamma","What is γ?",()=>visit("gamma-help",["help-panel"])));
    }
    const rw=el("div",undefined,"reason-field"), r=control("input","reason-"+f.name,"text");
    r.maxLength=1024;r.placeholder="Required if this value is unknown";labelled(rw,"Reason for unknown value",r);
    x.setAttribute("aria-describedby",r.id+(f.key==="gamma"?" gamma-field-help":""));reasonFields[f.name]=r;wrap.append(rw);groups[f.side].append(wrap);
    x.addEventListener("input",()=>{reasonVisibility(f);resetReport("Input changed — check again. No previous result applies to this edited request.");});
    r.addEventListener("input",()=>resetReport("Missing-value reason changed — check again."));
  }
  const policies=el("fieldset");policies.append(el("legend",connected?"Policies for the next explicit calculation":"Admissibility policies (stored, not executed)"));
  const policyInputs=[];
  for(const [id,title] of [["REGULAR_EVOLUTIONARY_1.0","Regular evolutionary policy"],["ENUMERATE_NONREGULAR_1.0","Also retain non-regular possibilities"]]) {
    const wrap=el("div",undefined,"checkbox-row"), x=control("input","policy-"+id,"checkbox");x.checked=true;x.value=id;
    labelled(wrap,title,x);x.addEventListener("change",()=>resetReport("Policy selection changed — check again."));
    policies.append(wrap);policyInputs.push(x);
  }
  editor.append(policies);
  const uncertainty=el("fieldset");uncertainty.append(el("legend","Uncertainty description"));
  uncertainty.append(el("p","For the built-in examples, leave Exact synthetic values selected. You do not need a covariance matrix.","help-small"));
  const covarianceHelp=el("details");covarianceHelp.id="covariance-help";
  covarianceHelp.append(el("summary","What is covariance, and why would I use it?"),
    el("p","Covariance describes how uncertain inputs vary together. For example, density and pressure estimates can share measurement errors. Treating them as unrelated could give a misleading picture of what is known."),
    el("p","The diagonal entries give the variance of each named parameter; the other entries describe their pairwise covariance. Zero covariance alone does not always mean full statistical independence."),
    el("p","This is optional expert input, not something to invent for a demonstration. Exact synthetic values are deliberately specified mathematical numbers, not a claim of perfect solar measurements. Here covariance is only checked and saved: no uncertainty propagation or MHD classification is performed."));
  uncertainty.append(covarianceHelp);
  const mode=control("select","uncertainty-mode");
  for(const [value,title] of [["exact_synthetic","Exact synthetic values"],["joint_covariance_metadata_only","Joint covariance — metadata only, not propagated"]]) {
    const o=el("option",title);o.value=value;mode.append(o);
  }
  mode.value="exact_synthetic";labelled(uncertainty,"How are these mathematical inputs specified?",mode);
  const covBox=el("div",undefined,"covariance-box");covBox.id="covariance-box";covBox.hidden=true;
  const params=control("input","covariance-parameters","text");params.maxLength=256;params.placeholder="rho_L, p_L";
  labelled(covBox,"Uncertain parameters, in matrix order (comma separated)",params);
  const matrix=control("textarea","covariance-matrix");matrix.rows=4;matrix.maxLength=32768;matrix.placeholder="0.0001 0.00005\n0.00005 0.0004";
  labelled(covBox,"Covariance: one row per line, numbers separated by spaces",matrix);
  const names=el("details");names.append(el("summary","Permitted parameter names"),el("p",C.names.join(", ")));covBox.append(names);
  covBox.append(el("p","Matrix order follows your named parameters. No reordering, averaging, sampling or probability calculation is performed.","muted"));
  covBox.append(button("load-covariance-example","Load a two-parameter metadata example",()=>{
    params.value="rho_L, p_L";matrix.value="0.0001 0.00005\n0.00005 0.0004";resetReport("Artificial covariance example entered. Check its input; this is not inferred uncertainty.");
  }));
  uncertainty.append(covBox);editor.append(uncertainty);
  mode.addEventListener("change",()=>{covBox.hidden=mode.value==="exact_synthetic";resetReport("Uncertainty mode changed — check again.");});
  params.addEventListener("input",()=>resetReport("Uncertain-parameter order changed — check again."));
  matrix.addEventListener("input",()=>resetReport("Covariance values changed — check again."));
  function collect() {
    const request=C.makeBlank(cfg.preset), parseIssues=[];request.request_id=idInput.value.trim();
    for(const f of C.FIELD_LIST) {
      const parsed=C.parseNumber(fields[f.name].value);C.setPath(request,f.path,parsed.value);
      if(parsed.error)parseIssues.push({path:f.path,code:"NUMBER_TEXT_INVALID",message:parsed.error});
      if(parsed.value===null&&reasonFields[f.name].value.trim())request.missing_reasons[f.path]=reasonFields[f.name].value.trim();
    }
    request.policies=policyInputs.filter(x=>x.checked).map(x=>x.value);
    if(mode.value!=="exact_synthetic") {
      const names=params.value.trim()?params.value.split(",").map(s=>s.trim()):[];
      const rows=matrix.value.trim()?matrix.value.trim().split(/\r?\n/):[];
      const covariance=rows.map((row,i)=>row.trim().split(/\s+/).map((s,j)=>{
        const v=C.parseNumber(s);if(v.error||v.value===null)parseIssues.push({path:"/uncertainty/covariance/"+i+"/"+j,code:"COVARIANCE_NUMBER_INVALID",message:v.error||"Missing matrix value."});return v.value;
      }));
      request.uncertainty={mode:"joint_covariance_metadata_only",parameters:names,covariance,propagation:"not_implemented"};
    }
    return {request,parseIssues};
  }
  function fill(request) {
    idInput.value=request.request_id;
    for(const f of C.FIELD_LIST) {
      const v=C.ptr(request,f.path);fields[f.name].value=v===null?"":String(v);
      reasonFields[f.name].value=request.missing_reasons[f.path]||"";reasonVisibility(f);
    }
    policyInputs.forEach(x=>{x.checked=request.policies.includes(x.value);});
    mode.value=request.uncertainty.mode;covBox.hidden=mode.value==="exact_synthetic";
    params.value="";matrix.value="";
  }
  function renderReport(report,request) {
    reportNode.replaceChildren();
    const titles={VALID:"Your input is ready.",INCOMPLETE:"Some information is still missing.",INVALID:"The input needs a correction."};
    const outcomes={VALID:"All required values are present and passed the input checks.",INCOMPLETE:"The known values passed the checks, but one or more values are still unknown. Their reasons have been kept.",INVALID:"At least one value or setting failed the input checks. Nothing was silently repaired."};
    const next={VALID:"Use Calculate this input to run these values, or View / edit parameters to change them.",INCOMPLETE:"Click View / edit parameters to supply missing values if you know them. Otherwise, keep them unknown; you may export this incomplete draft.",INVALID:"Click View / edit parameters to correct the reported fields, or load an example again. Then click Check input. Export is blocked while errors remain."};
    reportNode.append(el("h3",titles[report.input_status]),el("p",outcomes[report.input_status]),el("p","What next? "+next[report.input_status]));
    const actions=el("div",undefined,"preflight-actions");
    if(report.input_status==="VALID") {
      const calculate=button("report-calculate","4 · Calculate this input",()=>document.getElementById("live-run").click());
      calculate.className="primary";calculate.disabled=true;
      calculate.setAttribute("aria-describedby","report-calculation-status");actions.append(calculate);
    }
    actions.append(button("report-edit-parameters","View / edit parameters",showParameters));reportNode.append(actions);
    if(report.input_status==="VALID") {
      const status=el("p");status.id="report-calculation-status";status.setAttribute("role","status");reportNode.append(status);
    }
    const badge=el("strong","INPUT "+report.input_status,"badge input-status");reportNode.append(badge);
    const information=el("details");information.append(el("summary","What the input check means"));
    information.append(el("p",report.input_status==="VALID"?"Input checks passed. This is not support for an MHD interpretation.":report.input_status==="INCOMPLETE"?"Unknown values are retained with reasons. This request is not ready for physical computation.":"Correct the listed input errors. Values have not been repaired or replaced."));
    information.append(el("p",connected?"Input check only: this action did not run the solver. Use Calculate this input for an explicit, separate attempt.":"Calculation: DISABLED. No solver has run; no shock, wave family or observational classification has been assigned."));
    const uncertaintyText={NOT_CHECKED:"Uncertainty could not be checked because input errors remain.",INVALID_METADATA:"The covariance description needs correction; no uncertainty was propagated.",EXACT_SYNTHETIC_NO_PROPAGATION:"These are specified mathematical values. No observational uncertainty was inferred.",METADATA_ONLY_NOT_PROPAGATED:"Covariance metadata passed its checks. It has not been propagated into a physical result."};
    information.append(el("p",uncertaintyText[report.uncertainty.status]||"Uncertainty status is available in the technical report."));
    reportNode.append(information);
    if(report.issues.length) {
      const readable=el("ul");
      for(const issue of report.issues) {
        const f=C.FIELD_LIST.find(f=>f.path===issue.path), name=f?(f.side==="shared"?"":f.side.toUpperCase()+" — ")+labels[f.key]:issue.path.startsWith("/uncertainty")?"Uncertainty description":issue.path==="/request_id"?"Request name":"Request settings";
        readable.append(el("li",name+": "+issue.message));
      }
      reportNode.append(readable);
      const table=el("table"), head=el("tr");["Field", "Code", "Explanation"].forEach(t=>head.append(el("th",t)));table.append(head);
      for(const issue of report.issues) {
        const row=el("tr");[issue.path||"Request",issue.code,issue.message].forEach(t=>row.append(el("td",t)));table.append(row);
        const f=C.FIELD_LIST.find(f=>f.path===issue.path);if(f)fields[f.name].setAttribute("aria-invalid","true");
      }
      const errors=el("details");errors.append(el("summary","Technical error details"),table);reportNode.append(errors);
    }
    if(report.input_status==="INCOMPLETE") {
      const missing=el("ul");
      for(const f of C.FIELD_LIST) if(C.ptr(request,f.path)===null) missing.append(el("li",(f.side==="shared"?"":f.side.toUpperCase()+" — ")+labels[f.key]+": unknown. "+request.missing_reasons[f.path]));
      reportNode.append(missing);
    }
    if(report.notes.length){const ul=el("ul");report.notes.forEach(note=>ul.append(el("li",note)));information.append(ul);}
    if(report.request_sha256)information.append(el("p","Canonical request SHA-256: "+report.request_sha256,"fingerprint"));
    const detail=el("details");detail.append(el("summary",report.input_status==="INVALID"?"Current draft JSON — input errors remain":"Checked request JSON — input only"),el("pre",JSON.stringify(request,null,2)));reportNode.append(detail);
    const trace=el("details");trace.append(el("summary","Preflight report — no physical result"),el("pre",JSON.stringify(report,null,2)));reportNode.append(trace);
    reference.textContent=report.full_preset_match
      ? "The checked values match the Brio–Wu preset, including gamma, frame, policies and uncertainty mode. The examples below are saved references; no new calculation has run."
      : "Saved reference only — does not correspond to this checked request. Do not interpret a saved candidate label as the result of your edited input.";
  }
  function checkInput() {
    ready=null;exportButton.disabled=true;
    try {
      const {request,parseIssues}=collect(), report=engine.check(request,parseIssues);renderReport(report,request);
      if(report.input_status!=="INVALID") {
        ready={request:C.copy(request),canonical:C.canonical(request),report,revision};exportButton.disabled=false;
        exportButton.textContent=report.input_status==="INCOMPLETE"?"Export incomplete request (not a result)":"Export request JSON (not a result)";
      }
      document.dispatchEvent(new Event("rmo-input-checked"));
      visit("input-report");
    }catch(e) {reportNode.replaceChildren(el("p","CHECK UNAVAILABLE: "+String(e.message)+". No result or export is available."));}
  }
  function exportRequest() {
    if(!ready||ready.revision!==revision)return;
    const {request,parseIssues}=collect();
    if(parseIssues.length||!C.same(request,ready.request)) {resetReport("Input changed since checking — export blocked. Check again.");return;}
    try {
      const blob=new Blob([JSON.stringify(ready.request,null,2)+"\n"],{type:"application/json;charset=utf-8"});
      const url=URL.createObjectURL(blob), a=el("a");a.href=url;a.download="RMO_synthetic_request.json";
      document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
      reportNode.append(el("p","Local JSON download requested. It contains input only, not a solved fan or classification."));
    }catch(e){reportNode.append(el("p","Export unavailable in this browser: "+String(e.message)+". No upload was attempted."));}
  }
  function loadExample(kind) {
    const request=C.copy(cfg.preset);
    let title="Example 1 · Brio–Wu: complete synthetic input", expectation="Expected input status: VALID. This means the input checks pass, not that a physical solution was calculated.";
    if(kind==="unknown") {
      request.request_id="tutorial-unknown-Bn";request.shared_Bn=null;
      request.missing_reasons["/shared_Bn"]="Deliberately withheld for this synthetic tutorial; not a solar measurement.";
      title="Example 2 · One unknown value";expectation="Expected input status: INCOMPLETE. B_n is deliberately unknown and has a reason. It is not replaced by zero.";
    } else if(kind==="invalid") {
      request.request_id="tutorial-invalid-pressure";request.initial_states.right.p=-0.1;
      title="Example 3 · An intentional input error";expectation="Expected input status: INVALID. Right-side pressure is deliberately negative. This tests error reporting; it is not a physical plasma example.";
    }
    fill(request);resetReport("Example loaded automatically. Click Check input next. No manual entry or JSON export is required.");
    context.replaceChildren(el("strong","Loaded: "+title),el("p",expectation));
    if(kind==="brio") {
      const view=button("loaded-brio-view","View Brio–Wu saved solutions",()=>{
        const choice=document.getElementById("r63-result-choice");choice.value="brio";choice.dispatchEvent(new Event("change"));visit("r63-results");
      });
      view.className="primary";context.append(el("p","Explore the saved solutions, or check and inspect the loaded parameters. A new Brio–Wu calculation is not available here."),view);
    } else context.append(el("p","Click Check input to see the explanation of this exercise."));
    visit("example-context");
  }
  const controls=el("div",undefined,"preflight-actions");
  const presetButton=button("load-preset","Load Brio–Wu · saved solutions only",()=>loadExample("brio"));
  presetButton.className="secondary-start";
  const exampleHost=document.getElementById("guided-examples");
  exampleHost.append(presetButton);
  const exercises=el("details");exercises.id="optional-exercises";
  exercises.append(el("summary","Optional exercises — missing values and errors"),el("p","These are deliberate input tests, not warnings about your current request.","help-small"));
  const extra=el("div",undefined,"example-choice");
  for(const [kind,id,title,description] of [
    ["unknown","load-unknown-example","Example 2 · An unknown value","Learn why missing information is not the same as zero."],
    ["invalid","load-invalid-example","Example 3 · Deliberate error exercise","This example supplies negative pressure on purpose. It tests error reporting; it is not a warning about your input."]]) {
    const box=el("div");box.append(el("h3",title),el("p",description),button(id,"Load this input example",()=>loadExample(kind)));extra.append(box);
  }
  exercises.append(extra);exampleHost.append(exercises);
  const resetButton=button("reset-input","Reset — clear all physical fields",()=>{fill(C.makeBlank(cfg.preset));resetReport("Physical fields cleared. No unknown has been assumed to be zero.");});
  const checkButton=button("check-input","3 · Check input",checkInput);
  const exportButton=button("export-request","Export request JSON (optional; not a result)",exportRequest);exportButton.disabled=true;
  document.getElementById("check-input-after-edit").addEventListener("click",checkInput);
  controls.append(checkButton,button("show-parameters","View / edit parameters",showParameters),el("span",connected?"The check report and Calculate button appear below.":"Input check only. No solver is connected.","help-small"));
  document.getElementById("preflight-controls").append(controls);
  document.getElementById("help-navigation").append(
    button("open-help","Help",()=>visit("help-panel")),
    button("learn-riemann","Learn about Riemann solutions",()=>visit("riemann-help",["help-panel"])),
    button("view-saved","View a saved solution",()=>visit("saved-solutions")));
  const optional=el("div",undefined,"preflight-actions");optional.append(exportButton,resetButton);document.getElementById("optional-controls").append(optional);
  fill(C.makeBlank(cfg.preset));
  resetReport("Load contact to try a calculation, choose Brio–Wu to explore saved solutions, or enter your own values. Then check the input.");
  context.textContent="No example loaded yet. Contact is the simplest calculation example. Open Parameters to enter your own normalized synthetic values.";
  // Read current fields through the same parser. Never accept a VALID badge as input.
  globalThis.RMOInputBridge=Object.freeze({
    snapshot(){const x=collect();return {request:C.copy(x.request),report:engine.check(x.request,x.parseIssues),revision};},
    load(request){
      if(request.uncertainty.mode!=="exact_synthetic")throw new Error("This loader accepts exact synthetic examples only.");
      fill(C.copy(request));resetReport("Synthetic example loaded. Check input, then explicitly calculate if local Python is connected.");
      context.textContent="Contact example loaded into the actual fields. You may edit both normal velocities before calculating.";
    },
    subscribe(fn){changeListeners.push(fn);},
    check:checkInput,
    showParameters
  });
})();
