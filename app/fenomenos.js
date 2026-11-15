// Capas de fenómenos: satélite GOES-East, radar, lluvia IMERG, anomalía de temperatura del mar,
// aerosoles, ciclones tropicales del NHC y estado de ENOS. Si una fuente falla, no se dibuja nada.
(function(){
const $=id=>document.getElementById(id);
const nodo=(t,txt,c)=>{const n=document.createElement(t);if(txt!==undefined)n.textContent=txt;if(c)n.className=c;return n};
const dec=(v,n=1)=>v===null||v===undefined?'—':Number(v).toLocaleString('en-US',{minimumFractionDigits:n,maximumFractionDigits:n});
const json=r=>typeof leerJSON==='function'?leerJSON(r):r.json();
if(typeof mapa==='undefined'||!mapa)return;

// ---------------------------------------------------------------- capas raster
const CAPAS={
  sat:{capa:'GOES-East_ABI_GeoColor',limites:[[-81.3,-156.2],[81.3,6.2]],z:5,op:1,zoom:7},
  imerg:{capa:'IMERG_Precipitation_Rate_30min',z:6,op:.85,zoom:6},
  sst:{capa:'GHRSST_L4_MUR_Sea_Surface_Temperature_Anomalies',z:3,op:.75,zoom:7},
  aod:{capa:'MODIS_Combined_Value_Added_AOD',z:4,op:.7,zoom:6}
};
const estado={},vivo={},turno={};
const GIBS='https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/';
// GOES-East publica una imagen cada 10 min con ~30–40 min de retraso; las horas aún no publicadas dan 404.
// Se busca la más reciente desde el navegador, sin depender de la hora fijada al compilar.
async function ultimaGoes(capa){
  const paso=600000,ahora=Math.floor(Date.now()/paso)*paso;
  for(let i=1;i<=12;i++){
    const hora=new Date(ahora-i*paso).toISOString().slice(0,19)+'Z';
    try{const r=await fetch(`${GIBS}${capa}/default/${hora}/GoogleMapsCompatible_Level7/0/0/0.png`);
      if(r.ok)return{capa,hora_utc:hora,matriz:'GoogleMapsCompatible_Level7',formato:'png'}}catch(e){return null}
  }
  return null;
}
async function capaGibs(k){
  const c=CAPAS[k],chk=$('chk-'+k),mio=turno[k]=(turno[k]||0)+1;
  if(!chk.checked){if(vivo[k]){mapa.removeLayer(vivo[k]);vivo[k]=null}estado[k]=null;horaSat();return}
  try{
    let d=k==='sat'?await ultimaGoes(c.capa):null;
    if(!d){const r=await window.FuentesMeteo.fetch('/api/gibs_hora?capa='+encodeURIComponent(c.capa));d=await json(r);if(!r.ok)throw Error(d.error||'unavailable')}
    if(!chk.checked||turno[k]!==mio)return;
    if(vivo[k]&&estado[k]===d.hora_utc)return;
    // La imagen nueva se superpone y la anterior se retira al cargar: sin parpadeo al renovar.
    const viejo=vivo[k];
    vivo[k]=L.tileLayer(`${GIBS}${d.capa}/default/${d.hora_utc}/${d.matriz}/{z}/{y}/{x}.${d.formato}`,{maxNativeZoom:c.zoom,maxZoom:18,bounds:c.limites,opacity:c.op,zIndex:c.z,attribution:'NASA GIBS'}).addTo(mapa);
    if(viejo)vivo[k].once('load',()=>mapa.removeLayer(viejo));
    estado[k]=d.hora_utc;
  }catch(e){if(turno[k]===mio){if(vivo[k]){mapa.removeLayer(vivo[k]);vivo[k]=null}estado[k]='unavailable';chk.checked=false;typeof error==='function'&&error(Error(`${c.nombre||k} layer could not be loaded.`))}}
  if(k==='sat')horaSat();
}
function horaSat(){
  const h=estado.sat,span=$('hora-sat');if(!span)return;
  span.textContent=!h?'':h==='unavailable'?'Unavailable':`${h.slice(11,16)} UTC (${Math.max(0,Math.round((Date.now()-Date.parse(h))/60000))} min ago)`;
}
async function radar(){
  const mio=turno.radar=(turno.radar||0)+1;
  if(vivo.radar){mapa.removeLayer(vivo.radar);vivo.radar=null}
  if(!$('chk-radar').checked){estado.radar=null;return}
  try{const r=await fetch('https://api.rainviewer.com/public/weather-maps.json');const d=await json(r);if(!r.ok)throw Error('RainViewer '+r.status);const f=d.radar.past.at(-1);if(!$('chk-radar').checked||turno.radar!==mio)return;
    vivo.radar=L.tileLayer(`${d.host}${f.path}/256/{z}/{x}/{y}/2/1_1.png`,{opacity:.8,maxNativeZoom:7,maxZoom:18,zIndex:6,attribution:'Radar © RainViewer'}).addTo(mapa);
    estado.radar=new Date(f.time*1000).toISOString()}catch(e){if(turno.radar===mio){estado.radar='unavailable';$('chk-radar').checked=false;typeof error==='function'&&error(Error('Weather radar layer could not be loaded.'))}}
}
for(const k in CAPAS)$('chk-'+k).onchange=()=>capaGibs(k);
$('chk-radar').onchange=radar;
setInterval(()=>{if(document.hidden)return;if($('chk-radar').checked)radar();if($('chk-imerg').checked)capaGibs('imerg')},10*60000);
// GOES: buscar imagen nueva cada 2 min (sale cada 10) y refrescar el «hace N min».
setInterval(()=>{if(!document.hidden&&$('chk-sat').checked)capaGibs('sat')},2*60000);
// Los botones «Show» llevan al mapa 2D, activan la capa y encuadran la región.
document.querySelectorAll('[data-activar]').forEach(b=>b.onclick=async()=>{
  const c=$(b.dataset.activar);if(!c.checked){c.checked=true;c.dispatchEvent(new Event('change'))}
  const [la,lo,z]=(b.dataset.vista||'12,-80,3').split(',').map(Number);
  await window.SICC_vista.irA(la,lo,z);
});

// ---------------------------------------------------------------- ciclones tropicales
const capaTormentas=L.layerGroup();
const CATEGORIAS={'Depresión tropical':['Tropical depression','#5ec8ff'],'Tormenta tropical':['Tropical storm','#5fe08a'],'Huracán cat. 1':['Hurricane cat. 1','#ffe066'],'Huracán cat. 2':['Hurricane cat. 2','#ffb347'],'Huracán cat. 3':['Hurricane cat. 3','#ff7b4a'],'Huracán cat. 4':['Hurricane cat. 4','#ff4d6d'],'Huracán cat. 5':['Hurricane cat. 5','#d65cff']};
const categoria=c=>CATEGORIAS[c]||[c,'#fff'];
function geo(fc,estilo,popup){if(!fc||!fc.features||!fc.features.length)return null;const g=L.geoJSON(fc,{style:estilo,pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:4,color:'#fff',weight:1,fillColor:estilo().color,fillOpacity:1})});if(popup)g.bindPopup(popup);return g}
let tormentasDatos=null;
async function cargarTormentas(){
  const lista=$('lista-tormentas');
  try{
    const r=await window.FuentesMeteo.fetch('/api/tormentas');const d=await json(r);if(!r.ok)throw Error(d.error||'no data');tormentasDatos=d;
    capaTormentas.clearLayers();lista.replaceChildren();
    d.activas.forEach(t=>{
      const [cat,c]=categoria(t.categoria),pop=`${t.nombre} · ${cat} · ${dec(t.viento_kt,0)} kt · ${dec(t.presion_hpa,0)} hPa`;
      [geo(t.cono,()=>({color:c,weight:1,fillOpacity:.12,dashArray:'4 4'}),`${t.nombre}: forecast cone`),
       geo(t.trayectoria_pasada,()=>({color:'#cfd8e3',weight:2,opacity:.8}),`${t.nombre}: past track`),
       geo(t.trayectoria_pronostico,()=>({color:c,weight:2.5}),`${t.nombre}: forecast track`),
       geo(t.puntos_pronostico,()=>({color:c}),`${t.nombre}: forecast points`)].forEach(g=>g&&capaTormentas.addLayer(g));
      if(t.lat!=null)capaTormentas.addLayer(L.marker([t.lat,t.lon],{icon:L.divIcon({className:'',html:`<div class="ciclon" style="--c:${c}">🌀</div>`,iconSize:[30,30],iconAnchor:[15,15]})}).bindPopup(pop));
      const li=nodo('li');li.append(nodo('strong',`${t.nombre} — ${cat}`),nodo('span',` · ${dec(t.viento_kt,0)} kt · ${dec(t.presion_hpa,0)} hPa `));
      if(t.aviso_url){const a=nodo('a','NHC advisory');a.href=t.aviso_url;a.target='_blank';a.rel='noreferrer';li.append(a)}
      if(t.lat!=null&&t.lon!=null){const ver=nodo('button','Show','mini');ver.type='button';ver.onclick=async()=>{$('chk-tormentas').checked=true;capaTormentas.addTo(mapa);await window.SICC_vista.irA(t.lat,t.lon,5)};li.append(' ',ver)}
      lista.append(li);
    });
    const p=d.perspectiva||{};const zonas=geo(p.zonas_7_dias,()=>({color:'#ffcf5c',weight:1.5,fillOpacity:.15}),'Possible formation area (NHC 7-day outlook)');if(zonas)capaTormentas.addLayer(zonas);
    if(!d.activas.length)lista.append(nodo('li','No active cyclones in the Atlantic or eastern Pacific.'));
    document.dispatchEvent(new CustomEvent('sicc:tormentas',{detail:d}));
  }catch(e){lista.replaceChildren(nodo('li','Cyclone data unavailable.'))}
}
$('chk-tormentas').onchange=e=>{if(e.target.checked)capaTormentas.addTo(mapa);else capaTormentas.remove()};
cargarTormentas();setInterval(()=>{if(!document.hidden)cargarTormentas()},15*60000);

// ---------------------------------------------------------------- ENOS
const FASES={'El Niño':'El Niño','La Niña':'La Niña','Neutral':'Neutral','Neutro':'Neutral'};
async function cargarEnos(){
  const cont=$('enos-tarjetas');
  try{
    const r=await window.FuentesMeteo.fetch('/api/enos');const d=await json(r);if(!r.ok)throw Error(d.error||'no data');
    cont.replaceChildren();
    const t=(titulo,valor,detalle,clase)=>{const x=nodo('div',undefined,'tarjeta'+(clase?' '+clase:''));x.append(nodo('small',titulo),nodo('strong',valor),nodo('p',detalle));cont.append(x)};
    const ult=d.cpc?.ultimas?.at(-1),fase=d.oni_actual>=.5?'El Niño':d.oni_actual<=-.5?'La Niña':'Neutral';
    t('ENSO phase',FASES[fase]||fase,'NOAA ONI thresholds',d.oni_actual>=.5?'calido':d.oni_actual<=-.5?'frio':'');
    t('ONI',`${d.oni_actual>0?'+':''}${dec(d.oni_actual,2)} °C`,ult?`${ult.temporada} ${ult.anio} · NOAA CPC`:'NOAA CPC');
    const s=d.nino34_semanal?.semanas?.at(-1);
    if(s)t('Niño 3.4 weekly',`${s.nino34>0?'+':''}${dec(s.nino34,1)} °C`,`Week of ${s.semana} · OISST`);
    if(s)t('Niño 1+2',`${s.nino12>0?'+':''}${dec(s.nino12,1)} °C`,`Week of ${s.semana}`);
    document.dispatchEvent(new CustomEvent('sicc:enos',{detail:d}));
  }catch(e){cont.replaceChildren(nodo('p','ENSO data unavailable.'))}
}
cargarEnos();

window.SICC_fenomenos={estado:()=>({capas:{...estado},tormentas:tormentasDatos?tormentasDatos.activas.map(t=>t.nombre):null})};
})();
