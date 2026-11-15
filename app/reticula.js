// Retícula independiente: solo pinta la vista visible, sin alterar capas ni proyecciones existentes.
(function(){
  'use strict';
  const PASOS=[.0001,.0005,.001,.005,.01,.05,.1,.5,1,5,10,30,60,90];
  const TROPICO=23.436, POLAR=90-TROPICO; // Latitudes de referencia aproximadas, no efemérides.
  const PARALELOS=[
    {valor:0,nombre:'Equator',color:'#ffdf8f'},
    {valor:TROPICO,nombre:'Tropic of Cancer',color:'#b4f1bd'},
    {valor:-TROPICO,nombre:'Tropic of Capricorn',color:'#b4f1bd'},
    {valor:POLAR,nombre:'Arctic Circle',color:'#a6d7ff'},
    {valor:-POLAR,nombre:'Antarctic Circle',color:'#a6d7ff'}
  ];
  const MERIDIANOS=[{valor:0,nombre:'Greenwich meridian',color:'#9ae4f1'},
    {valor:180,nombre:'Antimeridian',color:'#e1b9ff'}];
  const $=id=>document.getElementById(id);
  const crear=(tag,texto,clase)=>{const e=document.createElement(tag);if(texto!=null)e.textContent=texto;if(clase)e.className=clase;return e;};
  const contenedor=document.querySelector('#barra-capas .ventana-cuerpo')||$('barra-capas');
  if(!contenedor)return;
  let visible=false,unidad='degrees';
  try{visible=localStorage.getItem('etd-reticula-visible')==='1';unidad=localStorage.getItem('etd-reticula-unidad')==='radians'?'radians':'degrees';}catch(e){}
  const grupo=crear('div',null,'reticula-controles');grupo.id='reticula-controles';grupo.setAttribute('role','group');grupo.setAttribute('aria-label','Map grid and orientation');
  const boton=crear('button',null,'reticula-principal');boton.type='button';boton.id='reticula-toggle';boton.setAttribute('aria-label','Geographic grid');
  const unidades=crear('select');unidades.id='reticula-unidades';unidades.setAttribute('aria-label','Coordinate units');
  for(const [valor,texto] of [['degrees','Degrees'],['radians','Radians']]){const o=crear('option',texto);o.value=valor;unidades.append(o);}unidades.value=unidad;
  const fila=crear('div',null,'reticula-fila'),norte=crear('button',null,'reticula-norte');norte.id='reticula-norte';norte.type='button';norte.setAttribute('aria-label','North up');
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 20 24');svg.setAttribute('aria-hidden','true');
  const flecha=document.createElementNS(svg.namespaceURI,'path');flecha.setAttribute('d','M10 3L4 18l6-4 6 4z');flecha.setAttribute('fill','none');flecha.setAttribute('stroke','currentColor');flecha.setAttribute('stroke-width','1.5');svg.append(flecha);norte.append(svg,crear('span','North up'));
  const ayuda=crear('button','?','reticula-ayuda');ayuda.id='reticula-ayuda';ayuda.type='button';ayuda.setAttribute('aria-label','Geographic grid guide');ayuda.setAttribute('aria-expanded','false');ayuda.setAttribute('aria-controls','reticula-guia');
  fila.append(norte,ayuda);grupo.append(boton,unidades,fila);contenedor.prepend(grupo);
  const estado=crear('p',null,'reticula-estado');estado.setAttribute('role','status');estado.setAttribute('aria-live','polite');grupo.append(estado);
  const guia=crear('section',null,'reticula-guia');guia.id='reticula-guia';guia.hidden=true;guia.tabIndex=-1;guia.setAttribute('role','dialog');guia.setAttribute('aria-label','Geographic grid guide');
  document.body.append(guia);
  let canvas=null,ctx=null,turno=0,paso=30,lineas=0,ultimaTextura='';
  const mapaListo=typeof mapa!=='undefined'&&mapa&&window.L;
  function avisar(t){estado.textContent=t;}
  function guardar(){try{localStorage.setItem('etd-reticula-visible',visible?'1':'0');localStorage.setItem('etd-reticula-unidad',unidad);return true;}catch(e){return false;}}
  const envolver=x=>((x+180)%360+360)%360-180;
  function formato(v,eje){
    const x=Math.abs(v)<1e-8?0:v;
    if(unidad==='radians'){const r=x*Math.PI/180,dec=window.SICC_vista?.modo()==='mapa'?Math.min(8,Math.max(3,Math.ceil(-Math.log10(paso*Math.PI/180))+1)):3;
      return (Math.abs(r)<.5*10**(-dec)?(0).toFixed(dec):r.toFixed(dec).replace('-','−'))+' rad';}
    const a=Number(Math.abs(x).toFixed(5));return a+'°'+(x===0||Math.abs(Math.abs(x)-180)<1e-7?'':eje==='lat'?(x>0?'N':'S'):(x>0?'E':'W'));
  }
  function pintarGuia(){guia.replaceChildren();guia.append(crear('h2','Geographic reference lines'));
    const ul=crear('ul');for(const l of [...PARALELOS,...MERIDIANOS])ul.append(crear('li',l.nombre+' · '+formato(l.valor,PARALELOS.includes(l)?'lat':'lon')));guia.append(ul,crear('p','Tropics and polar circles use approximate reference latitudes. Grid spacing adapts to the view; degrees and radians describe the same lines.'),crear('p','The map is north-up. Rotation is unavailable with the current weather layers.'));
    const cerrar=crear('button','Close');cerrar.type='button';cerrar.onclick=cerrarGuia;guia.append(cerrar);
  }
  function cerrarGuia(){guia.hidden=true;ayuda.setAttribute('aria-expanded','false');ayuda.focus();}
  function posicionGuia(){if(guia.hidden)return;const r=grupo.getBoundingClientRect(),h=document.querySelector('header')?.getBoundingClientRect();
    const ancho=Math.min(290,innerWidth-24);guia.style.width=ancho+'px';
    const x=Math.max(12,Math.min(innerWidth-ancho-12,r.left-ancho-12)),y=Math.max(12,Math.min(innerHeight-130,(h?.bottom??12)+8));let fondo=innerHeight-12;
    for(const e of document.querySelectorAll('#controles-mapa>*,.leaflet-control-zoom')){const q=e.getBoundingClientRect();if(q.width&&q.height&&q.left<x+ancho&&q.right>x&&q.top>y)fondo=Math.min(fondo,q.top-8);}
    guia.style.left=x+'px';guia.style.top=y+'px';guia.style.maxHeight=Math.max(80,Math.min(innerHeight*.55,fondo-y))+'px';
  }
  ayuda.onclick=()=>{if(!guia.hidden){cerrarGuia();return;}pintarGuia();guia.hidden=false;ayuda.setAttribute('aria-expanded','true');posicionGuia();guia.focus();};
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!guia.hidden){e.preventDefault();cerrarGuia();}});
  document.addEventListener('pointerdown',e=>{if(!guia.hidden&&!guia.contains(e.target)&&!ayuda.contains(e.target)){guia.hidden=true;ayuda.setAttribute('aria-expanded','false');}});
  function sincronizar(){boton.textContent=visible?'Grid: hide':'Grid: show';boton.setAttribute('aria-pressed',String(visible));boton.title=visible?'Hide geographic grid':'Show geographic grid';if(canvas)canvas.hidden=!visible;}
  // Solo se enumeran los múltiplos presentes en el intervalo visible, incluso junto a ±180°.
  function multiplos(min,max,s){const xs=[];for(let k=Math.ceil((min-1e-8)/s),fin=Math.floor((max+1e-8)/s);k<=fin&&xs.length<200;k++)xs.push(Number((k*s).toFixed(7)));return xs;}
  function espacioLibre(){const r=mapa.getContainer().getBoundingClientRect(),s=mapa.getSize();let izq=7,der=s.x-7,arriba=7,abajo=s.y-7;
    // Los rótulos se sitúan en el borde de la parte del mapa que dejan libre los paneles.
    const header=document.querySelector('header')?.getBoundingClientRect();if(header&&header.bottom>r.top&&header.top<r.bottom)arriba=Math.max(arriba,header.bottom-r.top+7);
    if(innerWidth>700){for(const e of document.querySelectorAll('aside,.vista:not([hidden])')){const q=e.getBoundingClientRect();if(q.width&&q.height&&q.left-r.left<s.x/2&&q.bottom>r.top)izq=Math.max(izq,q.right-r.left+7);}
      const c=$('barra-capas').getBoundingClientRect();if(c.width&&c.left>r.left)der=Math.min(der,c.left-r.left-7);}
    if(der-izq<80){izq=7;der=s.x-7;}
    return {izq,der,arriba,abajo};
  }
  function dibujar2D(){if(!ctx||!visible||window.SICC_vista?.modo()!=='mapa'){if(canvas)canvas.style.visibility='hidden';return;}
    const s=mapa.getSize();if(s.x<1||s.y<1)return;const dpr=Math.min(2,devicePixelRatio||1);
    canvas.width=Math.ceil(s.x*dpr);canvas.height=Math.ceil(s.y*dpr);canvas.style.width=s.x+'px';canvas.style.height=s.y+'px';canvas.style.visibility='';ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,s.x,s.y);
    const b=mapa.getBounds(),sur=Math.max(-85.05112878,b.getSouth()),norte=Math.min(85.05112878,b.getNorth()),oeste=b.getWest(),este=b.getEast();
    paso=PASOS.find(p=>p/360*256*2**mapa.getZoom()>=85)||90;lineas=0;
    const libre=espacioLibre(),ocupados=[];ctx.font='11px system-ui, sans-serif';ctx.textBaseline='middle';
    const obstaculos=[...document.querySelectorAll('header,aside,.vista,#controles-mapa>*,.leaflet-control')].filter(e=>!e.hidden).map(e=>{const q=e.getBoundingClientRect(),m=mapa.getContainer().getBoundingClientRect();return {x:q.left-m.left,y:q.top-m.top,w:q.width,h:q.height};}).filter(q=>q.w&&q.h);
    const choca=(a,b)=>a.x<b.x+b.w+3&&a.x+a.w+3>b.x&&a.y<b.y+b.h+3&&a.y+a.h+3>b.y;
    function etiqueta(t,x,y,color,alinear){const w=ctx.measureText(t).width+10,h=18;const r={x:alinear==='right'?x-w:x,y:y-h/2,w,h};
      if(r.x<1||r.x+w>s.x-1||r.y<1||r.y+h>s.y-1||ocupados.some(q=>choca(r,q))||obstaculos.some(q=>choca(r,q)))return;
      ocupados.push(r);ctx.fillStyle='rgba(7,17,29,.86)';ctx.fillRect(r.x,r.y,w,h);ctx.fillStyle=color;ctx.fillText(t,r.x+5,y);
    }
    function linea(v,eje,especial){const p=mapa.latLngToContainerPoint(eje==='lat'?[v,oeste]:[sur,v]),c=especial?.color||'rgba(225,238,249,.52)';
      ctx.beginPath();ctx.lineWidth=especial?1.5:.7;ctx.strokeStyle=c;ctx.setLineDash(especial&&especial.valor!==0?[5,4]:[]);
      if(eje==='lat'){ctx.moveTo(0,p.y);ctx.lineTo(s.x,p.y);}else{ctx.moveTo(p.x,0);ctx.lineTo(p.x,s.y);}ctx.stroke();ctx.setLineDash([]);lineas++;
      const valor=eje==='lon'?envolver(v):v,t=(especial?especial.nombre+' · ':'')+formato(especial?.nombre==='Antimeridian'?180:valor,eje);
      if(eje==='lat'){etiqueta(t,libre.izq,p.y,c);if(especial)etiqueta(t,libre.der,p.y,c,'right');}
      else{etiqueta(t,p.x+3,libre.arriba+10,c);if(especial)etiqueta(t,p.x+3,libre.abajo-10,c);}
    }
    const paralelos=PARALELOS.filter(l=>l.valor>=sur&&l.valor<=norte),meridianos=[];
    for(const l of MERIDIANOS)for(const v of multiplos(oeste-l.valor,este-l.valor,360))meridianos.push({...l,valor:v+l.valor});
    // Se rotulan primero las referencias, para que los intervalos ordinarios no les quiten espacio.
    for(const l of paralelos)linea(l.valor,'lat',l);for(const l of meridianos)linea(l.valor,'lon',l);
    for(const v of multiplos(sur,norte,paso))if(!paralelos.some(l=>Math.abs(l.valor-v)<1e-6))linea(v,'lat');
    for(const v of multiplos(oeste,este,paso))if(!meridianos.some(l=>Math.abs(l.valor-v)<1e-6))linea(v,'lon');
    canvas.setAttribute('aria-label','Visible geographic grid, '+formato(paso,'lat').replace(/[NS]$/,'')+' spacing. '+[...paralelos,...meridianos].map(l=>l.nombre).join(', '));
  }
  function dibujar3D(){const E=window.Espacio;if(!E?.reticula)return;
    const dist=E.centro().dist,intervalo=dist<1.7?5:dist<3?10:30,clave=visible+'|'+unidad+'|'+intervalo;
    if(clave===ultimaTextura)return;ultimaTextura=clave;if(!visible){E.reticula(null);return;}
    const c=crear('canvas');c.width=2048;c.height=1024;const x=c.getContext('2d');if(!x){avisar('Globe grid unavailable: canvas could not be created.');return;}
    function linea(v,eje,ref){const px=(v+180)/360*c.width,py=(90-v)/180*c.height;x.beginPath();x.strokeStyle=ref?.color||'rgba(228,239,250,.45)';x.lineWidth=ref?2:1;x.setLineDash(ref&&ref.valor!==0?[8,5]:[]);
      if(eje==='lat'){x.moveTo(0,py);x.lineTo(c.width,py);}else{x.moveTo(px,0);x.lineTo(px,c.height);}x.stroke();x.setLineDash([]);
      if(ref&&eje==='lat'){x.font='15px system-ui, sans-serif';for(const lon of [-120,0,120]){const xx=(lon+180)/360*c.width;x.lineWidth=3;x.strokeStyle='#081320';const t=ref.nombre+' · '+formato(v,'lat');x.strokeText(t,xx+5,py-5);x.fillStyle=ref.color;x.fillText(t,xx+5,py-5);}}
      if(ref&&eje==='lon'){x.font='15px system-ui, sans-serif';for(const lat of [-45,0,45]){const yy=(90-lat)/180*c.height,xx=((px%c.width)+c.width)%c.width+5,t=ref.nombre+' · '+formato(ref.valor,'lon');x.lineWidth=3;x.strokeStyle='#081320';x.strokeText(t,xx,yy+17);x.fillStyle=ref.color;x.fillText(t,xx,yy+17);}}
    }
    for(let v=-180;v<=180;v+=intervalo)linea(v,'lon');for(let v=-90+intervalo;v<90;v+=intervalo)linea(v,'lat');
    for(const l of PARALELOS)linea(l.valor,'lat',l);for(const l of MERIDIANOS){linea(l.valor,'lon',l);if(l.valor===180)linea(-180,'lon',l);}
    E.reticula(c);
  }
  function repintar(){turno=0;sincronizar();dibujar2D();dibujar3D();posicionGuia();}
  function pedir(){if(!turno)turno=requestAnimationFrame(repintar);}
  boton.onclick=()=>{visible=!visible;const guardado=guardar();pedir();avisar((visible?'Geographic grid shown.':'Geographic grid hidden.')+(guardado?'':' Settings could not be saved on this device.'));};
  unidades.onchange=()=>{unidad=unidades.value;const guardado=guardar();if(!guia.hidden)pintarGuia();pedir();avisar((unidad==='radians'?'Coordinates in radians.':'Coordinates in degrees.')+(guardado?'':' Settings could not be saved on this device.'));};
  norte.onclick=()=>{if(window.SICC_vista?.modo()==='mapa'){if(typeof mapa.setBearing==='function')mapa.setBearing(0);pedir();avisar('North is up.');}
    else if(window.Espacio?.norteArriba){avisar(window.Espacio.norteArriba()?'North is up.':'Wait for the view change, then try North up again.');}
    else avisar('Globe orientation unavailable. Use the 2D map or reload to retry.');};
  if(mapaListo){canvas=crear('canvas',null,'reticula-canvas');canvas.style.cssText='position:absolute;inset:0;pointer-events:none;z-index:460';canvas.id='reticula-canvas';canvas.setAttribute('role','img');mapa.getContainer().append(canvas);ctx=canvas.getContext('2d');
    if(!ctx)avisar('Map grid unavailable: this browser could not create a canvas.');
    mapa.on('movestart zoomstart',()=>{canvas.style.visibility='hidden';});mapa.on('moveend zoomend resize',pedir);
  }else avisar('Map grid unavailable: the map library did not load. Reload to retry.');
  if(getComputedStyle(grupo).display!=='flex'){
    // Si falla el CSS, el mapa sigue recibiendo gestos y queda un aviso visible.
    grupo.style.cssText='display:flex;flex-wrap:wrap;gap:4px';
    guia.style.cssText='position:fixed;z-index:12;max-width:90vw;max-height:55vh;overflow:auto;background:#101b2a;color:#fff;padding:12px';
    avisar('Map guide styles did not load. Reload to restore their layout.');
  }
  for(const ev of ['sicc:vista','sicc:paneles','sicc:pestana','espacio:listo'])document.addEventListener(ev,pedir);
  for(const id of ['vista-mapa','vista-globo'])$(id)?.addEventListener('click',pedir);
  $('espacio')?.addEventListener('wheel',pedir,{passive:true});$('espacio')?.addEventListener('pointerup',pedir);$('espacio')?.addEventListener('keyup',pedir);
  addEventListener('resize',pedir);sincronizar();pedir();
  setTimeout(()=>{if(visible&&window.SICC_vista?.modo()!=='mapa'&&!window.Espacio?.reticula)avisar('Globe grid unavailable. The grid remains available in the 2D map.');},20000);
  window.SICC_reticula={estado:()=>({visible,unidad,paso,lineas,globo:!!window.Espacio?.reticula}),formato,multiplos};
})();
