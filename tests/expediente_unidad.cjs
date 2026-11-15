/*
 * Comprobaciones de los módulos del expediente (src/expediente/) en Node. Imprime un JSON que
 * tests/test_expediente.py contrasta con pyproj, scipy y pypdf.
 */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const R = path.resolve(__dirname, '..');
const G = require(R + '/src/expediente/geo.js'), E = require(R + '/src/expediente/estado.js'), F = require(R + '/src/expediente/fuentes.js');
const A = require(R + '/src/expediente/analisis.js'), I = require(R + '/src/expediente/i18n.js'), P = require(R + '/src/expediente/paquete.js');
const INF = require(R + '/src/expediente/informe.js'), Est = require(R + '/src/estadistica.js');
const { jsPDF } = require(R + '/app/vendor/jspdf.umd.min.js'), qrcode = require(R + '/app/vendor/qrcode-generator.js');
const FIX = JSON.parse(zlib.gunzipSync(fs.readFileSync(R + '/tests/fixtures/expediente/power_nicaragua_2026-11-15.json.gz')));
const salida = process.argv[2] || null;

const fetchFix = async url => {
  const q = new URL(url).searchParams, r = FIX.respuestas[Number(q.get('latitude')).toFixed(4) + '_' + Number(q.get('longitude')).toFixed(4)];
  if (!r) return { ok: false, status: 503, json: async () => ({}) };
  return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(r)) };
};
function err(fn) { try { fn(); return null; } catch (e) { return e.codigo || String(e.message); } }

async function caso(geom, tipo, variable, extra) {
  extra = extra || {};
  const v = G.validar(geom), g = v.geometria, cel = G.celdasRejilla(g, F.POWER.rejilla);
  const c = E.validar(Object.assign(E.valoresPorDefecto(), { area: { tipo, nombre: extra.nombre || tipo, geometria: g, admin: extra.admin_c, radio_km: extra.radio_km }, variable, periodo: extra.periodo || { inicio: 1981, fin: 2024 }, meses: extra.meses || [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] }));
  const per = { inicio: Math.min(c.periodo.inicio, c.referencia.inicio), fin: Math.max(c.periodo.fin, c.referencia.fin) };
  const lect = extra.lecturas || await F.descargarCeldas(cel.celdas, variable, per, { fetch: extra.fetch || fetchFix, intentos: 1 });
  const area = { id: 'prueba', nombre: extra.nombre || tipo, tipo, geometria: g, extension: G.extension(g), centro: G.centro(g), superficie_km2: G.areaKm2(g), admin: extra.admin || null, procedencia: { tipo: 'dibujo' }, celdas: cel.celdas };
  return { res: A.analizar({ consulta: c, area, variable: F.VARIABLES[variable], fuente: F.POWER, lecturas: lect, generado_utc: '2026-11-15T00:00:00Z' }), lect, cel, consulta: c };
}

(async () => {
  const out = {};
  // ---- áreas geodésicas frente a pyproj (los valores de referencia se calcularon con pyproj al preparar los límites)
  const mun = JSON.parse(fs.readFileSync(R + '/data/admin/nicaragua_municipios.geojson'));
  out.areas_municipios = mun.features.map(f => ({ cod: f.properties.cod_municipio, js: G.areaKm2(G.validar(f.geometry).geometria), pyproj: f.properties.area_geodesica_simplificada_km2, ineter: f.properties.area_ineter_km2 }));
  // ---- círculo, antimeridiano, multipolígono, punto
  const circ = G.circulo(-86.25, 12.13, 25, 360);
  out.circulo = { area: G.areaKm2(circ), teorica: Math.PI * 25 * 25 };
  const cruza = G.validar({ type: 'Polygon', coordinates: [[[179, -17], [-179, -17], [-179, -16], [179, -16], [179, -17]]] }).geometria;
  const igual = G.validar({ type: 'Polygon', coordinates: [[[-1, -17], [1, -17], [1, -16], [-1, -16], [-1, -17]]] }).geometria;
  out.antimeridiano = { area: G.areaKm2(cruza), referencia: G.areaKm2(igual), extension: G.extension(cruza), centro: G.centro(cruza), contiene: G.contiene(cruza, 180, -16.5), celdas: G.celdasRejilla(cruza, F.POWER.rejilla).celdas.length };
  const multi = { type: 'MultiPolygon', coordinates: [[[[-86, 12], [-85.9, 12], [-85.9, 12.1], [-86, 12.1], [-86, 12]]], [[[-84, 13], [-83.9, 13], [-83.9, 13.1], [-84, 13.1], [-84, 13]]]] };
  out.multipoligono = { total: G.areaKm2(G.validar(multi).geometria), partes: [G.areaKm2({ type: 'Polygon', coordinates: multi.coordinates[0] }), G.areaKm2({ type: 'Polygon', coordinates: multi.coordinates[1] })] };
  const conAgujero = { type: 'Polygon', coordinates: [[[-86, 12], [-85, 12], [-85, 13], [-86, 13], [-86, 12]], [[-85.75, 12.25], [-85.75, 12.75], [-85.25, 12.75], [-85.25, 12.25], [-85.75, 12.25]]] };
  out.agujero = { total: G.areaKm2(G.validar(conAgujero).geometria), exterior: G.areaKm2({ type: 'Polygon', coordinates: [conAgujero.coordinates[0]] }), interior: G.areaKm2({ type: 'Polygon', coordinates: [conAgujero.coordinates[1].slice().reverse()] }) };
  out.forma_c = G.centro(G.validar({ type: 'Polygon', coordinates: [[[0, 0], [3, 0], [3, 1], [1, 1], [1, 2], [3, 2], [3, 3], [0, 3], [0, 0]]] }).geometria);
  out.punto = { area: G.areaKm2({ type: 'Point', coordinates: [-86, 12] }), celdas: G.celdasRejilla({ type: 'Point', coordinates: [-86.2514, 12.1364] }, F.POWER.rejilla).celdas };
  out.errores = {
    vacia: err(() => G.validar({ type: 'Polygon', coordinates: [] })), nula: err(() => G.validar(null)),
    lazo: err(() => G.validar({ type: 'Polygon', coordinates: [[[-86, 12], [-85, 13], [-85, 12], [-86, 13], [-86, 12]]] })),
    rango: err(() => G.validar({ type: 'Point', coordinates: [12, -95] })), abierto: err(() => G.validar({ type: 'Polygon', coordinates: [[[-86, 12], [-85, 12], [-85, 13]]] })),
    linea: err(() => G.validar({ type: 'LineString', coordinates: [[-86, 12], [-85, 12]] })), texto: err(() => G.validar({ type: 'Point', coordinates: ['a', 1] })),
    compleja: err(() => { const a = []; for (let i = 0; i < 25000; i++) { const t2 = 2 * Math.PI * i / 25000; a.push([-86 + Math.cos(t2), 12 + Math.sin(t2)]); } a.push(a[0]); return G.validar({ type: 'Polygon', coordinates: [a] }); }),
    grande: err(() => G.celdasRejilla(G.validar({ type: 'Polygon', coordinates: [[[-100, 0], [-60, 0], [-60, 30], [-100, 30], [-100, 0]]] }).geometria, F.POWER.rejilla))
  };
  const horario = G.validar({ type: 'Polygon', coordinates: [[[-86, 12], [-86, 13], [-85, 13], [-85, 12], [-86, 12]]] });
  out.orientacion = { avisos: horario.avisos, area: G.areaKm2(horario.geometria) };

  // ---- celdas y pesos de un departamento
  const dep = JSON.parse(fs.readFileSync(R + '/data/admin/nicaragua_departamentos.geojson'));
  const chontales = G.validar(dep.features.find(f => f.properties.nom_departamento === 'Chontales').geometry).geometria;
  const cch = G.celdasRejilla(chontales, F.POWER.rejilla);
  out.celdas_chontales = { n: cch.celdas.length, suma_pesos: cch.celdas.reduce((s, c) => s + c.peso, 0), suma_inter: cch.suma_intersecciones_km2, area: G.areaKm2(chontales) };

  // ---- estado y enlaces
  const masaya = mun.features.find(f => f.properties.nom_municipio === 'Masaya');
  const cm = await caso(masaya.geometry, 'poligono', 'T2M');
  const enl = await E.enlace(cm.consulta, 'https://nasa-challenge-q6cx.onrender.com/', { resultado_ref: cm.res.resultado_id });
  const fr = E.leerFragmento(enl.url.split('#')[1]);
  const vuelta = E.validar(await E.decodificar(fr.codigo));
  const c2 = JSON.parse(JSON.stringify(cm.consulta)); c2.vista = { centro: [10, -80], zoom: 5, anio_visible: 2000, capa: 'peso_celda', estilo: 'divergente' }; c2.idioma = 'en'; c2.titulo = 'otro';
  out.estado = {
    url: enl.url, compartible: enl.compartible, local: (await E.enlace(cm.consulta, 'http://localhost:8000/')).compartible,
    ida_vuelta: E.canonico(vuelta.area.geometria) === E.canonico(cm.consulta.area.geometria) && vuelta.variable === cm.consulta.variable && E.canonico(vuelta.periodo) === E.canonico(cm.consulta.periodo),
    resultado_ref: fr.resultado_ref, mismo_id_sin_vista: E.consultaId(c2) === E.consultaId(cm.consulta),
    id_cambia_con_periodo: E.consultaId(Object.assign({}, cm.consulta, { periodo: { inicio: 1990, fin: 2024 } })) !== E.consultaId(cm.consulta),
    errores: {
      corrupto: await E.decodificar('zAAAA!!').then(() => null, e => e.codigo), formato: await E.decodificar('qAAAA').then(() => null, e => e.codigo),
      futura: err(() => E.validar({ esquema: 'etd-consulta', version: 9 })), vieja: err(() => E.validar({ esquema: 'etd-consulta', version: 0 })),
      variable: err(() => E.validar(Object.assign({}, cm.consulta, { variable: 'X' }))), meses: err(() => E.validar(Object.assign({}, cm.consulta, { meses: [13] }))),
      periodo: err(() => E.validar(Object.assign({}, cm.consulta, { periodo: { inicio: 2020, fin: 2000 } }))), esquema: err(() => E.validar({ hola: 1 }))
    },
    descarta_desconocidos: !('api_key' in E.validar(Object.assign({}, cm.consulta, { api_key: 'x', token: 'y' }))),
    sha_abc: E.sha256('abc'), sha_vacio: E.sha256('')
  };
  // ---- análisis
  out.masaya = { serie: cm.res.serie.filter(p => p.en_periodo).map(p => [p.anio, p.valor]), tendencia: cm.res.tendencia, resumen: cm.res.resumen, celdas: cm.res.celdas.length, id: cm.res.resultado_id, avisos: cm.res.calidad.avisos };
  const directo = Est.analizar(cm.res.serie.filter(p => p.en_periodo && p.valor !== null).map(p => ({ anio: p.anio, valor: p.valor })), 0.95);
  out.masaya.directo_sen_decada = directo.sen.pendiente * 10; out.masaya.directo_mco_decada = directo.mco.pendiente * 10; out.masaya.directo_veredicto = directo.veredicto.estado;
  const cm2 = await caso(masaya.geometry, 'poligono', 'T2M', { lecturas: cm.lect });
  out.masaya.id_estable = cm2.res.resultado_id === cm.res.resultado_id;
  out.masaya.verifica = A.verificar(cm.res);
  const alter = JSON.parse(JSON.stringify(cm.res)); alter.datos_celdas[alter.celdas[0].id]['2000-03'] += 0.5; out.masaya.detecta_alteracion = !A.verificar(alter);
  // faltante: un mes eliminado → el año se excluye (nunca se rellena ni se pone a cero)
  const lectFalta = JSON.parse(JSON.stringify(cm.lect)); lectFalta.celdas[cm.res.celdas[0].id].meses['2003-07'] = null;
  const cf = await caso(masaya.geometry, 'poligono', 'T2M', { lecturas: lectFalta });
  out.faltante = { anio2003: cf.res.serie.find(p => p.anio === 2003), n: cf.res.resumen.n_validos, id_distinto: cf.res.resultado_id !== cm.res.resultado_id, avisos: cf.res.calidad.avisos };
  // precipitación: conversión mm/día × días
  const cp = await caso({ type: 'Point', coordinates: [-86.2514, 12.1364] }, 'punto', 'PRECTOTCORR');
  const bruto = FIX.respuestas['12.0000_-86.2500'].properties.parameter.PRECTOTCORR;
  let suma2001 = 0; for (let m = 1; m <= 12; m++) suma2001 += bruto['2001' + String(m).padStart(2, '0')] * A.diasMes(2001, m);
  out.precip_punto = { valor2001: cp.res.serie.find(p => p.anio === 2001).valor, esperado2001: suma2001, avisos: cp.res.calidad.avisos, huella: cp.res.cobertura.huella_punto_km2, superficie: cp.res.area.superficie_km2, febrero2004: cp.res.mensual.find(m => m.fecha === '2004-02').valor, bruto_feb2004: bruto['200402'] };
  // datos insuficientes
  const ci = await caso({ type: 'Point', coordinates: [-86.2514, 12.1364] }, 'punto', 'T2M', { periodo: { inicio: 2016, fin: 2024 } });
  out.insuficiente = { veredicto: ci.res.tendencia.veredicto, sen: ci.res.tendencia.sen, motivos: ci.res.calidad.motivos, insuficiente: ci.res.calidad.insuficiente };
  // cobertura espacial: una celda sin datos
  const chont = await caso(chontales, 'poligono', 'T2M', { fetch: async url => { const q = new URL(url).searchParams; if (Number(q.get('latitude')) === 12 && Number(q.get('longitude')) === -85) return { ok: false, status: 503, json: async () => ({}) }; return fetchFix(url); } });
  out.cobertura = { fallos: chont.lect.fallos.length, fraccion: chont.res.cobertura.fraccion_cubierta, avisos: chont.res.calidad.avisos, n: chont.res.resumen.n_validos, cobertura_media: chont.res.resumen.cobertura_espacial_media };
  // red caída: ninguna celda
  const caida = await F.descargarCeldas(cch.celdas.slice(0, 2), 'T2M', { inicio: 1981, fin: 2024 }, { fetch: async () => { throw new TypeError('Failed to fetch'); }, intentos: 2, espera_ms: 1 });
  out.red = { fallos: caida.fallos.map(f => f.error), celdas: Object.keys(caida.celdas).length };

  // ---- paquete
  const pdfDoc = INF.crear(cm.res, { jsPDF, qrcode, mundo: JSON.parse(fs.readFileSync(R + '/assets/mundo.geojson')), enlace: enl.url, idioma: 'es', plantilla: 'completo', notas: 'Nota del usuario de prueba.' });
  const pdf = new Uint8Array(pdfDoc.doc.output('arraybuffer'));
  const pk = P.construir(cm.res, { pdf, enlace: enl.url, generado_utc: '2026-11-15T00:00:00Z' });
  out.paquete = { archivos: pk.archivos.map(a => a.nombre), manifiesto: pk.manifiesto, crc_prueba: P.crc32(Buffer.from('123456789')).toString(16) };
  const pdfEn = INF.crear(cp.res, { jsPDF, qrcode, enlace: enl.url, idioma: 'en', plantilla: 'resumen' });
  const pdfFalta = INF.crear(ci.res, { jsPDF, qrcode, idioma: 'es', plantilla: 'completo' });
  if (salida) {
    fs.mkdirSync(salida, { recursive: true });
    fs.writeFileSync(salida + '/masaya.pdf', pdf); fs.writeFileSync(salida + '/masaya.zip', pk.zip);
    fs.writeFileSync(salida + '/punto_en.pdf', new Uint8Array(pdfEn.doc.output('arraybuffer')));
    fs.writeFileSync(salida + '/insuficiente.pdf', new Uint8Array(pdfFalta.doc.output('arraybuffer')));
    fs.writeFileSync(salida + '/masaya_resultados.json', JSON.stringify(cm.res));
  }
  out.pdf = { paginas: pdfDoc.paginas, id: pdfDoc.id, en_paginas: pdfEn.paginas };
  // ---- traducciones
  out.i18n = { solo_es: I.claves('es').filter(k => !(k in I.EN)), solo_en: I.claves('en').filter(k => !(k in I.ES)), num_es: I.num(-1234.567, 2, 'es'), num_en: I.num(-1234.567, 2, 'en') };
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
