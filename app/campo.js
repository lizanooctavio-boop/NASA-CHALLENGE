// Mapa estilo Meteored: capas de color (temperatura, lluvia, viento, ráfagas, nubes, humedad, presión),
// partículas que siguen el viento y línea de tiempo. Dibuja la malla mundial ECMWF y, donde existe,
// la malla regional horaria fundida encima. Publica la hora y la capa para el globo 3D.
(function(){
const $=id=>document.getElementById(id);
const soporte=window.SICC_soporte;
const json=r=>typeof leerJSON==='function'?leerJSON(r):r.json();
const texto=(id,t)=>{const e=$(id);if(e)e.textContent=t};
function sinCampo(msg){const b=$('indicador-datos');if(b){b.dataset.nivel='error';b.title=msg;texto('indicador-texto','No model data')}}
if(!soporte){sinCampo('Weather support module unavailable.');return}
if(typeof mapa==='undefined'||!mapa){sinCampo('Map library unavailable.');return}

const { escalas: ESCALAS, color } = window.PaletasMeteo;
const mqReducido=matchMedia('(prefers-reduced-motion:reduce)');
let reducido=mqReducido.matches;
const DPR=Math.min(2,window.devicePixelRatio||1);
const REFRESCO_MIN=60;
let G=null,variable='temperatura_c',hora=0,raf=0,opacidad=.7,conParticulas=true,reproducir=null;
const enGlobo=()=>window.SICC_vista?.modo()!=='mapa';
const avisar=nombre=>document.dispatchEvent(new CustomEvent(nombre));

const lon180=l=>((l+180)%360+360)%360-180;
function indice(lat,lon){const L=G.latitudes,O=G.longitudes;const fi=(lat-L[0])/(L[1]-L[0]),fj=(lon180(lon)-O[0])/(O[1]-O[0]);return fi>=0&&fj>=0&&fi<=L.length-1&&fj<=O.length-1?[fi,fj]:null}
function bilineal(M,fi,fj){const i=Math.min(Math.floor(fi),M.length-2),j=Math.min(Math.floor(fj),M[0].length-2),a=fi-i,b=fj-j;return soporte.bilineal([M[i][j],M[i][j+1],M[i+1][j],M[i+1][j+1]],a,b)}
const cacheViento={};
function campo(v,h){if(v==='viento_ms'){if(!cacheViento[h]){const U=G.variables.viento_u_ms[h],V=G.variables.viento_v_ms[h];cacheViento[h]=U.map((f,i)=>f.map((u,j)=>Math.hypot(u,V[i][j])))}return cacheViento[h]}return G.variables[v][h]}
function muestra(v,lat,lon,h=hora){if(!G)return null;const ij=indice(lat,lon);return ij?bilineal(campo(v,h),ij[0],ij[1]):null}
function borde(fi,fj){return Math.max(0,Math.min(1,Math.min(fi,G.latitudes.length-1-fi,fj,G.longitudes.length-1-fj)/2))}

// ---- Malla mundial (ECMWF IFS 1°, cada 3 h). La regional se funde encima en su borde.
let GM=null;const cacheG={},pidiendo={};
function mundialDisponible(){return GM&&GM.horas_utc.length>0&&soporte.utc(GM.corrida_utc)<=Date.now()}
const horasActivas=()=>G?.horas_utc||(mundialDisponible()?GM.horas_utc:[]);
function pasoGlobal(h=hora){if(!mundialDisponible())return null;if(!G)return GM.horas_utc[h]?h:null;const t=soporte.utc(G.horas_utc[h]);let mejor=null,d=1e15;GM.horas_utc.forEach((x,k)=>{const e=Math.abs(soporte.utc(x)-t);if(e<d){d=e;mejor=k}});return d<=90*60000?mejor:null}
const varGlobal=v=>v==='viento_ms'||v==='viento_u_ms'||v==='viento_v_ms'?'viento':v;
function campoG(v,paso){if(paso===null)return null;if(v==='viento_ms'){const w=cacheG['viento|'+paso];if(!w)return null;return cacheG['vms|'+paso]??=w.viento_u_ms.map((f,i)=>f.map((u,j)=>{
  const v=w.viento_v_ms[i][j];return Number.isFinite(u)&&Number.isFinite(v)?Math.hypot(u,v):null;
}))}
  const c=cacheG[varGlobal(v)+'|'+paso];if(!c)return null;return v==='viento'?c:c[v]}
async function pedirGlobal(v,paso){const k=varGlobal(v)+'|'+paso;if(paso===null||cacheG[k]||pidiendo[k])return;pidiendo[k]=true;const corrida=GM?.corrida_utc;
  try{const r=await window.FuentesMeteo.fetch(`/api/global?var=${varGlobal(v)}&paso=${paso}`);const d=await json(r);if(r.ok&&GM?.corrida_utc===corrida&&d.corrida_utc===corrida){cacheG[k]=d;reiniciar(true);leyenda()}}catch(e){}finally{delete pidiendo[k]}}
function muestraG(M,lat,lon){if(!M)return null;const fi=(GM.latitudes[0]-lat)/(GM.latitudes[0]-GM.latitudes[1]),fj=(lon180(lon)-GM.longitudes[0])/(GM.longitudes[1]-GM.longitudes[0]);
  if(!(fi>=0&&fi<=M.length-1))return null;const n=M[0].length,i=Math.min(Math.floor(fi),M.length-2),j0=Math.floor(fj),a=fi-i,b=fj-j0,j=((j0%n)+n)%n,j1=(j+1)%n;
  return soporte.bilineal([M[i][j],M[i][j1],M[i+1][j],M[i+1][j1]],a,b)}
function valor(v,lat,lon,M,MG){let r=null,w=0;if(G&&M){const ij=indice(lat,lon);if(ij){r=bilineal(M,ij[0],ij[1]);w=borde(ij[0],ij[1])}}
  const g=MG?muestraG(MG,lat,lon):null;if(r===null)return g;if(g===null)return w>0?r:null;return r*w+g*(1-w)}

// Lienzo de color en el panel de superposición (se mueve con el mapa; se oculta durante el zoom).
const cT=document.createElement('canvas');cT.className='campo-temp leaflet-zoom-hide';cT.setAttribute('aria-hidden','true');cT.style.cssText='position:absolute;pointer-events:none';
const pane=mapa.getPanes().overlayPane;pane.insertBefore(cT,pane.firstChild);
const cP=document.createElement('canvas');cP.className='campo-particulas';cP.setAttribute('aria-hidden','true');cP.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:401';mapa.getContainer().append(cP);
const ctxP=cP.getContext('2d');

function pintarCampo(){
  const s=mapa.getSize();cT.style.width=s.x+'px';cT.style.height=s.y+'px';L.DomUtil.setPosition(cT,mapa.containerPointToLayerPoint([0,0]));cT.style.opacity=opacidad;
  if(!horasActivas().length||variable==='ninguna'){cT.width=1;cT.height=1;return}
  // Mercator: la latitud solo depende de y y la longitud solo de x.
  const paso=3,w=Math.ceil(s.x/paso),h=Math.ceil(s.y/paso),img=new ImageData(w,h),lats=new Float64Array(h),lons=new Float64Array(w);
  for(let y=0;y<h;y++)lats[y]=mapa.containerPointToLatLng([0,y*paso+paso/2]).lat;
  for(let x=0;x<w;x++)lons[x]=mapa.containerPointToLatLng([x*paso+paso/2,0]).lng;
  const M=G?campo(variable,hora):null,pg=pasoGlobal(),MG=campoG(variable,pg);if(GM&&pg!==null&&!MG)pedirGlobal(variable,pg);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const val=valor(variable,lats[y],lons[x],M,MG);if(val===null)continue;const c=color(variable,val);if(!c)continue;const k=(y*w+x)*4;img.data[k]=c[0];img.data[k+1]=c[1];img.data[k+2]=c[2];img.data[k+3]=Math.round(255*c[3])}
  const tmp=document.createElement('canvas');tmp.width=w;tmp.height=h;tmp.getContext('2d').putImageData(img,0,0);
  cT.width=Math.round(s.x*DPR);cT.height=Math.round(s.y*DPR);const ctx=cT.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(tmp,0,0,cT.width,cT.height);
}

// Partículas: campo de velocidad en píxeles precalculado (rejilla de 8 px); velocidad en pantalla constante con el zoom.
const CEL=8,ESC=.42;let FV=null;
function campoPantalla(){
  const s=mapa.getSize(),nx=Math.ceil(s.x/CEL)+1,ny=Math.ceil(s.y/CEL)+1,u=new Float32Array(nx*ny),v=new Float32Array(nx*ny),ok=new Uint8Array(nx*ny),rap=new Float32Array(nx*ny);
  const lats=[],lons=[];for(let y=0;y<ny;y++)lats.push(mapa.containerPointToLatLng([0,y*CEL]).lat);for(let x=0;x<nx;x++)lons.push(mapa.containerPointToLatLng([x*CEL,0]).lng);
  const U=G?G.variables.viento_u_ms[hora]:null,V=G?G.variables.viento_v_ms[hora]:null,pg=pasoGlobal(),W=campoG('viento',pg);if(GM&&pg!==null&&!W)pedirGlobal('viento',pg);
  const UG=W?W.viento_u_ms:null,VG=W?W.viento_v_ms:null;
  for(let y=0;y<ny;y++)for(let x=0;x<nx;x++){const uu=valor('u',lats[y],lons[x],U,UG),vv=valor('v',lats[y],lons[x],V,VG);if(uu===null||vv===null)continue;const k=y*nx+x;u[k]=uu*ESC;v[k]=-vv*ESC;rap[k]=Math.hypot(uu,vv);ok[k]=1}
  return {nx,ny,u,v,ok,rap,w:s.x,h:s.y};
}
function vel(x,y){const F=FV,gx=x/CEL,gy=y/CEL,i=Math.floor(gx),j=Math.floor(gy);if(i<0||j<0||i>=F.nx-1||j>=F.ny-1)return null;const k=j*F.nx+i;if(!(F.ok[k]&&F.ok[k+1]&&F.ok[k+F.nx]&&F.ok[k+F.nx+1]))return null;const a=gx-i,b=gy-j,f=A=>A[k]*(1-a)*(1-b)+A[k+1]*a*(1-b)+A[k+F.nx]*(1-a)*b+A[k+F.nx+1]*a*b;return[f(F.u),f(F.v),f(F.rap)]}
let px=null,py=null,edad=null,vida=null,N=0;
function nueva(k){for(let t=0;t<20;t++){const x=Math.random()*FV.w,y=Math.random()*FV.h;if(vel(x,y)){px[k]=x;py[k]=y;edad[k]=0;vida[k]=80+Math.random()*120|0;return}}px[k]=-1;edad[k]=0;vida[k]=10}
function sembrar(){if(!FV){N=0;return}N=Math.min(4500,Math.round(FV.w*FV.h/650));px=new Float32Array(N);py=new Float32Array(N);edad=new Uint16Array(N);vida=new Uint16Array(N);for(let k=0;k<N;k++){nueva(k);edad[k]=Math.random()*vida[k]|0}}
const TRAMOS=[[0,2,'rgba(255,255,255,.35)'],[2,5,'rgba(255,255,255,.55)'],[5,9,'rgba(255,255,255,.78)'],[9,1e9,'rgba(255,255,255,.95)']];
function frame(){
  raf=0;if(!FV||!conParticulas){ctxP.setTransform(1,0,0,1,0,0);ctxP.clearRect(0,0,cP.width,cP.height);return}
  ctxP.setTransform(DPR,0,0,DPR,0,0);ctxP.globalCompositeOperation='destination-out';ctxP.fillStyle='rgba(0,0,0,.05)';ctxP.fillRect(0,0,FV.w,FV.h);ctxP.globalCompositeOperation='source-over';ctxP.lineWidth=1.4;ctxP.lineCap='round';
  const caminos=TRAMOS.map(()=>new Path2D());
  for(let k=0;k<N;k++){if(px[k]<0||++edad[k]>vida[k]){nueva(k);continue}const q=vel(px[k],py[k]);if(!q){nueva(k);continue}const x2=px[k]+q[0],y2=py[k]+q[1];let t=0;while(q[2]>=TRAMOS[t][1])t++;caminos[t].moveTo(px[k],py[k]);caminos[t].lineTo(x2,y2);px[k]=x2;py[k]=y2}
  TRAMOS.forEach((tr,t)=>{ctxP.strokeStyle=tr[2];ctxP.stroke(caminos[t])});
  if(!reducido&&!document.hidden&&!enGlobo())raf=requestAnimationFrame(frame);
}
function estatico(){ctxP.setTransform(1,0,0,1,0,0);ctxP.clearRect(0,0,cP.width,cP.height);if(!FV||!conParticulas)return;ctxP.setTransform(DPR,0,0,DPR,0,0);ctxP.lineWidth=1.2;ctxP.strokeStyle='rgba(255,255,255,.7)';const c=new Path2D();for(let k=0;k<Math.min(N,900);k++){let x=px[k],y=py[k];if(x<0)continue;c.moveTo(x,y);for(let s=0;s<16;s++){const q=vel(x,y);if(!q)break;x+=q[0]*1.5;y+=q[1]*1.5;c.lineTo(x,y)}}ctxP.stroke(c)}
function tamano(){const s=mapa.getSize();cP.width=Math.round(s.x*DPR);cP.height=Math.round(s.y*DPR)}
const ley=$('leyenda-campo');
const pantallaCorta=matchMedia('(max-width:700px), (max-height:700px)');
let leyendaElegida=null;
pantallaCorta.addEventListener('change',()=>{if(leyendaElegida===null)leyenda()});

// Indicador en la cabecera: modelo y hora de la corrida.
const ind=$('indicador-datos'),indDet=$('indicador-detalle');
let globalListo=false;
const fechaCorta=iso=>new Date(soporte.utc(iso)).toLocaleString('en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'UTC'})+' UTC';
function indicador(){
  if(!ind)return;
  let nivel,txt;
  if(mundialDisponible()){nivel='ok';txt='ECMWF IFS · '+fechaCorta(GM.corrida_utc)}
  else if(!globalListo){nivel='pendiente';txt='Loading data…'}
  else{nivel='error';txt='No model data'}
  ind.dataset.nivel=nivel;texto('indicador-texto',txt);
  const items=[['Model','ECMWF IFS · global 1° · 3-hourly'+(G?' · regional 0.25° · hourly':'')],['Run',GM?fechaCorta(GM.corrida_utc):'—'],['Shown',horasActivas()[hora]?fechaCorta(horasActivas()[hora]):'—'],['Imagery','NASA GIBS · Blue Marble, GOES-East, IMERG, MODIS']];
  const dl=document.createElement('dl');items.forEach(([k,v])=>{const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=k;dd.textContent=v;dl.append(dt,dd)});
  indDet.replaceChildren(dl);
}
if(ind){
  const abrir=v=>{indDet.hidden=!v;ind.setAttribute('aria-expanded',String(v))};
  ind.onclick=e=>{e.stopPropagation();abrir(indDet.hidden)};
  indDet.onclick=e=>e.stopPropagation();
  document.addEventListener('click',()=>abrir(false));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!indDet.hidden){abrir(false);ind.focus()}});
}
// conservar=true: al cambiar de hora o de capa se mantienen las partículas (solo cambia el campo de velocidad).
function reiniciar(conservar){
  indicador();
  cancelAnimationFrame(raf);raf=0;
  const hayCampo=horasActivas().length>0;
  ley.hidden=!hayCampo||variable==='ninguna';
  if(enGlobo()){ctxP.setTransform(1,0,0,1,0,0);ctxP.clearRect(0,0,cP.width,cP.height);return}
  pintarCampo();
  if(conservar&&FV&&hayCampo&&N){FV=campoPantalla()}else{tamano();ctxP.setTransform(1,0,0,1,0,0);ctxP.clearRect(0,0,cP.width,cP.height);FV=hayCampo?campoPantalla():null;sembrar()}
  if(reducido)estatico();else raf=requestAnimationFrame(frame);
}
mapa.on('movestart zoomstart',()=>{cancelAnimationFrame(raf);raf=0;cP.style.visibility='hidden'});
mapa.on('moveend zoomend resize',()=>{cP.style.visibility='';reiniciar()});
document.addEventListener('visibilitychange',()=>{cancelAnimationFrame(raf);raf=0;if(!document.hidden&&!reducido&&FV&&!enGlobo())raf=requestAnimationFrame(frame)});
mqReducido.addEventListener?.('change',e=>{reducido=e.matches;if(FV&&!enGlobo())reiniciar(true)});
document.addEventListener('sicc:vista',()=>reiniciar());

// Leyenda
function leyenda(){
  indicador();
  if(variable==='ninguna'||!horasActivas().length){ley.hidden=true;return}
  const E=ESCALAS[variable],T=E.tramos,pos=x=>E.log?(Math.log(x)-Math.log(T[0][0]))/(Math.log(T.at(-1)[0])-Math.log(T[0][0])):(x-T[0][0])/(T.at(-1)[0]-T[0][0]);
  const grad=T.map(t=>`rgba(${t[1].join(',')},${t[2]===undefined?1:Math.max(.25,t[2])}) ${(pos(t[0])*100).toFixed(1)}%`).join(',');
  const expandida=leyendaElegida===null?!pantallaCorta.matches:leyendaElegida;
  ley.classList.toggle('minimizada',!expandida);
  ley.replaceChildren();
  const bar=document.createElement('div');bar.className='ventana-barra';const tt=document.createElement('button');tt.type='button';tt.className='leyenda-alternar';tt.setAttribute('aria-expanded',String(expandida));tt.setAttribute('aria-controls','cuerpo-leyenda-meteo');
  const rotulo=a=>`${a?'▾':'▸'} ${E.nombre} · ${E.unidad}`;tt.textContent=rotulo(expandida);
  tt.onclick=()=>{leyendaElegida=ley.classList.contains('minimizada');ley.classList.toggle('minimizada',!leyendaElegida);tt.setAttribute('aria-expanded',String(leyendaElegida));tt.textContent=rotulo(leyendaElegida)};bar.append(tt);
  const cuerpo=document.createElement('div');cuerpo.className='ventana-cuerpo';cuerpo.id='cuerpo-leyenda-meteo';
  const g=document.createElement('div');g.className='gradiente';g.style.background=`linear-gradient(90deg,${grad})`;
  const et=document.createElement('div');et.className='etiquetas';E.etiquetas.forEach(t=>{const s=document.createElement('span');s.textContent=String(t);s.style.left=`${pos(t)*100}%`;et.append(s)});
  const lec=document.createElement('p');lec.id='lectura';lec.className='lectura';
  cuerpo.append(g,et,lec);ley.append(bar,cuerpo);
}

// Lectura bajo el cursor (mapa 2D)
const PUNTOS=['N','NE','E','SE','S','SW','W','NW'];let lecturaPend=null,lecturaProg=false;
function dirDe(u,v){return PUNTOS[Math.round(((Math.atan2(-u,-v)*180/Math.PI+360)%360)/45)%8]}
const fmt=(x,d=1)=>Number.isFinite(x)?x.toFixed(d):'—';
mapa.on('mousemove',e=>{lecturaPend=e.latlng;if(lecturaProg)return;lecturaProg=true;requestAnimationFrame(()=>{lecturaProg=false;const ll=lecturaPend,l=$('lectura');if(!l||!ll)return;
  const pos=`${Math.abs(ll.lat).toFixed(1)}°${ll.lat>=0?'N':'S'} ${Math.abs(lon180(ll.lng)).toFixed(1)}°${lon180(ll.lng)>=0?'E':'W'}`;
  const t=muestra('temperatura_c',ll.lat,ll.lng);
  if(t===null){const pg=pasoGlobal();if(pg===null){l.textContent=pos;return}
    const f=k=>{const M=campoG(k,pg);return M?muestraG(M,ll.lat,ll.lng):null},tg=f('temperatura_c'),W=campoG('viento',pg),ug=W?muestraG(W.viento_u_ms,ll.lat,ll.lng):null,vg=W?muestraG(W.viento_v_ms,ll.lat,ll.lng):null,vs=f(variable==='viento_ms'?'viento_ms':variable);
    l.textContent=`${pos} · ${tg!==null?tg.toFixed(1)+' °C':'—'}${ug!==null&&vg!==null?` · wind ${Math.hypot(ug,vg).toFixed(1)} m/s ${dirDe(ug,vg)}`:''}${variable!=='temperatura_c'&&variable!=='viento_ms'&&ESCALAS[variable]&&vs!==null?` · ${ESCALAS[variable].nombre.toLowerCase()} ${vs.toFixed(variable==='precipitacion_mm'?1:0)} ${ESCALAS[variable].unidad}`:''}`;return}
  const m=k=>muestra(k,ll.lat,ll.lng),u=m('viento_u_ms'),v=m('viento_v_ms');
  l.textContent=`${pos} · ${t.toFixed(1)} °C · rain ${fmt(m('precipitacion_mm'))} mm/h · wind ${u!==null&&v!==null?Math.hypot(u,v).toFixed(1)+' m/s '+dirDe(u,v):'—'} · clouds ${fmt(m('nubes_pct'),0)}% · RH ${fmt(m('humedad_pct'),0)}% · ${fmt(m('presion_hpa'),0)} hPa`})});

// Línea de tiempo
const lt=$('lt-rango'),ltEt=$('lt-etiqueta'),ltPlay=$('lt-play'),ltAhora=$('lt-ahora');
function fechaLocal(iso){return new Date(soporte.utc(iso)).toLocaleString('en-US',{weekday:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false})}
function indiceAhora(){
  if(G){const actual=new Date().toISOString().slice(0,13)+':00';const i=G.horas_utc.indexOf(actual);return i<0?G.indice_actual:i}
  return Math.max(0,horasActivas().findLastIndex(h=>soporte.utc(h)<=Date.now()));
}
function relativa(i){
  const H=horasActivas(),t=soporte.utc(H[i]);if(!Number.isFinite(t))return '';
  const d=Math.round((t-Date.now())/3600000);
  if(i===indiceAhora())return 'now';
  return (d>0?'+':'−')+Math.abs(d)+' h';
}
function etiquetaHora(){
  const iso=horasActivas()[hora];
  if(!iso){ltEt.textContent='No forecast data';return}
  const principal=document.createElement('strong');principal.textContent=fechaLocal(iso)+' · '+relativa(hora);
  const detalle=document.createElement('small');detalle.textContent='ECMWF IFS · '+iso.slice(11,16)+' UTC';
  ltEt.replaceChildren(principal,detalle);
  indicador();
}
// Marcas bajo el deslizador: cambio de día (hora local del visitante) y la hora actual.
const ltMarcas=$('lt-marcas');
function marcas(){
  if(!ltMarcas)return;
  const H=horasActivas(),n=H.length,pos=i=>`calc(8px + (100% - 16px) * ${n>1?i/(n-1):0})`;
  ltMarcas.replaceChildren();
  if(!n)return;
  let dia=null;
  H.forEach((iso,i)=>{const f=new Date(soporte.utc(iso)),d=f.toDateString();if(d===dia)return;const nuevo=dia!==null;dia=d;if(!nuevo)return;
    const m=document.createElement('span');m.className='lt-dia';m.style.left=pos(i);m.textContent=f.toLocaleDateString('en-US',{weekday:'short',day:'numeric'});ltMarcas.append(m)});
  let ia=indiceAhora();
  if(ia<n-1){const t0=soporte.utc(H[ia]),t1=soporte.utc(H[ia+1]);if(t1>t0)ia+=Math.min(1,Math.max(0,(Date.now()-t0)/(t1-t0)))}
  const a=document.createElement('span');a.className='lt-ahora';a.style.left=pos(ia);ltMarcas.append(a);
}
function ajustarTiempo(iso,seguirAhora){
  const horas=horasActivas();
  lt.disabled=ltPlay.disabled=ltAhora.disabled=!horas.length;
  marcas();
  if(!horas.length){parar();etiquetaHora();return}
  const i=seguirAhora?-1:horas.indexOf(iso);
  hora=i<0?indiceAhora():i;
  lt.max=horas.length-1;lt.value=hora;etiquetaHora();
}
let pendienteHora=false;
function ponerHora(h){
  const horas=horasActivas();
  if(!horas.length){ajustarTiempo();reiniciar();leyenda();return}
  hora=Math.max(0,Math.min(horas.length-1,h));lt.value=hora;etiquetaHora();
  if(pendienteHora)return;
  pendienteHora=true;
  requestAnimationFrame(()=>{pendienteHora=false;reiniciar(true);leyenda();document.dispatchEvent(new CustomEvent('sicc:hora',{detail:hora}))});
}
lt.oninput=e=>{parar();ponerHora(Number(e.target.value))};
function parar(){if(reproducir){clearInterval(reproducir);reproducir=null}ltPlay.textContent='▶';ltPlay.setAttribute('aria-label','Play forecast')}
ltPlay.onclick=()=>{if(reproducir)return parar();if(!horasActivas().length)return;ltPlay.textContent='❚❚';ltPlay.setAttribute('aria-label','Pause');reproducir=setInterval(()=>ponerHora(hora+1>=horasActivas().length?0:hora+1),G?700:1100)};
ltAhora.onclick=()=>{parar();ponerHora(indiceAhora())};

// Selector de capas
document.querySelectorAll('#barra-capas [data-var]').forEach(b=>b.onclick=()=>{variable=b.dataset.var;document.querySelectorAll('#barra-capas [data-var]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));leyenda();reiniciar(true);avisar('sicc:capa')});
$('chk-particulas').onchange=e=>{conParticulas=e.target.checked;reiniciar()};
const op=$('opacidad-temp');if(op){opacidad=Number(op.value)/100;op.oninput=e=>{opacidad=Number(e.target.value)/100;cT.style.opacity=opacidad}}

async function cargar(){
  try{
    const r=await window.FuentesMeteo.fetch('/api/campo_nicaragua'),d=await json(r);
    if(!r.ok)throw Error(d.error||'Regional grid unavailable');
    // Una instantánea vieja no cubre la hora actual: mejor la malla mundial vigente que una hora pasada.
    if(!d.horas_utc?.length||soporte.utc(d.horas_utc.at(-1))<Date.now())throw Error('Regional grid expired');
    const iso=G?.horas_utc[hora],seguirAhora=!G||hora===G.indice_actual;
    G=d;
    for(const k in cacheViento)delete cacheViento[k];
    ajustarTiempo(iso,seguirAhora);
  }catch(e){
    const iso=G?null:horasActivas()[hora];
    if(G)parar();
    G=null;
    ajustarTiempo(iso);
  }finally{
    reiniciar();leyenda();avisar('sicc:campo');
  }
}
let cargandoGlobal=false;
async function cargarGlobal(){
  if(cargandoGlobal)return;
  cargandoGlobal=true;
  try{
    const r=await window.FuentesMeteo.fetch('/api/global_meta'),d=await json(r);
    if(!r.ok)throw Error(d.error||'No global metadata');
    const iso=horasActivas()[hora],seguirAhora=hora===indiceAhora();
    if(GM?.corrida_utc!==d.corrida_utc)for(const k in cacheG)delete cacheG[k];
    GM=d;
    if(!G)ajustarTiempo(iso,seguirAhora);
  }catch(e){
    GM=null;
    for(const k in cacheG)delete cacheG[k];
    if(!G)ajustarTiempo();
  }finally{
    cargandoGlobal=false;globalListo=true;
    reiniciar(true);leyenda();avisar('sicc:campo');
  }
}
cargarGlobal();setInterval(()=>{if(!document.hidden)cargarGlobal()},30*60000);

window.SICC_campo={
  estado:()=>({datos:!!G,variable,hora,horaUTC:horasActivas()[hora]??null,particulas:N,mundial:GM?{corrida:GM.corrida_utc,paso:pasoGlobal(),horaGlobal:pasoGlobal()!==null?GM.horas_utc[pasoGlobal()]:null}:null}),
  meta:()=>GM,
  hora:()=>hora,
  datos:()=>G
};
cargar();setInterval(()=>{if(!document.hidden)cargar()},REFRESCO_MIN*60000);
})();
