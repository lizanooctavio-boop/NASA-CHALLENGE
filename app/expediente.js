// Pestaña «Area report / Expediente por área»: seleccionar zona → configurar → analizar → revisar → PDF → compartir.
// Usa los módulos de src/expediente/ (geo, estado, fuentes, analisis, informe, paquete, i18n) y el mapa Leaflet de
// app/shell.js. El panel, el PDF, el ZIP y el enlace leen el mismo objeto de resultados (ETDAnalisis.analizar).
(function () {
  'use strict';
  const G = window.ETDGeo, E = window.ETDEstado, F = window.ETDFuentes, A = window.ETDAnalisis, I = window.ETDi18n, P = window.ETDPaquete, INF = window.ETDInforme, PP = window.ETDPerspectiva;
  const raiz = document.getElementById('exp-raiz');
  if (!raiz || !G || !E || !F || !A || !I) return;
  const CFG = window.SICC_CONFIG || {};
  const $ = (sel, base) => (base || raiz).querySelector(sel);
  const h = (tag, attrs, ...hijos) => {
    const n = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (v === null || v === undefined || v === false) return;
      if (k === 'class') n.className = v; else if (k.startsWith('on')) n.addEventListener(k.slice(2), v); else if (k === 'html') n.innerHTML = v; else n.setAttribute(k, v === true ? '' : v);
    });
    hijos.flat().forEach(x => { if (x !== null && x !== undefined && x !== false) n.append(x.nodeType ? x : document.createTextNode(String(x))); });
    return n;
  };

  // ------------------------------------------------------------------ estado de la pestaña
  // El panel sigue el idioma de la aplicación (Settings); el traductor general no lo toca (data-i18n-ignore).
  const idiomaApp = () => window.GnomonI18n && window.GnomonI18n.language() === 'es' ? 'es' : 'en';
  const idiomaInicial = window.GnomonI18n ? idiomaApp() : (() => { try { return (localStorage.getItem('etd-exp-idioma') || (navigator.language || 'es')).slice(0, 2) === 'en' ? 'en' : 'es'; } catch (e) { return 'es'; } })();
  const S = {
    consulta: Object.assign(E.valoresPorDefecto(), { idioma: idiomaInicial }),
    area: null,          // área validada con sus atributos derivados (sin datos)
    modo: null,          // herramienta de dibujo activa
    borrador: [],        // vértices en curso
    resultado: null,     // objeto de ETDAnalisis
    origenResultado: null, // 'calculado' | 'guardado'
    referenciaEnlace: null,
    admin: null,         // límites INETER cargados
    exp: { idioma: idiomaInicial, plantilla: 'completo', secciones: INF ? INF.SECCIONES.slice() : [], autor: '', organizacion: '', notas: '' },
    ocupado: false, mensaje: null
  };
  const t = (k, v) => I.t(k, S.consulta.idioma, v);
  const num = (v, d) => I.num(v, d, S.consulta.idioma);

  // ------------------------------------------------------------------ mapa
  let capaArea = null, capaCeldas = null, capaBorrador = null;
  const mapaListo = () => typeof mapa !== 'undefined' && mapa && window.L;
  function asegurarCapas() {
    if (!mapaListo()) return false;
    if (!capaArea) { capaCeldas = L.layerGroup().addTo(mapa); capaArea = L.layerGroup().addTo(mapa); capaBorrador = L.layerGroup().addTo(mapa); }
    return true;
  }
  async function verMapa() { if (window.SICC_vista) await window.SICC_vista.cambiar('mapa'); }
  // shell.js consulta esta función antes de su propio clic (pronóstico): si dibujamos, el clic es nuestro.
  window.ETDCapturaMapa = function (e) {
    if (!S.modo || raiz.closest('.vista').hidden) return false;
    clicMapa(e.latlng.lat, L.Util.wrapNum(e.latlng.lng, [-180, 180]));
    return true;
  };
  function clicMapa(lat, lon) {
    const m = S.modo;
    if (m === 'punto') { fijarArea({ type: 'Point', coordinates: [lon, lat] }, 'punto', { tipo: 'dibujo' }); }
    else if (m === 'circulo') { const r = Number($('#exp-radio')?.value) || 10; fijarArea(G.circulo(lon, lat, r), 'circulo', { tipo: 'dibujo' }, { radio_km: r, centro_circulo: [lon, lat] }); }
    else if (m === 'rectangulo') {
      S.borrador.push([lon, lat]);
      if (S.borrador.length === 2) { const [a, b] = S.borrador; S.borrador = []; fijarArea(G.rectangulo(Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])), 'rectangulo', { tipo: 'dibujo' }); }
      else dibujarBorrador();
    } else if (m === 'poligono') { S.borrador.push([lon, lat]); dibujarBorrador(); render(); }
  }
  function dibujarBorrador() {
    if (!asegurarCapas()) return;
    capaBorrador.clearLayers();
    const ll = S.borrador.map(p => [p[1], p[0]]);
    ll.forEach(p => L.circleMarker(p, { radius: 4, color: '#ffd166', weight: 2, fillOpacity: 1 }).addTo(capaBorrador));
    if (ll.length > 1) L.polyline(ll, { color: '#ffd166', weight: 2, dashArray: '4 4' }).addTo(capaBorrador);
  }
  function geomALeaflet(g) {
    if (g.type === 'Point') return null;
    return G.poligonos(g).map(pol => G.desenvolverPoligono(pol).map(an => an.map(c => [c[1], c[0]])));
  }
  function dibujarArea(encuadrar) {
    if (!asegurarCapas()) return;
    capaArea.clearLayers(); capaBorrador.clearLayers();
    if (!S.area) return;
    const g = S.area.geometria;
    let capa;
    if (g.type === 'Point') capa = L.circleMarker([g.coordinates[1], g.coordinates[0]], { radius: 7, color: '#ff4d5e', weight: 3, fillColor: '#ff4d5e', fillOpacity: .5 });
    else capa = L.polygon(geomALeaflet(g), { color: '#ff4d5e', weight: 3, fillOpacity: .06 });
    capa.bindTooltip(S.area.nombre || t('area.' + S.area.tipo), { sticky: true }).addTo(capaArea);
    if (encuadrar) {
      const v = S.consulta.vista;
      if (v.centro && v.zoom) mapa.setView([v.centro[0], v.centro[1]], v.zoom);
      else if (g.type === 'Point') mapa.setView([g.coordinates[1], g.coordinates[0]], 8);
      else mapa.fitBounds(capa.getBounds(), { padding: [40, 40], maxZoom: 10 });
    }
  }
  function colorRampa(x, divergente, invertir) {
    if (x === null || x === undefined || !isFinite(x)) return '#888';
    x = Math.max(-1, Math.min(1, x)); if (invertir) x = -x;
    const a = divergente ? [[33, 102, 172], [247, 247, 247], [178, 24, 43]] : [[239, 243, 255], [107, 174, 214], [8, 69, 148]];
    const f = divergente ? (x + 1) / 2 : x, i = f < .5 ? 0 : 1, k = f < .5 ? f / .5 : (f - .5) / .5;
    return 'rgb(' + [0, 1, 2].map(j => Math.round(a[i][j] + (a[i + 1][j] - a[i][j]) * k)).join(',') + ')';
  }
  function dibujarCeldas() {
    if (!asegurarCapas()) return;
    capaCeldas.clearLayers();
    const celdas = S.resultado ? S.resultado.celdas : (S.area ? S.area.celdas : []);
    if (!celdas || !celdas.length) return;
    const capa = S.consulta.vista.capa, valor = c => capa === 'peso_celda' ? c.peso : capa === 'tendencia_celda' ? (c.tendencia && c.tendencia.sen_decada) : c.anomalia_anio_visible;
    const vals = celdas.map(valor).filter(v => v !== null && v !== undefined && isFinite(v));
    const m = vals.length ? Math.max(...vals.map(Math.abs)) || 1 : 1, mx = vals.length ? Math.max(...vals) : 1;
    const inv = S.consulta.variable === 'PRECTOTCORR' && capa !== 'peso_celda';
    celdas.forEach(c => {
      const b = c.caja, v = S.resultado ? valor(c) : null, sin = S.resultado && c.estado !== 'ok';
      const col = sin ? '#777' : S.resultado ? colorRampa(capa === 'peso_celda' ? v / mx : v / m, capa !== 'peso_celda', inv) : '#6fd8ff';
      L.rectangle([[b[1], b[0]], [b[3], b[2]]], { color: '#1b2a3a', weight: 1, fillColor: col, fillOpacity: S.resultado ? .55 : .12, dashArray: sin ? '3 3' : null, interactive: true })
        .bindTooltip(`${c.id} · ${t('f.valor').toLowerCase()}: ${v === null || v === undefined ? t('na') : num(v, 3)} · ${S.consulta.idioma === 'en' ? 'weight' : 'peso'} ${num(c.peso, 3)}`, { sticky: true })
        .addTo(capaCeldas);
    });
  }

  // ------------------------------------------------------------------ límites administrativos (INETER)
  async function cargarAdmin() {
    if (S.admin) return S.admin;
    const [dep, mun] = await Promise.all(['data/admin/nicaragua_departamentos.geojson', 'data/admin/nicaragua_municipios.geojson'].map(async u => {
      const r = await fetch(u); if (!r.ok) throw Object.assign(Error('HTTP ' + r.status), { codigo: 'red' }); return r.json();
    }));
    S.admin = { dep, mun };
    return S.admin;
  }
  function divisionDe(lon, lat) {
    if (!S.admin) return null;
    const m = S.admin.mun.features.find(f => G.contiene(f.geometry, lon, lat));
    if (m) return { pais: 'Nicaragua', departamento: m.properties.nom_departamento, municipio: m.properties.nom_municipio, cod_municipio: m.properties.cod_municipio, segun: 'centro' };
    return null;
  }

  // ------------------------------------------------------------------ fijar el área
  function nuevoId(tipo) { return 'aoi-' + tipo + '-' + E.sha256(String(Date.now()) + Math.random()).slice(0, 8); }
  function fijarArea(geom, tipo, procedencia, extra, admin) {
    try {
      const v = G.validar(geom), g = v.geometria;
      const celdas = G.celdasRejilla(g, F.POWER.rejilla);
      const centro = G.centro(g);
      const area = {
        id: (extra && extra.id) || nuevoId(tipo), nombre: (extra && extra.nombre) || (S.area && S.area.tipo === tipo && S.area.nombre) || '', tipo,
        geometria: g, extension: G.extension(g), centro, superficie_km2: G.areaKm2(g), vertices: v.vertices || null,
        radio_km: extra && extra.radio_km, admin: admin || null, procedencia, celdas: celdas.celdas, avisos_geometria: v.avisos
      };
      if (!area.admin && S.admin) { const d = divisionDe(centro.lon, centro.lat); if (d) area.admin = d; }
      S.area = area; S.resultado = null; S.origenResultado = null; S.modo = tipo === 'poligono' || tipo === 'rectangulo' ? null : S.modo; S.borrador = [];
      S.mensaje = null;
      dibujarArea(!(extra && extra.sinEncuadre)); dibujarCeldas(); render();
      if (!S.admin) cargarAdmin().then(() => { if (S.area === area && !area.admin) { const d = divisionDe(centro.lon, centro.lat); if (d) { area.admin = d; render(); } } }).catch(() => {});
      return true;
    } catch (err) { avisar(err); return false; }
  }
  function avisar(err, tipo) {
    const cod = err && err.codigo;
    S.mensaje = { tipo: tipo || 'error', texto: cod ? t('error.' + cod, { detalle: err.detalle || (err.message || '').split(': ').slice(1).join(': ') }) : String(err && err.message || err) };
    render();
  }

  // ------------------------------------------------------------------ análisis
  const TEMPORADAS = { anual: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], lluviosa: [5, 6, 7, 8, 9, 10], primera: [5, 6, 7, 8], postrera: [9, 10, 11], seca: [1, 2, 3, 4, 11, 12] };
  function temporadaActual() { const m = S.consulta.meses.join(','); return Object.keys(TEMPORADAS).find(k => TEMPORADAS[k].join(',') === m) || 'personalizada'; }
  function consultaCompleta() {
    const c = S.consulta, a = S.area;
    c.area = { id: a.id, nombre: a.nombre, tipo: a.tipo, geometria: a.geometria, radio_km: a.radio_km, admin: a.admin && a.admin.nivel ? { nivel: a.admin.nivel, codigo: a.admin.codigo, nombre: a.admin.nombre_unidad } : undefined, procedencia: a.procedencia };
    if (a.tipo === 'administrativa') c.area.admin = { nivel: a.admin.nivel, codigo: a.admin.codigo, nombre: a.admin.nombre_unidad };
    if (mapaListo()) { const ce = mapa.getCenter(); c.vista.centro = [Number(ce.lat.toFixed(5)), Number(ce.lng.toFixed(5))]; c.vista.zoom = mapa.getZoom(); }
    return E.validar(JSON.parse(JSON.stringify(c)));
  }
  async function cargarComparaciones(res) {
    try {
      const [fen, reg] = await Promise.all([fetch('data/fenomenos_nicaragua.json').then(r => r.ok ? r.json() : null), fetch('data/regiones_nicaragua.geojson').then(r => r.ok ? r.json() : null)]);
      if (!fen || !reg) return [];
      const c = res.area.centro, ids = reg.features.filter(f => f.properties.id !== 'caja_sicc' && G.contiene(f.geometry, c.lon, c.lat)).map(f => f.properties.id);
      const id = ids.find(x => x !== 'NIC') || ids[0];
      if (!id) return [];
      const r = fen.regiones.find(x => x.id === id), meses = res.consulta.meses.join(',');
      const clave = res.variable.id === 'T2M' ? (meses === TEMPORADAS.anual.join(',') ? 'temperatura_gistemp' : null)
        : meses === TEMPORADAS.anual.join(',') ? 'lluvia_anual_imerg' : meses === '6,7,8,9,10,11' ? 'lluvia_jun_nov_imerg' : null;
      const vv = clave && (r.variables[clave] || (fen.regiones.find(x => x.id === 'NIC').variables[clave]));
      const usarNIC = clave && !r.variables[clave];
      if (!vv || !vv.tendencia) return [];
      const ts = vv.tendencia.theil_sen || {}, mc = vv.tendencia.minimos_cuadrados || {};
      const pend = ts.por_decada !== undefined ? ts : mc;
      return [{ fuente: (clave === 'temperatura_gistemp' ? 'NASA GISTEMP v4 (' : 'NASA GPM IMERG V07 (') + (ts.por_decada !== undefined ? 'Theil-Sen' : (S.consulta.idioma === 'en' ? 'least squares' : 'mínimos cuadrados')) + ')',
        region: usarNIC ? fen.regiones.find(x => x.id === 'NIC').nombre : r.nombre, periodo: (vv.tendencia.periodo || []).join('–'), valor: pend.por_decada, inf: pend.ic_por_decada[0], sup: pend.ic_por_decada[1], unidad: vv.tendencia.unidad || vv.unidad }];
    } catch (e) { return []; }
  }
  // ------------------------------------------------------------------ perspectiva de la próxima década
  // Insumos estáticos del repositorio (índices anuales por celda, GISTEMP regional, CMIP6 regional). Se descargan una vez.
  let insumosPP = null;
  async function insumosPerspectiva() {
    if (insumosPP) return insumosPP;
    const txt = u => fetch(u).then(r => { if (!r.ok) throw Error(u + ' (' + r.status + ')'); return r.text(); });
    const json = u => fetch(u).then(r => r.ok ? r.json() : null).catch(() => null);
    const [idx, gis, cm, cmMeta, reg] = await Promise.all([
      txt('data/fenomenos/indices_anuales_celdas.csv'), txt('data/fenomenos/gistemp_nicaragua.csv').catch(() => null),
      txt('data/expediente/cmip6_regional_mensual.csv').catch(() => null), json('data/expediente/cmip6_regional.json'), json('data/regiones_nicaragua.geojson')]);
    insumosPP = { indices: PP.leerIndicesCeldas(idx), gistemp: gis, cmip6: cm, cmip6Meta: cmMeta, regiones: reg };
    return insumosPP;
  }
  function regionDe(reg, c) {
    if (!reg) return null;
    const fs = reg.features.filter(f => f.properties.id !== 'caja_sicc' && G.contiene(f.geometry, c.lon, c.lat));
    return fs.find(f => f.properties.id !== 'NIC') || fs[0] || null;
  }
  async function calcularPerspectiva(res) {
    const c = res.consulta, pc = c.perspectiva || {};
    if (!PP || pc.activa === false) return null;
    const ins = await insumosPerspectiva();
    const anual = c.meses.length === 12, h0 = Number((res.generado_utc || new Date().toISOString()).slice(0, 4));
    const ini = h0 + 1, fin = h0 + 10;
    // 1) la variable de la consulta; 2) índices del área (sin duplicar la variable de la consulta); 3) GISTEMP de la región.
    let indicadores = [PP.indicadorDeConsulta(res, c.idioma)];
    const ar = PP.indicadoresDeArea(res.celdas, ins.indices, 0.9);
    const duplicado = anual ? (c.variable === 'T2M' ? 't2m_media' : c.variable === 'PRECTOTCORR' ? 'prcptot' : null) : null;
    indicadores = indicadores.concat(ar.indicadores.filter(x => x.id !== duplicado));
    const excluidas = PP.EXCLUIDAS.slice();
    if (!ar.indicadores.length) excluidas.unshift({ id: 'indices_area', nombre: 'Índices de extremos del área (ETCCDI)', nombre_en: 'Area extreme indices (ETCCDI)',
      motivo: 'La malla de índices de la app cubre ' + (100 * ar.cobertura).toFixed(0) + ' % del área (mínimo 90 %): solo Nicaragua.',
      motivo_en: 'The app\'s index grid covers ' + (100 * ar.cobertura).toFixed(0) + ' % of the area (minimum 90 %): Nicaragua only.' });
    const rg = regionDe(ins.regiones, res.area.centro);
    let cmip6 = null;
    if (rg) {
      if (ins.gistemp) { const gi = PP.indicadorGistemp(ins.gistemp, rg.properties.id, rg.properties.nombre); if (gi) indicadores.push(gi); }
      if (ins.cmip6) {
        const prep = x => { const tiene = Object.values(x.variables).some(V => Object.values(V.escenarios).some(E2 => Object.values(E2).some(m => m[ini] !== undefined))); return tiene ? x : PP.interpolarCmip6(x, ini, fin); };
        const an = prep(PP.leerCmip6(ins.cmip6, rg.properties.id, null)), te = anual ? null : prep(PP.leerCmip6(ins.cmip6, rg.properties.id, c.meses));
        cmip6 = { region: rg.properties.id, nombre: rg.properties.nombre, interpolado: !!(an.interpolado || (te && te.interpolado)), anual: an, temporada: te,
          escenarios: pc.escenarios, archivo: 'data/expediente/cmip6_regional_mensual.csv', modelos: (ins.cmip6Meta && ins.cmip6Meta.modelos) || an.modelos };
      }
    }
    const ext = res.area.extension || G.extension(res.area.geometria);
    const mapas = PP.mapasCeldas(ins.indices, res.celdas, ext, c.referencia);
    if (mapas && ins.cmip6 && ins.regiones) {
      const regs = ins.regiones.features.filter(f => ['pacifico', 'central', 'caribe'].includes(f.properties.id)).map(f => ({ id: f.properties.id, nombre: f.properties.nombre }));
      mapas.cmip6_regiones = PP.cmipRegiones(ins.cmip6, regs, { inicio: ini, fin }, pc.escenarios);
    }
    return PP.evaluar({ anio_generacion: h0, referencia: c.referencia, indicadores, cmip6, semilla: pc.semilla, n_sim: pc.n_sim, modelo: pc.modelo,
      excluidas, mapas });
  }

  // Mapa con foto satelital para la portada y la sección C: Esri World Imagery con las capas de referencia de Esri
  // (límites y nombres de lugares, carreteras) superpuestas en un lienzo, como el mapa de la app. Si la foto de Esri
  // falla se usa NASA Blue Marble (GIBS) sin etiquetas; si todo falla, el informe dibuja el mapa vectorial.
  const imagenes = {};
  function aDataURL(blob) { return new Promise((ok, mal) => { const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = mal; r.readAsDataURL(blob); }); }
  function cajaImagen(e, asp, margen, minimo) {
    const k = Math.cos(((e[1] + e[3]) / 2) * Math.PI / 180), cx = (e[0] + e[2]) / 2, cy = (e[1] + e[3]) / 2;
    let wk = Math.max((e[2] - e[0]) * k, minimo) * margen, hk = Math.max(e[3] - e[1], minimo) * margen;
    if (wk / hk < asp) wk = hk * asp; else hk = wk / asp;
    return [cx - wk / k / 2, cy - hk / 2, cx + wk / k / 2, cy + hk / 2].map(v => Number(v.toFixed(5)));
  }
  async function traerImagen(url, tipoRe) {
    const traer = window.ETD_FETCH_IMAGEN || window.fetch.bind(window);
    const ctl = new AbortController(), tm = setTimeout(() => ctl.abort(), 15000);
    try {
      const r = await traer(url, { signal: ctl.signal });
      const tipo = (r.headers.get('content-type') || '');
      if (!r.ok || !tipoRe.test(tipo)) return null;
      const b = await r.blob(); return b.size < 200 ? null : b;
    } catch (x) { return null; } finally { clearTimeout(tm); }
  }
  async function aImagen(blob) {
    if (window.createImageBitmap) { try { return await createImageBitmap(blob); } catch (x) { /* abajo */ } }
    const url = URL.createObjectURL(blob);
    try { return await new Promise((ok, mal) => { const im = new Image(); im.onload = () => ok(im); im.onerror = mal; im.src = url; }); } finally { setTimeout(() => URL.revokeObjectURL(url), 1000); }
  }
  async function mapaSatelital(e, asp, margen, minimo) {
    if (e[0] > e[2]) return null;
    const ext = cajaImagen(e, asp, margen, minimo), W = 1600, H = Math.round(W * (ext[3] - ext[1]) / (ext[2] - ext[0])), hoy = new Date().toISOString().slice(0, 10), en = S.exp.idioma === 'en';
    const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
    // imageSR=4326 y bbox con el mismo aspecto que la imagen: proyección equirectangular, la misma que usa el PDF
    const exp = (svc, fmt) => ESRI + svc + '/MapServer/export?bbox=' + ext.join(',') + '&bboxSR=4326&imageSR=4326&size=' + W + ',' + H + '&dpi=144&format=' + fmt + '&transparent=' + (fmt === 'png32') + '&f=image';
    let base = await traerImagen(exp('World_Imagery', 'jpg'), /jpe?g/), fuente = 'Esri World Imagery (Esri, Maxar, Earthstar Geographics)', fecha = (en ? 'multi-date mosaic, accessed ' : 'mosaico de varias fechas, consultado ') + hoy, capas = [];
    if (base) {
      const [lim, vias] = await Promise.all([traerImagen(exp('Reference/World_Boundaries_and_Places', 'png32'), /png/), traerImagen(exp('Reference/World_Transportation', 'png32'), /png/)]);
      if (vias) capas.push({ b: vias, n: en ? 'roads (Esri World Transportation)' : 'carreteras (Esri World Transportation)' });
      if (lim) capas.push({ b: lim, n: en ? 'boundaries and place names (Esri World Boundaries and Places)' : 'límites y nombres de lugares (Esri World Boundaries and Places)' });
    } else {
      base = await traerImagen('https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1&LAYERS=BlueMarble_NextGeneration&STYLES=&SRS=EPSG:4326&BBOX=' + ext.join(',') + '&WIDTH=' + W + '&HEIGHT=' + H + '&FORMAT=image/jpeg', /jpe?g/);
      fuente = 'NASA Blue Marble: Next Generation (GIBS)'; fecha = (en ? '2004 composite, accessed ' : 'compuesto de 2004, consultado ') + hoy;
    }
    if (!base) return null;
    let datos = null, etiquetas = [];
    try {
      const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
      const cx = cv.getContext('2d');
      cx.drawImage(await aImagen(base), 0, 0, W, H);
      for (const c of capas) { try { cx.drawImage(await aImagen(c.b), 0, 0, W, H); etiquetas.push(c.n); } catch (x) { /* capa omitida */ } }
      datos = cv.toDataURL('image/jpeg', 0.86);
    } catch (x) { datos = await aDataURL(base); etiquetas = []; }
    return { datos, formato: 'JPEG', ancho: asp, alto: 1, ext, fuente: fuente + (etiquetas.length ? (en ? '; overlays: ' : '; capas superpuestas: ') + etiquetas.join(', ') : ''), fecha, etiquetas: etiquetas.length > 0 };
  }
  async function imagenPortada(res) {
    const k = res.resultado_id + '|' + S.exp.idioma;
    if (imagenes[k] !== undefined) return imagenes[k];
    const e = res.area.extension || G.extension(res.area.geometria);
    const celdas = res.celdas.map(c => c.caja).filter(Boolean), ed = celdas.length && e[0] <= e[2] ? [Math.min(e[0], ...celdas.map(b => b[0])), Math.min(e[1], ...celdas.map(b => b[1])), Math.max(e[2], ...celdas.map(b => b[2])), Math.max(e[3], ...celdas.map(b => b[3]))] : e;
    const [portada, detalle] = await Promise.all([mapaSatelital(e, 2.15, 1.25, 0.06), mapaSatelital(ed, 1.45, 1.12, 0.06)]);
    return (imagenes[k] = portada || detalle ? { portada, detalle } : null);
  }

  function panelPerspectiva() {
    const res = S.resultado, PV = res.perspectiva, en = S.consulta.idioma === 'en';
    const art = h('article', { id: 'exp-perspectiva' });
    if (!PV) {
      art.append(h('h3', null, t('pp.config')));
      art.append(h('p', { class: 'pista' }, res.perspectiva_error ? t('pp.error', { e: res.perspectiva_error }) : t('pp.inactiva')));
      return art;
    }
    art.setAttribute('data-perspectiva', PV.perspectiva_id);
    art.append(h('h3', null, t('pp.titulo', { ini: PV.horizonte.inicio, fin: PV.horizonte.fin })));
    const cuenta = cl => PV.indicadores.filter(o => o.clasificacion.clase === cl).length;
    art.append(h('p', { id: 'exp-pp-resumen' }, t('pp.resumen', { v: cuenta('validada'), e: cuenta('exploratorio'), n: cuenta('no_proyectable'), x: PV.excluidas.length })));
    const ref = PV.referencia.inicio + '–' + PV.referencia.fin;
    // Las filas exploratorias (sin habilidad o con la inhomogeneidad de lluvia de MERRA-2) van plegadas: sus cifras
    // no sostienen conclusiones y, a la vista, se confundirían con proyecciones validadas.
    const tabla = (id, filas) => { const x = h('table', { class: 'exp-ficha exp-pp-tabla', id }, h('caption', null, t('pp.tabla', { ref })));
      x.append(h('tr', null, ...['pp.col.indicador', 'pp.col.cambio', 'pp.col.intervalo', 'pp.col.habilidad', 'pp.col.clase'].map(k => h('th', { scope: 'col' }, t(k))))); filas.forEach(o => x.append(fila(o))); return x; };
    const fila = o => {
      const p = o.proyeccion, u = en ? o.unidad_en || o.unidad : o.unidad, d = o.decimales === undefined ? 1 : o.decimales, cl = o.clasificacion.clase;
      const cr = p && p.cambio_vs_referencia.prediccion, sel = o.seleccion && o.validacion && o.validacion.modelos[o.seleccion.modelo];
      const signo = v => (v > 0 ? '+' : '') + num(v, d);
      return h('tr', { 'data-indicador': o.id, 'data-clase': cl, class: PV.destacadas.includes(o.id) ? 'exp-pp-destacada' : null },
        h('th', { scope: 'row' }, (PV.destacadas.includes(o.id) ? '★ ' : '') + (en ? o.nombre_en : o.nombre)),
        h('td', null, cr ? signo(cr.p50) + ' ' + u : '—'),
        h('td', null, cr ? t('pp.pi80', { a: signo(cr.p10), b: signo(cr.p90) }) : '—'),
        h('td', null, sel ? t('p.modelo.' + o.seleccion.modelo) + ' · MSSS ' + num(sel.habilidad, 2) : '—'),
        h('td', { title: t('p.motivo.' + o.clasificacion.motivo) }, t('p.clase.' + cl)));
    };
    const exploratorias = PV.indicadores.filter(o => o.clasificacion.clase === 'exploratorio');
    art.append(tabla('exp-pp-tabla', PV.indicadores.filter(o => o.clasificacion.clase !== 'exploratorio')));
    if (exploratorias.length) art.append(h('details', { class: 'exp-pp-exploratorias', id: 'exp-pp-exploratorias' },
      h('summary', null, t('pp.exploratorias', { n: exploratorias.length })), h('p', { class: 'pista' }, t('pp.exploratorias_txt')), tabla('exp-pp-tabla-exploratorias', exploratorias)));
    if (PV.cmip6_fuente) art.append(h('p', { class: 'pista' }, t('pp.cmip', { region: PV.cmip6_fuente.nombre }) + (PV.cmip6_fuente.interpolado ? ' ' + t('pp.cmip_interp') : '')));
    art.append(h('p', { class: 'pista' }, t('pp.nota')));
    art.append(h('p', { class: 'pista exp-ids' }, t('pp.id') + ': ', h('code', { id: 'exp-perspectiva-id' }, PV.perspectiva_id)));
    return art;
  }
  async function analizar() {
    if (!S.area) return avisar({ codigo: 'sin_area' });
    let c;
    try { c = consultaCompleta(); } catch (e) { return avisar(e); }
    S.ocupado = true; S.mensaje = { tipo: 'info', texto: t('analizar.descargando', { hechas: 0, total: S.area.celdas.length }) }; render();
    try {
      const periodo = { inicio: Math.min(c.periodo.inicio, c.referencia.inicio), fin: Math.max(c.periodo.fin, c.referencia.fin) };
      const lect = await F.descargarCeldas(S.area.celdas, c.variable, periodo, {
        fetch: window.ETD_FETCH_FUENTE || window.fetch.bind(window),
        progreso: (n, tot) => { const p = $('#exp-progreso'); if (p) p.textContent = t('analizar.descargando', { hechas: n, total: tot }); }
      });
      if (!Object.keys(lect.celdas).length) {
        const f = lect.fallos[0] || {}; throw Object.assign(Error(f.detalle || 'todas_fallaron'), { codigo: f.error === 'red' || f.error === 'fuente_no_disponible' || f.error === 'fuente_rechazo' ? f.error : 'todas_fallaron', detalle: f.detalle });
      }
      const res = A.analizar({ consulta: c, area: Object.assign({}, S.area, { celdas: S.area.celdas, admin: S.area.admin }), variable: F.VARIABLES[c.variable], fuente: F.POWER, lecturas: lect });
      res.comparaciones = await cargarComparaciones(res);
      if (PP && c.perspectiva && c.perspectiva.activa !== false) {
        const p = $('#exp-progreso'); if (p) p.textContent = t('pp.calculando');
        await new Promise(r => setTimeout(r, 0));
        try { res.perspectiva = await calcularPerspectiva(res); } catch (x) { console.warn(x); res.perspectiva_error = String(x && x.message || x); }
      }
      S.resultado = res; S.origenResultado = 'calculado'; S.consulta = JSON.parse(JSON.stringify(c));
      let msg = t('analizar.listo', { id: res.resultado_id });
      if (S.referenciaEnlace) msg += ' · ' + (S.referenciaEnlace === res.resultado_id ? t('restaurar.coincide', { id: res.resultado_id }) : t('restaurar.difiere', { nuevo: res.resultado_id, orig: S.referenciaEnlace }));
      S.mensaje = { tipo: 'ok', texto: msg };
      document.dispatchEvent(new CustomEvent('etd:expediente', { detail: { resultado_id: res.resultado_id, consulta_id: res.consulta_id } }));
    } catch (e) {
      avisar(e);
      // Un fallo no borra el resultado anterior, pero se dice que el panel y las exportaciones siguen siendo de esa consulta.
      if (S.resultado) S.mensaje.texto += ' ' + t('analizar.se_mantiene', { id: S.resultado.resultado_id });
    } finally { S.ocupado = false; dibujarCeldas(); render(); }
  }

  // ------------------------------------------------------------------ exportación
  let libs = null;
  function cargarScript(src) { return new Promise((ok, mal) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = () => mal(Error('No se pudo cargar ' + src)); document.head.append(s); }); }
  async function cargarLibs() {
    if (libs) return libs;
    if (!(window.jspdf && window.jspdf.jsPDF)) await cargarScript('app/vendor/jspdf.umd.min.js');
    if (!window.qrcode) await cargarScript('app/vendor/qrcode-generator.js');
    const mundo = await fetch('assets/mundo.geojson').then(r => r.ok ? r.json() : null).catch(() => null);
    libs = { jsPDF: window.jspdf.jsPDF, qrcode: window.qrcode, mundo };
    return libs;
  }
  function urlBase() {
    const local = /^(localhost|127\.|0\.0\.0\.0|\[::1\])/.test(location.hostname) || location.protocol === 'file:';
    if (CFG.url_publica && local) return CFG.url_publica;
    return location.origin + location.pathname;
  }
  async function enlaceActual() {
    if (!S.resultado) return null;
    const e = await E.enlace(S.resultado.consulta, urlBase(), { resultado_ref: S.resultado.resultado_id });
    const local = /^(localhost|127\.|0\.0\.0\.0|\[::1\])/.test(location.hostname) || location.protocol === 'file:';
    e.local = local ? (await E.enlace(S.resultado.consulta, location.origin + location.pathname, { resultado_ref: S.resultado.resultado_id })).url : null;
    return e;
  }
  async function generarPDF() {
    const L2 = await cargarLibs(), e = await enlaceActual();
    const res = S.resultado, ex = S.exp;
    const sat = await imagenPortada(res);
    let regiones = null, admin = null;
    if (res.perspectiva && PP) { try { regiones = (await insumosPerspectiva()).regiones; } catch (x) { regiones = null; } }
    try { admin = (await cargarAdmin()).dep; } catch (x) { admin = null; }
    return INF.crear(res, { imagen: sat && sat.portada, mapaSatelite: sat && sat.detalle, regiones, admin, jsPDF: L2.jsPDF, qrcode: L2.qrcode, mundo: L2.mundo, enlace: e && !e.demasiado_largo ? e.url : null, idioma: ex.idioma, plantilla: ex.plantilla, secciones: ex.secciones, autor: ex.autor, organizacion: ex.organizacion, notas: ex.notas, comparaciones: res.comparaciones || [], desacuerdo: A.desacuerdoFuentes(res), generado_utc: new Date().toISOString() });
  }
  function descargar(nombre, datos, tipo) {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([datos], { type: tipo })); a.download = nombre; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 30000);
  }
  function nombreBase() { return 'expediente_' + (S.resultado.area.nombre || S.resultado.area.tipo).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9]+/g, '_').slice(0, 40) + '_' + S.resultado.resultado_id.slice(2, 10); }
  async function accion(fn) {
    if (!S.resultado) return avisar({ codigo: 'sin_resultado' });
    S.ocupado = true; S.mensaje = { tipo: 'info', texto: t('exp.generando') }; render();
    try { await fn(); } catch (e) { avisar(e); console.warn(e); } finally { S.ocupado = false; render(); }
  }
  const pdf = () => accion(async () => { const r = await generarPDF(); descargar(nombreBase() + '.pdf', r.doc.output('arraybuffer'), 'application/pdf'); S.mensaje = { tipo: 'ok', texto: r.id + ' · ' + r.paginas + ' p.' }; });
  const zip = () => accion(async () => {
    const r = await generarPDF(), e = await enlaceActual();
    const pk = P.construir(S.resultado, { pdf: new Uint8Array(r.doc.output('arraybuffer')), enlace: e && !e.demasiado_largo ? e.url : null, idioma: S.exp.idioma });
    descargar(nombreBase() + '.zip', pk.zip, 'application/zip');
    S.mensaje = { tipo: 'ok', texto: r.id + ' · ' + pk.archivos.length + ' archivos' };
  });
  const compartir = () => accion(async () => {
    const e = await enlaceActual(); S.enlace = e; S.mensaje = null;
    if (!e.demasiado_largo) { try { await navigator.clipboard.writeText(e.url); S.mensaje = { tipo: 'ok', texto: t('exp.copiado') }; } catch (x) { /* el campo de texto permite copiarlo a mano */ } }
  });
  async function abrirGuardado(archivo) {
    try {
      const txt = await archivo.text(); let res;
      try { res = JSON.parse(txt); } catch (e) { throw Object.assign(Error('json'), { codigo: 'json' }); }
      if (!A.verificar(res) || (res.perspectiva && !(PP && PP.verificar(res.perspectiva)))) { S.mensaje = { tipo: 'error', texto: t('restaurar.alterado') }; return render(); }
      const c = E.validar(res.consulta);
      S.consulta = c; S.resultado = res; S.origenResultado = 'guardado';
      S.area = Object.assign({}, res.area, { celdas: res.celdas });
      S.mensaje = { tipo: 'ok', texto: t('restaurar.guardado', { id: res.resultado_id }) };
      await verMapa(); dibujarArea(true); dibujarCeldas(); render();
    } catch (e) { avisar(e); }
  }

  // ------------------------------------------------------------------ restauración desde el enlace
  async function restaurarDesdeEnlace() {
    const fr = E.leerFragmento(location.hash);
    if (!fr) return false;
    abrirPestana();
    try {
      const bruto = await E.decodificar(fr.codigo), c = E.validar(bruto);
      S.consulta = c; S.exp.idioma = c.idioma; S.referenciaEnlace = fr.resultado_ref;
      let geom = c.area.geometria, proc = c.area.procedencia || { tipo: 'dibujo' }, admin = null;
      if (c.area.tipo === 'administrativa') {
        const ad = await cargarAdmin(), capa = c.area.admin.nivel === 'municipio' ? ad.mun : ad.dep;
        const f = capa.features.find(x => c.area.admin.nivel === 'municipio' ? String(x.properties.cod_municipio) === String(c.area.admin.codigo) : x.properties.nom_departamento === c.area.admin.nombre);
        if (!f) throw Object.assign(Error('unidad'), { codigo: 'unidad_no_encontrada' });
        geom = G.validar(f.geometry).geometria;
        if (c.area.hash_geometria && E.hashGeometria(geom) !== c.area.hash_geometria) S.mensajeLimites = t('error.limites_cambiaron');
        admin = adminDe(f, c.area.admin.nivel, capa); proc = procedenciaIneter(capa, c.area.admin.nivel);
      } else { await cargarAdmin().catch(() => null); }
      await verMapa();
      const ok = fijarArea(geom, c.area.tipo, proc, { id: c.area.id, nombre: c.area.nombre, radio_km: c.area.radio_km, sinEncuadre: true }, admin);
      if (!ok) return true;
      S.consulta = c; dibujarArea(true);
      S.mensaje = { tipo: 'info', texto: t('restaurar.ok') + (S.mensajeLimites ? ' ' + S.mensajeLimites : '') }; render();
      await analizar();
      if (S.mensajeLimites && S.mensaje) S.mensaje.texto += ' ' + S.mensajeLimites;
      render();
    } catch (e) { avisar(e); }
    return true;
  }
  function adminDe(f, nivel, capa) {
    const p = f.properties;
    return { pais: 'Nicaragua', departamento: p.nom_departamento, municipio: nivel === 'municipio' ? p.nom_municipio : null, nivel, codigo: nivel === 'municipio' ? String(p.cod_municipio) : null, nombre_unidad: nivel === 'municipio' ? p.nom_municipio : p.nom_departamento, area_oficial_km2: p.area_ineter_km2 || null, area_original_km2: p.area_geodesica_original_km2 };
  }
  function procedenciaIneter(capa, nivel) { const pr = capa.procedencia || {}; return { tipo: 'ineter', fuente: nivel === 'municipio' ? 'wsINETER-DGGC:Municipios' : 'wsINETER-DGGC:Departamentos', version: pr.version_limites || null, fecha_acceso: pr.fecha_acceso || null }; }
  function abrirPestana() { document.querySelector('nav button[data-tab="expediente"]')?.click(); }

  // ------------------------------------------------------------------ interfaz
  function campo(etq, control, ayuda) { return h('label', null, etq, control, ayuda ? h('small', { class: 'pista' }, ayuda) : null); }
  function selector(id, opciones, valor, onchange) {
    const s = h('select', { id, onchange }); opciones.forEach(([v, txt]) => s.append(h('option', { value: v, selected: String(v) === String(valor) }, txt))); return s;
  }
  function entrada(id, tipo, valor, attrs, oninput) { return h('input', Object.assign({ id, type: tipo, value: valor === null || valor === undefined ? '' : valor, oninput, onchange: oninput }, attrs || {})); }
  const anioMax = new Date().getUTCFullYear() - 1;

  function render() {
    const c = S.consulta, foco = document.activeElement && raiz.contains(document.activeElement) ? document.activeElement.id : null;
    raiz.replaceChildren();
    raiz.lang = c.idioma;
    // idioma
    raiz.append(h('div', { class: 'exp-cabecera' },
      h('div', null, h('h2', null, t('intro.titulo')), h('p', { class: 'pista' }, t('intro.texto'))),
      h('div', { class: 'exp-idioma', role: 'group', 'aria-label': t('consulta.idioma') },
        ...['es', 'en'].map(l => h('button', { type: 'button', 'aria-pressed': String(c.idioma === l), 'data-idioma': l, onclick: () => { if (window.GnomonI18n && window.GnomonI18n.setLanguage(l)) return; c.idioma = l; S.exp.idioma = l; try { localStorage.setItem('etd-exp-idioma', l); } catch (e) { } render(); } }, l.toUpperCase())))));
    if (S.mensaje) raiz.append(h('p', { id: 'exp-mensaje', class: 'exp-mensaje exp-' + S.mensaje.tipo, role: S.mensaje.tipo === 'error' ? 'alert' : 'status' }, S.mensaje.texto));

    // 1. área
    const a1 = h('article', { id: 'exp-paso-area' }, h('h3', null, t('paso.area')));
    const tipos = h('div', { class: 'botones-region', role: 'radiogroup', 'aria-label': t('paso.area') });
    ['punto', 'circulo', 'rectangulo', 'poligono', 'administrativa', 'archivo'].forEach(tp => {
      tipos.append(h('button', { type: 'button', role: 'radio', 'data-tipo': tp, 'aria-checked': String(S.modo === tp || (!S.modo && S.area && S.area.tipo === tp)), onclick: async () => { S.modo = tp; S.borrador = []; dibujarBorrador(); if (['punto', 'circulo', 'rectangulo', 'poligono'].includes(tp)) await verMapa(); if (tp === 'administrativa') cargarAdmin().then(render).catch(e => avisar(e)); render(); } }, t('area.' + tp)));
    });
    a1.append(tipos);
    const m = S.modo;
    if (m && m !== 'administrativa' && m !== 'archivo') a1.append(h('p', { class: 'pista' }, t('area.ayuda.' + m)));
    if (m === 'punto' || m === 'circulo') {
      const fila = h('div', { class: 'controles' },
        campo(t('area.lat'), entrada('exp-lat', 'number', '', { step: 'any', min: -90, max: 90 })),
        campo(t('area.lon'), entrada('exp-lon', 'number', '', { step: 'any', min: -180, max: 180 })));
      if (m === 'circulo') fila.append(campo(t('area.radio'), entrada('exp-radio', 'number', S.area && S.area.radio_km || 10, { step: 'any', min: 0.1, max: 500 })));
      fila.append(h('button', { type: 'button', id: 'exp-colocar', onclick: () => { const la = Number($('#exp-lat').value), lo = Number($('#exp-lon').value); if ($('#exp-lat').value === '' || $('#exp-lon').value === '') return avisar({ codigo: 'coordenada_invalida' }); if (m === 'punto') fijarArea({ type: 'Point', coordinates: [lo, la] }, 'punto', { tipo: 'coordenadas' }); else { const r = Number($('#exp-radio').value); fijarArea(G.circulo(lo, la, r), 'circulo', { tipo: 'coordenadas' }, { radio_km: r }); } } }, t('area.colocar')));
      a1.append(fila);
    }
    if (m === 'poligono') a1.append(h('div', { class: 'controles' },
      h('button', { type: 'button', id: 'exp-cerrar', disabled: S.borrador.length < 3, onclick: () => { const b = S.borrador.slice(); fijarArea({ type: 'Polygon', coordinates: [b.concat([b[0]])] }, 'poligono', { tipo: 'dibujo' }); } }, t('area.cerrar')),
      h('button', { type: 'button', disabled: !S.borrador.length, onclick: () => { S.borrador.pop(); dibujarBorrador(); render(); } }, t('area.deshacer'))));
    if (m === 'administrativa') a1.append(panelAdmin());
    if (m === 'archivo') a1.append(h('p', { class: 'pista' }, t('area.ayuda.archivo')), h('input', { type: 'file', id: 'exp-geojson', accept: '.geojson,.json,application/geo+json,application/json', onchange: async ev => {
      const f = ev.target.files[0]; if (!f) return;
      try { const g = JSON.parse(await f.text()); fijarArea(g, 'archivo', { tipo: 'archivo', fuente: f.name.slice(0, 120) }); await verMapa(); dibujarArea(true); } catch (e) { avisar(e.codigo ? e : { codigo: 'json' }); }
    } }));
    if (S.area) {
      a1.append(campo(t('area.nombre'), entrada('exp-nombre', 'text', S.area.nombre, { maxlength: 120 }, ev => { S.area.nombre = ev.target.value; })));
      a1.append(fichaArea());
      a1.append(h('div', { class: 'controles' }, h('button', { type: 'button', onclick: () => { S.area = null; S.resultado = null; S.modo = null; dibujarArea(); dibujarCeldas(); render(); } }, t('area.borrar'))));
    }
    raiz.append(a1);

    // 2. consulta
    const a2 = h('article', { id: 'exp-paso-consulta' }, h('h3', null, t('paso.consulta')));
    a2.append(campo(t('consulta.titulo'), entrada('exp-titulo', 'text', c.titulo, { maxlength: 160 }, ev => { c.titulo = ev.target.value; })));
    a2.append(h('div', { class: 'controles' },
      campo(t('consulta.variable'), selector('exp-variable', Object.values(F.VARIABLES).map(v => [v.id, (c.idioma === 'en' ? v.nombre_en : v.nombre) + ' · ' + v.unidad]), c.variable, ev => { c.variable = ev.target.value; S.resultado = null; render(); })),
      campo(t('consulta.meses'), selector('exp-temporada', Object.keys(TEMPORADAS).map(k => [k, t('consulta.temporada.' + k)]).concat(temporadaActual() === 'personalizada' ? [['personalizada', t('consulta.temporada.personalizada')]] : []), temporadaActual(), ev => { if (TEMPORADAS[ev.target.value]) c.meses = TEMPORADAS[ev.target.value].slice(); render(); }))));
    const meses = h('div', { class: 'exp-meses', role: 'group', 'aria-label': t('consulta.meses') });
    t('mes').forEach((nm, i) => meses.append(h('label', { class: 'chk' }, h('input', { type: 'checkbox', checked: c.meses.includes(i + 1), 'data-mes': i + 1, onchange: ev => { const k = i + 1; c.meses = ev.target.checked ? [...new Set(c.meses.concat(k))].sort((x, y) => x - y) : c.meses.filter(x => x !== k); if (!c.meses.length) c.meses = [k]; render(); } }), nm)));
    a2.append(meses);
    const anios = (id, val, fn) => entrada(id, 'number', val, { min: 1981, max: anioMax, step: 1 }, ev => fn(Number(ev.target.value)));
    a2.append(h('div', { class: 'controles' },
      campo(t('consulta.periodo'), h('span', { class: 'exp-rango' }, anios('exp-ini', c.periodo.inicio, v => { c.periodo.inicio = v; }), '–', anios('exp-fin', c.periodo.fin, v => { c.periodo.fin = v; }))),
      campo(t('consulta.referencia'), h('span', { class: 'exp-rango' }, anios('exp-ref-ini', c.referencia.inicio, v => { c.referencia.inicio = v; }), '–', anios('exp-ref-fin', c.referencia.fin, v => { c.referencia.fin = v; })))));
    a2.append(h('div', { class: 'controles' },
      campo(t('consulta.cobertura'), selector('exp-cobertura', [[1, '100 %'], [0.9, '90 %'], [0.75, '75 %']], c.calidad.min_cobertura_espacial, ev => { c.calidad.min_cobertura_espacial = Number(ev.target.value); })),
      campo(t('consulta.nivel'), selector('exp-nivel', [[0.9, '90 %'], [0.95, '95 %'], [0.99, '99 %']], c.estadistica.nivel, ev => { c.estadistica.nivel = Number(ev.target.value); }))));
    a2.append(h('div', { class: 'controles' },
      campo(t('consulta.capa'), selector('exp-capa', ['anomalia_anual', 'tendencia_celda', 'peso_celda'].map(k => [k, t('capa.' + k)]), c.vista.capa, ev => { c.vista.capa = ev.target.value; if (S.resultado) S.resultado.consulta.vista.capa = c.vista.capa; dibujarCeldas(); })),
      campo(t('consulta.anio_visible'), entrada('exp-anio-visible', 'number', c.vista.anio_visible || c.periodo.fin, { min: 1981, max: anioMax, step: 1 }, ev => { c.vista.anio_visible = Number(ev.target.value); }))));
    if (PP) {
      const pc = c.perspectiva;
      const fs = h('fieldset', { class: 'exp-secciones', id: 'exp-pp-config' }, h('legend', null, t('pp.config')),
        h('label', { class: 'chk' }, h('input', { type: 'checkbox', id: 'exp-pp-activa', checked: pc.activa !== false, onchange: ev => { pc.activa = ev.target.checked; render(); } }), t('pp.activa')));
      if (pc.activa !== false) {
        fs.append(h('div', { class: 'controles' },
          campo(t('pp.modelo'), selector('exp-pp-modelo', [['auto', t('pp.auto')]].concat(PP.MODELOS.map(m => [m.id || m, t('p.modelo.' + (m.id || m))])), pc.modelo, ev => { pc.modelo = ev.target.value; }))));
        const esc = h('div', { class: 'exp-meses', role: 'group', 'aria-label': t('pp.escenarios') }, h('span', { class: 'pista' }, t('pp.escenarios') + ': '));
        [['ssp245', 'SSP2-4.5'], ['ssp585', 'SSP5-8.5']].forEach(([k, nm]) => esc.append(h('label', { class: 'chk' }, h('input', { type: 'checkbox', 'data-escenario': k, checked: pc.escenarios.includes(k), onchange: ev => { pc.escenarios = ev.target.checked ? [...new Set(pc.escenarios.concat(k))] : pc.escenarios.filter(x => x !== k); } }), nm)));
        fs.append(esc, h('p', { class: 'pista' }, t('pp.config_ayuda')));
      }
      a2.append(fs);
    }
    a2.append(h('p', { class: 'pista' }, t('consulta.fecha_vs_periodo')), h('p', { class: 'pista' }, t('consulta.fuente_puntual')));
    raiz.append(a2);

    // 3. analizar
    const a3 = h('article', { id: 'exp-paso-analizar' }, h('h3', null, t('paso.analizar')),
      h('div', { class: 'controles' }, h('button', { type: 'button', id: 'exp-analizar', class: 'principal', disabled: S.ocupado || !S.area, onclick: analizar }, S.ocupado ? t('analizar.calculando') : t('analizar.boton'))),
      h('p', { id: 'exp-progreso', class: 'pista', role: 'status', 'aria-live': 'polite' }, S.area ? (S.area.celdas.length + ' × NASA POWER · ' + F.POWER.resolucion_espacial) : ''));
    raiz.append(a3);

    // 4. resultados
    if (S.resultado) raiz.append(panelResultados());
    if (S.resultado && PP) raiz.append(panelPerspectiva());
    // 5. exportar
    if (S.resultado) raiz.append(panelExportar());
    else raiz.append(h('article', null, h('h3', null, t('paso.exportar')), h('p', { class: 'pista' }, t('exp.abrir_ayuda')), botonAbrir()));
    if (foco) { const f = document.getElementById(foco); if (f) f.focus({ preventScroll: true }); }
  }

  function panelAdmin() {
    const cont = h('div', { class: 'exp-admin' });
    if (!S.admin) { cont.append(h('p', { class: 'pista', role: 'status' }, t('area.cargando_limites'))); return cont; }
    const deps = S.admin.dep.features.map(f => f.properties.nom_departamento).sort((a, b) => a.localeCompare(b, 'es'));
    S.depSel = S.depSel && deps.includes(S.depSel) ? S.depSel : deps[0];
    const muns = S.admin.mun.features.filter(f => f.properties.nom_departamento === S.depSel).sort((a, b) => a.properties.nom_municipio.localeCompare(b.properties.nom_municipio, 'es'));
    cont.append(h('div', { class: 'controles' },
      campo(t('area.departamento'), selector('exp-dep', deps.map(d => [d, d]), S.depSel, ev => { S.depSel = ev.target.value; S.munSel = ''; render(); })),
      campo(t('area.municipio'), selector('exp-mun', [['', '—']].concat(muns.map(f => [String(f.properties.cod_municipio), f.properties.nom_municipio])), S.munSel || '', ev => { S.munSel = ev.target.value; })),
      h('button', { type: 'button', id: 'exp-usar-admin', onclick: async () => {
        const esMun = !!S.munSel, capa = esMun ? S.admin.mun : S.admin.dep;
        const f = esMun ? capa.features.find(x => String(x.properties.cod_municipio) === S.munSel) : capa.features.find(x => x.properties.nom_departamento === S.depSel);
        const nivel = esMun ? 'municipio' : 'departamento', adm = adminDe(f, nivel, capa);
        if (fijarArea(f.geometry, 'administrativa', procedenciaIneter(capa, nivel), { nombre: adm.nombre_unidad, id: 'nic-' + nivel + '-' + (adm.codigo || E.sha256(adm.nombre_unidad).slice(0, 6)) }, adm)) { await verMapa(); dibujarArea(true); }
      } }, t('area.usar_admin'))));
    cont.append(h('p', { class: 'pista' }, t('proc.ineter') + ' · ' + (S.admin.mun.procedencia ? S.admin.mun.procedencia.simplificacion : '')));
    return cont;
  }

  function fichaArea() {
    const a = S.area, e = a.extension, filas = [];
    filas.push([t('ficha.id'), a.id]);
    filas.push([t('ficha.tipo'), t('area.' + a.tipo) + (a.radio_km ? ' · ' + num(a.radio_km, 2) + ' km' : '')]);
    filas.push([t('ficha.extension'), e.map(x => num(x, 4)).join(' ; ') + (e[0] > e[2] ? ' · ' + t('ficha.cruza') : '')]);
    filas.push([t('ficha.centro'), num(a.centro.lat, 5) + '°, ' + num(a.centro.lon, 5) + '° · ' + t('metodo.' + a.centro.metodo)]);
    filas.push([t('ficha.superficie'), a.superficie_km2 === null ? t('ficha.sin_superficie', { huella: num(a.celdas[0].area_celda_km2, 0), celda: a.celdas[0].id }) : num(a.superficie_km2, 2) + ' km²' + (a.admin && a.admin.area_oficial_km2 ? ' (INETER: ' + num(a.admin.area_oficial_km2, 2) + ' km²)' : '')]);
    filas.push([t('ficha.admin'), a.admin ? ['Nicaragua', a.admin.departamento, a.admin.municipio].filter(Boolean).join(' · ') + (a.admin.segun ? ' (' + t('ficha.centro').toLowerCase() + ')' : '') : t('na')]);
    filas.push([t('ficha.procedencia'), t('proc.' + (a.procedencia && a.procedencia.tipo || 'dibujo')) + (a.procedencia && a.procedencia.fuente ? ' · ' + a.procedencia.fuente : '')]);
    filas.push([t('ficha.version'), a.procedencia && a.procedencia.version || t('na')]);
    filas.push([t('res.celdas'), a.celdas.length + ' × ' + (S.consulta.idioma === 'en' ? F.POWER.resolucion_espacial_en : F.POWER.resolucion_espacial)]);
    const tb = h('table', { class: 'exp-ficha', id: 'exp-ficha' }, h('caption', null, t('area.ficha')));
    filas.forEach(([k, v]) => tb.append(h('tr', null, h('th', { scope: 'row' }, k), h('td', null, v))));
    return h('div', { class: 'tabla' }, tb);
  }

  function svgSerie(res) {
    const s = res.serie.filter(p => p.en_periodo), val = s.filter(p => p.valor !== null);
    if (val.length < 2) return null;
    const W = 520, H = 190, ml = 46, mr = 8, mt = 8, mb = 24, a0 = res.consulta.periodo.inicio, a1 = res.consulta.periodo.fin;
    const ys = val.map(p => p.valor), mn = Math.min(...ys), mx = Math.max(...ys), pad = (mx - mn) * .1 || 1;
    const X = a => ml + (a - a0) / Math.max(1, a1 - a0) * (W - ml - mr), Y = v => mt + (1 - (v - (mn - pad)) / (mx - mn + 2 * pad)) * (H - mt - mb);
    const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('class', 'exp-svg'); svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', t('res.serie') + ' ' + a0 + '–' + a1);
    const el = (tag, at) => { const n = document.createElementNS(ns, tag); Object.entries(at).forEach(([k, v]) => n.setAttribute(k, v)); svg.append(n); return n; };
    for (let k = 0; k <= 4; k++) { const v = mn - pad + (mx - mn + 2 * pad) * k / 4; el('line', { x1: ml, x2: W - mr, y1: Y(v), y2: Y(v), class: 'exp-rejilla' }); el('text', { x: ml - 4, y: Y(v) + 3, 'text-anchor': 'end', class: 'exp-eje' }).textContent = num(v, res.variable.decimales > 1 ? 1 : 0); }
    for (let a = Math.ceil(a0 / 10) * 10; a <= a1; a += 10) el('text', { x: X(a), y: H - 6, 'text-anchor': 'middle', class: 'exp-eje' }).textContent = a;
    let d = ''; s.forEach((p, i) => { if (p.valor === null) return; d += (i && s[i - 1].valor !== null ? 'L' : 'M') + X(p.anio).toFixed(1) + ' ' + Y(p.valor).toFixed(1); });
    el('path', { d, class: 'exp-linea' });
    val.forEach(p => el('circle', { cx: X(p.anio), cy: Y(p.valor), r: 2.2, class: 'exp-punto' }));
    const tr = (tt, cls) => { if (!tt) return; const f = a => tt.intercepto + tt.pendiente_decada / 10 * a; el('line', { x1: X(a0), x2: X(a1), y1: Y(f(a0)), y2: Y(f(a1)), class: cls }); };
    tr(res.tendencia.mco, 'exp-mco'); tr(res.tendencia.sen, 'exp-sen');
    s.filter(p => p.valor === null).forEach(p => { el('text', { x: X(p.anio), y: H - mb - 2, 'text-anchor': 'middle', class: 'exp-falta' }).textContent = '×'; });
    el('text', { x: 4, y: 12, class: 'exp-eje' }).textContent = res.variable.unidad;
    return svg;
  }

  const textoDesacuerdo = cmp => t('expl.desacuerdo.' + cmp.tipo, { fuente: cmp.fuente, region: cmp.region, periodo: cmp.periodo, valor: num(cmp.valor, 3), u: cmp.unidad, inf: num(cmp.inf, 3), sup: num(cmp.sup, 3) });
  function panelResultados() {
    const res = S.resultado, T = res.tendencia, R = res.resumen, u = res.variable.unidad, dec = res.variable.decimales, nivel = Math.round(T.nivel * 100);
    const art = h('article', { id: 'exp-resultados', 'data-resultado': res.resultado_id }, h('h3', null, t('paso.resultados')));
    if (S.origenResultado === 'guardado') art.append(h('p', { class: 'exp-sello' }, t('exp.enlace_resultado') + ' · ' + res.resultado_id));
    const dsc = A.desacuerdoFuentes(res), est = dsc ? 'desacuerdo' : T.veredicto.estado;
    art.append(h('div', { class: 'veredicto exp-veredicto', 'data-estado': est },
      h('div', { class: 'tarjeta' }, h('small', null, t('res.veredicto')), h('strong', { id: 'exp-veredicto' }, t('ver.' + est)), h('p', null, dsc ? textoDesacuerdo(dsc) : t('expl.' + est)))));
    const tj = h('div', { class: 'tarjetas' });
    const tarjeta = (id, tit, val, det) => tj.append(h('div', { class: 'tarjeta', id }, h('small', null, tit), h('strong', null, val), det ? h('p', null, det) : null));
    tarjeta('exp-sen', t('res.sen'), T.sen ? num(T.sen.pendiente_decada, dec + 1) + ' ' + t('res.por_decada', { u }) : t('na'), T.sen ? t('res.ic', { nivel, inf: num(T.sen.ic_inf_decada, dec + 1), sup: num(T.sen.ic_sup_decada, dec + 1) }) + ' · ' + t('res.mk') + ' ' + t('res.p', { p: T.sen.p_mann_kendall < 1e-4 ? '< ' + num(1e-4, 4) : '= ' + num(T.sen.p_mann_kendall, 4) }) : null);
    tarjeta('exp-mco', t('res.mco'), T.mco ? num(T.mco.pendiente_decada, dec + 1) + ' ± ' + num(T.mco.error_estandar_decada, dec + 1) : t('na'), T.mco ? t('res.ic', { nivel, inf: num(T.mco.ic_inf_decada, dec + 1), sup: num(T.mco.ic_sup_decada, dec + 1) }) : null);
    tarjeta('exp-media', t('res.media'), num(R.media, dec) + ' ' + u, (S.consulta.idioma === 'en' ? 'SD ' : 'desv. est. ') + num(R.desv_est, dec));
    tarjeta('exp-n', t('res.n'), R.n_validos + ' / ' + R.anios_periodo, (R.anio_inicio_efectivo || '–') + '–' + (R.anio_fin_efectivo || '–') + ' · ' + t('res.faltantes').toLowerCase() + ' ' + num(R.pct_anios_faltantes, 1) + ' %');
    tarjeta('exp-cobertura', t('res.cobertura'), res.cobertura.area_solicitada_km2 === null ? num(res.cobertura.huella_punto_km2, 0) + ' km²' : num(100 * res.cobertura.fraccion_cubierta, 1) + ' %',
      res.cobertura.area_solicitada_km2 === null ? t('ficha.sin_superficie', { huella: num(res.cobertura.huella_punto_km2, 0), celda: res.celdas[0].id }) : t('c.solicitada_cubierta', { sol: num(res.cobertura.area_solicitada_km2, 1), cub: num(res.cobertura.area_cubierta_km2, 1), pct: num(100 * res.cobertura.fraccion_cubierta, 1) }));
    art.append(tj);
    const g = svgSerie(res);
    if (g) art.append(h('figure', { class: 'exp-figura' }, g, h('figcaption', { class: 'pista' }, t('f.nota_serie'))));
    if (res.calidad.insuficiente) art.append(h('p', { class: 'exp-mensaje exp-error', id: 'exp-insuficiente' }, t('ver.faltan') + ': ' + res.calidad.motivos.map(mo => t('motivo.' + mo, { min: Math.max(res.consulta.calidad.min_anios, 10) })).join(' ') + ' ' + t('expl.faltan')));
    const av = h('ul', { class: 'lista exp-avisos', id: 'exp-avisos' });
    res.calidad.avisos.forEach(a => av.append(h('li', { 'data-aviso': a }, t('aviso.' + a, { huella: num(res.cobertura.huella_punto_km2 || res.celdas[0].area_celda_km2, 0), anios: res.calidad.anios_excluidos.join(', '), r1: num(T.r1_residuos, 2) }))));
    art.append(av);
    (res.comparaciones || []).forEach(cmp => art.append(h('p', { class: 'pista' }, t('g.literatura') + ': ' + t('g.comparacion_txt', { fuente: cmp.fuente, region: cmp.region, periodo: cmp.periodo, valor: num(cmp.valor, 3), u: cmp.unidad, inf: num(cmp.inf, 3), sup: num(cmp.sup, 3) }))));
    art.append(h('p', { class: 'pista' }, t('g.no_pronostico')));
    art.append(h('p', { class: 'pista exp-ids' }, t('inf.resultado') + ': ', h('code', { id: 'exp-resultado-id' }, res.resultado_id), ' · ' + t('inf.consulta') + ': ', h('code', null, res.consulta_id)));
    return art;
  }

  function botonAbrir() {
    return h('label', { class: 'exp-abrir' }, t('exp.abrir'), h('input', { type: 'file', id: 'exp-abrir', accept: '.json,application/json', onchange: ev => { const f = ev.target.files[0]; if (f) abrirGuardado(f); } }));
  }

  function panelExportar() {
    const ex = S.exp, art = h('article', { id: 'exp-exportar' }, h('h3', null, t('paso.exportar')));
    art.append(h('div', { class: 'controles' },
      campo(t('exp.idioma'), selector('exp-inf-idioma', [['es', 'Español'], ['en', 'English']], ex.idioma, ev => { ex.idioma = ev.target.value; })),
      campo(t('exp.plantilla'), selector('exp-plantilla', [['resumen', t('exp.resumen')], ['completo', t('exp.completo')]], ex.plantilla, ev => { ex.plantilla = ev.target.value; ex.secciones = (ex.plantilla === 'resumen' ? INF.RESUMEN : INF.SECCIONES).slice(); render(); }))));
    const secs = h('fieldset', { class: 'exp-secciones' }, h('legend', null, t('exp.secciones')));
    INF.SECCIONES.forEach(s => secs.append(h('label', { class: 'chk' }, h('input', { type: 'checkbox', checked: ex.secciones.includes(s), 'data-seccion': s, onchange: ev => { ex.secciones = ev.target.checked ? INF.SECCIONES.filter(x => x === s || ex.secciones.includes(x)) : ex.secciones.filter(x => x !== s); } }), s + '. ' + t('sec.' + s, S.resultado && S.resultado.perspectiva && S.resultado.perspectiva.horizonte ? { ini: S.resultado.perspectiva.horizonte.inicio, fin: S.resultado.perspectiva.horizonte.fin } : { ini: '', fin: '' }).replace(/:\s*–$/, ''))));
    art.append(secs);
    art.append(h('div', { class: 'controles' },
      campo(t('exp.autor'), entrada('exp-autor', 'text', ex.autor, { maxlength: 120 }, ev => { ex.autor = ev.target.value; })),
      campo(t('exp.organizacion'), entrada('exp-org', 'text', ex.organizacion, { maxlength: 120 }, ev => { ex.organizacion = ev.target.value; }))));
    const notas = h('textarea', { id: 'exp-notas', rows: 3, maxlength: 4000, oninput: ev => { ex.notas = ev.target.value; } }); notas.value = ex.notas;
    art.append(campo(t('exp.notas'), notas, t('exp.notas_ayuda')));
    art.append(h('div', { class: 'controles' },
      h('button', { type: 'button', id: 'exp-pdf', disabled: S.ocupado, onclick: pdf }, t('exp.pdf')),
      h('button', { type: 'button', id: 'exp-zip', disabled: S.ocupado, onclick: zip }, t('exp.zip')),
      h('button', { type: 'button', id: 'exp-compartir', disabled: S.ocupado, onclick: compartir }, t('exp.compartir'))));
    if (S.enlace && S.resultado && S.enlace.url.indexOf(S.resultado.resultado_id) > 0) {
      const e = S.enlace, caja = h('div', { class: 'exp-enlaces', id: 'exp-enlaces' });
      caja.append(h('h4', null, t('exp.enlace_consulta')), h('p', { class: 'pista' }, t('exp.enlace_consulta_ayuda')));
      if (e.demasiado_largo) caja.append(h('p', { class: 'exp-mensaje exp-error' }, t('exp.largo', { max: E.MAX_URL })));
      else {
        const inp = h('input', { type: 'text', id: 'exp-enlace', readonly: true, value: e.url, onfocus: ev => ev.target.select() });
        caja.append(inp, h('div', { class: 'controles' }, h('button', { type: 'button', onclick: async () => { try { await navigator.clipboard.writeText(e.url); S.mensaje = { tipo: 'ok', texto: t('exp.copiado') }; } catch (x) { inp.select(); } render(); } }, t('exp.copiar')), h('a', { class: 'boton', href: e.url, target: '_blank', rel: 'noopener' }, '↗')));
        if (!e.compartible || e.local) caja.append(h('p', { class: 'exp-mensaje exp-info' }, t('exp.localhost')));
        if (e.local) caja.append(h('p', { class: 'pista' }, 'Local: ', h('a', { id: 'exp-enlace-local', href: e.local }, e.local.slice(0, 80) + '…')));
      }
      caja.append(h('h4', null, t('exp.enlace_resultado')), h('p', { class: 'pista' }, t('exp.enlace_resultado_ayuda')));
      art.append(caja);
    }
    art.append(h('p', { class: 'pista' }, t('exp.abrir_ayuda')), botonAbrir());
    return art;
  }

  // ------------------------------------------------------------------ arranque
  const boton = document.querySelector('nav button[data-tab="expediente"]');
  document.addEventListener('sicc:vista', () => { if (S.area) { dibujarArea(false); dibujarCeldas(); } });
  render();
  window.ETDExpediente = { estado: S, analizar, render, restaurar: restaurarDesdeEnlace, abrirGuardado, generarPDF: async () => { const r = await generarPDF(); return { id: r.id, paginas: r.paginas, bytes: new Uint8Array(r.doc.output('arraybuffer')) }; }, paquete: async () => { const r = await generarPDF(), e = await enlaceActual(); return P.construir(S.resultado, { pdf: new Uint8Array(r.doc.output('arraybuffer')), enlace: e && !e.demasiado_largo ? e.url : null, idioma: S.exp.idioma }); }, enlace: enlaceActual };
  if (boton) boton.addEventListener('click', () => { if (S.area) { dibujarArea(false); dibujarCeldas(); } });
  addEventListener('hashchange', () => { if (E.leerFragmento(location.hash)) restaurarDesdeEnlace(); });
  document.addEventListener('gnomon:languagechange', () => { const l = idiomaApp(); if (S.consulta.idioma === l && S.exp.idioma === l) return; S.consulta.idioma = l; S.exp.idioma = l; render(); });
  restaurarDesdeEnlace();
})();
