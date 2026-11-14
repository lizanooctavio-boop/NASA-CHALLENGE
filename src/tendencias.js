/*
 * Pestaña de tendencia: precipitación anual GPM IMERG 2001–2024 en Nicaragua, la caja de estudio
 * y los países vecinos. Veredicto, comparación de pendientes, serie, región en el mapa y descargas.
 */
(function () {
  'use strict';
  var G = window.SofGraficas, C = window.SofContrato, F = G.formato;
  var $ = function (id) { return document.getElementById(id); };
  var NOMBRES = { nicaragua: 'Nicaragua', caja_original: 'Study box', honduras: 'Honduras', costa_rica: 'Costa Rica' };
  var EN_PREGUNTA = { caja_original: 'the study box' };
  var ROLES = { nicaragua: 'main area', caja_original: 'reference box', honduras: 'neighbor', costa_rica: 'neighbor' };
  var METODOS = { mco: 'Least squares', hac: 'Least squares, HAC', sen: 'Theil–Sen' };
  var estado = { datos: null, sel: 'nicaragua', metodoAbierto: false };

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
  function intervalos(a) {
    return ['mco', 'hac', 'sen'].filter(function (k) { return a[k]; }).map(function (k) { return [METODOS[k], a[k]]; });
  }
  function incluyeCero(t) { return t.ic_inf <= 0 && t.ic_sup >= 0; }
  function unir(lista) { return lista.length < 3 ? lista.join(' and ') : lista.slice(0, -1).join(', ') + ' and ' + lista[lista.length - 1]; }

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
    if (window.SICC_vista && window.SICC_vista.modo() === 'mapa') encuadrar();
    if (enfocar) document.querySelector('#botones-region [data-region="' + id + '"]').focus();
  }

  // ---------- pregunta y ficha ----------
  function pintarFicha() {
    var d = estado.datos, r = region(), p = d.meta.periodo;
    $('tend-pregunta').textContent = 'Has annual rainfall changed in ' + (EN_PREGUNTA[r.id] || r.nombre) + '?';
    $('tend-periodo').textContent = p.join('–') + ' · ' + (p[1] - p[0] + 1) + ' years';
    var area = $('tend-area');
    if (!area) {
      var div = document.createElement('div');
      div.innerHTML = '<dt>Area</dt><dd id="tend-area"></dd>';
      $('tend-ficha').appendChild(div);
      area = $('tend-area');
    }
    area.textContent = r.nombre + (r.area_km2 ? ' · ' + F.nf0.format(r.area_km2) + ' km²' : '');
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
    insuficiente: 'Every interval crosses zero, so “no change” still fits the data: the change cannot be told apart from year-to-year variability.',
    faltan: 'Not enough years with data to estimate a trend.'
  };
  function lectura(a, v) {
    if (v !== 'discrepan') return LECTURA[v];
    var excluyen = [], incluyen = [];
    ['mco', 'hac', 'sen'].forEach(function (k) { if (a[k]) (incluyeCero(a[k]) ? incluyen : excluyen).push(k); });
    if (!excluyen.length || !incluyen.length) return 'The result depends on the method, so no trend is claimed.';
    // Los dos intervalos de mínimos cuadrados se nombran juntos para que la frase se lea de corrido.
    function nombres(ks) {
      if (ks.indexOf('mco') >= 0 && ks.indexOf('hac') >= 0) ks = ['ambos'].concat(ks.filter(function (k) { return k === 'sen'; }));
      return { texto: unir(ks.map(function (k) { return { ambos: 'both least-squares intervals', mco: 'least squares', hac: 'least squares with HAC errors', sen: 'Theil–Sen' }[k]; })), plural: ks.length > 1 || ks[0] === 'ambos' };
    }
    var ex = nombres(excluyen), inc = nombres(incluyen);
    return 'The result depends on the method: ' + ex.texto + ' exclude' + (ex.plural ? '' : 's') + ' zero, but ' +
      inc.texto + ' include' + (inc.plural ? '' : 's') + ' it. No trend is claimed.';
  }

  function pintarVeredicto() {
    var r = region(), a = r.analisis, v = a.veredicto.estado, e = G.ESTADOS[v], u = estado.datos.meta.unidades_pendiente;
    $('veredicto').innerHTML =
      '<div class="veredicto"><span class="icono ' + e.clase + '" aria-hidden="true"><svg viewBox="0 0 24 24">' + ICONOS[v] + '</svg></span>' +
      '<div><p class="sub">' + G.escapar(r.nombre) + ' · ' + estado.datos.meta.periodo.join('–') + '</p>' +
      '<p class="estado ' + e.clase + '">' + e.etiqueta + '</p></div>' +
      (a.mco ? '<p class="pendiente-principal"><strong aria-hidden="true">' + F.conSigno(a.mco.pendiente) + '</strong> <span aria-hidden="true">' +
        G.escapar(u) + '</span><span class="sr">' + F.leerNumero(a.mco.pendiente) + ' ' + G.escapar(u) + '</span>' +
        '<small>Least-squares slope · ' + a.n_validos + ' years</small></p>' : '') +
      '<p class="detalle">' + lectura(a, v) + '</p>' +
      (a.mco ? '<details class="metodo"' + (estado.metodoAbierto ? ' open' : '') + '><summary>Three methods · ' + nivel() + ' intervals</summary><ul class="intervalos">' +
        intervalos(a).map(function (p) {
          return '<li><span>' + p[0] + '</span><b>' + G.escapar(ic(p[1])) + '</b><em>' + (incluyeCero(p[1]) ? 'includes zero' : 'excludes zero') + '</em></li>';
        }).join('') + '</ul></details>' : '') + '</div>';
    var det = $('veredicto').querySelector('details');
    if (det) det.addEventListener('toggle', function () { estado.metodoAbierto = det.open; });
  }

  // ---------- cifras en texto (siempre disponibles; abiertas si una gráfica falla) ----------
  function pintarTabla() {
    var u = estado.datos.meta.unidades_pendiente;
    var celda = function (t) { return t ? F.conSigno(t.pendiente) + ' <span class="tenue">(' + F.conSigno(t.ic_inf) + ' to ' + F.conSigno(t.ic_sup) + ')</span>' : '—'; };
    $('comp-tabla').innerHTML = '<table><caption class="sr">Trend per decade by area, ' + G.escapar(u) + ', with ' + nivel() + ' confidence intervals</caption>' +
      '<thead><tr><th scope="col">Area</th><th scope="col">Verdict</th><th scope="col">Least squares</th><th scope="col">Theil–Sen</th></tr></thead><tbody>' +
      estado.datos.regiones.map(function (r) {
        var a = r.analisis;
        return '<tr' + (r.id === estado.sel ? ' class="sel"' : '') + '><th scope="row">' + G.escapar(r.nombre) + '</th><td>' + G.ESTADOS[a.veredicto.estado].etiqueta +
          '</td><td>' + celda(a.mco) + '</td><td>' + celda(a.sen) + '</td></tr>';
      }).join('') + '</tbody></table><p class="sub-art">Values in ' + G.escapar(u) + '; ' + nivel() + ' confidence intervals in brackets.</p>';
  }
  function serieEnTexto(cont, r) {
    cont.innerHTML = '<div class="tabla"><table><caption class="sr">Annual rainfall in ' + G.escapar(r.nombre) + '</caption><thead><tr><th scope="col">Year</th><th scope="col">Rainfall (' +
      G.escapar(estado.datos.meta.unidades) + ')</th></tr></thead><tbody>' + r.serie.map(function (p) {
        return '<tr><td>' + p.anio + '</td><td>' + (p.valor === null ? 'no data' : F.nf0.format(p.valor)) + '</td></tr>';
      }).join('') + '</tbody></table></div>';
  }

  function pintar() {
    var d = estado.datos, r = region();
    document.querySelectorAll('#botones-region button').forEach(function (b) {
      var on = b.dataset.region === estado.sel;
      b.setAttribute('aria-checked', String(on));
      b.tabIndex = on ? 0 : -1;
    });
    G.ocultarTip();
    pintarFicha();
    pintarVeredicto();
    pintarTabla();
    $('leyenda-comp').innerHTML =
      '<li><svg width="22" height="12" aria-hidden="true"><line x1="1" x2="21" y1="6" y2="6" stroke="var(--serie-mco)" stroke-width="2.5"/><circle cx="11" cy="6" r="4.5" fill="var(--serie-mco)"/></svg>LS · least squares</li>' +
      '<li><svg width="22" height="12" aria-hidden="true"><line x1="1" x2="21" y1="6" y2="6" stroke="var(--serie-sen)" stroke-width="2.5" stroke-dasharray="5 3"/><rect x="7" y="2" width="8" height="8" fill="var(--serie-sen)" transform="rotate(45 11 6)"/></svg>TS · Theil–Sen</li>' +
      '<li><svg width="22" height="12" aria-hidden="true"><line x1="11" x2="11" y1="0" y2="12" stroke="#fff" stroke-width="1.5"/></svg>No change</li>';
    try {
      G.dibujarComparacion($('comparacion'), d.regiones, estado.sel, d.meta, function (id) { elegir(id, false); });
      $('comparacion').hidden = $('leyenda-comp').hidden = false;
    } catch (e) {
      $('comparacion').innerHTML = '';
      $('comparacion').hidden = $('leyenda-comp').hidden = true;
      $('comp-cifras').open = true;
    }
    $('serie-titulo').textContent = 'Annual rainfall · ' + r.nombre;
    $('leyenda-serie').innerHTML =
      '<li><span class="muestra" style="border-color:var(--observado)"></span>Annual rainfall</li>' +
      (r.analisis.mco ? '<li><span class="muestra" style="border-color:var(--serie-mco)"></span>Least squares</li>' +
        '<li><span class="muestra punteada" style="border-color:var(--serie-sen)"></span>Theil–Sen</li>' : '');
    try {
      G.dibujarSerie($('serie'), r, d.meta);
      $('leyenda-serie').hidden = false;
    } catch (e) {
      serieEnTexto($('serie'), r);
      $('leyenda-serie').hidden = true;
    }
    mapaRegiones();
  }

  // ---------- región en el mapa 2D ----------
  var capaMapa = null;
  function mapa2d() { return typeof mapa !== 'undefined' && mapa && window.L ? mapa : null; }
  function mapaRegiones() {
    var m = mapa2d();
    if (!m || !estado.datos) return;
    if (capaMapa) { m.removeLayer(capaMapa); capaMapa = null; }
    if ($('tendencias').hidden) return;
    var regiones = estado.datos.regiones.filter(function (r) { return r.poligonos; });
    // La región elegida se dibuja al final para quedar encima de las que se solapan con ella.
    regiones.sort(function (a, b) { return (a.id === estado.sel) - (b.id === estado.sel); });
    capaMapa = L.layerGroup(regiones.map(function (r) {
      var on = r.id === estado.sel;
      var capa = L.geoJSON({ type: 'MultiPolygon', coordinates: r.poligonos }, {
        style: { color: on ? '#6fd8ff' : 'rgba(235,242,250,.6)', weight: on ? 2.5 : 1, dashArray: on ? null : '4 4', fillColor: '#6fd8ff', fillOpacity: on ? 0.2 : 0 }
      });
      capa.on('click', function () { elegir(r.id, false); });
      if (on) capa.bindTooltip(G.escapar(r.nombre) + ' · ' + G.ESTADOS[r.analisis.veredicto.estado].etiqueta, { permanent: true, direction: 'center', className: 'tend-etiqueta' });
      return capa;
    })).addTo(m);
  }
  function encuadrar() {
    var m = mapa2d(), r = region();
    if (!m || !r || !r.bbox) return;
    var panel = $('tendencias'), izq = 20;
    if (innerWidth > 700 && !panel.hidden && !document.body.classList.contains('solo-mapa')) izq = panel.getBoundingClientRect().right + 20;
    if (innerWidth - izq < 320) izq = 20;
    m.fitBounds([[r.bbox[1], r.bbox[0]], [r.bbox[3], r.bbox[2]]], { paddingTopLeft: [izq, 90], paddingBottomRight: [20, 20], maxZoom: 7 });
  }
  $('tend-mapa').addEventListener('click', function () {
    if (!window.SICC_vista) return;
    // Sin hueco libre junto al panel (portátil estrecho o móvil) se ocultan los paneles para ver la región.
    var panel = $('tendencias').getBoundingClientRect();
    var estrecho = innerWidth <= 700 || innerWidth - panel.right < 320;
    Promise.resolve(window.SICC_vista.cambiar('mapa')).then(function () {
      if (estrecho && typeof soloMapa === 'function') soloMapa(true);
      mapaRegiones();
      requestAnimationFrame(encuadrar);
    });
  });

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
  function cabecera(r) {
    var d = estado.datos;
    return ['# Source: NASA GES DISC, GPM IMERG Final Run monthly V07B (GPM_3IMERGM.07)',
      '# Period: ' + d.meta.periodo.join('-') + '; confidence level: ' + d.meta.nivel_confianza + '; data contract: ' + d.version]
      .concat(r ? ['# Area: ' + r.nombre + ' (' + r.id + ')' + (r.area_km2 ? ', ' + Math.round(r.area_km2) + ' km2' : '')] : [])
      .concat(['# Downloaded: ' + new Date().toISOString()]).join('\n') + '\n';
  }
  function n(v, dec) { return v === null || v === undefined || !isFinite(v) ? '' : Number(v).toFixed(dec === undefined ? 3 : dec); }
  function csvSerie() {
    var r = region(), tm = r.analisis.mco, ts = r.analisis.sen;
    var filas = r.serie.map(function (p) {
      return [p.anio, n(p.valor, 1), tm ? n(C.valorAjustado(tm, p.anio), 1) : '', ts ? n(C.valorAjustado(ts, p.anio), 1) : ''].join(',');
    });
    descargar('annual_rainfall_' + r.id + '.csv', cabecera(r) + 'year,rainfall_mm,least_squares_mm,theil_sen_mm\n' + filas.join('\n') + '\n', 'text/csv;charset=utf-8');
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

  function iniciar() {
    $('veredicto').innerHTML = '<p class="detalle cargando-datos">Loading NASA rainfall data…</p>';
    cargar().then(function (bruto) {
      estado.datos = C.normalizar(bruto);
      estado.datos.regiones.forEach(function (r) { r.nombre = NOMBRES[r.id] || r.nombre; });
      estado.datos.meta.unidades = 'mm/yr';
      estado.datos.meta.unidades_pendiente = 'mm/decade';
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
      document.addEventListener('sicc:pestana', function (e) { if (e.detail === 'tendencias') requestAnimationFrame(pintar); else mapaRegiones(); });
      document.addEventListener('sicc:paneles', function () { if (!$('tendencias').hidden) requestAnimationFrame(pintar); });
    }).catch(function (e) {
      $('veredicto').innerHTML = '<p class="detalle">The rainfall data could not be loaded (' + G.escapar(e.message) + ').</p>' +
        '<div class="controles"><button type="button" id="tend-reintentar">Try again</button></div>';
      $('tend-reintentar').addEventListener('click', iniciar);
    });
  }
  iniciar();
})();
