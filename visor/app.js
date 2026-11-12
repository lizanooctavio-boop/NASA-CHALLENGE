let mapa,punto;
const $=id=>document.getElementById(id);
function error(e){$('error').hidden=false;$('error-texto').textContent=e.message||String(e)}
$('error-cerrar').onclick=()=>{$('error').hidden=true};
// Lee JSON sin mostrar errores crípticos («Unexpected token <») cuando el servidor o Render devuelven HTML.
async function leerJSON(r){const t=await r.text();try{return JSON.parse(t)}catch(e){throw Error(r.ok?'El servidor devolvió una respuesta no válida.':`El servidor respondió ${r.status}${r.status>=500?': servicio no disponible o reiniciándose; inténtalo en unos minutos':''}.`)}}
function limpiar(n){n.replaceChildren()}
function nodo(tag,texto,clase){const n=document.createElement(tag);if(texto!==undefined)n.textContent=texto;if(clase)n.className=clase;return n}
function tarjeta(contenedor,titulo,valor,detalle){const d=nodo('div',undefined,'tarjeta');d.append(nodo('small',titulo),nodo('strong',valor),nodo('p',detalle));contenedor.append(d)}
const decimal=(v,n=2)=>Number(v).toLocaleString('es-NI',{maximumFractionDigits:n,minimumFractionDigits:n});
async function api(url){const r=await window.FuentesMeteo.fetch(url);const d=await leerJSON(r);if(!r.ok)throw Error(d.error||'Error al leer datos');return d}
function tab(id){window.scrollTo(0,0);document.querySelectorAll('.vista').forEach(v=>v.hidden=v.id!==id);document.querySelectorAll('nav button').forEach(b=>{b.classList.toggle('activo',b.dataset.tab===id);if(b.dataset.tab===id)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});$('titulo').textContent=document.querySelector(`[data-tab="${id}"]`).textContent;soloMapa(false)}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>tab(b.dataset.tab));$('vermapa') && ($('vermapa').onclick=()=>{soloMapa(true);centrarNic(8)});
async function iniciarMapa(){if(mapa)return;if(!window.L){$('mapaestado').textContent='No se pudo cargar Leaflet desde CDN. La consulta por coordenadas sigue disponible.';return}// Un solo mundo: sin copias al alejar el zoom (zoom mínimo según el ancho de pantalla y límites fijos).
const MUNDO=[[-85,-180],[85,180]];const zoomMin=()=>Math.max(2,Math.ceil(Math.log2(Math.max(innerWidth,innerHeight*1.6)/256)));mapa=L.map('mapa',{zoomControl:false,worldCopyJump:false,maxBounds:MUNDO,maxBoundsViscosity:1,minZoom:zoomMin()}).setView([12.6,-85.1],7);addEventListener('resize',()=>mapa.setMinZoom(zoomMin()));L.control.zoom({position:'bottomright'}).addTo(mapa);const TES=(window.SICC_CONFIG||{}).teselas||{base:'https://tile.openstreetmap.org/{z}/{x}/{y}.png',base_oscurecer:true,base_atribucion:'© OpenStreetMap contributors'};if(TES.base)L.tileLayer(TES.base,{maxZoom:18,noWrap:true,bounds:MUNDO,subdomains:'abcd',className:TES.base_oscurecer?'base-osm':'base-propia',attribution:TES.base_atribucion}).addTo(mapa);else baseVectorial(TES.base_atribucion);L.rectangle([[10.7,-86.5],[12.6,-83.6]],{color:'#c27c2a',weight:2,fill:false}).addTo(mapa).bindPopup('Caja de las observaciones históricas; no cuenca oficial.');mapa.on('click',e=>{if($('consultar').disabled)return;$('lat').value=e.latlng.lat.toFixed(3);$('lon').value=L.Util.wrapNum(e.latlng.lng,[-180,180]).toFixed(3);$('consulta-punto').requestSubmit()});try{const geo=await api('/api/territorio');L.geoJSON(geo,{style:{color:'#28776f',weight:1,fillOpacity:.12}}).addTo(mapa).bindPopup('Máscara terrestre candidata WFS INETER n3=952; excluye lagos y Costa Rica.');$('mapaestado').textContent='Verde: máscara terrestre candidata INETER. Naranja: caja histórica. Ninguna se presenta como cuenca completa vigente.'}catch(e){$('mapaestado').textContent='La máscara territorial no está disponible: '+e.message}}
async function consultar(){const b=$('consultar');if(b.disabled)return;
  const lat=$('lat').valueAsNumber,lon=$('lon').valueAsNumber;
  document.dispatchEvent(new CustomEvent('sicc:punto',{detail:[lat,lon]}));
  if(mapa&&punto){mapa.removeLayer(punto);punto=null}
  b.disabled=true;b.textContent='Consultando…';$('error').hidden=true;try{const r=await api(`/api/tiempo?lat=${lat}&lon=${lon}`);const c=r.datos.current,u=r.datos.current_units;const met=$('meteo');limpiar(met);met.append(nodo('h2',`${lat.toFixed(3)}°, ${lon.toFixed(3)}° · estimación de modelo`));const tarjetas=nodo('div',undefined,'tarjetas');const intervalo=Number(c.interval)||0;const valor=v=>v===null||v===undefined?'Sin dato':decimal(v,1);tarjeta(tarjetas,'Temperatura a 2 m',`${valor(c.temperature_2m)} ${u.temperature_2m}`,'ECMWF IFS 0,25°');tarjeta(tarjetas,'Precipitación estimada',`${valor(c.precipitation)} ${u.precipitation}`,`Acumulado de 15 min previos, interpolado de modelo horario; paso ${intervalo} s`);tarjeta(tarjetas,'Viento a 10 m',`${valor(c.wind_speed_10m)} ${u.wind_speed_10m}`,`Procede de ${valor(c.wind_direction_10m)}°`);met.append(tarjetas,nodo('p',`Hora válida: ${c.time} UTC · Consulta: ${r.consulta_utc}. Hora de corrida: ${r.hora_corrida}.`),nodo('p',`Fuente: ${r.fuente}. Celda devuelta: ${r.datos.latitude}°, ${r.datos.longitude}°. Valores de modelo, sin validación local.`));if(mapa){if(punto)mapa.removeLayer(punto);const dir=Number(c.wind_direction_10m);if(c.wind_direction_10m!==null&&Number.isFinite(dir)){const icon=L.divIcon({className:'',html:`<div class="viento" style="transform:rotate(${dir+180}deg)">↑</div>`,iconSize:[32,38],iconAnchor:[16,19]});punto=L.marker([lat,lon],{icon}).addTo(mapa).bindPopup('Flecha hacia donde sopla el viento; estimación puntual.')}else punto=L.marker([lat,lon]).addTo(mapa)}}catch(e){error(e);limpiar($('meteo'));$('meteo').append(nodo('h2','Consulta no disponible'),nodo('p','No se muestran datos antiguos ni ilustrativos como actuales. '+e.message))}finally{b.disabled=false;b.textContent='Consultar punto'}}
$('consulta-punto').onsubmit=e=>{e.preventDefault();consultar()};
function centrarNic(zoom=7){if(!mapa)return;mapa.setView([12.6,-85.1],zoom,{animate:false});if(innerWidth>1000&&!document.body.classList.contains('solo-mapa'))mapa.panBy([-330,0],{animate:false})}
$('centrar').onclick=()=>centrarNic();
function soloMapa(v){const antes=document.body.classList.contains('solo-mapa');document.body.classList.toggle('solo-mapa',v);if(mapa&&antes!==v&&innerWidth>1000)mapa.panBy([v?330:-330,0],{animate:false});$('solomapa').setAttribute('aria-pressed',String(v));$('solomapa').textContent=v?'Mostrar paneles':'Solo mapa';requestAnimationFrame(ajustarAltoMapa)}
$('solomapa').onclick=()=>soloMapa(!document.body.classList.contains('solo-mapa'));
// El mapa ocupa el espacio que deja la franja de controles en pantallas compactas.
function ajustarAltoMapa(){const cont=document.getElementById('controles-mapa');if(!cont)return;const compacto=matchMedia('(max-width:700px), (max-height:500px) and (max-width:1000px)').matches;const alto=compacto?Math.ceil(cont.getBoundingClientRect().height):0;const valor=alto+'px';if(document.documentElement.style.getPropertyValue('--alto-controles-mapa')===valor)return;document.documentElement.style.setProperty('--alto-controles-mapa',valor);if(mapa)mapa.invalidateSize({animate:false})}
if(typeof ResizeObserver==='function'){const franja=document.getElementById('controles-mapa');if(franja)new ResizeObserver(ajustarAltoMapa).observe(franja)}
addEventListener('resize',ajustarAltoMapa);ajustarAltoMapa();
// Ventanas: barra de título con minimizar y cerrar
document.querySelectorAll('.vista').forEach(v=>{const titulo=document.querySelector(`[data-tab="${v.id}"]`).textContent;const cuerpo=nodo('div',undefined,'ventana-cuerpo');while(v.firstChild)cuerpo.append(v.firstChild);const barra=nodo('div',undefined,'ventana-barra');const pts=nodo('div',undefined,'ventana-botones');const cerrar=nodo('button','','punto rojo');cerrar.type='button';cerrar.title='Ocultar ventana';cerrar.setAttribute('aria-label','Ocultar ventana');cerrar.onclick=()=>soloMapa(true);const min=nodo('button','','punto ambar');min.type='button';min.title='Minimizar / restaurar';min.setAttribute('aria-label','Minimizar o restaurar ventana');min.onclick=()=>v.classList.toggle('minimizada');const max=nodo('button','','punto verde');max.type='button';max.title='Ancho completo';max.setAttribute('aria-label','Alternar ancho completo');max.onclick=()=>v.classList.toggle('ancha');pts.append(cerrar,min,max);barra.append(pts,nodo('span',titulo,'ventana-titulo'));barra.ondblclick=()=>v.classList.toggle('minimizada');v.append(barra,cuerpo);v.classList.add('ventana')});
iniciarMapa();centrarNic();

// Preferencias de cada visitante (si el navegador bloquea el almacenamiento, se usan los valores por defecto).
const pref={leer:(k,s=localStorage)=>{try{return s.getItem(k)}catch(e){return null}},guardar:(k,v,s=localStorage)=>{try{s.setItem(k,v)}catch(e){}}};
if((window.SICC_CONFIG||{}).publico){const a=$('aviso-publico');if(a)a.hidden=pref.leer('sicc952-aviso-oculto',sessionStorage)==='1'}
$('aviso-cerrar').onclick=()=>{$('aviso-publico').hidden=true;pref.guardar('sicc952-aviso-oculto','1',sessionStorage);requestAnimationFrame(()=>{ajustarAltoMapa();avisoEncima()})};

// Menú plegable: en escritorio se reduce a una barra de iconos y deja más mapa a la vista.
function plegarMenu(v,guardar){
  document.body.classList.toggle('menu-plegado',v);
  const b=$('plegar-menu');b.setAttribute('aria-expanded',String(!v));b.setAttribute('aria-label',v?'Desplegar menú':'Plegar menú');b.title=v?'Desplegar menú':'Plegar menú';
  // El nombre sigue en el texto oculto visualmente (lectores de pantalla) y en una etiqueta al enfocar o pasar el cursor.
  document.querySelectorAll('nav button').forEach(x=>{x.dataset.nombre=x.textContent.trim();x.removeAttribute('title')});
  if(guardar)pref.guardar('sicc952-menu-plegado',v?'1':'0');
}
{const p=pref.leer('sicc952-menu-plegado');plegarMenu(p===null?innerWidth<1280:p==='1',false)}
$('plegar-menu').onclick=()=>plegarMenu(!document.body.classList.contains('menu-plegado'),true);

// Columna de controles del mapa en escritorio: la leyenda se apila sobre la línea de tiempo y la barra
// de capas usa solo el alto que queda libre, sin taparse entre sí.
function medirColumnaMapa(){
  const lt=$('linea-tiempo'),ley=$('leyenda-campo'),raiz=document.documentElement.style;
  // offsetParent siempre es null en elementos fijos: se usa getClientRects para saber si se ven.
  const alto=el=>el&&!el.hidden&&el.getClientRects().length?Math.ceil(el.getBoundingClientRect().height):0;
  raiz.setProperty('--alto-lt',alto(lt)+'px');raiz.setProperty('--alto-ley',alto(ley)+'px');
  raiz.setProperty('--alto-cabecera',(alto(document.querySelector('header'))||58)+'px');
  marcarDesborde();avisoEncima();
}
// El aviso de demostración nunca queda tapado: si coincide con un control del mapa, los paneles suben por encima.
function avisoEncima(){
  const a=$('aviso-publico'),ra=a&&!a.hidden?a.getBoundingClientRect():null;
  const cruza=!!ra&&ra.height>0&&['estado-meteo-mapa','leyenda-campo','linea-tiempo','barra-capas'].some(id=>{const e=$(id);if(!e||!e.getClientRects().length)return false;const r=e.getBoundingClientRect();return r.width&&r.height&&r.left<ra.right&&r.right>ra.left&&r.top<ra.bottom&&r.bottom>ra.top});
  document.body.classList.toggle('aviso-encima',cruza);
}
{let pend=false;addEventListener('scroll',()=>{if(pend)return;pend=true;requestAnimationFrame(()=>{pend=false;avisoEncima()})},{passive:true})}
function marcarDesborde(){const c=document.querySelector('#barra-capas .ventana-cuerpo');if(!c)return;c.classList.toggle('mas-abajo',c.scrollTop+c.clientHeight<c.scrollHeight-4)}
{const c=document.querySelector('#barra-capas .ventana-cuerpo');if(c)c.addEventListener('scroll',marcarDesborde,{passive:true})}
if(typeof ResizeObserver==='function'){const ro=new ResizeObserver(medirColumnaMapa);['linea-tiempo','leyenda-campo','barra-capas','estado-meteo-mapa','aviso-publico'].forEach(id=>{const e=$(id);if(e)ro.observe(e)});ro.observe(document.querySelector('header'))}
addEventListener('resize',medirColumnaMapa);medirColumnaMapa();

// Mapa base vectorial propio (versión pública): países, lagos, fronteras y nombres desde Natural Earth.
function baseVectorial(atribucion){
  const panel=(n,z)=>{if(!mapa.getPane(n)){mapa.createPane(n);mapa.getPane(n).style.zIndex=z;mapa.getPane(n).style.pointerEvents='none'}};
  panel('base-vector',150);panel('referencia',450);
  mapa.attributionControl.addAttribution(atribucion);
  const CIUDADES=[['Managua',12.136,-86.251,5],['León',12.435,-86.879,6],['Granada',11.934,-85.956,6],['Masaya',11.974,-86.094,7],['Matagalpa',12.927,-85.917,6],['Estelí',13.092,-86.354,6],['Chinandega',12.629,-87.131,7],['Jinotega',13.091,-86.0,7],['Juigalpa',12.106,-85.364,6],['Rivas',11.437,-85.826,7],['San Carlos',11.123,-84.778,6],['Bluefields',12.014,-83.764,6],['Bilwi',14.035,-83.389,6],['Nueva Guinea',11.69,-84.456,7],['Boaco',12.472,-85.659,7],['Tegucigalpa',14.072,-87.192,5],['San José',9.928,-84.091,5],['San Salvador',13.69,-89.19,5],['Guatemala',14.634,-90.507,5],['Panamá',8.98,-79.52,5]];
  fetch('mundo.geojson').then(r=>r.json()).then(g=>{
    L.geoJSON(g,{pane:'base-vector',renderer:L.canvas({pane:'base-vector'}),interactive:false,style:f=>f.properties.tipo==='lago'?{color:'#2b4766',weight:.5,fillColor:'#0b1d33',fillOpacity:1}:{color:'#36506d',weight:.6,fillColor:'#18263a',fillOpacity:1}}).addTo(mapa);
    L.geoJSON({type:'FeatureCollection',features:g.features.filter(f=>f.properties.tipo==='pais')},{pane:'referencia',renderer:L.canvas({pane:'referencia'}),interactive:false,style:{color:'rgba(235,242,250,.55)',weight:.8,fill:false}}).addTo(mapa);
    const etq=[];
    g.features.filter(f=>f.properties.tipo==='pais'&&f.properties.lx!=null).forEach(f=>etq.push([L.marker([f.properties.ly,f.properties.lx],{pane:'referencia',interactive:false,keyboard:false,icon:L.divIcon({className:'etq-pais',html:f.properties.nombre,iconSize:null})}),Math.max(3,(f.properties.rango||5)-1)]));
    etq.sort((a,b)=>a[1]-b[1]);
    CIUDADES.forEach(([n,la,lo,z])=>etq.push([L.marker([la,lo],{pane:'referencia',interactive:false,keyboard:false,icon:L.divIcon({className:'etq-ciudad',html:'<i></i>'+n,iconSize:null})}),z]));
    const capa=L.layerGroup().addTo(mapa);
    const ver=()=>{
      const z=mapa.getZoom(), visibles=etq.filter(([,zmin])=>z>=zmin);
      capa.clearLayers();
      visibles.forEach(([m])=>capa.addLayer(m));
      const etiquetas=visibles.map(([m])=>m.getElement());
      const rects=etiquetas.map(el=>el.getBoundingClientRect());
      const ocupados=[];
      etiquetas.forEach((el,i)=>{
        const r=rects[i];
        const cruza=ocupados.some(o=>r.left<o.right+4&&r.right+4>o.left&&r.top<o.bottom+2&&r.bottom+2>o.top);
        el.style.visibility=cruza?'hidden':'';
        if(!cruza)ocupados.push(r);
      });
    };
    mapa.on('zoomend',ver);ver();
  }).catch(e=>{const n=$('mapaestado');if(n)n.textContent='Mapa base no disponible: '+e.message});
}
