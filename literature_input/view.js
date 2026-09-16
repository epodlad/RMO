(function () {
  'use strict';
  const M=globalThis.RMOLiterature, cfg=JSON.parse(document.getElementById('r67-config').textContent);
  const $=id=>document.getElementById(id), el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  let card=null, draft=null, lastReviewed=null, betaSvg='';
  let importAttempt=0, workingRevision=0;
  const offered=new Set(), storageKey='rmo67-offered-draft-hashes-v1';let saving=false;
  const numeric=['beta0','low','high','height','reference_height','scale_height','plot_min','plot_max'];
  function notice(text) {$('r67-notice').textContent=text;}
  function saveNotice(text) {notice(text);$('r67-save-status').textContent=text;}
  function nextStep(c) {
    return c.id==='E05'?'Use the crossing exposure, quiet control and full geometry. Image-pattern speed is not the plasma normal velocity u_n.':c.next;
  }
  function showChanges(d) {
    const box=$('r67-changes'),original=M.draft(card),changed=[];
    const labels={value:'Value',low:'Lower bound',high:'Upper bound',error:'Error magnitude',note:'Note'};
    card.values.forEach((v,i)=>{
      for(const k of Object.keys(labels)) {
        const before=String(original.rows[i][k]??'').trim(),after=String(d.rows[i][k]??'').trim();
        if(before===after || (k!=='note' && before!=='' && after!=='' && Number(before)===Number(after)))continue;
        const unit=k==='note'?'':' '+v.unit;
        changed.push([v.name+' · '+labels[k],before?before+unit:'Unspecified',after?after+unit:'Unspecified']);
      }
    });
    box.replaceChildren();
    if(!changed.length){box.append(el('p',card.values.length?'Measurement fields match the published values.':'No numerical measurements have been extracted for this event.'));return;}
    const table=el('table'),head=el('tr');
    ['Changed field','Published value / note','Your working value / note'].forEach(label=>{const th=el('th',label);th.scope='col';head.append(th);});table.append(head);
    changed.forEach(values=>{const row=el('tr');values.forEach(value=>row.append(el('td',value)));table.append(row);});
    box.append(el('h4','Your changes to the published measurements'),table);
  }
  function download(content,name,type) {
    const blob=new Blob([content],{type}), url=URL.createObjectURL(blob), a=el('a');
    a.href=url; a.download=name; document.body.append(a); a.click(); a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function collect() {
    const d=JSON.parse(JSON.stringify(draft));
    d.rows=card.values.map((v,i)=>{const r={};for(const k of ['value','low','high','error','note'])r[k]=$('r67-row-'+i+'-'+k).value;return r;});
    d.region=$('r67-region').value; d.notes=$('r67-notes').value; d.nickname=$('r67-nickname').value;
    d.beta.mode=$('r67-beta-mode').value; for(const k of [...numeric,'basis'])d.beta[k]=$('r67-b-'+k).value;
    return d;
  }
  function invalidate() {
    workingRevision++;
    if (!draft) return;
    $('r67-changes').replaceChildren();$('r67-save-status').textContent='';
    lastReviewed=null; $('r67-save').disabled=true; $('r67-save-again').hidden=true; $('r67-beta-output').hidden=true; betaSvg='';
    $('r67-review-status').textContent='Edited — review the current constraints before saving.';
    $('r67-sentence').textContent='Inputs changed: review them again before interpreting the result.';$('r80-literature-detail').textContent='Your working inputs have changed; no current scenario review or new RMO solution is available.';
    $('r67-next').textContent='Click Review constraints to check the edited values and display any assumed beta.';
  }
  function betaVisibility() {
    const mode=$('r67-beta-mode').value;
    $('r67-beta-values').hidden=mode==='unknown';$('r67-profile-fields').hidden=mode!=='profile';
  }
  function fillBeta(b) {
    $('r67-beta-mode').value=b.mode;
    for(const k of [...numeric,'basis'])$('r67-b-'+k).value=b[k];
    betaVisibility();
  }
  function published(v) {
    if (v.range) return v.range.join('–')+' '+v.unit+' (published range)';
    return v.value+(v.error == null ? '' : ' ± '+v.error)+' '+v.unit;
  }
  function sourceLine(id,c,kind) {
    const node=$(id);node.replaceChildren();
    node.append(el('strong',c.id+' · '+(c.date||'Event date not extracted')+' · '+kind+'. '));
    node.append(el('span',c.source+' '));
    for(const [label,url] of [['Article / DOI',c.url],['Source used',c.read_url]]) {
      if(!url)continue;
      const a=el('a',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';
      node.append(a,el('span',' '));
    }
  }
  function renderRows() {
    const body=$('r67-rows');body.replaceChildren();
    if (!card.values.length) {const tr=el('tr'),td=el('td','No numerical state values have been extracted for this example. Missing values are not filled from a different event.');td.setAttribute('colspan','3');tr.append(td);body.append(tr);}
    card.values.forEach((v,i)=>{
      const tr=el('tr'),name=el('td'),source=el('td',published(v)),work=el('td');
      name.append(el('strong',v.name),el('small','Unit: '+v.unit),el('small','Meaning: '+v.role.replaceAll('_',' ')));
      if(v.cadence_s)source.append(el('small','Cadence: '+v.cadence_s+' s'));
      if(!v.range && v.error == null)source.append(el('small','Numerical uncertainty not extracted.'));
      for(const k of ['value','low','high','error','note']) {
        const label=el('label',({value:'Value',low:'Lower range bound',high:'Upper range bound',error:'Error magnitude, if known',note:'Reason / note on your change'})[k]);
        const input=el(k==='note'?'textarea':'input');input.id='r67-row-'+i+'-'+k;input.value=draft.rows[i][k];
        input.setAttribute('aria-label',v.name+' — '+label.textContent); if(k!=='note')input.setAttribute('inputmode','decimal');
        input.addEventListener('input',invalidate);label.append(input);work.append(label);
      }
      tr.append(name,source,work);body.append(tr);
    });
  }
  function reference() {
    $('r67-figure').replaceChildren();$('r67-figure-downloads').replaceChildren();
    const assets=cfg.figures[card.id];
    if (!assets) {$('r67-figure-note').textContent='No figure was extracted for this card. The parameter table and linked primary source remain available; no trajectory or solution curve is invented.';return;}
    $('r67-figure-note').textContent='Original plot of the published summary values. It stays unchanged when you edit the working inputs. It is not a new image measurement or a solver result.';
    const img=el('img');img.src=assets.svg.url;img.alt='Published summary values: '+card.title;$('r67-figure').append(img);
    for (const format of ['pdf','svg','png']) {
      const a=el('a',format==='pdf'?'Save reference · vector PDF':'Save reference · '+format.toUpperCase());
      a.href=assets[format].url;a.download=assets[format].filename;$('r67-figure-downloads').append(a);
    }
  }
  function loadLiterature(c,d=M.draft(c),restored=false) {
    workingRevision++;
    card=c;draft=d;lastReviewed=null;betaSvg='';
    $('r67-choice').value=c.id;$('r67-synthetic-workspace').hidden=false;$('r67-literature').hidden=false;
    $('r67-category').textContent=c.category+' · LITERATURE CONSTRAINTS · '+c.scope.replaceAll('_',' ');
    $('r67-event-title').textContent=c.id+' · '+(c.date || 'Event date not extracted')+' · '+c.title;
    $('r67-context').textContent=c.instruments+'. '+c.facts;
    $('r67-source').textContent=c.source;$('r67-source').href=c.read_url;
    sourceLine('r73-result-source',c,'RMO review of literature constraints');
    sourceLine('r73-figure-source',c,'Published values plotted by RMO');
    sourceLine('r73-beta-source',c,'Your assumed scenario for this event');
    $('r73-published-interpretation').textContent=c.author_interpretation;
    $('r67-errors-note').textContent=c.uncertainty_note;
    $('r67-author').textContent=c.author_interpretation;$('r67-literature-note').textContent=c.answer;
    $('r67-read-level').textContent='Source coverage: '+c.read_level;$('r67-source-json').textContent=JSON.stringify(c,null,2);
    $('r67-missing').replaceChildren(...c.missing.map(x=>el('li',x)));
    $('r67-region').value=d.region;$('r67-notes').value=d.notes;$('r67-nickname').value=d.nickname;
    $('r67-beta-fields').disabled=c.id==='E08';$('r67-beta-restriction').hidden=c.id!=='E08';
    fillBeta(d.beta);renderRows();reference();
    $('r67-changes').replaceChildren();$('r67-save-status').textContent='';
    $('r67-save').disabled=true;$('r67-save-again').hidden=true;$('r67-beta-output').hidden=true;
    const r=M.validate(c,d);$('r67-sentence').textContent=globalThis.RMOPlainResult.literature(r);$('r80-literature-detail').textContent=M.sentence(c,d,r);$('r67-next').textContent=nextStep(c);
    $('r67-review-status').textContent=restored?'Draft restored. Review before saving it again. Imported result labels were not reused.':'Published inputs loaded. Review constraints after any edits. No solar solve has run.';
    notice((restored?'Restored: ':'Loaded: ')+c.title+'. Source values are loaded below. Inspect or edit them, then review your constraints.');
  }
  function loadSelected() {
    workingRevision++;
    const id=$('r67-choice').value;
    if (id==='contact' || id==='brio') {
      card=null;draft=null;lastReviewed=null;$('r67-literature').hidden=true;$('r67-synthetic-workspace').hidden=false;
      if(id==='contact')globalThis.RMOInputBridge.load(JSON.parse($('local-contact-input').textContent));
      else $('load-preset').click();
      $('r63-result-choice').value=id;$('r63-result-choice').dispatchEvent(new Event('change'));
      notice((id==='contact'?'Contact':'Brio–Wu')+' inputs loaded. The diagrams below are saved references; a new calculation requires an explicit Run.');
      return;
    }
    const found=cfg.cards.find(c=>c.id===id);if(found){loadLiterature(found);jump('r67-event-title');}
  }
  function escapeXML(s) {return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');}
  function plot(b) {
    const pts=b.points,xlo=pts[0].height_Mm,xhi=pts.at(-1).height_Mm;
    const xs=xhi===xlo?[Math.max(0,xlo-10),xlo+10]:[xlo,xhi];
    const values=pts.flatMap(p=>[p.beta,...(p.low===null?[]:[p.low,p.high])]);
    let lmin=Math.min(...values.map(Math.log10)), lmax=Math.max(...values.map(Math.log10));
    if (lmax-lmin<.4) {const mid=(lmin+lmax)/2;lmin=mid-.2;lmax=mid+.2;}
    const X=x=>85+625*(x-xs[0])/(xs[1]-xs[0]),Y=v=>325-235*(Math.log10(v)-lmin)/(lmax-lmin);
    const tags=[];
    for(let i=0;i<5;i++) {
      const h=xs[0]+(xs[1]-xs[0])*i/4,lv=lmin+(lmax-lmin)*i/4,y=325-235*i/4;
      tags.push(`<text x="${X(h)}" y="349" text-anchor="middle">${Number(h.toPrecision(4))}</text>`);
      tags.push(`<path d="M85 ${y}H710" stroke="#e3e9e8"/><text x="74" y="${y+5}" text-anchor="end">${Number(Math.pow(10,lv).toPrecision(3))}</text>`);
    }
    if(b.band) {
      const poly=pts.map(p=>[X(p.height_Mm),Y(p.low)].join(',')).concat([...pts].reverse().map(p=>[X(p.height_Mm),Y(p.high)].join(','))).join(' ');
      if(pts.length>1)tags.push(`<polygon points="${poly}" fill="#d6e7e3"/>`);
      else tags.push(`<path d="M${X(b.height_Mm)} ${Y(b.band[0])}V${Y(b.band[1])}" stroke="#76998e" stroke-width="8"/>`);
    }
    if(pts.length>1)tags.push(`<polyline points="${pts.map(p=>[X(p.height_Mm),Y(p.beta)].join(',')).join(' ')}" fill="none" stroke="#196b67" stroke-width="3"/>`);
    tags.push(`<circle cx="${X(b.height_Mm)}" cy="${Y(b.value)}" r="6" fill="#ad531a"/>`);
    const description=escapeXML('ASSUMED SCENARIO. '+b.model+'. Selected beta '+b.value+' at '+b.height_Mm+' Mm. '+b.basis);
    return `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450" role="img" aria-label="Assumed beta versus height"><title>Assumed beta versus height</title><desc>${description}</desc><rect width="800" height="450" fill="white"/><g font-family="Arial,sans-serif" font-size="15" fill="#173639"><text x="85" y="32" font-size="23">Assumed beta · no MHD-family classification</text><text x="85" y="59">Selected: β = ${Number(b.value.toPrecision(4))} at h = ${b.height_Mm} Mm</text>${tags.join('')}<path d="M85 90V325H710" fill="none" stroke="#173639"/><text x="395" y="380" text-anchor="middle">Height above the stated reference surface (Mm)</text><text transform="translate(22,212) rotate(-90)" text-anchor="middle">Plasma β (log scale)</text><text x="85" y="412">Point: selected height. Curve and bounds, if shown, are assumptions.</text><text x="85" y="435">No observed upstream/downstream states are reconstructed.</text></g></svg>`;
  }
  function review() {
    if(!card)return;
    draft=collect();const r=M.validate(card,draft);showChanges(draft);$('r67-save-status').textContent='';
    $('r67-sentence').textContent=globalThis.RMOPlainResult.literature(r);$('r80-literature-detail').textContent=M.sentence(card,draft,r);
    $('r67-review-status').textContent=r.errors.length?'Needs correction: '+r.errors.join(' '):'Constraints reviewed. This is an input review, not a complete Riemann solution.';
    $('r67-next').textContent=r.errors.length?'Correct the listed input and review again.':r.beta.status==='ASSUMED_SCENARIO'?'Constrain co-spatial thermal pressure, total magnetic-field strength and height. Front geometry and plasma-velocity jumps are also needed to distinguish MHD families.':nextStep(card);
    lastReviewed=r.errors.length?null:JSON.stringify(draft);$('r67-save').disabled=r.errors.length>0;
    $('r67-beta-output').hidden=true;betaSvg='';
    if(!r.errors.length && r.beta.status==='ASSUMED_SCENARIO') {
      betaSvg=plot(r.beta);
      // Only our numeric plot and XML-escaped provenance are inserted as markup.
      $('r67-beta-graph').innerHTML=betaSvg;
      $('r67-beta-caption').textContent='Region: '+draft.region+'. Basis: '+draft.beta.basis+' Bounds, if supplied, are scenario limits. This curve is not attributed to the event paper.';
      $('r67-beta-output').hidden=false;
    }
  }
  $('r67-load').addEventListener('click',loadSelected);
  // Navigation changes only the viewed reference. It never loads a preset or runs Python.
  function jump(id) {
    const target=$(id); if(!target)return;
    for(let n=target;n;n=n.parentElement)if(n.tagName==='DETAILS')n.open=true;
    target.setAttribute('tabindex','-1');
    target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'auto'});
  }
  for(const id of ['contact','brio'])$('r69-'+id+'-view').addEventListener('click',()=>{
    $('r67-synthetic-workspace').hidden=false;
    $('r63-result-choice').value=id;$('r63-result-choice').dispatchEvent(new Event('change'));
    notice((id==='contact'?'Contact':'Brio–Wu')+' saved result opened. Your editable inputs are unchanged.');
    jump('r63-results');
  });
  $('r69-input-view').addEventListener('click',()=>{
    $('r67-synthetic-workspace').hidden=false;$('advanced-input').open=true;
    notice('Synthetic input fields opened. Literature constraints remain separate; no values were replaced.');
    jump('input-editor');
  });
  $('r67-choice').addEventListener('change',()=>notice('Selected: '+($('r67-choice').value)+'. Click 1 · Load example to fill its fields. Existing inputs stay unchanged until then.'));
  $('r67-check').addEventListener('click',()=>{review();jump('r67-review-output');});
  $('r67-review-top').addEventListener('click',()=>{review();jump('r67-review-output');});
  for(const id of ['r67-open-values','r67-edit-reviewed'])$(id).addEventListener('click',()=>jump('r67-values'));
  $('r67-beta-mode').addEventListener('change',()=>{betaVisibility();invalidate();});
  for(const k of [...numeric,'basis'])$('r67-b-'+k).addEventListener('input',()=>{if(draft)draft.beta.origin='user_assumption';invalidate();});
  for(const id of ['r67-region','r67-nickname','r67-notes'])$(id).addEventListener('input',invalidate);
  $('r67-beta-illustration').addEventListener('click',()=>{
    if(!draft || card.id==='E08')return;
    draft.beta=M.illustrativeBeta();fillBeta(draft.beta);
    if(!$('r67-region').value.trim())$('r67-region').value='Illustrative coronal region; height above the photosphere. Not a location measured in this event.';
    invalidate();notice('Illustrative beta(h) values loaded. Click Review constraints to display the assumed profile and its one-sentence outcome.');
  });
  async function saveDraft(again=false) {
    if(saving)return;saving=true;
    try {
      const d=collect();if(!lastReviewed || JSON.stringify(d)!==lastReviewed){invalidate();throw Error('Review the current inputs before saving.');}
      const selected=card, rec=M.record(selected,d), key=M.identity(rec);let hash=null,stored=[];
      if(globalThis.crypto && globalThis.crypto.subtle) {
        const bytes=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(key));
        hash=Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');
        try {const x=JSON.parse(globalThis.localStorage.getItem(storageKey)||'[]');if(Array.isArray(x))stored=x.filter(s=>typeof s==='string' && /^[a-f0-9]{64}$/.test(s)).slice(-255);}catch(e){/* file-mode storage may be unavailable */}
      }
      if(card!==selected || !lastReviewed || JSON.stringify(collect())!==lastReviewed)throw Error('The inputs changed while preparing the download. Review them again.');
      if(!again && (offered.has(key) || (hash && stored.includes(hash)))) {
        $('r67-save-again').hidden=false;saveNotice('This identical draft was already offered for download. No second file was created. Use Download again if you need another copy.');return;
      }
      download(JSON.stringify(rec,null,2),'RMO_'+selected.id+'_working_draft.json','application/json');offered.add(key);
      if(hash)try {globalThis.localStorage.setItem(storageKey,JSON.stringify([...new Set([...stored,hash])].slice(-256)));}catch(e){/* session detection remains active */}
      $('r67-save-again').hidden=false;
      saveNotice('JSON download offered. Your browser handles the file save; nothing was submitted to a public catalogue.');
    }catch(e){saveNotice(e.message);}finally{saving=false;}
  }
  $('r67-save').addEventListener('click',()=>saveDraft(false));
  $('r67-save-again').addEventListener('click',()=>saveDraft(true));
  $('r67-beta-svg').addEventListener('click',()=>{
    if(!betaSvg || !lastReviewed || JSON.stringify(collect())!==lastReviewed){invalidate();notice('Review the current inputs before saving the beta figure.');return;}
    download(betaSvg,'RMO_'+card.id+'_assumed_beta.svg','image/svg+xml');
  });
  async function importSelected() {
    const input=$('r67-import'),f=input.files && input.files[0],attempt=++importAttempt,revision=workingRevision;
    const status=$('r70-import-status'),retry=$('r70-import-retry');
    retry.disabled=!f;
    if(!f){status.textContent='No file selected. Choose a saved .json draft, for example RMO_E05_import_example.json. Your working inputs are unchanged.';return;}
    const name=typeof f.name==='string' && f.name ? f.name : 'Selected JSON file';
    status.textContent='Reading: '+name+' …';
    try {
      if(/\.(?:html?|zip|pdf)$/i.test(name))throw Error('Choose a saved .json draft, for example RMO_E05_import_example.json. This control does not import an HTML page, ZIP or PDF.');
      if(f.size>250000)throw Error('Use a JSON draft below 250 kB.');
      const text=await f.text();
      if(attempt!==importAttempt)return;
      if(revision!==workingRevision)throw Error('The working inputs changed while the file was being read. Click Import selected JSON again if you want to replace them with this file.');
      const result=M.restore(text.replace(/^\uFEFF/,''),cfg.cards);loadLiterature(result.card,result.draft,true);
      status.textContent='Imported: '+name+' · '+result.card.id+'. Input import completed. Review the working fields below before saving. No new calculation was run.';
      notice('Imported: '+name+'. '+result.card.title+' parameters are below.');jump('r67-event-title');
    }catch(e){
      if(attempt!==importAttempt)return;
      const reason=e.name==='SyntaxError'?'This file is not valid JSON. Choose a saved RMO .json draft, for example RMO_E05_import_example.json.':e.message;
      status.textContent='Not imported: '+name+'. '+reason+' Your working inputs are unchanged.';
      notice('Draft not imported: '+reason);
    }
    // Retain input.value: clearing it produces the misleading native "No file chosen".
  }
  $('r67-import').addEventListener('change',importSelected);
  $('r70-import-retry').addEventListener('click',importSelected);
})();
