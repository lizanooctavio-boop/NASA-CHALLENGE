/*
 * Serie anual y comparación de pendientes en SVG, sin librerías.
 * Cada gráfica se dibuja al ancho real de su contenedor para que el texto conserve su tamaño en móvil.
 */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  function formato(options) { return { format: function(v) { return new Intl.NumberFormat(window.GnomonI18n?.locale() || 'en-US', options).format(v); } }; }
  var nf1 = formato({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var nf0 = formato({ maximumFractionDigits: 0 });
  var nf2 = formato({ minimumFractionDigits: 2, maximumFractionDigits: 2 });

  function conSigno(v, f) { f = f || nf1; return (v > 0 ? '+' : v < 0 ? '−' : '') + f.format(Math.abs(v)); }

  function el(tag, attrs, padre) {
    var e = document.createElementNS(NS, tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]); });
    if (padre) padre.appendChild(e);
    return e;
  }
  function texto(padre, x, y, contenido, attrs) {
    var t = el('text', Object.assign({ x: x, y: y }, attrs || {}), padre);
    t.textContent = contenido;
    return t;
  }

  function ticksBonitos(min, max, n) {
    var paso = Math.pow(10, Math.floor(Math.log10((max - min) / n)));
    var err = (max - min) / n / paso;
    if (err >= 7.5) paso *= 10; else if (err >= 3.5) paso *= 5; else if (err >= 1.5) paso *= 2;
    var ini = Math.ceil(min / paso) * paso, ticks = [];
    for (var v = ini; v <= max + paso * 1e-9; v += paso) ticks.push(Math.round(v / paso) * paso);
    return ticks;
  }

  // ---------- tooltip compartido ----------
  var tip = null;
  function tooltip() { return tip || (tip = document.getElementById('tooltip')); }
  function mostrarTip(html, clientX, clientY) {
    var t = tooltip();
    t.innerHTML = html;
    t.hidden = false;
    var x = clientX, y = clientY;
    var ancho = t.offsetWidth, min = ancho / 2 + 8, max = document.documentElement.clientWidth - ancho / 2 - 8;
    t.style.left = Math.max(min, Math.min(max, x)) + 'px';
    t.style.top = y + 'px';
  }
  function ocultarTip() { if (tooltip()) tooltip().hidden = true; }

  // ---------- colores ----------
  var ESTADOS = {
    aumento: { etiqueta: 'Increase', clase: 'est-aumento' },
    disminucion: { etiqueta: 'Decrease', clase: 'est-disminucion' },
    insuficiente: { etiqueta: 'Insufficient evidence', clase: 'est-insuficiente' },
    discrepan: { etiqueta: 'Methods disagree', clase: 'est-discrepan' },
    faltan: { etiqueta: 'Missing data', clase: 'est-faltan' }
  };

  function claseDivergente(v, maxAbs) {
    if (v === null || v === undefined || !isFinite(v)) return null;
    var r = Math.abs(v) / (maxAbs || 1);
    var paso = r < 0.2 ? 0 : r < 0.5 ? 1 : r < 0.8 ? 2 : 3;
    if (paso === 0) return 'var(--div-neutro)';
    return 'var(--div-' + (v > 0 ? 'pos' : 'neg') + '-' + paso + ')';
  }

  function colorMapa(r, regiones) {
    if (!r || r.analisis.veredicto.estado === 'faltan' || !r.analisis.sen) return '--tierra';
    return claseDivergente(r.analisis.sen.pendiente, maxAbsPendiente(regiones)).slice(4, -1);
  }

  function maxAbsPendiente(regiones) {
    var m = 0;
    regiones.forEach(function (r) { if (r.analisis.sen) m = Math.max(m, Math.abs(r.analisis.sen.pendiente)); });
    return m || 1;
  }

  function resumenCorto(r, meta) {
    var v = r.analisis.veredicto.estado, s = ESTADOS[v].etiqueta;
    if (r.analisis.sen) s += '<br><span class="t">Theil-Sen ' + conSigno(r.analisis.sen.pendiente) + ' ' + meta.unidades_pendiente + '</span>';
    return s;
  }

  // ---------- serie anual ----------
  function dibujarSerie(cont, region, meta) {
    cont.innerHTML = '';
    var W = Math.max(280, cont.clientWidth || 600), estrecho = W < 480;
    var H = estrecho ? 240 : 300, m = { l: estrecho ? 46 : 56, r: 12, t: 12, b: 30 };
    var serie = region.serie;
    var validos = serie.filter(function (p) { return p.valor !== null; });
    var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H }, cont);
    if (!validos.length) {
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', 'No data for ' + region.nombre);
      texto(svg, W / 2, H / 2, 'No rainfall data for this area.', { 'text-anchor': 'middle' });
      return;
    }
    var a0 = meta.periodo[0], a1 = meta.periodo[1];
    var tm = region.analisis.mco, ts = region.analisis.sen;
    var ys = validos.map(function (p) { return p.valor; });
    [tm, ts].forEach(function (t) { if (t && isFinite(t.intercepto)) { ys.push(window.SofContrato.valorAjustado(t, a0), window.SofContrato.valorAjustado(t, a1)); } });
    var ymin = Math.min.apply(null, ys), ymax = Math.max.apply(null, ys), pad = (ymax - ymin) * 0.08 || 50;
    ymin -= pad; ymax += pad;
    var X = function (a) { return m.l + (a - a0) / (a1 - a0) * (W - m.l - m.r); };
    var Y = function (v) { return m.t + (ymax - v) / (ymax - ymin) * (H - m.t - m.b); };

    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Annual precipitation in ' + region.nombre + ' from ' + a0 + ' to ' + a1 +
      (tm ? ', with least-squares (' + conSigno(tm.pendiente) + ') and Theil–Sen (' + conSigno(ts.pendiente) + ') trend lines, ' + meta.unidades_pendiente : '') +
      '. Use the left and right arrow keys to step through the years.');
    svg.setAttribute('tabindex', '0');

    var gEje = el('g', { class: 'eje' }, svg);
    ticksBonitos(ymin, ymax, estrecho ? 4 : 5).forEach(function (v) {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), class: 'rejilla-h' }, gEje);
      texto(gEje, m.l - 6, Y(v) + 4, nf0.format(v), { 'text-anchor': 'end' });
    });
    var pasoA = estrecho ? 6 : 3;
    for (var a = a0; a <= a1; a++) {
      if ((a - a0) % pasoA === 0 || a === a1) texto(gEje, X(a), H - 8, String(a), { 'text-anchor': 'middle' });
    }
    texto(gEje, m.l, m.t - 2, meta.unidades, { 'text-anchor': 'start', 'font-size': 11, dy: 0, style: 'fill:var(--texto-3)' }).setAttribute('y', 10);

    // tendencias (detrás de la serie)
    if (tm) el('line', { x1: X(a0), x2: X(a1), y1: Y(window.SofContrato.valorAjustado(tm, a0)), y2: Y(window.SofContrato.valorAjustado(tm, a1)), stroke: 'var(--serie-mco)', 'stroke-width': 2.5 }, svg);
    if (ts) el('line', { x1: X(a0), x2: X(a1), y1: Y(window.SofContrato.valorAjustado(ts, a0)), y2: Y(window.SofContrato.valorAjustado(ts, a1)), stroke: 'var(--serie-sen)', 'stroke-width': 2.5, 'stroke-dasharray': '7 5' }, svg);

    // serie observada con huecos donde falta dato
    var d = '', abierto = false;
    serie.forEach(function (p) {
      if (p.valor === null) { abierto = false; return; }
      d += (abierto ? 'L' : 'M') + X(p.anio).toFixed(1) + ',' + Y(p.valor).toFixed(1);
      abierto = true;
    });
    el('path', { d: d, fill: 'none', stroke: 'var(--observado)', 'stroke-width': 2, 'stroke-linejoin': 'round' }, svg);
    validos.forEach(function (p) {
      el('circle', { cx: X(p.anio), cy: Y(p.valor), r: 4, fill: 'var(--observado)', stroke: 'var(--superficie)', 'stroke-width': 2 }, svg);
    });
    (region.anios_sin_dato || []).forEach(function (a) {
      texto(svg, X(a), H - m.b - 6, '×', { 'text-anchor': 'middle', style: 'fill:var(--texto-3)', 'font-size': 14 });
    });

    // capa de lectura: cruz + tooltip, ratón y teclado
    var guia = el('line', { y1: m.t, y2: H - m.b, stroke: 'var(--texto-3)', 'stroke-width': 1, visibility: 'hidden' }, svg);
    var foco = el('circle', { r: 6, fill: 'none', stroke: 'var(--texto)', 'stroke-width': 2, visibility: 'hidden' }, svg);
    var capa = el('rect', { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: 'transparent' }, svg);
    var actual = null;
    function mostrar(anio, cx, cy) {
      actual = anio;
      var p = serie.find(function (q) { return q.anio === anio; });
      guia.setAttribute('x1', X(anio)); guia.setAttribute('x2', X(anio)); guia.setAttribute('visibility', 'visible');
      if (p && p.valor !== null) { foco.setAttribute('cx', X(anio)); foco.setAttribute('cy', Y(p.valor)); foco.setAttribute('visibility', 'visible'); }
      else foco.setAttribute('visibility', 'hidden');
      var html = '<strong>' + anio + '</strong><br>Observed: ' + (p && p.valor !== null ? nf0.format(p.valor) + ' ' + escapar(meta.unidades) : 'no data');
      if (tm) html += '<br><span class="t">Least squares: ' + nf0.format(window.SofContrato.valorAjustado(tm, anio)) + '</span>';
      if (ts) html += '<br><span class="t">Theil–Sen: ' + nf0.format(window.SofContrato.valorAjustado(ts, anio)) + '</span>';
      if (cx === undefined) {
        var r = svg.getBoundingClientRect();
        cx = r.left + X(anio) * r.width / W; cy = r.top + (p && p.valor !== null ? Y(p.valor) : m.t + 20) * r.height / H;
      }
      mostrarTip(html, cx, cy);
    }
    function ocultar() { guia.setAttribute('visibility', 'hidden'); foco.setAttribute('visibility', 'hidden'); ocultarTip(); }
    capa.addEventListener('pointermove', function (ev) {
      var r = svg.getBoundingClientRect(), xv = (ev.clientX - r.left) * W / r.width;
      var anio = Math.round(a0 + (xv - m.l) / (W - m.l - m.r) * (a1 - a0));
      mostrar(Math.max(a0, Math.min(a1, anio)), ev.clientX, ev.clientY);
    });
    capa.addEventListener('pointerleave', ocultar);
    svg.addEventListener('keydown', function (ev) {
      if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].indexOf(ev.key) < 0) { if (ev.key === 'Escape') ocultar(); return; }
      ev.preventDefault();
      var n = actual === null ? a0 : ev.key === 'ArrowLeft' ? actual - 1 : ev.key === 'ArrowRight' ? actual + 1 : ev.key === 'Home' ? a0 : a1;
      mostrar(Math.max(a0, Math.min(a1, n)));
    });
    svg.addEventListener('blur', ocultar);
  }

  // ---------- comparación de pendientes ----------
  function dibujarComparacion(cont, regiones, selId, meta, alElegir) {
    cont.innerHTML = '';
    var W = Math.max(280, cont.clientWidth || 800), estrecho = W < 560;
    var etq = estrecho ? 112 : 190, m = { l: etq, r: 16, t: 8, b: 34 }, fila = estrecho ? 58 : 52;
    var H = m.t + m.b + fila * regiones.length;
    var vals = [0];
    regiones.forEach(function (r) { ['mco', 'sen'].forEach(function (k) { var t = r.analisis[k]; if (t) vals.push(t.ic_inf, t.ic_sup); }); });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), pad = (hi - lo) * 0.06 || 1;
    lo -= pad; hi += pad;
    var X = function (v) { return m.l + (v - lo) / (hi - lo) * (W - m.l - m.r); };
    var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img',
      'aria-label': 'Theil–Sen and least-squares slopes with ' + Math.round(meta.nivel_confianza * 100) + '% intervals for each area on a common scale with a zero line.' }, cont);

    var g = el('g', { class: 'eje' }, svg);
    ticksBonitos(lo, hi, estrecho ? 4 : 7).forEach(function (v) {
      el('line', { x1: X(v), x2: X(v), y1: m.t, y2: H - m.b, class: 'rejilla-h' }, g);
      texto(g, X(v), H - m.b + 16, conSigno(v, nf0), { 'text-anchor': 'middle' });
    });
    texto(g, W - m.r, H - 4, meta.unidades_pendiente, { 'text-anchor': 'end', style: 'fill:var(--texto-3)', 'font-size': 11 });
    texto(g, X(0), H - 4, estrecho ? '' : 'no change', { 'text-anchor': 'middle', style: 'fill:var(--texto-3)', 'font-size': 11 });

    regiones.forEach(function (r, i) {
      var y0 = m.t + i * fila, yc = y0 + fila / 2;
      var grupo = el('g', { 'data-region': r.id, style: 'cursor:pointer' }, svg);
      el('rect', { x: 0, y: y0 + 2, width: W, height: fila - 4, rx: 6, fill: r.id === selId ? 'var(--superficie-2)' : 'transparent' }, grupo);
      if (r.id === selId) el('rect', { x: 0, y: y0 + 2, width: 3, height: fila - 4, fill: 'var(--texto)' }, grupo);
      var est = ESTADOS[r.analisis.veredicto.estado];
      texto(grupo, 10, yc - 3, r.nombre, { style: 'fill:var(--texto);font-weight:' + (r.id === selId ? 700 : 500), 'font-size': 13 });
      var tEst = texto(grupo, 10, yc + 13, est.etiqueta, { 'font-size': 11 });
      tEst.setAttribute('class', est.clase);
      tEst.style.fill = 'currentColor';
      if (!r.analisis.mco) {
        texto(grupo, X(0) + 8, yc + 4, 'no trend available', { style: 'fill:var(--texto-3)', 'font-size': 12 });
      }
      [['mco', -7, 'var(--serie-mco)', 'Least squares'], ['sen', 7, 'var(--serie-sen)', 'Theil–Sen']].forEach(function (cfg) {
        var t = r.analisis[cfg[0]]; if (!t) return;
        var y = yc + cfg[1];
        el('line', { x1: X(t.ic_inf), x2: X(t.ic_sup), y1: y, y2: y, stroke: cfg[2], 'stroke-width': 2.5, 'stroke-linecap': 'round', 'stroke-dasharray': cfg[0] === 'sen' ? '6 3' : null }, grupo);
        var forma = cfg[0] === 'mco'
          ? el('circle', { cx: X(t.pendiente), cy: y, r: 5, fill: cfg[2], stroke: 'var(--superficie)', 'stroke-width': 2 }, grupo)
          : el('rect', { x: X(t.pendiente) - 5, y: y - 5, width: 10, height: 10, fill: cfg[2], stroke: 'var(--superficie)', 'stroke-width': 2, transform: 'rotate(45 ' + X(t.pendiente) + ' ' + y + ')' }, grupo);
        var hit = el('rect', { x: X(t.ic_inf) - 6, y: y - 7, width: X(t.ic_sup) - X(t.ic_inf) + 12, height: 14, fill: 'transparent' }, grupo);
        [hit, forma].forEach(function (n) {
          n.addEventListener('pointermove', function (ev) {
            mostrarTip('<strong>' + escapar(r.nombre) + ' · ' + escapar(cfg[3]) + '</strong><br>' + conSigno(t.pendiente) + ' ' + escapar(meta.unidades_pendiente) +
              '<br><span class="t">' + Math.round(meta.nivel_confianza * 100) + '% CI: ' + conSigno(t.ic_inf) + ' to ' + conSigno(t.ic_sup) + '</span>', ev.clientX, ev.clientY);
          });
          n.addEventListener('pointerleave', ocultarTip);
        });
      });
      grupo.addEventListener('click', function () { alElegir(r.id); });
    });
    el('line', { x1: X(0), x2: X(0), y1: m.t, y2: H - m.b, class: 'cero' }, svg);
  }

  function escapar(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }

  window.SofGraficas = {
    ESTADOS: ESTADOS, colorMapa: colorMapa, dibujarSerie: dibujarSerie,
    dibujarComparacion: dibujarComparacion, ocultarTip: ocultarTip,
    formato: { nf0: nf0, nf1: nf1, nf2: nf2, conSigno: conSigno }, escapar: escapar
  };
})();
