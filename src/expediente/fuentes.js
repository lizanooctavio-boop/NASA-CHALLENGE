/*
 * Catálogo de fuentes del expediente territorial y adaptador de NASA POWER.
 *
 * Solo se incluyen fuentes comprobadas desde el navegador (CORS abierto, sin clave):
 *   NASA POWER Monthly & Annual API v2.10 (comunidad AG), parámetros T2M y PRECTOTCORR,
 *   rejilla nativa MERRA-2 de 0,5° × 0,625°. Comprobado el 2026-11-15: la respuesta a un Origin externo trae
 *   «access-control-allow-origin: *»; el valor de relleno es -999.
 * POWER es una consulta puntual: cada petición devuelve la celda de la rejilla que contiene la coordenada.
 * Para áreas se consulta el centro de cada celda que toca el área y se pondera por la superficie de intersección.
 */
(function (raiz, fabrica) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) module.exports = fabrica();
  else raiz.ETDFuentes = fabrica();
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';

  var POWER = {
    id: 'nasa_power',
    nombre: 'NASA POWER',
    producto: 'POWER Monthly & Annual API (comunidad AG), fuente nativa MERRA-2',
    producto_en: 'POWER Monthly & Annual API (AG community), native MERRA-2 source',
    tipo_dato: 'reanalisis',
    url_oficial: 'https://power.larc.nasa.gov/',
    url_documentacion: 'https://power.larc.nasa.gov/docs/services/api/temporal/monthly/',
    api: 'https://power.larc.nasa.gov/api/temporal/monthly/point',
    requiere_cuenta: false,
    licencia: 'Datos públicos de la NASA, sin cuenta ni clave. Atribución solicitada por el proyecto POWER.',
    licencia_en: 'Public NASA data, no account or key. Attribution requested by the POWER project.',
    atribucion: 'These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program.',
    rejilla: { dlat: 0.5, dlon: 0.625, lat0: -90, lon0: -180 },
    resolucion_espacial: '0,5° lat × 0,625° lon (rejilla nativa MERRA-2)',
    resolucion_espacial_en: '0.5° lat × 0.625° lon (native MERRA-2 grid)',
    resolucion_temporal: 'mensual',
    modo_consulta: 'puntual',
    anio_min: 1981,
    restricciones: [
      'reanalisis_no_observacion', 'lluvia_merra2_inhomogeneidad', 'resolucion_gruesa', 'ultimo_anio_incompleto'
    ],
    referencias: ['gelaro2017']
  };

  // Variables ofrecidas. operacion_temporal define cómo se pasa de meses a un valor anual o estacional.
  var VARIABLES = {
    T2M: {
      id: 'T2M', fuente: 'nasa_power', parametro: 'T2M', unidad_fuente: 'C', unidad: '°C', decimales: 2,
      nombre: 'Temperatura del aire a 2 m (media)', nombre_en: 'Air temperature at 2 m (mean)',
      operacion_temporal: 'media', operacion_espacial: 'media_ponderada_superficie', anomalia: 'diferencia'
    },
    PRECTOTCORR: {
      id: 'PRECTOTCORR', fuente: 'nasa_power', parametro: 'PRECTOTCORR', unidad_fuente: 'mm/day', unidad: 'mm', decimales: 1,
      nombre: 'Precipitación corregida (acumulado)', nombre_en: 'Corrected precipitation (total)',
      operacion_temporal: 'suma_mm_dia_por_dias', operacion_espacial: 'media_ponderada_superficie', anomalia: 'diferencia'
    }
  };

  var FUENTES = { nasa_power: POWER };

  var REFERENCIAS = {
    sen1968: { autores: 'Sen, P. K.', anio: 1968, titulo: "Estimates of the Regression Coefficient Based on Kendall's Tau", revista: 'Journal of the American Statistical Association 63(324), 1379–1389', doi: '10.1080/01621459.1968.10480934', verificado: '2026-11-15 (Crossref)' },
    mann1945: { autores: 'Mann, H. B.', anio: 1945, titulo: 'Nonparametric Tests Against Trend', revista: 'Econometrica 13(3), 245–259', doi: '10.2307/1907187', verificado: '2026-11-15 (Crossref)' },
    gelaro2017: { autores: 'Gelaro, R. et al.', anio: 2017, titulo: 'The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2)', revista: 'Journal of Climate 30(14), 5419–5454', doi: '10.1175/JCLI-D-16-0758.1', verificado: '2026-11-15 (Crossref)' },
    karney2013: { autores: 'Karney, C. F. F.', anio: 2013, titulo: 'Algorithms for geodesics', revista: 'Journal of Geodesy 87(1), 43–55', doi: '10.1007/s00190-012-0578-z', verificado: '2026-11-15 (Crossref)' },
    kendall1975: { autores: 'Kendall, M. G.', anio: 1975, titulo: 'Rank Correlation Methods', revista: '4.ª ed., Charles Griffin, Londres (libro, sin DOI)', revista_en: '4th ed., Charles Griffin, London (book, no DOI)', doi: null, verificado: null },
    power: { autores: 'NASA Langley Research Center', anio: null, titulo: 'POWER Project — Monthly & Annual API', revista: 'https://power.larc.nasa.gov/docs/services/api/temporal/monthly/', doi: null, verificado: null },
    ineter: { autores: 'Instituto Nicaragüense de Estudios Territoriales (INETER)', anio: null, titulo: 'Límites municipales y departamentales (capas wsINETER-DGGC:Municipios y wsINETER-DGGC:Departamentos)', revista: 'https://mapserveride.ineter.gob.ni/geoserver/ows', doi: null, verificado: null }
  };

  function urlCelda(variable, lon, lat, inicio, fin) {
    var q = 'parameters=' + encodeURIComponent(variable) + '&community=AG&longitude=' + lon.toFixed(4) + '&latitude=' + lat.toFixed(4) +
      '&start=' + inicio + '&end=' + fin + '&format=JSON';
    return POWER.api + '?' + q;
  }

  /*
   * Convierte una respuesta POWER en { meses: {'YYYY-MM': valor|null}, version, fuentes, relleno, unidad }.
   * El valor de relleno (-999) se convierte en null: nunca en cero. El mes 13 (anual de POWER) se descarta:
   * la agregación anual la hace el expediente para poder aplicar temporadas y reglas de completitud.
   */
  function leerRespuesta(json, variable) {
    if (!json || !json.properties || !json.properties.parameter || !json.properties.parameter[variable]) {
      var msg = json && json.messages && json.messages.length ? json.messages.join(' ') : 'respuesta sin el parámetro ' + variable;
      var e = new Error('fuente_respuesta_invalida: ' + msg); e.codigo = 'fuente_respuesta_invalida'; throw e;
    }
    var cab = json.header || {}, relleno = cab.fill_value === undefined ? -999 : Number(cab.fill_value);
    var datos = json.properties.parameter[variable], meses = {};
    Object.keys(datos).forEach(function (k) {
      if (!/^\d{6}$/.test(k)) return;
      var mm = Number(k.slice(4));
      if (mm < 1 || mm > 12) return;
      var v = datos[k];
      meses[k.slice(0, 4) + '-' + k.slice(4)] = (v === null || v === undefined || !isFinite(v) || Number(v) === relleno) ? null : Number(v);
    });
    return {
      meses: meses,
      version: cab.api && cab.api.version ? cab.api.version : null,
      api: cab.api && cab.api.name ? cab.api.name : null,
      fuentes: cab.sources || [],
      relleno: relleno,
      unidad: json.parameters && json.parameters[variable] ? json.parameters[variable].units : null,
      nombre_largo: json.parameters && json.parameters[variable] ? json.parameters[variable].longname : null
    };
  }

  function esperar(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  // Descarga con tiempo límite y reintentos (errores de red y 429/5xx). fetchFn permite inyectar datos en pruebas.
  async function descargarCelda(fetchFn, url, opciones) {
    opciones = opciones || {};
    var intentos = opciones.intentos || 3, ultimo = null;
    for (var i = 0; i < intentos; i++) {
      var ctrl = typeof AbortController === 'function' ? new AbortController() : null, t = null;
      try {
        if (ctrl) t = setTimeout(function () { ctrl.abort(); }, opciones.timeout_ms || 45000);
        var r = await fetchFn(url, ctrl ? { signal: ctrl.signal } : undefined);
        if (r.status === 429 || r.status >= 500) { ultimo = new Error('fuente_no_disponible: HTTP ' + r.status); ultimo.codigo = 'fuente_no_disponible'; }
        else if (!r.ok) { var e = new Error('fuente_rechazo: HTTP ' + r.status); e.codigo = 'fuente_rechazo'; throw e; }
        else return await r.json();
      } catch (err) {
        if (err.codigo === 'fuente_rechazo') throw err;
        ultimo = err.codigo ? err : Object.assign(new Error('red: ' + (err && err.message || err)), { codigo: 'red' });
      } finally { if (t) clearTimeout(t); }
      if (i < intentos - 1) await esperar((opciones.espera_ms || 1500) * (i + 1));
    }
    throw ultimo;
  }

  /*
   * Descarga todas las celdas con un máximo de peticiones simultáneas. Devuelve
   * { celdas: {id: lectura}, fallos: [{id, error}], acceso_utc }.
   */
  async function descargarCeldas(celdas, variable, periodo, opciones) {
    opciones = opciones || {};
    var fetchFn = opciones.fetch || (typeof fetch === 'function' ? fetch.bind(typeof window !== 'undefined' ? window : globalThis) : null);
    if (!fetchFn) throw new Error('sin_fetch');
    var cola = celdas.slice(), resultado = {}, fallos = [], hechas = 0, simult = opciones.simultaneas || 3;
    var acceso = new Date().toISOString();
    async function trabajador() {
      while (cola.length) {
        var c = cola.shift();
        try {
          var json = await descargarCelda(fetchFn, urlCelda(variable, c.lon, c.lat, periodo.inicio, periodo.fin), opciones);
          resultado[c.id] = leerRespuesta(json, variable);
        } catch (e) { fallos.push({ id: c.id, error: e.codigo || 'error', detalle: String(e.message || e) }); }
        hechas++;
        if (opciones.progreso) opciones.progreso(hechas, celdas.length);
      }
    }
    var trabajadores = [];
    for (var i = 0; i < Math.min(simult, celdas.length); i++) trabajadores.push(trabajador());
    await Promise.all(trabajadores);
    return { celdas: resultado, fallos: fallos, acceso_utc: acceso };
  }

  return {
    FUENTES: FUENTES, VARIABLES: VARIABLES, REFERENCIAS: REFERENCIAS, POWER: POWER,
    urlCelda: urlCelda, leerRespuesta: leerRespuesta, descargarCeldas: descargarCeldas
  };
});
