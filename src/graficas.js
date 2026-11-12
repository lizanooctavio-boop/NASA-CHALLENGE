/*
 * Dibujo de mapa, serie anual, comparación de pendientes y bloque ONI en SVG, sin librerías.
 * Cada gráfica se dibuja al ancho real de su contenedor para que el texto conserve su tamaño en móvil.
 */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var nf1 = new Intl.NumberFormat('es-NI', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var nf0 = new Intl.NumberFormat('es-NI', { maximumFractionDigits: 0 });
  var nf2 = new Intl.NumberFormat('es-NI', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

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
    var x = clientX + window.scrollX, y = clientY + window.scrollY;
    var ancho = t.offsetWidth, min = window.scrollX + ancho / 2 + 8, max = window.scrollX + document.documentElement.clientWidth - ancho / 2 - 8;
    t.style.left = Math.max(min, Math.min(max, x)) + 'px';
    t.style.top = y + 'px';
  }
  function ocultarTip() { if (tooltip()) tooltip().hidden = true; }

  // ---------- colores ----------
  var ESTADOS = {
    aumento: { etiqueta: 'Aumento', clase: 'est-aumento' },
    disminucion: { etiqueta: 'Disminución', clase: 'est-disminucion' },
    insuficiente: { etiqueta: 'Evidencia insuficiente', clase: 'est-insuficiente' },
    discrepan: { etiqueta: 'Los métodos discrepan', clase: 'est-discrepan' },
    faltan: { etiqueta: 'Datos faltantes', clase: 'est-faltan' }
  };

  function claseDivergente(v, maxAbs) {
    if (v === null || v === undefined || !isFinite(v)) return null;
    var r = Math.abs(v) / (maxAbs || 1);
    var paso = r < 0.2 ? 0 : r < 0.5 ? 1 : r < 0.8 ? 2 : 3;
    if (paso === 0) return 'var(--div-neutro)';
    return 'var(--div-' + (v > 0 ? 'pos' : 'neg') + '-' + paso + ')';
  }

  // ---------- mapa ----------
  function dibujarMapa(cont, datos, selId, alElegir) {
    cont.innerHTML = '';
    var C = window.SOF_CONTORNOS;
    var lon0 = -89.6, lon1 = -82.3, lat0 = 7.85, lat1 = 16.15, cosl = Math.cos(12 * Math.PI / 180);
    var W = Math.max(260, cont.clientWidth || 400);
    var k = W / ((lon1 - lon0) * cosl), H = Math.round((lat1 - lat0) * k);
    function px(p) { return [((p[0] - lon0) * cosl * k).toFixed(1), ((lat1 - p[1]) * k).toFixed(1)]; }
    function ruta(anillo) { return 'M' + anillo.map(function (p) { return px(p).join(','); }).join('L') + 'Z'; }

    var porId = {};
    datos.regiones.forEach(function (r) { porId[r.id] = r; });
    var maxAbs = maxAbsPendiente(datos.regiones);
    var sel = porId[selId];
    var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img',
      'aria-label': 'Mapa de Centroamérica con ' + (sel ? sel.nombre : '') + ' resaltada. ' + datos.regiones.map(function (r) {
        return r.nombre + ': ' + ESTADOS[r.analisis.veredicto.estado].etiqueta.toLowerCase();
      }).join('; ') + '.' }, cont);
    el('rect', { x: 0, y: 0, width: W, height: H, fill: 'var(--agua)', rx: 6 }, svg);
    var defs = el('defs', null, svg);
    var pat = el('pattern', { id: 'rayado', width: 6, height: 6, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' }, defs);
    el('rect', { width: 6, height: 6, fill: 'var(--tierra)' }, pat);
    el('line', { x1: 0, y1: 0, x2: 0, y2: 6, stroke: 'var(--texto-3)', 'stroke-width': 1.2 }, pat);

    function relleno(r) {
      if (!r || r.analisis.veredicto.estado === 'faltan' || !r.analisis.sen) return 'url(#rayado)';
      return claseDivergente(r.analisis.sen.pendiente, maxAbs);
    }
    function alPasar(r) {
      return function (ev) {
        mostrarTip('<strong>' + r.nombre + '</strong><br>' + resumenCorto(r, datos.meta), ev.clientX, ev.clientY);
      };
    }

    ['honduras', 'costa_rica', 'nicaragua'].forEach(function (id) {
      var r = porId[id];
      var anillo = (r && Array.isArray(r.contorno) && r.contorno.length > 2) ? r.contorno : C.paises[id];
      var p = el('path', { d: ruta(anillo), class: 'pais' + (id === selId ? ' sel' : ''), fill: relleno(r), 'data-region': id }, svg);
      p.addEventListener('click', function () { alElegir(id); });
      p.addEventListener('pointermove', alPasar(r));
      p.addEventListener('pointerleave', ocultarTip);
    });
    // la región seleccionada se dibuja encima para que su borde no quede tapado
    var selPath = svg.querySelector('.pais.sel');
    if (selPath) svg.appendChild(selPath);

    var caja = porId.caja_original;
    if (caja && caja.bbox) {
      var a = px([caja.bbox[0], caja.bbox[3]]), b = px([caja.bbox[2], caja.bbox[1]]);
      var g = el('g', null, svg);
      var fondo = el('rect', { x: a[0], y: a[1], width: b[0] - a[0], height: b[1] - a[1], fill: relleno(caja), 'fill-opacity': selId === 'caja_original' ? 0.9 : 0.6, 'data-region': 'caja_original' }, g);
      var borde = el('rect', { x: a[0], y: a[1], width: b[0] - a[0], height: b[1] - a[1], class: 'caja' + (selId === 'caja_original' ? ' sel' : '') }, g);
      [fondo, borde].forEach(function (n) {
        n.style.cursor = 'pointer';
        n.addEventListener('click', function () { alElegir('caja_original'); });
        n.addEventListener('pointermove', alPasar(caja));
        n.addEventListener('pointerleave', ocultarTip);
      });
      texto(svg, Number(a[0]) + 6, Number(b[1]) - 8, 'Caja original', { class: 'rotulo-caja' });
    }
    C.lagos.forEach(function (l) { el('path', { d: ruta(l), class: 'lago' }, svg); });
    Object.keys(C.rotulos).forEach(function (id) {
      var p = px(C.rotulos[id]);
      texto(svg, p[0], p[1], (porId[id] && porId[id].nombre) || id, { class: 'rotulo', 'text-anchor': 'middle' });
    });
    svg.addEventListener('pointerleave', ocultarTip);
  }

  function dibujarEscalaMapa(cont, regiones, meta) {
    var maxAbs = maxAbsPendiente(regiones);
    cont.innerHTML = '<span>Menos lluvia</span><span class="barras">' +
      ['neg-3', 'neg-2', 'neg-1'].map(function (c) { return '<span style="background:var(--div-' + c + ')"></span>'; }).join('') +
      '<span style="background:var(--div-neutro)"></span>' +
      ['pos-1', 'pos-2', 'pos-3'].map(function (c) { return '<span style="background:var(--div-' + c + ')"></span>'; }).join('') +
      '</span><span>Más lluvia</span><span>(±' + nf0.format(maxAbs) + ' ' + meta.unidades_pendiente + ')</span>' +
      '<span class="barras"><span style="background:var(--tierra);background-image:repeating-linear-gradient(45deg,var(--texto-3) 0 1px,transparent 1px 5px)"></span></span><span>sin datos</span>';
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
      svg.setAttribute('aria-label', 'Sin datos para ' + region.nombre);
      texto(svg, W / 2, H / 2, 'No hay datos de lluvia para esta región.', { 'text-anchor': 'middle' });
      return;
    }
    var a0 = meta.periodo[0], a1 = meta.periodo[1];
    var tm = region.analisis.mco, ts = region.analisis.sen;
    var ys = validos.map(function (p) { return p.valor; });
    [tm, ts].forEach(function (t) { if (t && isFinite(t.intercepto)) { ys.push(t.intercepto + t.pendiente * a0, t.intercepto + t.pendiente * a1); } });
    var ymin = Math.min.apply(null, ys), ymax = Math.max.apply(null, ys), pad = (ymax - ymin) * 0.08 || 50;
    ymin -= pad; ymax += pad;
    var X = function (a) { return m.l + (a - a0) / (a1 - a0) * (W - m.l - m.r); };
    var Y = function (v) { return m.t + (ymax - v) / (ymax - ymin) * (H - m.t - m.b); };

    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Precipitación anual de ' + region.nombre + ' entre ' + a0 + ' y ' + a1 +
      (tm ? ', con rectas de tendencia por mínimos cuadrados (' + conSigno(tm.pendiente) + ') y Theil-Sen (' + conSigno(ts.pendiente) + ') ' + meta.unidades_pendiente : '') +
      '. Use las flechas izquierda y derecha para recorrer los años.');
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
    if (tm) el('line', { x1: X(a0), x2: X(a1), y1: Y(tm.intercepto + tm.pendiente * a0), y2: Y(tm.intercepto + tm.pendiente * a1), stroke: 'var(--serie-mco)', 'stroke-width': 2.5 }, svg);
    if (ts) el('line', { x1: X(a0), x2: X(a1), y1: Y(ts.intercepto + ts.pendiente * a0), y2: Y(ts.intercepto + ts.pendiente * a1), stroke: 'var(--serie-sen)', 'stroke-width': 2.5, 'stroke-dasharray': '7 5' }, svg);

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
      var html = '<strong>' + anio + '</strong><br>Observado: ' + (p && p.valor !== null ? nf0.format(p.valor) + ' ' + meta.unidades : 'sin dato');
      if (tm) html += '<br><span class="t">Recta MCO: ' + nf0.format(tm.intercepto + tm.pendiente * anio) + '</span>';
      if (ts) html += '<br><span class="t">Recta Theil-Sen: ' + nf0.format(ts.intercepto + ts.pendiente * anio) + '</span>';
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
      'aria-label': 'Pendientes de Theil-Sen y mínimos cuadrados con intervalos del ' + Math.round(meta.nivel_confianza * 100) + ' % para las cuatro regiones, en una misma escala con una línea en cero. La tabla siguiente contiene los mismos valores.' }, cont);

    var g = el('g', { class: 'eje' }, svg);
    ticksBonitos(lo, hi, estrecho ? 4 : 7).forEach(function (v) {
      el('line', { x1: X(v), x2: X(v), y1: m.t, y2: H - m.b, class: 'rejilla-h' }, g);
      texto(g, X(v), H - m.b + 16, conSigno(v, nf0), { 'text-anchor': 'middle' });
    });
    texto(g, W - m.r, H - 4, meta.unidades_pendiente, { 'text-anchor': 'end', style: 'fill:var(--texto-3)', 'font-size': 11 });
    texto(g, X(0), H - 4, estrecho ? '' : 'sin cambio', { 'text-anchor': 'middle', style: 'fill:var(--texto-3)', 'font-size': 11 });

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
        texto(grupo, X(0) + 8, yc + 4, 'sin tendencia calculable', { style: 'fill:var(--texto-3)', 'font-size': 12 });
      }
      [['mco', -7, 'var(--serie-mco)', 'Mínimos cuadrados'], ['sen', 7, 'var(--serie-sen)', 'Theil-Sen']].forEach(function (cfg) {
        var t = r.analisis[cfg[0]]; if (!t) return;
        var y = yc + cfg[1];
        el('line', { x1: X(t.ic_inf), x2: X(t.ic_sup), y1: y, y2: y, stroke: cfg[2], 'stroke-width': 2.5, 'stroke-linecap': 'round', 'stroke-dasharray': cfg[0] === 'sen' ? '6 3' : null }, grupo);
        var forma = cfg[0] === 'mco'
          ? el('circle', { cx: X(t.pendiente), cy: y, r: 5, fill: cfg[2], stroke: 'var(--superficie)', 'stroke-width': 2 }, grupo)
          : el('rect', { x: X(t.pendiente) - 5, y: y - 5, width: 10, height: 10, fill: cfg[2], stroke: 'var(--superficie)', 'stroke-width': 2, transform: 'rotate(45 ' + X(t.pendiente) + ' ' + y + ')' }, grupo);
        var hit = el('rect', { x: X(t.ic_inf) - 6, y: y - 7, width: X(t.ic_sup) - X(t.ic_inf) + 12, height: 14, fill: 'transparent' }, grupo);
        [hit, forma].forEach(function (n) {
          n.addEventListener('pointermove', function (ev) {
            mostrarTip('<strong>' + r.nombre + ' · ' + cfg[3] + '</strong><br>' + conSigno(t.pendiente) + ' ' + meta.unidades_pendiente +
              '<br><span class="t">IC ' + Math.round(meta.nivel_confianza * 100) + ' %: ' + conSigno(t.ic_inf) + ' a ' + conSigno(t.ic_sup) + '</span>', ev.clientX, ev.clientY);
          });
          n.addEventListener('pointerleave', ocultarTip);
        });
      });
      grupo.addEventListener('click', function () { alElegir(r.id); });
    });
    el('line', { x1: X(0), x2: X(0), y1: m.t, y2: H - m.b, class: 'cero' }, svg);
  }

  // ---------- ONI ----------
  function dibujarOni(cont, oni, region, meta) {
    cont.innerHTML = '';
    var E = window.SofEstadistica;
    var limites = '<div class="limites"><h3>Qué muestra y qué no</h3><ul>' +
      '<li>Muestra <strong>asociación</strong>: si los años con El Niño o La Niña coinciden con años más secos o más lluviosos. No demuestra que el ONI cause la diferencia ni explica la tendencia.</li>' +
      '<li>El ONI anual es un promedio; El Niño suele alcanzar su máximo en diciembre-febrero y su efecto sobre la lluvia cambia según la temporada y entre la vertiente del Pacífico y la del Caribe.</li>' +
      '<li>En 24 años hay pocos eventos fuertes, así que un solo año puede mover la correlación.</li>' +
      '<li>Para no mezclar la relación con la tendencia, la lluvia se compara como anomalía respecto a la recta de Theil-Sen.</li></ul></div>';
    if (!oni) {
      cont.innerHTML = '<p class="sub">El archivo de datos no incluye la serie ONI, así que este bloque queda vacío.</p>' + limites;
      return;
    }
    var porAnio = {};
    oni.serie.forEach(function (p) { porAnio[p.anio] = p.valor; });
    var pares = [];
    if (region.analisis.sen) {
      region.serie.forEach(function (p) {
        if (p.valor !== null && porAnio[p.anio] !== undefined) {
          var t = region.analisis.sen;
          pares.push({ anio: p.anio, oni: porAnio[p.anio], anom: p.valor - (t.intercepto + t.pendiente * p.anio) });
        }
      });
    }
    var c = pares.length >= 3 ? E.pearson(pares.map(function (q) { return q.oni; }), pares.map(function (q) { return q.anom; })) : null;
    var frase = c
      ? 'En ' + region.nombre + ', la correlación entre el ONI anual y la anomalía de lluvia es r = ' + nf2.format(c.r) + ' (n = ' + c.n + ' años, p ≈ ' + nf2.format(c.p) + '). ' +
        (c.p < 0.05 ? (c.r < 0 ? 'Los años con ONI alto (El Niño) tienden a ser más secos.' : 'Los años con ONI alto (El Niño) tienden a ser más lluviosos.') : 'Con estos datos la asociación no es clara.')
      : 'No hay suficientes años con lluvia y ONI para calcular la asociación en ' + region.nombre + '.';
    var intro = document.createElement('div');
    intro.innerHTML = '<p class="sub">Fuente: ' + escapar(oni.fuente) + '. Agregación: ' + escapar(oni.agregacion) + '.</p><p>' + frase + '</p>';
    cont.appendChild(intro);

    var fila = document.createElement('div');
    fila.className = 'dos';
    var c1 = document.createElement('div'), c2 = document.createElement('div');
    c1.className = 'grafica'; c2.className = 'grafica';
    fila.appendChild(c1); fila.appendChild(c2);
    cont.appendChild(fila);
    var lim = document.createElement('div');
    lim.innerHTML = limites;
    cont.appendChild(lim);

    // barras ONI por año
    var W = Math.max(260, c1.clientWidth || 400), H = 200, m = { l: 36, r: 8, t: 22, b: 26 };
    var a0 = meta.periodo[0], a1 = meta.periodo[1];
    var vmax = Math.max(2, Math.max.apply(null, oni.serie.map(function (p) { return Math.abs(p.valor); })));
    var bw = (W - m.l - m.r) / (a1 - a0 + 1);
    var X = function (a) { return m.l + (a - a0) * bw; }, Y = function (v) { return m.t + (vmax - v) / (2 * vmax) * (H - m.t - m.b); };
    var s1 = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Índice ONI anual de ' + a0 + ' a ' + a1 + '. Barras hacia arriba: El Niño; hacia abajo: La Niña.' }, c1);
    texto(s1, m.l, 12, 'ONI anual (°C)', { style: 'fill:var(--texto-3)', 'font-size': 11 });
    [-1, -0.5, 0, 0.5, 1].forEach(function (v) {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), class: v === 0 ? 'cero' : 'rejilla-h' }, s1);
      if (v !== 0.5 && v !== -0.5) texto(s1, m.l - 4, Y(v) + 4, conSigno(v, nf0), { 'text-anchor': 'end' });
    });
    oni.serie.forEach(function (p) {
      if (p.anio < a0 || p.anio > a1) return;
      var color = p.valor >= 0.5 ? 'var(--div-neg-2)' : p.valor <= -0.5 ? 'var(--div-pos-2)' : 'var(--texto-3)';
      var y = Math.min(Y(0), Y(p.valor)), h = Math.max(1, Math.abs(Y(p.valor) - Y(0)));
      var b = el('rect', { x: X(p.anio) + 1, y: y, width: Math.max(1, bw - 2), height: h, fill: color, rx: 2 }, s1);
      b.addEventListener('pointermove', function (ev) {
        mostrarTip('<strong>' + p.anio + '</strong><br>ONI ' + conSigno(p.valor, nf2) + '<br><span class="t">' + (p.valor >= 0.5 ? 'El Niño' : p.valor <= -0.5 ? 'La Niña' : 'Neutro') + '</span>', ev.clientX, ev.clientY);
      });
      b.addEventListener('pointerleave', ocultarTip);
    });
    [a0, a0 + 8, a0 + 16, a1].forEach(function (a) { texto(s1, X(a) + bw / 2, H - 8, String(a), { 'text-anchor': 'middle' }); });

    // dispersión ONI vs anomalía
    var W2 = Math.max(260, c2.clientWidth || 400), m2 = { l: 48, r: 10, t: 22, b: 30 };
    var s2 = el('svg', { width: W2, height: H, viewBox: '0 0 ' + W2 + ' ' + H, role: 'img', 'aria-label': 'Dispersión de ONI anual frente a la anomalía de lluvia de ' + region.nombre + '.' }, c2);
    texto(s2, m2.l, 12, 'Anomalía de lluvia (' + meta.unidades + ') frente a ONI', { style: 'fill:var(--texto-3)', 'font-size': 11 });
    if (!pares.length) { texto(s2, W2 / 2, H / 2, 'Sin datos', { 'text-anchor': 'middle' }); return; }
    var amax = Math.max.apply(null, pares.map(function (q) { return Math.abs(q.anom); })) * 1.1;
    var X2 = function (v) { return m2.l + (v + vmax) / (2 * vmax) * (W2 - m2.l - m2.r); };
    var Y2 = function (v) { return m2.t + (amax - v) / (2 * amax) * (H - m2.t - m2.b); };
    ticksBonitos(-amax, amax, 4).forEach(function (v) {
      el('line', { x1: m2.l, x2: W2 - m2.r, y1: Y2(v), y2: Y2(v), class: v === 0 ? 'cero' : 'rejilla-h' }, s2);
      texto(s2, m2.l - 4, Y2(v) + 4, conSigno(v, nf0), { 'text-anchor': 'end' });
    });
    [-1, 0, 1].forEach(function (v) {
      el('line', { x1: X2(v), x2: X2(v), y1: m2.t, y2: H - m2.b, class: v === 0 ? 'cero' : 'rejilla-h' }, s2);
      texto(s2, X2(v), H - 12, conSigno(v, nf0), { 'text-anchor': 'middle' });
    });
    texto(s2, W2 - m2.r, H - 1, 'ONI', { 'text-anchor': 'end', style: 'fill:var(--texto-3)', 'font-size': 11 });
    pares.forEach(function (q) {
      var p = el('circle', { cx: X2(q.oni), cy: Y2(q.anom), r: 5, fill: 'var(--observado)', 'fill-opacity': 0.75, stroke: 'var(--superficie)', 'stroke-width': 1.5 }, s2);
      p.addEventListener('pointermove', function (ev) {
        mostrarTip('<strong>' + q.anio + '</strong><br>ONI ' + conSigno(q.oni, nf2) + '<br>Anomalía ' + conSigno(q.anom, nf0) + ' ' + meta.unidades, ev.clientX, ev.clientY);
      });
      p.addEventListener('pointerleave', ocultarTip);
    });
  }

  function escapar(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }

  window.SofGraficas = {
    ESTADOS: ESTADOS, dibujarMapa: dibujarMapa, dibujarEscalaMapa: dibujarEscalaMapa, dibujarSerie: dibujarSerie,
    dibujarComparacion: dibujarComparacion, dibujarOni: dibujarOni, ocultarTip: ocultarTip,
    formato: { nf0: nf0, nf1: nf1, nf2: nf2, conSigno: conSigno }, escapar: escapar
  };
})();
