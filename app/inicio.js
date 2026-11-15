// Atajos de la tarjeta inicial de Weather: llevan a Investigate, que es el núcleo del reto,
// sin quitar nada de la pestaña del tiempo.
(function(){
const tarjeta=document.querySelector('#meteorologia .ayuda-inicio');
const pestana=document.querySelector('nav button[data-tab="investigar"]');
if(!tarjeta||!pestana)return;
const boton=(texto,clase)=>{const b=document.createElement('button');b.type='button';b.textContent=texto;if(clase)b.className=clase;return b};
const fila=document.createElement('div');fila.className='inicio-atajos';
const abrir=boton('Investigate trends','inicio-principal');
const ejemplo=boton('Example: Mediterranean marine heatwaves');
abrir.onclick=()=>pestana.click();
ejemplo.onclick=()=>{
  pestana.click();
  // Investigate carga sus datos al abrirse; se elige el ejemplo en cuanto están listos.
  const t0=Date.now();
  const esperar=()=>{const inv=window.SICC_investigar;
    if(inv&&inv.estado().cargado)inv.elegir({categoria:'costa',lugar:'mediterraneo',investigacion:'mediterraneo_olas_calor'});
    else if(Date.now()-t0<15000)setTimeout(esperar,150)};
  esperar();
};
fila.append(abrir,ejemplo);
tarjeta.append(fila);
})();

// Orientación en paneles largos: títulos de sección en Layers y el lugar o la variable
// elegidos siempre a la vista dentro de sus listas con desplazamiento.
(function(){
const cuerpo=document.querySelector('#barra-capas .ventana-cuerpo');
const titulo=texto=>{const t=document.createElement('div');t.className='capas-seccion';t.textContent=texto;return t};
const reticula=document.getElementById('reticula-controles');
if(cuerpo&&reticula&&reticula.parentNode===cuerpo)reticula.before(titulo('Map grid'));
const primera=cuerpo&&cuerpo.querySelector(':scope > [data-var]');
if(primera)primera.before(titulo('Weather layer'));
const aLaVista=lista=>{const b=lista.querySelector('[aria-checked="true"]');if(!b)return;
  const r=b.getBoundingClientRect(),q=lista.getBoundingClientRect();if(!q.height)return;
  if(r.top<q.top)lista.scrollTop+=r.top-q.top-6;else if(r.bottom>q.bottom)lista.scrollTop+=r.bottom-q.bottom+6};
['inv-lugares','inv-variables'].forEach(id=>{const lista=document.getElementById(id);
  if(lista)new MutationObserver(()=>aLaVista(lista)).observe(lista,{childList:true})});
})();
