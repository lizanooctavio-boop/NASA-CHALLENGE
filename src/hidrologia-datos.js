/* Utilidades puras: códigos completos, fechas del proveedor y exportación segura. */
(function(raiz){
  'use strict';
  function codigo(p){return String(p.codigo_completo??p.PFAF_ID??p.code_pfafs??'');}
  function filasCSV(fs){
    const claves=[...new Set(fs.flatMap(f=>Object.keys(f.properties)))];
    const campo=x=>{let t=x==null?'':String(x);if(typeof x==='string'&&/^[=+@\-\t\r]/.test(t))t="'"+t;return '"'+t.replaceAll('"','""')+'"';};
    return '\ufeff'+[claves,...fs.map(f=>claves.map(k=>f.properties[k]))].map(f=>f.map(campo).join(',')).join('\r\n')+'\r\n';
  }
  function fecha(p){
    const iso=p.fechaultimatransmision??p['Ultima lectura'];
    if(iso)return iso;
    // fechaformato no incluye huso: se conserva y NO se interpreta como UTC.
    return p.fechaformato?String(p.fechaformato)+' '+String(p.horaformato??'')+' (timezone not supplied)':null;
  }
  function antiguedad(p,ahora=Date.now()){
    const t=p.fechaultimatransmision??p['Ultima lectura'];
    if(!t||!/(Z|[+-]\d\d:\d\d)$/.test(t))return 'Observation time unknown';
    const ms=Date.parse(t);if(!Number.isFinite(ms))return 'Observation time unknown';
    if(ms>ahora+300000)return 'Future timestamp: check source';
    return ahora-ms>48*3600000?'Older than 48 hours':'Within the last 48 hours';
  }
  function buscar(fs,q){q=q.trim().toLocaleLowerCase();return q?fs.filter(f=>[codigo(f.properties),f.properties.cuencas,f.properties.HYBAS_ID].some(v=>String(v??'').toLocaleLowerCase().includes(q))):[];}
  const api={codigo,filasCSV,fecha,antiguedad,buscar};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else raiz.HidrologiaDatos=api;
})(typeof window==='undefined'?globalThis:window);
