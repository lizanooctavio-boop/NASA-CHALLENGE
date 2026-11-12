// Gráficas (Chart.js 4.4.1 desde CDN con versión fijada). Si la biblioteca no carga, se avisa y el resto sigue.
(function(){
const $=id=>document.getElementById(id);
const avisar=t=>document.querySelectorAll('.graf-aviso').forEach(n=>n.textContent=t);
const MANAGUA=[12.13,-86.25];
let punto=MANAGUA;
const botonesCSV=[...document.querySelectorAll('[data-csv-meteo]')];
const informe=b=>b.closest('#exportar')!==null;
function actualizarExportaciones(){
  const campo=window.SICC_campo?.datos();
  for(const b of botonesCSV){
    const coordenadas=informe(b)?MANAGUA:punto;
    const disponible=campo&&(b.dataset.csvMeteo==='campo'||window.SICC_campo.contiene(...coordenadas));
    b.disabled=!disponible||b.getAttribute('aria-busy')==='true';
  }
  const estado=campo?(campo.respaldo?'CSV de la malla regional de respaldo.':''):'CSV meteorológicos no disponibles sin malla regional.';
  $('csv-informes-estado').textContent=estado;
  $('csv-meteo-estado').textContent=campo&&!window.SICC_campo.contiene(...punto)
    ? (estado+' El punto elegido está fuera de la malla regional.').trim():estado;
}
for(const b of botonesCSV)b.addEventListener('click',async()=>{
  const tipo=b.dataset.csvMeteo,coordenadas=informe(b)?MANAGUA:punto;
  const parametros=tipo==='campo'
    ? (informe(b)?{}:{hora_utc:window.SICC_campo.estado().horaUTC})
    : {lat:coordenadas[0].toFixed(3),lon:coordenadas[1].toFixed(3)};
  const estado=$(informe(b)?'csv-informes-estado':'csv-meteo-estado');
  b.setAttribute('aria-busy','true');
  b.disabled=true;
  estado.textContent='Preparando CSV…';
  let mensaje;
  try{
    const r=await window.FuentesMeteo.fetch('/api/exportar/'+tipo+'.csv?'+new URLSearchParams(parametros));
    if(!r.ok){
      const detalle=await r.json().catch(()=>null);
      throw Error(detalle?.error||'No se pudo obtener el archivo.');
    }
    if(!r.headers.get('Content-Type')?.startsWith('text/csv'))throw Error('El servidor no devolvió un CSV.');
    const url=URL.createObjectURL(await r.blob()),a=document.createElement('a');
    a.href=url;
    a.download=r.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1]||'sicc952_'+tipo+'.csv';
    a.click();
    setTimeout(()=>URL.revokeObjectURL(url),30000);
    mensaje='CSV listo para descargar.';
  }catch(e){
    mensaje='CSV no disponible: '+(e.message||e);
  }finally{
    b.removeAttribute('aria-busy');
    actualizarExportaciones();
    estado.textContent=mensaje;
  }
});
document.addEventListener('sicc:punto',e=>{punto=e.detail;actualizarExportaciones()});
document.addEventListener('sicc:campo',actualizarExportaciones);
actualizarExportaciones();
if(!window.Chart){avisar('No se pudo cargar Chart.js desde el CDN; las gráficas no están disponibles. Los datos siguen exportables en CSV.');window.SICC_graf={estado:()=>({chart:false})};return}
Chart.defaults.color='#a9b8c9';Chart.defaults.borderColor='rgba(255,255,255,.09)';Chart.defaults.font.family='system-ui,Cantarell,Ubuntu,"Segoe UI",sans-serif';Chart.defaults.font.size=11;
Chart.defaults.plugins.legend.labels.boxWidth=12;Chart.defaults.maintainAspectRatio=false;Chart.defaults.animation.duration=300;
const C={cian:'#6fd8ff',ambar:'#f6c76b',rojo:'#ff7b6b',verde:'#6fe0a0',violeta:'#b493ff',gris:'#9db0c6',azul:'#4f8fe8'};
const SSP={ssp126:C.verde,ssp245:C.cian,ssp370:C.ambar,ssp585:C.rojo};
const graficas={};
function crear(id,config){const c=$(id);if(!c)return null;graficas[id]?.destroy();graficas[id]=new Chart(c,config);return graficas[id]}
const eje=(titulo,extra={})=>({title:{display:true,text:titulo},...extra});
let S=null;

// ---------------------------------------------------------------- series observadas de la cuenca
function observadas(){
  const anual={};S.cuenca_mensual.forEach(f=>{(anual[f.anio]??={pr:0,t:[],n:0});if(f.pr_mm!==null){anual[f.anio].pr+=f.pr_mm;anual[f.anio].n++}if(f.tmed_c!==null)anual[f.anio].t.push(f.tmed_c)});
  const anios=Object.keys(anual).map(Number).filter(a=>anual[a].n===12);
  crear('graf-anual',{data:{labels:anios,datasets:[
    {type:'bar',label:'Lluvia anual (mm) · CHIRPS v2',data:anios.map(a=>anual[a].pr),backgroundColor:'rgba(79,143,232,.55)',yAxisID:'y'},
    {type:'line',label:'Temperatura media (°C)',data:anios.map(a=>anual[a].t.reduce((x,y)=>x+y,0)/anual[a].t.length),borderColor:C.ambar,pointRadius:0,tension:.25,yAxisID:'y1'}]},
    options:{interaction:{mode:'index',intersect:false},scales:{y:eje('mm/año'),y1:eje('°C',{position:'right',grid:{drawOnChartArea:false}})},
      plugins:{subtitle:{display:true,text:'Solo años completos. Caja geográfica de la cuenca; satélite y reanálisis, no estaciones.'}}}});
  // Climatología mensual 1991–2020 frente al año en curso
  const MESES=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],ultimo=Math.max(...S.cuenca_mensual.map(f=>f.anio));
  const clima=MESES.map((_,m)=>{const f=S.cuenca_mensual.filter(x=>x.mes===m+1&&x.anio>=1991&&x.anio<=2020);return{pr:f.reduce((a,x)=>a+x.pr_mm,0)/f.length,t:f.reduce((a,x)=>a+x.tmed_c,0)/f.length}});
  const actual=MESES.map((_,m)=>S.cuenca_mensual.find(x=>x.anio===ultimo&&x.mes===m+1)||{});
  crear('graf-mensual',{data:{labels:MESES,datasets:[
    {type:'bar',label:'Lluvia normal 1991–2020 (mm)',data:clima.map(x=>x.pr),backgroundColor:'rgba(157,176,198,.35)',yAxisID:'y'},
    {type:'bar',label:`Lluvia ${ultimo} (mm)`,data:actual.map(x=>x.pr_mm??null),backgroundColor:'rgba(111,216,255,.75)',yAxisID:'y'},
    {type:'line',label:'Temp. normal (°C)',data:clima.map(x=>x.t),borderColor:C.gris,borderDash:[4,4],pointRadius:0,yAxisID:'y1'},
    {type:'line',label:`Temp. ${ultimo} (°C)`,data:actual.map(x=>x.tmed_c??null),borderColor:C.ambar,pointRadius:2,yAxisID:'y1'}]},
    options:{interaction:{mode:'index',intersect:false},scales:{y:eje('mm/mes'),y1:eje('°C',{position:'right',grid:{drawOnChartArea:false}})}}});
}

// ---------------------------------------------------------------- escenarios v0.1
function escenarios(){
  const ventana=$('ventana-cmip').value, ssp=$('ssp').value;
  const filas=S.proyecciones.filter(f=>f.ventana===ventana);
  const anios=[...new Set(filas.map(f=>f.anio))].sort((a,b)=>a-b);
  for(const [id,clave,unidad] of [['graf-dT','dT','ΔT estacional (°C)'],['graf-dP','dP','ΔP estacional (%)']]){
    crear(id,{type:'line',data:{labels:anios,datasets:Object.keys(SSP).map(s=>({
      label:s.toUpperCase(),data:anios.map(a=>filas.find(f=>f.escenario===s&&f.anio===a)?.[clave]??null),
      borderColor:SSP[s],borderWidth:s===ssp?3:1.2,pointRadius:0,tension:.2
    }))},options:{scales:{y:eje(unidad+' vs. 1981–1995')}}});
  }
}

// ---------------------------------------------------------------- ENOS
document.addEventListener('sicc:enos',e=>{const d=e.detail;
  const f=d.oni_local.filter(x=>x.oni!==null);
  crear('graf-oni',{type:'bar',data:{labels:f.map(x=>`${x.anio}-${String(x.mes).padStart(2,'0')}`),datasets:[{label:'ONI (°C)',data:f.map(x=>x.oni),backgroundColor:f.map(x=>x.oni>=.5?'rgba(255,123,107,.85)':x.oni<=-.5?'rgba(79,143,232,.85)':'rgba(157,176,198,.45)'),borderWidth:0,barPercentage:1,categoryPercentage:1}]},
    options:{plugins:{legend:{display:false},subtitle:{display:true,text:'Rojo: El Niño (≥ +0,5) · Azul: La Niña (≤ −0,5) · NOAA CPC, ERSSTv5'}},scales:{x:{ticks:{maxTicksLimit:16,autoSkip:true}},y:eje('°C')}}});
  const s=d.nino34_semanal?.semanas||[];
  crear('graf-nino34',{type:'line',data:{labels:s.map(x=>x.semana),datasets:[['nino12','Niño 1+2',C.rojo],['nino3','Niño 3',C.ambar],['nino34','Niño 3.4',C.cian],['nino4','Niño 4',C.violeta]].map(([k,n,c])=>({label:n,data:s.map(x=>x[k]),borderColor:c,pointRadius:0,borderWidth:k==='nino34'?2.6:1.4}))},
    options:{interaction:{mode:'index',intersect:false},scales:{y:eje('Anomalía semanal (°C)')}}});
});
document.addEventListener('sicc:tormentas',e=>{const h=e.detail.historicas||[];const dec={};h.forEach(t=>{const d=Math.floor(t.anio/10)*10;dec[d]=(dec[d]||0)+1});
  crear('graf-tormentas',{type:'scatter',data:{datasets:[{label:'Sistemas cercanos (HURDAT2)',data:h.map(t=>({x:t.anio,y:t.viento_max_kt,n:t.nombre,km:t.km_min})),backgroundColor:h.map(t=>t.viento_max_kt>=64?'rgba(255,123,107,.9)':'rgba(111,216,255,.8)'),pointRadius:h.map(t=>Math.max(3,9-t.km_min/50))}]},
    options:{plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.raw.n} ${c.raw.x}: ${c.raw.y} kt, a ${Math.round(c.raw.km)} km`}},subtitle:{display:true,text:'Viento máximo del sistema; rojo = huracán. Punto mayor = pasó más cerca de la cuenca.'}},scales:{x:eje('Año'),y:eje('Viento máximo (kt)')}}});
});

// ---------------------------------------------------------------- meteograma del punto elegido
function meteograma(){
  const s=window.SICC_campo?.serie(...punto),t=$('meteograma-titulo');
  $('graf-meteograma').parentElement.hidden=!s;
  if(!s){
    graficas['graf-meteograma']?.destroy();
    delete graficas['graf-meteograma'];
    t.textContent='Pronóstico 48 h en un punto';
    $('meteograma-estado').textContent=window.SICC_campo?.datos()
      ?'Elige un punto dentro de la malla de Nicaragua.'
      :'Pronóstico puntual regional no disponible.';
    return;
  }
  $('meteograma-estado').textContent=window.SICC_campo.datos().respaldo?'Malla regional de respaldo.':'';
  if(t)t.textContent=`Pronóstico horario en ${punto[0].toFixed(2)}°, ${punto[1].toFixed(2)}° · ECMWF IFS (malla interpolada, estimación de modelo)`;
  const etiquetas=s.horas.map(h=>new Date(h+':00Z').toLocaleString('es-NI',{timeZone:'America/Managua',weekday:'short',hour:'2-digit'}));
  const hora=window.SICC_campo.hora();
  crear('graf-meteograma',{data:{labels:etiquetas,datasets:[
    {type:'line',label:'Temperatura (°C)',data:s.temperatura_c,borderColor:C.ambar,pointRadius:s.horas.map((_,i)=>i===hora?5:0),pointBackgroundColor:'#fff',tension:.3,yAxisID:'y'},
    {type:'bar',label:'Lluvia (mm/h)',data:s.precipitacion_mm,backgroundColor:'rgba(79,143,232,.75)',yAxisID:'y1'},
    {type:'line',label:'Ráfagas (m/s)',data:s.rafagas_ms,borderColor:C.violeta,borderDash:[3,3],pointRadius:0,yAxisID:'y2'}]},
    options:{interaction:{mode:'index',intersect:false},scales:{x:{ticks:{maxTicksLimit:10}},y:eje('°C'),y1:eje('mm/h',{position:'right',grid:{drawOnChartArea:false},min:0}),y2:{display:false,min:0}}}});
}
document.addEventListener('sicc:punto',meteograma);
document.addEventListener('sicc:campo',meteograma);
document.addEventListener('sicc:hora',meteograma);
meteograma();

window.FuentesMeteo.fetch('/api/series').then(r=>r.json().then(d=>{if(!r.ok)throw Error(d.error);S=d;observadas(); const selector=$('ventana-cmip'); [...new Set(S.proyecciones.map(f=>f.ventana))].forEach(v=>selector.add(new Option(v,v))); escenarios();avisar('')})).catch(e=>avisar('Series no disponibles: '+(e.message||e)));
['ssp','ventana-cmip'].forEach(id=>$(id)?.addEventListener('change',()=>S&&escenarios()));
// Chart.js no dibuja bien en lienzos ocultos: se redimensiona al cambiar de pestaña.
document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',()=>setTimeout(()=>Object.values(graficas).forEach(g=>g.resize()),30)));
window.SICC_graf={estado:()=>({chart:true,graficas:Object.keys(graficas)})};
})();
