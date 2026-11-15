// Gráficas con Chart.js 4.4.1: pronóstico puntual, ENOS y escenarios CMIP6.
(function(){
const $=id=>document.getElementById(id);
if(!window.Chart){window.SICC_graf={estado:()=>({chart:false})};return}
Chart.defaults.color='#a9b8c9';Chart.defaults.borderColor='rgba(255,255,255,.09)';Chart.defaults.font.family='system-ui,"Segoe UI",sans-serif';Chart.defaults.font.size=11;
Chart.defaults.plugins.legend.labels.boxWidth=12;Chart.defaults.maintainAspectRatio=false;Chart.defaults.animation.duration=300;
const C={cian:'#6fd8ff',ambar:'#f6c76b',rojo:'#ff7b6b',verde:'#6fe0a0',violeta:'#b493ff',gris:'#9db0c6',azul:'#4f8fe8'};
const SSP={ssp126:C.verde,ssp245:C.cian,ssp370:C.ambar,ssp585:C.rojo};
const NOMBRE_SSP={ssp126:'SSP1-2.6',ssp245:'SSP2-4.5',ssp370:'SSP3-7.0',ssp585:'SSP5-8.5'};
const graficas={};
function crear(id,config){const c=$(id);if(!c)return null;graficas[id]?.destroy();graficas[id]=new Chart(c,config);return graficas[id]}
const eje=(titulo,extra={})=>({title:{display:true,text:titulo},...extra});
const signo=(v,d=1)=>(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(d);
const extremos=a=>{const v=a.filter(x=>x!==null&&x!==undefined&&Number.isFinite(Number(x))).map(Number);return v.length?v.reduce(([mn,mx],x)=>[Math.min(mn,x),Math.max(mx,x)],[Infinity,-Infinity]):null};
let S=null;

// ---------------------------------------------------------------- escenarios
function escenarios(){
  const ventana=$('ventana-cmip').value,ssp=$('ssp').value;
  const filas=S.proyecciones.filter(f=>f.ventana===ventana);
  const anios=[...new Set(filas.map(f=>f.anio))].sort((a,b)=>a-b);
  for(const [id,clave,unidad,dec,titulo] of [['graf-dT','dT','°C',1,'Projected warming'],['graf-dP','dP','%',0,'Projected precipitation change']]){
    crear(id,{type:'line',data:{labels:anios,datasets:Object.keys(SSP).map(s=>({
      label:NOMBRE_SSP[s],data:anios.map(a=>filas.find(f=>f.escenario===s&&f.anio===a)?.[clave]??null),
      borderColor:SSP[s],borderWidth:s===ssp?3:1.2,pointRadius:0,tension:.2
    }))},options:{scales:{y:eje(unidad)}}});
    const r=extremos(filas.map(f=>f[clave])),fin=filas.filter(f=>f.escenario===ssp).sort((a,b)=>b.anio-a.anio)[0];
    if(r&&anios.length){
      const finTxt=fin&&Number.isFinite(Number(fin[clave]))?`, active scenario ${NOMBRE_SSP[ssp]} reaches ${signo(Number(fin[clave]),dec)} ${unidad} by ${fin.anio}`:'';
      $(id)?.setAttribute('aria-label',`${titulo} from ${anios[0]} to ${anios.at(-1)} for ${ventana}${finTxt}; range across scenarios ${signo(r[0],dec)} to ${signo(r[1],dec)} ${unidad}`);
    }
  }
  const cont=$('cambios');cont.replaceChildren();
  [2040,2060,2080,2100].forEach(meta=>{
    const f=filas.filter(x=>x.escenario===ssp).sort((a,b)=>Math.abs(a.anio-meta)-Math.abs(b.anio-meta))[0];if(!f)return;
    tarjeta(cont,String(f.anio),`${signo(f.dT)} °C`,`${signo(f.dP,0)} % precipitation`);
  });
}

// ---------------------------------------------------------------- ENOS
document.addEventListener('sicc:enos',e=>{const d=e.detail;
  const f=d.oni_local.filter(x=>x.oni!==null);
  crear('graf-oni',{type:'bar',data:{labels:f.map(x=>`${x.anio}-${String(x.mes).padStart(2,'0')}`),datasets:[{label:'ONI (°C)',data:f.map(x=>x.oni),backgroundColor:f.map(x=>x.oni>=.5?'rgba(255,123,107,.85)':x.oni<=-.5?'rgba(79,143,232,.85)':'rgba(157,176,198,.45)'),borderWidth:0,barPercentage:1,categoryPercentage:1}]},
    options:{plugins:{legend:{display:false},subtitle:{display:true,text:'Red: El Niño (≥ +0.5) · Blue: La Niña (≤ −0.5)'}},scales:{x:{ticks:{maxTicksLimit:16,autoSkip:true}},y:eje('°C')}}});
  if(f.length){
    const rOni=extremos(f.map(x=>x.oni)),ult=f.at(-1),fase=ult.oni>=.5?'El Niño':ult.oni<=-.5?'La Niña':'Neutral';
    $('graf-oni')?.setAttribute('aria-label',`Oceanic Niño Index from ${f[0].anio} to ${ult.anio}. Range ${signo(rOni[0],2)} to ${signo(rOni[1],2)} °C; latest ${ult.anio}-${String(ult.mes).padStart(2,'0')} is ${signo(ult.oni,2)} °C (${fase})`);
  }
  const s=d.nino34_semanal?.semanas||[];
  crear('graf-nino34',{type:'line',data:{labels:s.map(x=>x.semana),datasets:[['nino12','Niño 1+2',C.rojo],['nino3','Niño 3',C.ambar],['nino34','Niño 3.4',C.cian],['nino4','Niño 4',C.violeta]].map(([k,n,c])=>({label:n,data:s.map(x=>x[k]),borderColor:c,pointRadius:0,borderWidth:k==='nino34'?2.6:1.4}))},
    options:{interaction:{mode:'index',intersect:false},scales:{y:eje('Weekly anomaly (°C)')}}});
  if(s.length){
    const r34=extremos(s.map(x=>x.nino34)),ult34=s.at(-1);
    const desc34=r34&&ult34.nino34!=null?`; Niño 3.4 range ${signo(r34[0],2)} to ${signo(r34[1],2)} °C, latest ${signo(ult34.nino34,2)} °C`:'';
    $('graf-nino34')?.setAttribute('aria-label',`Weekly sea temperature anomalies by Niño region from ${s[0].semana} to ${ult34.semana}${desc34}`);
  }
});

// ---------------------------------------------------------------- pronóstico del punto elegido
document.addEventListener('sicc:pronostico',e=>{
  const p=e.detail,caja=$('graf-meteograma').parentElement;
  caja.hidden=!p?.horas;
  if(!p?.horas){graficas['graf-meteograma']?.destroy();delete graficas['graf-meteograma'];return}
  const h=p.horas,etiquetas=h.time.map(t=>new Date(t+'Z').toLocaleString('en-US',{weekday:'short',hour:'2-digit',hour12:false}));
  const rT=extremos(h.temperature_2m||[]),rP=extremos(h.precipitation||[]),rG=extremos(h.wind_gusts_10m||[]);
  $('graf-meteograma')?.setAttribute('aria-label',`Hourly forecast at ${Math.abs(p.lat).toFixed(2)}° ${p.lat>=0?'N':'S'}, ${Math.abs(p.lon).toFixed(2)}° ${p.lon>=0?'E':'W'}${rT?`, temperature ${rT[0].toFixed(1)} to ${rT[1].toFixed(1)} °C`:''}${rP?`, peak rainfall ${rP[1].toFixed(1)} mm/h`:''}${rG?`, peak wind gusts ${rG[1].toFixed(1)} m/s`:''}`);
  crear('graf-meteograma',{data:{labels:etiquetas,datasets:[
    {type:'line',label:'Temperature (°C)',data:h.temperature_2m,borderColor:C.ambar,pointRadius:0,tension:.3,yAxisID:'y'},
    {type:'bar',label:'Rain (mm/h)',data:h.precipitation,backgroundColor:'rgba(79,143,232,.75)',yAxisID:'y1'},
    {type:'line',label:'Gusts (m/s)',data:h.wind_gusts_10m,borderColor:C.violeta,borderDash:[3,3],pointRadius:0,yAxisID:'y2'}]},
    options:{interaction:{mode:'index',intersect:false},scales:{x:{ticks:{maxTicksLimit:9}},y:eje('°C'),y1:eje('mm/h',{position:'right',grid:{drawOnChartArea:false},min:0}),y2:{display:false,min:0}}}});
});

window.FuentesMeteo.fetch('/api/series').then(r=>r.json().then(d=>{if(!r.ok)throw Error(d.error);S=d;const selector=$('ventana-cmip');[...new Set(S.proyecciones.map(f=>f.ventana))].forEach(v=>selector.add(new Option(v,v)));escenarios()})).catch(()=>{});
['ssp','ventana-cmip'].forEach(id=>$(id)?.addEventListener('change',()=>S&&escenarios()));
// Chart.js no dibuja bien en lienzos ocultos: se redimensiona al cambiar de pestaña.
document.addEventListener('sicc:pestana',()=>setTimeout(()=>Object.values(graficas).forEach(g=>g.resize()),30));
window.SICC_graf={estado:()=>({chart:true,graficas:Object.keys(graficas)})};
})();
