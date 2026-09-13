/* RMO-67: literature constraints and explicit assumed beta. No solver calls. */
(function (root) {
  'use strict';
  const SCHEMA = 'rmo-literature-draft-0.1.0';
  const copy = x => JSON.parse(JSON.stringify(x));
  const numberPattern = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
  function number(text, label, optional = false) {
    if (typeof text !== 'string' || text.length > 100) throw Error(label + ': enter a number.');
    if (text.trim() === '' && optional) return null;
    if (!numberPattern.test(text.trim()) || !Number.isFinite(Number(text))) throw Error(label + ': enter a finite decimal number.');
    return Number(text);
  }
  function shortText(value, label, max = 2000) {
    if (typeof value !== 'string' || value.length > max) throw Error(label + ': text is missing or too long.');
    return value;
  }
  function blankBeta() {
    return {mode:'unknown', beta0:'', low:'', high:'', height:'', reference_height:'', scale_height:'', plot_min:'', plot_max:'', basis:'', origin:'user_assumption'};
  }
  function rowFrom(v) {
    return {value: v.value == null ? '' : String(v.value), low: v.range ? String(v.range[0]) : '', high: v.range ? String(v.range[1]) : '', error: v.error == null ? '' : String(v.error), note:''};
  }
  function draft(card) {
    return {event_id:card.id, rows:card.values.map(rowFrom), beta:blankBeta(), nickname:'', region:'', notes:''};
  }
  function illustrativeBeta() {
    return {mode:'profile', beta0:'0.1', low:'', high:'', height:'100', reference_height:'100', scale_height:'100', plot_min:'0', plot_max:'200', basis:'Illustrative exponential scenario chosen for this interface demonstration. Not a measured or average solar profile.', origin:'illustrative_assumption'};
  }
  function beta(input) {
    if (!input || !['unknown','estimate','profile'].includes(input.mode)) throw Error('Choose a beta mode.');
    const b = copy(input);
    for (const k of Object.keys(blankBeta())) shortText(b[k], 'Beta ' + k);
    if (!['user_assumption','illustrative_assumption'].includes(b.origin)) throw Error('Unknown assumption origin.');
    if (b.mode === 'unknown') return {status:'UNKNOWN', provenance:'not_supplied', value:null, points:[], band:null};
    if (!b.basis.trim()) throw Error('Explain the basis of the assumed beta.');
    const v = number(b.beta0,'Reference beta'), h = number(b.height,'Selected height');
    if (v <= 0 || h < 0) throw Error('Beta must be positive; height above the reference surface must be non-negative.');
    const lo = number(b.low,'Lower beta',true), hi = number(b.high,'Upper beta',true);
    if ((lo === null) !== (hi === null)) throw Error('Supply both beta bounds or leave both blank.');
    if (lo !== null && !(0 < lo && lo <= v && v <= hi)) throw Error('Beta bounds must be positive and contain the reference beta.');
    let h0=h, H=null, hmin=h, hmax=h;
    if (b.mode === 'profile') {
      h0=number(b.reference_height,'Reference height'); H=number(b.scale_height,'Beta scale height');
      hmin=number(b.plot_min,'Minimum plot height'); hmax=number(b.plot_max,'Maximum plot height');
      if (h0 < 0 || H === 0 || hmin < 0 || hmax <= hmin || h < hmin || h > hmax) throw Error('Use non-negative heights, a non-zero scale height and a plot interval containing the selected height.');
    }
    function at(height, ref=v) {
      const logValue=Math.log(ref)+(H === null ? 0 : (height-h0)/H);
      const value=Math.exp(logValue);
      if (!Number.isFinite(value) || value <= 0) throw Error('This beta profile exceeds the numerical range. Change its height range or scale height.');
      return value;
    }
    const points=b.mode === 'profile' ? Array.from({length:81},(_,i)=>{
      const x=hmin+(hmax-hmin)*i/80;
      return {height_Mm:x, beta:at(x), low:lo === null ? null : at(x,lo), high:hi === null ? null : at(x,hi)};
    }) : [{height_Mm:h,beta:v,low:lo,high:hi}];
    return {status:'ASSUMED_SCENARIO', provenance:b.origin, model:b.mode === 'profile' ? 'beta(h)=beta0*exp((h-h0)/H_beta)' : 'single_height_estimate', value:at(h), height_Mm:h, reference_height_Mm:h0, scale_height_Mm:H, band:lo === null ? null : [at(h,lo),at(h,hi)], points, basis:b.basis, uncertainty:'User scenario bounds, when supplied; not a statistical confidence interval.', physical_family:null};
  }
  function validate(card, d) {
    const errors=[], rows=[];
    let b=null, edited=0;
    try {
      if (!d || d.event_id !== card.id || !Array.isArray(d.rows) || d.rows.length !== card.values.length) throw Error('This draft does not match the selected source.');
      shortText(d.nickname,'Name',80); shortText(d.region,'Region',400); shortText(d.notes,'Notes',4000);
      d.rows.forEach((r,i)=>{
        try {
          const original=card.values[i], base=rowFrom(original);
          if (!r || typeof r !== 'object') throw Error('Missing parameter row.');
          shortText(r.note,'Parameter note');
          const value=number(r.value,original.name,true), low=number(r.low,original.name+' lower bound',true), high=number(r.high,original.name+' upper bound',true), error=number(r.error,original.name+' error',true);
          if ((low===null)!==(high===null) || (low!==null && low>high)) throw Error(original.name+': supply an ordered pair of bounds.');
          if (value!==null && low!==null && (value<low || value>high)) throw Error(original.name+': the value must lie inside its bounds.');
          if (error!==null && error<0) throw Error(original.name+': an error magnitude cannot be negative.');
          if (error!==null && value===null) throw Error(original.name+': an error needs a central value.');
          const changed=Object.keys(base).some(k=>r[k]!==base[k]);
          if (changed) edited++;
          if (value===null && low===null && !r.note.trim()) throw Error(original.name+': explain the missing value in its note.');
          rows.push({name:original.name, unit:original.unit, role:original.role, value, range:low===null ? null : [low,high], error, note:r.note, provenance:changed ? 'user_override' : 'published_extraction'});
        } catch(e) { errors.push(e.message); }
      });
    } catch(e) { errors.push(e.message); }
    try { b=beta(d && d.beta); } catch(e) {errors.push(e.message);}
    if (b && b.status==='ASSUMED_SCENARIO' && d && !d.region.trim()) errors.push('Describe the region and height reference for the assumed beta.');
    if (card.id==='E08' && b && b.status!=='UNKNOWN') errors.push('This historical control is reserved for feature identity and instrument tests; no beta-based physical inference is enabled for it.');
    return {status:errors.length ? 'INPUT_NEEDS_CORRECTION' : 'CONSTRAINTS_REVIEWED', errors, rows, beta:b, edited, solver_ready:false, rmo_family_result:null};
  }
  function sentence(card,d,r) {
    if (r.errors.length) return 'The input needs a correction: '+r.errors[0];
    if (r.beta.status==='ASSUMED_SCENARIO') {
      return 'Assumed beta = '+Number(r.beta.value.toPrecision(4))+' at h = '+r.beta.height_Mm+' Mm; the MHD family remains undetermined.';
    }
    return (r.edited ? r.edited+' user-edited parameter row'+(r.edited===1?'':'s')+' retained' : card.values.length+' published parameter row'+(card.values.length===1?'':'s')+' loaded')+'; no new RMO classification has been calculated.';
  }
  function record(card,d) {
    const r=validate(card,d);
    if (r.errors.length) throw Error(r.errors.join(' '));
    return {schema_version:SCHEMA, kind:'literature_constraints_with_optional_assumptions', checkpoint:'RMO-67', event_id:card.id, draft:copy(d), source_snapshot:copy(card), review:r, result_in_one_sentence:sentence(card,d,r), contributor:{display_name:d.nickname.trim() || null, display_as:d.nickname.trim() || 'Anonymous'}, calculation:{status:'NOT_RUN', beta_arithmetic_only:r.beta.status==='ASSUMED_SCENARIO', rmo_result:null}, publication:{status:'NOT_PUBLISHED', submitted:false}};
  }
  function restore(text,cards) {
    if (typeof text!=='string' || text.length>250000) throw Error('Use a saved RMO-67 JSON record below 250 kB.');
    const obj=JSON.parse(text);
    if (obj.schema_version!==SCHEMA || obj.kind!=='literature_constraints_with_optional_assumptions') throw Error('This is not an RMO-67 literature draft. Synthetic requests and solver results use their own controls.');
    const card=cards.find(c=>c.id===obj.event_id);
    if (!card) throw Error('The source example is not present in this version.');
    if (JSON.stringify(obj.source_snapshot)!==JSON.stringify(card)) throw Error('The source snapshot differs from the preserved catalogue. It cannot be imported as this source.');
    const candidate=copy(obj.draft), r=validate(card,candidate);
    if (r.errors.length) throw Error(r.errors.join(' '));
    // Always derive review and outcome afresh; never trust imported result labels.
    return {card,draft:candidate,review:r};
  }
  function identity(record) {
    const d=copy(record.draft);
    for(const row of d.rows)for(const k of ['value','low','high','error'])row[k]=number(row[k],k,true);
    for(const k of ['beta0','low','high','height','reference_height','scale_height','plot_min','plot_max']) {
      // Inactive beta fields are retained but may be blank or an unfinished draft.
      const t=d.beta[k];d.beta[k]=t.trim()==='' ? null : numberPattern.test(t.trim()) && Number.isFinite(Number(t)) ? Number(t) : t;
    }
    function canonical(x) {
      if(Array.isArray(x))return x.map(canonical);
      if(x && typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])]));
      return x;
    }
    return JSON.stringify(canonical({schema:SCHEMA,event_id:record.event_id,source:record.source_snapshot,draft:d}));
  }
  const api={SCHEMA,draft,blankBeta,illustrativeBeta,beta,validate,sentence,record,restore,identity,number};
  if (typeof module==='object' && module.exports) module.exports=api;
  root.RMOLiterature=Object.freeze(api);
})(typeof globalThis==='object' ? globalThis : this);
