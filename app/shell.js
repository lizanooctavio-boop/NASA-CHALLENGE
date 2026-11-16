// Armazón de la interfaz: mapa Leaflet, pestañas, ventanas, consulta puntual mundial y cambio de vista
// entre el globo 3D (app/espacio.js) y el mapa 2D.
let mapa,punto;
const $=id=>document.getElementById(id);
function mensajeError(e,respaldo='Connection error: external data could not be loaded.'){
  const m=e&&e.message?String(e.message):String(e||'');
  if(!m||/failed to fetch|networkerror|load failed|fetch/i.test(m))return respaldo;
  return m;
}
let focoAntesError=null;
function cerrarError(){const caja=$('error');if(caja.hidden)return;const dentro=caja.contains(document.activeElement);caja.hidden=true;if(dentro)(focoAntesError?.isConnected?focoAntesError:$('contenido-principal'))?.focus({preventScroll:true});focoAntesError=null}
function error(e,respaldo){if($('error').hidden&&document.activeElement&&!$('error').contains(document.activeElement))focoAntesError=document.activeElement;$('error').hidden=false;$('error-texto').textContent=mensajeError(e,respaldo)}
$('error-cerrar').onclick=cerrarError;
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('error').hidden){e.preventDefault();cerrarError()}});
// Lee JSON sin errores crípticos («Unexpected token <») cuando el servidor devuelve HTML.
async function leerJSON(r){const t=await r.text();try{return JSON.parse(t)}catch(e){throw Error(r.ok?'Invalid server response.':`Server responded ${r.status}.`)}}
function limpiar(n){n.replaceChildren()}
function nodo(tag,texto,clase){const n=document.createElement(tag);if(texto!==undefined)n.textContent=texto;if(clase)n.className=clase;return n}
function tarjeta(contenedor,titulo,valor,detalle){const d=nodo('div',undefined,'tarjeta');d.append(nodo('small',titulo),nodo('strong',valor));if(detalle)d.append(nodo('p',detalle));contenedor.append(d)}
const decimal=(v,n=2)=>Number(v).toLocaleString(window.GnomonI18n?.locale()||'en-US',{maximumFractionDigits:n,minimumFractionDigits:n});
async function api(url){const r=await window.FuentesMeteo.fetch(url);const d=await leerJSON(r);if(!r.ok)throw Error(d.error||'Data unavailable');return d}
function tab(id,actualizarRuta=true){const boton=document.querySelector(`nav button[data-tab="${id}"]`);if(!boton)return;document.querySelectorAll('.vista').forEach(v=>v.hidden=v.id!==id);document.querySelectorAll('nav button').forEach(b=>{b.classList.toggle('activo',b.dataset.tab===id);if(b.dataset.tab===id)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});$('titulo').textContent=boton.textContent;soloMapa(false);if(actualizarRuta&&location.hash!=='#'+id)history.pushState(null,'','#'+id);document.dispatchEvent(new CustomEvent('sicc:pestana',{detail:id}))}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>tab(b.dataset.tab));
// Acceso a Configuración del encabezado del menú móvil (en escritorio sigue en la lista).
$('atajo-configuracion').onclick=()=>tab('configuracion');
document.addEventListener('sicc:pestana',e=>{if(e.detail==='configuracion')$('atajo-configuracion').setAttribute('aria-current','page');else $('atajo-configuracion').removeAttribute('aria-current')});

// ---------------------------------------------------------------- mapa 2D
const CENTRO_AMERICA=[12,-80];
const zoomAjuste=()=>Math.max(2,Math.ceil(Math.log2(Math.max(innerWidth,innerHeight)/256)));
let esriEtiquetasOk=true,refrescarEtiquetas=null,baseFallo=false,avisoBase=false;
function vigilarBase(capa,nombre,esEtiqueta){
  let cargadas=0,errores=0;
  capa.on('tileload',()=>{
    cargadas++;
    if(esEtiqueta&&!esriEtiquetasOk){esriEtiquetasOk=true;refrescarEtiquetas?.()}
    if(!esEtiqueta){baseFallo=false}
  });
  capa.on('tileerror',()=>{
    errores++;
    if(cargadas===0&&errores>=2){
      if(esEtiqueta&&esriEtiquetasOk){esriEtiquetasOk=false;refrescarEtiquetas?.()}
      if(!esEtiqueta){baseFallo=true;if(modo==='mapa'&&!avisoBase){avisoBase=true;error(`${nombre} base imagery could not be loaded. Vector borders and labels remain active.`)}}
    }
  });
}
function iniciarMapa(){
  if(mapa||!window.L)return;
  mapa=L.map('mapa',{zoomControl:false,worldCopyJump:true,minZoom:2,maxZoom:18,zoomSnap:1}).setView(CENTRO_AMERICA,zoomAjuste());
  L.control.zoom({position:'bottomright'}).addTo(mapa);
  // Mismo mosaico Blue Marble que la textura del globo: el paso de 3D a 2D no cambia la imagen.
  const nasaBase=L.tileLayer('https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_NextGeneration/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg',{maxNativeZoom:8,maxZoom:18,className:'base-nasa',attribution:'NASA Blue Marble · GIBS'}).addTo(mapa);
  vigilarBase(nasaBase,'NASA Blue Marble',false);
  // Al acercarse, foto satelital de alta resolución (mosaico fijo, no en vivo) y nombres de lugares encima.
  const ESRI='https://server.arcgisonline.com/ArcGIS/rest/services/';
  const esriImg=L.tileLayer(ESRI+'World_Imagery/MapServer/tile/{z}/{y}/{x}',{minZoom:6,maxNativeZoom:19,maxZoom:18,zIndex:1,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'}).addTo(mapa);
  vigilarBase(esriImg,'High-resolution satellite',false);
  mapa.createPane('etiquetas').style.zIndex=350;
  const esriEtq=L.tileLayer(ESRI+'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{pane:'etiquetas',minZoom:6,maxNativeZoom:19,maxZoom:18,attribution:'Labels © Esri'}).addTo(mapa);
  vigilarBase(esriEtq,'Place labels',true);
  mapa.on('click',e=>{if(window.ETDCapturaMapa?.(e))return;if($('consultar').disabled)return;elegirPunto(e.latlng.lat,L.Util.wrapNum(e.latlng.lng,[-180,180]))});
}
function elegirPunto(lat,lon){$('lat').value=lat.toFixed(3);$('lon').value=lon.toFixed(3);if(!$('meteorologia').hidden||true)$('consulta-punto').requestSubmit()}

// ---------------------------------------------------------------- consulta puntual (Open-Meteo, mundial)
let pronostico=null;
async function consultar(){const b=$('consultar');if(b.disabled)return;
  const lat=$('lat').valueAsNumber,lon=$('lon').valueAsNumber;
  if(!Number.isFinite(lat+lon))return;
  if(document.querySelector('nav button.activo')?.dataset.tab!=='meteorologia')tab('meteorologia');
  document.dispatchEvent(new CustomEvent('sicc:punto',{detail:[lat,lon]}));
  b.disabled=true;b.textContent='Loading…';$('error').hidden=true;
  try{
    const r=await api(`/api/tiempo?lat=${lat}&lon=${lon}`);const c=r?.datos?.current,u=r?.datos?.current_units;
    if(!c||!u)throw Error('Live forecast service returned incomplete data.');
    const met=$('meteo');limpiar(met);
    met.append(nodo('p',`${Math.abs(lat).toFixed(2)}° ${lat>=0?'N':'S'}, ${Math.abs(lon).toFixed(2)}° ${lon>=0?'E':'W'} · ${c.time.replace('T',' ')} UTC`,'coordenadas'));
    const tarjetas=nodo('div',undefined,'tarjetas');const valor=v=>v===null||v===undefined?'—':decimal(v,1);
    tarjeta(tarjetas,'Temperature',`${valor(c.temperature_2m)} ${u.temperature_2m}`);
    tarjeta(tarjetas,'Precipitation',`${valor(c.precipitation)} ${u.precipitation}`);
    tarjeta(tarjetas,'Wind',`${valor(c.wind_speed_10m)} ${u.wind_speed_10m}`,c.wind_direction_10m==null?'':`from ${Math.round(c.wind_direction_10m)}°`);
    met.append(tarjetas);
    pronostico={lat,lon,horas:r.datos.hourly,unidades:r.datos.hourly_units,fuente:r.fuente,consulta:r.consulta_utc};
    if(mapa){if(punto)mapa.removeLayer(punto);const dir=Number(c.wind_direction_10m);const icon=L.divIcon({className:'',html:Number.isFinite(dir)?`<div class="viento" style="transform:rotate(${dir+180}deg)">↑</div>`:'<div class="marca-punto-mapa"></div>',iconSize:[32,38],iconAnchor:[16,19]});punto=L.marker([lat,lon],{icon,interactive:false}).addTo(mapa)}
    document.dispatchEvent(new CustomEvent('sicc:pronostico',{detail:pronostico}));
  }catch(e){
    const msg=mensajeError(e,'Live forecast service could not be reached. Check your connection or try again later.');
    error(msg);const met=$('meteo');limpiar(met);met.append(nodo('p',msg,'pista'));
    pronostico=null;document.dispatchEvent(new CustomEvent('sicc:pronostico',{detail:null}));
  }
  finally{b.disabled=false;b.textContent='Get forecast'}}
$('consulta-punto').onsubmit=e=>{e.preventDefault();consultar()};
function csvPunto(){
  if(!pronostico?.horas)return;
  const h=pronostico.horas,cols=Object.keys(h).filter(k=>k!=='time');
  const filas=h.time.map((t,i)=>[t,pronostico.lat,pronostico.lon,...cols.map(k=>h[k][i]??'')].join(','));
  const csv='﻿'+['# Source: '+pronostico.fuente,'# Retrieved: '+pronostico.consulta,'time_utc,latitude,longitude,'+cols.join(',')].concat(filas).join('\r\n')+'\r\n';
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download=`forecast_${pronostico.lat.toFixed(2)}_${pronostico.lon.toFixed(2)}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),30000);
}
document.addEventListener('sicc:pronostico',e=>{const ok=!!e.detail;$('exp-punto').disabled=!ok;const b=document.querySelector('[data-descarga="punto"]');if(b)b.disabled=!ok});
$('exp-punto').onclick=csvPunto;
document.querySelector('[data-descarga="punto"]').onclick=csvPunto;

// ---------------------------------------------------------------- paneles
// Si el foco estaba en un panel que se oculta, pasa a «Show panels»; al restaurarlos vuelve a ese control.
let focoPaneles=null;
function soloMapa(v){const activo=document.activeElement;document.body.classList.toggle('solo-mapa',v);if(v){if(activo&&activo!==$('solomapa')&&activo.closest?.('aside,.vista')){focoPaneles=activo;$('solomapa').focus()}}else{const f=focoPaneles;focoPaneles=null;if(f&&document.activeElement===$('solomapa')&&f.isConnected&&f.getClientRects().length)f.focus()}$('solomapa').setAttribute('aria-pressed',String(v));$('solomapa').textContent=v?'Show panels':'Hide panels';document.dispatchEvent(new CustomEvent('sicc:paneles'));requestAnimationFrame(ajustarAltoMapa)}
$('solomapa').onclick=()=>soloMapa(!document.body.classList.contains('solo-mapa'));
// El mapa ocupa el espacio que deja la franja de controles en pantallas compactas.
function ajustarAltoMapa(){const cont=$('controles-mapa');if(!cont)return;const compacto=matchMedia('(max-width:700px), (max-height:500px) and (max-width:1000px)').matches;const valor=(compacto?Math.ceil(cont.getBoundingClientRect().height):0)+'px';if(document.documentElement.style.getPropertyValue('--alto-controles-mapa')===valor)return;document.documentElement.style.setProperty('--alto-controles-mapa',valor);if(mapa)mapa.invalidateSize({animate:false})}
if(typeof ResizeObserver==='function')new ResizeObserver(ajustarAltoMapa).observe($('controles-mapa'));
addEventListener('resize',ajustarAltoMapa);ajustarAltoMapa();
// Ventanas: barra de título con ocultar, minimizar y ancho completo
document.querySelectorAll('.vista').forEach(v=>{const titulo=document.querySelector(`[data-tab="${v.id}"]`).textContent;const cuerpo=nodo('div',undefined,'ventana-cuerpo');while(v.firstChild)cuerpo.append(v.firstChild);const barra=nodo('div',undefined,'ventana-barra');const pts=nodo('div',undefined,'ventana-botones');
  const boton=(clase,etiqueta,accion)=>{const b=nodo('button','','punto '+clase);b.type='button';b.title=etiqueta;b.setAttribute('aria-label',etiqueta);b.onclick=accion;pts.append(b)};
  boton('rojo','Hide panel',()=>soloMapa(true));boton('ambar','Minimize',()=>{v.classList.toggle('minimizada');document.dispatchEvent(new CustomEvent('sicc:paneles'))});boton('verde','Wide',()=>{v.classList.toggle('ancha');document.dispatchEvent(new CustomEvent('sicc:paneles'))});
  barra.append(pts,nodo('span',titulo,'ventana-titulo'));barra.ondblclick=()=>v.classList.toggle('minimizada');v.append(barra,cuerpo);v.classList.add('ventana')});
iniciarMapa();
if(!window.L){const b=$('vista-mapa');if(b){b.disabled=true;b.title='2D map unavailable: its files could not be downloaded'}error('The 2D map could not be downloaded. The 3D globe still works; reload to try again.')}

const pref={leer:(k,s)=>{try{return (s||window.localStorage).getItem(k)}catch(e){return null}},guardar:(k,v,s)=>{try{(s||window.localStorage).setItem(k,v)}catch(e){}}};
// Menú plegable: en escritorio se reduce a una barra de iconos.
function plegarMenu(v,guardar){
  document.body.classList.toggle('menu-plegado',v);
  const b=$('plegar-menu');b.setAttribute('aria-expanded',String(!v));b.setAttribute('aria-label',v?'Expand menu':'Collapse menu');b.title=v?'Expand menu':'Collapse menu';
  document.querySelectorAll('nav button').forEach(x=>{x.dataset.nombre=x.textContent.trim();x.removeAttribute('title')});
  if(guardar)pref.guardar('etd-menu-plegado',v?'1':'0');
  document.dispatchEvent(new CustomEvent('sicc:paneles'));
}
{const p=pref.leer('etd-menu-plegado');plegarMenu(p===null?innerWidth<1280:p==='1',false)}
$('plegar-menu').onclick=()=>plegarMenu(!document.body.classList.contains('menu-plegado'),true);

// Columna de controles: la leyenda se apila sobre la línea de tiempo y la barra de capas usa el alto libre.
function medirColumnaMapa(){
  const raiz=document.documentElement.style,alto=el=>el&&!el.hidden&&el.getClientRects().length?Math.ceil(el.getBoundingClientRect().height):0;
  raiz.setProperty('--alto-lt',alto($('linea-tiempo'))+'px');raiz.setProperty('--alto-ley',alto($('leyenda-campo'))+'px');
  raiz.setProperty('--alto-cabecera',(alto(document.querySelector('header'))||58)+'px');marcarDesborde();
}
// En pantallas estrechas el menú se desplaza en horizontal: se difumina el borde que aún tiene pestañas detrás.
function marcarMenu(){const n=$('menu-principal');if(n){n.classList.toggle('mas-derecha',n.scrollLeft+n.clientWidth<n.scrollWidth-4);n.classList.toggle('mas-izquierda',n.scrollLeft>4)}}
$('menu-principal')?.addEventListener('scroll',marcarMenu,{passive:true});addEventListener('resize',marcarMenu);setTimeout(marcarMenu,0);
function marcarDesborde(){const c=document.querySelector('#barra-capas .ventana-cuerpo');if(c)c.classList.toggle('mas-abajo',c.scrollTop+c.clientHeight<c.scrollHeight-4)}
document.querySelector('#barra-capas .ventana-cuerpo').addEventListener('scroll',marcarDesborde,{passive:true});
if(typeof ResizeObserver==='function'){const ro=new ResizeObserver(medirColumnaMapa);['linea-tiempo','leyenda-campo','barra-capas'].forEach(id=>ro.observe($(id)));ro.observe(document.querySelector('header'))}
addEventListener('resize',medirColumnaMapa);medirColumnaMapa();

// ---------------------------------------------------------------- globo 3D ⇄ mapa 2D
let modo='globo',cambiando=false,vistaPendiente=null,transicionActual=null,vectorialCargado=false;
function cargarBaseVectorial(){if(vectorialCargado||!mapa)return;vectorialCargado=true;baseVectorial()}
const esperar=ms=>new Promise(r=>setTimeout(r,ms));
function marcarVista(){
  $('vista-globo').setAttribute('aria-pressed',String(modo==='globo'));
  $('vista-mapa').setAttribute('aria-pressed',String(modo==='mapa'));
  // Evita que #espacio siga en el orden de tabulación detrás de #mapa cuando el mapa 2D está activo.
  const enMapa=modo==='mapa';
  $('espacio')?.setAttribute('tabindex',enMapa?'-1':'0');
  if(enMapa){$('espacio')?.setAttribute('aria-hidden','true');$('mapa')?.removeAttribute('aria-hidden')}
  else{$('espacio')?.removeAttribute('aria-hidden');$('mapa')?.setAttribute('aria-hidden','true')}
}
async function cambiarVista(nuevo){
  if(!mapa)return;
  if(nuevo==='globo'&&$('vista-globo').disabled)return;
  if(cambiando){vistaPendiente=nuevo;return transicionActual}
  if(nuevo===modo)return;
  if(nuevo==='mapa')cargarBaseVectorial();
  if(!window.Espacio){
    modo=nuevo;document.body.classList.toggle('modo-mapa',nuevo==='mapa');document.body.classList.toggle('modo-globo',nuevo==='globo');
    marcarVista();document.dispatchEvent(new CustomEvent('sicc:vista',{detail:nuevo}));
    if(nuevo==='mapa'&&baseFallo&&!avisoBase){avisoBase=true;error('Base satellite imagery could not be loaded. Vector borders and labels remain active.')}
    return;
  }
  cambiando=true;document.body.classList.add('en-transicion');modo=nuevo;marcarVista();
  transicionActual=(async()=>{
    try{
      if(nuevo==='mapa'){
        mapa.invalidateSize({animate:false});mapa.setView(CENTRO_AMERICA,zoomAjuste(),{animate:false});
        const c=mapa.getCenter();
        await window.Espacio.aMapa({lon:c.lng,lat:c.lat,zoom:mapa.getZoom()});
        document.body.classList.toggle('modo-mapa',true);document.body.classList.toggle('modo-globo',false);
        document.dispatchEvent(new CustomEvent('sicc:vista',{detail:'mapa'}));
        if(baseFallo&&!avisoBase){avisoBase=true;error('Base satellite imagery could not be loaded. Vector borders and labels remain active.')}
        if(!matchMedia('(prefers-reduced-motion:reduce)').matches)await esperar(520);
        if(!vistaPendiente||vistaPendiente==='mapa')window.Espacio.pausar(true);
      }else{
        const c=mapa.getCenter(),vuelta=window.Espacio.aGlobo({lon:L.Util.wrapNum(c.lng,[-180,180]),lat:c.lat,zoom:mapa.getZoom()});
        document.body.classList.toggle('modo-globo',true);document.body.classList.toggle('modo-mapa',false);
        document.dispatchEvent(new CustomEvent('sicc:vista',{detail:'globo'}));
        if(!matchMedia('(prefers-reduced-motion:reduce)').matches)await esperar(420);
        await vuelta.animar();
      }
    }finally{
      cambiando=false;document.body.classList.remove('en-transicion');
    }
    const sig=vistaPendiente;vistaPendiente=null;
    if(sig&&sig!==modo)return cambiarVista(sig);
  })();
  return transicionActual;
}
$('vista-globo').onclick=()=>{if(!$('meteorologia').hidden)history.pushState(null,'','#globe');cambiarVista('globo')};
$('vista-mapa').onclick=()=>{if(!$('meteorologia').hidden)history.pushState(null,'','#map');cambiarVista('mapa')};
// Marca del lugar de una investigación («Show on the map»): un círculo con su nombre, uno cada vez.
let marcaLugar=null;
function marcar(lat,lon,nombre){
  if(!mapa)return;
  marcaLugar?.remove();
  marcaLugar=L.circleMarker([lat,lon],{radius:9,color:'#f6c76b',weight:3,fillColor:'#f6c76b',fillOpacity:.25}).addTo(mapa);
  if(nombre)marcaLugar.bindTooltip(nodo('span',nombre),{permanent:true,direction:'top',offset:[0,-8],className:'marca-lugar'}).openTooltip();
}
window.SICC_vista={modo:()=>modo,cambiar:cambiarVista,irA:async(lat,lon,z)=>{if(!mapa)return;await cambiarVista('mapa');mapa.setView([lat,lon],z)},marcar,soloMapa};
const salidaHash=()=>{if(location.hash==='#map'){if(modo==='mapa'&&window.Espacio)window.Espacio.pausar(true);else cambiarVista('mapa')}};
document.addEventListener('espacio:listo',()=>{document.body.classList.remove('cargando');salidaHash()});
// Sin WebGL el globo no arranca: se entra al mapa 2D y se desactiva el botón Globe.
// Si falla la descarga del globo (Three.js desde la CDN) ocurre lo mismo, con otro aviso.
document.addEventListener('espacio:error',e=>{
  document.body.classList.remove('cargando');
  const carga=e.detail==='carga',b=$('vista-globo');b.disabled=true;
  b.title=carga?'3D globe unavailable: its files could not be downloaded':'3D globe unavailable: WebGL is disabled in this browser';
  cambiarVista('mapa');
  error(carga?'The 3D globe could not be downloaded. Showing the 2D map; reload to try again.':'The 3D globe needs WebGL, which is unavailable in this browser. Showing the 2D map.');
});
if(window.Espacio)document.body.classList.remove('cargando');
setTimeout(()=>{if(location.hash==='#map'&&modo!=='mapa'&&!window.Espacio)salidaHash()},1200);
// Explicación concreta de Aprender: abre la pestaña, conserva el fragmento exacto en la URL y la resalta.
function abrirExplicacion(ancla,actualizarRuta=true){const e=ancla.startsWith('aprender-')&&document.getElementById(ancla);if(!e||!$('aprender').contains(e))return false;tab('aprender',false);if(actualizarRuta&&location.hash!=='#'+ancla)history.pushState(null,'','#'+ancla);e.scrollIntoView({block:'start'});e.classList.add('resaltado');setTimeout(()=>e.classList.remove('resaltado'),1600);return true}
// #inv=… es una investigación compartida (app/expediente.js): no cambia la vista por sí sola.
function seguirRuta(){const hash=location.hash.slice(1);if(hash.startsWith('inv='))return;if(abrirExplicacion(hash,false))return;if(hash==='map'||hash==='globe'){tab('meteorologia',false);cambiarVista(hash==='map'?'mapa':'globo');return}const id=hash==='proyecciones'?'escenarios':hash;if(document.querySelector(`nav button[data-tab="${CSS.escape(id)}"]`))tab(id,false);else if(!hash)tab('meteorologia',false)}
addEventListener('hashchange',seguirRuta);
addEventListener('popstate',seguirRuta);
document.addEventListener('DOMContentLoaded',seguirRuta);

// ---------------------------------------------------------------- base vectorial: fronteras y nombres (Natural Earth)
function baseVectorial(){
  const panel=(n,z)=>{if(!mapa.getPane(n)){mapa.createPane(n);mapa.getPane(n).style.zIndex=z;mapa.getPane(n).style.pointerEvents='none'}};
  panel('referencia',450);
  const CIUDADES=[['Washington',38.9,-77.04,4],['Mexico City',19.43,-99.13,4],['Ottawa',45.42,-75.7,5],['Havana',23.11,-82.37,5],['Guatemala City',14.63,-90.51,6],['Managua',12.14,-86.25,6],['San José',9.93,-84.09,6],['Panama City',8.98,-79.52,6],['Bogotá',4.71,-74.07,4],['Caracas',10.48,-66.9,5],['Quito',-0.18,-78.47,5],['Lima',-12.05,-77.04,4],['La Paz',-16.5,-68.15,5],['Brasília',-15.79,-47.88,4],['Santiago',-33.45,-70.67,4],['Buenos Aires',-34.6,-58.38,4],['Montevideo',-34.9,-56.16,5],['New York',40.71,-74.01,4],['Los Angeles',34.05,-118.24,5],['London',51.51,-0.13,4],['Paris',48.86,2.35,4],['Madrid',40.42,-3.7,4],['Rome',41.9,12.5,5],['Berlin',52.52,13.4,5],['Cairo',30.04,31.24,4],['Lagos',6.52,3.38,5],['Nairobi',-1.29,36.82,5],['Cape Town',-33.92,18.42,5],['Moscow',55.76,37.62,4],['Delhi',28.61,77.21,4],['Beijing',39.9,116.4,4],['Tokyo',35.68,139.69,4],['Jakarta',-6.2,106.85,5],['Sydney',-33.87,151.21,4]];
  fetch('assets/mundo.geojson').then(r=>r.json()).then(g=>{
    L.geoJSON({type:'FeatureCollection',features:g.features.filter(f=>f.properties.tipo==='pais')},{pane:'referencia',renderer:L.canvas({pane:'referencia'}),interactive:false,style:{color:'rgba(235,242,250,.5)',weight:.7,fill:false}}).addTo(mapa);
    const etq=[];
    g.features.filter(f=>f.properties.tipo==='pais'&&f.properties.lx!=null).forEach(f=>etq.push([L.marker([f.properties.ly,f.properties.lx],{pane:'referencia',interactive:false,keyboard:false,icon:L.divIcon({className:'etq-pais',html:nodo('span',f.properties.nombre_en||f.properties.nombre),iconSize:null})}),Math.max(3,(f.properties.rango||5)-1)]));
    etq.sort((a,b)=>a[1]-b[1]);
    CIUDADES.forEach(([n,la,lo,z])=>etq.push([L.marker([la,lo],{pane:'referencia',interactive:false,keyboard:false,icon:L.divIcon({className:'etq-ciudad',html:'<i></i>'+n,iconSize:null})}),z]));
    const capa=L.layerGroup().addTo(mapa);
    const ver=()=>{
      // Desde el zoom 6 rotulan las etiquetas de Esri, más detalladas, salvo si sus teselas fallan.
      const z=mapa.getZoom(),visibles=(z>=6&&esriEtiquetasOk)?[]:etq.filter(([,zmin])=>z>=zmin);
      capa.clearLayers();visibles.forEach(([m])=>capa.addLayer(m));
      const ocupados=[];
      visibles.map(([m])=>m.getElement()).forEach(el=>{const r=el.getBoundingClientRect();const cruza=ocupados.some(o=>r.left<o.right+4&&r.right+4>o.left&&r.top<o.bottom+2&&r.bottom+2>o.top);el.style.visibility=cruza?'hidden':'';if(!cruza)ocupados.push(r)});
    };
    refrescarEtiquetas=ver;
    mapa.on('zoomend',ver);ver();
  }).catch(()=>{vectorialCargado=false});
}
// Descargas de /clima-base/: si el archivo no existe en esta compilación, aviso claro en lugar de una página 404.
document.addEventListener('click',async ev=>{
  const a=ev.target.closest?.('a[href^="/clima-base/"][download]');
  if(!a)return;
  ev.preventDefault();
  try{
    const r=await fetch(a.getAttribute('href'));
    if(!r.ok)throw Error('This data file is not available in this build (HTTP '+r.status+').');
    const b=await r.blob(),u=URL.createObjectURL(b),tmp=document.createElement('a');
    tmp.href=u;tmp.download=a.getAttribute('download')||'';tmp.click();
    setTimeout(()=>URL.revokeObjectURL(u),30000);
  }catch(err){error(err)}
});
