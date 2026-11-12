(function(){
'use strict';
function utc(iso){
  if(typeof iso!=='string')return NaN;
  return Date.parse(/(?:Z|[+-]\d\d:\d\d)$/.test(iso)?iso:iso+'Z');
}
function bilineal(q,a,b){
  if(q.length!==4||q.some(x=>!Number.isFinite(x)))return null;
  return q[0]*(1-a)*(1-b)+q[1]*(1-a)*b+q[2]*a*(1-b)+q[3]*a*b;
}
window.SICC_soporte=Object.freeze({utc,bilineal});
})();
