// Indicadores climáticos de Nicaragua por región (backend clima_nic): tendencias con fuentes NASA
// independientes, contraste con el reanálisis MERRA-2, habilidad del pronóstico estacional y
// escenarios NEX-GDDP-CMIP6. Lee data/fenomenos_nicaragua.json al abrir la pestaña.
(function(){
const $=id=>document.getElementById(id);
const nodo=(t,txt,c)=>{const n=document.createElement(t);if(txt!==undefined)n.textContent=txt;if(c)n.className=c;return n};
const num=(v,d=2)=>Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const signo=(v,d=2)=>(v>0?'+':v<0?'−':'')+num(Math.abs(v),d);

const REGIONES=[['NIC','Nicaragua','whole country'],['pacifico','Pacific','lowlands'],['central','Central','highlands · Dry Corridor'],['caribe','Caribbean','coast']];
// Solo variables con fuente independiente del reanálisis (Astral, §4: MERRA-2 no sirve para tendencias).
const VARIABLES=[
  {id:'temperatura_gistemp',nombre:'Temperature',fuente:'NASA GISS GISTEMP v4 · station-based',unidad:'°C',dec:2,titulo:'Temperature anomaly vs. 1951–1980',contraste:r=>({clave:'temperatura_'+r,serie:'t2m_media',a:'GISTEMP v4',b:'MERRA-2 T2M',ka:'sen_gistemp_c_decada',ia:'ic_gistemp',va:'veredicto_gistemp',kb:'sen_merra2_c_decada',ib:'ic_merra2',vb:'veredicto_merra2'})},
  {id:'lluvia_anual_imerg',nombre:'Annual rainfall',fuente:'NASA GPM IMERG Final V07B · satellite',unidad:'mm',dec:0,titulo:'Annual rainfall',contraste:r=>({clave:'lluvia_'+r,serie:'lluvia_anual',a:'GPM IMERG',b:'MERRA-2',ka:'sen_imerg_mm_decada',ia:'ic_imerg',va:'veredicto_imerg',kb:'sen_power_mm_decada',ib:'ic_power',vb:'veredicto_power'})},
  {id:'lluvia_jun_nov_imerg',nombre:'Rainy season',fuente:'NASA GPM IMERG Final V07B · June–November',unidad:'mm',dec:0,titulo:'June–November rainfall'},
  {id:'ndvi',nombre:'Vegetation',fuente:'NASA MODIS MOD13Q1 NDVI · ORNL DAAC sites',unidad:'NDVI',dec:3,titulo:'Vegetation greenness (NDVI)'}
];
const VEREDICTO={tendencia_detectada:['Trend detected','aumento'],evidencia_insuficiente:['Not enough evidence of a trend','insuficiente'],metodos_discrepan:['Methods disagree','insuficiente'],datos_insuficientes:['Not enough data','insuficiente']};
const ESCENARIOS=[['lluvia_anual','Annual rainfall','%'],['lluvia_jun_nov','Rainy season (Jun–Nov)','%'],['lluvia_jul_ago','Midsummer drought (Jul–Aug)','%'],['t2m_media','Mean temperature','°C']];

let D=null,carga=null,sel={region:'NIC',variable:'temperatura_gistemp'},capaMapa=null;
const graficas={};
function crear(id,config){graficas[id]?.destroy();graficas[id]=new Chart($(id),config);return graficas[id]}
const region=id=>D.regiones.find(r=>r.id===id);
const disponibles=r=>VARIABLES.filter(v=>region(r)?.variables[v.id]);

function cargar(){
  carga??=fetch('data/fenomenos_nicaragua.json')
    .then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
    .then(d=>{D=d;construir();const c=$('ind-csv'),m=$('ind-ver-mapa');if(c)c.disabled=false;if(m)m.disabled=false;return d})
    .catch(err=>{
      carga=null;
      const v=$('ind-veredicto');
      if(v)v.textContent='Could not load regional climate series. Check your connection and try opening this tab again.';
      const c=$('ind-csv'),m=$('ind-ver-mapa');
      if(c)c.disabled=true;
      if(m)m.disabled=true;
      throw err;
    });
  return carga;
}

// ---------------------------------------------------------------- selectores
function botones(cont,items,activo,alElegir){
  cont.replaceChildren();
  items.forEach(([id,nombre,rol])=>{const b=nodo('button');b.type='button';b.setAttribute('role','radio');b.dataset.id=id;b.setAttribute('aria-checked',String(id===activo));
    b.append(nodo('span',nombre));if(rol)b.append(nodo('span',rol,'rol'));b.onclick=()=>alElegir(id);cont.append(b)});
  cont.onkeydown=ev=>{const paso={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[ev.key];if(!paso)return;ev.preventDefault();
    const ids=items.map(i=>i[0]),i=ids.indexOf(cont.querySelector('[aria-checked="true"]')?.dataset.id);const n=ids[(i+paso+ids.length)%ids.length];alElegir(n);cont.querySelector(`[data-id="${n}"]`)?.focus()};
}
function construir(){
  botones($('ind-regiones'),REGIONES,sel.region,id=>{sel.region=id;if(!region(id).variables[sel.variable])sel.variable=disponibles(id)[0].id;pintar()});
  const s=$('esc-region');REGIONES.forEach(([id,n])=>s.add(new Option(n,id)));s.onchange=escenarios;
  estacional();escenarios();pintar();
}
function pintar(){
  botones($('ind-regiones'),REGIONES,sel.region,id=>{sel.region=id;if(!region(id).variables[sel.variable])sel.variable=disponibles(id)[0].id;pintar()});
  botones($('ind-variables'),disponibles(sel.region).map(v=>[v.id,v.nombre]),sel.variable,id=>{sel.variable=id;pintar()});
  resultado();contraste();mapaRegiones();
}

// ---------------------------------------------------------------- resultado y serie
function resultado(){
  const v=VARIABLES.find(x=>x.id===sel.variable),x=region(sel.region).variables[v.id],t=x.tendencia,sen=t.theil_sen;
  const [texto,icono]=VEREDICTO[t.veredicto]||[t.veredicto,'insuficiente'];
  const forma=t.veredicto==='tendencia_detectada'?(sen.por_decada>=0?'aumento':'disminucion'):icono;
  const nombreRegion=REGIONES.find(r=>r[0]===sel.region)[1],u=v.unidad==='NDVI'?'NDVI':v.unidad;
  const c=$('ind-veredicto');c.replaceChildren();c.className='veredicto '+forma;
  const ic=nodo('div',undefined,'icono');ic.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true">${{aumento:'<path d="M4 15l6-6 4 4 6-7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',disminucion:'<path d="M4 7l6 6 4-4 6 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',insuficiente:'<path d="M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>'}[forma]}</svg>`;
  const cab=nodo('div');cab.append(nodo('p',texto,'estado'),nodo('p',`${v.titulo} · ${nombreRegion} · ${t.periodo[0]}–${t.periodo[1]}`,'sub'));
  c.append(ic,cab);
  const tj=nodo('div',undefined,'tarjetas');tj.style.gridColumn='1/-1';
  const tar=(a,b,d)=>{const e=nodo('div',undefined,'tarjeta');e.append(nodo('small',a),nodo('strong',b));if(d)e.append(nodo('p',d));tj.append(e)};
  tar('Change per decade',`${signo(sen.por_decada,v.dec+1)} ${u}`,`95% CI ${signo(sen.ic_por_decada[0],v.dec+1)} to ${signo(sen.ic_por_decada[1],v.dec+1)} · Theil–Sen`);
  const mk=t.mann_kendall_modificado;if(mk)tar('Significance',mk.p_valor<0.001?'p < 0.001':`p = ${num(mk.p_valor,3)}`,'Mann–Kendall, corrected for autocorrelation');
  const ce=t.controlada_por_indices;if(ce)tar('Without El Niño',`${signo(ce.por_decada,v.dec+1)} ${u}`,`95% CI ${signo(ce.ic_por_decada[0],v.dec+1)} to ${signo(ce.ic_por_decada[1],v.dec+1)} · Niño 3.4 removed`);
  c.append(tj,nodo('p',v.fuente,'detalle'));
  // Serie con la recta de Theil–Sen
  // Ordenada de Sen: mediana de y − b·x, la misma que usa scipy.stats.theilslopes.
  const anios=x.anios,vals=x.valores,b=sen.por_decada/10,res=vals.map((y,i)=>y-b*anios[i]).sort((p,q)=>p-q);
  const a0=res.length%2?res[(res.length-1)/2]:(res[res.length/2-1]+res[res.length/2])/2;
  const recta=anios.map(a=>a0+b*a);
  $('ind-serie-titulo').textContent=`${v.titulo} · ${nombreRegion}`;
  crear('ind-serie',{data:{labels:anios,datasets:[
    {type:v.unidad==='mm'?'bar':'line',label:`${v.nombre} (${u})`,data:vals,borderColor:'#6fd8ff',backgroundColor:v.unidad==='mm'?'rgba(79,143,232,.7)':'rgba(111,216,255,.15)',pointRadius:v.unidad==='mm'?0:2,borderWidth:v.unidad==='mm'?0:2},
    {type:'line',label:'Theil–Sen trend',data:recta,borderColor:'#f6c76b',borderDash:[6,4],pointRadius:0,borderWidth:2}]},
    options:{interaction:{mode:'index',intersect:false},scales:{x:{ticks:{maxTicksLimit:12}},y:{title:{display:true,text:u}}}}});
}

// ---------------------------------------------------------------- contraste con MERRA-2
function contraste(){
  const v=VARIABLES.find(x=>x.id===sel.variable),art=$('ind-contraste');
  const cfg=v.contraste?.(sel.region),c=cfg&&D.comparaciones_independientes[cfg.clave];
  art.hidden=!c;if(!c)return;
  const otra=region(sel.region).variables[cfg.serie],propia=region(sel.region).variables[v.id];
  const [i0,i1]=c.periodo,ini=Math.max(i0,propia.anios[0]),fin=Math.min(i1,propia.anios.at(-1));
  const anios=propia.anios.filter(a=>a>=ini&&a<=fin);
  const anomalia=(x)=>{const par=anios.map(a=>x.valores[x.anios.indexOf(a)]);const m=par.reduce((s,y)=>s+y,0)/par.length;return par.map(y=>y-m)};
  const u=v.unidad,d=v.dec+1;
  $('ind-contraste-sub').textContent=`${cfg.a} vs. ${cfg.b} reanalysis · ${ini}–${fin} · anomalies from each product's mean`;
  crear('ind-contraste-graf',{type:'line',data:{labels:anios,datasets:[
    {label:cfg.a,data:anomalia(propia),borderColor:'#6fd8ff',pointRadius:0,borderWidth:2.4,tension:.2},
    {label:cfg.b,data:anomalia(otra),borderColor:'#ff7b6b',pointRadius:0,borderWidth:1.6,borderDash:[4,3],tension:.2}]},
    options:{interaction:{mode:'index',intersect:false},scales:{x:{ticks:{maxTicksLimit:12}},y:{title:{display:true,text:`Anomaly (${u})`}}}}});
  const tj=$('ind-contraste-tarjetas');tj.replaceChildren();
  [[cfg.a,c[cfg.ka],c[cfg.ia],c[cfg.va]],[cfg.b,c[cfg.kb],c[cfg.ib],c[cfg.vb]]].forEach(([n,p,ic,ver],i)=>{
    const e=nodo('div',undefined,'tarjeta '+(i?'calido':''));e.append(nodo('small',n),nodo('strong',`${signo(p,d)} ${u}/decade`),nodo('p',`95% CI ${signo(ic[0],d)} to ${signo(ic[1],d)}`),nodo('p',(VEREDICTO[ver]||[ver])[0]));tj.append(e)});
  if(c.r_anual!==undefined){const e=nodo('div',undefined,'tarjeta');e.append(nodo('small','Year-to-year agreement'),nodo('strong',`r = ${num(c.r_anual,2)}`),nodo('p',`Mean ${num(c.media_imerg_mm,0)} vs. ${num(c.media_power_mm,0)} mm`));tj.append(e)}
}

// ---------------------------------------------------------------- pronóstico estacional (IMERG)
function estacional(){
  const p=D.modelo_estacional.principales.filter(x=>x.region==='NIC (IMERG)');
  const solo=p.find(x=>x.modelo==='nino34_mam'),tna=p.find(x=>x.modelo==='nino34_tna_mam');
  const tj=$('ind-estacional');tj.replaceChildren();if(!solo||!tna)return;
  const pct=v=>`${signo(v*100,0)}%`;
  [['El Niño 3.4 alone',solo,'frio'],['El Niño 3.4 + Tropical North Atlantic',tna,'']].forEach(([n,x,c])=>{
    const e=nodo('div',undefined,'tarjeta '+c);e.append(nodo('small',n),nodo('strong',pct(x.bloque_1.msess)),nodo('p',`skill vs. climatology · p = ${num(x.p_permutacion_msess,3)}`),nodo('p',`${Math.round(x.bloque_1.aciertos_tercil*100)}% of terciles right (33% by chance)`));tj.append(e)});
  $('ind-estacional-sub').textContent=`Predicting June–November rainfall from March–May sea temperatures · NASA IMERG, Nicaragua, ${tna.periodo[0]}–${tna.periodo[1]} · each year left out of the fit`;
}

// ---------------------------------------------------------------- escenarios NEX-GDDP-CMIP6
function escenarios(){
  const r=$('esc-region').value||'NIC',E=D.escenarios_cmip6[r];if(!E)return;
  const t=$('esc-tabla');t.replaceChildren();
  const cab=nodo('tr');['Variable','Recent (1995–2014)','SSP2-4.5','SSP5-8.5','Models drier / wetter'].forEach(h=>cab.append(nodo('th',h)));t.append(cab);
  ESCENARIOS.forEach(([k,n,u])=>{const e=E[k];if(!e)return;const fila=nodo('tr');fila.append(nodo('td',n));
    fila.append(nodo('td',e.unidad==='mm'?`${num(e.observado_historico,0)} mm`:`${num(e.observado_historico,1)} °C`));
    ['ssp245','ssp585'].forEach(s=>{const c=e.escenarios[s].cambio,dd=u==='%'?0:1;const td=nodo('td');td.append(nodo('strong',`${signo(c.mediana,dd)} ${u}`),nodo('span',` ${signo(c.minimo,dd)} to ${signo(c.maximo,dd)}`,'tenue'));fila.append(td)});
    const c=e.escenarios.ssp585.cambio;fila.append(nodo('td',u==='%'?`${c.modelos_disminucion} / ${c.modelos_aumento} of ${c.n_modelos}`:`${c.n_modelos} of ${c.n_modelos} warmer`));t.append(fila)});
  const e0=Object.values(E)[0];
  $('esc-sub').textContent=`NASA NEX-GDDP-CMIP6 · ${e0.escenarios.ssp245.cambio.n_modelos} models · ${e0.periodo_futuro[0]}–${e0.periodo_futuro[1]} average vs. ${e0.periodo_historico[0]}–${e0.periodo_historico[1]} · median and model range`;
}

// ---------------------------------------------------------------- regiones en el mapa 2D
let geo=null;
function mapaRegiones(){
  if(typeof mapa==='undefined'||!mapa||!window.L)return;
  const activa=!$('indicadores').hidden;
  if(!activa){if(capaMapa)mapa.removeLayer(capaMapa);return}
  const dibujar=()=>{if(capaMapa)mapa.removeLayer(capaMapa);
    capaMapa=L.geoJSON({type:'FeatureCollection',features:geo.features.filter(f=>['pacifico','central','caribe'].includes(f.properties.id))},{interactive:false,
      style:f=>{const on=sel.region==='NIC'||f.properties.id===sel.region;return{color:on?'#6fd8ff':'rgba(235,242,250,.45)',weight:on?2:1,fillColor:'#6fd8ff',fillOpacity:on?.18:0}}}).addTo(mapa)};
  if(geo)dibujar();else fetch('data/regiones_nicaragua.geojson').then(r=>r.json()).then(g=>{geo=g;if(!$('indicadores').hidden)dibujar()}).catch(()=>{});
}
$('ind-ver-mapa').onclick=()=>window.SICC_vista.irA(12.8,-85.2,7);

// ---------------------------------------------------------------- descargas
function bajar(nombre,texto,tipo){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([texto],{type:tipo}));a.download=nombre;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),30000)}
$('ind-csv').onclick=async()=>{try{await cargar();const v=VARIABLES.find(x=>x.id===sel.variable),r=region(sel.region),x=r&&v&&r.variables[v.id];if(!x)return;
  bajar(`${v.id}_${sel.region}.csv`,'\ufeff'+[`# Source: ${v.fuente}`,`# Area: ${REGIONES.find(r=>r[0]===sel.region)[1]}, Nicaragua`,`year,${v.id}_${v.unidad==='NDVI'?'ndvi':v.unidad==='°C'?'c':'mm'}`,...x.anios.map((a,i)=>`${a},${x.valores[i]}`)].join('\r\n')+'\r\n','text/csv;charset=utf-8')}catch(err){typeof error==='function'&&error(err)}};

document.addEventListener('sicc:pestana',e=>{
  if(e.detail==='indicadores'||e.detail==='escenarios')cargar().then(()=>{mapaRegiones();setTimeout(()=>Object.values(graficas).forEach(g=>g.resize()),30)}).catch(err=>typeof error==='function'&&error(err));
  else mapaRegiones();
});
window.SICC_indicadores={estado:()=>({cargado:!!D,sel:{...sel},graficas:Object.keys(graficas)})};
})();
