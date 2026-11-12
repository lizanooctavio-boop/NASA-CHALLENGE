/*
 * Dibujo de mapa, serie anual, comparación de intervalos y bloque ONI en SVG, sin librerías.
 * Cada gráfica se dibuja al ancho real de su contenedor para que el texto conserve su tamaño en móvil.
 * Las pendientes se expresan en mm/década, como en el contrato 1.0.0.
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
  function escapar(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
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

  // ---------- estados ----------
  var ESTADOS = {
    detectada: { etiqueta: 'Tendencia detectada', clase: 'est-detectada' },
    insuficiente: { etiqueta: 'Evidencia insuficiente', clase: 'est-insuficiente' },
    discrepan: { etiqueta: 'Los métodos discrepan', clase: 'est-discrepan' },
    faltan: { etiqueta: 'Datos faltantes', clase: 'est-faltan' }
  };
  var METODOS = [
    { clave: 'principal', nombre: 'Mínimos cuadrados (principal)', corto: 'MCO', color: 'var(--serie-mco)', forma: 'circulo', guiones: null },
    { clave: 'hac', nombre: 'HAC de Newey–West', corto: 'HAC', color: 'var(--serie-hac)', forma: 'cuadrado', guiones: '2 3' },
    { clave: 'sen', nombre: 'Theil–Sen', corto: 'Theil–Sen', color: 'var(--serie-sen)', forma: 'rombo', guiones: '6 3' }
  ];

  function rellenoEstado(r) {
    var t = r && r.tendencia;
    if (!t || t.estado === 'faltan') return 'url(#rayado)';
    if (t.estado === 'detectada') return t.principal && t.principal.pendiente < 0 ? 'var(--mapa-detectada-neg)' : 'var(--mapa-detectada-pos)';
    return t.estado === 'discrepan' ? 'var(--mapa-discrepan)' : 'var(--mapa-insuficiente)';
  }

  function resumenCorto(r, meta) {
    var t = r.tendencia, s = ESTADOS[t.estado].etiqueta;
    if (t.principal) s += '<br><span class="t">MCO ' + conSigno(t.principal.pendiente) + ' ' + meta.unidades_pendiente + '</span>';
    return s;
  }

  // ---------- mapa ----------
  var CONTORNO_LOCAL = { NIC: 'nicaragua', HND: 'honduras', CRI: 'costa_rica' };

  function anillosDe(geom) {
    if (!geom) return null;
    if (geom.type === 'Polygon') return geom.coordinates;
    if (geom.type === 'MultiPolygon') return geom.coordinates.reduce(function (a, p) { return a.concat(p); }, []);
    return null;
  }

  function dibujarMapa(cont, datos, selId, alElegir) {
    cont.innerHTML = '';
    var C = window.SOF_CONTORNOS;
    var lon0 = -89.6, lon1 = -82.3, lat0 = 7.85, lat1 = 16.15, cosl = Math.cos(12 * Math.PI / 180);
    var W = Math.max(260, cont.clientWidth || 400);
    var k = W / ((lon1 - lon0) * cosl), H = Math.round((lat1 - lat0) * k);
    function px(p) { return [((p[0] - lon0) * cosl * k).toFixed(1), ((lat1 - p[1]) * k).toFixed(1)]; }
    function ruta(anillos) { return anillos.map(function (an) { return 'M' + an.map(function (p) { return px(p).join(','); }).join('L') + 'Z'; }).join(''); }

    var porId = {};
    datos.regiones.forEach(function (r) { porId[r.id] = r; });
    var sel = porId[selId];
    var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img',
      'aria-label': 'Mapa de Centroamérica con ' + (sel ? sel.nombre : '') + ' resaltada. ' + datos.regiones.map(function (r) {
        return r.nombre + ': ' + ESTADOS[r.tendencia.estado].etiqueta.toLowerCase();
      }).join('; ') + '.' }, cont);
    el('rect', { x: 0, y: 0, width: W, height: H, fill: 'var(--agua)', rx: 6 }, svg);
    var defs = el('defs', null, svg);
    var pat = el('pattern', { id: 'rayado', width: 6, height: 6, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' }, defs);
    el('rect', { width: 6, height: 6, fill: 'var(--tierra)' }, pat);
    el('line', { x1: 0, y1: 0, x2: 0, y2: 6, stroke: 'var(--texto-3)', 'stroke-width': 1.2 }, pat);

    function conEventos(n, r) {
      n.addEventListener('click', function () { alElegir(r.id); });
      n.addEventListener('pointermove', function (ev) { mostrarTip('<strong>' + escapar(r.nombre) + '</strong><br>' + resumenCorto(r, datos.meta), ev.clientX, ev.clientY); });
      n.addEventListener('pointerleave', ocultarTip);
    }

    var usaGeojson = false;
    ['HND', 'CRI', 'NIC'].forEach(function (id) {
      var r = porId[id] || { id: id, nombre: id, tendencia: { estado: 'faltan' } };
      var anillos = anillosDe(r.geometria);
      if (anillos) usaGeojson = true; else anillos = [C.paises[CONTORNO_LOCAL[id]]];
      var p = el('path', { d: ruta(anillos), class: 'pais' + (id === selId ? ' sel' : ''), fill: rellenoEstado(r), 'fill-rule': 'evenodd', 'data-region': id }, svg);
      conEventos(p, r);
    });
    var selPath = svg.querySelector('.pais.sel');
    if (selPath) svg.appendChild(selPath);
    if (!usaGeojson) C.lagos.forEach(function (l) { el('path', { d: ruta([l]), class: 'lago' }, svg); });

    var caja = porId.caja_sicc;
    if (caja && (caja.bbox || caja.geometria)) {
      var g = el('g', null, svg), forma;
      var an = anillosDe(caja.geometria);
      var b = caja.bbox || [-86.5, 10.7, -83.6, 12.6];
      if (!an) an = [[[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]]];
      el('path', { d: ruta(an), fill: rellenoEstado(caja), 'fill-opacity': selId === 'caja_sicc' ? 0.9 : 0.55, 'data-region': 'caja_sicc', style: 'cursor:pointer' }, g);
      forma = el('path', { d: ruta(an), class: 'caja' + (selId === 'caja_sicc' ? ' sel' : '') }, g);
      Array.prototype.forEach.call(g.childNodes, function (n) { conEventos(n, caja); });
      var esq = px([b[0], b[1]]);
      texto(svg, Number(esq[0]) + 6, Number(esq[1]) - 8, 'Caja original', { class: 'rotulo-caja' });
    }
    Object.keys(C.rotulos).forEach(function (clave) {
      var id = Object.keys(CONTORNO_LOCAL).filter(function (k2) { return CONTORNO_LOCAL[k2] === clave; })[0];
      var p = px(C.rotulos[clave]);
      texto(svg, p[0], p[1], (porId[id] && porId[id].nombre) || id, { class: 'rotulo', 'text-anchor': 'middle' });
    });
    svg.addEventListener('pointerleave', ocultarTip);
    return usaGeojson;
  }

  function dibujarEscalaMapa(cont) {
    var m = function (fondo, txt) { return '<span class="item"><span class="muestra-mapa" style="' + fondo + '"></span>' + txt + '</span>'; };
    cont.innerHTML =
      m('background:var(--mapa-detectada-pos)', 'tendencia detectada (más lluvia)') +
      m('background:var(--mapa-detectada-neg)', 'tendencia detectada (menos lluvia)') +
      m('background:var(--mapa-insuficiente)', 'evidencia insuficiente') +
      m('background:var(--mapa-discrepan)', 'métodos discrepan') +
      m('background:var(--tierra);background-image:repeating-linear-gradient(45deg,var(--texto-3) 0 1px,transparent 1px 5px)', 'sin datos');
  }

  // ---------- serie anual ----------
  function recta(t, anio) { return t.intercepto + t.pendiente / 10 * anio; }

  function dibujarSerie(cont, region, meta) {
    cont.innerHTML = '';
    var W = Math.max(280, cont.clientWidth || 600), estrecho = W < 480;
    var H = estrecho ? 240 : 300, m = { l: estrecho ? 46 : 56, r: 12, t: 16, b: 30 };
    var serie = region.serie;
    var validos = serie.filter(function (p) { return p.valor !== null; });
    var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H }, cont);
    if (!validos.length) {
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', 'Sin datos para ' + region.nombre);
      texto(svg, W / 2, H / 2, 'No hay datos de lluvia para este dominio.', { 'text-anchor': 'middle' });
      return;
    }
    var a0 = meta.periodo[0], a1 = meta.periodo[1];
    var t = region.tendencia;
    var tm = t.principal && isFinite(t.principal.intercepto) ? t.principal : null;
    var ts = t.sen && isFinite(t.sen.intercepto) ? t.sen : null;
    var ys = validos.map(function (p) { return p.valor; });
    [tm, ts].forEach(function (q) { if (q) ys.push(recta(q, a0), recta(q, a1)); });
    var ymin = Math.min.apply(null, ys), ymax = Math.max.apply(null, ys), pad = (ymax - ymin) * 0.08 || 50;
    ymin -= pad; ymax += pad;
    var X = function (a) { return m.l + (a - a0) / (a1 - a0) * (W - m.l - m.r); };
    var Y = function (v) { return m.t + (ymax - v) / (ymax - ymin) * (H - m.t - m.b); };

    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Precipitación anual de ' + region.nombre + ' entre ' + a0 + ' y ' + a1 +
      (tm ? ', con recta de mínimos cuadrados (' + conSigno(tm.pendiente) + ' ' + meta.unidades_pendiente + ')' : '') +
      (ts ? ' y recta de Theil–Sen (' + conSigno(ts.pendiente) + ')' : '') + '. Use las flechas izquierda y derecha para recorrer los años.');
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
    texto(gEje, m.l, 10, meta.unidades, { 'text-anchor': 'start', 'font-size': 11, style: 'fill:var(--texto-3)' });

    if (tm) el('line', { x1: X(a0), x2: X(a1), y1: Y(recta(tm, a0)), y2: Y(recta(tm, a1)), stroke: 'var(--serie-mco)', 'stroke-width': 2.5 }, svg);
    if (ts) el('line', { x1: X(a0), x2: X(a1), y1: Y(recta(ts, a0)), y2: Y(recta(ts, a1)), stroke: 'var(--serie-sen)', 'stroke-width': 2.5, 'stroke-dasharray': '7 5' }, svg);

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
    (region.anios_sin_dato || []).forEach(function (an) {
      texto(svg, X(an), H - m.b - 6, '×', { 'text-anchor': 'middle', style: 'fill:var(--texto-3)', 'font-size': 14 });
    });

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
      var html = '<strong>' + anio + '</strong><br>Lluvia: ' + (p && p.valor !== null ? nf0.format(p.valor) + ' ' + meta.unidades : 'sin dato');
      if (tm) html += '<br><span class="t">Recta MCO: ' + nf0.format(recta(tm, anio)) + '</span>';
      if (ts) html += '<br><span class="t">Recta Theil–Sen: ' + nf0.format(recta(ts, anio)) + '</span>';
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

  // ---------- comparación de intervalos ----------
  function marca(forma, x, y, color, padre) {
    if (forma === 'circulo') return el('circle', { cx: x, cy: y, r: 5, fill: color, stroke: 'var(--superficie)', 'stroke-width': 2 }, padre);
    if (forma === 'cuadrado') return el('rect', { x: x - 4.5, y: y - 4.5, width: 9, height: 9, fill: color, stroke: 'var(--superficie)', 'stroke-width': 2 }, padre);
    return el('rect', { x: x - 4.5, y: y - 4.5, width: 9, height: 9, fill: color, stroke: 'var(--superficie)', 'stroke-width': 2, transform: 'rotate(45 ' + x + ' ' + y + ')' }, padre);
  }

  function dibujarComparacion(cont, regiones, selId, meta, alElegir) {
    cont.innerHTML = '';
    var W = Math.max(280, cont.clientWidth || 800), estrecho = W < 560;
    var etq = estrecho ? 112 : 200, m = { l: etq, r: 16, t: 8, b: 34 }, fila = estrecho ? 66 : 60;
    var H = m.t + m.b + fila * regiones.length;
    var vals = [0];
    regiones.forEach(function (r) { METODOS.forEach(function (mt) { var t = r.tendencia[mt.clave]; if (t) vals.push(t.ic_inf, t.ic_sup); }); });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), pad = (hi - lo) * 0.06 || 1;
    lo -= pad; hi += pad;
    var X = function (v) { return m.l + (v - lo) / (hi - lo) * (W - m.l - m.r); };
    var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img',
      'aria-label': 'Pendientes con intervalos del 95 % de tres métodos para los cuatro dominios, en una misma escala con una línea en cero. La tabla siguiente contiene los mismos valores.' }, cont);

    var g = el('g', { class: 'eje' }, svg);
    ticksBonitos(lo, hi, estrecho ? 4 : 7).forEach(function (v) {
      el('line', { x1: X(v), x2: X(v), y1: m.t, y2: H - m.b, class: 'rejilla-h' }, g);
      texto(g, X(v), H - m.b + 16, conSigno(v, nf0), { 'text-anchor': 'middle' });
    });
    texto(g, W - m.r, H - 4, meta.unidades_pendiente, { 'text-anchor': 'end', style: 'fill:var(--texto-3)', 'font-size': 11 });
    if (!estrecho) texto(g, X(0), H - 4, 'sin cambio', { 'text-anchor': 'middle', style: 'fill:var(--texto-3)', 'font-size': 11 });

    regiones.forEach(function (r, i) {
      var y0 = m.t + i * fila, yc = y0 + fila / 2;
      var grupo = el('g', { 'data-region': r.id, style: 'cursor:pointer' }, svg);
      el('rect', { x: 0, y: y0 + 2, width: W, height: fila - 4, rx: 6, fill: r.id === selId ? 'var(--superficie-2)' : 'transparent' }, grupo);
      if (r.id === selId) el('rect', { x: 0, y: y0 + 2, width: 3, height: fila - 4, fill: 'var(--texto)' }, grupo);
      var est = ESTADOS[r.tendencia.estado];
      texto(grupo, 10, yc - 3, r.nombre, { style: 'fill:var(--texto);font-weight:' + (r.id === selId ? 700 : 500), 'font-size': estrecho ? 12 : 13 });
      var tEst = texto(grupo, 10, yc + 13, est.etiqueta, { 'font-size': 11 });
      tEst.setAttribute('class', est.clase);
      tEst.style.fill = 'currentColor';
      if (r.tendencia.estado === 'faltan') texto(grupo, X(0) + 8, yc + 4, 'sin tendencia', { style: 'fill:var(--texto-3)', 'font-size': 12 });
      METODOS.forEach(function (mt, j) {
        var t = r.tendencia[mt.clave]; if (!t) return;
        var y = yc + (j - 1) * 13;
        el('line', { x1: X(t.ic_inf), x2: X(t.ic_sup), y1: y, y2: y, stroke: mt.color, 'stroke-width': 2.5, 'stroke-linecap': 'round', 'stroke-dasharray': mt.guiones }, grupo);
        var forma = marca(mt.forma, X(t.pendiente), y, mt.color, grupo);
        var hit = el('rect', { x: X(t.ic_inf) - 6, y: y - 6, width: X(t.ic_sup) - X(t.ic_inf) + 12, height: 12, fill: 'transparent' }, grupo);
        [hit, forma].forEach(function (n) {
          n.addEventListener('pointermove', function (ev) {
            mostrarTip('<strong>' + escapar(r.nombre) + ' · ' + mt.nombre + '</strong><br>' + conSigno(t.pendiente) + ' ' + meta.unidades_pendiente +
              '<br><span class="t">IC 95 %: ' + conSigno(t.ic_inf) + ' a ' + conSigno(t.ic_sup) + '</span>', ev.clientX, ev.clientY);
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
    var limites = '<div class="limites"><h3>Qué muestra y qué no</h3><ul>' +
      '<li>Muestra una <strong>asociación descriptiva</strong> entre el ONI de la temporada y la lluvia de junio a noviembre. No prueba que el ONI cause la diferencia ni explica la tendencia, y no permite predecir un año concreto.</li>' +
      '<li>Son 24 puntos: un solo año extremo puede mover la correlación, y la relación puede cambiar de un evento a otro.</li>' +
      '<li>La lluvia de Centroamérica también responde al Atlántico, al Caribe y a la variabilidad local; el ONI no mide la lluvia.</li>' +
      '<li>Los dominios se solapan y comparten el mismo ONI, así que sus correlaciones no son resultados independientes.</li>' +
      '<li>La etiqueta El Niño / La Niña es descriptiva de la media de la temporada (±0,5), no el criterio oficial de NOAA.</li></ul></div>';
    if (!oni) {
      cont.innerHTML = '<p class="sub">El archivo de datos no incluye el bloque ONI, así que este contexto no se muestra.</p>' + limites;
      return;
    }
    var lluvia = oni.lluvia[region.id], corr = oni.correlacion[region.id];
    var frase = corr && isFinite(corr.r)
      ? 'En ' + escapar(region.nombre) + ', la correlación entre el ONI de ' + escapar(oni.temporada) + ' y la lluvia de esos meses es r = ' + conSigno(corr.r, nf2) + ' (n = ' + corr.n + ' años). ' +
        (corr.r <= -0.3 ? 'Los años con ONI alto (El Niño) tienden a ser más secos en esos meses.' : corr.r >= 0.3 ? 'Los años con ONI alto tienden a ser más lluviosos en esos meses.' : 'La asociación es débil.')
      : 'No hay correlación disponible para ' + escapar(region.nombre) + '.';
    var intro = document.createElement('div');
    intro.innerHTML = '<p class="sub">Fuente: ' + (oni.fuente_url ? '<a href="' + escapar(oni.fuente_url) + '" rel="noopener">' + escapar(oni.fuente) + '</a>' : escapar(oni.fuente)) +
      '. Temporada: ' + escapar(oni.temporada) + (oni.agregacion ? ' (' + escapar(oni.agregacion) + ')' : '') + '.</p><p>' + frase + '</p>' +
      '<p class="aviso-oni"><strong>Advertencia:</strong> ' + escapar(oni.advertencia) + '</p>';
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

    var W = Math.max(260, c1.clientWidth || 400), H = 200, m = { l: 36, r: 8, t: 22, b: 26 };
    var a0 = Math.min.apply(null, oni.anios), a1 = Math.max.apply(null, oni.anios);
    var vmax = Math.max(2, Math.max.apply(null, oni.valores.map(Math.abs)));
    var bw = (W - m.l - m.r) / (a1 - a0 + 1);
    var X = function (a) { return m.l + (a - a0) * bw; }, Y = function (v) { return m.t + (vmax - v) / (2 * vmax) * (H - m.t - m.b); };
    var s1 = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'ONI medio de ' + oni.temporada + ', ' + a0 + ' a ' + a1 + '. Barras hacia arriba: El Niño; hacia abajo: La Niña.' }, c1);
    texto(s1, m.l, 12, 'ONI medio de ' + oni.temporada + ' (°C)', { style: 'fill:var(--texto-3)', 'font-size': 11 });
    [-1, -0.5, 0, 0.5, 1].forEach(function (v) {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), class: v === 0 ? 'cero' : 'rejilla-h' }, s1);
      if (v !== 0.5 && v !== -0.5) texto(s1, m.l - 4, Y(v) + 4, conSigno(v, nf0), { 'text-anchor': 'end' });
    });
    oni.anios.forEach(function (anio, i) {
      var v = oni.valores[i], cat = oni.categorias[i] || (v >= 0.5 ? 'el_nino' : v <= -0.5 ? 'la_nina' : 'neutral');
      var color = cat === 'el_nino' ? 'var(--oni-nino)' : cat === 'la_nina' ? 'var(--oni-nina)' : 'var(--texto-3)';
      var y = Math.min(Y(0), Y(v)), h = Math.max(1, Math.abs(Y(v) - Y(0)));
      var b = el('rect', { x: X(anio) + 1, y: y, width: Math.max(1, bw - 2), height: h, fill: color, rx: 2 }, s1);
      b.addEventListener('pointermove', function (ev) {
        mostrarTip('<strong>' + anio + '</strong><br>ONI ' + conSigno(v, nf2) + '<br><span class="t">' + (cat === 'el_nino' ? 'El Niño (descriptivo)' : cat === 'la_nina' ? 'La Niña (descriptivo)' : 'Neutral') + '</span>', ev.clientX, ev.clientY);
      });
      b.addEventListener('pointerleave', ocultarTip);
    });
    [a0, a0 + 8, a0 + 16, a1].forEach(function (a) { texto(s1, X(a) + bw / 2, H - 8, String(a), { 'text-anchor': 'middle' }); });

    var W2 = Math.max(260, c2.clientWidth || 400), m2 = { l: 52, r: 10, t: 22, b: 30 };
    var s2 = el('svg', { width: W2, height: H, viewBox: '0 0 ' + W2 + ' ' + H, role: 'img', 'aria-label': 'Dispersión del ONI frente a la lluvia de ' + oni.temporada + ' en ' + region.nombre + '.' }, c2);
    texto(s2, m2.l, 12, 'Lluvia de ' + oni.temporada + ' (mm) frente a ONI', { style: 'fill:var(--texto-3)', 'font-size': 11 });
    if (!Array.isArray(lluvia) || !lluvia.length) { texto(s2, W2 / 2, H / 2, 'Sin datos para este dominio', { 'text-anchor': 'middle' }); return; }
    var pares = oni.anios.map(function (a, i) { return { anio: a, oni: oni.valores[i], mm: lluvia[i] }; }).filter(function (p) { return isFinite(p.oni) && isFinite(p.mm); });
    var ymin = Math.min.apply(null, pares.map(function (p) { return p.mm; })), ymax = Math.max.apply(null, pares.map(function (p) { return p.mm; }));
    var padY = (ymax - ymin) * 0.1 || 50; ymin -= padY; ymax += padY;
    var X2 = function (v) { return m2.l + (v + vmax) / (2 * vmax) * (W2 - m2.l - m2.r); };
    var Y2 = function (v) { return m2.t + (ymax - v) / (ymax - ymin) * (H - m2.t - m2.b); };
    ticksBonitos(ymin, ymax, 4).forEach(function (v) {
      el('line', { x1: m2.l, x2: W2 - m2.r, y1: Y2(v), y2: Y2(v), class: 'rejilla-h' }, s2);
      texto(s2, m2.l - 4, Y2(v) + 4, nf0.format(v), { 'text-anchor': 'end' });
    });
    [-1, 0, 1].forEach(function (v) {
      el('line', { x1: X2(v), x2: X2(v), y1: m2.t, y2: H - m2.b, class: v === 0 ? 'cero' : 'rejilla-h' }, s2);
      texto(s2, X2(v), H - 12, conSigno(v, nf0), { 'text-anchor': 'middle' });
    });
    texto(s2, W2 - m2.r, H - 1, 'ONI', { 'text-anchor': 'end', style: 'fill:var(--texto-3)', 'font-size': 11 });
    pares.forEach(function (q) {
      var p = el('circle', { cx: X2(q.oni), cy: Y2(q.mm), r: 5, fill: 'var(--observado)', 'fill-opacity': 0.75, stroke: 'var(--superficie)', 'stroke-width': 1.5 }, s2);
      p.addEventListener('pointermove', function (ev) {
        mostrarTip('<strong>' + q.anio + '</strong><br>ONI ' + conSigno(q.oni, nf2) + '<br>Lluvia ' + nf0.format(q.mm) + ' mm', ev.clientX, ev.clientY);
      });
      p.addEventListener('pointerleave', ocultarTip);
    });
  }

  window.SofGraficas = {
    ESTADOS: ESTADOS, METODOS: METODOS, dibujarMapa: dibujarMapa, dibujarEscalaMapa: dibujarEscalaMapa, dibujarSerie: dibujarSerie,
    dibujarComparacion: dibujarComparacion, dibujarOni: dibujarOni, ocultarTip: ocultarTip, recta: recta,
    formato: { nf0: nf0, nf1: nf1, nf2: nf2, conSigno: conSigno }, escapar: escapar
  };
})();
