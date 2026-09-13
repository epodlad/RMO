/* Synthetic request validation only. No solver, observation import or inference. */
"use strict";
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.RMOPreflight = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const VERSION = "RMO-PREFLIGHT-0.2.0";
  const MAX_TEXT = 65536;
  const AXES = ["rho", "p", "u_n", "u_t1", "u_t2", "B_t1", "B_t2"];
  const FIELD_LIST = [];
  for (const [side, suffix] of [["left", "L"], ["right", "R"]]) {
    for (const key of AXES) {
      const tail = {rho:"rho",p:"p",u_n:"u/0",u_t1:"u/1",u_t2:"u/2",B_t1:"B_t/0",B_t2:"B_t/1"}[key];
      FIELD_LIST.push({name:key + "_" + suffix, path:"/initial_states/" + side + "/" + tail, side, key});
    }
  }
  FIELD_LIST.push({name:"B_n",path:"/shared_Bn",side:"shared",key:"B_n"},
                  {name:"gamma",path:"/physics/gamma",side:"shared",key:"gamma"});
  const names = FIELD_LIST.map(f => f.name);
  const knownPaths = new Set(FIELD_LIST.map(f => f.path));
  const isObject = x => x !== null && typeof x === "object" && !Array.isArray(x);
  const copy = x => JSON.parse(JSON.stringify(x));
  function canonical(x) {
    if (x === null) return "null";
    if (typeof x === "number") { if (!Number.isFinite(x)) throw Error("NONFINITE_JSON"); return JSON.stringify(x); }
    if (typeof x === "boolean" || typeof x === "string") return JSON.stringify(x);
    if (Array.isArray(x)) return "[" + x.map(canonical).join(",") + "]";
    if (isObject(x)) return "{" + Object.keys(x).sort().map(k => JSON.stringify(k) + ":" + canonical(x[k])).join(",") + "}";
    throw Error("NON_JSON_VALUE");
  }
  const same = (a,b) => { try { return canonical(a) === canonical(b); } catch (_) { return false; } };
  const ptr = (x, path) => path.slice(1).split("/").reduce((v,k) => v[k.replace(/~1/g,"/").replace(/~0/g,"~")], x);
  function setPath(x, path, value) {
    const keys = path.slice(1).split("/"); let obj = x;
    for (const k of keys.slice(0,-1)) obj = obj[k];
    obj[keys[keys.length-1]] = value;
  }
  function parseNumber(text) {
    const s = String(text).trim();
    if (!s) return {value:null};
    if (s.length > 128 || !/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(s))
      return {value:s,error:"Use one decimal number (dot separator), not a formula, comma decimal, NaN or Infinity."};
    const n = Number(s);
    if (!Number.isFinite(n)) return {value:s,error:"Number is not finite in binary64."};
    if (n === 0 && /[1-9]/.test(s.split(/[eE]/)[0])) return {value:s,error:"Number underflows to zero; it has not been accepted as zero."};
    return {value:n};
  }
  /* SHA-256 is used solely as a reproducibility fingerprint of canonical UTF-8 JSON. */
  function sha256(text) {
    const K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
      0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
      0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
      0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
      0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
      0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
      0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    const bytes = new TextEncoder().encode(text), n = Math.ceil((bytes.length + 9)/64)*64;
    const padded = new Uint8Array(n); padded.set(bytes); padded[bytes.length] = 128;
    const view = new DataView(padded.buffer), bits = bytes.length * 8;
    view.setUint32(n-8, Math.floor(bits / 4294967296)); view.setUint32(n-4, bits >>> 0);
    const H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const R = (x,b) => (x >>> b) | (x << (32-b)), W = new Uint32Array(64);
    for (let offset=0; offset<n; offset+=64) {
      for (let i=0;i<16;i++) W[i] = view.getUint32(offset+4*i);
      for (let i=16;i<64;i++) {
        const s0=R(W[i-15],7)^R(W[i-15],18)^(W[i-15]>>>3), s1=R(W[i-2],17)^R(W[i-2],19)^(W[i-2]>>>10);
        W[i]=(W[i-16]+s0+W[i-7]+s1)>>>0;
      }
      let [a,b,c,d,e,f,g,h]=H;
      for(let i=0;i<64;i++) {
        const t1=(h+(R(e,6)^R(e,11)^R(e,25))+((e&f)^(~e&g))+K[i]+W[i])>>>0;
        const t2=((R(a,2)^R(a,13)^R(a,22))+((a&b)^(a&c)^(b&c)))>>>0;
        h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
      }
      [a,b,c,d,e,f,g,h].forEach((v,i)=>{H[i]=(H[i]+v)>>>0;});
    }
    return H.map(v=>v.toString(16).padStart(8,"0")).join("");
  }
  function compileShape(schema) {
    const allowed = new Set(["$schema","$id","title","description","$defs","$ref","type","properties","required","additionalProperties","allOf","oneOf","const","enum","minItems","maxItems","uniqueItems","items","minLength"]);
    function inspect(s) {
      if (!isObject(s)) throw Error("Unsupported schema node");
      for (const k of Object.keys(s)) if (!allowed.has(k)) throw Error("Unsupported schema keyword: "+k);
      if (s.$ref) { if (!s.$ref.startsWith("#/")) throw Error("External schema references disabled"); ptr(schema,s.$ref.slice(1)); }
      for (const child of Object.values(s.properties || {})) inspect(child);
      for (const child of Object.values(s.$defs || {})) inspect(child);
      if (isObject(s.additionalProperties)) inspect(s.additionalProperties);
      if (s.items) inspect(s.items);
      for (const child of [...(s.allOf || []),...(s.oneOf || [])]) inspect(child);
    }
    inspect(schema);
    function visit(v,s,path,errors) {
      const fail = message => errors.push({path,code:"REQUEST_SHAPE_INVALID",message});
      if (s.$ref) visit(v,ptr(schema,s.$ref.slice(1)),path,errors);
      if (s.allOf) s.allOf.forEach(child=>visit(v,child,path,errors));
      if (s.oneOf) {
        const matches=s.oneOf.filter(child=>{const e=[];visit(v,child,path,e);return !e.length;}).length;
        if(matches!==1) fail("Expected exactly one permitted uncertainty representation.");
      }
      if (Object.hasOwn(s,"const") && !same(v,s.const)) fail("Value must match the fixed units, frame, role or mode specified here.");
      if (s.enum && !s.enum.some(x=>same(v,x))) fail("Value is not one of the permitted choices.");
      if (s.type) {
        const types = Array.isArray(s.type) ? s.type : [s.type];
        const ok=types.some(t=> t==="null" ? v===null : t==="number" ? typeof v==="number"&&Number.isFinite(v) : t==="object" ? isObject(v) : t==="array" ? Array.isArray(v) : t==="string" ? typeof v==="string" : false);
        if (!ok) {fail("Expected "+types.join(" or ")+"; numbers must be finite and cannot be booleans."); return;}
      }
      if (typeof v==="string" && s.minLength!==undefined && [...v].length<s.minLength) fail("Text cannot be empty.");
      if (Array.isArray(v)) {
        if (s.minItems!==undefined&&v.length<s.minItems) fail("Too few entries.");
        if (s.maxItems!==undefined&&v.length>s.maxItems) fail("Too many entries.");
        if (s.uniqueItems && v.some((x,i)=>v.slice(0,i).some(y=>same(x,y)))) fail("Duplicate entries are not allowed.");
        if (s.items) v.forEach((x,i)=>visit(x,s.items,path+"/"+i,errors));
      }
      if (isObject(v)) {
        for (const k of s.required||[]) if(!Object.hasOwn(v,k)) errors.push({path:path+"/"+k,code:"REQUEST_SHAPE_INVALID",message:"Required field is missing."});
        for (const k of Object.keys(v)) {
          const p=path+"/"+k.replace(/~/g,"~0").replace(/\//g,"~1");
          if (s.properties && Object.hasOwn(s.properties,k)) visit(v[k],s.properties[k],p,errors);
          else if(s.additionalProperties===false) errors.push({path:p,code:"UNEXPECTED_REQUEST_FIELD",message:"This field is not accepted. Evidence labels, results and extra inputs cannot be injected."});
          else if(isObject(s.additionalProperties)) visit(v[k],s.additionalProperties,p,errors);
        }
      }
    }
    return request => {const errors=[];visit(request,schema,"",errors);return errors;};
  }
  function covarianceIssues(unc) {
    if(unc.mode==="exact_synthetic") return [];
    const issues=[], add=message=>issues.push({path:"/uncertainty/covariance",code:"COVARIANCE_INVALID",message});
    const C=unc.covariance, k=unc.parameters.length;
    if(C.length!==k || C.some(row=>row.length!==k)) {add("Matrix dimensions must match the named uncertain-parameter order.");return issues;}
    if(C.some((row,i)=>row[i]<=0)) {add("Diagonal variances must be positive. Fixed parameters belong outside the uncertain subset.");return issues;}
    for(let i=0;i<k;i++) for(let j=0;j<k;j++) if(C[i][j]!==C[j][i]) {add("Matrix must be explicitly symmetric; no averaging is performed.");return issues;}
    const d=C.map((row,i)=>Math.sqrt(row[i])), L=Array.from({length:k},()=>Array(k).fill(0));
    const tol=64*Number.EPSILON*k;
    for(let i=0;i<k;i++) for(let j=0;j<=i;j++) {
      let v=(C[i][j]/d[i])/d[j];
      for(let m=0;m<j;m++) v-=L[i][m]*L[j][m];
      if(!Number.isFinite(v)) {add("Scaled covariance arithmetic is outside the supported numeric range.");return issues;}
      if(i===j) {
        if(v<=0) {add("Matrix is not positive definite (or is singular); no jitter or low-rank repair is performed.");return issues;}
        if(v<=tol) {add("Positive definiteness is not numerically resolved at the declared pivot threshold; no regularization is performed.");return issues;}
        L[i][j]=Math.sqrt(v);
      } else L[i][j]=v/L[j][j];
    }
    return issues;
  }
  function createEngine(schema,preset) {
    const shape=compileShape(schema);
    function check(request,parseIssues=[]) {
      const issues=parseIssues.map(copy), notes=[], base={version:VERSION,input_status:null,issues,notes,
        calculation:{status:"DISABLED",solver_called:false,reason:"Preflight only. No solver is connected and no MHD family is assessed."},
        uncertainty:{status:"NOT_CHECKED"},request_sha256:null,hash_format:"sorted-key compact JSON; UTF-8; no newline",preset_physical_match:false,full_preset_match:false};
      let text;
      try {text=canonical(request);if(new TextEncoder().encode(text).length>MAX_TEXT)throw Error("Request exceeds the 64 KiB implementation envelope.");}
      catch(e) {issues.push({path:"",code:"REQUEST_ENCODING_INVALID",message:String(e.message)});base.input_status="INVALID";return base;}
      issues.push(...shape(request));
      if(issues.length) {base.input_status="INVALID";return base;}
      const add=(path,code,message)=>issues.push({path,code,message});
      if(!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$/.test(request.request_id)) add("/request_id","REQUEST_ID_INVALID","Use 1–80 letters, digits, dots, underscores or hyphens, starting with a letter or digit.");
      let missing=0;
      for(const f of FIELD_LIST) {
        const value=ptr(request,f.path), reason=request.missing_reasons[f.path];
        if(value===null) {
          missing++;
          if(typeof reason!=="string"||!reason.trim()) add(f.path,"MISSING_REASON_REQUIRED","Blank/unknown value needs a reason. It is not assumed to be zero.");
        } else if(f.key==="rho"||f.key==="p") {
          if(value<=0) add(f.path,"INVALID_STATE","Density and thermal pressure must be positive; no floor is applied.");
          else if(value<=1e-12) add(f.path,"OUTSIDE_NUMERIC_DOMAIN","Positive value is at/below the frozen 1e-12 numeric limit; it is not clipped.");
        } else if(f.key==="gamma"&&value<=1) add(f.path,"INVALID_STATE","Gamma must exceed one.");
      }
      for(const [path,reason] of Object.entries(request.missing_reasons)) {
        if(!knownPaths.has(path)||ptr(request,path)!==null) add(path,"MISSING_REASON_NOT_APPLICABLE","A reason must refer to one currently null physical scalar.");
        if(!reason.trim()||reason.length>1024) add(path,"MISSING_REASON_INVALID","Supply a nonblank reason of at most 1024 characters.");
      }
      const covarianceErrors=covarianceIssues(request.uncertainty);
      issues.push(...covarianceErrors);
      base.uncertainty.status=covarianceErrors.length ? "INVALID_METADATA" : request.uncertainty.mode==="exact_synthetic" ? "EXACT_SYNTHETIC_NO_PROPAGATION" : "METADATA_ONLY_NOT_PROPAGATED";
      if(request.shared_Bn===0) notes.push("Zero normal field is not rejected by itself. General degenerate-fan coverage is not established.");
      if([request.initial_states.left.u[2],request.initial_states.right.u[2],request.initial_states.left.B_t[1],request.initial_states.right.B_t[1]].some(x=>x!==null&&x!==0))
        notes.push("Out-of-plane components are present in this basis. No targeted coplanar routing or hidden rotation is performed.");
      if(request.uncertainty.mode!=="exact_synthetic") notes.push(covarianceErrors.length
        ? "Covariance checks did not pass. No repair or uncertainty propagation has been performed."
        : "Covariance is checked and retained as metadata only. No samples, posterior or family probabilities have been computed.");
      base.input_status=issues.length ? "INVALID" : missing ? "INCOMPLETE" : "VALID";
      if(base.input_status!=="INVALID") base.request_sha256=sha256(text);
      const physicalKeys=["physics","normalization","geometry","shared_Bn","initial_states","policies"];
      base.preset_physical_match=physicalKeys.every(k=>same(request[k],preset[k]));
      base.full_preset_match=base.preset_physical_match&&same(request.uncertainty,preset.uncertainty)&&same(request.missing_reasons,preset.missing_reasons);
      if(missing) notes.push(missing+" physical value(s) remain unknown. This is an incomplete request, not an assumed zero state.");
      return base;
    }
    return {check,shape};
  }
  function makeBlank(preset) {
    const r=copy(preset);r.request_id="synthetic-request";
    FIELD_LIST.forEach(f=>setPath(r,f.path,null));r.missing_reasons={};r.uncertainty={mode:"exact_synthetic"};return r;
  }
  return {VERSION,MAX_TEXT,FIELD_LIST,names,copy,ptr,setPath,canonical,same,parseNumber,sha256,compileShape,createEngine,makeBlank};
});
