/* Presentation only. Never assign a physical class or change an input/result. */
(function(root){'use strict';
 const exact={
  fast_shock:'Fast shock: the supplied model states pass the physical checks.',
  slow_shock:'Slow shock: the supplied model states pass the physical checks.',
  contact:'Contact: a density boundary travels with the plasma.',
  rotational_discontinuity:'Rotational discontinuity: the magnetic field changes direction across the boundary.'
 };
 function local(out){
  if(!out||typeof out!=='object')return 'No checked result is available yet.';
  if(['EXACT_LOCAL_CLASS','SUPPORTED_LOCAL_CLASS'].includes(out.status)&&Object.hasOwn(exact,out.family))return exact[out.family];
  if(out.status==='CONDITIONAL_ROBUST_CLASS'&&['fast_shock','slow_shock'].includes(out.family)){
   const name=out.family==='fast_shock'?'Fast shock':'Slow shock';
   return ['RMO79-fixed-perpendicular-bounds','RMO81-conservation-coupled-perpendicular'].includes(out.integration)
    ? name+': the type stays supported with these errors if the geometry is exactly perpendicular.'
    : name+': the type stays supported within these error ranges and the stated model assumptions.';
  }
  if(out.status==='NOT_CERTIFIED')return 'With these errors, the type is not confirmed; this does not establish a different type.';
  if(['PERPENDICULAR_UNCERTAINTY_NOT_SUPPORTED','UNCERTAINTY_NOT_IMPLEMENTED'].includes(out.status))return 'These error ranges have not been assessed by the available test.';
  if(['MISSING_MEASUREMENTS','INSUFFICIENT_DATA'].includes(out.status))return 'More measurements are needed before this test can identify the front type.';
  if(out.status==='SEARCH_INCOMPLETE')return 'No checked state was found; the front type remains unresolved.';
  if(out.status==='NOMINAL_NOT_CHECKED')return 'The central values do not yet give a checked result; the type remains unresolved.';
  if(out.status==='INDEPENDENT_CHECK_FAILED')return 'The independent checks disagree; no verified type is assigned.';
  if(['INVALID_INPUT','INVALID_BOUNDS','OUTSIDE_NUMERIC_DOMAIN'].includes(out.status))return 'Correct the input values; no physical type has been assigned.';
  if(['INCONSISTENT_BN','INCONSISTENT_SINGLE_DISCONTINUITY'].includes(out.status))return 'These values fail the physical checks for one ideal-MHD boundary.';
  if(out.status==='NO_RESOLVED_JUMP')return 'No distinct boundary is resolved in these model states.';
  return 'This test has not established a physical type for the supplied inputs.';
 }
 function literature(review){
  if(review?.errors?.length)return 'Correct the entered values; no new wave type has been calculated.';
  if(review?.beta?.status==='ASSUMED_SCENARIO')return 'Your assumed beta is displayed; it does not determine the wave type.';
  return 'The event measurements are available; RMO has not yet determined its wave type.';
 }
 const api={local,literature,exact};root.RMOPlainResult=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
