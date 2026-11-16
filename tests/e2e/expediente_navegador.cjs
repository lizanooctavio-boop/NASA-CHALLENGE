/*
 * Recorrido de extremo a extremo del expediente por área en Chromium (Playwright).
 *
 * Uso: node tests/e2e/expediente_navegador.cjs <carpeta_salida>
 *   ETD_NODE_MODULES=/ruta/node_modules  sirve leaflet, chart.js, three y proj4 desde npm cuando el entorno no
 *                                        alcanza los CDN (si no se indica, se usan los CDN reales).
 * NASA POWER se sustituye por las respuestas reales guardadas en tests/fixtures/expediente/ (descargadas el
 * 2026-11-15), para que el resultado sea reproducible. Las teselas externas se bloquean.
 *
 * Escribe <salida>/resumen.json con las comprobaciones y deja los PDF, ZIP y enlaces generados.
 */
const fs = require('fs'), path = require('path'), http = require('http'), zlib = require('zlib');
const { chromium } = require('playwright');

const RAIZ = path.resolve(__dirname, '..', '..');
const SALIDA = path.resolve(process.argv[2] || path.join(RAIZ, 'tests', 'salida_expediente'));
const NM = process.env.ETD_NODE_MODULES || null;
fs.mkdirSync(SALIDA, { recursive: true });
const FIX = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(RAIZ, 'tests/fixtures/expediente/power_nicaragua_2026-11-15.json.gz'))));

const TIPOS = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.geojson': 'application/geo+json', '.jpg': 'image/jpeg', '.png': 'image/png', '.csv': 'text/csv', '.gz': 'application/gzip' };
function servidor() {
  return new Promise(ok => {
    const s = http.createServer((req, res) => {
      const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      let f = path.join(RAIZ, u === '/' ? 'index.html' : u);
      if (!f.startsWith(RAIZ) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'Content-Type': TIPOS[path.extname(f)] || 'application/octet-stream' });
      fs.createReadStream(f).pipe(res);
    });
    s.listen(0, '127.0.0.1', () => ok(s));
  });
}

const CDN = [
  [/unpkg\.com\/leaflet@1\.9\.4\/dist\/(.*)$/, m => path.join(NM, 'leaflet/dist', m[1])],
  [/cdn\.jsdelivr\.net\/npm\/chart\.js@4\.4\.1\/dist\/(.*)$/, m => path.join(NM, 'chart.js/dist', m[1])],
  [/cdn\.jsdelivr\.net\/npm\/three@0\.160\.0\/(.*)$/, m => path.join(NM, 'three', m[1])],
  [/cdnjs\.cloudflare\.com\/ajax\/libs\/proj4js\/2\.9\.2\/proj4\.js$/, () => path.join(NM, 'proj4/dist/proj4.js')]
];
let peticionesPower = 0, powerFalla = false, peticionesImagen = 0;
const RAIZ_PRUEBA = path.resolve(__dirname, '..', '..');
async function rutas(ctx) {
  await ctx.route('**/*', async route => {
    const url = route.request().url();
    if (url.startsWith('http://127.0.0.1')) return route.continue();
    if (url.startsWith('https://power.larc.nasa.gov/')) {
      peticionesPower++;
      if (powerFalla) return route.abort('internetdisconnected');
      const q = new URL(url).searchParams, k = Number(q.get('latitude')).toFixed(4) + '_' + Number(q.get('longitude')).toFixed(4);
      const r = FIX.respuestas[k];
      if (!r) return route.fulfill({ status: 422, contentType: 'application/json', body: JSON.stringify({ messages: ['fuera de la caja de prueba'] }) });
      const p = q.get('parameters'), copia = JSON.parse(JSON.stringify(r));
      copia.properties.parameter = { [p]: r.properties.parameter[p] }; copia.parameters = { [p]: r.parameters[p] };
      return route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: JSON.stringify(copia) });
    }
    // mapa satelital del informe: imágenes sintéticas de prueba (no del lugar) con las mismas cabeceras CORS que Esri
    // ETD_ESRI_DIR: imágenes reales de Esri ya descargadas para Masaya (para el ejemplo); si no, las sintéticas
    if (process.env.ETD_ESRI_DIR && /arcgisonline\.com.*\/export/.test(url)) {
      const pre = url.includes('bbox=-86.36136,') ? 'portada' : url.includes('bbox=-86.66507,') ? 'detalle' : null;
      const capa = /World_Imagery/.test(url) ? 'img.jpg' : /Boundaries/.test(url) ? 'lim.png' : 'vias.png';
      const f = pre && path.join(process.env.ETD_ESRI_DIR, pre + '_' + capa);
      if (f && fs.existsSync(f)) { peticionesImagen++; return route.fulfill({ status: 200, contentType: capa.endsWith('jpg') ? 'image/jpeg' : 'image/png', headers: { 'access-control-allow-origin': '*' }, path: f }); }
    }
    if (/server\.arcgisonline\.com\/ArcGIS\/rest\/services\/World_Imagery\/MapServer\/export/.test(url)) { peticionesImagen++; return route.fulfill({ status: 200, contentType: 'image/jpeg', headers: { 'access-control-allow-origin': '*' }, path: path.join(RAIZ_PRUEBA, 'tests/fixtures/expediente/portada_prueba.jpg') }); }
    if (/server\.arcgisonline\.com\/ArcGIS\/rest\/services\/Reference\/.*\/MapServer\/export/.test(url)) { peticionesImagen++; return route.fulfill({ status: 200, contentType: 'image/png', headers: { 'access-control-allow-origin': '*' }, path: path.join(RAIZ_PRUEBA, 'tests/fixtures/expediente/etiquetas_prueba.png') }); }
    if (NM) for (const [re, f] of CDN) { const m = url.match(re); if (m) { let file = f(m); if (!fs.existsSync(file)) file = file.replace('.min.js', '.js'); if (fs.existsSync(file)) return route.fulfill({ path: file, contentType: TIPOS[path.extname(file)] || 'text/javascript' }); } }
    if (/unpkg|jsdelivr|cdnjs/.test(url) && !NM) return route.continue();
    return route.fulfill({ status: 404, body: '' }); // teselas y servicios en vivo: fuera de la prueba
  });
}

function leerZip(buf) {
  const archivos = {}; let p = 0;
  while (buf.readUInt32LE(p) === 0x04034b50) {
    const tam = buf.readUInt32LE(p + 18), nl = buf.readUInt16LE(p + 26), el = buf.readUInt16LE(p + 28);
    const nombre = buf.slice(p + 30, p + 30 + nl).toString('utf8'), ini = p + 30 + nl + el;
    archivos[nombre] = buf.slice(ini, ini + tam); p = ini + tam;
  }
  return archivos;
}
const sha = b => require('crypto').createHash('sha256').update(b).digest('hex');

async function abrir(ctx, url, errores) {
  const page = await ctx.newPage();
  page.on('pageerror', e => errores.push({ tipo: 'pageerror', texto: String(e) }));
  page.on('console', m => { if (m.type() === 'error') errores.push({ tipo: 'console', texto: m.text(), url: (m.location() || {}).url || '' }); });
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.ETDExpediente && typeof mapa !== 'undefined' && mapa, null, { timeout: 120000 });
  return page;
}
async function pestana(page) { await page.click('nav button[data-tab="expediente"]'); await page.waitForSelector('#exp-paso-area'); }
async function esperarResultado(page) {
  await page.waitForFunction(() => { const S = window.ETDExpediente.estado; return !S.ocupado && (S.resultado || (S.mensaje && S.mensaje.tipo === 'error')); }, null, { timeout: 180000 });
}
async function descargarCon(page, sel, nombre) {
  const [d] = await Promise.all([page.waitForEvent('download', { timeout: 120000 }), page.click(sel)]);
  const f = path.join(SALIDA, nombre); await d.saveAs(f); return f;
}
async function clicMapa(page, lat, lon) {
  const p = await page.evaluate(([la, lo]) => { const q = mapa.latLngToContainerPoint([la, lo]), r = document.getElementById('mapa').getBoundingClientRect(); return [r.left + q.x, r.top + q.y]; }, [lat, lon]);
  await page.mouse.click(p[0], p[1]);
}

(async () => {
  const srv = await servidor(), base = `http://127.0.0.1:${srv.address().port}/`;
  const navegador = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const R = { base, casos: {}, errores_consola: [] };
  const errores = R.errores_consola;
  try {
    // ---------------- 1. Municipio de Nicaragua (Masaya), español, informe completo, ZIP y enlace
    let ctx = await navegador.newContext({ acceptDownloads: true, viewport: { width: 1440, height: 1000 }, locale: 'es-NI' });
    await rutas(ctx);
    let page = await abrir(ctx, base, errores);
    await pestana(page);
    await page.click('[data-idioma="es"]');
    await page.click('[data-tipo="administrativa"]');
    await page.waitForSelector('#exp-dep');
    await page.selectOption('#exp-dep', 'Masaya');
    await page.waitForSelector('#exp-mun option:nth-child(3)', { state: 'attached' });
    const codMasaya = await page.evaluate(() => [...document.querySelectorAll('#exp-mun option')].find(o => o.textContent === 'Masaya').value);
    await page.selectOption('#exp-mun', codMasaya);
    await page.click('#exp-usar-admin');
    await page.waitForSelector('#exp-ficha');
    await page.fill('#exp-titulo', 'Temperatura del aire en el municipio de Masaya');
    await page.selectOption('#exp-variable', 'T2M');
    await page.click('#exp-analizar');
    await esperarResultado(page);
    const mun = await page.evaluate(() => { const S = window.ETDExpediente.estado; return { id: S.resultado && S.resultado.resultado_id, ui_id: document.getElementById('exp-resultado-id')?.textContent, veredicto: document.getElementById('exp-veredicto')?.textContent, geom: S.area.geometria, capa: (() => { let g = null; mapa.eachLayer(l => { if (l instanceof L.Polygon && l.options.color === '#ff4d5e') g = l.toGeoJSON().geometry; }); return g; })(), avisos: S.resultado.calidad.avisos, sen: S.resultado.tendencia.sen, n: S.resultado.resumen.n_validos, sup: S.resultado.area.superficie_km2, admin: S.resultado.area.admin, mensaje: S.mensaje }; });
    R.casos.municipio = mun;
    await page.screenshot({ path: path.join(SALIDA, 'municipio_panel.png') });
    const pdfMun = await descargarCon(page, '#exp-pdf', 'municipio_masaya_completo_es.pdf');
    const zipMun = await descargarCon(page, '#exp-zip', 'municipio_masaya_expediente.zip');
    const zf = leerZip(fs.readFileSync(zipMun)), man = JSON.parse(zf['manifest.json']);
    R.casos.municipio.zip = { archivos: Object.keys(zf), hashes_ok: man.archivos.every(a => sha(zf[a.nombre]) === a.sha256), resultado_id: JSON.parse(zf['resultados.json']).resultado_id, geom_zip: JSON.parse(zf['area_interes.geojson']).features[0].geometry, enlace: man.enlace_consulta };
    for (const n of Object.keys(zf)) fs.writeFileSync(path.join(SALIDA, 'zip_' + n), zf[n]);
    R.casos.municipio.pdf = pdfMun;
    await page.click('#exp-compartir');
    await page.waitForSelector('#exp-enlace');
    const enlaces = await page.evaluate(() => ({ publico: document.getElementById('exp-enlace').value, local: document.getElementById('exp-enlace-local')?.getAttribute('href') }));
    R.casos.municipio.enlaces = enlaces;
    const vistaOriginal = await page.evaluate(() => window.ETDExpediente.estado.resultado.consulta);

    // ---------------- 1b. Departamento (varias celdas) para el informe de ejemplo
    await page.click('[data-tipo="administrativa"]');
    await page.waitForSelector('#exp-dep');
    await page.selectOption('#exp-dep', 'Matagalpa');
    await page.selectOption('#exp-mun', '');
    await page.click('#exp-usar-admin');
    await page.waitForFunction(() => window.ETDExpediente.estado.area && window.ETDExpediente.estado.area.nombre === 'Matagalpa');
    await page.fill('#exp-titulo', 'Temperatura del aire en el departamento de Matagalpa, 1981-2024');
    await page.click('#exp-analizar');
    await esperarResultado(page);
    await page.fill('#exp-autor', 'Earth System Trend Detective (ejemplo)');
    await page.click('#exp-compartir');
    await page.waitForSelector('#exp-enlace');
    R.casos.departamento = await page.evaluate(() => { const r = window.ETDExpediente.estado.resultado; return { id: r.resultado_id, celdas: r.celdas.length, veredicto: document.getElementById('exp-veredicto').textContent, enlace: document.getElementById('exp-enlace').value, local: document.getElementById('exp-enlace-local')?.getAttribute('href'), sen: r.tendencia.sen, cobertura: r.cobertura }; });
    R.casos.departamento.perspectiva = await page.evaluate(() => { const p = window.ETDExpediente.estado.resultado.perspectiva; return p && { id: p.perspectiva_id, horizonte: p.horizonte, destacadas: p.destacadas, filas: document.querySelectorAll('.exp-pp-tabla tr[data-indicador]').length, indicadores: p.indicadores.length, clases: p.indicadores.map(o => [o.id, o.clasificacion.clase]) }; });
    if (!R.casos.departamento.perspectiva || R.casos.departamento.perspectiva.filas !== R.casos.departamento.perspectiva.indicadores) throw Error('perspectiva ausente en el panel');
    await page.locator('#exp-perspectiva').screenshot({ path: path.join(SALIDA, 'perspectiva_panel.png') });
    R.casos.departamento.pdf = await descargarCon(page, '#exp-pdf', 'ejemplo_matagalpa_completo_es.pdf');
    R.casos.departamento.zip = await descargarCon(page, '#exp-zip', 'ejemplo_matagalpa_expediente.zip');
    await page.selectOption('#exp-inf-idioma', 'en');
    await page.selectOption('#exp-plantilla', 'resumen');
    R.casos.departamento.pdf_en = await descargarCon(page, '#exp-pdf', 'ejemplo_matagalpa_resumen_en.pdf');
    await page.screenshot({ path: path.join(SALIDA, 'departamento_panel.png') });
    await ctx.close();

    // ---------------- 2. El enlace en otra sesión restaura la consulta completa
    ctx = await navegador.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 900 }, locale: 'en-US' });
    await rutas(ctx);
    page = await abrir(ctx, enlaces.local, errores);
    await esperarResultado(page);
    const rest = await page.evaluate(() => { const S = window.ETDExpediente.estado; const c = mapa.getCenter(); return { id: S.resultado && S.resultado.resultado_id, consulta: S.resultado && S.resultado.consulta, geom: S.area.geometria, mensaje: S.mensaje, idioma: document.getElementById('exp-raiz').lang, pestana: !document.getElementById('expediente').hidden, centro: [c.lat, c.lng], zoom: mapa.getZoom() }; });
    // misma consulta científica, mismo idioma, capa, año visible y escala; el centro puede diferir por redondeo del mapa
    const sinVista = c => Object.assign({}, c, { vista: Object.assign({}, c.vista, { centro: null }) });
    rest.consulta_igual = JSON.stringify(sinVista(rest.consulta)) === JSON.stringify(sinVista(vistaOriginal));
    rest.centro_original = vistaOriginal.vista.centro; rest.zoom_original = vistaOriginal.vista.zoom;
    R.casos.restaurar = rest;
    await page.screenshot({ path: path.join(SALIDA, 'restaurado.png') });
    // resultado guardado: abrir resultados.json sin descargar datos
    const antes = peticionesPower;
    await page.setInputFiles('#exp-abrir', path.join(SALIDA, 'zip_resultados.json'));
    await page.waitForSelector('.exp-sello');
    R.casos.guardado = await page.evaluate(() => ({ id: window.ETDExpediente.estado.resultado.resultado_id, origen: window.ETDExpediente.estado.origenResultado }));
    R.casos.guardado.peticiones_nuevas = peticionesPower - antes;
    // archivo alterado
    const alterado = JSON.parse(fs.readFileSync(path.join(SALIDA, 'zip_resultados.json')));
    alterado.datos_celdas[Object.keys(alterado.datos_celdas)[0]]['2000-01'] += 1;
    fs.writeFileSync(path.join(SALIDA, 'alterado.json'), JSON.stringify(alterado));
    await page.setInputFiles('#exp-abrir', path.join(SALIDA, 'alterado.json'));
    await page.waitForFunction(() => window.ETDExpediente.estado.mensaje && window.ETDExpediente.estado.mensaje.tipo === 'error');
    R.casos.alterado = await page.evaluate(() => window.ETDExpediente.estado.mensaje.texto);
    await ctx.close();

    // ---------------- 3. Punto (inglés): no se describe como promedio de un área
    ctx = await navegador.newContext({ acceptDownloads: true, viewport: { width: 390, height: 844 }, locale: 'en-US', isMobile: true, hasTouch: true });
    await rutas(ctx);
    page = await abrir(ctx, base, errores);
    await pestana(page);
    await page.click('[data-idioma="en"]');
    await page.click('[data-tipo="punto"]');
    await page.fill('#exp-lat', '12.1364'); await page.fill('#exp-lon', '-86.2514');
    await page.click('#exp-colocar');
    await page.selectOption('#exp-variable', 'PRECTOTCORR');
    await page.click('#exp-analizar');
    await esperarResultado(page);
    R.casos.punto = await page.evaluate(() => { const S = window.ETDExpediente.estado; return { id: S.resultado.resultado_id, avisos: S.resultado.calidad.avisos, aviso_txt: document.querySelector('[data-aviso="consulta_puntual"]')?.textContent, ficha: document.getElementById('exp-ficha')?.textContent, superficie: S.resultado.area.superficie_km2, huella: S.resultado.cobertura.huella_punto_km2, admin: S.resultado.area.admin, veredicto: document.getElementById('exp-veredicto').textContent }; });
    await page.screenshot({ path: path.join(SALIDA, 'punto_movil.png'), fullPage: false });
    await page.selectOption('#exp-inf-idioma', 'en');
    await page.selectOption('#exp-plantilla', 'resumen');
    R.casos.punto.pdf = await descargarCon(page, '#exp-pdf', 'punto_managua_resumen_en.pdf');
    await ctx.close();

    // ---------------- 4. Polígono irregular dibujado con clics sobre el mapa
    ctx = await navegador.newContext({ acceptDownloads: true, viewport: { width: 1440, height: 1000 }, locale: 'es-NI' });
    await rutas(ctx);
    page = await abrir(ctx, base, errores);
    await pestana(page);
    await page.click('[data-idioma="es"]');
    await page.click('[data-tipo="poligono"]');
    await page.waitForFunction(() => document.body.classList.contains('modo-mapa'), null, { timeout: 60000 });
    await page.evaluate(() => { mapa.fitBounds([[12.2, -86.5], [13.6, -85.1]], { paddingTopLeft: [920, 120], paddingBottomRight: [40, 80], animate: false }); }); // el área queda a la derecha del panel
    await page.waitForTimeout(400);
    const vertices = [[13.55, -86.45], [13.5, -85.3], [12.95, -85.15], [12.9, -85.85], [12.35, -85.6], [12.25, -86.35], [12.85, -86.15]]; // forma en «C»
    for (const [la, lo] of vertices) await clicMapa(page, la, lo);
    await page.click('#exp-cerrar');
    await page.waitForSelector('#exp-ficha');
    await page.selectOption('#exp-temporada', 'lluviosa');
    await page.selectOption('#exp-variable', 'PRECTOTCORR');
    await page.click('#exp-analizar');
    await esperarResultado(page);
    R.casos.poligono = await page.evaluate(() => { const S = window.ETDExpediente.estado, r = S.resultado; return { id: r.resultado_id, celdas: r.celdas.length, pesos: r.celdas.reduce((s, c) => s + c.peso, 0), sup: r.area.superficie_km2, inter: r.celdas.reduce((s, c) => s + c.interseccion_km2, 0), centro: r.area.centro, meses: r.consulta.meses, geom: r.area.geometria, veredicto: document.getElementById('exp-veredicto').textContent }; });
    await page.screenshot({ path: path.join(SALIDA, 'poligono_mapa.png') });
    R.casos.poligono.pdf = await descargarCon(page, '#exp-pdf', 'poligono_irregular_completo_es.pdf');

    // ---------------- 5. Datos insuficientes: 6 años
    await page.fill('#exp-ini', '2015'); await page.fill('#exp-fin', '2020');
    await page.click('#exp-analizar');
    await esperarResultado(page);
    R.casos.insuficiente = await page.evaluate(() => { const r = window.ETDExpediente.estado.resultado; return { estado: r.tendencia.veredicto.estado, sen: r.tendencia.sen, texto: document.getElementById('exp-insuficiente')?.textContent, veredicto: document.getElementById('exp-veredicto').textContent }; });

    // ---------------- 6. Error de red de la fuente
    powerFalla = true;
    await page.fill('#exp-ini', '1981'); await page.fill('#exp-fin', '2024');
    await page.click('#exp-analizar');
    await esperarResultado(page);
    R.casos.red = await page.evaluate(() => ({ mensaje: window.ETDExpediente.estado.mensaje, hay_resultado: !!window.ETDExpediente.estado.resultado }));
    powerFalla = false;

    // ---------------- 7. GeoJSON inválido (lazo autointersecado) y fuera de rango
    await page.click('[data-tipo="archivo"]');
    const lazo = path.join(SALIDA, 'lazo.geojson'), rango = path.join(SALIDA, 'rango.geojson');
    fs.writeFileSync(lazo, JSON.stringify({ type: 'Polygon', coordinates: [[[-86, 12], [-85, 13], [-85, 12], [-86, 13], [-86, 12]]] }));
    fs.writeFileSync(rango, JSON.stringify({ type: 'Polygon', coordinates: [[[12, -86], [13, -86], [13, -95], [12, -86]]] }));
    await page.setInputFiles('#exp-geojson', lazo);
    await page.waitForSelector('#exp-mensaje');
    R.casos.geojson_invalido = await page.textContent('#exp-mensaje');
    await page.setInputFiles('#exp-geojson', rango);
    await page.waitForFunction(() => /rango/.test(document.getElementById('exp-mensaje')?.textContent || ''));
    R.casos.geojson_rango = await page.textContent('#exp-mensaje');
    await ctx.close();

    // ---------------- 8. Enlace dañado y de versión futura
    ctx = await navegador.newContext({ viewport: { width: 1280, height: 900 } });
    await rutas(ctx);
    page = await abrir(ctx, base + '#inv=zAAAA!!', errores);
    await page.waitForSelector('#exp-mensaje');
    R.casos.enlace_corrupto = await page.textContent('#exp-mensaje');
    const futura = Buffer.from(JSON.stringify({ esquema: 'etd-consulta', version: 9 })).toString('base64url');
    await page.goto(base + '#inv=j' + futura); await page.reload();
    await page.waitForFunction(() => window.ETDExpediente && /versi/i.test(document.getElementById('exp-mensaje')?.textContent || ''), null, { timeout: 120000 });
    R.casos.enlace_futuro = await page.textContent('#exp-mensaje');
    await ctx.close();
  } catch (e) {
    R.fallo = String(e && e.stack || e);
  } finally {
    await navegador.close(); srv.close();
    R.peticiones_imagen = peticionesImagen;
    fs.writeFileSync(path.join(SALIDA, 'resumen.json'), JSON.stringify(R, null, 1));
    console.log(JSON.stringify({ salida: SALIDA, fallo: R.fallo || null }));
  }
})();
