/*
 * Pestaña de tendencia: precipitación anual GPM IMERG 2001–2024 en Nicaragua, la caja de estudio
 * y los países vecinos. Veredicto, serie, comparación de pendientes y descargas.
 */
(function () {
  'use strict';
  var G = window.SofGraficas, C = window.SofContrato, F = G.formato;
  var $ = function (id) { return document.getElementById(id); };
  var NOMBRES = { nicaragua: 'Nicaragua', caja_original: 'Study box', honduras: 'Honduras', costa_rica: 'Costa Rica' };
  var ROLES = { nicaragua: 'main area', caja_original: 'reference box', honduras: 'neighbor', costa_rica: 'neighbor' };
  var estado = { datos: null, sel: 'nicaragua' };

  async function cargar() {
    async function leer(ruta) {
      var r = await fetch(ruta);
      if (!r.ok) throw new Error('HTTP ' + r.status + ' · ' + ruta);
      return r.json();
    }
    var res = await Promise.all([leer('data/clima.json'), leer('data/dominios.geojson')]);
    return C.desdeClima(res[0], res[1]);
  }

  function region() { return estado.datos.regiones.find(function (r) { return r.id === estado.sel; }); }
  function nivel() { return Math.round(estado.datos.meta.nivel_confianza * 100) + '%'; }
  function ic(t) {
    return F.conSigno(t.pendiente) + ' ' + estado.datos.meta.unidades_pendiente + ' (' + nivel() + ' CI ' + F.conSigno(t.ic_inf) + ' to ' + F.conSigno(t.ic_sup) + ')';
  }

  // ---------- selector ----------
  function construirSelector() {
    var cont = $('botones-region');
    cont.innerHTML = '';
    estado.datos.regiones.forEach(function (r) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role', 'radio');
      b.dataset.region = r.id;
      b.innerHTML = '<span>' + G.escapar(r.nombre) + '</span><span class="rol">' + ROLES[r.id] + '</span>';
      b.addEventListener('click', function () { elegir(r.id, false); });
      cont.appendChild(b);
    });
    cont.addEventListener('keydown', function (ev) {
      var paso = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[ev.key];
      if (!paso) return;
      ev.preventDefault();
      var ids = estado.datos.regiones.map(function (r) { return r.id; });
      elegir(ids[(ids.indexOf(estado.sel) + paso + ids.length) % ids.length], true);
    });
  }
  function elegir(id, enfocar) {
    estado.sel = id;
    pintar();
    if (enfocar) document.querySelector('#botones-region [data-region="' + id + '"]').focus();
  }

  // ---------- veredicto ----------
  var ICONOS = {
    aumento: '<path d="M4 15l6-6 4 4 6-7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    disminucion: '<path d="M4 7l6 6 4-4 6 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    insuficiente: '<path d="M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>',
    discrepan: '<path d="M5 8h9M10 16h9M14 5l3 3-3 3M10 13l-3 3 3 3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    faltan: '<path d="M12 6v8M12 18v.5" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>'
  };
  var LECTURA = {
    aumento: 'All intervals lie above zero: annual rainfall increased over the period.',
    disminucion: 'All intervals lie below zero: annual rainfall decreased over the period.',
    insuficiente: 'The intervals include zero: the change cannot be distinguished from year-to-year variability.',
    discrepan: 'The methods disagree on whether the interval excludes zero, so no trend is claimed.',
    faltan: 'Not enough years with data to estimate a trend.'
  };

  function pintarVeredicto() {
    var r = region(), a = r.analisis, v = a.veredicto.estado, e = G.ESTADOS[v];
    var intervalos = a.hac ? [['Least squares', a.mco], ['Least squares, HAC', a.hac], ['Theil–Sen', a.sen]] : [['Least squares', a.mco], ['Theil–Sen', a.sen]];
    $('veredicto').innerHTML =
      '<div class="veredicto"><span class="icono ' + e.clase + '" aria-hidden="true"><svg viewBox="0 0 24 24">' + ICONOS[v] + '</svg></span>' +
      '<div><p class="sub">' + G.escapar(r.nombre) + ' · ' + estado.datos.meta.periodo.join('–') + '</p>' +
      '<p class="estado ' + e.clase + '">' + e.etiqueta + '</p></div>' +
      (a.mco ? '<p class="pendiente-principal"><strong>' + F.conSigno(a.mco.pendiente) + '</strong> <span>' +
        G.escapar(estado.datos.meta.unidades_pendiente) + '</span><small>Least-squares slope · ' + a.n_validos + ' years</small></p>' : '') +
      '<p class="detalle">' + LECTURA[v] + '</p>' +
      (a.mco ? '<ul class="intervalos">' + intervalos.filter(function (p) { return p[1]; }).map(function (p) {
        return '<li><span>' + p[0] + '</span><b>' + G.escapar(ic(p[1])) + '</b></li>';
      }).join('') + '</ul>' : '') + '</div>';
  }

  function pintar() {
    var d = estado.datos, r = region();
    document.querySelectorAll('#botones-region button').forEach(function (b) {
      var on = b.dataset.region === estado.sel;
      b.setAttribute('aria-checked', String(on));
      b.tabIndex = on ? 0 : -1;
    });
    G.ocultarTip();
    pintarVeredicto();
    $('leyenda-serie').innerHTML =
      '<li><span class="muestra" style="border-color:var(--observado)"></span>Annual rainfall</li>' +
      (r.analisis.mco ? '<li><span class="muestra" style="border-color:var(--serie-mco)"></span>Least squares</li>' +
        '<li><span class="muestra punteada" style="border-color:var(--serie-sen)"></span>Theil–Sen</li>' : '');
    G.dibujarSerie($('serie'), r, d.meta);
    $('leyenda-comp').innerHTML =
      '<li><svg width="22" height="12" aria-hidden="true"><line x1="1" x2="21" y1="6" y2="6" stroke="var(--serie-mco)" stroke-width="2.5"/><circle cx="11" cy="6" r="4.5" fill="var(--serie-mco)"/></svg>Least squares</li>' +
      '<li><svg width="22" height="12" aria-hidden="true"><line x1="1" x2="21" y1="6" y2="6" stroke="var(--serie-sen)" stroke-width="2.5" stroke-dasharray="5 3"/><rect x="7" y="2" width="8" height="8" fill="var(--serie-sen)" transform="rotate(45 11 6)"/></svg>Theil–Sen</li>';
    G.dibujarComparacion($('comparacion'), d.regiones, estado.sel, d.meta, function (id) { elegir(id, false); });
  }

  // ---------- descargas ----------
  function descargar(nombre, contenido, tipo) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([contenido], { type: tipo }));
    a.download = nombre;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    $('estado-descarga').textContent = 'Downloaded: ' + nombre;
  }
  function cabecera() {
    var d = estado.datos;
    return ['# Source: NASA GES DISC, GPM IMERG Final Run monthly V07B (GPM_3IMERGM.07)',
      '# Period: ' + d.meta.periodo.join('-') + '; confidence level: ' + d.meta.nivel_confianza + '; data contract: ' + d.version,
      '# Downloaded: ' + new Date().toISOString()].join('\n') + '\n';
  }
  function n(v, dec) { return v === null || v === undefined || !isFinite(v) ? '' : Number(v).toFixed(dec === undefined ? 3 : dec); }
  function csvSerie() {
    var r = region(), tm = r.analisis.mco, ts = r.analisis.sen;
    var filas = r.serie.map(function (p) {
      return [p.anio, n(p.valor, 1), tm ? n(C.valorAjustado(tm, p.anio), 1) : '', ts ? n(C.valorAjustado(ts, p.anio), 1) : ''].join(',');
    });
    descargar('annual_rainfall_' + r.id + '.csv', cabecera() + 'year,rainfall_mm,least_squares_mm,theil_sen_mm\n' + filas.join('\n') + '\n', 'text/csv;charset=utf-8');
  }
  function csvPendientes() {
    var filas = estado.datos.regiones.map(function (r) {
      var a = r.analisis, t = function (x, k) { return x ? n(x[k]) : ''; };
      return [r.id, '"' + r.nombre + '"', a.n_validos, t(a.mco, 'pendiente'), t(a.mco, 'ic_inf'), t(a.mco, 'ic_sup'), a.mco && isFinite(a.mco.p) ? n(a.mco.p, 4) : '',
        t(a.sen, 'pendiente'), t(a.sen, 'ic_inf'), t(a.sen, 'ic_sup'), a.sen && isFinite(a.sen.p) ? n(a.sen.p, 4) : '', t(a.hac, 'ic_inf'), t(a.hac, 'ic_sup'), G.ESTADOS[a.veredicto.estado].etiqueta].join(',');
    });
    descargar('rainfall_trends_by_area.csv', cabecera() + 'area_id,area,years,ls_slope_mm_decade,ls_ci_low,ls_ci_high,ls_p,theil_sen_slope,theil_sen_ci_low,theil_sen_ci_high,mann_kendall_p,hac_ci_low,hac_ci_high,verdict\n' + filas.join('\n') + '\n', 'text/csv;charset=utf-8');
  }
  function jsonEvidencia() {
    var d = estado.datos;
    descargar('rainfall_trend_evidence.json', JSON.stringify({
      question: 'Has annual rainfall changed in Nicaragua between ' + d.meta.periodo.join(' and ') + '?',
      product: 'NASA GPM IMERG Final Run monthly V07B', contract_version: d.version, period: d.meta.periodo,
      confidence_level: d.meta.nivel_confianza, units: { series: 'mm/yr', slope: 'mm/decade' },
      method: d.meta.metodo, sources: d.meta.fuentes, downloaded: new Date().toISOString(),
      areas: d.regiones.map(function (r) {
        return { id: r.id, name: r.nombre, verdict: G.ESTADOS[r.analisis.veredicto.estado].etiqueta, years: r.analisis.n_validos,
          least_squares: r.analisis.mco, hac: r.analisis.hac, theil_sen: r.analisis.sen, series: r.serie };
      })
    }, null, 2), 'application/json');
  }
  var ACCIONES = { serie: csvSerie, pendientes: csvPendientes, evidencia: jsonEvidencia };
  function construirDescargas() {
    var opciones = [['serie', 'Annual series', 'Selected area · CSV'], ['pendientes', 'Trends by area', 'Slopes and intervals · CSV'], ['evidencia', 'Full evidence', 'Data, method and rule · JSON']];
    $('descargas').innerHTML = '';
    opciones.forEach(function (o) {
      var b = document.createElement('button');
      b.type = 'button';
      b.innerHTML = '<span class="n">' + o[1] + '</span><span class="d">' + o[2] + '</span>';
      b.addEventListener('click', ACCIONES[o[0]]);
      $('descargas').appendChild(b);
    });
    document.querySelectorAll('[data-descarga]').forEach(function (b) {
      if (ACCIONES[b.dataset.descarga]) b.addEventListener('click', ACCIONES[b.dataset.descarga]);
    });
  }

  cargar().then(function (bruto) {
    estado.datos = C.normalizar(bruto);
    estado.datos.regiones.forEach(function (r) { r.nombre = NOMBRES[r.id] || r.nombre; });
    estado.datos.meta.unidades = 'mm/yr';
    estado.datos.meta.unidades_pendiente = 'mm/decade';
    $('tend-sub').textContent = 'NASA GPM IMERG Final V07B · ' + estado.datos.meta.periodo.join('–') + ' · ' + nivel() + ' confidence';
    construirSelector();
    construirDescargas();
    pintar();
    var ancho = innerWidth, t = null;
    addEventListener('resize', function () {
      if (innerWidth === ancho) return;
      ancho = innerWidth;
      clearTimeout(t);
      t = setTimeout(pintar, 150);
    });
    document.addEventListener('sicc:pestana', function (e) { if (e.detail === 'tendencias') requestAnimationFrame(pintar); });
    document.addEventListener('gnomon:languagechange', pintar);
    document.addEventListener('sicc:paneles', function () { if (!$('tendencias').hidden) requestAnimationFrame(pintar); });
  }).catch(function (e) {
    $('veredicto').innerHTML = '<p class="detalle">Trend data unavailable (' + G.escapar(e.message) + ').</p>';
  });
})();
