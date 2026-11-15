// Recorrido guiado con Terra, la detective de tendencias: un guion fijo (sin IA ni claves) que resalta
// los elementos reales de la app. Accesible: teclado, Escape para salir, foco atrapado y aria-live.
// La primera visita muestra una invitación; «ya visto» se guarda en localStorage dentro de try/catch.
(function(){
'use strict';
const $=id=>document.getElementById(id);
const nodo=(t,txt,c)=>{const n=document.createElement(t);if(txt!==undefined)n.textContent=txt;if(c)n.className=c;return n};
const CLAVE='etd-tour-visto';
const visto={leer:()=>{try{return localStorage.getItem(CLAVE)==='1'}catch(e){return false}},guardar:()=>{try{localStorage.setItem(CLAVE,'1')}catch(e){}}};
const reducido=()=>matchMedia('(prefers-reduced-motion:reduce)').matches;
const irAPestana=id=>{if(typeof window.tab==='function')window.tab(id);else document.querySelector(`nav button[data-tab="${id}"]`)?.click()};
const visible=el=>!!el&&el.getClientRects().length>0&&getComputedStyle(el).visibility!=='hidden';

// Retrato de Terra: dibujo propio en SVG (no generado por IA, sin marcas de ninguna agencia).
const TERRA='<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false"><circle cx="28" cy="30" r="20" fill="#2f7fd0"/>'+
  '<path d="M14 24c4-6 10-6 12-2s-2 6 2 9-2 8-6 7-6-5-9-6-2-5 1-8zM33 13c5 0 10 3 12 8-4 0-6 3-9 1s-6-1-6-4 1-5 3-5zM34 38c3-2 7-1 9 2-1 4-5 7-9 7-2-3-2-7 0-9z" fill="#5fc28f"/>'+
  '<circle cx="22" cy="29" r="2.4" fill="#0d1726"/><circle cx="32" cy="29" r="2.4" fill="#0d1726"/><path d="M22 36c3 3 7 3 10 0" stroke="#0d1726" stroke-width="2" fill="none" stroke-linecap="round"/>'+
  '<path d="M9 17c6-8 32-8 38 0l-3 2c-7-5-25-5-32 0z" fill="#c98f4f"/><path d="M15 15c4-9 22-9 26 0z" fill="#a8733b"/>'+
  '<circle cx="47" cy="45" r="8" fill="rgba(160,225,255,.35)" stroke="#f6c76b" stroke-width="3"/><path d="M52.5 50.5l7 7" stroke="#f6c76b" stroke-width="4" stroke-linecap="round"/></svg>';

// Guion: cada paso nombra el elemento real que se resalta. «antes» prepara la vista si hace falta.
const PASOS=[
  {titulo:"Hi, I'm Terra",texto:"I'm your trend detective. In about a minute I'll show you where everything is. Use Next and Back, or press Escape to leave at any time."},
  {destino:'#menu-principal',titulo:'The menu',texto:'Each button opens a section. Weather is the live 48-hour forecast; the other sections look at climate records that span many years.'},
  {destino:'.interruptor',titulo:'Globe or map',texto:'Switch between the 3D globe and the flat map. Click any point on either one to get a 48-hour forecast for that place.'},
  {destino:'#barra-capas',titulo:'Layers',texto:'Choose what the globe shows: temperature, rain, wind and more. The timeline plays the forecast hour by hour.'},
  {destino:'#inv-categorias',respaldo:'nav button[data-tab="investigar"]',antes:()=>irAPestana('investigar'),titulo:'Investigate',texto:'Start here. Pick a topic, then a place, and the app tests whether it has changed over the years.'},
  {destino:'#inv-veredicto',respaldo:'#investigar',antes:()=>irAPestana('investigar'),titulo:'The verdict',texto:'Each series gets a verdict: Trend detected, Not enough evidence of a trend, or Methods disagree. “Not enough evidence” never means “no change”.'},
  {destino:'#inv-demos',respaldo:'#investigar',antes:()=>irAPestana('investigar'),titulo:'Guided examples',texto:'Short stories that walk you through real questions step by step, such as “Has Nicaragua’s rainfall changed?”.'},
  {destino:'nav button[data-tab="hidrologia"]',titulo:'Watersheds',texto:'Follow water across borders: watershed boundaries for Nicaragua and the world, with their original codes and dated station readings.'},
  {destino:'nav button[data-tab="aprender"]',titulo:'Learn',texto:'Plain-language explanations of trends, confidence intervals, p-values and why methods sometimes disagree.'},
  {destino:'nav button[data-tab="fuentes"]',titulo:'Sources',texto:'Every dataset and challenge resource behind the app, with links to the originals.'},
  {destino:'nav button[data-tab="ayuda"]',titulo:'Help',texto:'Search 100 questions in English or Spanish whenever you are stuck. You can restart this tour from Help.'}];

let capa=null,foco=null,tarjeta=null,paso=0,previo=null,marco=0;
// ---------------------------------------------------------------- recorrido
function iniciar(desde=0){
  cerrarInvitacion(false);
  if(!capa)construir();
  previo=document.activeElement instanceof HTMLElement?document.activeElement:null;
  capa.hidden=false;document.body.classList.add('tour-activo');
  ir(desde);
}
function construir(){
  capa=nodo('div',undefined,'tour-capa');capa.hidden=true;
  foco=nodo('div',undefined,'tour-foco');foco.setAttribute('aria-hidden','true');
  tarjeta=nodo('div',undefined,'tour-tarjeta');tarjeta.setAttribute('role','dialog');tarjeta.setAttribute('aria-modal','true');
  tarjeta.setAttribute('aria-labelledby','tour-titulo');tarjeta.setAttribute('aria-describedby','tour-texto');tarjeta.tabIndex=-1;
  capa.append(foco,tarjeta);document.body.append(capa);
  capa.addEventListener('keydown',teclas);
  // Un clic en el fondo oscuro no cierra (evita salir sin querer); para salir: Skip tour o Escape.
  capa.addEventListener('mousedown',e=>{if(e.target===capa||e.target===foco)e.preventDefault()});
  addEventListener('resize',recolocar);addEventListener('scroll',recolocar,true);
}
function objetivo(p){
  if(!p.destino)return null;
  let el=document.querySelector(p.destino);
  if(!visible(el)&&p.respaldo)el=document.querySelector(p.respaldo);
  // En el móvil los botones del menú están en una franja con desplazamiento: si el botón no se ve, se resalta la franja.
  if(!visible(el)&&p.destino.startsWith('nav '))el=$('menu-principal');
  return visible(el)?el:null;
}
async function ir(n){
  paso=Math.max(0,Math.min(PASOS.length-1,n));
  const p=PASOS[paso];
  try{p.antes?.()}catch(e){}
  pintarTarjeta(p);
  const el=objetivo(p);
  if(el){el.scrollIntoView({block:'nearest',inline:'center',behavior:'auto'});}
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  recolocar();
  tarjeta.querySelector('[data-accion="siguiente"]')?.focus({preventScroll:true});
}
function pintarTarjeta(p){
  const ultimo=paso===PASOS.length-1;
  tarjeta.replaceChildren();
  const cab=nodo('div',undefined,'tour-cabeza');const av=nodo('div',undefined,'tour-avatar');av.innerHTML=TERRA;
  const quien=nodo('p',undefined,'tour-quien');quien.append(nodo('strong','Terra'),nodo('span',', your trend detective'));
  cab.append(av,quien);
  const contador=nodo('p',`Step ${paso+1} of ${PASOS.length}`,'tour-contador');
  const h=nodo('h2',p.titulo);h.id='tour-titulo';
  // El texto del paso se anuncia al cambiar (aria-live), sin repetir los botones.
  const vivo=nodo('div',undefined,'tour-vivo');vivo.setAttribute('aria-live','polite');vivo.setAttribute('aria-atomic','true');
  const t=nodo('p',p.texto);t.id='tour-texto';vivo.append(nodo('span',`${p.titulo}. `,'tour-oculto'),t);
  const puntos=nodo('div',undefined,'tour-puntos');puntos.setAttribute('aria-hidden','true');
  PASOS.forEach((_,i)=>puntos.append(nodo('i',undefined,i===paso?'activo':'')));
  const ctl=nodo('div',undefined,'tour-controles');
  const boton=(txt,accion,clase,fn,etq)=>{const b=nodo('button',txt,clase||'');b.type='button';b.dataset.accion=accion;b.onclick=fn;if(etq)b.setAttribute('aria-label',etq);return b};
  const saltar=boton('Skip tour','saltar','tour-saltar',()=>cerrar());
  const atras=boton('Back','atras','',()=>ir(paso-1));atras.disabled=paso===0;
  const grupo=nodo('div',undefined,'tour-grupo');
  if(ultimo)grupo.append(atras,boton('Open Help','ayuda','',()=>{cerrar(true);window.SICC_ayuda?.abrir()}),boton('Finish','siguiente','tour-principal',()=>cerrar()));
  else grupo.append(atras,boton('Next','siguiente','tour-principal',()=>ir(paso+1)));
  ctl.append(saltar,grupo);
  tarjeta.append(cab,contador,h,vivo,puntos,ctl);
}
// Coloca el marco de luz sobre el elemento y la tarjeta donde quepa (debajo, encima, a un lado o centrada).
function recolocar(){
  if(!capa||capa.hidden)return;
  cancelAnimationFrame(marco);
  marco=requestAnimationFrame(()=>{
    const el=objetivo(PASOS[paso]),W=innerWidth,H=innerHeight,m=12;
    const tw=Math.min(380,W-2*m);tarjeta.style.width=tw+'px';
    const th=tarjeta.offsetHeight;
    if(!el){foco.hidden=true;capa.classList.add('tour-sin-foco');tarjeta.style.left=Math.round((W-tw)/2)+'px';tarjeta.style.top=Math.round(Math.max(m,(H-th)/2))+'px';return}
    capa.classList.remove('tour-sin-foco');foco.hidden=false;
    const r=el.getBoundingClientRect(),pad=6;
    const f={l:Math.max(4,r.left-pad),t:Math.max(4,r.top-pad),r:Math.min(W-4,r.right+pad),b:Math.min(H-4,r.bottom+pad)};
    Object.assign(foco.style,{left:f.l+'px',top:f.t+'px',width:Math.max(0,f.r-f.l)+'px',height:Math.max(0,f.b-f.t)+'px'});
    const centroX=Math.min(Math.max(m,(f.l+f.r)/2-tw/2),W-tw-m),centroY=Math.min(Math.max(m,(f.t+f.b)/2-th/2),H-th-m);
    const opciones=[
      [f.b+m+th<=H-m,centroX,f.b+m],[f.t-m-th>=m,centroX,f.t-m-th],
      [f.r+m+tw<=W-m,f.r+m,centroY],[f.l-m-tw>=m,f.l-m-tw,centroY]];
    let [,x,y]=opciones.find(o=>o[0])||[0,centroX,(f.t+f.b)/2<H/2?H-th-m:m];
    tarjeta.style.left=Math.round(x)+'px';tarjeta.style.top=Math.round(Math.max(m,y))+'px';
  });
}
function enfocables(){return [...tarjeta.querySelectorAll('button:not(:disabled),[href],[tabindex]:not([tabindex="-1"])')].filter(visible)}
function teclas(e){
  if(e.key==='Escape'){e.preventDefault();e.stopPropagation();cerrar();return}
  if(e.key==='Tab'){const l=enfocables();if(!l.length){e.preventDefault();return}
    const i=l.indexOf(document.activeElement);
    if(e.shiftKey&&(i<=0)){e.preventDefault();l.at(-1).focus()}
    else if(!e.shiftKey&&(i===-1||i===l.length-1)){e.preventDefault();l[0].focus()}
    return}
  if(e.target.tagName==='BUTTON'&&(e.key==='ArrowRight'||e.key==='ArrowLeft')){
    e.preventDefault();if(e.key==='ArrowRight'&&paso<PASOS.length-1)ir(paso+1);else if(e.key==='ArrowLeft'&&paso>0)ir(paso-1)}
}
// Si el foco escapa (p. ej. con el ratón fuera de la tarjeta), vuelve a la tarjeta.
document.addEventListener('focusin',e=>{if(capa&&!capa.hidden&&!tarjeta.contains(e.target))tarjeta.focus({preventScroll:true})});
function cerrar(sinDevolverFoco){
  if(!capa||capa.hidden)return;
  capa.hidden=true;document.body.classList.remove('tour-activo');visto.guardar();
  if(!sinDevolverFoco&&previo?.isConnected)previo.focus({preventScroll:true});
}

// ---------------------------------------------------------------- invitación de la primera visita
let invitacion=null;
function invitar(){
  if(invitacion||(capa&&!capa.hidden))return;
  invitacion=nodo('div',undefined,'tour-invitacion');invitacion.setAttribute('role','dialog');invitacion.setAttribute('aria-modal','false');
  invitacion.setAttribute('aria-labelledby','tour-inv-texto');
  const av=nodo('div',undefined,'tour-avatar');av.innerHTML=TERRA;
  const cuerpo=nodo('div');
  const t=nodo('p',"Hi, I'm Terra. Want a 1-minute tour of the app?");t.id='tour-inv-texto';t.setAttribute('aria-live','polite');
  const ctl=nodo('div',undefined,'tour-controles');
  const empezar=nodo('button','Start','tour-principal');empezar.type='button';empezar.onclick=()=>{visto.guardar();iniciar()};
  const ahoraNo=nodo('button','Not now');ahoraNo.type='button';ahoraNo.onclick=()=>cerrarInvitacion(true);
  ctl.append(empezar,ahoraNo);cuerpo.append(t,ctl);invitacion.append(av,cuerpo);
  invitacion.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();cerrarInvitacion(true)}});
  colocarInvitacion();['sicc:pestana','sicc:paneles'].forEach(ev=>document.addEventListener(ev,colocarInvitacion));
  // Solo se lleva el foco a la invitación si la persona aún no ha empezado a usar la app.
  if(document.activeElement===document.body||!document.activeElement)empezar.focus({preventScroll:true});
}
// Se coloca como aviso al principio del panel abierto, para no tapar ningún control. Si los paneles
// están ocultos, queda flotando abajo, centrada.
function colocarInvitacion(){
  if(!invitacion)return;
  const vista=[...document.querySelectorAll('.vista')].find(v=>!v.hidden&&visible(v));
  const dentro=vista&&(vista.querySelector('.ventana-cuerpo')||vista);
  if(dentro&&!document.body.classList.contains('solo-mapa')){
    invitacion.classList.add('tour-en-flujo');if(invitacion.parentNode!==dentro)dentro.prepend(invitacion);
  }else{invitacion.classList.remove('tour-en-flujo');if(invitacion.parentNode!==document.body)document.body.append(invitacion)}
}
function cerrarInvitacion(guardar){
  if(!invitacion)return;
  ['sicc:pestana','sicc:paneles'].forEach(ev=>document.removeEventListener(ev,colocarInvitacion));
  const tenia=invitacion.contains(document.activeElement);
  invitacion.remove();invitacion=null;if(guardar)visto.guardar();
  if(tenia&&guardar)($('contenido-principal')||document.body).focus?.({preventScroll:true});
}
// Se ofrece cuando el globo está listo (o a los 4 s si no llega), una sola vez por navegador.
if(!visto.leer()){
  let hecho=false;const ofrecer=()=>{if(hecho)return;hecho=true;setTimeout(invitar,reducido()?0:600)};
  document.addEventListener('espacio:listo',ofrecer,{once:true});setTimeout(ofrecer,4000);
}
window.SICC_tutorial={iniciar:()=>iniciar(0),invitar,cerrar:()=>cerrar(),pasos:PASOS.length};
})();
