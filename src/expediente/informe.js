/*
 * Informe PDF del expediente territorial (jsPDF, texto seleccionable, Helvetica WinAnsi con tildes).
 *
 * Dos plantillas («resumen» y «completo») leen el MISMO objeto de resultados de ETDAnalisis: el informe no
 * recalcula ninguna cifra. La organización documental sigue la lógica de un informe técnico de proyecto
 * (identificación, representación del espacio, parámetros de cálculo, resultados, planos, tablas y anexos),
 * adaptada al clima, sin magnitudes luminotécnicas ni certificaciones.
 *
 * Mapas: composición cartográfica vectorial propia (no captura de la interfaz), proyección equirrectangular
 * centrada en la latitud media del mapa, con escala gráfica exacta en esa latitud, norte, retícula, leyenda y
 * atribución.
 */
(function (raiz, fabrica) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) module.exports = fabrica(require('./i18n.js'), require('./geo.js'), require('./fuentes.js'));
  else raiz.ETDInforme = fabrica(raiz.ETDi18n, raiz.ETDGeo, raiz.ETDFuentes);
})(typeof window !== 'undefined' ? window : this, function (I18n, Geo, Fuentes) {
  'use strict';

  var A4 = { w: 210, h: 297 }, M = { l: 18, r: 18, t: 20, b: 20 }, ANCHO = A4.w - M.l - M.r;
  var COL = { texto: [28, 33, 40], suave: [95, 105, 115], linea: [190, 196, 204], acento: [11, 61, 145], area: [200, 30, 45], fondo: [245, 247, 250], tierra: [236, 233, 224], agua: [214, 230, 242] };
  var SECCIONES = ['B', 'C', 'D', 'E', 'F', 'G', 'H'];
  var RESUMEN = ['B', 'C', 'F', 'G', 'H'];

  // Caracteres fuera de WinAnsi sustituidos por equivalentes legibles (las tildes y la ñ se conservan).
  var SUST = { '−': '-', '≈': '~', 'α': 'alfa', '≥': '>=', '≤': '<=', ' ': ' ', ' ': ' ', ' ': ' ', '→': '->', '✓': 'v' };
  function limpio(s) { return String(s === null || s === undefined ? '' : s).replace(/[−≈α≥≤   →✓]/g, function (c) { return SUST[c]; }); }

  function crear(res, op) {
    var idioma = op.idioma || res.consulta.idioma, t = function (k, v) { return I18n.t(k, idioma, v); };
    var n = function (v, d) { return I18n.num(v, d, idioma); };
    var pf = function (p) { return p === null || p === undefined ? '= ' + I18n.t('na', idioma) : p < 0.0001 ? '< ' + I18n.num(0.0001, 4, idioma) : '= ' + I18n.num(p, 4, idioma); };
    var JsPDF = op.jsPDF || (typeof window !== 'undefined' && window.jspdf && window.jspdf.jsPDF);
    if (!JsPDF) throw new Error('jsPDF no está cargado');
    var doc = new JsPDF({ unit: 'mm', format: 'a4', compress: true, putOnlyUsedFonts: true });
    var plantilla = op.plantilla === 'resumen' ? 'resumen' : 'completo';
    var secciones = (op.secciones && op.secciones.length ? op.secciones : (plantilla === 'resumen' ? RESUMEN : SECCIONES)).filter(function (s) { return SECCIONES.indexOf(s) >= 0; });
    var v = res.variable, u = v.unidad, dec = v.decimales, nivelPct = Math.round(res.tendencia.nivel * 100);
    var idInforme = 'ETD-' + res.resultado_id.slice(2, 14).toUpperCase();
    var titulo = res.consulta.titulo || ((idioma === 'en' ? v.nombre_en : v.nombre) + ' · ' + (res.area.nombre || t('area.' + res.area.tipo)));
    var y = M.t, numSeccion = 0, figura = 0, tablaN = 0;
    doc.setProperties({ title: limpio(titulo), subject: limpio(t('inf.subtitulo')), author: limpio(op.autor || 'Earth System Trend Detective'), keywords: res.resultado_id + ' ' + res.consulta_id, creator: 'Earth System Trend Detective ' + res.version_codigo });
    doc.setLanguage && doc.setLanguage(idioma === 'en' ? 'en-US' : 'es-ES');

    // ------------------------------------------------------------------ primitivas de maquetación
    function color(c, tipo) { if (tipo === 'f') doc.setFillColor(c[0], c[1], c[2]); else if (tipo === 'd') doc.setDrawColor(c[0], c[1], c[2]); else doc.setTextColor(c[0], c[1], c[2]); }
    function fuente(tam, estilo) { doc.setFont('helvetica', estilo || 'normal'); doc.setFontSize(tam); }
    function nuevaPagina() { doc.addPage(); y = M.t; }
    function asegurar(h) { if (y + h > A4.h - M.b) { nuevaPagina(); return true; } return false; }
    function parrafo(txt, op2) {
      op2 = op2 || {};
      fuente(op2.tam || 9.5, op2.estilo); color(op2.color || COL.texto);
      var ancho = op2.ancho || ANCHO, x = op2.x || M.l, lh = (op2.tam || 9.5) * 0.43;
      var lineas = doc.splitTextToSize(limpio(txt), ancho);
      lineas.forEach(function (l) { asegurar(lh); doc.text(l, x, y + lh * 0.8); y += lh; });
      y += op2.despues === undefined ? 1.8 : op2.despues;
    }
    function titular(txt, nivel) {
      var tam = nivel === 1 ? 14 : 11;
      asegurar(nivel === 1 ? 22 : 14);
      if (nivel === 1) { y += 2; color(COL.acento, 'd'); doc.setLineWidth(0.6); doc.line(M.l, y, M.l + ANCHO, y); y += 2; }
      fuente(tam, 'bold'); color(nivel === 1 ? COL.acento : COL.texto);
      doc.text(limpio(txt), M.l, y + tam * 0.36); y += tam * 0.5 + 2.5;
    }
    function seccion(letra) { numSeccion++; titular(letra + '. ' + t('sec.' + letra), 1); doc.outline && doc.outline.add(null, letra + '. ' + limpio(t('sec.' + letra)), { pageNumber: doc.getNumberOfPages() }); }
    function pie(txt) { parrafo(txt, { tam: 7.8, color: COL.suave, despues: 3 }); }

    // Tabla con cabecera repetida y filas que nunca se parten entre páginas.
    function tabla(cab, filas, anchos, op3) {
      op3 = op3 || {};
      var tam = op3.tam || 8.2, lh = tam * 0.42, pad = 1.4;
      var total = anchos.reduce(function (s, a) { return s + a; }, 0), esc = ANCHO / total;
      anchos = anchos.map(function (a) { return a * esc; });
      function alto(fila, estilo) {
        fuente(tam, estilo);
        return Math.max.apply(null, fila.map(function (c, i) { return doc.splitTextToSize(limpio(c), anchos[i] - 2 * pad).length; })) * lh + 2 * pad;
      }
      if (op3.titulo) {
        tablaN++;
        asegurar(6 + (cab ? alto(cab, 'bold') : 0) + (filas[0] ? alto(filas[0], 'normal') : 0));
        parrafo((idioma === 'en' ? 'Table ' : 'Tabla ') + tablaN + '. ' + op3.titulo, { tam: 8.6, estilo: 'bold', despues: 1 });
      }
      function dibujarFila(fila, estilo, fondo) {
        var h = alto(fila, estilo), x = M.l;
        if (fondo) { color(fondo, 'f'); doc.rect(M.l, y, ANCHO, h, 'F'); }
        fuente(tam, estilo); color(COL.texto);
        fila.forEach(function (c, i) {
          var ls = doc.splitTextToSize(limpio(c), anchos[i] - 2 * pad);
          ls.forEach(function (l, k) { doc.text(l, x + pad, y + pad + lh * (k + 0.8)); });
          x += anchos[i];
        });
        color(COL.linea, 'd'); doc.setLineWidth(0.15); doc.line(M.l, y + h, M.l + ANCHO, y + h);
        y += h;
      }
      if (cab) { asegurar(alto(cab, 'bold') + alto(filas[0] || cab, 'normal')); dibujarFila(cab, 'bold', [226, 232, 240]); }
      filas.forEach(function (f, i) {
        var h = alto(f, 'normal');
        if (asegurar(h) && cab) dibujarFila(cab, 'bold', [226, 232, 240]);
        dibujarFila(f, 'normal', i % 2 ? COL.fondo : null);
      });
      y += 3;
    }
    function leyendaFigura(txt) { figura++; parrafo((idioma === 'en' ? 'Figure ' : 'Figura ') + figura + '. ' + txt, { tam: 8, estilo: 'bold', despues: 0.8 }); }

    // ------------------------------------------------------------------ cartografía
    function proyector(ext, rect) {
      // ext: [oeste, sur, este, norte] con este >= oeste (desenvuelto)
      var lat0 = (ext[1] + ext[3]) / 2, k = Math.cos(lat0 * Math.PI / 180);
      var w = (ext[2] - ext[0]) * k, h = ext[3] - ext[1];
      var s = Math.min(rect.w / w, rect.h / h), ox = rect.x + (rect.w - w * s) / 2, oy = rect.y + (rect.h - h * s) / 2;
      var lonC = (ext[0] + ext[2]) / 2;
      return {
        lat0: lat0, s: s, k: k, ext: ext,
        p: function (lon, lat) { var dl = lon - lonC; dl = dl > 180 ? dl - 360 : dl < -180 ? dl + 360 : dl; return [ox + (dl + lonC - ext[0]) * k * s, oy + (ext[3] - lat) * s]; },
        mmPorKm: function () { return s / 111.32 / 1; } // 1° de latitud ≈ 111,32 km; en x la escala es la misma a lat0
      };
    }
    function anillo(P, coords, estilo) {
      if (coords.length < 2) return;
      var pts = coords.map(function (c) { return P.p(c[0], c[1]); }), d = [];
      for (var i = 1; i < pts.length; i++) d.push([pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]]);
      doc.lines(d, pts[0][0], pts[0][1], [1, 1], estilo, true);
    }
    function recortarA(rect) { doc.saveGraphicsState(); doc.rect(rect.x, rect.y, rect.w, rect.h, null); doc.clip(); doc.discardPath(); }
    function paises(P, rect, mundo, etiquetas) {
      if (!mundo) return;
      var e = P.ext;
      color(COL.tierra, 'f'); color([150, 150, 150], 'd'); doc.setLineWidth(0.18);
      mundo.features.forEach(function (f) {
        if (!f.geometry || (f.properties && f.properties.tipo && f.properties.tipo !== 'pais')) return;
        Geo.poligonos(f.geometry).forEach(function (pol) {
          var ext = pol[0], lo = Infinity, hi = -Infinity, s = Infinity, nn = -Infinity;
          ext.forEach(function (c) { lo = Math.min(lo, c[0]); hi = Math.max(hi, c[0]); s = Math.min(s, c[1]); nn = Math.max(nn, c[1]); });
          if (hi < e[0] - 5 || lo > e[2] + 5 || nn < e[1] - 5 || s > e[3] + 5) return;
          anillo(P, ext, 'FD');
        });
      });
      if (etiquetas) {
        fuente(6.5, 'italic'); color([90, 90, 90]);
        mundo.features.forEach(function (f) {
          var p = f.properties || {};
          if (p.tipo !== 'pais' || p.lx === undefined) return;
          if (p.lx < e[0] || p.lx > e[2] || p.ly < e[1] || p.ly > e[3]) return;
          var q = P.p(p.lx, p.ly);
          if (q[0] > rect.x + 8 && q[0] < rect.x + rect.w - 8 && q[1] > rect.y + 4 && q[1] < rect.y + rect.h - 4) doc.text(limpio(idioma === 'en' ? p.nombre_en || p.nombre : p.nombre), q[0], q[1], { align: 'center' });
        });
      }
    }
    function dibujarArea(P, grosor) {
      var g = res.area.geometria;
      color(COL.area, 'd'); doc.setLineWidth(grosor || 0.6);
      if (g.type === 'Point') {
        var q = P.p(g.coordinates[0], g.coordinates[1]);
        color(COL.area, 'f'); doc.circle(q[0], q[1], 1.2, 'FD');
        doc.setLineWidth(0.3); doc.circle(q[0], q[1], 2.6, 'S');
        return;
      }
      Geo.poligonos(g).forEach(function (pol) { Geo.desenvolverPoligono(pol).forEach(function (a) { anillo(P, a, 'S'); }); });
    }
    function reticula(P, rect, paso) {
      var e = P.ext;
      color([120, 130, 140], 'd'); doc.setLineWidth(0.08); fuente(6, 'normal'); color(COL.suave);
      doc.setLineDashPattern([0.6, 0.8], 0);
      for (var lon = Math.ceil(e[0] / paso) * paso; lon <= e[2] + 1e-9; lon += paso) {
        var a = P.p(lon, e[3]), b = P.p(lon, e[1]);
        if (a[0] < rect.x || a[0] > rect.x + rect.w) continue;
        doc.line(a[0], Math.max(a[1], rect.y), b[0], Math.min(b[1], rect.y + rect.h));
        var L = Geo.envolverLon(lon);
        doc.text(n(Math.abs(L), paso < 1 ? 2 : 0) + '°' + (L < 0 ? (idioma === 'en' ? 'W' : 'O') : 'E'), a[0], rect.y + rect.h + 3, { align: 'center' });
      }
      for (var lat = Math.ceil(e[1] / paso) * paso; lat <= e[3] + 1e-9; lat += paso) {
        var c = P.p(e[0], lat), d = P.p(e[2], lat);
        if (c[1] < rect.y || c[1] > rect.y + rect.h) continue;
        doc.line(Math.max(c[0], rect.x), c[1], Math.min(d[0], rect.x + rect.w), d[1]);
        doc.text(n(Math.abs(lat), paso < 1 ? 2 : 0) + '°' + (lat < 0 ? 'S' : 'N'), rect.x - 1, c[1] + 1, { align: 'right' });
      }
      doc.setLineDashPattern([], 0);
    }
    function pasoReticula(span) { var p = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20]; for (var i = 0; i < p.length; i++) if (span / p[i] <= 6) return p[i]; return 30; }
    function norte(x, yy) {
      color(COL.texto, 'f'); color(COL.texto, 'd'); doc.setLineWidth(0.2);
      doc.triangle(x, yy, x - 2, yy + 5.5, x, yy + 4.2, 'FD'); color([255, 255, 255], 'f'); doc.triangle(x, yy, x + 2, yy + 5.5, x, yy + 4.2, 'FD');
      fuente(7, 'bold'); color(COL.texto); doc.text(t('c.norte'), x, yy - 0.8, { align: 'center' });
    }
    function escala(P, x, yy, maxMm) {
      // longitud geodésica real de un tramo este-oeste a lat0 (GeographicLib), no aproximación de Mercator
      var kmPorMm = Geo.distanciaKm(0, P.lat0, 1, P.lat0) / (P.k * P.s);
      var bruto = maxMm * kmPorMm, pot = Math.pow(10, Math.floor(Math.log10(bruto))), opciones = [1, 2, 5, 10];
      var km = pot; opciones.forEach(function (o) { if (o * pot <= bruto) km = o * pot; });
      var mm = km / kmPorMm;
      color(COL.texto, 'd'); doc.setLineWidth(0.3);
      color(COL.texto, 'f'); doc.rect(x, yy, mm / 2, 1.2, 'FD'); color([255, 255, 255], 'f'); doc.rect(x + mm / 2, yy, mm / 2, 1.2, 'FD');
      fuente(6.5, 'normal'); color(COL.texto);
      doc.text('0', x, yy + 4, { align: 'center' }); doc.text(n(km, km < 10 ? 1 : 0) + ' km', x + mm, yy + 4, { align: 'center' });
      fuente(5.8, 'normal'); color(COL.suave); doc.text(limpio(t('c.escala', { lat: n(P.lat0, 1) })), x, yy + 7);
    }
    function rampa(valor, min, max, divergente, invertir) {
      if (valor === null || valor === undefined) return null;
      var a = [[33, 102, 172], [247, 247, 247], [178, 24, 43]], sec = [[239, 243, 255], [107, 174, 214], [8, 69, 148]];
      var x, pal = divergente ? a : sec;
      if (divergente) { var m = Math.max(Math.abs(min), Math.abs(max)) || 1; x = (valor / m + 1) / 2; } else x = max > min ? (valor - min) / (max - min) : 0.5;
      if (invertir) x = 1 - x;
      x = Math.max(0, Math.min(1, x));
      var i = x < 0.5 ? 0 : 1, f = x < 0.5 ? x / 0.5 : (x - 0.5) / 0.5;
      return [0, 1, 2].map(function (k) { return Math.round(pal[i][k] + (pal[i + 1][k] - pal[i][k]) * f); });
    }
    function valorCapa(c, capa) {
      if (capa === 'tendencia_celda') return c.tendencia && c.tendencia.sen_decada !== undefined ? c.tendencia.sen_decada : null;
      if (capa === 'peso_celda') return c.peso;
      return c.anomalia_anio_visible;
    }
    function extDetalle() {
      var e = res.area.extension.slice(), w = e[0], ee = e[2] < e[0] ? e[2] + 360 : e[2];
      res.celdas.forEach(function (c) { var b = c.caja, b0 = b[0], b2 = b[2]; while (b0 < w - 180) { b0 += 360; b2 += 360; } while (b0 > w + 180) { b0 -= 360; b2 -= 360; } w = Math.min(w, b0); ee = Math.max(ee, b2); e[1] = Math.min(e[1], b[1]); e[3] = Math.max(e[3], b[3]); });
      var pw = (ee - w) * 0.12 + 0.05, ph = (e[3] - e[1]) * 0.12 + 0.05;
      return [w - pw, e[1] - ph, ee + pw, e[3] + ph];
    }
    // Mapa de detalle con celdas coloreadas por la capa elegida.
    function mapaDetalle(rect, capa) {
      var e = extDetalle(), P = proyector(e, rect);
      color(COL.agua, 'f'); doc.rect(rect.x, rect.y, rect.w, rect.h, 'F');
      recortarA(rect);
      paises(P, rect, op.mundo, false);
      var vals = res.celdas.map(function (c) { return valorCapa(c, capa); }).filter(function (x) { return x !== null && x !== undefined; });
      var mn = vals.length ? Math.min.apply(null, vals) : 0, mx = vals.length ? Math.max.apply(null, vals) : 1;
      var divergente = capa !== 'peso_celda', invertir = v.id === 'PRECTOTCORR' && capa !== 'peso_celda';
      res.celdas.forEach(function (c) {
        var b = c.caja, val = valorCapa(c, capa), col = c.estado === 'ok' ? rampa(val, mn, mx, divergente, invertir) : null;
        var poly = [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]];
        color([60, 60, 60], 'd'); doc.setLineWidth(0.15);
        if (col) { color(col, 'f'); doc.setGState && doc.setGState(new doc.GState({ opacity: 0.8 })); anillo(P, poly, 'FD'); doc.setGState && doc.setGState(new doc.GState({ opacity: 1 })); }
        else {
          color([200, 200, 200], 'f'); anillo(P, poly, 'FD');
          var a = P.p(b[0], b[3]), z = P.p(b[2], b[1]); color([120, 120, 120], 'd'); doc.setLineWidth(0.1);
          for (var k = 0; k < 8; k++) { var f = k / 8; doc.line(a[0] + (z[0] - a[0]) * f, z[1], a[0], z[1] - (z[1] - a[1]) * (1 - f)); }
        }
      });
      dibujarArea(P, 0.7);
      doc.restoreGraphicsState();
      reticula(P, rect, pasoReticula(Math.max(e[2] - e[0], e[3] - e[1])));
      color(COL.texto, 'd'); doc.setLineWidth(0.3); doc.rect(rect.x, rect.y, rect.w, rect.h, 'S');
      norte(rect.x + rect.w - 6, rect.y + 4);
      color([255, 255, 255], 'f'); doc.rect(rect.x + 2, rect.y + rect.h - 11, 46, 9.5, 'F');
      escala(P, rect.x + 4, rect.y + rect.h - 9.5, 30);
      return { min: mn, max: mx, divergente: divergente, invertir: invertir, P: P };
    }
    function leyendaCapa(x, yy, info, capa, ancho) {
      var et = capa === 'tendencia_celda' ? u + '/' + (idioma === 'en' ? 'decade' : 'década') : capa === 'peso_celda' ? (idioma === 'en' ? 'weight (0–1)' : 'peso (0–1)') : u;
      fuente(7, 'bold'); color(COL.texto); doc.text(limpio(t('c.leyenda')), x, yy); yy += 2;
      var nn = 24, w = ancho / nn;
      for (var i = 0; i < nn; i++) {
        var val = info.divergente ? (-1 + 2 * (i + 0.5) / nn) * Math.max(Math.abs(info.min), Math.abs(info.max)) : info.min + (info.max - info.min) * (i + 0.5) / nn;
        var c = rampa(val, info.min, info.max, info.divergente, info.invertir) || [200, 200, 200];
        color(c, 'f'); doc.rect(x + i * w, yy, w + 0.05, 3, 'F');
      }
      color(COL.texto, 'd'); doc.setLineWidth(0.15); doc.rect(x, yy, ancho, 3, 'S');
      fuente(6.5, 'normal'); color(COL.texto);
      var m = info.divergente ? Math.max(Math.abs(info.min), Math.abs(info.max)) : null;
      doc.text(n(info.divergente ? -m : info.min, 2), x, yy + 6); doc.text(n(info.divergente ? m : info.max, 2), x + ancho, yy + 6, { align: 'right' });
      doc.text(limpio(et), x + ancho / 2, yy + 6, { align: 'center' });
      yy += 9;
      color(COL.area, 'd'); doc.setLineWidth(0.7); doc.line(x, yy, x + 6, yy); fuente(6.8, 'normal'); color(COL.texto); doc.text(limpio(t('c.area')), x + 8, yy + 1);
      yy += 4; color([60, 60, 60], 'd'); doc.setLineWidth(0.15); doc.rect(x, yy - 1.5, 6, 3, 'S'); doc.text(limpio(t('c.celdas')), x + 8, yy + 1);
      yy += 4; color([200, 200, 200], 'f'); doc.rect(x, yy - 1.5, 6, 3, 'FD'); doc.text(limpio(t('c.sin_cobertura')), x + 8, yy + 1);
      return yy + 4;
    }
    function nombreCapa(capa) { return t('capa.' + capa); }
    function anioCapa(capa) { return capa === 'anomalia_anual' ? String(res.consulta.vista.anio_visible || res.consulta.periodo.fin) + ' · ' + t('res.referencia', { ini: res.referencia.inicio, fin: res.referencia.fin }) : res.consulta.periodo.inicio + '–' + res.consulta.periodo.fin; }
    function bloqueMapaDetalle(capa, alto) {
      capa = capa || res.consulta.vista.capa || 'anomalia_anual';
      if (capa === 'anomalia_anual' && !res.referencia.suficiente) capa = 'peso_celda';
      asegurar(alto + 18);
      var rect = { x: M.l + 7, y: y, w: ANCHO - 62, h: alto }, info = mapaDetalle(rect, capa);
      var yy = leyendaCapa(M.l + ANCHO - 48, y + 4, info, capa, 46);
      fuente(6.3, 'normal'); color(COL.suave);
      doc.text(doc.splitTextToSize(limpio(t('c.capa', { capa: nombreCapa(capa), anio: anioCapa(capa) })), 48), M.l + ANCHO - 48, yy + 2);
      y += alto + 6;
      pie(t('c.proyeccion', { lat: n(info.P.lat0, 2) }) + ' ' + t('c.atribucion', { limites: limitesTexto() }));
    }
    function limitesTexto() { return res.area.procedencia && res.area.procedencia.tipo === 'ineter' ? 'INETER (WFS público), ' + (res.area.procedencia.version || '') : limpio(t('proc.' + (res.area.procedencia && res.area.procedencia.tipo || 'dibujo'))); }
    function mapaContexto(rect) {
      var c = res.area.centro, e = res.area.extension, ee = e[2] < e[0] ? e[2] + 360 : e[2];
      var semi = Math.max(4, (ee - e[0]) * 1.6, (e[3] - e[1]) * 1.6);
      var ext = [c.lon - semi * 1.3, c.lat - semi, c.lon + semi * 1.3, c.lat + semi], P = proyector(ext, rect);
      color(COL.agua, 'f'); doc.rect(rect.x, rect.y, rect.w, rect.h, 'F');
      recortarA(rect); paises(P, rect, op.mundo, true);
      var d = extDetalle(), a = P.p(d[0], d[3]), b = P.p(d[2], d[1]);
      color(COL.acento, 'd'); doc.setLineWidth(0.35); doc.rect(a[0], a[1], Math.max(1, b[0] - a[0]), Math.max(1, b[1] - a[1]), 'S');
      dibujarArea(P, 0.5);
      doc.restoreGraphicsState();
      reticula(P, rect, pasoReticula(ext[2] - ext[0]));
      color(COL.texto, 'd'); doc.setLineWidth(0.3); doc.rect(rect.x, rect.y, rect.w, rect.h, 'S');
      norte(rect.x + rect.w - 6, rect.y + 4);
      color([255, 255, 255], 'f'); doc.rect(rect.x + 2, rect.y + rect.h - 11, 46, 9.5, 'F');
      escala(P, rect.x + 4, rect.y + rect.h - 9.5, 30);
      return P;
    }

    // ------------------------------------------------------------------ gráficas
    function ejes(rect, xmin, xmax, ymin, ymax, ytxt) {
      var X = function (x) { return rect.x + (x - xmin) / (xmax - xmin || 1) * rect.w; }, Y = function (v2) { return rect.y + rect.h - (v2 - ymin) / (ymax - ymin || 1) * rect.h; };
      color(COL.linea, 'd'); doc.setLineWidth(0.1); fuente(6.5, 'normal'); color(COL.suave);
      var paso = niceStep((ymax - ymin) / 5);
      for (var yv = Math.ceil(ymin / paso) * paso; yv <= ymax + 1e-9; yv += paso) { doc.line(rect.x, Y(yv), rect.x + rect.w, Y(yv)); doc.text(n(yv, paso < 1 ? (paso < 0.1 ? 2 : 1) : 0), rect.x - 1.2, Y(yv) + 1, { align: 'right' }); }
      color(COL.texto, 'd'); doc.setLineWidth(0.25); doc.line(rect.x, rect.y + rect.h, rect.x + rect.w, rect.y + rect.h); doc.line(rect.x, rect.y, rect.x, rect.y + rect.h);
      fuente(7, 'normal'); color(COL.texto);
      var et = limpio(ytxt), wt = Math.min(doc.getTextWidth(et), rect.h);
      doc.text(et, rect.x - 10, rect.y + rect.h / 2 + wt / 2, { angle: 90 });
      return { X: X, Y: Y };
    }
    function niceStep(x) { var p = Math.pow(10, Math.floor(Math.log10(x || 1))), r2 = x / p; return (r2 <= 1 ? 1 : r2 <= 2 ? 2 : r2 <= 5 ? 5 : 10) * p; }
    function etiquetasAnios(rect, X, a0, a1) {
      fuente(6.5, 'normal'); color(COL.suave);
      var paso = a1 - a0 > 40 ? 10 : a1 - a0 > 15 ? 5 : 2;
      for (var a = Math.ceil(a0 / paso) * paso; a <= a1; a += paso) doc.text(String(a), X(a), rect.y + rect.h + 3.5, { align: 'center' });
      fuente(7, 'normal'); color(COL.texto); doc.text(idioma === 'en' ? 'Year' : 'Año', rect.x + rect.w / 2, rect.y + rect.h + 7.5, { align: 'center' });
    }
    function grafSerie() {
      var s = res.serie.filter(function (p) { return p.en_periodo; }), val = s.filter(function (p) { return p.valor !== null; });
      if (!val.length) return;
      var a0 = res.consulta.periodo.inicio, a1 = res.consulta.periodo.fin;
      var ys = val.map(function (p) { return p.valor; }), mn = Math.min.apply(null, ys), mx = Math.max.apply(null, ys), pad = (mx - mn) * 0.12 || 1;
      asegurar(78); leyendaFigura(t('f.serie') + ' · ' + a0 + '–' + a1);
      var rect = { x: M.l + 16, y: y + 2, w: ANCHO - 20, h: 58 }, E = ejes(rect, a0 - 0.5, a1 + 0.5, mn - pad, mx + pad, (idioma === 'en' ? v.nombre_en : v.nombre).split('(')[0].trim() + ' (' + u + ')');
      color(COL.acento, 'd'); doc.setLineWidth(0.25);
      for (var i = 1; i < s.length; i++) if (s[i].valor !== null && s[i - 1].valor !== null) doc.line(E.X(s[i - 1].anio), E.Y(s[i - 1].valor), E.X(s[i].anio), E.Y(s[i].valor));
      color(COL.acento, 'f'); val.forEach(function (p) { doc.circle(E.X(p.anio), E.Y(p.valor), 0.65, 'F'); });
      color(COL.area, 'd'); fuente(6, 'bold'); color(COL.area);
      s.filter(function (p) { return p.valor === null; }).forEach(function (p) { doc.text('x', E.X(p.anio), rect.y + rect.h - 1, { align: 'center' }); });
      var T = res.tendencia;
      function recta(tt, dash, col) { if (!tt) return; color(col, 'd'); doc.setLineWidth(0.5); doc.setLineDashPattern(dash, 0); var f = function (x) { return tt.intercepto + tt.pendiente_decada / 10 * x; }; doc.line(E.X(a0), E.Y(f(a0)), E.X(a1), E.Y(f(a1))); doc.setLineDashPattern([], 0); }
      recta(T.mco, [1.6, 1], [90, 90, 90]); recta(T.sen, [], [214, 96, 77]);
      etiquetasAnios(rect, E.X, a0, a1);
      y = rect.y + rect.h + 10;
      pie(t('f.nota_serie') + (res.calidad.anios_excluidos.length ? ' x: ' + t('aviso.anios_excluidos', { anios: res.calidad.anios_excluidos.join(', ') }) : ''));
    }
    function grafAnomalias() {
      if (!res.referencia.suficiente) return;
      var s = res.serie.filter(function (p) { return p.en_periodo && p.anomalia !== null; });
      if (!s.length) return;
      var a0 = res.consulta.periodo.inicio, a1 = res.consulta.periodo.fin, ys = s.map(function (p) { return p.anomalia; });
      var m = Math.max(Math.abs(Math.min.apply(null, ys)), Math.abs(Math.max.apply(null, ys))) * 1.15 || 1;
      asegurar(66); leyendaFigura(t('f.anomalias', { ini: res.referencia.inicio, fin: res.referencia.fin }) + ' · ' + a0 + '–' + a1);
      var rect = { x: M.l + 16, y: y + 2, w: ANCHO - 20, h: 46 }, E = ejes(rect, a0 - 0.5, a1 + 0.5, -m, m, t('res.anomalia') + ' (' + u + ')');
      var bw = Math.max(0.4, rect.w / (a1 - a0 + 1) * 0.7), inv = v.id === 'PRECTOTCORR';
      s.forEach(function (p) {
        var pos = p.anomalia >= 0; color((pos !== inv) ? [178, 24, 43] : [33, 102, 172], 'f');
        var y1 = E.Y(Math.max(0, p.anomalia)), y2 = E.Y(Math.min(0, p.anomalia));
        doc.rect(E.X(p.anio) - bw / 2, y1, bw, Math.max(0.1, y2 - y1), 'F');
      });
      etiquetasAnios(rect, E.X, a0, a1);
      y = rect.y + rect.h + 10;
      pie((idioma === 'en' ? 'Reference mean: ' : 'Media de referencia: ') + n(res.referencia.media, dec) + ' ' + u + ' (' + res.referencia.n + '/' + res.referencia.n_esperados + (idioma === 'en' ? ' valid years). Source: NASA POWER (MERRA-2).' : ' años válidos). Fuente: NASA POWER (MERRA-2).'));
    }
    function grafCiclo() {
      var c = res.ciclo_estacional.filter(function (x) { return x.media !== null; });
      if (c.length < 2) return;
      var ys = c.map(function (x) { return x.media; }), mn = Math.min(0, Math.min.apply(null, ys)), mx = Math.max.apply(null, ys) * 1.1;
      if (v.id === 'T2M') { mn = Math.min.apply(null, ys) - 1; mx = Math.max.apply(null, ys) + 1; }
      asegurar(62); leyendaFigura(t('f.ciclo') + ' · ' + res.consulta.periodo.inicio + '–' + res.consulta.periodo.fin);
      var rect = { x: M.l + 16, y: y + 2, w: ANCHO - 20, h: 42 }, E = ejes(rect, 0.5, 12.5, mn, mx, c[0].unidad);
      var meses = t('mes');
      color([107, 174, 214], 'f');
      c.forEach(function (x) { var y1 = E.Y(x.media), y0 = E.Y(mn); doc.rect(E.X(x.mes) - 2.6, y1, 5.2, Math.max(0.1, y0 - y1), 'F'); });
      fuente(6.5, 'normal'); color(COL.suave);
      for (var k = 1; k <= 12; k++) doc.text(meses[k - 1], E.X(k), rect.y + rect.h + 3.5, { align: 'center' });
      y = rect.y + rect.h + 7;
      pie((idioma === 'en' ? 'Only the selected months are shown. Source: NASA POWER (MERRA-2).' : 'Solo se muestran los meses seleccionados. Fuente: NASA POWER (MERRA-2).'));
    }

    // ------------------------------------------------------------------ textos comunes
    function veredictoTxt() { return t('ver.' + res.tendencia.veredicto.estado); }
    function temporadaTxt() {
      var m = res.consulta.meses, nombres = t('mes');
      if (m.length === 12) return t('consulta.temporada.anual');
      return (idioma === 'en' ? 'months ' : 'meses ') + m.map(function (k) { return nombres[k - 1]; }).join(', ');
    }
    function tipoTxt() { var a = res.area; return a.tipo === 'administrativa' && a.admin && a.admin.nivel ? (idioma === 'en' ? 'Administrative unit (' + (a.admin.nivel === 'municipio' ? 'municipality' : 'department') + ')' : 'Unidad administrativa (' + a.admin.nivel + ')') : t('area.' + a.tipo); }
    function adminTxt() {
      var a = res.area.admin;
      if (!a) return t('na');
      return ['Nicaragua', a.departamento, a.municipio].filter(Boolean).join(' · ');
    }
    function avisoTxt(cod) {
      return t('aviso.' + cod, { huella: n(res.cobertura.huella_punto_km2 || (res.celdas[0] && res.celdas[0].area_celda_km2), 0), anios: res.calidad.anios_excluidos.join(', '), r1: n(res.tendencia.r1_residuos, 2) });
    }
    function motivoTxt() { return res.calidad.motivos.map(function (m) { return t('motivo.' + m, { min: Math.max(res.consulta.calidad.min_anios, 10) }); }).join(' '); }
    function limitacionPrincipal() {
      var av = res.calidad.avisos;
      var orden = ['consulta_puntual', 'lluvia_merra2_inhomogeneidad', 'area_menor_que_celda', 'una_sola_celda', 'celdas_sin_datos', 'autocorrelacion_residuos', 'reanalisis'];
      for (var i = 0; i < orden.length; i++) if (av.indexOf(orden[i]) >= 0) return avisoTxt(orden[i]);
      return avisoTxt('reanalisis');
    }
    function senTxt() { var s = res.tendencia.sen; return s ? n(s.pendiente_decada, dec + 1) : t('na'); }
    var enlace = op.enlace || null;

    // ------------------------------------------------------------------ A. Portada
    (function portada() {
      color(COL.acento, 'f'); doc.rect(0, 0, A4.w, 34, 'F');
      fuente(10, 'bold'); color([255, 255, 255]); doc.text('Earth System Trend Detective', M.l, 13);
      fuente(9, 'normal'); doc.text(limpio(t('inf.subtitulo') + ' · ' + (plantilla === 'resumen' ? t('inf.resumen') : t('inf.completo'))), M.l, 19.5);
      fuente(8, 'normal'); doc.text(limpio(t('inf.id') + ': ' + idInforme), A4.w - M.r, 13, { align: 'right' });
      doc.text(limpio(t('inf.generado') + ': ' + (op.generado_utc || res.generado_utc).slice(0, 19).replace('T', ' ') + ' UTC'), A4.w - M.r, 19.5, { align: 'right' });
      y = 44;
      parrafo(titulo, { tam: 17, estilo: 'bold', despues: 2 });
      parrafo((res.area.nombre || t('area.' + res.area.tipo)) + ' · ' + tipoTxt() + (res.area.admin ? ' · ' + adminTxt() : ''), { tam: 10.5, color: COL.suave, despues: 1 });
      parrafo((idioma === 'en' ? v.nombre_en : v.nombre) + ' · ' + res.consulta.periodo.inicio + '–' + res.consulta.periodo.fin + ' · ' + temporadaTxt(), { tam: 10.5, color: COL.suave, despues: 4 });
      bloqueMapaDetalle(null, 92);
      var filas = [
        [t('inf.id'), idInforme], [t('inf.revision'), res.resultado_id + ' · ' + (op.generado_utc || res.generado_utc).slice(0, 10)],
        [t('inf.consulta'), res.consulta_id], [t('inf.version_app'), res.version_codigo + ' · NASA POWER API ' + (res.fuente.version_api || t('na'))]
      ];
      if (op.autor) filas.push([t('inf.autor'), op.autor]);
      if (op.organizacion) filas.push([t('inf.organizacion'), op.organizacion]);
      var yTabla = y;
      tabla(null, filas, [40, 90]);
      if (enlace && op.qrcode) {
        var qr = op.qrcode(0, 'M'); qr.addData(enlace); qr.make();
        var mods = qr.getModuleCount(), lado = 30, celda = lado / mods, x0 = A4.w - M.r - lado, y0 = Math.max(yTabla, y + 2);
        if (y0 + lado + 14 > A4.h - M.b) { y0 = A4.h - M.b - lado - 14; }
        color([0, 0, 0], 'f');
        for (var r2 = 0; r2 < mods; r2++) for (var c2 = 0; c2 < mods; c2++) if (qr.isDark(r2, c2)) doc.rect(x0 + c2 * celda, y0 + r2 * celda, celda + 0.01, celda + 0.01, 'F');
        doc.link(x0, y0, lado, lado, { url: enlace });
        y = Math.max(y, y0 - 2);
        fuente(9, 'bold'); color(COL.acento); doc.textWithLink(limpio(t('inf.enlace')), M.l, y + 4, { url: enlace });
        y += 6;
        fuente(6.5, 'normal'); color(COL.suave);
        var lin = doc.splitTextToSize(enlace, ANCHO - lado - 6).slice(0, 6);
        lin.forEach(function (l, i) { doc.textWithLink(l, M.l, y + 3 + i * 2.8, { url: enlace }); });
        y += lin.length * 2.8 + 4;
        parrafo(t('inf.qr') + ' ' + t('exp.enlace_consulta_ayuda'), { tam: 7.5, color: COL.suave, ancho: ANCHO - lado - 6 });
        y = Math.max(y, y0 + lado + 3);
      }
      parrafo(t('inf.no_oficial'), { tam: 7.5, estilo: 'italic', color: COL.suave });
    })();

    // ------------------------------------------------------------------ B. Resumen ejecutivo
    function secB() {
      nuevaPagina(); seccion('B');
      var T = res.tendencia, R = res.resumen;
      parrafo(t('b.donde'), { estilo: 'bold', despues: 0.5 });
      parrafo((res.area.nombre || t('area.' + res.area.tipo)) + ' (' + tipoTxt() + (res.area.superficie_km2 !== null ? ', ' + n(res.area.superficie_km2, 1) + ' km²' : '') + (res.area.admin ? '; ' + adminTxt() : '') + ').');
      parrafo(t('b.que'), { estilo: 'bold', despues: 0.5 });
      parrafo((idioma === 'en' ? v.nombre_en : v.nombre) + ' (' + u + ').');
      parrafo(t('b.periodo'), { estilo: 'bold', despues: 0.5 });
      parrafo(t('b.periodo_txt', { ini: res.consulta.periodo.inicio, fin: res.consulta.periodo.fin, n: R.n_validos, total: R.anios_periodo, temporada: temporadaTxt(), fuente: 'NASA POWER ' + (res.fuente.version_api || '') + ' (MERRA-2)', tipo: t('tipo.' + res.fuente.tipo_dato) }));
      parrafo(t('b.resultado'), { estilo: 'bold', despues: 0.5 });
      if (T.sen) parrafo(t('b.resultado_tend', { veredicto: veredictoTxt(), sen: senTxt(), u: u, nivel: nivelPct, inf: n(T.sen.ic_inf_decada, dec + 1), sup: n(T.sen.ic_sup_decada, dec + 1), p: pf(T.sen.p_mann_kendall) }) + ' ' + t('expl.' + T.veredicto.estado));
      else parrafo(t('b.resultado_falta', { motivo: motivoTxt() }) + ' ' + t('expl.faltan'));
      parrafo(t('b.limitacion'), { estilo: 'bold', despues: 0.5 });
      parrafo(limitacionPrincipal());
      y += 2;
      tabla([t('f.indicador'), t('f.valor')], indicadores(), [60, 110], { titulo: t('b.indicadores') });
    }
    function indicadores() {
      var T = res.tendencia, R = res.resumen, f = [];
      f.push([t('res.veredicto'), veredictoTxt()]);
      f.push([t('res.sen'), T.sen ? senTxt() + ' ' + t('res.por_decada', { u: u }) + ' · ' + t('res.ic', { nivel: nivelPct, inf: n(T.sen.ic_inf_decada, dec + 1), sup: n(T.sen.ic_sup_decada, dec + 1) }) : t('na')]);
      f.push([t('res.mk'), T.sen ? t('res.p', { p: pf(T.sen.p_mann_kendall) }) : t('na')]);
      f.push([t('res.mco'), T.mco ? n(T.mco.pendiente_decada, dec + 1) + ' ± ' + n(T.mco.error_estandar_decada, dec + 1) + ' ' + t('res.por_decada', { u: u }) + ' (' + (idioma === 'en' ? 'std. error' : 'error estándar') + ') · ' + t('res.ic', { nivel: nivelPct, inf: n(T.mco.ic_inf_decada, dec + 1), sup: n(T.mco.ic_sup_decada, dec + 1) }) + ' · ' + t('res.p', { p: pf(T.mco.p) }) : t('na')]);
      f.push([t('res.media'), n(R.media, dec) + ' ' + u + ' (' + (idioma === 'en' ? 'SD ' : 'desv. est. ') + n(R.desv_est, dec) + ')']);
      f.push([idioma === 'en' ? 'Minimum / maximum' : 'Mínimo / máximo', R.minimo ? n(R.minimo.valor, dec) + ' (' + R.minimo.anio + ') / ' + n(R.maximo.valor, dec) + ' (' + R.maximo.anio + ')' : t('na')]);
      f.push([t('res.n'), R.n_validos + ' / ' + R.anios_periodo + ' (' + (R.anio_inicio_efectivo || '–') + '–' + (R.anio_fin_efectivo || '–') + ')']);
      f.push([idioma === 'en' ? 'Missing years / months' : 'Años / meses faltantes', n(R.pct_anios_faltantes, 1) + ' % / ' + n(R.pct_meses_faltantes, 1) + ' %']);
      f.push([t('res.cobertura'), res.cobertura.area_solicitada_km2 === null ? t('ficha.sin_superficie', { huella: n(res.cobertura.huella_punto_km2, 0), celda: res.celdas[0].id }) : t('c.solicitada_cubierta', { sol: n(res.cobertura.area_solicitada_km2, 1), cub: n(res.cobertura.area_cubierta_km2, 1), pct: n(100 * res.cobertura.fraccion_cubierta, 1) })]);
      if (res.comparacion_periodos) { var c = res.comparacion_periodos; f.push([t('f.comparacion'), c.b.inicio + '–' + c.b.fin + ' − ' + c.a.inicio + '–' + c.a.fin + ': ' + n(c.diferencia, dec) + ' ' + u]); }
      f.push([idioma === 'en' ? 'Lag-1 autocorrelation of residuals' : 'Autocorrelación de orden 1 de residuos', n(T.r1_residuos, 2)]);
      return f;
    }

    // ------------------------------------------------------------------ C. Localización y delimitación
    function secC() {
      nuevaPagina(); seccion('C');
      if (plantilla === 'completo') {
        asegurar(84); leyendaFigura(t('c.contexto'));
        var rect = { x: M.l + 7, y: y + 1, w: ANCHO - 10, h: 70 }, P = mapaContexto(rect);
        y = rect.y + rect.h + 6;
        pie(t('c.proyeccion', { lat: n(P.lat0, 2) }) + ' ' + t('c.atribucion', { limites: limitesTexto() }) + (idioma === 'en' ? ' Blue frame: extent of the detail map.' : ' Recuadro azul: extensión del mapa de detalle.'));
      }
      leyendaFigura(t('c.detalle'));
      bloqueMapaDetalle(null, 96);
      ficha();
    }
    function ficha() {
      var a = res.area, e = a.extension, f = [];
      f.push([t('ficha.id'), a.id || t('na')]);
      f.push([t('area.nombre'), a.nombre || t('na')]);
      f.push([t('ficha.tipo'), tipoTxt() + (a.radio_km ? ' · ' + t('area.radio') + ' ' + n(a.radio_km, 2) : '')]);
      f.push([t('ficha.extension'), [e[0], e[1], e[2], e[3]].map(function (x) { return n(x, 5); }).join(' ; ') + (e[0] > e[2] ? ' · ' + t('ficha.cruza') : '')]);
      f.push([t('ficha.centro'), n(a.centro.lat, 5) + '°, ' + n(a.centro.lon, 5) + '° (lat, lon) · ' + t('metodo.' + a.centro.metodo)]);
      f.push([t('ficha.superficie'), a.superficie_km2 === null ? t('ficha.sin_superficie', { huella: n(res.cobertura.huella_punto_km2, 0), celda: res.celdas[0].id }) : n(a.superficie_km2, 3) + ' km² (WGS84, GeographicLib)' + (a.admin && a.admin.area_oficial_km2 ? ' · ' + (idioma === 'en' ? 'published by INETER: ' : 'publicada por INETER: ') + n(a.admin.area_oficial_km2, 3) + ' km²' : '')]);
      f.push([t('c.area') + ' / ' + (idioma === 'en' ? 'coverage' : 'cobertura'), res.cobertura.area_solicitada_km2 === null ? '—' : t('c.solicitada_cubierta', { sol: n(res.cobertura.area_solicitada_km2, 1), cub: n(res.cobertura.area_cubierta_km2, 1), pct: n(100 * res.cobertura.fraccion_cubierta, 1) })]);
      f.push([t('ficha.admin'), adminTxt()]);
      f.push([t('ficha.procedencia'), a.procedencia ? t('proc.' + a.procedencia.tipo) + (a.procedencia.fuente ? ' · ' + a.procedencia.fuente : '') : t('na')]);
      f.push([t('ficha.version'), a.procedencia && a.procedencia.version ? a.procedencia.version : t('na')]);
      if (a.vertices) f.push([t('ficha.vertices'), String(a.vertices)]);
      f.push(['CRS', 'EPSG:4326 · GeoJSON (lon, lat)']);
      tabla([t('c.ficha'), ''], f, [45, 125], { titulo: t('c.ficha') });
    }

    // ------------------------------------------------------------------ D. Inventario
    function secD() {
      nuevaPagina(); seccion('D');
      var f = res.fuente;
      var fila = ['NASA POWER · ' + (idioma === 'en' ? f.producto_en : f.producto), (idioma === 'en' ? v.nombre_en : v.nombre) + ' (' + v.parametro + ')', f.unidad_original + ' → ' + u,
        idioma === 'en' ? f.resolucion_espacial_en : f.resolucion_espacial, f.periodo_descargado.inicio + '–' + f.periodo_descargado.fin + ' (' + (idioma === 'en' ? 'monthly' : 'mensual') + ')',
        'API ' + (f.version_api || t('na')) + ' · ' + (f.fuentes_declaradas || []).join(', '), String(f.acceso_utc).slice(0, 10), res.cobertura.celdas_con_datos + '/' + res.cobertura.celdas_total + (idioma === 'en' ? ' cells' : ' celdas')];
      var filas = [fila];
      if (res.area.procedencia && res.area.procedencia.tipo === 'ineter') filas.push(['INETER · ' + (res.area.procedencia.fuente || ''), t('d.limites'), '—', (idioma === 'en' ? 'vector, simplified 0.001°' : 'vectorial, simplificado 0,001°'), '—', res.area.procedencia.version || t('na'), res.area.procedencia.fecha_acceso || t('na'), 'Nicaragua']);
      tabla(t('d.tabla'), filas, [30, 22, 14, 22, 20, 20, 16, 14], { titulo: t('sec.D'), tam: 7.2 });
      var det = [
        [t('d.url'), f.url_oficial + ' · ' + f.url_documentacion],
        [idioma === 'en' ? 'Data type' : 'Tipo de dato', t('tipo.' + f.tipo_dato) + ' (MERRA-2; Gelaro et al., 2017)'],
        [t('d.licencia'), (idioma === 'en' ? f.licencia_en : f.licencia) + ' «' + f.atribucion + '»'],
        [t('d.cuenta'), t('d.no')],
        [t('d.transformaciones'), t('d.transf.' + v.id)],
        [t('d.restricciones'), f.restricciones.filter(function (x) { return x !== 'ultimo_anio_incompleto' || res.calidad.avisos.indexOf('anio_en_curso') >= 0; }).map(function (x) { return ({ reanalisis_no_observacion: avisoTxt('reanalisis'), lluvia_merra2_inhomogeneidad: v.id === 'PRECTOTCORR' ? avisoTxt('lluvia_merra2_inhomogeneidad') : '', resolucion_gruesa: t('d.resolucion_txt'), ultimo_anio_incompleto: avisoTxt('anio_en_curso') })[x]; }).filter(Boolean).join(' ')],
        [t('d.resolucion'), t('d.resolucion_txt')],
        [idioma === 'en' ? 'Query mode' : 'Modo de consulta', t('consulta.fuente_puntual')]
      ];
      if (f.fallos && f.fallos.length) det.push([idioma === 'en' ? 'Failed cells' : 'Celdas fallidas', f.fallos.map(function (x) { return x.id + ' (' + x.error + ')'; }).join(', ')]);
      tabla(null, det, [38, 132]);
    }

    // ------------------------------------------------------------------ E. Metodología
    function secE() {
      nuevaPagina(); seccion('E');
      var q = res.consulta.calidad;
      [['e.seleccion', 'e.seleccion_txt'], ['e.ponderacion', 'e.ponderacion_txt'], ['e.calidad', 'e.calidad_txt'], ['e.suficiencia', 'e.suficiencia_txt'], ['e.metodos', 'e.metodos_txt'], ['e.reproducir', 'e.reproducir_txt']]
        .forEach(function (p) {
          titular(t(p[0]), 2);
          parrafo(t(p[1], { cob: n(q.min_cobertura_espacial * 100, 0), min: Math.max(q.min_anios, 10), fr: n(q.min_fraccion_referencia * 100, 0), nivel: nivelPct, alfa: n(res.tendencia.alfa, 2) }));
        });
      titular(t('e.parametros'), 2);
      var c = res.consulta, f = [
        ['variable', v.id + ' · ' + v.unidad], ['fuente', c.fuente + ' · ' + (res.fuente.version_api || '')], ['periodo', c.periodo.inicio + '–' + c.periodo.fin],
        ['referencia', c.referencia.inicio + '–' + c.referencia.fin], ['meses', c.meses.join(', ')],
        ['agregacion_temporal', v.operacion_temporal], ['agregacion_espacial', v.operacion_espacial + ' · ' + res.celdas.length + (idioma === 'en' ? ' cells' : ' celdas')],
        ['calidad.min_cobertura_espacial', String(q.min_cobertura_espacial)], ['calidad.min_anios', String(q.min_anios)], ['calidad.min_fraccion_referencia', String(q.min_fraccion_referencia)],
        ['estadistica.metodos', c.estadistica.metodos.join(', ')], ['estadistica.nivel', String(c.estadistica.nivel)],
        ['vista.anio_visible / capa', (c.vista.anio_visible || c.periodo.fin) + ' · ' + c.vista.capa], ['idioma', c.idioma], ['version_codigo', c.version_codigo]
      ];
      tabla([idioma === 'en' ? 'Parameter' : 'Parámetro', t('f.valor')], f, [55, 115], { titulo: t('e.parametros'), tam: 7.8 });
    }

    // ------------------------------------------------------------------ F. Resultados
    function secF() {
      nuevaPagina(); seccion('F');
      var T = res.tendencia;
      if (res.calidad.insuficiente) parrafo(t('ver.faltan') + ': ' + motivoTxt() + ' ' + t('expl.faltan'), { estilo: 'bold', color: COL.area });
      grafSerie();
      var filas = [];
      if (T.sen) filas.push(['Theil-Sen', n(T.sen.pendiente_decada, dec + 2), n(T.sen.ic_inf_decada, dec + 2) + ' … ' + n(T.sen.ic_sup_decada, dec + 2), 'Mann-Kendall p ' + pf(T.sen.p_mann_kendall), String(T.sen.n)]);
      if (T.mco) filas.push([idioma === 'en' ? 'Least squares' : 'Mínimos cuadrados', n(T.mco.pendiente_decada, dec + 2) + ' ± ' + n(T.mco.error_estandar_decada, dec + 2), n(T.mco.ic_inf_decada, dec + 2) + ' … ' + n(T.mco.ic_sup_decada, dec + 2), 't p ' + pf(T.mco.p), String(T.mco.n)]);
      if (filas.length) tabla([idioma === 'en' ? 'Method' : 'Método', u + '/' + (idioma === 'en' ? 'decade' : 'década'), (idioma === 'en' ? 'CI ' + nivelPct + '%' : 'IC ' + nivelPct + ' %'), 'p', 'n'], filas, [40, 32, 40, 38, 12], { titulo: (idioma === 'en' ? 'Trend and uncertainty · verdict: ' : 'Tendencia e incertidumbre · veredicto: ') + veredictoTxt() });
      parrafo(t('expl.' + T.veredicto.estado), { tam: 8.6 });
      if (plantilla === 'completo') {
        grafAnomalias();
        grafCiclo();
        if (res.celdas.length > 1) { asegurar(110); leyendaFigura(t('f.distribucion') + ' · ' + res.consulta.periodo.inicio + '–' + res.consulta.periodo.fin); bloqueMapaDetalle('tendencia_celda', 84); }
        if (res.comparacion_periodos) {
          var c = res.comparacion_periodos;
          tabla([idioma === 'en' ? 'Period' : 'Periodo', idioma === 'en' ? 'Mean' : 'Media', 'n'], [[c.a.inicio + '–' + c.a.fin + (idioma === 'en' ? ' (reference)' : ' (referencia)'), n(c.a.media, dec) + ' ' + u, String(c.a.n)], [c.b.inicio + '–' + c.b.fin + (idioma === 'en' ? ' (last 10 valid years)' : ' (últimos 10 años válidos)'), n(c.b.media, dec) + ' ' + u, String(c.b.n)], [idioma === 'en' ? 'Difference' : 'Diferencia', n(c.diferencia, dec) + ' ' + u + (c.solapan ? (idioma === 'en' ? ' (periods overlap)' : ' (los periodos se solapan)') : ''), '']], [70, 70, 20], { titulo: t('f.comparacion') });
        }
        var fc = res.celdas.map(function (c) { return [c.id, n(c.lat, 3) + ', ' + n(c.lon, 3), c.interseccion_km2 === null ? '—' : n(c.interseccion_km2, 1), n(c.peso, 4), c.estado === 'ok' ? n(c.media, dec) : t('c.sin_cobertura'), c.tendencia && c.tendencia.sen_decada !== undefined ? n(c.tendencia.sen_decada, dec + 2) + ' (' + n(c.tendencia.ic_inf_decada, dec + 2) + ' … ' + n(c.tendencia.ic_sup_decada, dec + 2) + ')' : t('na'), t('ver.' + (c.tendencia ? c.tendencia.veredicto : 'faltan'))]; });
        tabla([idioma === 'en' ? 'Cell' : 'Celda', 'lat, lon', idioma === 'en' ? 'Intersection km²' : 'Intersección km²', idioma === 'en' ? 'Weight' : 'Peso', (idioma === 'en' ? 'Mean ' : 'Media ') + u, 'Sen ' + u + '/' + (idioma === 'en' ? 'dec.' : 'déc.') + ' (IC)', t('res.veredicto')], fc, [24, 22, 18, 13, 16, 38, 30], { titulo: t('f.tabla_celdas'), tam: 7 });
        pie(t('f.nota_celdas'));
        var R = res.resumen, dq = [
          [idioma === 'en' ? 'Valid years' : 'Años válidos', R.n_validos + ' / ' + R.anios_periodo],
          [idioma === 'en' ? 'Effective first / last year' : 'Primer / último año efectivo', (R.anio_inicio_efectivo || t('na')) + ' / ' + (R.anio_fin_efectivo || t('na'))],
          [idioma === 'en' ? 'Missing months (%)' : 'Meses faltantes (%)', n(R.pct_meses_faltantes, 2)],
          [idioma === 'en' ? 'Mean monthly spatial coverage' : 'Cobertura espacial mensual media', n(100 * R.cobertura_espacial_media, 1) + ' %'],
          [idioma === 'en' ? 'Excluded years' : 'Años excluidos', res.calidad.anios_excluidos.join(', ') || (idioma === 'en' ? 'none' : 'ninguno')],
          [idioma === 'en' ? 'Reference years valid' : 'Años válidos en la referencia', res.referencia.n + ' / ' + res.referencia.n_esperados + (res.referencia.suficiente ? '' : ' · ' + avisoTxt('referencia_insuficiente'))]
        ];
        res.calidad.avisos.forEach(function (a) { dq.push([idioma === 'en' ? 'Notice' : 'Aviso', avisoTxt(a)]); });
        tabla([t('f.indicador'), t('f.valor')], dq, [50, 120], { titulo: t('f.diagnostico'), tam: 7.8 });
      }
    }

    // ------------------------------------------------------------------ G. Interpretación
    function secG() {
      nuevaPagina(); seccion('G');
      var T = res.tendencia;
      titular('1. ' + t('g.calculado'), 2);
      parrafo(T.sen ? t('b.resultado_tend', { veredicto: veredictoTxt(), sen: senTxt(), u: u, nivel: nivelPct, inf: n(T.sen.ic_inf_decada, dec + 1), sup: n(T.sen.ic_sup_decada, dec + 1), p: pf(T.sen.p_mann_kendall) }) : t('b.resultado_falta', { motivo: motivoTxt() }));
      titular('2. ' + t('g.interpretacion'), 2);
      parrafo(t('expl.' + T.veredicto.estado) + ' ' + t('g.no_pronostico'));
      if (res.calidad.avisos.indexOf('consulta_puntual') >= 0) parrafo(avisoTxt('consulta_puntual'));
      titular('3. ' + t('g.literatura'), 2);
      var comps = op.comparaciones || [];
      if (!comps.length) parrafo(t('g.sin_comparacion'));
      comps.forEach(function (c) { parrafo(t('g.comparacion_txt', { fuente: c.fuente, region: c.region, periodo: c.periodo, valor: n(c.valor, 3), u: c.unidad, inf: n(c.inf, 3), sup: n(c.sup, 3) })); });
      titular('4. ' + t('g.limitaciones'), 2);
      res.calidad.avisos.forEach(function (a) { parrafo('• ' + avisoTxt(a)); });
      if (!res.tendencia.correccion_autocorrelacion) parrafo('• ' + (idioma === 'en' ? 'The intervals do not correct for serial autocorrelation (lag-1 r of residuals = ' : 'Los intervalos no corrigen la autocorrelación serial (r de orden 1 de los residuos = ') + n(T.r1_residuos, 2) + ').');
    }

    // ------------------------------------------------------------------ N. Notas del usuario
    function secN() {
      if (!op.notas) return;
      asegurar(30); titular(t('sec.N'), 1);
      parrafo(t('n.aviso'), { tam: 8, estilo: 'italic', color: COL.suave });
      color(COL.fondo, 'f');
      parrafo(op.notas, { tam: 9.5 });
    }

    // ------------------------------------------------------------------ H. Referencias y anexos
    function secH() {
      nuevaPagina(); seccion('H');
      titular(t('h.referencias'), 2);
      ['sen1968', 'mann1945', 'kendall1975', 'gelaro2017', 'karney2013', 'power'].concat(res.area.procedencia && res.area.procedencia.tipo === 'ineter' ? ['ineter'] : []).forEach(function (k) {
        var r = Fuentes.REFERENCIAS[k];
        var txt = r.autores + (r.anio ? ' (' + r.anio + '). ' : '. ') + r.titulo + '. ' + (idioma === 'en' && r.revista_en ? r.revista_en : r.revista) + '.';
        parrafo(txt, { tam: 8.6, despues: 0.4 });
        if (r.doi) { fuente(8.2, 'normal'); color(COL.acento); asegurar(4); doc.textWithLink('https://doi.org/' + r.doi, M.l + 4, y + 2.8, { url: 'https://doi.org/' + r.doi }); y += 4; parrafo(t('h.doi_verificado', { fecha: r.verificado.slice(0, 10) }), { tam: 7, color: COL.suave, x: M.l + 4, despues: 1.5 }); }
        else y += 1.4;
      });
      titular(t('h.archivos'), 2);
      tabla([idioma === 'en' ? 'File' : 'Archivo', idioma === 'en' ? 'Content' : 'Contenido'], ['informe.pdf', 'area_interes.geojson', 'consulta.json', 'resultados.json', 'serie_temporal.csv', 'serie_mensual.csv', 'celdas_mensual.csv', 'fuentes.csv', 'manifest.json', 'LEEME.txt'].map(function (a) { return [a, t('arch.' + a)]; }), [40, 130], { tam: 8 });
      if (plantilla === 'completo') {
        titular(idioma === 'en' ? 'Original data requests (NASA POWER)' : 'Peticiones originales de datos (NASA POWER)', 2);
        res.celdas.slice(0, 64).forEach(function (c) { parrafo(Fuentes.urlCelda(v.parametro, c.lon, c.lat, res.fuente.periodo_descargado.inicio, res.fuente.periodo_descargado.fin), { tam: 6.4, color: COL.suave, despues: 0.3 }); });
      }
    }

    var mapa = { B: secB, C: secC, D: secD, E: secE, F: secF, G: secG, H: secH };
    secciones.forEach(function (s) { mapa[s](); if (s === 'G') secN(); });
    if (secciones.indexOf('G') < 0) secN();

    // encabezados y pies con numeración
    var total = doc.getNumberOfPages();
    for (var p = 1; p <= total; p++) {
      doc.setPage(p);
      if (p > 1) {
        fuente(7, 'normal'); color(COL.suave);
        doc.text(limpio('Earth System Trend Detective · ' + t('inf.subtitulo')), M.l, 11);
        doc.text(idInforme, A4.w - M.r, 11, { align: 'right' });
        color(COL.linea, 'd'); doc.setLineWidth(0.2); doc.line(M.l, 12.5, A4.w - M.r, 12.5);
      }
      fuente(7, 'normal'); color(COL.suave);
      doc.text(limpio(t('inf.pagina', { n: p, total: total })), A4.w - M.r, A4.h - 9, { align: 'right' });
      doc.text(limpio(res.resultado_id), M.l, A4.h - 9);
    }
    return { doc: doc, id: idInforme, paginas: total };
  }

  return { crear: crear, SECCIONES: SECCIONES, RESUMEN: RESUMEN, limpio: limpio };
});
