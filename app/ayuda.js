// Pestaña «Help»: 100 preguntas frecuentes (data/ayuda_preguntas.json) con buscador inmediato
// en inglés y español, y botón «Show me» que lleva a la pestaña o al elemento de cada respuesta.
// Todo se crea desde aquí (document.createElement): no se toca el HTML ni los módulos de otros.
(function(){
'use strict';
const $=id=>document.getElementById(id);
const nodo=(t,txt,c)=>{const n=document.createElement(t);if(txt!==undefined)n.textContent=txt;if(c)n.className=c;return n};
const pref={leer:k=>{try{return localStorage.getItem(k)}catch(e){return null}},guardar:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}}};
const reducido=()=>matchMedia('(prefers-reduced-motion:reduce)').matches;

// Nombres de los temas en los dos idiomas, en el orden en que se muestran.
const TEMAS={
  primeros_pasos:['Getting started','Primeros pasos'],
  globo_mapa:['The globe and the map','El globo y el mapa'],
  investigar:['Investigate','Investigate'],
  veredictos:['Reading a verdict','Cómo leer un veredicto'],
  metodos:['The statistical methods','Los métodos estadísticos'],
  cuencas:['Watersheds','Watersheds (cuencas)'],
  tiempo:['Weather, forecast and climate outlook','El tiempo, el pronóstico y el clima futuro'],
  capas:['Satellite and weather layers','Capas satelitales y del tiempo'],
  descargas:['Downloads','Descargas'],
  fuentes_limites:['Sources and limits','Fuentes y límites']};
const TXT={
  en:{titulo:'How can we help?',intro:'Search the questions people ask most, or browse them by topic. Each answer can take you to the part of the app it talks about.',
    buscar:'Search the help',marcador:'e.g. watershed, verdict, rain…',idioma:'Español',idiomaEtq:'Show questions in Spanish',tour:'Start the tour',
    mostrar:'Show me',todas:n=>`${n} questions in ${Object.keys(TEMAS).length} topics.`,
    resultados:(n,q,max)=>n?`${n} question${n===1?'':'s'} match “${q}”${n>max?`; showing the best ${max}`:''}.`:`No questions match “${q}”. Try another word, such as rain, map or trend.`,
    cargando:'Loading questions…',fallo:'The help questions could not be loaded. Check your connection and try again.',reintentar:'Retry',
    sinTour:'The guided tour is not available right now.',listaEtq:'Questions'},
  es:{titulo:'¿En qué podemos ayudarte?',intro:'Busca entre las preguntas más frecuentes o explóralas por tema. Cada respuesta puede llevarte a la parte de la app de la que habla.',
    buscar:'Buscar en la ayuda',marcador:'p. ej. cuenca, veredicto, lluvia…',idioma:'English',idiomaEtq:'Show questions in English',tour:'Start the tour',
    mostrar:'Show me',todas:n=>`${n} preguntas en ${Object.keys(TEMAS).length} temas.`,
    resultados:(n,q,max)=>n?`${n} pregunta${n===1?'':'s'} coinciden con «${q}»${n>max?`; se muestran las ${max} mejores`:''}.`:`Ninguna pregunta coincide con «${q}». Prueba otra palabra, como lluvia, mapa o tendencia.`,
    cargando:'Cargando preguntas…',fallo:'No se pudieron cargar las preguntas de ayuda. Revisa la conexión y vuelve a intentarlo.',reintentar:'Retry',
    sinTour:'El recorrido guiado no está disponible ahora.',listaEtq:'Preguntas'}};

// ---------------------------------------------------------------- búsqueda
// Sin acentos, en minúsculas y solo letras y números.
const normal=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
// Sinónimos sencillos español ⇄ inglés: cada grupo se trata como una misma idea.
const SINONIMOS=[
  'cuenca cuencas watershed watersheds basin basins hydrobasins hidrologia',
  'lluvia lluvias llueve rain rainfall raining precipitation precipitacion',
  'tendencia tendencias trend trends cambio change changing',
  'temperatura temperature calor caliente warming calentamiento warm',
  'mapa map maps plano flat','globo globe tierra earth 3d',
  'descarga descargas descargar download downloads csv json export exportar archivo file',
  'fuente fuentes source sources dataset datasets datos data',
  'veredicto veredictos verdict verdicts resultado result',
  'metodo metodos method methods prueba pruebas test tests estadistica statistics',
  'pronostico forecast tiempo weather meteorologia',
  'capa capas layer layers','satelite satelites satellite satellites',
  'viento wind rafagas gusts','nube nubes cloud clouds','humedad humidity','presion pressure',
  'huracan huracanes hurricane hurricanes ciclon ciclones cyclone cyclones tormenta tormentas storm storms',
  'hielo ice glaciar glaciares glacier glaciers','mar oceano sea ocean costa coast coastal',
  'bosque bosques forest forests vegetacion vegetation arboles tree trees','lago lagos lake lakes',
  'rio rios river rivers','estacion estaciones station stations','suelo soil',
  'nino enso oni','escenario escenarios scenario scenarios proyeccion proyecciones projection projections futuro future 2050',
  'ayuda help','recorrido tour tutorial guia guided guide terra',
  'intervalo interval confianza confidence','significativo significant significance significancia',
  'autocorrelacion autocorrelation','ejemplo ejemplos example examples',
  'aprender learn','investigar investigate','buscar search find encontrar',
  'codigo codigos code codes','amenaza amenazas hazard hazards riesgo risk','inundacion inundaciones flood floods',
  'sequia drought','aire air','incertidumbre uncertainty','pendiente slope','menu menú',
  'oculto ocultar hide panel paneles panels','zoom acercar alejar','idioma language espanol spanish ingles english'
].map(g=>g.split(' ').map(normal));
const VACIAS=new Set(normal('a an the of to in on is are do does i my me can how what why which where when it this that for and or with be as at by from de la el los las un una que como en y es son se mi por para con del al lo cual donde cuando qué cómo hay puedo puede').split(' '));

// Alternativas de un término: él mismo y su grupo de sinónimos (prefijos de 3 letras o más).
function alternativas(t){
  const alt=new Map([[t,1]]);
  if(t.length>=3)for(const g of SINONIMOS)if(g.some(w=>w.startsWith(t)||(w.length>=4&&t.startsWith(w))))g.forEach(w=>{if(!alt.has(w))alt.set(w,.8)});
  return alt;
}
function puntosCampo(palabras,a){let p=0;for(const w of palabras){if(w===a)return 3;if(w.startsWith(a))p=Math.max(p,2);else if(a.length>=4&&w.includes(a))p=Math.max(p,1)}return p}
let indice=[];
function indexar(preguntas){
  indice=preguntas.map(q=>{const tema=TEMAS[q.tema]||[q.tema,q.tema];
    return {q,campos:[[normal(q.pregunta_en+' '+q.pregunta_es).split(' '),3],[normal(tema.join(' ')).split(' '),2],[normal(q.respuesta_en+' '+q.respuesta_es).split(' '),1]],
      frase:normal(q.pregunta_en)+' | '+normal(q.pregunta_es)}});
}
function buscar(texto){
  const consulta=normal(texto);if(!consulta)return [];
  let terminos=consulta.split(' ').filter(t=>!VACIAS.has(t));
  if(!terminos.length)terminos=consulta.split(' ');
  const alts=terminos.map(alternativas);
  const salida=[];
  for(const e of indice){
    let total=0,acierta=0;
    alts.forEach(alt=>{let mejor=0;
      for(const [a,peso] of alt)for(const [palabras,pc] of e.campos){const p=puntosCampo(palabras,a)*pc*peso;if(p>mejor)mejor=p}
      if(mejor>0){acierta++;total+=mejor}});
    if(!acierta)continue;
    if(consulta.length>=4&&e.frase.includes(consulta))total+=6;
    salida.push({q:e.q,total,acierta});
  }
  // Primero las que contienen todos los términos; después, por puntuación.
  return salida.sort((x,y)=>(y.acierta-x.acierta)||(y.total-x.total)).filter((r,_,l)=>r.acierta===l[0].acierta||l[0].acierta<terminos.length);
}

// ---------------------------------------------------------------- navegación
function irAPestana(id){
  if(typeof window.tab==='function')window.tab(id);
  else document.querySelector(`nav button[data-tab="${id}"]`)?.click();
}
// «Show me»: abre la pestaña o el elemento del enlace, lo desplaza a la vista y lo resalta.
async function mostrar(enlace){
  if(enlace==='ayuda-tour')return iniciarTour();
  if(enlace==='ayuda-idioma'){const b=$('ayuda-idioma');b?.focus();resaltar(b);return}
  let el=$(enlace);
  const boton=document.querySelector(`nav button[data-tab="${enlace}"]`);
  if(boton&&el?.classList.contains('vista')){irAPestana(enlace);el=el.querySelector('.ventana-cuerpo h2, .ventana-cuerpo h3, .ventana-cuerpo')||el}
  else if(el){
    const vista=el.closest('.vista');
    if(vista&&vista.hidden)irAPestana(vista.id);
    if(el.closest('.solo-mapa-capas')&&window.SICC_vista?.modo()!=='mapa')await window.SICC_vista?.cambiar('mapa');
    if(vista&&vista.classList.contains('minimizada'))vista.classList.remove('minimizada');
  }
  if(!el)return;
  await new Promise(r=>requestAnimationFrame(()=>setTimeout(r,60)));
  el.scrollIntoView({block:'center',inline:'nearest',behavior:reducido()?'auto':'smooth'});
  resaltar(el);
  const enfocable=el.matches('button,a[href],input,select,textarea,[tabindex]')&&!el.disabled;
  if(!enfocable)el.setAttribute('tabindex','-1');
  el.focus({preventScroll:true});
}
function resaltar(el){if(!el)return;el.classList.remove('ayuda-resaltado');void el.offsetWidth;el.classList.add('ayuda-resaltado');setTimeout(()=>el.classList.remove('ayuda-resaltado'),2400)}
function iniciarTour(){if(window.SICC_tutorial)window.SICC_tutorial.iniciar();else estado(TXT[idioma].sinTour)}

// ---------------------------------------------------------------- interfaz
let preguntas=null,carga=null,idioma=window.GnomonI18n?.language()||(pref.leer('etd-ayuda-idioma')==='es'?'es':'en'),ultima='';
const MAX=15;
let seccion,cuerpo,entrada,lista,linea,botonIdioma,botonTour,titulo,intro,etiquetaBuscar;
function estado(t){if(linea)linea.textContent=t}

function crearBotonMenu(){
  const nav=$('menu-principal');if(!nav||nav.querySelector('[data-tab="ayuda"]'))return;
  const b=nodo('button');b.type='button';b.dataset.tab='ayuda';
  b.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 1 1 3.4 2.3c-.6.3-1 .8-1 1.5v.6M12 16.8v.2"/></svg>';
  b.append(nodo('span','Help','txt'));b.dataset.nombre='Help';
  b.onclick=()=>abrir();
  const aprender=nav.querySelector('[data-tab="aprender"]');
  if(aprender)aprender.after(b);else nav.append(b);
  // Acceso permanente al recorrido de Terra (tras verlo una vez la invitación ya no vuelve a salir).
  // Va en la cabecera, junto a «Hide panels»: en el menú lateral empujaba Sources fuera de la vista.
  const solo=$('solomapa');
  if(solo&&!$('menu-tour')){const t=nodo('button','Guided tour');t.type='button';t.id='menu-tour';t.onclick=iniciarTour;solo.after(t)}
}
function crearSeccion(){
  const main=$('contenido-principal')||document.querySelector('main');if(!main)return;
  seccion=nodo('section',undefined,'vista ventana ayuda');seccion.id='ayuda';seccion.hidden=true;seccion.setAttribute('aria-labelledby','ayuda-titulo');
  // Barra de ventana igual que las demás pestañas: ocultar, minimizar y ancho completo.
  const barra=nodo('div',undefined,'ventana-barra'),pts=nodo('div',undefined,'ventana-botones');
  const punto=(clase,etq,fn)=>{const b=nodo('button','','punto '+clase);b.type='button';b.title=etq;b.setAttribute('aria-label',etq);b.onclick=fn;pts.append(b)};
  const paneles=()=>document.dispatchEvent(new CustomEvent('sicc:paneles'));
  punto('rojo','Hide panel',()=>{window.SICC_vista?.soloMapa?.(true)});
  punto('ambar','Minimize',()=>{seccion.classList.toggle('minimizada');paneles()});
  punto('verde','Wide',()=>{seccion.classList.toggle('ancha');paneles()});
  barra.append(pts,nodo('span','Help','ventana-titulo'));barra.ondblclick=()=>{seccion.classList.toggle('minimizada');paneles()};
  cuerpo=nodo('div',undefined,'ventana-cuerpo');
  const cab=nodo('div',undefined,'intro');titulo=nodo('h2');titulo.id='ayuda-titulo';intro=nodo('p');cab.append(titulo,intro);
  const herramientas=nodo('div',undefined,'ayuda-herramientas');
  etiquetaBuscar=nodo('label',undefined,'ayuda-buscar');
  const etqTexto=nodo('span');entrada=nodo('input');entrada.type='search';entrada.id='ayuda-buscar';entrada.autocomplete='off';entrada.spellcheck=false;
  entrada.setAttribute('aria-controls','ayuda-lista');entrada.setAttribute('aria-describedby','ayuda-estado');
  etiquetaBuscar.append(etqTexto,entrada);
  const acciones=nodo('div',undefined,'ayuda-acciones');
  botonIdioma=nodo('button',undefined,'mini');botonIdioma.type='button';botonIdioma.id='ayuda-idioma';
  botonIdioma.setAttribute('data-i18n-ignore','');
  botonIdioma.onclick=()=>{if(window.GnomonI18n){window.GnomonI18n.setLanguage(idioma==='en'?'es':'en');return}idioma=idioma==='en'?'es':'en';pref.guardar('etd-ayuda-idioma',idioma);textos();pintar(entrada.value)};
  botonTour=nodo('button',undefined,'ayuda-tour');botonTour.type='button';botonTour.id='ayuda-tour';
  botonTour.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5l11 7-11 7z"/></svg>';botonTour.append(nodo('span'));
  botonTour.onclick=iniciarTour;
  acciones.append(botonTour,botonIdioma);
  herramientas.append(etiquetaBuscar,acciones);
  linea=nodo('p',undefined,'ayuda-estado');linea.id='ayuda-estado';linea.setAttribute('role','status');linea.setAttribute('aria-live','polite');
  lista=nodo('div',undefined,'ayuda-lista');lista.id='ayuda-lista';lista.setAttribute('role','region');
  cuerpo.append(cab,herramientas,linea,lista);
  seccion.append(barra,cuerpo);
  main.append(seccion);
  // Búsqueda inmediata; flecha abajo o Intro llevan a la primera pregunta encontrada.
  entrada.addEventListener('input',()=>pintar(entrada.value));
  entrada.addEventListener('keydown',e=>{
    if(e.key==='ArrowDown'){const b=lista.querySelector('.ayuda-pregunta');if(b){e.preventDefault();b.focus()}}
    else if(e.key==='Enter'){const b=lista.querySelector('.ayuda-pregunta');if(b){e.preventDefault();desplegar(b,true);b.focus()}}
    else if(e.key==='Escape'&&entrada.value){e.preventDefault();e.stopPropagation();entrada.value='';pintar('')}
  });
  // Flechas arriba y abajo entre preguntas, como en una lista.
  lista.addEventListener('keydown',e=>{
    if(!e.target.classList?.contains('ayuda-pregunta')||!['ArrowDown','ArrowUp','Home','End'].includes(e.key))return;
    const todas=[...lista.querySelectorAll('.ayuda-pregunta')],i=todas.indexOf(e.target);e.preventDefault();
    if(e.key==='ArrowUp'&&i===0)return entrada.focus();
    const j={ArrowDown:i+1,ArrowUp:i-1,Home:0,End:todas.length-1}[e.key];todas[Math.max(0,Math.min(todas.length-1,j))]?.focus();
  });
  textos();
}
function textos(){
  const t=TXT[idioma];
  titulo.textContent=t.titulo;intro.textContent=t.intro;etiquetaBuscar.firstChild.textContent=t.buscar;entrada.placeholder=t.marcador;
  botonIdioma.textContent=t.idioma;botonIdioma.setAttribute('aria-label',t.idiomaEtq);botonIdioma.lang=idioma==='en'?'es':'en';
  botonIdioma.setAttribute('aria-pressed',String(idioma==='es'));
  botonTour.querySelector('span').textContent=t.tour;
  lista.setAttribute('aria-label',t.listaEtq);lista.lang=idioma;intro.lang=titulo.lang=idioma;
}
function desplegar(b,abrirSiempre){
  const r=$(b.getAttribute('aria-controls'));const abrir=abrirSiempre||b.getAttribute('aria-expanded')!=='true';
  b.setAttribute('aria-expanded',String(abrir));if(r)r.hidden=!abrir;
}
function itemPregunta(q,abierta){
  const li=nodo('li',undefined,'ayuda-item');li.dataset.id=q.id;
  const b=nodo('button',undefined,'ayuda-pregunta');b.type='button';b.id='ayuda-p-'+q.id;b.setAttribute('aria-controls','ayuda-r-'+q.id);b.setAttribute('aria-expanded','false');
  b.append(nodo('span',idioma==='es'?q.pregunta_es:q.pregunta_en));
  b.insertAdjacentHTML('beforeend','<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 10l5 5 5-5"/></svg>');
  const r=nodo('div',undefined,'ayuda-respuesta');r.id='ayuda-r-'+q.id;r.hidden=true;r.setAttribute('role','region');r.setAttribute('aria-labelledby',b.id);
  r.append(nodo('p',idioma==='es'?q.respuesta_es:q.respuesta_en));
  if(q.enlace){const m=nodo('button',TXT[idioma].mostrar,'mini ayuda-mostrar');m.type='button';m.lang='en';m.onclick=()=>mostrar(q.enlace);r.append(m)}
  b.onclick=()=>desplegar(b);
  li.append(b,r);if(abierta)desplegar(b,true);
  return li;
}
function pintar(texto){
  if(!preguntas)return;
  const t=TXT[idioma],abiertas=new Set([...lista.querySelectorAll('.ayuda-pregunta[aria-expanded="true"]')].map(b=>b.closest('li').dataset.id));
  const foco=document.activeElement?.closest?.('#ayuda-lista li')?.dataset.id;
  lista.replaceChildren();
  const q=texto.trim();
  if(!q){
    for(const [tema,nombres] of Object.entries(TEMAS)){
      const del=preguntas.filter(p=>p.tema===tema);if(!del.length)continue;
      const g=nodo('section',undefined,'ayuda-tema');const h=nodo('h3',nombres[idioma==='es'?1:0]);h.id='ayuda-t-'+tema;g.setAttribute('aria-labelledby',h.id);
      const ul=nodo('ul',undefined,'ayuda-preguntas');del.forEach(p=>ul.append(itemPregunta(p,abiertas.has(p.id))));
      g.append(h,ul);lista.append(g);
    }
    if(q!==ultima||!linea.textContent)estado(t.todas(preguntas.length));
  }else{
    const r=buscar(q),ul=nodo('ul',undefined,'ayuda-preguntas ayuda-resultados');
    r.slice(0,MAX).forEach(x=>ul.append(itemPregunta(x.q,abiertas.has(x.q.id))));
    lista.append(ul);estado(t.resultados(r.length,q,MAX));
  }
  ultima=q;
  if(foco)lista.querySelector(`li[data-id="${foco}"] .ayuda-pregunta`)?.focus({preventScroll:true});
}
function cargar(){
  if(preguntas)return Promise.resolve(preguntas);
  estado(TXT[idioma].cargando);
  carga??=fetch('data/ayuda_preguntas.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
    .then(d=>{if(!Array.isArray(d)||!d.length)throw Error('empty');preguntas=d;indexar(d);pintar(entrada.value);return d})
    .catch(()=>{carga=null;estado(TXT[idioma].fallo);const b=nodo('button',TXT[idioma].reintentar);b.type='button';b.onclick=()=>{lista.replaceChildren();cargar()};lista.replaceChildren(b)});
  return carga;
}
function abrir(consulta){
  irAPestana('ayuda');
  cargar().then(()=>{if(typeof consulta==='string'){entrada.value=consulta;pintar(consulta)}});
  requestAnimationFrame(()=>entrada?.focus({preventScroll:true}));
}

crearBotonMenu();crearSeccion();
// El recorrido de Terra vive en app/tutorial.js; se carga desde aquí para dejar una sola línea en index.html.
if(!window.SICC_tutorial){const s=document.createElement('script');s.src='app/tutorial.js';s.defer=true;
  s.onerror=()=>{botonTour.disabled=true;botonTour.title=TXT.en.sinTour};document.head.append(s)}
document.addEventListener('sicc:pestana',e=>{if(e.detail==='ayuda')cargar()});
document.addEventListener('gnomon:languagechange',e=>{idioma=e.detail.language;if(entrada){textos();if(preguntas)pintar(entrada.value)}});
window.SICC_ayuda={abrir,buscar:texto=>{if(!indice.length)return [];return buscar(texto).map(r=>r.q.id)},cargar,mostrar};
})();
