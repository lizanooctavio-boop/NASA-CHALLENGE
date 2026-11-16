/*
 * Comprobaciones de la perspectiva de la próxima década (src/expediente/perspectiva.js) en Node.
 * Imprime un JSON que tests/test_perspectiva.py contrasta con implementaciones independientes en Python.
 * Datos: respuestas reales de NASA POWER (tests/fixtures/expediente/) e insumos del repositorio
 * (data/fenomenos/indices_anuales_celdas.csv, gistemp_nicaragua.csv, data/expediente/cmip6_regional_mensual.csv).
 */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const R = path.resolve(__dirname, '..');
const G = require(R + '/src/expediente/geo.js'), E = require(R + '/src/expediente/estado.js'), F = require(R + '/src/expediente/fuentes.js');
const A = require(R + '/src/expediente/analisis.js'), P = require(R + '/src/expediente/paquete.js'), INF = require(R + '/src/expediente/informe.js');
const PP = require(R + '/src/expediente/perspectiva.js');
const { jsPDF } = require(R + '/app/vendor/jspdf.umd.min.js'), qrcode = require(R + '/app/vendor/qrcode-generator.js');
const FIX = JSON.parse(zlib.gunzipSync(fs.readFileSync(R + '/tests/fixtures/expediente/power_nicaragua_2026-11-15.json.gz')));
const salida = process.argv[2] || null;
const leer = f => fs.readFileSync(R + '/' + f, 'utf8');

const fetchFix = async url => {
  const q = new URL(url).searchParams, r = FIX.respuestas[Number(q.get('latitude')).toFixed(4) + '_' + Number(q.get('longitude')).toFixed(4)];
  if (!r) return { ok: false, status: 503, json: async () => ({}) };
  return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(r)) };
};

// Serie sintética reproducible: tendencia + AR(1).
function sintetica(semilla, n, pendiente, phi, sd, inicio) {
  const g = PP.generador(semilla), anios = [], valores = [];
  let e = 0;
  for (let i = 0; i < n; i++) { e = phi * e + sd * Math.sqrt(1 - phi * phi) * g.normal(); anios.push(inicio + i); valores.push(10 + pendiente * i + e); }
  return { anios, valores };
}
const ind = (id, s, extra) => Object.assign({ id, nombre: id, nombre_en: id, unidad: 'u', decimales: 2, anios: s.anios, valores: s.valores, fuente: 'sintética', tipo_dato: 'prueba', origen: 'prueba' }, extra || {});

(async () => {
  const out = {};
  // ---- Mann-Kendall modificado y BH: entradas y salidas para recalcular en Python
  out.mk = [[1, 44, 0, 0, 1], [2, 44, 0.02, 0.6, 0.5], [3, 60, 0.0, 0.8, 1], [4, 30, 0.05, 0.3, 0.4]].map(([sem, n, b, phi, sd]) => {
    const s = sintetica(sem, n, b, phi, sd, 1981), sen = require(R + '/src/estadistica.js').analizar(s.anios.map((a, i) => ({ anio: a, valor: s.valores[i] })), 0.95).sen.pendiente;
    return { x: s.anios, y: s.valores, sen, r: PP.mannKendallModificado(s.anios, s.valores, sen) };
  });
  const gp = PP.generador(7), ps = Array.from({ length: 12 }, () => gp.u());
  ps[3] = null;
  out.bh = { p: ps, q: PP.benjaminiHochberg(ps) };

  // ---- reglas de clasificación con series sintéticas
  const fuerte = sintetica(11, 44, 0.04, 0.2, 0.15, 1981), ruido = sintetica(12, 44, 0, 0, 1, 1981), corta = sintetica(13, 20, 0.05, 0, 0.2, 2005);
  const lluvia = sintetica(14, 44, 0.04, 0.2, 0.15, 1981);
  const conHueco = sintetica(15, 44, 0.03, 0.2, 0.2, 1981); conHueco.valores[10] = null; conHueco.valores[30] = null;
  const acotada = sintetica(16, 44, -0.25, 0.3, 3, 1981); acotada.valores = acotada.valores.map(v => Math.max(0, v - 10 + 4));
  const base = { anio_generacion: 2026, semilla: 99, n_sim: 600, n_sim_validacion: 150 };
  const ev = PP.evaluar(Object.assign({}, base, { indicadores: [ind('fuerte', fuerte), ind('ruido', ruido), ind('corta', corta), ind('lluvia', lluvia, { homogeneidad: 'lluvia_merra2' }), ind('hueco', conHueco), ind('acotada', acotada, { minimo: 0 })] }));
  const por = id => ev.indicadores.find(o => o.id === id);
  out.reglas = {
    horizonte: ev.horizonte, destacadas: ev.destacadas, familia: ev.familia_hipotesis,
    clases: Object.fromEntries(ev.indicadores.map(o => [o.id, o.clasificacion])),
    q: Object.fromEntries(ev.indicadores.map(o => [o.id, [o.historico.mann_kendall ? o.historico.mann_kendall.p_modificado : null, o.historico.q_bh === undefined ? null : o.historico.q_bh]])),
    hueco: { obs10: por('hueco').observaciones[10], obs30: por('hueco').observaciones[30], n_validos: por('hueco').historico.n_validos, n_esperados: por('hueco').historico.n_esperados },
    acotada_min: Math.min(...por('acotada').proyeccion.trayectoria.map(t => t.p025)), acotada_central_min: Math.min(...por('acotada').proyeccion.trayectoria.map(t => t.central)),
    fuerte: { seleccion: por('fuerte').seleccion, validacion: por('fuerte').validacion, cambio: por('fuerte').proyeccion.cambio_vs_referencia, deteccion: por('fuerte').proyeccion.deteccion_10_anios, trayectoria: por('fuerte').proyeccion.trayectoria },
    modelo_forzado: PP.evaluar(Object.assign({}, base, { modelo: 'persistencia', indicadores: [ind('fuerte', fuerte)] })).indicadores[0].seleccion
  };
  // reproducibilidad del identificador
  const ev2 = PP.evaluar(Object.assign({}, base, { indicadores: [ind('fuerte', fuerte), ind('ruido', ruido), ind('corta', corta), ind('lluvia', lluvia, { homogeneidad: 'lluvia_merra2' }), ind('hueco', conHueco), ind('acotada', acotada, { minimo: 0 })] }));
  const ev3 = PP.evaluar(Object.assign({}, base, { semilla: 100, indicadores: [ind('fuerte', fuerte)] }));
  const alterada = JSON.parse(JSON.stringify(ev)); alterada.indicadores[0].proyeccion.media_decada += 0.01;
  out.identidad = { id: ev.perspectiva_id, igual: ev2.perspectiva_id === ev.perspectiva_id, verifica: PP.verificar(JSON.parse(JSON.stringify(ev))), alterada: PP.verificar(alterada), otra_semilla: ev3.perspectiva_id !== ev.perspectiva_id };

  // ---- caso real: departamento de Matagalpa, T2M anual, con índices, GISTEMP y CMIP6
  const dep = JSON.parse(leer('data/admin/nicaragua_departamentos.geojson'));
  const f = dep.features.find(x => x.properties.nom_departamento === 'Matagalpa');
  const g = G.validar(f.geometry).geometria, cel = G.celdasRejilla(g, F.POWER.rejilla);
  const c = E.validar(Object.assign(E.valoresPorDefecto(), { area: { tipo: 'poligono', nombre: 'Matagalpa', geometria: g }, variable: 'T2M' }));
  const lect = await F.descargarCeldas(cel.celdas, 'T2M', { inicio: 1981, fin: 2024 }, { fetch: fetchFix, intentos: 1 });
  const area = { id: 'mt', nombre: 'Matagalpa', tipo: 'poligono', geometria: g, extension: G.extension(g), centro: G.centro(g), superficie_km2: G.areaKm2(g), admin: null, procedencia: { tipo: 'dibujo' }, celdas: cel.celdas };
  const res = A.analizar({ consulta: c, area, variable: F.VARIABLES.T2M, fuente: F.POWER, lecturas: lect, generado_utc: '2026-11-15T00:00:00Z' });
  const idx = PP.leerIndicesCeldas(leer('data/fenomenos/indices_anuales_celdas.csv'));
  const ar = PP.indicadoresDeArea(res.celdas, idx, 0.9);
  const cm0 = PP.leerCmip6(leer('data/expediente/cmip6_regional_mensual.csv'), 'central', null);
  // igual que la app: se interpola solo si la década no está en los datos descargados
  const tieneDecada = Object.values(cm0.variables).some(V => Object.values(V.escenarios).some(E2 => Object.values(E2).some(m => m[2027] !== undefined)));
  const cm = tieneDecada ? cm0 : PP.interpolarCmip6(cm0, 2027, 2036);
  const inds = [PP.indicadorDeConsulta(res)].concat(ar.indicadores.filter(x => x.id !== 't2m_media'), [PP.indicadorGistemp(leer('data/fenomenos/gistemp_nicaragua.csv'), 'central', 'Región Central')]);
  const pc = c.perspectiva;
  const regiones = JSON.parse(leer('data/regiones_nicaragua.geojson'));
  const mapas = PP.mapasCeldas(idx, res.celdas, res.area.extension, c.referencia);
  mapas.cmip6_regiones = PP.cmipRegiones(leer('data/expediente/cmip6_regional_mensual.csv'), regiones.features.filter(f => ['pacifico', 'central', 'caribe'].includes(f.properties.id)).map(f => ({ id: f.properties.id, nombre: f.properties.nombre })), { inicio: 2027, fin: 2036 }, pc.escenarios);
  res.perspectiva = PP.evaluar({ anio_generacion: 2026, referencia: c.referencia, indicadores: inds, cmip6: { region: 'central', nombre: 'Región Central', interpolado: !tieneDecada, anual: cm, escenarios: pc.escenarios, archivo: 'data/expediente/cmip6_regional_mensual.csv', modelos: cm.modelos },
    semilla: pc.semilla, n_sim: pc.n_sim, modelo: pc.modelo, excluidas: PP.EXCLUIDAS, mapas });
  out.matagalpa = { cobertura: ar.cobertura, perspectiva: res.perspectiva, gistemp: leer('data/fenomenos/gistemp_nicaragua.csv').split(/\r?\n/).slice(0, 1)[0] };
  const conPP = pp => () => E.validar(Object.assign(E.valoresPorDefecto(), { area: c.area, perspectiva: Object.assign({}, E.valoresPorDefecto().perspectiva, pp) })).perspectiva;
  const errDe = fn => { try { fn(); return null; } catch (e) { return e.codigo || String(e.message); } };
  out.estado = { defecto: E.valoresPorDefecto().perspectiva, escenarios_filtrados: conPP({ escenarios: ['ssp999', 'ssp585'] })(),
    modelo_invalido: errDe(conPP({ modelo: 'inventado' })), semilla_invalida: errDe(conPP({ semilla: -4 })), n_sim_invalido: errDe(conPP({ n_sim: 5 })),
    mismo_consulta_id: E.consultaId ? E.consultaId(c) === E.consultaId(Object.assign({}, c, { perspectiva: Object.assign({}, c.perspectiva, { modelo: 'persistencia' }) })) : null };
  const mundo = JSON.parse(leer('assets/mundo.geojson'));
  // mapa satelital de la sección C: imagen sintética de prueba (no del lugar) sobre la extensión de las celdas
  const jpgSat = 'data:image/jpeg;base64,' + fs.readFileSync(R + '/tests/fixtures/expediente/portada_prueba.jpg').toString('base64');
  const cj = res.celdas.map(x => x.caja), extSat = [Math.min(...cj.map(b => b[0])) - 0.05, Math.min(...cj.map(b => b[1])) - 0.05, Math.max(...cj.map(b => b[2])) + 0.05, Math.max(...cj.map(b => b[3])) + 0.05];
  const mapaSatelite = { datos: jpgSat, formato: 'JPEG', ancho: (extSat[2] - extSat[0]) * Math.cos(12.8 * Math.PI / 180), alto: extSat[3] - extSat[1], ext: extSat, fuente: 'Imagen de prueba', fecha: '2026-11-16' };
  const pdfEs = INF.crear(res, { jsPDF, qrcode, mundo, regiones, admin: dep, mapaSatelite, idioma: 'es', plantilla: 'completo', generado_utc: '2026-11-15T00:00:00Z' });
  const pdfSinRegiones = INF.crear(res, { jsPDF, qrcode, mundo, idioma: 'es', plantilla: 'completo', generado_utc: '2026-11-15T00:00:00Z' });
  out.mapas = { ambito: mapas.ambito, ventana: mapas.ventana, n_celdas: mapas.celdas.length, cmip6_regiones: mapas.cmip6_regiones, anio_mapa: res.mapa_anomalia,
    paginas_sin_regiones: pdfSinRegiones.paginas };
  // periodo hasta un año sin datos (como 2025 en Masaya): el mapa de anomalías usa el último año con datos
  const c25 = E.validar(Object.assign(E.valoresPorDefecto(), { area: c.area, variable: 'T2M', periodo: { inicio: 1981, fin: 2025 } }));
  const r25 = A.analizar({ consulta: c25, area, variable: F.VARIABLES.T2M, fuente: F.POWER, lecturas: lect, generado_utc: '2026-11-15T00:00:00Z' });
  out.mapas.anio_2025 = { mapa: r25.mapa_anomalia, con_valor: r25.celdas.filter(x => x.anomalia_anio_visible !== null).length, celdas: r25.celdas.length };
  const pdf25 = INF.crear(r25, { jsPDF, qrcode, mundo, idioma: 'es', plantilla: 'resumen', generado_utc: '2026-11-15T00:00:00Z' });
  if (salida) fs.writeFileSync(salida + '/anio_2025.pdf', new Uint8Array(pdf25.doc.output('arraybuffer')));
  const pdfEn = INF.crear(res, { jsPDF, qrcode, mundo, regiones, admin: dep, idioma: 'en', plantilla: 'resumen', generado_utc: '2026-11-15T00:00:00Z' });
  const bytes = new Uint8Array(pdfEs.doc.output('arraybuffer'));
  // portada con imagen (imagen sintética de prueba, no del lugar) y contorno del área
  const jpg = 'data:image/jpeg;base64,' + fs.readFileSync(R + '/tests/fixtures/expediente/portada_prueba.jpg').toString('base64');
  const e0 = res.area.extension, ext = [e0[0] - 0.3, e0[1] - 0.1, e0[2] + 0.3, e0[3] + 0.1];
  const pdfImg = INF.crear(res, { jsPDF, qrcode, mundo, idioma: 'es', plantilla: 'resumen', generado_utc: '2026-11-15T00:00:00Z',
    imagen: { datos: jpg, formato: 'JPEG', ancho: 2.15, alto: 1, ext, fuente: 'Imagen de prueba', fecha: '2026-11-15' } });
  const pk = P.construir(res, { pdf: bytes, generado_utc: '2026-11-15T00:00:00Z' });
  out.paquete = { archivos: pk.archivos.map(a => a.nombre), paginas: pdfEs.paginas, paginas_en: pdfEn.paginas };
  if (salida) {
    fs.mkdirSync(salida, { recursive: true });
    fs.writeFileSync(salida + '/matagalpa_perspectiva.pdf', bytes);
    fs.writeFileSync(salida + '/matagalpa_perspectiva_en.pdf', new Uint8Array(pdfEn.doc.output('arraybuffer')));
    fs.writeFileSync(salida + '/matagalpa_perspectiva.zip', pk.zip);
    fs.writeFileSync(salida + '/matagalpa_portada.pdf', new Uint8Array(pdfImg.doc.output('arraybuffer')));
  }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
