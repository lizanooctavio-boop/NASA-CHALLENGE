// Pestañas «Investigate», «Learn» y «Sources»: recorrido guiado qué/dónde con los recursos del reto.
// Lee data/recursos_integrados.json (backend/clima_nic/recursos.py) al abrir cualquiera de las tres pestañas.
// Solo muestra categorías, lugares y recursos con datos; las series de registro corto no llevan tendencia.
(function(){
const $=id=>document.getElementById(id);
const nodo=(t,txt,c)=>{const n=document.createElement(t);if(txt!==undefined)n.textContent=txt;if(c)n.className=c;return n};
const num=(v,d=2)=>Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const signo=(v,d=2)=>(v>0?'+':v<0?'−':'')+num(Math.abs(v),d);
const DECIMALES={mm:0,'°C':2,NDVI:3,m:2,'mg/m³':2,days:1,'mm/day':2,'million km²':2,storms:1,months:1,Gt:0,cm:1,pH:3,'Ω':2,fraction:2,'°C-weeks':1,'km²':0};
const dec=u=>DECIMALES[u]??2;

const VEREDICTO={
  tendencia_detectada:['Trend detected','aprender-metodos'],
  evidencia_insuficiente:['Not enough evidence of a trend','aprender-no-significativo'],
  metodos_discrepan:['Methods disagree','aprender-metodos'],
  datos_insuficientes:['Not enough data for a trend test','aprender-registro-corto']};
const ICONOS={aumento:'<path d="M4 15l6-6 4 4 6-7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
  disminucion:'<path d="M4 7l6 6 4-4 6 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
  insuficiente:'<path d="M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>'};

let D=null,carga=null,sel={categoria:null,lugar:null,investigacion:null},demo=null,demoOrigen=null;
const graficas={};
function crear(id,config){graficas[id]?.destroy();graficas[id]=new Chart($(id),config);return graficas[id]}
const inv=id=>D.investigaciones.find(i=>i.id===id);
const lugar=id=>D.lugares.find(l=>l.id===id);
const contraste=id=>D.contrastes.find(c=>c.id===id);
const deCategoria=c=>D.investigaciones.filter(i=>i.categoria===c);

function cargar(){
  carga??=fetch('data/recursos_integrados.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(d=>{D=d;construir();return d});
  return carga;
}

// ---------------------------------------------------------------- selectores
function botones(cont,items,activo,alElegir){
  const teniaFoco=cont.contains(document.activeElement);
  cont.replaceChildren();
  const hayActivo=items.some(([id])=>id===activo);
  items.forEach(([id,nombre,rol],idx)=>{const b=nodo('button');b.type='button';b.setAttribute('role','radio');b.dataset.id=id;
    const on=id===activo;b.setAttribute('aria-checked',String(on));b.tabIndex=on||(!hayActivo&&idx===0)?0:-1;
    b.append(nodo('span',nombre));if(rol)b.append(nodo('span',rol,'rol'));b.onclick=()=>alElegir(id);cont.append(b)});
  if(teniaFoco)(cont.querySelector('[aria-checked="true"]')||cont.querySelector('button'))?.focus({preventScroll:true});
  cont.onkeydown=ev=>{const paso={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[ev.key];if(!paso)return;ev.preventDefault();
    const ids=items.map(i=>i[0]);if(!ids.length)return;
    const i=Math.max(0,ids.indexOf(cont.querySelector('[aria-checked="true"]')?.dataset.id));const n=ids[(i+paso+ids.length)%ids.length];alElegir(n);cont.querySelector(`[data-id="${n}"]`)?.focus()};
}
function construir(){
  const primera=D.categorias.find(c=>c.con_datos);
  elegir({categoria:primera.id});
  demostraciones();fuentes();
}
// Fija la selección y completa lo que falte con la primera opción disponible.
function elegir(cambio){
  Object.assign(sel,cambio);
  const candidatas=deCategoria(sel.categoria);
  if(cambio.categoria&&!cambio.lugar)sel.lugar=null;
  if(!candidatas.some(i=>i.lugar===sel.lugar))sel.lugar=candidatas[0].lugar;
  const aqui=candidatas.filter(i=>i.lugar===sel.lugar);
  if(!aqui.some(i=>i.id===sel.investigacion))sel.investigacion=aqui[0].id;
  pintar();
}
function pintar(){
  const cats=D.categorias.filter(c=>c.con_datos);
  botones($('inv-categorias'),cats.map(c=>[c.id,c.nombre_en]),sel.categoria,id=>elegir({categoria:id}));
  const c=D.categorias.find(x=>x.id===sel.categoria);
  $('inv-pregunta').textContent=c.pregunta_en;
  $('inv-descripcion').textContent=c.descripcion_en||'';$('inv-descripcion').hidden=!c.descripcion_en;
  const lugares=[...new Set(deCategoria(sel.categoria).map(i=>i.lugar))].map(lugar).filter(Boolean);
  botones($('inv-lugares'),lugares.map(l=>[l.id,l.nombre_en,l.pais]),sel.lugar,id=>elegir({lugar:id}));
  const variantes=deCategoria(sel.categoria).filter(i=>i.lugar===sel.lugar);
  $('inv-variables').hidden=variantes.length<2;
  botones($('inv-variables'),variantes.map(i=>[i.id,i.titulo_en]),sel.investigacion,id=>elegir({investigacion:id}));
  resultado();contrastes();
}

// ---------------------------------------------------------------- resultado y serie
function resultado(){
  const x=inv(sel.investigacion),l=lugar(x.lugar),t=x.tendencia,u=x.unidad,d=dec(u)+1;
  const c=$('inv-veredicto');c.replaceChildren();
  const corto=x.papel==='demostracion_registro_corto';
  const ok=t&&t.veredicto!=='datos_insuficientes';
  const forma=ok&&t.veredicto==='tendencia_detectada'?(t.sen.por_decada>=0?'aumento':'disminucion'):'insuficiente';
  c.className='veredicto '+forma;
  const ic=nodo('div',undefined,'icono');ic.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true">${ICONOS[forma]}</svg>`;
  const [desde,hasta]=x.periodo||[x.tiempos[0],x.tiempos.at(-1)];
  const periodo=desde===hasta?String(desde):`${desde}–${hasta}`;
  const [texto,ancla]=corto?['Record too short for a trend test','aprender-registro-corto']:VEREDICTO[t.veredicto]||[t.veredicto,'aprender-tendencia'];
  const cab=nodo('div');cab.append(nodo('p',texto,'estado'),nodo('p',`${x.titulo_en} · ${l.nombre_en} · ${periodo}`,'sub'));
  c.append(ic,cab);
  const tj=nodo('div',undefined,'tarjetas');tj.style.gridColumn='1/-1';
  const tar=(a,b,dd)=>{const e=nodo('div',undefined,'tarjeta');e.append(nodo('small',a),nodo('strong',b));if(dd)e.append(nodo('p',dd));tj.append(e)};
  if(ok){
    tar('How much per decade',`${signo(t.sen.por_decada,d)} ${u}`,`95% CI ${signo(t.sen.ic[0],d)} to ${signo(t.sen.ic[1],d)} · Theil–Sen`);
    tar('How sure',t.mann_kendall_p<0.001?'p < 0.001':`p = ${num(t.mann_kendall_p,3)}`,'Mann–Kendall, corrected for autocorrelation');
    tar('Least squares',`${signo(t.mco.por_decada,d)} ${u}`,`95% CI ${signo(t.mco.ic[0],d)} to ${signo(t.mco.ic[1],d)}`);
  }else if(corto){
    const vals=x.valores.filter(v=>v!==null);
    const escenas=x.frecuencia==='escena';
    const unidad=escenas?'scene':'month';
    tar('Observations',`${vals.length} ${unidad}${vals.length===1?'':'s'}`,periodo.replace('–',' to '));
    if(vals.length===1)tar('Value',`${num(vals[0],d)} ${u}`,String(desde));
    else tar('Range',`${num(Math.min(...vals),d)}–${num(Math.max(...vals),d)} ${u}`,escenas?'lowest to highest scene':'lowest to highest monthly mean');
  }
  if(x.validacion?.estado==='NO_VALIDADA')tar('Validation','Not validated',x.validacion.detalle_en);
  c.append(tj);
  const pie=nodo('p',undefined,'detalle');pie.append(nodo('span',x.definicion_en+' '));
  const a=nodo('a','What does this mean?');a.href='#'+ancla;a.onclick=ev=>{ev.preventDefault();aprender(ancla)};pie.append(a);
  c.append(pie);
  (x.notas||[]).forEach(n=>c.append(nodo('p',n,'detalle nota')));
  c.append(nodo('p',x.fuente.producto,'detalle fuente'));
  serie(x,t,ok);
}
// Las series anuales con años sin dato se dibujan con hueco: el eje es de categorías y, sin rellenar, juntaría 2016 y 2019.
function conHuecos(x){
  const t=x.tiempos;
  if(x.frecuencia!=='anual'||!t.every(Number.isInteger)||t.at(-1)-t[0]+1===t.length)return {tiempos:t,valores:x.valores};
  const por=new Map(t.map((a,i)=>[a,x.valores[i]])),tiempos=[];
  for(let a=t[0];a<=t.at(-1);a++)tiempos.push(a);
  return {tiempos,valores:tiempos.map(a=>por.has(a)?por.get(a):null)};
}
function serie(x,t,ok){
  const u=x.unidad,barras=['mm','storms','months','Gt'].includes(u)&&!x.id.startsWith('nivel_mar_');
  const eje=conHuecos(x);
  $('inv-serie-titulo').textContent=`${x.titulo_en} · ${lugar(x.lugar).nombre_en}`;
  const ds=[{type:barras?'bar':'line',label:`${x.titulo_en} (${u})`,data:eje.valores,borderColor:'#6fd8ff',backgroundColor:barras?'rgba(79,143,232,.7)':'rgba(111,216,255,.15)',pointRadius:barras?0:2,borderWidth:barras?0:2,spanGaps:false}];
  if(ok){
    // Ordenada de Sen: mediana de y − b·x, la misma que usa scipy.stats.theilslopes.
    const b=t.sen.por_decada/10,res=x.tiempos.map((a,i)=>x.valores[i]===null?null:x.valores[i]-b*a).filter(v=>v!==null).sort((p,q)=>p-q);
    const a0=res.length%2?res[(res.length-1)/2]:(res[res.length/2-1]+res[res.length/2])/2;
    ds.push({type:'line',label:'Theil–Sen trend',data:eje.tiempos.map(a=>a0+b*a),borderColor:'#f6c76b',borderDash:[6,4],pointRadius:0,borderWidth:2});
  }
  const [desde,hasta]=x.periodo||[x.tiempos[0],x.tiempos.at(-1)];
  const valsNum=eje.valores.filter(v=>v!==null&&v!==undefined&&Number.isFinite(Number(v)));
  const rTxt=valsNum.length?`, range ${num(Math.min(...valsNum),dec(u))} to ${num(Math.max(...valsNum),dec(u))} ${u}`:'';
  const tTxt=ok?`, Theil–Sen trend ${signo(t.sen.por_decada,dec(u)+1)} ${u} per decade`:'';
  $('inv-serie').setAttribute('aria-label',`${x.titulo_en} in ${lugar(x.lugar).nombre_en}, ${desde} to ${hasta}${rTxt}${tTxt}`);
  crear('inv-serie',{data:{labels:eje.tiempos,datasets:ds},options:{locale:x.validacion?'en-US':undefined,interaction:{mode:'index',intersect:false},scales:{x:{ticks:{maxTicksLimit:12}},y:{title:{display:true,text:u}}}}});
}

// ---------------------------------------------------------------- segundas opiniones
function contrastes(){
  const x=inv(sel.investigacion),art=$('inv-contrastes'),lista=$('inv-contrastes-lista');
  const cs=x.contrastes.map(contraste).filter(Boolean);
  art.hidden=!cs.length;lista.replaceChildren();Object.keys(graficas).filter(k=>k.startsWith('inv-c-')).forEach(k=>{graficas[k].destroy();delete graficas[k]});
  const u=x.unidad,d=dec(u)+1;
  cs.forEach((c,k)=>{
    const bloque=nodo('div',undefined,'contraste');bloque.dataset.id=c.id;lista.append(bloque);
    bloque.append(nodo('h3',c.tipo==='metodo'?`Same data, another method: ${c.externa.nombre_en}`:c.externa.nombre_en));
    const tj=nodo('div',undefined,'tarjetas');
    const tar=(a,b,dd,cl)=>{const e=nodo('div',undefined,'tarjeta '+(cl||''));e.append(nodo('small',a),nodo('strong',b));if(dd)e.append(nodo('p',dd));tj.append(e)};
    if(c.tipo==='metodo'){
      tar('Their slope',`${signo(c.externa.por_decada,d)} ${u}/decade`,c.externa.p_valor!=null?`p = ${c.externa.p_valor<0.001?'< 0.001':num(c.externa.p_valor,3)} · ${c.externa.significativa?'significant':'not significant'} at 5%`:'');
      tar('Our verdict',(VEREDICTO[x.tendencia.veredicto]||[x.tendencia.veredicto])[0],`Theil–Sen ${signo(x.tendencia.sen.por_decada,d)} ${u}/decade`,'calido');
    }else{
      if(c.externa.por_decada!=null)tar(c.externa.nombre_en,`${signo(c.externa.por_decada,d)} ${u}/decade`,(VEREDICTO[c.externa.veredicto]||[c.externa.veredicto||''])[0]);
      if(c.nuestra.por_decada!=null)tar(c.nuestra.nombre_en,`${signo(c.nuestra.por_decada,d)} ${u}/decade`,(VEREDICTO[c.nuestra.veredicto]||[c.nuestra.veredicto||''])[0],'calido');
      if(c.r!=null)tar('Agreement',`r = ${num(c.r,2)}`,c.diferencia_media!=null?`mean difference ${signo(c.diferencia_media,dec(c.unidad||u))} ${c.unidad||u}`:'');
    }
    bloque.append(tj);
    const etiquetas=c.externa.anios||c.externa.tiempos,ve=c.externa.valores,vn=c.nuestra?.valores;
    if(etiquetas?.length&&ve?.length&&vn?.length){
      const lienzo=nodo('canvas');lienzo.id='inv-c-'+k;lienzo.setAttribute('role','img');
      lienzo.setAttribute('aria-label',`${c.externa.nombre_en} compared with ${c.nuestra.nombre_en}, ${etiquetas[0]} to ${etiquetas.at(-1)}${c.r!=null?`, correlation r = ${num(c.r,2)}`:''}`);
      const g=nodo('div',undefined,'graf baja');g.append(lienzo);bloque.append(g);
      const ejes=c.nuestra.anios||c.nuestra.tiempos,mapa=new Map(ejes.map((a,i)=>[a,vn[i]]));
      crear(lienzo.id,{type:'line',data:{labels:etiquetas,datasets:[
        {label:c.nuestra.nombre_en,data:etiquetas.map(a=>mapa.get(a)??null),borderColor:'#6fd8ff',pointRadius:0,borderWidth:2.2,tension:.2},
        {label:c.externa.nombre_en,data:ve,borderColor:'#ff7b6b',pointRadius:0,borderWidth:1.6,borderDash:[4,3],tension:.2}]},
        options:{interaction:{mode:'index',intersect:false},scales:{x:{ticks:{maxTicksLimit:10}},y:{title:{display:true,text:c.unidad||u}}}}});
    }
    if(c.frase_en)bloque.append(nodo('p',c.frase_en,'frase'));
  });
}

// ---------------------------------------------------------------- recorridos guiados
function demostraciones(){
  const cont=$('inv-demos');cont.replaceChildren();
  D.demostraciones.forEach(dm=>{const b=nodo('button',dm.titulo_en);b.type='button';b.dataset.demo=dm.id;b.onclick=()=>iniciarDemo(dm.id);cont.append(b)});
}
function iniciarDemo(id){
  demoOrigen=document.activeElement?.closest('#inv-demos')?document.activeElement:document.querySelector(`#inv-demos [data-demo="${id}"]`);
  demo={dm:D.demostraciones.find(d=>d.id===id),paso:0};pasoDemo('inicio');
}
function pasoDemo(focoDestino){
  const panel=$('inv-demo-panel');
  if(!demo){
    const volver=panel.contains(document.activeElement);
    panel.hidden=true;
    if(volver)(demoOrigen?.isConnected?demoOrigen:document.querySelector('#inv-demos button'))?.focus({preventScroll:true});
    return;
  }
  const {dm,paso}=demo,p=dm.pasos[paso],x=inv(p.investigacion);
  sel.categoria=x.categoria;sel.lugar=x.lugar;sel.investigacion=x.id;pintar();
  panel.hidden=false;panel.tabIndex=-1;panel.setAttribute('aria-label',`${dm.titulo_en} · step ${paso+1} of ${dm.pasos.length}`);
  panel.onkeydown=e=>{if(e.key==='Escape'&&demo){e.preventDefault();demo=null;pasoDemo()}};
  panel.replaceChildren();
  panel.append(nodo('p',`${dm.titulo_en} · step ${paso+1} of ${dm.pasos.length}`,'demo-titulo'),nodo('p',p.texto_en,'demo-texto'));
  if(p.ver==='comparacion'&&dm.comparacion){
    const tj=nodo('div',undefined,'tarjetas');
    Object.entries(dm.comparacion).forEach(([iid,t],k)=>{const y=inv(iid),e=nodo('div',undefined,'tarjeta '+(k?'frio':'calido'));
      e.append(nodo('small',`${lugar(y.lugar).nombre_en} · ${dm.ventana[0]}–${dm.ventana[1]}`),nodo('strong',`${signo(t.sen.por_decada,2)} °C/decade`),nodo('p',`95% CI ${signo(t.sen.ic[0],2)} to ${signo(t.sen.ic[1],2)}`),nodo('p',(VEREDICTO[t.veredicto]||[t.veredicto])[0]));tj.append(e)});
    panel.append(tj);
  }
  const ctl=nodo('div',undefined,'controles');
  const boton=(txt,fn,des)=>{const b=nodo('button',txt);b.type='button';b.disabled=!!des;b.dataset.accion=txt.toLowerCase();b.onclick=fn;ctl.append(b)};
  boton('Previous',()=>{demo.paso--;pasoDemo('previous')},paso===0);
  if(paso<dm.pasos.length-1)boton('Next',()=>{demo.paso++;pasoDemo('next')});else boton('Finish',()=>{demo=null;pasoDemo()});
  panel.append(ctl);
  const destino={veredicto:'inv-veredicto',contrastes:'inv-contrastes'}[p.ver];
  if(p.ver==='aprender'){const b=nodo('button','Open the explanation');b.type='button';b.onclick=()=>aprender(p.ancla||'aprender-no-significativo');ctl.append(b)}
  (destino?$(destino):panel).scrollIntoView({block:'nearest',behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});
  if(focoDestino==='inicio')panel.focus({preventScroll:true});
  else if(focoDestino){
    const elegido=ctl.querySelector(`[data-accion="${focoDestino}"]:not(:disabled)`)||ctl.querySelector('button:not(:disabled)');
    elegido?.focus({preventScroll:true});
  }
}

// ---------------------------------------------------------------- Learn y Sources
function aprender(ancla){tab('aprender');const e=$(ancla);if(e){e.scrollIntoView({block:'start'});e.classList.add('resaltado');setTimeout(()=>e.classList.remove('resaltado'),1600)}}
function fuentes(){
  const lista=$('fuentes-recursos');lista.replaceChildren();
  D.recursos.filter(r=>r.estado==='en_uso').forEach(r=>{const li=nodo('li');li.dataset.recurso=r.id;const a=nodo('a',r.nombre);a.href=r.url;a.target='_blank';a.rel='noopener';
    li.append(a,nodo('span',` · ${r.organizacion}`,'tenue'),nodo('p',r.uso_en));lista.append(li)});
  const otros=new Map();
  D.investigaciones.forEach(i=>otros.set(i.fuente.producto,i.fuente.url||''));
  D.contrastes.forEach(c=>{if(c.tipo==='fuente')otros.set(c.externa.nombre_en,c.externa.url||'')});
  const l2=$('fuentes-datos');l2.replaceChildren();
  [...otros].sort((a,b)=>a[0].localeCompare(b[0])).forEach(([n,u])=>{const li=nodo('li');if(/^https?:/.test(u)&&!u.includes('{')){const a=nodo('a',n);a.href=u;a.target='_blank';a.rel='noopener';li.append(a)}else li.textContent=n;l2.append(li)});
}

// ---------------------------------------------------------------- mapa y descarga
// En el móvil los paneles tapan el mapa entero: se ocultan para que se vea el lugar marcado.
$('inv-mapa').onclick=async()=>{const l=lugar(inv(sel.investigacion).lugar);
  await window.SICC_vista.irA(l.centro[0],l.centro[1],l.zoom);window.SICC_vista.marcar?.(l.centro[0],l.centro[1],l.nombre_en);
  if(matchMedia('(max-width:700px),(max-height:500px) and (max-width:1000px)').matches)window.SICC_vista.soloMapa?.(true)};
function bajar(nombre,texto){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([texto],{type:'text/csv;charset=utf-8'}));a.download=nombre;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),30000)}
$('inv-csv').onclick=async()=>{await cargar();const x=inv(sel.investigacion),col=x.frecuencia==='mensual'?'month':x.frecuencia==='escena'?'date':'year';
  bajar(`${x.id}.csv`,'﻿'+[`# Source: ${x.fuente.producto}`,`# Place: ${lugar(x.lugar).nombre_en}`,`${col},value_${x.unidad.replace(/[^\w°³]+/g,'_')}`,...x.tiempos.map((a,i)=>`${a},${x.valores[i]??''}`)].join('\r\n')+'\r\n')};

document.addEventListener('sicc:pestana',e=>{
  if(['investigar','aprender','fuentes'].includes(e.detail))cargar().then(()=>setTimeout(()=>Object.values(graficas).forEach(g=>g.resize()),30)).catch(err=>typeof error==='function'&&error(err));
});
window.SICC_investigar={estado:()=>({cargado:!!D,sel:{...sel},demo:demo&&{id:demo.dm.id,paso:demo.paso}}),elegir:c=>{elegir(c)},demo:iniciarDemo};
})();
