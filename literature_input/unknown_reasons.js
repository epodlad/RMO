/* Suggested reasons are plain metadata. Unknown physical values stay null. */
(function(){
  'use strict';
  const C=globalThis.RMOPreflight,bridge=globalThis.RMOInputBridge;
  if(!C||!bridge)return;
  const reasons=['Not specified in this model','Not reported in the source','Not measured','Measurement not reliable','Geometry or field direction unknown','Deliberately withheld for this test'];
  const rows=[];let writing=false;
  const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  const meanings={rho:'Mass per unit volume in this initial region.',p:'Thermal gas pressure; magnetic pressure is separate.',u_n:'Plasma velocity normal to the boundary, in the common reference frame.',u_t1:'Plasma velocity along the first tangential axis.',u_t2:'Plasma velocity along the second tangential axis.',B_n:'Magnetic field component normal to the boundary, shared by both states.',B_t1:'Magnetic field component along the first tangential axis; keep its sign.',B_t2:'Magnetic field component along the second tangential axis; keep its sign.',gamma:'Ratio of specific heats chosen for the model. Brio–Wu uses 2.'};
  const editor=document.getElementById('input-editor');
  const guide=el('p','LEFT and RIGHT are the two neighbouring plasma regions at the initial boundary. Each has its own state values in the same coordinate system. These model fields use the stated synthetic normalization.');guide.id='r74-state-guide';editor.insertBefore(guide,editor.children[0]);
  for(const f of C.FIELD_LIST){
    const raw=document.getElementById('reason-'+f.name),value=document.getElementById('value-'+f.name);
    if(!raw||!value)continue;
    const parent=raw.parentNode,oldLabel=[...parent.children].find(n=>n.tagName.toLowerCase()==='label');
    const label=el('label','Why is this value unknown?'),choice=el('select');choice.id='reason-choice-'+f.name;label.htmlFor=choice.id;
    for(const [v,t] of [['','Choose a reason…'],...reasons.map(s=>[s,s]),['other','Other reason — write your own']]){const o=el('option',t);o.value=v;choice.append(o);}
    const hint=el('small','Choose a reason if the physical value is blank. This explains missing information; it does not supply a number.');hint.id='reason-help-'+f.name;
    parent.insertBefore(label,parent.children[0]);parent.insertBefore(choice,oldLabel||raw);parent.insertBefore(hint,oldLabel||raw);
    if(oldLabel)oldLabel.textContent='Your explanation';raw.placeholder='For example: field direction was not available for this region.';
    const meaning=el('small',meanings[f.key]);meaning.id='value-help-'+f.name;meaning.className='r74-field-hint';parent.parentNode.insertBefore(meaning,parent);
    value.setAttribute('aria-describedby',meaning.id+' '+hint.id+(f.key==='gamma'?' gamma-field-help':''));choice.setAttribute('aria-describedby',hint.id);
    function sync(){
      const s=raw.value;
      if(reasons.includes(s)){choice.value=s;raw.hidden=true;if(oldLabel)oldLabel.hidden=true;}
      else if(s || (choice.value==='other' && document.activeElement===raw)){choice.value='other';raw.hidden=false;if(oldLabel)oldLabel.hidden=false;}
      else {choice.value='';raw.hidden=true;if(oldLabel)oldLabel.hidden=true;}
    }
    choice.addEventListener('change',()=>{
      const custom=choice.value==='other';
      raw.value=custom?'':choice.value;raw.hidden=!custom;if(oldLabel)oldLabel.hidden=!custom;
      writing=true;try{raw.dispatchEvent(new Event('input',{bubbles:true}));}finally{writing=false;}
      if(custom)raw.focus();
    });
    rows.push(sync);sync();
  }
  bridge.subscribe(()=>{if(!writing)for(const sync of rows)sync();});
})();
