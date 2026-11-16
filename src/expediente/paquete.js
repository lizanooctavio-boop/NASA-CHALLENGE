/*
 * Paquete descargable del expediente: archivos de datos, manifiesto con SHA-256 y ZIP (método «store», sin
 * compresión, para no depender de bibliotecas). Todos los archivos salen del mismo objeto de resultados que
 * alimenta el panel y el PDF.
 *
 * Contenido: informe.pdf, area_interes.geojson, consulta.json, resultados.json, serie_temporal.csv,
 * serie_mensual.csv, celdas_mensual.csv, fuentes.csv, manifest.json, LEEME.txt
 * Faltantes: celda vacía en CSV y null en JSON (nunca 0). Fechas ISO 8601. Separador decimal: punto.
 */
(function (raiz, fabrica) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) module.exports = fabrica(require('./estado.js'), require('./i18n.js'), require('./fuentes.js'));
  else raiz.ETDPaquete = fabrica(raiz.ETDEstado, raiz.ETDi18n, raiz.ETDFuentes);
})(typeof window !== 'undefined' ? window : this, function (Estado, I18n, Fuentes) {
  'use strict';

  // ------------------------------------------------------------------ ZIP
  var TABLA = (function () { var t = new Uint32Array(256); for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(b) { var c = 0xffffffff; for (var i = 0; i < b.length; i++) c = TABLA[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }
  function bytes(x) { return typeof x === 'string' ? Estado.utf8(x) : x; }

  function zip(archivos, fecha) {
    fecha = fecha || new Date();
    var dosT = (fecha.getUTCHours() << 11) | (fecha.getUTCMinutes() << 5) | (fecha.getUTCSeconds() >> 1);
    var dosD = ((fecha.getUTCFullYear() - 1980) << 9) | ((fecha.getUTCMonth() + 1) << 5) | fecha.getUTCDate();
    var partes = [], central = [], off = 0;
    archivos.forEach(function (a) {
      var nom = Estado.utf8(a.nombre), dat = bytes(a.datos), crc = crc32(dat);
      var h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(8, 0, true);
      h.setUint16(10, dosT, true); h.setUint16(12, dosD, true); h.setUint32(14, crc, true); h.setUint32(18, dat.length, true);
      h.setUint32(22, dat.length, true); h.setUint16(26, nom.length, true); h.setUint16(28, 0, true);
      partes.push(new Uint8Array(h.buffer), nom, dat);
      var c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(8, 0x0800, true); c.setUint16(10, 0, true);
      c.setUint16(12, dosT, true); c.setUint16(14, dosD, true); c.setUint32(16, crc, true); c.setUint32(20, dat.length, true); c.setUint32(24, dat.length, true);
      c.setUint16(28, nom.length, true); c.setUint32(42, off, true);
      central.push(new Uint8Array(c.buffer), nom);
      off += 30 + nom.length + dat.length;
    });
    var tam = central.reduce(function (s, x) { return s + x.length; }, 0);
    var fin = new DataView(new ArrayBuffer(22));
    fin.setUint32(0, 0x06054b50, true); fin.setUint16(8, archivos.length, true); fin.setUint16(10, archivos.length, true);
    fin.setUint32(12, tam, true); fin.setUint32(16, off, true);
    var todo = partes.concat(central, [new Uint8Array(fin.buffer)]), n = todo.reduce(function (s, x) { return s + x.length; }, 0);
    var out = new Uint8Array(n), p = 0;
    todo.forEach(function (x) { out.set(x, p); p += x.length; });
    return out;
  }

  // ------------------------------------------------------------------ CSV
  function celda(v) {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number') return isFinite(v) ? String(v) : '';
    var s = String(v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  function csv(filas) { return filas.map(function (f) { return f.map(celda).join(','); }).join('\r\n') + '\r\n'; }

  function serieCSV(res) {
    var u = res.variable.unidad, cab = ['# ' + res.resultado_id + ' · ' + res.consulta_id, '# variable=' + res.variable.id + ' unidad=' + u + ' faltante=celda vacía'];
    var filas = [['anio', 'valor_' + u, 'anomalia_' + u, 'meses_validos', 'meses_faltantes', 'cobertura_espacial_min', 'en_periodo', 'en_referencia', 'estado']];
    res.serie.forEach(function (p) { filas.push([p.anio, p.valor, p.anomalia, p.meses_validos, p.meses_faltantes.join(' '), p.cobertura_espacial_min, p.en_periodo, p.en_referencia, p.estado]); });
    return cab.join('\r\n') + '\r\n' + csv(filas);
  }
  function mensualCSV(res) {
    var u = res.variable.operacion_temporal === 'suma_mm_dia_por_dias' ? 'mm_mes' : res.variable.unidad;
    var filas = [['fecha', 'valor_' + u, 'cobertura_espacial', 'estado']];
    res.mensual.forEach(function (m) { filas.push([m.fecha, m.valor, m.cobertura_espacial, m.estado]); });
    return csv(filas);
  }
  function celdasCSV(res) {
    var ids = res.celdas.map(function (c) { return c.id; });
    var filas = [['fecha'].concat(ids)];
    res.mensual.forEach(function (m) { filas.push([m.fecha].concat(ids.map(function (id) { return res.datos_celdas[id][m.fecha]; }))); });
    filas.push(['# peso'].concat(res.celdas.map(function (c) { return Number(c.peso.toFixed(8)); })));
    filas.push(['# lon_centro'].concat(res.celdas.map(function (c) { return c.lon; })));
    filas.push(['# lat_centro'].concat(res.celdas.map(function (c) { return c.lat; })));
    return csv(filas);
  }
  function fuentesCSV(res, idioma) {
    var f = res.fuente, v = res.variable;
    var filas = [['fuente', 'producto', 'variable', 'parametro', 'unidad_original', 'unidad_expediente', 'tipo_dato', 'resolucion', 'periodo_usado', 'version', 'fecha_acceso', 'cobertura', 'url_oficial', 'licencia', 'requiere_cuenta', 'transformaciones']];
    filas.push([f.nombre, idioma === 'en' ? f.producto_en : f.producto, idioma === 'en' ? v.nombre_en : v.nombre, v.parametro, f.unidad_original, v.unidad, f.tipo_dato,
      idioma === 'en' ? f.resolucion_espacial_en : f.resolucion_espacial, res.consulta.periodo.inicio + '/' + res.consulta.periodo.fin, (f.version_api || '') + ' ' + (f.fuentes_declaradas || []).join('+'),
      f.acceso_utc, res.cobertura.celdas_con_datos + '/' + res.cobertura.celdas_total + ' celdas', f.url_oficial, idioma === 'en' ? f.licencia_en : f.licencia, 'no', I18n.t('d.transf.' + v.id, idioma)]);
    if (res.area.procedencia && res.area.procedencia.tipo === 'ineter') {
      filas.push(['INETER', res.area.procedencia.fuente, I18n.t('d.limites', idioma), '', '', '', 'limites', '', '', res.area.procedencia.version || '', res.area.procedencia.fecha_acceso || '', '', 'https://mapserveride.ineter.gob.ni/geoserver/ows', 'Servicio público INETER', 'no', 'simplificación Douglas-Peucker 0,001°']);
    }
    return csv(filas);
  }

  // ---------------------------------------------------------------- perspectiva de la próxima década
  function obsIndicadoresCSV(P) {
    var filas = [['indicador', 'unidad', 'fuente', 'tipo_dato', 'escala', 'anio', 'valor']];
    P.indicadores.forEach(function (o) { o.observaciones.forEach(function (x) { filas.push([o.id, o.unidad, o.fuente, o.tipo_dato, o.escala, x.anio, x.valor === null ? null : Number(x.valor.toFixed(6))]); }); });
    return '# ' + P.perspectiva_id + ' · faltante=celda vacía\r\n' + csv(filas);
  }
  function proyeccionesCSV(P) {
    var filas = [['indicador', 'unidad', 'modelo', 'clasificacion', 'anio', 'central', 'p025', 'p10', 'p50', 'p90', 'p975', 'tipo']];
    P.indicadores.forEach(function (o) {
      if (!o.proyeccion) return;
      o.proyeccion.trayectoria.forEach(function (x) {
        filas.push([o.id, o.unidad, o.proyeccion.modelo, o.clasificacion.clase, x.anio].concat(['central', 'p025', 'p10', 'p50', 'p90', 'p975'].map(function (k) { return Number(x[k].toFixed(4)); })).concat([x.anio >= P.horizonte.inicio ? 'estimacion_decada' : 'estimacion_puente']));
      });
    });
    var res = [['indicador', 'cantidad', 'tipo_intervalo', 'p025', 'p10', 'p50', 'p90', 'p975']];
    P.indicadores.forEach(function (o) {
      if (!o.proyeccion) return;
      var pr = o.proyeccion, add = function (cant, tipo, q) { res.push([o.id, cant, tipo, q.p025, q.p10, q.p50, q.p90, q.p975].map(function (v) { return typeof v === 'number' ? Number(v.toFixed(5)) : v; })); };
      add('media_decada', 'prediccion', pr.media_decada);
      add('cambio_vs_referencia', 'prediccion_realizacion', pr.cambio_vs_referencia.prediccion);
      add('cambio_vs_referencia', 'confianza_respuesta_media', pr.cambio_vs_referencia.respuesta_media);
      add('cambio_vs_ultima_decada', 'prediccion_realizacion', pr.cambio_vs_ultima_decada.prediccion);
      add('cambio_vs_ultima_decada', 'confianza_respuesta_media', pr.cambio_vs_ultima_decada.respuesta_media);
      add('pendiente_en_decada_por_decada', 'distribucion_simulada', pr.pendiente_en_decada);
      if (o.cmip6) Object.keys(o.cmip6.escenarios).forEach(function (e) { var c = o.cmip6.escenarios[e]; res.push([o.id, 'cmip6_' + e + '_cambio_vs_1995_2014_' + c.unidad_cambio, 'dispersion_entre_modelos_n' + c.n_modelos, c.cambio_min, null, c.cambio_mediana, null, c.cambio_max].map(function (v) { return typeof v === 'number' ? Number(v.toFixed(5)) : v; })); });
    });
    return '# ' + P.perspectiva_id + ' · horizonte ' + P.horizonte.inicio + '-' + P.horizonte.fin + ' · semilla ' + P.semilla + ' · ' + P.n_simulaciones + ' simulaciones\r\n' + csv(filas) + '\r\n' + csv(res);
  }
  function validacionCSV(P) {
    var filas = [['indicador', 'modelo', 'seleccionado', 'origenes', 'n_ventanas', 'decadas_independientes', 'anticipacion', 'mae_decada', 'rmse_decada', 'sesgo_decada', 'mae_anual', 'rmse_anual', 'habilidad_msss_vs_climatologia', 'cobertura80', 'cobertura95', 'anchura80', 'anchura95']];
    P.indicadores.forEach(function (o) {
      if (!o.validacion || !o.validacion.suficiente) return;
      Object.keys(o.validacion.modelos).forEach(function (k) {
        var m = o.validacion.modelos[k];
        filas.push([o.id, k, o.seleccion.modelo === k, o.validacion.origenes.join('-'), m.n, o.validacion.decadas_independientes, o.validacion.desfase].concat(
          ['mae_decada', 'rmse_decada', 'sesgo_decada', 'mae_anual', 'rmse_anual', 'habilidad', 'cobertura80', 'cobertura95', 'anchura80', 'anchura95'].map(function (q) { return m[q] === null || m[q] === undefined ? null : Number(m[q].toFixed(5)); })));
      });
    });
    return csv(filas);
  }

  function areaGeoJSON(res) {
    var a = res.area;
    return JSON.stringify({
      type: 'FeatureCollection',
      features: [{
        type: 'Feature', id: a.id,
        properties: { id: a.id, nombre: a.nombre, tipo: a.tipo, extension_oeste_sur_este_norte: a.extension, centro: a.centro, superficie_km2: a.superficie_km2, admin: a.admin, procedencia: a.procedencia, radio_km: a.radio_km || null, resultado_id: res.resultado_id, consulta_id: res.consulta_id, crs: 'EPSG:4326 (lon, lat)' },
        geometry: a.geometria
      }].concat(res.celdas.map(function (c) {
        var b = c.caja;
        return { type: 'Feature', id: c.id, properties: { capa: 'celda_nasa_power', id: c.id, lon_centro: c.lon, lat_centro: c.lat, area_celda_km2: c.area_celda_km2, interseccion_km2: c.interseccion_km2, peso: c.peso, estado: c.estado, media: c.media, tendencia: c.tendencia },
          geometry: { type: 'Polygon', coordinates: [[[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]]] } };
      }))
    }, null, 1);
  }

  function leeme(res, enlace, idioma) {
    var es = idioma !== 'en', L = [];
    L.push('Earth System Trend Detective · ' + (es ? 'Expediente técnico territorial' : 'Area technical report'));
    L.push('');
    L.push((es ? 'Resultado: ' : 'Result: ') + res.resultado_id);
    L.push((es ? 'Consulta: ' : 'Query: ') + res.consulta_id);
    L.push((es ? 'Generado (UTC): ' : 'Generated (UTC): ') + res.generado_utc);
    L.push((es ? 'Enlace a la consulta: ' : 'Query link: ') + (enlace || '-'));
    L.push('');
    L.push(es ? 'ARCHIVOS' : 'FILES');
    ['informe.pdf', 'area_interes.geojson', 'consulta.json', 'resultados.json', 'serie_temporal.csv', 'serie_mensual.csv', 'celdas_mensual.csv', 'fuentes.csv']
      .concat(res.perspectiva && res.perspectiva.indicadores ? ['perspectiva.json', 'observaciones_indicadores.csv', 'proyecciones.csv', 'validacion.csv'] : [])
      .concat(['manifest.json', 'LEEME.txt'])
      .forEach(function (n) { L.push('  ' + n + ': ' + I18n.t('arch.' + n, idioma)); });
    if (res.perspectiva && res.perspectiva.indicadores) {
      L.push('');
      L.push(es ? 'PERSPECTIVA DE LA PRÓXIMA DÉCADA' : 'NEXT-DECADE OUTLOOK');
      L.push('  ' + res.perspectiva.perspectiva_id + ' · ' + res.perspectiva.horizonte.inicio + '–' + res.perspectiva.horizonte.fin + ' · ' + (es ? 'semilla ' : 'seed ') + res.perspectiva.semilla + ' · ' + res.perspectiva.n_simulaciones + (es ? ' simulaciones' : ' simulations'));
      L.push(es ? '  Extrapolación estadística validada fuera de muestra y proyección CMIP6 por escenario. No es un pronóstico de años concretos.' : '  Out-of-sample validated statistical extrapolation and CMIP6 projection by scenario. Not a forecast of specific years.');
    }
    L.push('');
    L.push(es ? 'CONVENCIONES' : 'CONVENTIONS');
    L.push(es ? '  Coordenadas EPSG:4326, orden longitud, latitud. Fechas ISO 8601. Decimales con punto.' : '  Coordinates EPSG:4326, longitude, latitude order. ISO 8601 dates. Dot decimals.');
    L.push(es ? '  Faltantes: celda vacía en CSV, null en JSON. Nunca se sustituyen por cero ni se rellenan.' : '  Missing: empty cell in CSV, null in JSON. Never replaced by zero or filled.');
    L.push((es ? '  Unidad: ' : '  Unit: ') + res.variable.unidad + (res.variable.id === 'PRECTOTCORR' ? (es ? ' (acumulado de los meses seleccionados; mensual en mm/mes)' : ' (total over the selected months; monthly in mm/month)') : ''));
    L.push('');
    L.push(es ? 'RECUPERAR LOS DATOS ORIGINALES' : 'RETRIEVE THE ORIGINAL DATA');
    res.celdas.forEach(function (c) { L.push('  ' + Fuentes.urlCelda(res.variable.parametro, c.lon, c.lat, res.fuente.periodo_descargado.inicio, res.fuente.periodo_descargado.fin)); });
    L.push('');
    L.push(es ? 'VERIFICAR' : 'VERIFY');
    L.push(es ? '  manifest.json lista el SHA-256 de cada archivo (salvo el propio manifiesto). En la aplicación, «Abrir expediente guardado» comprueba que resultados.json no fue alterado.'
      : '  manifest.json lists the SHA-256 of every file (except itself). In the app, “Open saved package” checks that resultados.json was not altered.');
    L.push('');
    L.push(es ? 'ATRIBUCIÓN' : 'ATTRIBUTION');
    L.push('  ' + res.fuente.atribucion);
    if (res.area.procedencia && res.area.procedencia.tipo === 'ineter') L.push(es ? '  Límites administrativos: INETER (servicio WFS público).' : '  Administrative boundaries: INETER (public WFS service).');
    return L.join('\r\n') + '\r\n';
  }

  /*
   * Construye la lista de archivos del expediente y el ZIP. pdf: Uint8Array del informe (puede ser null en pruebas).
   */
  function construir(res, opciones) {
    opciones = opciones || {};
    var idioma = opciones.idioma || res.consulta.idioma, enlace = opciones.enlace || null;
    var archivos = [];
    if (opciones.pdf) archivos.push({ nombre: 'informe.pdf', datos: opciones.pdf });
    archivos.push({ nombre: 'area_interes.geojson', datos: areaGeoJSON(res) });
    archivos.push({ nombre: 'consulta.json', datos: JSON.stringify(res.consulta, null, 1) });
    archivos.push({ nombre: 'resultados.json', datos: JSON.stringify(res) });
    archivos.push({ nombre: 'serie_temporal.csv', datos: serieCSV(res) });
    archivos.push({ nombre: 'serie_mensual.csv', datos: mensualCSV(res) });
    archivos.push({ nombre: 'celdas_mensual.csv', datos: celdasCSV(res) });
    archivos.push({ nombre: 'fuentes.csv', datos: fuentesCSV(res, idioma) });
    if (res.perspectiva && res.perspectiva.indicadores) {
      archivos.push({ nombre: 'perspectiva.json', datos: JSON.stringify(res.perspectiva) });
      archivos.push({ nombre: 'observaciones_indicadores.csv', datos: obsIndicadoresCSV(res.perspectiva) });
      archivos.push({ nombre: 'proyecciones.csv', datos: proyeccionesCSV(res.perspectiva) });
      archivos.push({ nombre: 'validacion.csv', datos: validacionCSV(res.perspectiva) });
    }
    archivos.push({ nombre: 'LEEME.txt', datos: leeme(res, enlace, idioma) });
    var manifiesto = {
      esquema: 'etd-manifiesto', version: 1, aplicacion: 'Earth System Trend Detective', version_codigo: res.version_codigo,
      generado_utc: opciones.generado_utc || new Date().toISOString(), resultado_id: res.resultado_id, consulta_id: res.consulta_id,
      enlace_consulta: enlace, fuente: { nombre: res.fuente.nombre, version_api: res.fuente.version_api, acceso_utc: res.fuente.acceso_utc },
      perspectiva: res.perspectiva && res.perspectiva.indicadores ? { perspectiva_id: res.perspectiva.perspectiva_id, version: res.perspectiva.version, horizonte: res.perspectiva.horizonte, semilla: res.perspectiva.semilla, n_simulaciones: res.perspectiva.n_simulaciones, generador: 'mulberry32 + Box-Muller', cmip6: res.perspectiva.cmip6_fuente } : null,
      software: { jspdf: '2.5.2', qrcode_generator: '1.4.4', geographiclib_geodesic: '2.1.1', estadistica: 'src/estadistica.js', perspectiva: res.perspectiva ? res.perspectiva.version : null },
      archivos: archivos.map(function (a) { var b = bytes(a.datos); return { nombre: a.nombre, bytes: b.length, sha256: Estado.sha256(b) }; })
    };
    archivos.push({ nombre: 'manifest.json', datos: JSON.stringify(manifiesto, null, 1) });
    return { archivos: archivos, manifiesto: manifiesto, zip: zip(archivos, opciones.fecha) };
  }

  return { construir: construir, zip: zip, crc32: crc32, serieCSV: serieCSV, mensualCSV: mensualCSV, celdasCSV: celdasCSV, fuentesCSV: fuentesCSV, areaGeoJSON: areaGeoJSON, leeme: leeme };
});
