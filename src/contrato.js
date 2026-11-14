/*
 * Lectura de data/clima.json según el contrato 1.0.0 (data/contrato.md, rama codex/datos-climaticos).
 *
 * Reglas del contrato que se respetan aquí:
 *  - Se usan `veredicto` y `veredicto_texto` del JSON; la interfaz no recalcula tendencias.
 *  - Si `tendencia.estado` ≠ "ok" o hay menos de 24 años válidos, se muestra `mensaje` y no se dibuja tendencia.
 *  - Los campos desconocidos se ignoran; los opcionales que falten no rompen la lectura.
 *  - Las rutas de `geometria.archivo` son relativas a data/.
 *
 * El resto de la interfaz consume solo el objeto que devuelve `normalizar()`.
 */
(function () {
  'use strict';
  var ORDEN = ['caja_sicc', 'NIC', 'HND', 'CRI'];
  var AUXILIARES = ['NIC_fuera_caja'];
  var NOMBRES = { caja_sicc: 'Caja original SICC-952', NIC: 'Nicaragua', HND: 'Honduras', CRI: 'Costa Rica', NIC_fuera_caja: 'Nicaragua fuera de la caja' };
  var ROL_POR_DEFECTO = { caja_sicc: 'referencia', NIC: 'principal', HND: 'contexto', CRI: 'contexto', NIC_fuera_caja: 'auxiliar' };
  var VEREDICTOS = { tendencia_detectada: 'detectada', evidencia_insuficiente: 'insuficiente', metodos_discrepan: 'discrepan' };

  function num(v) { return typeof v === 'number' && isFinite(v) ? v : null; }
  function intervalo(ic) {
    return Array.isArray(ic) && ic.length === 2 && num(ic[0]) !== null && num(ic[1]) !== null ? { ic_inf: ic[0], ic_sup: ic[1] } : null;
  }
  function mediana(a) {
    var s = a.slice().sort(function (x, y) { return x - y; }), n = s.length;
    return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  }

  function leerDominio(d, anioFinal, aniosEsperados, avisos) {
    var id = d.id;
    var anios = Array.isArray(d.anios_validos) ? d.anios_validos : [];
    var valores = Array.isArray(d.serie_anual_mm) ? d.serie_anual_mm : [];
    if (anios.length !== valores.length) avisos.push('«' + (d.nombre || id) + '»: anios_validos y serie_anual_mm tienen longitudes distintas; se usa la parte común.');
    var serie = [], porAnio = {};
    for (var i = 0; i < Math.min(anios.length, valores.length); i++) {
      if (num(anios[i]) !== null && num(valores[i]) !== null) porAnio[anios[i]] = valores[i];
    }
    for (var a = anioFinal[0]; a <= anioFinal[1]; a++) serie.push({ anio: a, valor: porAnio[a] !== undefined ? porAnio[a] : null });
    var validos = serie.filter(function (p) { return p.valor !== null; });
    var faltan = serie.filter(function (p) { return p.valor === null; }).map(function (p) { return p.anio; });

    var t = d.tendencia || {};
    var res = { estado: 'faltan', mensaje: t.mensaje || '', crudo: t };
    var ok = t.estado === 'ok' && validos.length >= aniosEsperados && VEREDICTOS[t.veredicto];
    if (!ok) {
      if (!res.mensaje) {
        res.mensaje = t.estado && t.estado !== 'ok' ? 'El archivo indica que no hay datos suficientes para estimar una tendencia.'
          : validos.length < aniosEsperados ? 'Hay ' + validos.length + ' años válidos de ' + aniosEsperados + '; no se dibuja tendencia.'
          : 'El archivo no trae un veredicto reconocible para este dominio.';
      }
      avisos.push('«' + (d.nombre || NOMBRES[id] || id) + '»: ' + res.mensaje);
    } else {
      var ctr = t.controles || {};
      var principal = intervalo(t.ic_mm_por_decada);
      var hac = ctr.hac ? intervalo(ctr.hac.ic_mm_por_decada) : null;
      var sen = ctr.theil_sen ? intervalo(ctr.theil_sen.ic_mm_por_decada) : null;
      if (principal) { principal.pendiente = num(t.mm_por_decada); principal.p = num(t.p_valor); }
      if (hac) { hac.pendiente = num(t.mm_por_decada); hac.rezago = ctr.hac.rezago; }
      if (sen) sen.pendiente = num(ctr.theil_sen.mm_por_decada);
      // rectas para la gráfica: MCO pasa por (media de años, media de lluvia); Theil-Sen se centra en las medianas
      var xs = validos.map(function (p) { return p.anio; }), ys = validos.map(function (p) { return p.valor; });
      var mx = xs.reduce(function (s, v) { return s + v; }, 0) / xs.length, my = ys.reduce(function (s, v) { return s + v; }, 0) / ys.length;
      if (principal && principal.pendiente !== null) principal.intercepto = my - principal.pendiente / 10 * mx;
      if (sen && sen.pendiente !== null) sen.intercepto = mediana(ys) - sen.pendiente / 10 * mediana(xs);
      res = {
        estado: VEREDICTOS[t.veredicto], veredicto_texto: t.veredicto_texto || '', interpretacion: t.interpretacion || '',
        nivel_confianza: num(t.nivel_confianza) || 0.95, media: num(t.media_anual_mm),
        principal: principal, hac: hac, sen: sen,
        mann_kendall: ctr.mann_kendall || null, n_efectivo: num(t.n_efectivo), r1: num(t.r1_residuos),
        pct: num(t.pct_por_decada), ic_pct: intervalo(t.ic_pct_por_decada),
        sensibilidad: Array.isArray(t.sensibilidad) ? t.sensibilidad : [],
        omitir: intervalo(t.omitir_un_anio_mm_por_decada), crudo: t
      };
    }
    return {
      id: id, nombre: d.nombre || NOMBRES[id] || id, tipo: d.tipo, rol: d.rol || ROL_POR_DEFECTO[id] || 'contexto',
      bbox: Array.isArray(d.bbox) ? d.bbox : null, area_km2: num(d.area_km2), geometria: null,
      serie: serie, anios_sin_dato: faltan, n_validos: validos.length, tendencia: res, original: d
    };
  }

  function ausente(id) {
    return { id: id, nombre: NOMBRES[id], rol: ROL_POR_DEFECTO[id], faltante: true, serie: [], anios_sin_dato: [], n_validos: 0,
      tendencia: { estado: 'faltan', mensaje: 'El archivo de datos no incluye este dominio.' }, original: null };
  }

  function normalizar(bruto) {
    if (!bruto || typeof bruto !== 'object') throw new Error('el archivo no contiene un objeto JSON');
    if (!Array.isArray(bruto.dominios)) throw new Error('falta la lista «dominios» del contrato 1.0.0');
    var avisos = [];
    var version = bruto.version_esquema || 'sin versión';
    if (String(version).split('.')[0] !== '1') avisos.push('El archivo declara la versión de esquema ' + version + '; esta interfaz se escribió para la 1.x.');
    var md = bruto.metadatos || {};
    var per = md.periodo || {};
    var periodo = [num(per.inicio) || 2001, num(per.fin) || 2024];
    var aniosEsperados = num(per.anios) || (periodo[1] - periodo[0] + 1);
    var porId = {};
    bruto.dominios.forEach(function (d) { if (d && d.id) porId[d.id] = d; });

    var regiones = ORDEN.map(function (id) {
      if (!porId[id]) { avisos.push('Falta el dominio «' + NOMBRES[id] + '» en los datos.'); return ausente(id); }
      return leerDominio(porId[id], periodo, aniosEsperados, avisos);
    });
    var auxiliares = AUXILIARES.filter(function (id) { return porId[id]; }).map(function (id) { return leerDominio(porId[id], periodo, aniosEsperados, []); });

    var producto = md.producto || {};
    var fuenteTexto = 'NASA GPM IMERG Final ' + (producto.version || 'V07B') + (producto.id ? ' (' + producto.id + ')' : '');
    var oni = null;
    var o = bruto.oni;
    if (o && Array.isArray(o.anios) && Array.isArray(o.oni_temporada) && o.anios.length === o.oni_temporada.length) {
      oni = {
        fuente: o.fuente && (o.fuente.nombre || o.fuente.url) ? (o.fuente.nombre || 'NOAA CPC') : (typeof o.fuente === 'string' ? o.fuente : 'NOAA CPC, índice ONI'),
        fuente_url: o.fuente && o.fuente.url,
        definicion: o.definicion_temporal || '',
        temporada: (o.temporada && o.temporada.nombre) || 'junio–noviembre',
        agregacion: (o.temporada && o.temporada.agregacion) || '',
        anios: o.anios, valores: o.oni_temporada, categorias: o.categoria_descriptiva || [],
        lluvia: o.lluvia_jun_nov_mm || {}, correlacion: o.correlacion_descriptiva || {},
        advertencia: o.advertencia || 'La correlación es descriptiva: no prueba causa.'
      };
    }

    return {
      version: version, estado: bruto.estado || '', es_ejemplo: !!bruto.es_ejemplo || bruto.estado === 'ejemplo_sintetico',
      meta: {
        titulo: md.titulo || '', fuente: fuenteTexto, producto: producto,
        unidades: md.unidad_serie || 'mm/año', unidades_pendiente: md.unidad_pendiente || 'mm/década',
        periodo: periodo, anios: aniosEsperados, nivel_confianza: 0.95,
        metodo: md.metodo || null, fuentes: Array.isArray(md.fuentes) ? md.fuentes : [], limites: Array.isArray(md.limites) ? md.limites : []
      },
      regiones: regiones, auxiliares: auxiliares,
      superposicion: bruto.superposicion || null,
      oni: oni, avisos: avisos, crudo: bruto
    };
  }

  // Añade las geometrías de data/dominios.geojson (si se pudo cargar) a cada región
  function unirGeometrias(datos, geojson) {
    if (!geojson || !Array.isArray(geojson.features)) return;
    var porId = {};
    geojson.features.forEach(function (f) {
      var id = (f.properties && (f.properties.id || f.properties.dominio)) || f.id;
      if (id && f.geometry) porId[id] = f.geometry;
    });
    datos.regiones.concat(datos.auxiliares).forEach(function (r) { if (porId[r.id]) r.geometria = porId[r.id]; });
  }

  // Variante para probar el mensaje de datos faltantes (?caso=faltantes)
  function variarFaltantes(bruto) {
    var copia = JSON.parse(JSON.stringify(bruto));
    copia.dominios = copia.dominios.filter(function (d) { return d.id !== 'HND'; });
    copia.dominios.forEach(function (d) {
      if (d.id === 'CRI') {
        d.anios_validos = d.anios_validos.slice(0, 7);
        d.serie_anual_mm = d.serie_anual_mm.slice(0, 7);
        d.tendencia = { estado: 'datos_insuficientes', anios: 7, mensaje: 'Solo hay 7 años con los 12 meses válidos; se necesitan 24 para estimar la tendencia.' };
      }
    });
    delete copia.oni;
    return copia;
  }

  window.SofContrato = { normalizar: normalizar, unirGeometrias: unirGeometrias, variarFaltantes: variarFaltantes, ORDEN: ORDEN };
})();
