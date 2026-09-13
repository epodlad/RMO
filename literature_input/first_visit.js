(function () {
  'use strict';
  const $=id=>document.getElementById(id);
  function reveal(target) {
    for(let n=target;n;n=n.parentElement) {
      if(n.tagName && n.tagName.toLowerCase()==='details')n.open=true;
    }
  }
  // Capture runs before existing control handlers, so their focus/scroll
  // actions can reach the full workspace. No input values are changed here.
  document.addEventListener('click',function(e){
    const control=e.target.closest ? e.target.closest('a,button') : null;
    if(!control)return;
    const route=control.getAttribute('data-r73-route');
    if(route) {
      e.preventDefault();
      const button=$(route==='input'?'r69-input-view':'r69-'+route+'-view');
      if(button)button.click();
      return;
    }
    const targets={'r69-contact-view':'r63-results','r69-brio-view':'r63-results',
                   'r69-input-view':'input-editor','r63-open-brio':'r63-results'};
    if(targets[control.id])reveal($(targets[control.id]));
    if(control.id==='r67-load') {
      const chosen=$('r67-choice').value;
      reveal($(chosen==='contact'||chosen==='brio'?'r63-results':'r67-literature'));
    }
    const href=control.getAttribute('href');
    if(href && href.startsWith('#'))reveal($(href.slice(1)));
  },true);
  if(location.hash)reveal($(location.hash.slice(1)));
})();
