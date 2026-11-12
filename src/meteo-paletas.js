(function () {
'use strict';
// Escalas mundiales compartidas por el globo 3D, el mapa 2D y sus leyendas.
const ESCALAS={
  temperatura_c:{nombre:'Temperature at 2 m',unidad:'°C',etiquetas:[-40,-20,-10,0,10,20,30,40],
    tramos:[[-50,[221,240,250]],[-35,[172,193,249]],[-20,[86,105,204]],[-8,[29,129,199]],[0,[63,196,218]],[10,[128,206,142]],[20,[254,218,90]],[28,[250,153,47]],[34,[229,71,42]],[40,[161,22,55]],[46,[85,12,42]]]},
  precipitacion_mm:{nombre:'Rain rate',unidad:'mm/h',minimo:.1,log:true,etiquetas:[.1,.5,1,2,5,10,20,40],
    tramos:[[.1,[150,205,255],.45],[.5,[90,165,250],.7],[1,[40,110,235],.8],[2,[30,175,120],.85],[5,[245,225,40],.9],[10,[250,140,30],.92],[20,[225,35,55],.95],[40,[175,35,175],.95]]},
  viento_ms:{nombre:'Wind at 10 m',unidad:'m/s',etiquetas:[0,3,6,9,12,16,22,30],
    tramos:[[0,[42,58,128]],[3,[40,128,196]],[6,[52,182,140]],[9,[214,214,64]],[12,[240,150,40]],[16,[218,56,50]],[22,[150,36,140]],[30,[235,225,240]]]},
  rafagas_ms:{nombre:'Wind gusts',unidad:'m/s',etiquetas:[0,5,10,14,18,23,30,40],
    tramos:[[0,[42,58,128]],[5,[40,128,196]],[10,[52,182,140]],[14,[214,214,64]],[18,[240,150,40]],[23,[218,56,50]],[30,[150,36,140]],[40,[235,225,240]]]},
  nubes_pct:{nombre:'Cloud cover',unidad:'%',etiquetas:[0,25,50,75,100],
    tramos:[[0,[40,60,90],0],[20,[150,165,185],.25],[50,[200,208,220],.55],[80,[232,236,242],.78],[100,[250,251,253],.9]]},
  humedad_pct:{nombre:'Relative humidity',unidad:'%',etiquetas:[20,40,60,80,100],
    tramos:[[20,[170,110,60]],[40,[222,196,120]],[60,[150,206,150]],[75,[70,175,190]],[90,[40,110,205]],[100,[34,54,160]]]},
  presion_hpa:{nombre:'Sea-level pressure',unidad:'hPa',etiquetas:[980,995,1005,1013,1020,1035],
    tramos:[[975,[110,40,150]],[995,[50,100,200]],[1005,[50,170,190]],[1010,[110,200,110]],[1015,[240,220,70]],[1022,[245,150,50]],[1040,[210,50,50]]]}
};
function color(v,x,E=ESCALAS[v],normalizado=false){const T=E.tramos;if(normalizado)x=T[0][0]+x*(T.at(-1)[0]-T[0][0]);if(E.minimo!==undefined&&x<E.minimo)return null;
  const val=t=>[t[1][0],t[1][1],t[1][2],t[2]===undefined?1:t[2]];
  if(x<=T[0][0])return val(T[0]);if(x>=T.at(-1)[0])return val(T.at(-1));
  for(let i=1;i<T.length;i++)if(x<=T[i][0]){const a=val(T[i-1]),b=val(T[i]),t=(x-T[i-1][0])/(T[i][0]-T[i-1][0]);return a.map((c,k)=>c+(b[k]-c)*t)}}
window.PaletasMeteo = { escalas: ESCALAS, color };
})();
