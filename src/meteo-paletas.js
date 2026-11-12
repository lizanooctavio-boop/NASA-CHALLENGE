(function () {
'use strict';
const ESCALAS={
  temperatura_c:{nombre:'Temperatura a 2 m',unidad:'°C',etiquetas:[12,16,20,24,28,32,37],
    tramos:[[12,[59,44,140]],[16,[46,94,196]],[19,[38,150,214]],[22,[46,190,170]],[24,[110,204,110]],[26,[198,222,82]],[28,[252,212,72]],[30,[252,160,48]],[32,[240,104,46]],[34,[214,48,54]],[37,[160,22,82]]]},
  precipitacion_mm:{nombre:'Lluvia · intensidad media',unidad:'mm/h',minimo:.1,log:true,etiquetas:[.1,.5,1,2,5,10,20,40],
    tramos:[[.1,[150,205,255],.45],[.5,[90,165,250],.7],[1,[40,110,235],.8],[2,[30,175,120],.85],[5,[245,225,40],.9],[10,[250,140,30],.92],[20,[225,35,55],.95],[40,[175,35,175],.95]]},
  viento_ms:{nombre:'Viento a 10 m',unidad:'m/s',etiquetas:[0,3,6,9,12,16,22,30],
    tramos:[[0,[42,58,128]],[3,[40,128,196]],[6,[52,182,140]],[9,[214,214,64]],[12,[240,150,40]],[16,[218,56,50]],[22,[150,36,140]],[30,[235,225,240]]]},
  rafagas_ms:{nombre:'Ráfagas a 10 m',unidad:'m/s',etiquetas:[0,5,10,14,18,23,30,40],
    tramos:[[0,[42,58,128]],[5,[40,128,196]],[10,[52,182,140]],[14,[214,214,64]],[18,[240,150,40]],[23,[218,56,50]],[30,[150,36,140]],[40,[235,225,240]]]},
  nubes_pct:{nombre:'Nubosidad total',unidad:'%',etiquetas:[0,25,50,75,100],
    tramos:[[0,[40,60,90],0],[20,[150,165,185],.25],[50,[200,208,220],.55],[80,[232,236,242],.78],[100,[250,251,253],.9]]},
  humedad_pct:{nombre:'Humedad relativa',unidad:'%',etiquetas:[20,40,60,80,100],
    tramos:[[20,[170,110,60]],[40,[222,196,120]],[60,[150,206,150]],[75,[70,175,190]],[90,[40,110,205]],[100,[34,54,160]]]},
  presion_hpa:{nombre:'Presión a nivel del mar',unidad:'hPa',etiquetas:[996,1004,1008,1012,1016,1020],
    tramos:[[996,[110,40,150]],[1004,[50,100,200]],[1008,[50,170,190]],[1011,[110,200,110]],[1013,[240,220,70]],[1016,[245,150,50]],[1020,[210,50,50]]]}
};
function color(v,x,E=ESCALAS[v],normalizado=false){const T=E.tramos;if(normalizado)x=T[0][0]+x*(T.at(-1)[0]-T[0][0]);if(E.minimo!==undefined&&x<E.minimo)return null;
  const val=t=>[t[1][0],t[1][1],t[1][2],t[2]===undefined?1:t[2]];
  if(x<=T[0][0])return val(T[0]);if(x>=T.at(-1)[0])return val(T.at(-1));
  for(let i=1;i<T.length;i++)if(x<=T[i][0]){const a=val(T[i-1]),b=val(T[i]),t=(x-T[i-1][0])/(T[i][0]-T[i-1][0]);return a.map((c,k)=>c+(b[k]-c)*t)}}
window.PaletasMeteo = { escalas: ESCALAS, color };
})();
