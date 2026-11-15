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
