// Tendencia de la precipitación anual en la caja de estudio (reto Earth System Trend Detective).
// Reutiliza Leaflet, Chart.js y la exportación CSV de la vista «Clima observado». Si algo falla, el resto sigue.
(function(){
const $=id=>document.getElementById(id);
const raiz=$('tendencia');
if(!raiz)return;
const num=(v,d=1)=>v===null||v===undefined?'—':Number(v).toLocaleString('es',{minimumFractionDigits:d,maximumFractionDigits:d});
const ic=(a,d=1)=>a?`${num(a[0],d)} a ${num(a[1],d)}`:'—';
const ETIQUETA={imerg:'NASA GPM IMERG Final V07B',chirps:'CHIRPS v2.0 · mismo período (contraste)',chirps_1981_2025:'CHIRPS v2.0 · registro largo 1981–2025'};
const VEREDICTO={tendencia_detectada:'Tendencia detectada',evidencia_insuficiente:'Evidencia insuficiente',metodos_discrepan:'No concluyente: los métodos discrepan'};
let datos=null,grafica=null,mapaMini=null,cargado=false;

function celda(tr,texto){const td=document.createElement('td');td.textContent=texto;tr.append(td)}
function resumen(items){
  const dl=$('tend-resumen');dl.replaceChildren();
  for(const [t,v] of items){const d=document.createElement('div'),a=document.createElement('dt'),b=document.createElement('dd');a.textContent=t;b.textContent=v;d.append(a,b);dl.append(d)}
}
function dibujarMapa(){
  if(!window.L||!datos)return;
  const [s,n]=datos.caja.lat,[o,e]=datos.caja.lon;
  if(!mapaMini){
    mapaMini=L.map('tend-mapa',{zoomControl:false,attributionControl:false,dragging:false,scrollWheelZoom:false,doubleClickZoom:false,boxZoom:false,keyboard:false});
    fetch('mundo.geojson').then(r=>r.json()).then(g=>L.geoJSON(g,{style:{color:'#4b6178',weight:1,fillColor:'#1c2f44',fillOpacity:1}}).addTo(mapaMini)).catch(()=>{});
    L.rectangle([[s,o],[n,e]],{color:'#c27c2a',weight:2,fillOpacity:.15}).addTo(mapaMini).bindTooltip('Caja de estudio de SICC');
  }
  mapaMini.invalidateSize();
  mapaMini.fitBounds([[s-3,o-4],[n+3,e+4]]);
}
function pintar(){
  const clave=$('tend-producto').value,p=datos.productos[clave],estado=$('tend-estado');
  $('tend-interpretacion').textContent='';
  if(p.estado!=='ok'){
    grafica?.destroy();grafica=null;resumen([]);$('tend-filas').replaceChildren();
    estado.textContent=p.motivo||'Producto no disponible.';
    return;
  }
  const a=p.analisis,excl=Object.entries(p.anios_excluidos);
  estado.textContent=`${p.nombre} · resolución ${p.resolucion} · ponderación: ${p.ponderacion}. Años excluidos por mes faltante o inválido: ${excl.length?excl.map(([y,m])=>`${y} (${m})`).join('; '):'ninguno'}.`;
  if(window.Chart){
    grafica?.destroy();
    // Eje con todos los años del período: un año excluido queda como hueco visible, no se omite en silencio.
    const mm=new Map(p.anuales.map(f=>[f.anio,f.mm])),r=a.recta,anios=[];
    if(p.anuales.length)for(let y=p.anuales[0].anio;y<=p.anuales[p.anuales.length-1].anio;y++)anios.push(y);
    grafica=new Chart($('graf-tendencia'),{data:{labels:anios,datasets:[
      {type:'bar',label:'Lluvia anual (mm)',data:anios.map(y=>mm.has(y)?mm.get(y):null),backgroundColor:'rgba(79,143,232,.55)'},
      ...(a.estado==='ok'?[{type:'line',label:'Recta de tendencia',data:anios.map(y=>r.intercepto+r.pendiente_anual*y),borderColor:'#f6c76b',pointRadius:0,borderWidth:2}]:[])]},
      options:{interaction:{mode:'index',intersect:false},scales:{y:{title:{display:true,text:'mm/año'}}},
        plugins:{subtitle:{display:true,text:`${p.nombre} · ${anios[0]}–${anios[anios.length-1]} · solo años con doce meses válidos`}}}});
  }
  if(a.estado!=='ok'){
    const sinInferencia=a.estado==='inferencia_no_disponible';
    resumen([['Producto',ETIQUETA[clave]],['Estado',sinInferencia?'Inferencia no disponible (años faltantes)':'Datos insuficientes'],
      ...(sinInferencia?[['Pendiente descriptiva',`${num(a.mm_por_decada)} mm por década, sin intervalo`],['Años faltantes',(a.anios_faltantes||[]).join(', ')]]:[])]);$('tend-interpretacion').textContent=a.mensaje;$('tend-filas').replaceChildren();return}
  resumen([
    ['Variable','Precipitación anual (mm/año)'],['Región','Caja de estudio de SICC'],['Período',`${a.periodo[0]}–${a.periodo[1]} (${a.anios} años)`],
    ['Cambio por década',`${num(a.mm_por_decada)} mm`],['IC 95 %',`${ic(a.ic_mm_por_decada)} mm`],['Relativo',`${num(a.pct_por_decada)} % (${ic(a.ic_pct_por_decada)})`],
    ['Evidencia',VEREDICTO[a.veredicto]],['Valor p (principal)',num(a.p_valor_principal,3)]]);
  $('tend-interpretacion').textContent=a.interpretacion;
  const f=$('tend-filas');f.replaceChildren();
  const fila=(...c)=>{const tr=document.createElement('tr');c.forEach(x=>celda(tr,x));f.append(tr)};
  fila(`Principal: MCO, ${num(a.n_efectivo)} años efectivos (r₁ = ${num(a.r1_residuos,2)})${a.anios_faltantes?.length?` · rezagos en años calendario (faltan ${a.anios_faltantes.length})`:''}`,num(a.mm_por_decada),ic(a.ic_mm_por_decada),a.anios);
  fila(`HAC Newey–West (rezago ${a.hac.rezago})`,'—',ic(a.hac.ic_mm_por_decada),a.anios);
  fila('Theil–Sen',num(a.theil_sen.mm_por_decada),ic(a.theil_sen.ic_mm_por_decada),a.anios);
  fila(`Mann–Kendall: tau ${num(a.mann_kendall.tau,2)}, p ${num(a.mann_kendall.p_valor,3)}`,'—','—',a.anios);
  for(const s of a.sensibilidad.slice(1))fila(`Sensibilidad: ${s.ventana}`,s.mm_por_decada===undefined?'—':num(s.mm_por_decada),s.ic_mm_por_decada?ic(s.ic_mm_por_decada):'—',s.anios);
  fila('Omitiendo un año (mínimo a máximo)','—',ic(a.omitir_un_anio_mm_por_decada),a.anios-1);
}

// ---------------------------------------------------------------- comparación por regiones (¿cambia la conclusión según dónde miramos?)
const COLOR={oeste:'#6fd8ff',este:'#f6c76b',caja:'#9db0c6',dif:'#b493ff'};
const NOMBRE={oeste:'Oeste',este:'Este',caja:'Caja completa (caso base)',dif:'Oeste − Este'};
let graficasReg={},mapaReg=null,capasReg={},vistaReg='comparar';
const VISTAS=['comparar','oeste','este','caja'];
const hex2rgba=(h,a)=>{const n=parseInt(h.slice(1),16);return `rgba(${n>>16},${(n>>8)&255},${n&255},${a})`};
function resumenEn(id,items){
  const dl=$(id);if(!dl)return;dl.replaceChildren();
  for(const [t,v] of items){const d=document.createElement('div'),a=document.createElement('dt'),b=document.createElement('dd');a.textContent=t;b.textContent=v;d.append(a,b);dl.append(d)}
}
function graficaReg(id,config){
  const c=$(id);if(!c||!window.Chart)return null;
  graficasReg[id]?.destroy();graficasReg[id]=new Chart(c,config);return graficasReg[id];
}
function zonaReg(clave,z,maxY){
  const a=z.analisis,c=z.caja;
  resumenEn('reg-res-'+clave,[
    ['Región',`${NOMBRE[clave]} · ${num(c.lat[0])}–${num(c.lat[1])}° N, ${num(-c.lon[0])}–${num(-c.lon[1])}° O`],
    ['Celdas y meses',`${z.celdas??'—'} celdas · ${z.meses_validos??z.analisis?.anios*12} meses válidos`],
    ['Período',`${a.periodo[0]}–${a.periodo[1]} (${a.anios} años completos)`],
    ['Cambio por década',`${num(a.mm_por_decada)} mm`],['IC 95 %',`${ic(a.ic_mm_por_decada)} mm`],
    ['Evidencia',VEREDICTO[a.veredicto]],['Valor p (principal)',num(a.p_valor_principal,3)]]);
  $('reg-int-'+clave).textContent=a.interpretacion;
  const anios=z.anuales.map(f=>f.anio),r=a.recta;
  graficaReg('graf-reg-'+clave,{data:{labels:anios,datasets:[
    {type:'bar',label:'Lluvia anual (mm)',data:z.anuales.map(f=>f.mm),backgroundColor:hex2rgba(COLOR[clave],.55)},
    {type:'line',label:'Recta de tendencia',data:anios.map(y=>r.intercepto+r.pendiente_anual*y),borderColor:'#fff',pointRadius:0,borderWidth:2}]},
    options:{interaction:{mode:'index',intersect:false},scales:{y:{min:0,max:maxY,title:{display:true,text:'mm/año (misma escala en todas las regiones)'}}},
      plugins:{subtitle:{display:true,text:`${NOMBRE[clave]} · IMERG V07B · ${anios[0]}–${anios[anios.length-1]}`}}}});
}
const marcasReg={id:'estimacionesReg',afterDatasetsDraw(ch){
  const est=ch.$estimaciones;if(!est)return;
  const {ctx,scales:{x,y}}=ch;ctx.save();ctx.fillStyle='#fff';ctx.strokeStyle='#0d1b2a';ctx.lineWidth=1.5;
  est.forEach((v,i)=>{const px=x.getPixelForValue(v),py=y.getPixelForValue(i);ctx.beginPath();ctx.moveTo(px,py-7);ctx.lineTo(px+7,py);ctx.lineTo(px,py+7);ctx.lineTo(px-7,py);ctx.closePath();ctx.fill();ctx.stroke()});
  ctx.restore()}};
function intervalosReg(g){
  const filas=[['oeste',g.zonas.oeste.analisis],['este',g.zonas.este.analisis],['caja',g.zonas.caja.analisis],['dif',g.diferencia.analisis]].filter(([,a])=>a.estado==='ok');
  const lim=Math.max(100,Math.ceil(Math.max(...filas.flatMap(([,a])=>a.ic_mm_por_decada.map(Math.abs)))*1.05/100)*100);
  const sel=vistaReg==='comparar'?['oeste','este']:[vistaReg];
  const ch=graficaReg('graf-reg-ic',{type:'bar',data:{labels:filas.map(([k])=>k==='caja'?'Caja completa':NOMBRE[k]),datasets:[{label:'IC 95 % (mm/década)',
      data:filas.map(([,a])=>a.ic_mm_por_decada),backgroundColor:filas.map(([k])=>hex2rgba(COLOR[k],k==='dif'||sel.includes(k)||vistaReg==='comparar'?.8:.35)),barThickness:16,borderSkipped:false}]},
    options:{indexAxis:'y',scales:{x:{min:-lim,max:lim,title:{display:true,text:'mm por década · escala común · línea blanca = 0'},
        grid:{color:c=>c.tick.value===0?'#ffffff':'rgba(255,255,255,.09)',lineWidth:c=>c.tick.value===0?2:1}}},
      plugins:{legend:{display:false},subtitle:{display:true,text:'Rombo = estimación. Un intervalo que cruza cero no detecta cambio con este método.'},
        tooltip:{callbacks:{label:c=>{const a=filas[c.dataIndex][1];return `IC 95 %: ${ic(a.ic_mm_por_decada)} mm/década · estimación ${num(a.mm_por_decada)}`}}}}},plugins:[marcasReg]});
  if(ch){ch.$estimaciones=filas.map(([,a])=>a.mm_por_decada);ch.update('none')}
}
function diferenciaReg(g){
  const d=g.diferencia.analisis;
  if(d.estado!=='ok'){resumenEn('reg-res-dif',[['Estado','Diferencia no estimada']]);$('reg-int-dif').textContent=g.diferencia.interpretacion;$('reg-lectura').textContent=g.lectura;return}
  resumenEn('reg-res-dif',[['Serie','Oeste − Este (años completos en ambas)'],['Años',String(d.anios)],['Cambio de la diferencia',`${num(d.mm_por_decada)} mm/década`],
    ['IC 95 % (principal)',`${ic(d.ic_mm_por_decada)} mm`],['IC 95 % (HAC)',`${ic(d.hac.ic_mm_por_decada)} mm`],['IC 95 % (Theil–Sen)',`${ic(d.theil_sen.ic_mm_por_decada)} mm`],
    ['Evidencia',VEREDICTO[d.veredicto]],['Valor p (principal)',num(d.p_valor_principal,3)]]);
  $('reg-int-dif').textContent=g.diferencia.interpretacion;
  $('reg-lectura').textContent=g.lectura;
}
function tablaReg(g){
  const f=$('reg-filas');if(!f)return;f.replaceChildren();
  const fila=(...c)=>{const tr=document.createElement('tr');c.forEach(x=>celda(tr,x));f.append(tr)};
  for(const [k,a] of [['oeste',g.zonas.oeste.analisis],['este',g.zonas.este.analisis],['caja',g.zonas.caja.analisis],['dif',g.diferencia.analisis]]){
    if(a.estado!=='ok'){fila(NOMBRE[k],'—','—','—','—');continue}
    fila(NOMBRE[k],`${num(a.mm_por_decada)} (${ic(a.ic_mm_por_decada)})`,ic(a.hac.ic_mm_por_decada),`${num(a.theil_sen.mm_por_decada)} (${ic(a.theil_sen.ic_mm_por_decada)})`,num(a.p_valor_principal,3));
  }
}
function mapaRegiones(g){
  if(!window.L||!$('reg-mapa'))return;
  const def=Object.fromEntries(g.definiciones.map(d=>[d.id,d]));
  if(!mapaReg){
    mapaReg=L.map('reg-mapa',{zoomControl:false,attributionControl:false,dragging:false,scrollWheelZoom:false,doubleClickZoom:false,boxZoom:false,keyboard:false});
    fetch('mundo.geojson').then(r=>r.json()).then(j=>L.geoJSON(j,{style:{color:'#4b6178',weight:1,fillColor:'#1c2f44',fillOpacity:1}}).addTo(mapaReg).bringToBack()).catch(()=>{});
    for(const k of ['oeste','este']){
      const d=def[k];
      capasReg[k]=L.rectangle([[d.lat[0],d.lon[0]],[d.lat[1],d.lon[1]]],{color:COLOR[k],weight:2,fillOpacity:.25}).addTo(mapaReg)
        .bindTooltip(NOMBRE[k],{permanent:true,direction:'center',className:'tend-etiqueta'}).bindPopup(`${NOMBRE[k]}: ${d.celdas??'—'} celdas de 0,1°`);
    }
    const c=def.caja;L.rectangle([[c.lat[0],c.lon[0]],[c.lat[1],c.lon[1]]],{color:COLOR.caja,weight:1.5,dashArray:'5 4',fill:false}).addTo(mapaReg);
  }
  const sel=vistaReg==='comparar'||vistaReg==='caja'?['oeste','este']:[vistaReg];
  for(const k of ['oeste','este'])capasReg[k].setStyle({fillOpacity:sel.includes(k)?.3:.05,weight:sel.includes(k)?2.5:1});
  const c=def.caja;mapaReg.invalidateSize();mapaReg.fitBounds([[c.lat[0]-.5,c.lon[0]-.7],[c.lat[1]+.5,c.lon[1]+.7]]);
}
function pintarRegiones(){
  const sec=$('regiones');if(!sec||!datos||!datos.regiones)return;
  const g=datos.regiones,est=$('reg-estado');
  const csvs=[$('reg-csv-anual'),$('reg-csv-mensual')];
  if(g.estado!=='ok'){
    sec.querySelectorAll('[data-reg-contenido]').forEach(n=>{n.hidden=true});
    est.textContent=g.motivo||'La comparación por regiones no está disponible en este servidor.';
    csvs.forEach(b=>b&&b.setAttribute('aria-disabled','true'));return;
  }
  sec.querySelectorAll('[data-reg-contenido]').forEach(n=>{n.hidden=false});
  csvs.forEach(b=>b&&b.removeAttribute('aria-disabled'));
  est.textContent=`${g.producto} · ${g.ventana[0]}–${g.ventana[1]} · misma variable y método en todas las vistas. Regiones fijadas antes de calcular pendientes.`;
  const av=$('reg-aviso');if(av)av.textContent=`${g.aviso} Criterio y coordenadas: ${g.criterio}.`;
  const mostrar=vistaReg==='comparar'?['oeste','este']:[vistaReg];
  for(const c of ['oeste','este','caja'])$('reg-zona-'+c).hidden=!mostrar.includes(c);
  const cols=sec.querySelector('.reg-columnas');if(cols&&cols.classList)cols.classList.toggle('una',mostrar.length===1);
  const maxY=Math.ceil(Math.max(...['oeste','este','caja'].flatMap(c=>g.zonas[c].anuales.map(f=>f.mm)))/500)*500;
  for(const c of mostrar)zonaReg(c,g.zonas[c],maxY);
  intervalosReg(g);diferenciaReg(g);tablaReg(g);mapaRegiones(g);
}
function elegirVista(v,actualizarEnlace=true){
  if(!VISTAS.includes(v))v='comparar';
  vistaReg=v;const s=$('reg-vista');if(s)s.value=v;
  pintarRegiones();
  if(actualizarEnlace&&window.history?.replaceState)try{history.replaceState(null,'','#reto='+v)}catch(e){}
}
function iniciarRegiones(){
  const s=$('reg-vista');if(!s||s.dataset.listo)return;
  s.dataset.listo='1';s.addEventListener('change',()=>elegirVista(s.value));
}

// Una sola carga compartida: el clic en la pestaña y el enlace directo esperan la misma promesa. Si falla, se puede reintentar.
let promesaCarga=null;
function cargar(){
  if(!promesaCarga)promesaCarga=cargarDatos().then(()=>{if(!cargado)promesaCarga=null});
  return promesaCarga;
}
async function cargarDatos(){
  if(cargado)return;cargado=true;
  const sel=$('tend-producto'),estado=$('tend-estado');
  try{
    const r=await window.FuentesMeteo.fetch('/api/tendencia_precipitacion');
    datos=await r.json();
    if(!r.ok)throw Error(datos.error||'sin respuesta');
  }catch(e){
    cargado=false;estado.textContent='La tendencia no está disponible en este servidor: '+(e.message||e);
    $('tend-csv-anual').setAttribute('aria-disabled','true');return;
  }
  sel.replaceChildren();
  for(const k of ['imerg','chirps','chirps_1981_2025']){
    const o=document.createElement('option');o.value=k;o.textContent=ETIQUETA[k]+(datos.productos[k].estado!=='ok'?' (no disponible)':'');sel.append(o);
  }
  sel.value=datos.productos.imerg.estado==='ok'?'imerg':'chirps';
  $('tend-metodo').textContent=datos.metodo+' '+datos.caja.aviso;
  const cal=datos.calendario_agricola,t=cal.temporadas;
  $('tend-calendario').textContent=`Calendario agrícola: primera (mayo–agosto) recibe en promedio ${num(t.primera.mm_medio,0)} mm (${num(t.primera.pct_del_anual,0)} % del año) y postrera (septiembre–noviembre) ${num(t.postrera.mm_medio,0)} mm (${num(t.postrera.pct_del_anual,0)} %), según ${cal.producto==='imerg'?'IMERG':'CHIRPS v2'}. ${cal.lectura}`;
  const mensual=$('tend-csv-mensual');
  if(datos.productos.imerg.estado!=='ok')mensual.setAttribute('aria-disabled','true');else mensual.removeAttribute('aria-disabled');
  sel.addEventListener('change',pintar);
  pintar();dibujarMapa();
  iniciarRegiones();pintarRegiones();
}
document.querySelector('nav [data-tab="graficas"]')?.addEventListener('click',()=>{cargar().then(()=>setTimeout(()=>{dibujarMapa();if(mapaReg&&datos?.regiones?.estado==='ok')mapaRegiones(datos.regiones)},60))});
// Enlace directo al reto: #reto abre «Clima observado» en la comparación; #reto=oeste|este|caja|comparar elige la vista.
// El diseño y las gráficas terminan de asentarse después de la carga: se reintenta unas veces, salvo que la persona ya se haya desplazado.
function irARegiones(){
  let usuario=false;const parar=()=>{usuario=true};
  if(typeof addEventListener==='function')['wheel','touchstart','keydown','mousedown'].forEach(e=>addEventListener(e,parar,{once:true,passive:true}));
  for(const ms of [150,700,1600])setTimeout(()=>{
    const t=$('regiones');if(usuario||!t||!t.scrollIntoView)return;
    const arriba=t.getBoundingClientRect?t.getBoundingClientRect().top:0;
    if(Math.abs(arriba)>40)t.scrollIntoView({block:'start'});
  },ms);
}
function abrirReto(){
  const hash=typeof location!=='undefined'&&location.hash||'',m=/^#reto(?:=([a-z]+))?$/.exec(hash);if(!m)return;
  document.querySelector('nav [data-tab="graficas"]')?.click();
  cargar().then(()=>{if(!datos)return;elegirVista(m[1]||'comparar',false);irARegiones()});
}
if(typeof addEventListener==='function')addEventListener('hashchange',abrirReto);
abrirReto();
window.SICC_tendencia={estado:()=>({cargado,producto:$('tend-producto').value,datos,vistaRegiones:vistaReg})};
})();
