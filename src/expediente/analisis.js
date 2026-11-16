/*
 * Análisis de una investigación por área de interés: agregación espacial y temporal, control de calidad,
 * descriptivos, anomalías, ciclo estacional, tendencia y veredicto.
 *
 * La tendencia y el veredicto se calculan EXCLUSIVAMENTE con src/estadistica.js (SofEstadistica.analizar),
 * el mismo módulo que usa la interfaz. El informe PDF, el CSV y el panel leen este objeto: no recalculan.
 *
 * Reglas: los faltantes nunca se rellenan ni se sustituyen por cero; un año solo cuenta si todos los meses
 * seleccionados son válidos; un mes de área solo es válido si la fracción de superficie con dato alcanza
 * calidad.min_cobertura_espacial (los pesos se renormalizan sobre las celdas con dato y se informa).
 */
(function (raiz, fabrica) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) module.exports = fabrica(require('../estadistica.js'), require('./estado.js'));
  else raiz.ETDAnalisis = fabrica(raiz.SofEstadistica, raiz.ETDEstado);
})(typeof window !== 'undefined' ? window : this, function (Est, Estado) {
  'use strict';

  function diasMes(anio, mes) { return new Date(Date.UTC(anio, mes, 0)).getUTCDate(); }
  function clave(anio, mes) { return anio + '-' + (mes < 10 ? '0' : '') + mes; }
  function r(v, d) { if (v === null || v === undefined || !isFinite(v)) return null; var f = Math.pow(10, d); return Math.round(v * f) / f; }
  function media(a) { return a.length ? a.reduce(function (s, v) { return s + v; }, 0) / a.length : null; }
  function desv(a) { if (a.length < 2) return null; var m = media(a); return Math.sqrt(a.reduce(function (s, v) { return s + (v - m) * (v - m); }, 0) / (a.length - 1)); }

  // Valor mensual en la unidad del expediente: °C para medias; mm del mes para la precipitación (mm/día × días).
  function convertir(variable, valor, anio, mes) {
    if (valor === null || valor === undefined) return null;
    if (variable.operacion_temporal === 'suma_mm_dia_por_dias') return valor * diasMes(anio, mes);
    return valor;
  }

  // Agrega meses de un año según la variable. Devuelve null si falta alguno (no se rellena).
  function agregarAnio(variable, valores, anio, meses) {
    if (valores.some(function (v) { return v === null; })) return null;
    if (variable.operacion_temporal === 'suma_mm_dia_por_dias') return valores.reduce(function (s, v) { return s + v; }, 0);
    // media ponderada por días: la media anual de una variable intensiva respeta la duración de cada mes
    var sd = 0, s = 0;
    valores.forEach(function (v, i) { var d = diasMes(anio, meses[i]); s += v * d; sd += d; });
    return s / sd;
  }

  function residuosLag1(serie, mco) {
    if (!mco) return null;
    var res = serie.map(function (p) { return p.valor - (mco.intercepto + mco.pendiente * p.anio); });
    if (res.length < 3) return null;
    var m = media(res), num = 0, den = 0;
    for (var i = 0; i < res.length; i++) { den += (res[i] - m) * (res[i] - m); if (i) num += (res[i] - m) * (res[i - 1] - m); }
    return den > 0 ? num / den : null;
  }

  function tendenciaDe(serieValida, nivel, minAnios) {
    var a = Est.analizar(serieValida, nivel);
    var suficiente = a.n_validos >= Math.max(minAnios, Est.MIN_ANIOS) && a.mco && a.sen;
    var dec = function (t) {
      return t ? { pendiente_decada: t.pendiente * 10, ic_inf_decada: t.ic_inf * 10, ic_sup_decada: t.ic_sup * 10, p: t.p, intercepto: t.intercepto, pendiente_anual: t.pendiente, n: t.n } : null;
    };
    return {
      n_validos: a.n_validos,
      sen: suficiente ? dec(a.sen) : null,
      mco: suficiente ? dec(a.mco) : null,
      veredicto: suficiente ? a.veredicto : { estado: 'faltan' },
      r1_residuos: suficiente ? residuosLag1(serieValida, a.mco) : null
    };
  }

  /*
   * entrada = { consulta, area, variable, fuente, lecturas, generado_utc }
   *   area: { geometria, extension, centro, superficie_km2, admin, procedencia, celdas: [...] }
   *   lecturas: { celdas: {id: {meses:{'YYYY-MM': v|null}, version, fuentes}}, fallos: [...], acceso_utc }
   */
  function analizar(entrada) {
    var c = entrada.consulta, v = entrada.variable, area = entrada.area, lect = entrada.lecturas;
    var nivel = c.estadistica.nivel, q = c.calidad, meses = c.meses;
    var a0 = Math.min(c.periodo.inicio, c.referencia.inicio), a1 = Math.max(c.periodo.fin, c.referencia.fin);
    var avisos = [], motivos = [];

    // ---- celdas: estado de descarga
    var celdas = area.celdas.map(function (cel) {
      var l = lect.celdas[cel.id];
      return Object.assign({}, cel, { estado: l ? 'ok' : 'fallo' });
    });
    var pesoTotal = celdas.reduce(function (s, x) { return s + x.peso; }, 0);
    if (celdas.some(function (x) { return x.estado === 'fallo'; })) avisos.push('celdas_sin_datos');

    // ---- mensual por celda (unidad del expediente) y agregado espacial
    var datosCeldas = {}, mensual = [];
    celdas.forEach(function (cel) { datosCeldas[cel.id] = {}; });
    for (var anio = a0; anio <= a1; anio++) {
      for (var k = 0; k < meses.length; k++) {
        var mes = meses[k], key = clave(anio, mes), suma = 0, pesos = 0;
        celdas.forEach(function (cel) {
          var l = lect.celdas[cel.id], bruto = l ? l.meses[key] : undefined;
          var val = bruto === undefined ? null : convertir(v, bruto, anio, mes);
          datosCeldas[cel.id][key] = val === null ? null : r(val, 4);
          if (val !== null) { suma += val * cel.peso; pesos += cel.peso; }
        });
        var cob = pesoTotal > 0 ? pesos / pesoTotal : 0;
        var ok = pesos > 0 && cob >= q.min_cobertura_espacial - 1e-9;
        mensual.push({ fecha: key, anio: anio, mes: mes, valor: ok ? r(suma / pesos, 4) : null, cobertura_espacial: r(cob, 4), estado: ok ? 'valido' : (pesos > 0 ? 'cobertura_insuficiente' : 'sin_dato') });
      }
    }

    // ---- anual (o temporada) agregada
    var porAnio = {};
    mensual.forEach(function (m) { (porAnio[m.anio] = porAnio[m.anio] || []).push(m); });
    var serie = [];
    for (anio = a0; anio <= a1; anio++) {
      var ms = porAnio[anio] || [], vals = ms.map(function (m) { return m.valor; });
      var val = ms.length === meses.length ? agregarAnio(v, vals, anio, meses) : null;
      var faltan = ms.filter(function (m) { return m.valor === null; }).map(function (m) { return m.mes; });
      serie.push({
        anio: anio, valor: r(val, 4), meses_validos: ms.length - faltan.length, meses_faltantes: faltan,
        cobertura_espacial_min: ms.length ? r(Math.min.apply(null, ms.map(function (m) { return m.cobertura_espacial; })), 4) : 0,
        en_periodo: anio >= c.periodo.inicio && anio <= c.periodo.fin,
        en_referencia: anio >= c.referencia.inicio && anio <= c.referencia.fin,
        estado: val === null ? (faltan.length ? 'meses_incompletos' : 'sin_dato') : 'valido'
      });
    }
    var enPeriodo = serie.filter(function (p) { return p.en_periodo; });
    var validos = enPeriodo.filter(function (p) { return p.valor !== null; });
    var mesesPeriodo = mensual.filter(function (m) { return m.anio >= c.periodo.inicio && m.anio <= c.periodo.fin; });

    // ---- referencia y anomalías
    var ref = serie.filter(function (p) { return p.en_referencia && p.valor !== null; });
    var nRef = c.referencia.fin - c.referencia.inicio + 1;
    var refOk = ref.length >= Math.ceil(q.min_fraccion_referencia * nRef) && ref.length >= 3;
    var mediaRef = refOk ? media(ref.map(function (p) { return p.valor; })) : null;
    serie.forEach(function (p) { p.anomalia = (refOk && p.valor !== null) ? r(p.valor - mediaRef, 4) : null; });
    if (!refOk) avisos.push('referencia_insuficiente');

    // ---- descriptivos del periodo
    var vv = validos.map(function (p) { return p.valor; });
    var minP = null, maxP = null;
    validos.forEach(function (p) { if (!minP || p.valor < minP.valor) minP = p; if (!maxP || p.valor > maxP.valor) maxP = p; });
    var resumen = {
      anios_periodo: enPeriodo.length,
      n_validos: validos.length,
      anio_inicio_efectivo: validos.length ? validos[0].anio : null,
      anio_fin_efectivo: validos.length ? validos[validos.length - 1].anio : null,
      pct_anios_faltantes: enPeriodo.length ? r(100 * (enPeriodo.length - validos.length) / enPeriodo.length, 2) : null,
      meses_periodo: mesesPeriodo.length,
      pct_meses_faltantes: mesesPeriodo.length ? r(100 * mesesPeriodo.filter(function (m) { return m.valor === null; }).length / mesesPeriodo.length, 2) : null,
      cobertura_espacial_media: mesesPeriodo.length ? r(media(mesesPeriodo.map(function (m) { return m.cobertura_espacial; })), 4) : null,
      media: r(media(vv), 4), desv_est: r(desv(vv), 4),
      minimo: minP ? { valor: minP.valor, anio: minP.anio } : null,
      maximo: maxP ? { valor: maxP.valor, anio: maxP.anio } : null
    };
    var faltanAnios = enPeriodo.filter(function (p) { return p.valor === null; }).map(function (p) { return p.anio; });
    if (faltanAnios.length) avisos.push('anios_excluidos');

    // ---- tendencia (mismo módulo que la interfaz)
    var t = tendenciaDe(validos.map(function (p) { return { anio: p.anio, valor: p.valor }; }), nivel, q.min_anios);
    if (t.veredicto.estado === 'faltan') motivos.push(validos.length < Math.max(q.min_anios, Est.MIN_ANIOS) ? 'pocos_anios' : 'sin_tendencia');
    var tendencia = {
      metodos: ['Theil-Sen + Mann-Kendall (Sen, 1968; Mann, 1945; Kendall, 1975)', 'Mínimos cuadrados ordinarios con intervalo t'],
      implementacion: 'src/estadistica.js (SofEstadistica.analizar)',
      nivel: nivel, alfa: r(1 - nivel, 4),
      correccion_autocorrelacion: false, correccion_estacionalidad: 'no aplica: serie de valores anuales o de temporada',
      sen: t.sen ? { pendiente_decada: r(t.sen.pendiente_decada, 5), ic_inf_decada: r(t.sen.ic_inf_decada, 5), ic_sup_decada: r(t.sen.ic_sup_decada, 5), p_mann_kendall: r(t.sen.p, 6), intercepto: r(t.sen.intercepto, 6), n: t.sen.n } : null,
      mco: t.mco ? { pendiente_decada: r(t.mco.pendiente_decada, 5), ic_inf_decada: r(t.mco.ic_inf_decada, 5), ic_sup_decada: r(t.mco.ic_sup_decada, 5), p: r(t.mco.p, 6), error_estandar_decada: r((t.mco.ic_sup_decada - t.mco.ic_inf_decada) / (2 * Est.cuantilT(1 - nivel, t.mco.n - 2)), 5), intercepto: r(t.mco.intercepto, 6), n: t.mco.n } : null,
      veredicto: t.veredicto,
      r1_residuos: r(t.r1_residuos, 4)
    };
    if (tendencia.r1_residuos !== null && tendencia.r1_residuos > 0.3) avisos.push('autocorrelacion_residuos');

    // ---- ciclo estacional (climatología mensual del periodo)
    var ciclo = meses.map(function (mes) {
      var x = mesesPeriodo.filter(function (m) { return m.mes === mes && m.valor !== null; }).map(function (m) { return m.valor; });
      return { mes: mes, media: r(media(x), 4), n: x.length, unidad: v.operacion_temporal === 'suma_mm_dia_por_dias' ? 'mm/mes' : v.unidad };
    });

    // ---- comparación entre periodos: referencia frente a los últimos 10 años válidos del periodo analizado
    var ult = validos.slice(-10), comp = null;
    if (refOk && ult.length >= 5) {
      var mu = media(ult.map(function (p) { return p.valor; }));
      comp = { a: { inicio: c.referencia.inicio, fin: c.referencia.fin, media: r(mediaRef, 4), n: ref.length },
        b: { inicio: ult[0].anio, fin: ult[ult.length - 1].anio, media: r(mu, 4), n: ult.length },
        diferencia: r(mu - mediaRef, 4), solapan: ult[0].anio <= c.referencia.fin };
    }

    // ---- año del mapa de anomalías: el pedido o, si ese año no tiene dato completo (p. ej. el año en curso), el último
    // año válido anterior. Así el mapa no queda vacío por un año sin datos; el informe dice qué año se muestra.
    var anioPedido = c.vista.anio_visible || c.periodo.fin, anioMapa = anioPedido;
    if (!validos.some(function (p) { return p.anio === anioPedido; })) {
      var previos = validos.filter(function (p) { return p.anio <= anioPedido; });
      if (previos.length) anioMapa = previos[previos.length - 1].anio;
    }
    // ---- celdas: media y tendencia propias (misma regla de completitud, sin agregación espacial)
    celdas.forEach(function (cel) {
      if (cel.estado !== 'ok') { cel.media = null; cel.tendencia = null; return; }
      var s = [];
      for (var an = c.periodo.inicio; an <= c.periodo.fin; an++) {
        var vs = meses.map(function (m) { return datosCeldas[cel.id][clave(an, m)]; });
        var x = agregarAnio(v, vs, an, meses);
        if (x !== null) s.push({ anio: an, valor: x });
      }
      var tc = tendenciaDe(s, nivel, q.min_anios);
      cel.media = r(media(s.map(function (p) { return p.valor; })), 4);
      cel.n_anios = s.length;
      cel.tendencia = tc.sen ? { sen_decada: r(tc.sen.pendiente_decada, 5), ic_inf_decada: r(tc.sen.ic_inf_decada, 5), ic_sup_decada: r(tc.sen.ic_sup_decada, 5), p_mann_kendall: r(tc.sen.p, 6), veredicto: tc.veredicto.estado } : { veredicto: 'faltan' };
      var an2 = anioMapa;
      var vsa = meses.map(function (m) { return datosCeldas[cel.id][clave(an2, m)]; }), xa = agregarAnio(v, vsa, an2, meses);
      var refc = [];
      for (an = c.referencia.inicio; an <= c.referencia.fin; an++) {
        var y = agregarAnio(v, meses.map(function (m) { return datosCeldas[cel.id][clave(an, m)]; }), an, meses);
        if (y !== null) refc.push(y);
      }
      cel.anomalia_anio_visible = (xa !== null && refc.length >= Math.ceil(q.min_fraccion_referencia * nRef)) ? r(xa - media(refc), 4) : null;
    });

    // ---- cobertura del área
    var interseccionCubierta = celdas.filter(function (x) { return x.estado === 'ok'; }).reduce(function (s, x) { return s + (x.interseccion_km2 || 0); }, 0);
    var cobertura = {
      area_solicitada_km2: area.superficie_km2 === null ? null : r(area.superficie_km2, 3),
      area_cubierta_km2: area.superficie_km2 === null ? null : r(interseccionCubierta, 3),
      fraccion_cubierta: area.superficie_km2 === null ? (celdas[0].estado === 'ok' ? 1 : 0) : r(interseccionCubierta / area.superficie_km2, 4),
      celdas_total: celdas.length, celdas_con_datos: celdas.filter(function (x) { return x.estado === 'ok'; }).length,
      superficie_celdas_km2: r(celdas.reduce(function (s, x) { return s + x.area_celda_km2; }, 0), 1),
      huella_punto_km2: area.tipo === 'punto' ? r(celdas[0].area_celda_km2, 1) : null
    };
    if (area.tipo === 'punto') avisos.push('consulta_puntual');
    else if (area.superficie_km2 !== null && area.superficie_km2 < 0.5 * media(celdas.map(function (x) { return x.area_celda_km2; }))) avisos.push('area_menor_que_celda');
    if (celdas.length === 1 && area.tipo !== 'punto') avisos.push('una_sola_celda');
    avisos.push('reanalisis');
    if (v.id === 'PRECTOTCORR') avisos.push('lluvia_merra2_inhomogeneidad');
    if (c.periodo.fin >= new Date().getUTCFullYear()) avisos.push('anio_en_curso');

    var insuficiente = tendencia.veredicto.estado === 'faltan' || validos.length === 0;
    if (validos.length === 0) motivos.push('sin_datos_validos');

    var lecturaUna = lect.celdas[Object.keys(lect.celdas)[0]] || {};
    var fuente = Object.assign({}, entrada.fuente, {
      version_api: lecturaUna.version || null, fuentes_declaradas: lecturaUna.fuentes || [], acceso_utc: lect.acceso_utc,
      unidad_original: lecturaUna.unidad || v.unidad_fuente, nombre_largo: lecturaUna.nombre_largo || null,
      periodo_descargado: { inicio: a0, fin: a1 }, fallos: lect.fallos || []
    });

    var res = {
      esquema: 'etd-resultados', version: 1, version_codigo: Estado.VERSION_CODIGO,
      consulta_id: Estado.consultaId(c), consulta: c,
      area: Object.assign({}, area, { celdas: undefined }),
      cobertura: cobertura, fuente: fuente, variable: v,
      celdas: celdas, mensual: mensual, serie: serie, resumen: resumen, mapa_anomalia: { anio_pedido: anioPedido, anio_mostrado: anioMapa },
      referencia: { inicio: c.referencia.inicio, fin: c.referencia.fin, media: r(mediaRef, 4), n: ref.length, n_esperados: nRef, suficiente: refOk },
      tendencia: tendencia, ciclo_estacional: ciclo, comparacion_periodos: comp,
      calidad: { avisos: avisos, insuficiente: insuficiente, motivos: motivos, anios_excluidos: faltanAnios },
      datos_celdas: datosCeldas,
      generado_utc: entrada.generado_utc || new Date().toISOString()
    };
    delete res.area.celdas;
    res.resultado_id = resultadoId(res);
    return res;
  }

  // Identidad del resultado: datos procesados por celda + consulta + versión de código + versión de la fuente.
  function resultadoId(res) {
    return 'R-' + Estado.sha256(Estado.canonico({
      consulta_id: res.consulta_id, version_codigo: res.version_codigo, version_api: res.fuente.version_api,
      celdas: res.celdas.map(function (x) { return [x.id, x.peso, x.estado]; }), datos: res.datos_celdas
    })).slice(0, 32);
  }

  // Comprueba que un resultado guardado no ha sido alterado (se usa al abrir un expediente).
  function verificar(res) { return !!res && res.esquema === 'etd-resultados' && resultadoId(res) === res.resultado_id; }

  /*
   * Desacuerdo entre fuentes: la tendencia del área (NASA POWER/MERRA-2) excluye el cero y una comparación independiente
   * (GISTEMP o IMERG) no la confirma: la excluye con el signo contrario («contrario») o incluye el cero («no_confirma»).
   * MERRA-2 tiene saltos conocidos por cambios en las observaciones asimiladas, así que en esos casos la tendencia no se
   * presenta como confirmada. Devuelve la comparación con su tipo, o null.
   */
  function desacuerdoFuentes(res, comparaciones) {
    var s = res && res.tendencia && res.tendencia.sen;
    if (!s || !(s.ic_inf_decada * s.ic_sup_decada > 0)) return null;
    var signo = Math.sign(s.ic_inf_decada);
    var c = (comparaciones || res.comparaciones || []).filter(function (x) { return x && isFinite(x.inf) && isFinite(x.sup); })[0];
    if (!c || (c.inf * c.sup > 0 && Math.sign(c.inf) === signo)) return null;
    return Object.assign({}, c, { tipo: c.inf * c.sup > 0 ? 'contrario' : 'no_confirma' });
  }

  return { analizar: analizar, resultadoId: resultadoId, verificar: verificar, diasMes: diasMes, desacuerdoFuentes: desacuerdoFuentes };
});
