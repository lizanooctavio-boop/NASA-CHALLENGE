// Estilo de texto opcional (paletas de Benjamin). «Original» no cambia nada; las fuentes de
// Google solo se descargan cuando se elige una paleta que las usa.
(function(){
'use strict';
const CLAVE='gnomon-text-style';
// id, nombre, fuentes de Google que necesita
const PALETAS=[
  ['original','Original',null],
  ['pastel-lavanda','Lavender mist','DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700'],
  ['pastel-menta','Ionic mint','Work+Sans:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700'],
  ['pastel-coral','Photon coral','DM+Sans:wght@400;500;600;700&family=Outfit:wght@600;700'],
  ['pastel-orbita','Orbit blue','Inter:wght@400;500;600;700&family=Manrope:wght@600;800'],
  ['pastel-terracota','Peach terracotta','Work+Sans:wght@400;500;600&family=Lora:wght@600;700'],
  ['pastel-rosa','Holographic quartz','IBM+Plex+Sans:wght@400;500;600;700&family=Syne:wght@600;700'],
  ['pastel-arena','Satellite sand','Work+Sans:wght@400;500;600&family=Merriweather:wght@700'],
  ['pastel-lima','Zero-gravity lime','Open+Sans:wght@400;500;600&family=Rubik:wght@500;600'],
  ['royal','Royal Dusk','Inter:wght@400;500;600;700&family=Manrope:wght@600;800'],
  ['nordic','Nordic Frost','Open+Sans:wght@400;500;600&family=Rubik:wght@500;600']
];
const valida=v=>PALETAS.some(([id])=>id===v);
const raiz=document.documentElement;
let actual='original';
try{const g=localStorage.getItem(CLAVE);if(valida(g))actual=g}catch(e){/* sin almacenamiento */}
function fuentes(id){
  const f=PALETAS.find(p=>p[0]===id)?.[2];if(!f||document.getElementById('fuentes-estilo-'+id))return;
  const l=document.createElement('link');l.id='fuentes-estilo-'+id;l.rel='stylesheet';
  l.href='https://fonts.googleapis.com/css2?family='+f+'&family=JetBrains+Mono:wght@400;500&display=swap';document.head.append(l);
}
function aplicar(id){
  if(id==='original')delete raiz.dataset.uiTheme;else{raiz.dataset.uiTheme=id;fuentes(id)}
}
// Antes del primer dibujo, para no ver un destello con otro estilo.
aplicar(actual);
document.addEventListener('DOMContentLoaded',()=>{
  const sel=document.getElementById('estilo-texto'),estado=document.getElementById('estilo-texto-estado');
  if(!sel)return;
  const t=s=>window.GnomonI18n?.t(s)??s;
  const opciones=()=>{sel.replaceChildren(...PALETAS.map(([id,nombre])=>{const o=document.createElement('option');o.value=id;o.textContent=t(nombre);return o}));sel.value=actual};
  opciones();
  sel.addEventListener('change',()=>{
    if(!valida(sel.value))return;
    actual=sel.value;aplicar(actual);
    try{localStorage.setItem(CLAVE,actual)}catch(e){/* vale para esta sesión */}
    if(estado)estado.textContent=t('Text style applied.');
  });
  document.addEventListener('gnomon:languagechange',opciones);
});
})();
