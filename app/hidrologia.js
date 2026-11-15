// Cuencas de referencia, catálogo nacional y observaciones con sus fechas originales.
(function(){
  'use strict';
  const $=id=>document.getElementById(id), H=window.HidrologiaDatos;
  const regiones={af:'Africa',ar:'North American Arctic',as:'Asia',au:'Australia and Oceania',eu:'Europe and Middle East',gr:'Greenland',na:'North and Central America and Caribbean',sa:'South America',si:'Siberia'};
  const WFS='https://mapserveride.ineter.gob.ni/geoserver/ows';
  // Solo nombres publicados en GetCapabilities; no se aceptan URL proporcionadas por el usuario.
  const referencias=[
    ['Climate regions','wsINETER-DGMT:Regiones_Climaticas','Reference climate classification; period not specified in the catalogue.'],
    ['Annual precipitation map','wsINETER-DGMT:Precipitacion_Anual','Reference rainfall map; do not treat it as a time series.'],
    ['Annual temperature map','wsINETER-DGMT:Temperatura_Anual','Reference temperature map; observation period must be checked in the source.'],
    ['Drought hazard','wsINETER-DGMT:Amenaza_Sequia','Historical hazard map, not a current drought observation.'],
    ['Extreme rainfall hazard · 2022 edition','wsINETER-DGMT:Lluvias_AmenEx_Anual_2022','2022 map edition; not a detected change or a current warning.'],
    ['Flood susceptibility · 2021 edition','wsINETER-RH:Mapa_Nacional_Susceptible_Inundacion_2021','Susceptibility reference map, not an active flood footprint.'],
    ['Historical flood hazard','wsINETER-DGRH:Amenaza_Inundacion_Historica','Historical mapped hazard; no annual trend is inferred.'],
    ['Landslides · reference polygons','wsINETER-DGGG:Deslizamiento_Nicaragua_Poligonos','Mapped landslides; event dates and completeness require source checks.'],
    ['Groundwater management units · 2022','wsINETER-DGRH:UnidadGestionAguaSubterranea_2022','Management boundaries, not measured groundwater storage.'],
    ['Hydrological monitoring network','wsINETER-DGRH:Estaciones_Hidrologicas','Station locations, not current readings.'],
  ];
  let manifiesto=null, catalogo=null, sinapred=null, fc=null, estaciones=null, cuencas=null, puntos=null, referencia=null;
  let secuencia=0, secEst=0, visible=false, estacionesVisibles=false, activa=false;
  const cache=new Map(), etiquetas=L.layerGroup();
  const el=(tag,t)=>{const n=document.createElement(tag);if(t!=null)n.textContent=t;return n;};
  const texto=(id,t)=>{$(id).textContent=t;};
  function fuenteWFS(tipo){const q=new URLSearchParams({service:'WFS',version:'2.0.0',request:'GetFeature',typeNames:tipo,outputFormat:'application/json',srsName:'CRS:84'});return WFS+'?'+q;}
  async function json(url){const r=await fetch(url,{signal:AbortSignal.timeout(35000)});if(!r.ok)throw Error('HTTP '+r.status);
    if(url.endsWith('.gz')){
      if(typeof DecompressionStream==='undefined')throw Error('This browser needs gzip stream support; download the original vectors instead');
      // Algunos servidores descomprimen automáticamente con Content-Encoding: gzip.
      const b=new Uint8Array(await r.arrayBuffer());
      if(b[0]!==31||b[1]!==139)return JSON.parse(new TextDecoder().decode(b));
      return new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
    }return r.json();}
  async function datos(url){if(!cache.has(url))cache.set(url,json(url).catch(e=>{cache.delete(url);throw e;}));return cache.get(url);}
  function descargar(texto,nombre,tipo){const u=URL.createObjectURL(new Blob([texto],{type:tipo})),a=el('a');a.href=u;a.download=nombre;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  function atributos(p,titulo){const d=el('div');d.append(el('strong',titulo));const dl=el('dl');
    for(const [k,v] of Object.entries(p)){if(v!==null&&typeof v==='object')continue;dl.append(el('dt',k),el('dd',v===null?'Unavailable':String(v)));}d.append(dl);return d;}
  function detalle(f,capa){const p=f.properties,d=$('hid-detalle');d.replaceChildren();
    d.append(el('h3','Complete source code: '+H.codigo(p)),el('p',p.sistema));
    if(p.HYBAS_ID)d.append(el('p','HYBAS_ID (separate identifier): '+p.HYBAS_ID));
    if(p.n3)d.append(el('p','Published components: '+[3,4,5,6,7].map(n=>'n'+n+'='+p['n'+n]).join(' · ')));
    if(p.codigo_discrepa)d.append(el('p','Code from the published components: '+p.codigo_componentes),el('p','Source inconsistency: code_pfafs differs from the published n3–n7 components. Both are retained; neither is corrected.'));
    if(capa){seleccionada=capa;cuencas?.resetStyle();resaltar();}
  }
  function buscar(){const fs=H.buscar(fc?.features??[],$('hid-buscar').value),c=$('hid-resultados');c.replaceChildren();
    fs.slice(0,100).forEach(f=>{const li=el('li'),b=el('button',H.codigo(f.properties)+' · '+(f.properties.cuencas||f.properties.HYBAS_ID||'Watershed'));b.type='button';b.onclick=()=>{let encontrado;cuencas?.eachLayer(l=>{if(l.feature===f)encontrado=l;});detalle(f,encontrado);if(encontrado)mapa.fitBounds(encontrado.getBounds(),{maxZoom:11,padding:[30,30]});};li.append(b);c.append(li);});
    if(fs.length>100)c.append(el('li',fs.length+' matches; narrow the search to see more.'));
  }
  function rotular(){etiquetas.clearLayers();if(!visible||!$('hid-etiquetas').checked||window.SICC_vista.modo()!=='mapa')return;
    let n=0;cuencas?.eachLayer(l=>{if(n>=150||!mapa.getBounds().intersects(l.getBounds()))return;const centro=l.getCenter();if(!mapa.getBounds().contains(centro))return;
      const t=el('span',H.codigo(l.feature.properties));L.marker(centro,{interactive:false,keyboard:false,icon:L.divIcon({className:'hid-etiqueta',html:t,iconSize:null})}).addTo(etiquetas);n++;});if(!mapa.hasLayer(etiquetas))etiquetas.addTo(mapa);
  }
  // Más cerca de la precisión de origen, el trazo se atenúa y se vuelve punteado: INETER publica sus
  // cuencas a escala 1:750 000 (~375 m) y HydroBASINS está simplificado a 0,003° (nivel 6) o 0,01°
  // (nivel 4); con imagen satelital de detalle, un trazo sólido aparentaría más exactitud de la que tiene.
  let seleccionada=null;
  function zoomPreciso(){const r=$('hid-region').value;return r==='nic'?12:(r==='world'||$('hid-nivel').value==='4')?8:10}
  function aproximado(){return mapa.getZoom()>=zoomPreciso()}
  function resaltar(){if(seleccionada&&cuencas?.hasLayer(seleccionada)){seleccionada.setStyle({weight:3,color:'#fff3a1',fillOpacity:.25,opacity:1,dashArray:null});seleccionada.bringToFront();}}
  let aproxPrevio=null;
  mapa.on('zoomend',()=>{if(!cuencas)return;const a=aproximado();if(a===aproxPrevio)return;aproxPrevio=a;cuencas.resetStyle();resaltar();});
  function pintarCuencas(){cuencas?.remove();seleccionada=null;aproxPrevio=null;
    cuencas=L.geoJSON(fc,{renderer:L.canvas({padding:.3}),bubblingMouseEvents:false,
      attribution:$('hid-region').value==='nic'?'Watersheds: INETER / IDE-RH Nicaragua (public service)':'Watersheds: HydroBASINS © HydroSHEDS (Lehner & Grill 2013)',
      style:f=>{const n=[...H.codigo(f.properties)].reduce((a,c)=>a+c.charCodeAt(0),0),color=`hsl(${170+n%100},75%,68%)`;
        return aproximado()?{color,weight:1,opacity:.75,dashArray:'4 5',fillOpacity:0}:{color,weight:1.1,opacity:1,dashArray:null,fillOpacity:.07};},
      onEachFeature:(f,l)=>{l.bindTooltip(el('span',H.codigo(f.properties)+(f.properties.cuencas?' · '+f.properties.cuencas:'')),{sticky:true});l.on('click',()=>detalle(f,l));}
    });if(visible)cuencas.addTo(mapa);buscar();rotular();
  }
  // «World» solo en nivel 4: las nueve regiones en nivel 6 son 16 397 polígonos y ~1,5 GB de memoria en el navegador.
  async function cargarCuencas(){const turno=++secuencia,r=$('hid-region').value,n=r==='world'?4:Number($('hid-nivel').value);texto('hid-estado','Loading watershed vectors…');
    try{
      const archivos=r==='nic'?['nicaragua_pfafstetter.geojson.gz']:(r==='world'?Object.keys(regiones):[r]).map(c=>`hydrobasins_${c}_l${n}.geojson.gz`);
      const colecciones=await Promise.all(archivos.map(a=>datos('data/hidrologia/'+a)));
      if(turno!==secuencia)return;
      fc={type:'FeatureCollection',features:colecciones.flatMap(c=>c.features),metadata:{sources:colecciones.map(c=>c.metadata),retrieved_snapshot:manifiesto.generated_utc}};
      visible=true;await window.SICC_vista.cambiar('mapa');if(turno!==secuencia)return;pintarCuencas();
      if(r==='nic')mapa.fitBounds(cuencas.getBounds(),{padding:[20,20]});else if(r==='world')mapa.setView([15,0],2);else mapa.fitBounds(cuencas.getBounds(),{maxZoom:5,padding:[20,20]});
      texto('hid-estado',`${fc.features.length.toLocaleString((window.GnomonI18n?.locale()||'en-US'))} polygons · ${r==='nic'?'2021 edition · '+manifiesto.nicaragua.code_discrepancies+' source code inconsistencies retained':'HydroBASINS v1c · level '+n} · Reference boundaries, not live water conditions.`);
      $('hid-geojson').disabled=$('hid-csv').disabled=false;
      $('hid-original').href=r==='nic'?'https://www.arcgis.com/home/item.html?id=a367394491e5470c89ab165525c4c246':r==='world'?'https://www.hydrosheds.org/products/hydrobasins':`https://data.hydrosheds.org/file/hydrobasins/standard/hybas_${r}_lev12_v1c.zip`;
      $('hid-original').textContent=r==='nic'?'Original national vectors (ArcGIS REST)':r==='world'?'Original vectors · all regions and levels 1–12':'Download original level 12 vectors (SHP ZIP)';
    }catch(e){if(turno===secuencia)texto('hid-estado','Watersheds unavailable: '+e.message+'. Try loading again.');}
  }
  function opciones(){const r=$('hid-region').value,nic=r==='nic';for(const o of $('hid-nivel').options)o.disabled=nic?o.value!=='7':o.value==='7'||(r==='world'&&o.value==='6');$('hid-nivel').value=nic?'7':'4';}
  function fechaResumen(d){let viejas=0,sin=0;d.features.forEach(f=>{const a=H.antiguedad(f.properties);if(a==='Older than 48 hours')viejas++;if(a.includes('unknown'))sin++;});return `${d.features.length} stations · ${viejas} older than 48 hours · ${sin} without a verified UTC observation time.`;}
  function pintarEstaciones(){puntos?.remove();
    puntos=L.geoJSON(estaciones,{bubblingMouseEvents:false,attribution:'Stations: INETER Nicaragua (public service)',
      pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:6,color:'#142636',weight:1,fillOpacity:1,fillColor:H.antiguedad(f.properties)==='Within the last 48 hours'?'#8de1c4':'#b8a2a2'}),
      onEachFeature:(f,l)=>{const p=f.properties,div=atributos(p,p.nombreestacion||p.Estacion||p.nombrebd||'INETER station');div.prepend(el('p',H.antiguedad(p)),el('p',H.fecha(p)||'Observation time not supplied'));l.bindPopup(div);}
    });if(estacionesVisibles)puntos.addTo(mapa);$('hid-estaciones-csv').disabled=false;
  }
  async function cargarEstaciones(refrescar=false){const turno=++secEst,id=$('hid-estacion').value;
    texto('hid-estaciones-estado',refrescar?'Requesting station readings…':'Loading dated station snapshot…');
    let aviso='Dated snapshot';
    try{
      let d;
      const base=window.SICC_CONFIG.hidrologia_api;
      if(refrescar&&base){try{d=await json(base.replace(/\/$/,'')+'/hidrologia/observaciones/'+id);aviso='INETER response';}catch(e){aviso='Live request unavailable; dated snapshot retained';}}
      else if(refrescar)aviso='Live gateway not configured; dated snapshot';
      d??=await datos('data/hidrologia/ineter_'+id+'.geojson');if(turno!==secEst)return;
      estaciones=d;estacionesVisibles=true;await window.SICC_vista.cambiar('mapa');if(turno!==secEst)return;pintarEstaciones();
      texto('hid-estaciones-estado',`${aviso} · retrieved ${d.metadata.retrieved_utc}. ${fechaResumen(d)} Retrieval time is not observation time.`);
      if(puntos.getBounds().isValid())mapa.fitBounds(puntos.getBounds(),{maxZoom:8,padding:[20,20]});
    }catch(e){if(turno===secEst)texto('hid-estaciones-estado','Station readings unavailable: '+e.message+'. No values were substituted.');}
  }
  function mostrarReferencia(fuente=null){referencia?.remove();const [nombre,tipo,nota]=fuente||referencias[Number($('hid-referencia').value)];
    const origen=WFS.replace(/ows$/,'wms');
    referencia=L.tileLayer.wms(origen,{layers:tipo,format:'image/png',transparent:true,version:'1.1.1',opacity:.6,attribution:'INETER · '+nombre});
    const esta=referencia;referencia.on('tileerror',()=>{if(referencia===esta)texto('hid-referencia-estado','Reference map temporarily unavailable from INETER. '+nota);});
    window.SICC_vista.irA(12.8,-85,7).then(()=>referencia?.addTo(mapa));texto('hid-referencia-estado',nota+' Colors follow the provider style; open the source legend for units and classes.');
    $('hid-referencia-fuente').href=fuenteWFS(tipo);$('hid-referencia-fuente').textContent='Download original vectors (WFS GeoJSON)';
    $('hid-referencia-leyenda').href=WFS.replace(/ows$/,'wms')+'?'+new URLSearchParams({service:'WMS',version:'1.1.1',request:'GetLegendGraphic',format:'image/png',layer:tipo});
  }
  async function mostrarSinapred(x){const turno=++secReferencia;referencia?.remove();referencia=null;texto('hid-referencia-estado','Loading original SINAPRED vectors…');
    try{
      await window.SICC_vista.irA(12.8,-85,7);
      const query=x.url+'/query?',ids=await json(query+new URLSearchParams({where:'1=1',returnIdsOnly:'true',f:'json'}));
      if(ids.error||!Array.isArray(ids.objectIds))throw Error('Public query unavailable');
      if(ids.objectIds.length>10000)throw Error('Layer is large; use its original download service');
      const fs=[];
      for(let i=0;i<ids.objectIds.length;i+=100){if(turno!==secReferencia)return;
        const grupo=ids.objectIds.slice(i,i+100),d=await json(query+new URLSearchParams({objectIds:grupo.join(','),outFields:'*',outSR:'4326',f:'geojson',maxAllowableOffset:'0.0002'}));
        if(d.exceededTransferLimit||d.features?.length!==grupo.length)throw Error('Incomplete response; no partial layer displayed');fs.push(...d.features);
      }
      if(turno!==secReferencia)return;
      referencia=L.geoJSON({type:'FeatureCollection',features:fs},{renderer:L.canvas(),bubblingMouseEvents:false,style:{color:'#eaba88',weight:1,fillOpacity:.14},onEachFeature:(f,l)=>l.bindPopup(atributos(f.properties,x.title_source))}).addTo(mapa);
      texto('hid-referencia-estado',`${x.title_source} · ${fs.length} source features. Reference map; this is not a current event or a detected climate trend.`);
      $('hid-referencia-fuente').href=x.url;$('hid-referencia-fuente').textContent='SINAPRED source metadata and query';$('hid-referencia-leyenda').href=x.url+'?f=pjson';
    }catch(e){if(turno===secReferencia)texto('hid-referencia-estado','SINAPRED layer unavailable: '+e.message);}
  }
  let secReferencia=0;
  // Solo las capas de amenazas de SINAPRED, con nombre en inglés y el original entre paréntesis. El catálogo WFS
  // completo de INETER (más de 400 capas con nombres internos) se enlaza, no se lista.
  const NOMBRES_SINAPRED={'Corredor seco':'Dry Corridor','Peligro de inundación':'Flood hazard','Amenaza sísmica':'Seismic hazard',
    'Fallas sísmicas':'Seismic faults','Amenaza volcánica':'Volcanic hazard','Tsunami pacífico':'Pacific tsunami hazard',
    'Ruta de huracanes':'Historical hurricane tracks','Inundación Caribe':'Caribbean flooding','Ríos y Lagunas':'Rivers and lagoons'};
  function filtrarCatalogo(){const c=$('hid-catalogo');c.replaceChildren();const q=$('hid-catalogo-buscar').value.toLocaleLowerCase();
    for(const x of sinapred?.layers??[]){const nombre=NOMBRES_SINAPRED[x.title_source]||x.title_source;
      if(q&&!(nombre+' '+x.title_source).toLocaleLowerCase().includes(q))continue;
      const li=el('li'),a=el('a',`${nombre} (${x.title_source}) · SINAPRED`),b=el('button','Show map');a.href=x.url;a.target='_blank';a.rel='noopener';b.type='button';b.onclick=()=>mostrarSinapred(x);li.append(a,' ',b);c.append(li);}
  }
  async function iniciar(){if(activa)return;activa=true;
    try{[manifiesto,catalogo,sinapred]=await Promise.all([datos('data/hidrologia/procedencia.json'),datos('data/hidrologia/ineter_catalogo.json'),datos('data/hidrologia/sinapred_catalogo.json')]);filtrarCatalogo();await cargarCuencas();}
    catch(e){activa=false;texto('hid-estado','Hydrology catalogue unavailable: '+e.message);}
  }
  for(const [id,n] of Object.entries(regiones)){const o=el('option',n+' · HydroBASINS');o.value=id;$('hid-region').append(o);}
  referencias.forEach(([n],i)=>{const o=el('option',n);o.value=i;$('hid-referencia').append(o);});
  $('hid-region').onchange=opciones;$('hid-ver').onclick=()=>manifiesto?cargarCuencas():iniciar();
  $('hid-ocultar').onclick=()=>{visible=false;secuencia++;cuencas?.remove();etiquetas.clearLayers();texto('hid-estado','Watershed layer hidden.');};
  $('hid-etiquetas').onchange=rotular;$('hid-buscar').oninput=buscar;
  $('hid-geojson').onclick=()=>{if(fc)descargar(JSON.stringify(fc),'watersheds.geojson','application/geo+json');};
  $('hid-csv').onclick=()=>{if(fc)descargar(H.filasCSV(fc.features),'watershed_codes.csv','text/csv;charset=utf-8');};
  $('hid-estaciones-ver').onclick=()=>cargarEstaciones();$('hid-actualizar').onclick=()=>cargarEstaciones(true);
  $('hid-estaciones-ocultar').onclick=()=>{estacionesVisibles=false;secEst++;puntos?.remove();texto('hid-estaciones-estado','Station layer hidden.');};
  $('hid-estaciones-csv').onclick=()=>{if(estaciones)descargar(H.filasCSV(estaciones.features),'ineter_station_attributes.csv','text/csv;charset=utf-8');};
  $('hid-referencia-ver').onclick=()=>{secReferencia++;mostrarReferencia();};$('hid-referencia-ocultar').onclick=()=>{secReferencia++;referencia?.remove();referencia=null;texto('hid-referencia-estado','Reference layer hidden.');};
  $('hid-catalogo-buscar').oninput=filtrarCatalogo;
  for(const b of document.querySelectorAll('[data-hid-capa]'))b.onclick=async()=>{await window.SICC_vista.cambiar('mapa');const c=$(b.dataset.hidCapa);c.checked=!c.checked;c.dispatchEvent(new Event('change'));};
  mapa.on('moveend',rotular);document.addEventListener('sicc:vista',rotular);
  document.addEventListener('sicc:pestana',e=>{if(e.detail==='hidrologia')iniciar();});
  setInterval(()=>{if(!document.hidden&&!$('hidrologia').hidden&&$('hid-auto').checked)cargarEstaciones(true);},300000);
  window.SICC_hidrologia={estado:()=>({cargado:!!fc,poligonos:fc?.features.length??0,estaciones:estaciones?.features.length??0,visible}),cargarEstaciones};
})();
