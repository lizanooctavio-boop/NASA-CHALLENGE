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
// A cached forecast can still be explored after expiry, but it must not be labelled current.
function vigente(horas,ahora=Date.now()){
  const tiempos=(horas||[]).map(utc).filter(Number.isFinite).sort((a,b)=>a-b);
  if(!tiempos.length||!Number.isFinite(ahora))return false;
  const ultimo=tiempos.at(-1),paso=tiempos.length>1?ultimo-tiempos.at(-2):3600000;
  return ahora>=tiempos[0]&&ahora<ultimo+Math.max(1,paso);
}
window.SICC_soporte=Object.freeze({utc,bilineal,vigente});
})();
