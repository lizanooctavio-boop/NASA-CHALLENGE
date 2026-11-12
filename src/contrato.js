/*
 * Lectura y validación del JSON de evidencia.
 *
 * ESTADO: forma PROPUESTA. El contrato definitivo acordado con Octavio no estaba disponible
 * al construir la demo. Si sus nombres de campo difieren, basta con adaptar `normalizar()`;
 * el resto de la interfaz solo consume el objeto que devuelve esta función.
 *
 * Forma esperada (campos con ? son opcionales):
 * {
 *   version_contrato, es_ejemplo?,
 *   meta: { fuente, variable, unidades, unidades_pendiente, periodo:[ini,fin], nivel_confianza?, generado?, nota? },
 *   regiones: [{
 *     id, nombre, rol: "original"|"principal"|"contexto", bbox:[oeste,sur,este,norte], contorno?:[[lon,lat],...],
 *     serie: [{ anio, valor|null }],
 *     tendencias?: { mco:{pendiente,ic_inf,ic_sup,p?}, sen:{pendiente,ic_inf,ic_sup,p?} }
 *   }],
 *   oni?: { fuente, agregacion, serie:[{ anio, valor }] }
 * }
 * Si una región no trae `tendencias`, se calculan en el navegador con src/estadistica.js.
 */
(function () {
  'use strict';
  var E = window.SofEstadistica;
  var ORDEN = ['caja_original', 'nicaragua', 'honduras', 'costa_rica'];
  var NOMBRES = { caja_original: 'Caja original SICC', nicaragua: 'Nicaragua', honduras: 'Honduras', costa_rica: 'Costa Rica' };

  function tendenciaValida(t) {
    return t && isFinite(t.pendiente) && isFinite(t.ic_inf) && isFinite(t.ic_sup);
  }

  function normalizar(bruto) {
    var avisos = [];
    if (!bruto || typeof bruto !== 'object') throw new Error('El archivo no contiene un objeto JSON.');
    var meta = bruto.meta || {};
    if (!bruto.meta) avisos.push('El archivo no trae el bloque «meta»; se usan unidades por defecto.');
    var nivel = isFinite(meta.nivel_confianza) ? Number(meta.nivel_confianza) : 0.95;
    var lista = Array.isArray(bruto.regiones) ? bruto.regiones : [];
    var porId = {};
    lista.forEach(function (r) { if (r && r.id) porId[r.id] = r; });

    var regiones = ORDEN.map(function (id) {
      var r = porId[id];
      if (!r) {
        avisos.push('Falta la región «' + NOMBRES[id] + '» en los datos.');
        return { id: id, nombre: NOMBRES[id], rol: id === 'nicaragua' ? 'principal' : 'contexto', faltante: true,
          serie: [], analisis: { mco: null, sen: null, n_validos: 0, veredicto: { estado: 'faltan' } } };
      }
      var serie = (Array.isArray(r.serie) ? r.serie : []).map(function (p) {
        return { anio: Number(p.anio), valor: p.valor === null || p.valor === undefined || !isFinite(p.valor) ? null : Number(p.valor) };
      }).filter(function (p) { return isFinite(p.anio); }).sort(function (a, b) { return a.anio - b.anio; });
      var calculado = E.analizar(serie, nivel);
      var analisis = calculado, origen = 'calculado en el navegador';
      if (r.tendencias && tendenciaValida(r.tendencias.mco) && tendenciaValida(r.tendencias.sen)) {
        var tm = Object.assign({ metodo: 'mco', intercepto: calculado.mco && calculado.mco.intercepto }, r.tendencias.mco);
        var ts = Object.assign({ metodo: 'sen', intercepto: calculado.sen && calculado.sen.intercepto }, r.tendencias.sen);
        analisis = { mco: tm, sen: ts, n_validos: calculado.n_validos, veredicto: E.veredicto(tm, ts) };
        origen = 'proporcionado en el JSON';
      }
      var faltan = serie.filter(function (p) { return p.valor === null; }).map(function (p) { return p.anio; });
      if (calculado.n_validos < E.MIN_ANIOS) {
        avisos.push('«' + (r.nombre || NOMBRES[id]) + '» tiene ' + calculado.n_validos + ' años con dato; se necesitan al menos ' + E.MIN_ANIOS + '.');
        analisis = { mco: null, sen: null, n_validos: calculado.n_validos, veredicto: { estado: 'faltan' } };
      }
      return {
        id: id, nombre: r.nombre || NOMBRES[id], rol: r.rol || 'contexto', bbox: r.bbox, contorno: r.contorno,
        serie: serie, anios_sin_dato: faltan, analisis: analisis, origen_tendencias: origen
      };
    });

    var oni = null;
    if (bruto.oni && Array.isArray(bruto.oni.serie) && bruto.oni.serie.length) {
      oni = {
        fuente: bruto.oni.fuente || 'NOAA CPC, índice ONI',
        agregacion: bruto.oni.agregacion || 'media anual',
        serie: bruto.oni.serie.filter(function (p) { return p && isFinite(p.anio) && isFinite(p.valor); })
          .map(function (p) { return { anio: Number(p.anio), valor: Number(p.valor) }; })
      };
    }

    return {
      version: bruto.version_contrato || 'sin versión',
      es_ejemplo: !!bruto.es_ejemplo,
      meta: {
        fuente: meta.fuente || 'Fuente no indicada',
        variable: meta.variable || 'Precipitación anual',
        unidades: meta.unidades || 'mm/año',
        unidades_pendiente: meta.unidades_pendiente || 'mm/año por año',
        periodo: Array.isArray(meta.periodo) ? meta.periodo : [2001, 2024],
        nivel_confianza: nivel,
        generado: meta.generado || '',
        nota: meta.nota || ''
      },
      regiones: regiones,
      oni: oni,
      avisos: avisos
    };
  }

  // Variante para probar el mensaje de datos faltantes (?caso=faltantes)
  function variarFaltantes(bruto) {
    var copia = JSON.parse(JSON.stringify(bruto));
    copia.regiones = copia.regiones.filter(function (r) { return r.id !== 'honduras'; });
    copia.regiones.forEach(function (r) {
      if (r.id === 'costa_rica') r.serie.forEach(function (p, i) { if (i % 3) p.valor = null; });
    });
    delete copia.oni;
    return copia;
  }

  window.SofContrato = { normalizar: normalizar, variarFaltantes: variarFaltantes, ORDEN: ORDEN };
})();
