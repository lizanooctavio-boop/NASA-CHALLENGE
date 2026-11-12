// Fenómenos y capas en vivo: satélite GOES-East, radar, lluvia satelital IMERG, anomalía de temperatura del mar
// (El Niño), aerosoles, ciclones tropicales del NHC y estado de ENOS. Si una fuente falla, no se dibuja nada.
(function(){
const $=id=>document.getElementById(id);
const nodo=(t,txt,c)=>{const n=document.createElement(t);if(txt!==undefined)n.textContent=txt;if(c)n.className=c;return n};
const dec=(v,n=1)=>v===null||v===undefined?'—':Number(v).toLocaleString('es-NI',{minimumFractionDigits:n,maximumFractionDigits:n});
const json=r=>typeof leerJSON==='function'?leerJSON(r):r.json();
if(typeof mapa==='undefined'||!mapa)return;

// ---------------------------------------------------------------- capas raster
if(!mapa.getPane('referencia')){mapa.createPane('referencia');mapa.getPane('referencia').style.zIndex=450;mapa.getPane('referencia').style.pointerEvents='none'}
const TES=(window.SICC_CONFIG||{}).teselas||{etiquetas:'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',etiquetas_atribucion:'Fronteras y nombres © Esri'};
const referencia=!TES.etiquetas?null:L.tileLayer(TES.etiquetas,{pane:'referencia',maxZoom:18,noWrap:true,subdomains:'abcd',bounds:[[-85,-180],[85,180]],opacity:.9,attribution:TES.etiquetas_atribucion});
const CAPAS={
  sat:{capa:'GOES-East_ABI_GeoColor',limites:[[-81.3,-156.2],[81.3,6.2]],z:5,op:1,nombre:'Satélite GOES-East',nota:'NASA publica con ~40–70 min de retraso',zoom:7},
  imerg:{capa:'IMERG_Precipitation_Rate_30min',z:6,op:.85,nombre:'Lluvia satelital IMERG',nota:'estimación satelital NASA GPM con ~5–7 h de retraso',zoom:6},
  sst:{capa:'GHRSST_L4_MUR_Sea_Surface_Temperature_Anomalies',z:3,op:.75,nombre:'Anomalía de temperatura del mar',nota:'MUR GHRSST diario; rojo = mar más cálido de lo normal (El Niño en el Pacífico)',zoom:7},
  aod:{capa:'MODIS_Combined_Value_Added_AOD',z:4,op:.7,nombre:'Aerosoles (polvo y humo)',nota:'espesor óptico MODIS diario; huecos = nubes o sin pase',zoom:6}
};
const estado={},vivo={},turno={};
function texto(){const p=[];for(const k in CAPAS)if($('chk-'+k)?.checked)p.push(`${CAPAS[k].nombre}: ${estado[k]||'…'} (${CAPAS[k].nota})`);if($('chk-radar')?.checked)p.push(`Radar RainViewer: ${estado.radar||'…'} · cobertura parcial en Nicaragua: sin color no significa sin lluvia`);$('vivo-estado').textContent=p.length?p.join(' · '):'Sin capas satelitales activas.'}
async function capaGibs(k){
  const c=CAPAS[k],chk=$('chk-'+k),mio=turno[k]=(turno[k]||0)+1;
  if(vivo[k]){mapa.removeLayer(vivo[k]);vivo[k]=null}
  if(k==='sat')referencia?.remove();
  if(!chk.checked){estado[k]=null;texto();return}
  try{
    const r=await window.FuentesMeteo.fetch('/api/gibs_hora?capa='+encodeURIComponent(c.capa));const d=await json(r);if(!r.ok)throw Error(d.error||'sin hora publicada');
    if(!chk.checked||turno[k]!==mio)return;
    vivo[k]=L.tileLayer(`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${d.capa}/default/${d.hora_utc}/${d.matriz}/{z}/{y}/{x}.${d.formato}`,{maxNativeZoom:c.zoom,maxZoom:18,noWrap:true,bounds:c.limites||[[-85,-180],[85,180]],opacity:c.op,zIndex:c.z,attribution:'NASA GIBS'}).addTo(mapa);
    if(k==='sat')referencia?.addTo(mapa);
    estado[k]=d.hora_utc.replace('T',' ').replace(':00Z',' UTC');
  }catch(e){
    if(turno[k]!==mio)return; // una respuesta antigua que falla no sustituye el estado de la solicitud vigente
    estado[k]='no disponible ('+(e.message||e)+')';
  }
  texto();
}
async function radar(){
  const mio=turno.radar=(turno.radar||0)+1; // solo la última solicitud añade la capa: evita radares duplicados
  if(vivo.radar){mapa.removeLayer(vivo.radar);vivo.radar=null}
  if(!$('chk-radar').checked){estado.radar=null;texto();return}
  try{const r=await fetch('https://api.rainviewer.com/public/weather-maps.json');const d=await json(r);if(!r.ok)throw Error('RainViewer respondió '+r.status);const f=d.radar.past.at(-1);if(!$('chk-radar').checked||turno.radar!==mio)return;
    vivo.radar=L.tileLayer(`${d.host}${f.path}/256/{z}/{x}/{y}/2/1_1.png`,{opacity:.8,maxNativeZoom:7,maxZoom:18,noWrap:true,bounds:[[-85,-180],[85,180]],zIndex:6,attribution:'Radar © RainViewer'}).addTo(mapa);
    estado.radar=new Date(f.time*1000).toISOString().slice(0,16).replace('T',' ')+' UTC'}catch(e){if(turno.radar!==mio)return;estado.radar='no disponible ('+(e.message||e)+')'}
  texto();
}
for(const k in CAPAS)$('chk-'+k).onchange=()=>capaGibs(k);
$('chk-radar').onchange=radar;
setInterval(()=>{if(document.hidden)return;if($('chk-sat').checked)capaGibs('sat');if($('chk-radar').checked)radar();if($('chk-imerg').checked)capaGibs('imerg')},10*60000);
capaGibs('sat');
document.querySelectorAll('[data-activar]').forEach(b=>b.onclick=()=>{const c=$(b.dataset.activar);if(!c.checked){c.checked=true;c.dispatchEvent(new Event('change'))}if(b.dataset.vista){const [la,lo,z]=b.dataset.vista.split(',').map(Number);mapa.setView([la,lo],z)}if(typeof soloMapa==='function')soloMapa(true)});

// ---------------------------------------------------------------- ciclones tropicales
const capaTormentas=L.layerGroup();
const COLOR_CAT={'Depresión tropical':'#5ec8ff','Tormenta tropical':'#5fe08a','Huracán cat. 1':'#ffe066','Huracán cat. 2':'#ffb347','Huracán cat. 3':'#ff7b4a','Huracán cat. 4':'#ff4d6d','Huracán cat. 5':'#d65cff'};
function geo(fc,estilo,popup){if(!fc||!fc.features||!fc.features.length)return null;const g=L.geoJSON(fc,{style:estilo,pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:4,color:'#fff',weight:1,fillColor:estilo().color,fillOpacity:1})});if(popup)g.bindPopup(popup);return g}
let tormentasDatos=null;
async function cargarTormentas(){
  const lista=$('lista-tormentas'),est=$('tormentas-estado');
  try{
    const r=await window.FuentesMeteo.fetch('/api/tormentas');const d=await json(r);if(!r.ok)throw Error(d.error||'sin datos');tormentasDatos=d;
    capaTormentas.clearLayers();lista.replaceChildren();
    d.activas.forEach(t=>{
      const c=COLOR_CAT[t.categoria]||'#fff',pop=`${t.nombre} · ${t.categoria} · ${dec(t.viento_kt,0)} kt · ${dec(t.presion_hpa,0)} hPa · aviso NHC`;
      [geo(t.cono,()=>({color:c,weight:1,fillOpacity:.12,dashArray:'4 4'}),'Cono de incertidumbre del NHC: zona probable del centro, no del área afectada.'),
       geo(t.trayectoria_pasada,()=>({color:'#cfd8e3',weight:2,opacity:.8}),`${t.nombre}: trayectoria pasada`),
       geo(t.trayectoria_pronostico,()=>({color:c,weight:2.5}),`${t.nombre}: trayectoria pronosticada por el NHC`),
       geo(t.puntos_pronostico,()=>({color:c}),`${t.nombre}: puntos de pronóstico NHC`)].forEach(g=>g&&capaTormentas.addLayer(g));
      if(t.lat!=null)capaTormentas.addLayer(L.marker([t.lat,t.lon],{icon:L.divIcon({className:'',html:`<div class="ciclon" style="--c:${c}">🌀</div>`,iconSize:[30,30],iconAnchor:[15,15]})}).bindPopup(pop));
      const li=nodo('li');li.append(nodo('strong',`${t.nombre} — ${t.categoria}`),nodo('span',` · ${dec(t.viento_kt,0)} kt · ${dec(t.presion_hpa,0)} hPa · a ${t.km_a_managua?.toLocaleString('es-NI')??'—'} km de Managua · actualizado ${t.actualizado_utc?.slice(0,16).replace('T',' ')} UTC `));
      if(t.aviso_url){const a=nodo('a','Aviso oficial NHC');a.href=t.aviso_url;a.target='_blank';a.rel='noreferrer';li.append(a)}
      const ver=nodo('button','Ver en el mapa','mini');ver.type='button';
      if(t.lat==null||t.lon==null){ver.disabled=true;ver.title='El NHC no publicó la posición del centro en este aviso.'}
      else ver.onclick=()=>{$('chk-tormentas').checked=true;capaTormentas.addTo(mapa);mapa.setView([t.lat,t.lon],5);if(typeof soloMapa==='function')soloMapa(true)};
      li.append(' ',ver);lista.append(li);
    });
    const p=d.perspectiva||{};const zonas=geo(p.zonas_7_dias,()=>({color:'#ffcf5c',weight:1.5,fillOpacity:.15}),'Zona de posible formación ciclónica (perspectiva NHC a 7 días)');if(zonas)capaTormentas.addLayer(zonas);
    if(!d.activas.length)lista.append(nodo('li','No hay ciclones activos en el Atlántico ni en el Pacífico nororiental según el NHC.'));
    const nz=(p.zonas_7_dias?.features||[]).length;
    est.textContent=`NHC · consulta ${new Date(d.consulta_utc).toLocaleTimeString('es-NI')} · ${d.activas.length} sistema(s) activo(s) · ${nz} zona(s) de posible formación a 7 días.${d.errores.length?' Avisos: '+d.errores.join('; '):''} Información operativa: ante cualquier amenaza sigue los avisos de SINAPRED e INETER.`;
    document.dispatchEvent(new CustomEvent('sicc:tormentas',{detail:d}));
  }catch(e){est.textContent='Ciclones no disponibles: '+(e.message||e)+'. No se muestran datos simulados.'}
}
$('chk-tormentas').onchange=e=>{if(e.target.checked)capaTormentas.addTo(mapa);else capaTormentas.remove()};
cargarTormentas();setInterval(()=>{if(!document.hidden)cargarTormentas()},15*60000);

// ---------------------------------------------------------------- ENOS
async function cargarEnos(){
  const cont=$('enos-tarjetas'),est=$('enos-estado');
  try{
    const r=await window.FuentesMeteo.fetch('/api/enos');const d=await json(r);if(!r.ok)throw Error(d.error||'sin datos');
    cont.replaceChildren();
    const t=(titulo,valor,detalle,clase)=>{const x=nodo('div',undefined,'tarjeta'+(clase?' '+clase:''));x.append(nodo('small',titulo),nodo('strong',valor),nodo('p',detalle));cont.append(x)};
    const ult=d.cpc?.ultimas?.at(-1);
    t('Fase actual (ONI)',d.fase_actual,'Clasificación orientativa por umbrales NOAA',d.oni_actual>=.5?'calido':d.oni_actual<=-.5?'frio':'');
    t('ONI',`${d.oni_actual>0?'+':''}${dec(d.oni_actual,2)} °C`,ult?`Temporada ${ult.temporada} ${ult.anio} · NOAA CPC`:'Archivo local');
    const s=d.nino34_semanal?.semanas?.at(-1);
    if(s)t('Niño 3.4 semanal',`${s.nino34>0?'+':''}${dec(s.nino34,1)} °C`,`Semana del ${s.semana} · OISST`);
    if(s)t('Niño 1+2 (costa de Sudamérica)',`${s.nino12>0?'+':''}${dec(s.nino12,1)} °C`,`Semana del ${s.semana}`);
    est.textContent=`${d.criterio} Fuentes: ${d.fuente_local}; ${d.cpc?.fuente||'CPC no disponible'}; ${d.nino34_semanal?.fuente||''}.${d.errores.length?' Avisos: '+d.errores.join('; '):''} Relación con lluvia en Nicaragua: El Niño suele asociarse a déficit de lluvia en el Pacífico y centro del país, pero no en todos los años; no es un pronóstico local.`;
    document.dispatchEvent(new CustomEvent('sicc:enos',{detail:d}));
  }catch(e){est.textContent='ENOS no disponible: '+(e.message||e)}
}
cargarEnos();

window.SICC_fenomenos={estado:()=>({capas:{...estado},tormentas:tormentasDatos?tormentasDatos.activas.map(t=>t.nombre):null})};
})();
