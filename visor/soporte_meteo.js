(function(){
'use strict';
function utc(iso){
  if(typeof iso!=='string')return NaN;
  return Date.parse(/(?:Z|[+-]\d\d:\d\d)$/.test(iso)?iso:iso+'Z');
}
function vigencia(meta,ahora=Date.now()){
  if(!meta)return 'Malla mundial no disponible.';
  const corrida=utc(meta.corrida_utc),fin=utc(meta.horas_utc?.at(-1));
  if(!Number.isFinite(corrida)||!Number.isFinite(fin))return 'Vigencia mundial no verificable.';
  const edad=((ahora-corrida)/3600000).toFixed(1);
  if(ahora>fin)return `Archivo histórico: horizonte finalizado ${meta.horas_utc.at(-1)} UTC · edad de corrida ${edad} h.`;
  if(ahora<corrida)return 'Corrida futura: no representa la hora actual.';
  return `Horizonte mundial cubre la hora actual · edad de corrida ${edad} h. No implica validación local.`;
}
function soporte(variable,respuesta){
  if(!respuesta)return 'Soporte temporal pendiente de cargar.';
  const s=respuesta.soporte;
  if(!s?.contrato_grib_verificado)return 'Contrato GRIB e intervalo sin verificar para este archivo.';
  if(!s.dato_disponible)return 'Sin dato para esta variable en el paso inicial; no equivale a cero.';
  const intervalo=s.intervalo_h===0?`Valor instantáneo ${s.fin_intervalo_utc} UTC.`:
    s.intervalo_h>0?`${s.tipo_temporal==='maximo_del_intervalo'?'Máximo':'Media horaria'} de ${s.intervalo_h} h: ${s.inicio_intervalo_utc} a ${s.fin_intervalo_utc} UTC.`:'Intervalo no documentado.';
  return intervalo+(variable==='precipitacion_mm'?` ${s.politica_lluvia==='enmascarar_cuantizacion'?'Lluvia indeterminada por cuantización: sin color, no cero. ':''}Cero decodificado no demuestra ausencia física de lluvia.`:'');
}
function etiquetaHora(iso,ahora=Date.now()){
  const t=utc(iso);if(!Number.isFinite(t))return 'Hora no verificable';
  if(t<=ahora&&ahora-t<3600000)return 'hora del modelo en curso, no observación';
  return t>ahora?'hora futura de modelo':'hora pasada de modelo, no observación';
}
function bilineal(q,a,b){
  if(q.length!==4||q.some(x=>!Number.isFinite(x)))return null;
  return q[0]*(1-a)*(1-b)+q[1]*(1-a)*b+q[2]*a*(1-b)+q[3]*a*b;
}
const formato=(x,d=1)=>Number.isFinite(x)?x.toFixed(d):'sin dato';
window.SICC_soporte=Object.freeze({utc,vigencia,soporte,etiquetaHora,bilineal,formato});
})();
