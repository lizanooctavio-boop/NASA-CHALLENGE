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
  var SECCIONES = ['B', 'C', 'D', 'E', 'F', 'G', 'P', 'H'];
  var RESUMEN = ['B', 'C', 'F', 'G', 'P', 'H'];

  // Caracteres fuera de WinAnsi sustituidos por equivalentes legibles (las tildes y la ñ se conservan).
  var SUST = { '−': '-', '≈': '~', 'α': 'alfa', '≥': '>=', '≤': '<=', ' ': ' ', ' ': ' ', ' ': ' ', '→': '->', '✓': 'v' };
  function limpio(s) { return String(s === null || s === undefined ? '' : s).replace(/[−≈α≥≤   →✓]/g, function (c) { return SUST[c]; }); }

  function crear(res, op) {
    var idioma = op.idioma || res.consulta.idioma, t = function (k, v) { return I18n.t(k, idioma, v); };
    var n = function (v, d) { return I18n.num(v, d, idioma); };
    var pf = function (p) { return p === null || p === undefined ? '= ' + I18n.t('na', idioma) : p < 0.0001 ? '< ' + I18n.num(0.0001, 4, idioma) : '= ' + I18n.num(p, 4, idioma); };
    var JsPDF = op.jsPDF || (typeof window !== 'undefined' && window.jspdf && window.jspdf.jsPDF);
    if (!JsPDF) throw new Error('jsPDF no está cargado');
    var doc = new JsPDF({ unit: 'mm', format: 'a4', compress: true, putOnlyUsedFonts: true, floatPrecision: 3 });
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
    var PV = res.perspectiva && res.perspectiva.indicadores ? res.perspectiva : null;
    var varsSec = PV ? { ini: PV.horizonte.inicio, fin: PV.horizonte.fin } : {};
    function seccion(letra) { numSeccion++; titular(letra + '. ' + t('sec.' + letra, varsSec), 1); doc.outline && doc.outline.add(null, letra + '. ' + limpio(t('sec.' + letra, varsSec)), { pageNumber: doc.getNumberOfPages() }); }
    function banda(txt) {
      fuente(9, 'bold');
      var ls = doc.splitTextToSize(limpio(txt), ANCHO - 8), alto = 4 + ls.length * 4;
      asegurar(alto + 4); color([232, 240, 252], 'f'); doc.rect(M.l, y, ANCHO, alto, 'F'); color(COL.acento, 'f'); doc.rect(M.l, y, 1.6, alto, 'F');
      fuente(9, 'bold'); color(COL.acento); ls.forEach(function (l, i) { doc.text(l, M.l + 4, y + 5.4 + i * 4); }); y += alto + 3;
    }
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
        lat0: lat0, s: s, k: k, ext: ext, rect: rect,
        p: function (lon, lat) { var dl = lon - lonC; dl = dl > 180 ? dl - 360 : dl < -180 ? dl + 360 : dl; return [ox + (dl + lonC - ext[0]) * k * s, oy + (ext[3] - lat) * s]; },
        mmPorKm: function () { return s / 111.32 / 1; } // 1° de latitud ≈ 111,32 km; en x la escala es la misma a lat0
      };
    }
    function anillo(P, coords, estilo) {
      if (coords.length < 2) return;
      // se omiten los vértices a menos de 0,1 mm del anterior: no se ven y engordan el PDF
      var todos = coords.map(function (c) { return P.p(c[0], c[1]); }), pts = [todos[0]], d = [];
      // islotes de menos de 0,3 mm o anillos enteros fuera del marco: no se dibujan
      var bx = [Infinity, Infinity, -Infinity, -Infinity];
      todos.forEach(function (q) { bx[0] = Math.min(bx[0], q[0]); bx[1] = Math.min(bx[1], q[1]); bx[2] = Math.max(bx[2], q[0]); bx[3] = Math.max(bx[3], q[1]); });
      if (estilo && bx[2] - bx[0] < 0.3 && bx[3] - bx[1] < 0.3) return;
      if (P.rect && (bx[2] < P.rect.x || bx[0] > P.rect.x + P.rect.w || bx[3] < P.rect.y || bx[1] > P.rect.y + P.rect.h)) return;
      // y los que caen fuera del marco del mapa en el mismo lado que el anterior conservado y el siguiente
      var R2 = P.rect, oc = R2 ? function (q) { return (q[0] < R2.x - 2 ? 1 : 0) | (q[0] > R2.x + R2.w + 2 ? 2 : 0) | (q[1] < R2.y - 2 ? 4 : 0) | (q[1] > R2.y + R2.h + 2 ? 8 : 0); } : function () { return 0; };
      for (var k = 1; k < todos.length; k++) {
        var u2 = pts[pts.length - 1];
        if (k === todos.length - 1) { pts.push(todos[k]); break; }
        if (oc(u2) & oc(todos[k]) & oc(todos[k + 1])) continue;
        if (Math.abs(todos[k][0] - u2[0]) + Math.abs(todos[k][1] - u2[1]) >= 0.1) pts.push(todos[k]);
      }
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
          // celda sin dato: gris claro y discontinua, sin rayado
          color([215, 215, 215], 'f'); doc.setLineDashPattern([0.8, 0.6], 0); anillo(P, poly, 'FD'); doc.setLineDashPattern([], 0);
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
      yy += 4; color([215, 215, 215], 'f'); doc.setLineDashPattern([0.8, 0.6], 0); doc.rect(x, yy - 1.5, 6, 3, 'FD'); doc.setLineDashPattern([], 0); doc.text(limpio(t('c.sin_cobertura')), x + 8, yy + 1);
      return yy + 4;
    }
    function nombreCapa(capa) { return t('capa.' + capa); }
    function anioMostrado() { return res.mapa_anomalia ? res.mapa_anomalia.anio_mostrado : (res.consulta.vista.anio_visible || res.consulta.periodo.fin); }
    function anioCapa(capa) { return capa === 'anomalia_anual' ? String(anioMostrado()) + (res.mapa_anomalia && res.mapa_anomalia.anio_mostrado !== res.mapa_anomalia.anio_pedido ? ' (' + t('c.anio_sustituido', { pedido: res.mapa_anomalia.anio_pedido }) + ')' : '') + ' · ' + t('res.referencia', { ini: res.referencia.inicio, fin: res.referencia.fin }) : res.consulta.periodo.inicio + '–' + res.consulta.periodo.fin; }
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
    // Mapa con foto satelital (imagen equirectangular ya compuesta en la app: foto + límites, nombres y carreteras de Esri)
    // con la malla de celdas de NASA POWER y el contorno del área encima.
    function bloqueSatelite(img) {
      var ih = Math.min(118, ANCHO * img.alto / img.ancho), iw = ih * img.ancho / img.alto, x0 = M.l + (ANCHO - iw) / 2;
      asegurar(ih + 16); leyendaFigura(t('c.satelite'));
      var y0 = y + 1;
      try { doc.addImage(img.datos, img.formato || 'JPEG', x0, y0, iw, ih, undefined, 'FAST'); }
      catch (e) { parrafo(t('p.imagen_error'), { tam: 7.5, color: COL.suave }); return; }
      var e2 = img.ext, Pi = { lat0: (e2[1] + e2[3]) / 2, p: function (lon, lat) { return [x0 + (lon - e2[0]) / (e2[2] - e2[0]) * iw, y0 + (e2[3] - lat) / (e2[3] - e2[1]) * ih]; } };
      doc.saveGraphicsState(); doc.rect(x0, y0, iw, ih, null); doc.clip(); doc.discardPath();
      color([255, 255, 255], 'd'); doc.setLineWidth(0.2); doc.setLineDashPattern([1, 0.7], 0);
      res.celdas.forEach(function (c) { var b = c.caja; if (b) anillo(Pi, [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]], 'S'); });
      doc.setLineDashPattern([], 0);
      color([255, 77, 94], 'd'); doc.setLineWidth(0.8);
      var g = res.area.geometria;
      if (g.type === 'Point') { var pp = Pi.p(g.coordinates[0], g.coordinates[1]); color([255, 77, 94], 'f'); doc.circle(pp[0], pp[1], 1.2, 'FD'); }
      else Geo.poligonos(g).forEach(function (pol) { Geo.desenvolverPoligono(pol).forEach(function (a) { anillo(Pi, a, 'S'); }); });
      doc.restoreGraphicsState();
      color(COL.texto, 'd'); doc.setLineWidth(0.25); doc.rect(x0, y0, iw, ih, 'S');
      // norte y escala (en x la imagen ya está corregida por cos(lat): mm por km iguales en ambos ejes)
      color([255, 255, 255], 'f'); doc.rect(x0 + iw - 8, y0 + 1.5, 6.5, 9, 'F'); norte(x0 + iw - 4.75, y0 + 3);
      var mmKm = ih / ((e2[3] - e2[1]) * 111.32), bruto = iw * 0.22 / mmKm, pot = Math.pow(10, Math.floor(Math.log10(bruto))), km = [1, 2, 5].map(function (k) { return k * pot; }).filter(function (k) { return k <= bruto; }).pop() || pot, mm = km * mmKm;
      color([255, 255, 255], 'f'); doc.rect(x0 + 1.5, y0 + ih - 7.5, mm + 16, 6, 'F');
      color(COL.texto, 'f'); doc.rect(x0 + 3, y0 + ih - 4.6, mm, 1, 'F');
      fuente(6, 'normal'); color(COL.texto); doc.text(n(km, km < 1 ? 1 : 0) + ' km', x0 + 4 + mm, y0 + ih - 3.6);
      y = y0 + ih + 2;
      pie(t('c.satelite_pie', { fuente: img.fuente, fecha: img.fecha || t('na'), limites: limitesTexto() }));
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
      parrafo((idioma === 'en' ? v.nombre_en : v.nombre) + ' · ' + res.consulta.periodo.inicio + '–' + res.consulta.periodo.fin + ' · ' + temporadaTxt(), { tam: 10.5, color: COL.suave, despues: PV ? 1 : 4 });
      if (PV) parrafo(t('p.portada', { ini: PV.horizonte.inicio, fin: PV.horizonte.fin }), { tam: 10.5, estilo: 'bold', color: COL.acento, despues: 3 });
      var img = op.imagen;
      if (img && img.datos) {
        var ih = Math.min(84, ANCHO * img.alto / img.ancho);
        try {
          doc.addImage(img.datos, img.formato || 'JPEG', M.l, y, ANCHO, ih, undefined, 'FAST');
          // contorno del área sobre la imagen (misma proyección equirectangular que la petición de la imagen)
          if (img.ext) {
            var Pi = { lat0: 0, p: function (lon, lat) { return [M.l + (lon - img.ext[0]) / (img.ext[2] - img.ext[0]) * ANCHO, y + (img.ext[3] - lat) / (img.ext[3] - img.ext[1]) * ih]; } };
            doc.saveGraphicsState(); doc.rect(M.l, y, ANCHO, ih, null); doc.clip(); doc.discardPath();
            color([255, 77, 94], 'd'); doc.setLineWidth(0.7);
            Geo.poligonos(res.area.geometria).forEach(function (pol) { Geo.desenvolverPoligono(pol).forEach(function (a) { anillo(Pi, a, 'S'); }); });
            if (res.area.geometria.type === 'Point') { var pp = Pi.p(res.area.geometria.coordinates[0], res.area.geometria.coordinates[1]); doc.circle(pp[0], pp[1], 1.4, 'S'); }
            doc.restoreGraphicsState();
          }
          color(COL.texto, 'd'); doc.setLineWidth(0.2); doc.rect(M.l, y, ANCHO, ih, 'S');
          y += ih + 1.5;
          pie(t('p.imagen', { fuente: img.fuente, fecha: img.fecha || t('na') }));
        } catch (e) { parrafo(t('p.imagen_error'), { tam: 7.5, color: COL.suave }); }
      } else bloqueMapaDetalle(null, PV ? 80 : 92);
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
      nuevaPagina(); if (PV) banda(t('p.bloque1')); seccion('B');
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
      if (op.mapaSatelite && op.mapaSatelite.datos) bloqueSatelite(op.mapaSatelite);
      asegurar(96 + 24); leyendaFigura(t('c.detalle'));
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
      ['sen1968', 'mann1945', 'kendall1975', 'gelaro2017', 'karney2013', 'power'].concat(PV ? ['hamed1998', 'benjamini1995', 'tashman2000', 'gardner1985', 'zhang2011', 'lenssen2019'].concat(PV.cmip6_fuente ? ['thrasher2022'] : []) : []).concat(res.area.procedencia && res.area.procedencia.tipo === 'ineter' ? ['ineter'] : []).forEach(function (k) {
        var r = Fuentes.REFERENCIAS[k];
        var txt = (idioma === 'en' && r.autores_en ? r.autores_en : r.autores) + (r.anio ? ' (' + r.anio + '). ' : '. ') + r.titulo + '. ' + (idioma === 'en' && r.revista_en ? r.revista_en : r.revista) + '.';
        parrafo(txt, { tam: 8.6, despues: 0.4 });
        if (r.doi) { fuente(8.2, 'normal'); color(COL.acento); asegurar(4); doc.textWithLink('https://doi.org/' + r.doi, M.l + 4, y + 2.8, { url: 'https://doi.org/' + r.doi }); y += 4; parrafo(t('h.doi_verificado', { fecha: r.verificado.slice(0, 10) }), { tam: 7, color: COL.suave, x: M.l + 4, despues: 1.5 }); }
        else y += 1.4;
      });
      titular(t('h.archivos'), 2);
      tabla([idioma === 'en' ? 'File' : 'Archivo', idioma === 'en' ? 'Content' : 'Contenido'], ['informe.pdf', 'area_interes.geojson', 'consulta.json', 'resultados.json', 'serie_temporal.csv', 'serie_mensual.csv', 'celdas_mensual.csv', 'fuentes.csv'].concat(PV ? ['perspectiva.json', 'observaciones_indicadores.csv', 'proyecciones.csv', 'validacion.csv'] : []).concat(['manifest.json', 'LEEME.txt']).map(function (a) { return [a, t('arch.' + a)]; }), [40, 130], { tam: 8 });
      if (plantilla === 'completo') {
        titular(idioma === 'en' ? 'Original data requests (NASA POWER)' : 'Peticiones originales de datos (NASA POWER)', 2);
        res.celdas.slice(0, 64).forEach(function (c) { parrafo(Fuentes.urlCelda(v.parametro, c.lon, c.lat, res.fuente.periodo_descargado.inicio, res.fuente.periodo_descargado.fin), { tam: 6.4, color: COL.suave, despues: 0.3 }); });
      }
    }

    // ------------------------------------------------------------------ P. Perspectiva de la próxima década
    function nomInd(o) { return idioma === 'en' ? o.nombre_en : o.nombre; }
    function uInd(o) { return idioma === 'en' ? (o.unidad_en || o.unidad) : o.unidad; }
    function clase(o) { return t('p.clase.' + o.clasificacion.clase); }
    function rango(q, d, uu) { return n(q.p10, d) + ' … ' + n(q.p90, d) + (uu ? ' ' + uu : ''); }
    function sgn(v, d) { return (v > 0 ? '+' : '') + n(v, d); }
    function mesTxt(o) { var m = o.ultima_observacion; return m || t('na'); }
    // Minimapas de campo continuo (estilo OMM/IDEAM): los valores reales por celda (0,5° × 0,625°) se interpolan
    // bilinealmente solo para dibujar, se recortan a la tierra de Nicaragua (lagos restados) y se colorean por clases.
    var PALETAS = {
      temp: [[5, 48, 97], [33, 102, 172], [67, 147, 195], [146, 197, 222], [209, 229, 240], [247, 247, 247], [253, 219, 199], [244, 165, 130], [214, 96, 77], [178, 24, 43], [103, 0, 31]],
      lluvia: [[84, 48, 5], [140, 81, 10], [191, 129, 45], [223, 194, 125], [246, 232, 195], [245, 245, 245], [199, 234, 229], [128, 205, 193], [53, 151, 143], [1, 102, 94], [0, 60, 48]]
    };
    function tipoPaleta(id) { return /prcp|rx1|rx5|r95|lluvia|rain|^pr$/.test(id) ? 'lluvia' : /cdd/.test(id) ? 'seco' : 'temp'; }
    function colorPaleta(x, tipo) {
      var pal = PALETAS[tipo === 'temp' ? 'temp' : 'lluvia'];
      if (tipo === 'seco') x = 1 - x;
      x = Math.max(0, Math.min(1, x)) * (pal.length - 1);
      var i = Math.min(pal.length - 2, Math.floor(x)), f = x - i;
      return [0, 1, 2].map(function (k) { return Math.round(pal[i][k] + (pal[i + 1][k] - pal[i][k]) * f); });
    }
    function clasesSimetricas(vals) {
      var a = vals.filter(function (x) { return x !== null && x !== undefined && isFinite(x); }).map(Math.abs).sort(function (p, q) { return p - q; });
      var m = a.length ? a[Math.min(a.length - 1, Math.floor(0.98 * (a.length - 1) + 0.5))] : 1;
      if (!(m > 0)) m = a.length && a[a.length - 1] > 0 ? a[a.length - 1] : 1;
      var paso = niceStep(m / 5), nk = Math.max(2, Math.ceil(m / paso - 1e-9));
      var lim = []; for (var k = -nk; k <= nk; k++) lim.push(k * paso);
      return { lim: lim, paso: paso, n: 2 * nk, dec: paso >= 1 ? 0 : paso >= 0.1 ? 1 : paso >= 0.01 ? 2 : 3 };
    }
    function claseDe(v, C) { var k = Math.floor((v - C.lim[0]) / C.paso); return Math.max(0, Math.min(C.n - 1, k)); }
    var cacheMascara = {};
    function geomNicaragua() {
      var f = op.regiones && op.regiones.features && op.regiones.features.filter(function (x) { return x.properties && x.properties.id === 'NIC'; })[0];
      return f ? f.geometry : null;
    }
    function mascaraGeom(g, ext, W, H, nombre) {
      var clave = nombre + '|' + ext.join(',') + '|' + W + 'x' + H;
      if (cacheMascara[clave]) return cacheMascara[clave];
      var m = new Uint8Array(W * H);
      if (!g) { for (var q = 0; q < m.length; q++) m[q] = 1; return (cacheMascara[clave] = m); }
      var anillos = []; Geo.poligonos(g).forEach(function (pol) { pol.forEach(function (a) { anillos.push(a); }); });
      for (var r = 0; r < H; r++) {
        var lat = ext[3] - (r + 0.5) / H * (ext[3] - ext[1]), xs = [];
        anillos.forEach(function (a) { for (var i = 0, j = a.length - 1; i < a.length; j = i++) { var yi = a[i][1], yj = a[j][1]; if ((yi > lat) !== (yj > lat)) xs.push(a[i][0] + (lat - yi) / (yj - yi) * (a[j][0] - a[i][0])); } });
        xs.sort(function (p2, q2) { return p2 - q2; });
        for (var k = 0; k + 1 < xs.length; k += 2) {
          var c0 = Math.max(0, Math.ceil((xs[k] - ext[0]) / (ext[2] - ext[0]) * W - 0.5)), c1 = Math.min(W - 1, Math.floor((xs[k + 1] - ext[0]) / (ext[2] - ext[0]) * W - 0.5));
          for (var c = c0; c <= c1; c++) m[r * W + c] = 1;
        }
      }
      return (cacheMascara[clave] = m);
    }
    function mascaraTierra(ext, W, H) { return mascaraGeom(geomNicaragua(), ext, W, H, 'NIC'); }
    function interpolador(M2, valores) {
      var g = {}, a0 = M2.celdas[0], dla = M2.rejilla.dlat, dlo = M2.rejilla.dlon;
      var cl = function (la, lo) { return la.toFixed(3) + ',' + lo.toFixed(3); };
      M2.celdas.forEach(function (c, i) { var v2 = valores[i]; if (v2 !== null && v2 !== undefined && isFinite(v2)) g[cl(c.lat, c.lon)] = v2; });
      return function (lon, lat) {
        var fi = (lat - a0.lat) / dla, fj = (lon - a0.lon) / dlo, i0 = Math.floor(fi), j0 = Math.floor(fj), ti = fi - i0, tj = fj - j0, s2 = 0, w2 = 0;
        for (var di = 0; di < 2; di++) for (var dj = 0; dj < 2; dj++) {
          var v2 = g[cl(a0.lat + (i0 + di) * dla, a0.lon + (j0 + dj) * dlo)];
          if (v2 === undefined) continue;
          var ww = (di ? ti : 1 - ti) * (dj ? tj : 1 - tj) + 1e-6; s2 += ww * v2; w2 += ww;
        }
        if (w2 > 0) return s2 / w2;
        var mejor = null, bd = 1.05;
        for (di = -1; di <= 2; di++) for (dj = -1; dj <= 2; dj++) {
          var la = a0.lat + (i0 + di) * dla, lo = a0.lon + (j0 + dj) * dlo, v3 = g[cl(la, lo)];
          if (v3 === undefined) continue;
          var d = Math.sqrt(Math.pow((lat - la) / dla, 2) + Math.pow((lon - lo) / dlo, 2));
          if (d < bd) { bd = d; mejor = v3; }
        }
        return mejor;
      };
    }
    // Ráster RGBA (transparente fuera de Nicaragua o sin dato) de la función f(lon, lat) → valor o null.
    function rasterCampo(ext, W, H, f, C, tipo) {
      // ráster opaco: el recorte a la tierra de Nicaragua lo hace el trazado vectorial (jsPDF no aplica el canal alfa)
      var m = mascaraTierra(ext, W, H), data = new Uint8ClampedArray(W * H * 4), cols = [];
      for (var k = 0; k < C.n; k++) cols.push(colorPaleta((k + 0.5) / C.n, tipo));
      for (var r = 0; r < H; r++) {
        var lat = ext[3] - (r + 0.5) / H * (ext[3] - ext[1]);
        for (var c = 0; c < W; c++) {
          var q = r * W + c;
          var v2 = f(ext[0] + (c + 0.5) / W * (ext[2] - ext[0]), lat, q, W, H), o = q * 4;
          if (v2 === null || v2 === undefined || !isFinite(v2)) { var gr = m[q] ? 205 : 236; data[o] = gr; data[o + 1] = gr; data[o + 2] = gr; data[o + 3] = 255; continue; }
          var col = cols[claseDe(v2, C)]; data[o] = col[0]; data[o + 1] = col[1]; data[o + 2] = col[2]; data[o + 3] = 255;
        }
      }
      return { data: data, width: W, height: H };
    }
    // PNG RGB comprimido con el deflate del propio jsPDF: el RGBA crudo no se comprime y engordaba el PDF (~1 MB por panel).
    var TABLA_CRC = (function () { var t2 = []; for (var k = 0; k < 256; k++) { var c = k; for (var j = 0; j < 8; j++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t2[k] = c >>> 0; } return t2; })();
    function pngRGB(im) {
      if (!doc.processDataByFilters) return null;
      var W = im.width, H = im.height, d = im.data, raw = '';
      var trozos = [];
      for (var r = 0; r < H; r++) {
        var fila = [0];
        for (var c = 0; c < W; c++) { var o = (r * W + c) * 4; fila.push(d[o], d[o + 1], d[o + 2]); }
        trozos.push(String.fromCharCode.apply(null, fila));
      }
      raw = trozos.join('');
      var z = doc.processDataByFilters(raw, ['FlateEncode']).data;
      function u32(x) { return String.fromCharCode((x >>> 24) & 255, (x >>> 16) & 255, (x >>> 8) & 255, x & 255); }
      function bloque(tipo, datos) {
        var c = 0xFFFFFFFF, todo = tipo + datos;
        for (var i = 0; i < todo.length; i++) c = TABLA_CRC[(c ^ todo.charCodeAt(i)) & 255] ^ (c >>> 8);
        return u32(datos.length) + todo + u32((c ^ 0xFFFFFFFF) >>> 0);
      }
      var bin = '\x89PNG\r\n\x1a\n' + bloque('IHDR', u32(W) + u32(H) + String.fromCharCode(8, 2, 0, 0, 0)) + bloque('IDAT', z) + bloque('IEND', '');
      var u8 = new Uint8Array(bin.length); for (var q = 0; q < bin.length; q++) u8[q] = bin.charCodeAt(q);
      return u8;
    }
    function lagos(P) {
      if (!op.mundo) return;
      color(COL.agua, 'f'); color([120, 150, 175], 'd'); doc.setLineWidth(0.1);
      var e = P.ext;
      op.mundo.features.forEach(function (f) {
        if (!(f.properties && f.properties.tipo === 'lago' && f.geometry)) return;
        Geo.poligonos(f.geometry).forEach(function (pol) {
          var dentro = pol[0].some(function (c) { return c[0] >= e[0] - 1 && c[0] <= e[2] + 1 && c[1] >= e[1] - 1 && c[1] <= e[3] + 1; });
          if (dentro) anillo(P, pol[0], 'FD');
        });
      });
    }
    function limitesNacionales(P) {
      if (op.admin && op.admin.features) {
        color([255, 255, 255], 'd'); doc.setLineWidth(0.12);
        op.admin.features.forEach(function (f) { if (f.geometry) Geo.poligonos(f.geometry).forEach(function (pol) { anillo(P, pol[0], 'S'); }); });
      }
      var g = geomNicaragua();
      if (g) { color([40, 40, 40], 'd'); doc.setLineWidth(0.22); Geo.poligonos(g).forEach(function (pol) { pol.forEach(function (a) { anillo(P, a, 'S'); }); }); }
    }
    function marcoMinimapa(rect, P) {
      color(COL.texto, 'd'); doc.setLineWidth(0.2); doc.rect(rect.x, rect.y, rect.w, rect.h, 'S');
      fuente(5.5, 'bold'); color(COL.texto); doc.text('N', rect.x + rect.w - 3, rect.y + 3.2, { align: 'center' });
      color(COL.texto, 'f'); doc.triangle(rect.x + rect.w - 3, rect.y + 3.8, rect.x + rect.w - 4.2, rect.y + 7, rect.x + rect.w - 1.8, rect.y + 7, 'F');
      var kmPorMm = Geo.distanciaKm(0, P.lat0, 1, P.lat0) / (P.k * P.s), km = [10, 20, 25, 50, 100, 200].filter(function (k) { return k / kmPorMm <= rect.w * 0.3; }).pop() || 10, mm = km / kmPorMm;
      color([255, 255, 255], 'f'); doc.rect(rect.x + 1, rect.y + rect.h - 5, mm + 9, 4, 'F');
      color(COL.texto, 'f'); doc.rect(rect.x + 2, rect.y + rect.h - 3.2, mm, 0.8, 'F');
      fuente(5, 'normal'); color(COL.texto); doc.text(km + ' km', rect.x + 3 + mm, rect.y + rect.h - 2.4);
    }
    function barraClases(x, yb, w, C, tipo, unidad) {
      var bw = w / C.n;
      for (var k = 0; k < C.n; k++) { color(colorPaleta((k + 0.5) / C.n, tipo), 'f'); doc.rect(x + k * bw, yb, bw + 0.03, 2.4, 'F'); }
      color(COL.texto, 'd'); doc.setLineWidth(0.1); doc.rect(x, yb, w, 2.4, 'S');
      fuente(5.2, 'normal'); color(COL.texto);
      var cada = C.n > 8 ? 2 : 1;
      C.lim.forEach(function (l, k) { if (k % cada) return; doc.line(x + k * bw, yb + 2.4, x + k * bw, yb + 3.1); doc.text(n(l, C.dec), x + k * bw, yb + 5.2, { align: 'center' }); });
      fuente(5.4, 'normal'); doc.text(limpio(unidad), x + w / 2, yb + 7.6, { align: 'center' });
    }
    function rectMinimapa(x, yy, w, ext) {
      var k = Math.cos((ext[1] + ext[3]) / 2 * Math.PI / 180);
      return { x: x, y: yy, w: w, h: w * (ext[3] - ext[1]) / ((ext[2] - ext[0]) * k) };
    }
    // Dibuja un minimapa: f(lon, lat) da el valor (o null); C son las clases comunes de la figura.
    function miniCampo(rect, ext, f, C, tipo, titulo, unidad, conArea) {
      var P = proyector(ext, rect);
      color(COL.agua, 'f'); doc.rect(rect.x, rect.y, rect.w, rect.h, 'F');
      recortarA(rect); paises(P, rect, op.mundo, false);
      var a = P.p(ext[0], ext[3]), z = P.p(ext[2], ext[1]);
      var W = Math.max(60, Math.min(420, Math.round((z[0] - a[0]) * 6))), H = Math.max(40, Math.round(W * (z[1] - a[1]) / (z[0] - a[0])));
      var gN = geomNicaragua();
      doc.saveGraphicsState();
      if (gN) {
        Geo.poligonos(gN).forEach(function (pol) { anillo(P, pol[0], null); });
        doc.clip(); doc.discardPath();
      }
      try {
        var im = rasterCampo(ext, W, H, f, C, tipo), png = pngRGB(im);
        if (png) doc.addImage(png, 'PNG', a[0], a[1], z[0] - a[0], z[1] - a[1], undefined, 'FAST');
        else doc.addImage(im, 'RGBA', a[0], a[1], z[0] - a[0], z[1] - a[1], undefined, 'FAST');
      } catch (e) { /* sin ráster: queda el mapa base */ }
      doc.restoreGraphicsState();
      lagos(P);
      limitesNacionales(P);
      if (conArea !== false) dibujarArea(P, 0.45);
      doc.restoreGraphicsState();
      marcoMinimapa(rect, P);
      fuente(6.6, 'bold'); color(COL.texto);
      doc.text(doc.splitTextToSize(limpio(titulo), rect.w).slice(0, 2), rect.x, rect.y - 3.6);
      barraClases(rect.x, rect.y + rect.h + 1.4, rect.w, C, tipo, unidad);
      return P;
    }
    function rejillaMinimapas(clave, titulo, unidadFn) {
      var M2 = PV.mapas, ids = Object.keys(M2.indicadores).filter(function (id) { return PV.indicadores.some(function (o) { return o.id === id; }); });
      if (!ids.length) return;
      var cols = 3, gap = 6, w = (ANCHO - gap * (cols - 1)) / cols, r0 = rectMinimapa(0, 0, w, M2.ventana), filaH = r0.h + 17;
      asegurar(filaH + 12); leyendaFigura(titulo);
      y += 5;
      ids.forEach(function (id, k) {
        var c = k % cols;
        if (c === 0 && k > 0) y += filaH;
        if (c === 0 && asegurar(filaH)) y += 5;
        var o = PV.indicadores.filter(function (x) { return x.id === id; })[0], vals = M2.indicadores[id][clave];
        miniCampo(rectMinimapa(M.l + c * (w + gap), y, w, M2.ventana), M2.ventana, interpolador(M2, vals), clasesSimetricas(vals), tipoPaleta(id), nomInd(o), unidadFn(o));
      });
      y += filaH + 1;
    }
    // CMIP6 por región (Pacífico, Central, Caribe): mediana de los modelos del cambio de la década frente a 1995–2014.
    function rejillaCmipRegiones() {
      var CR = PV.mapas && PV.mapas.cmip6_regiones, reg = op.regiones;
      if (!CR || !reg) return false;
      var paneles = [];
      ['tas', 'pr'].forEach(function (vv) { Object.keys(CR.escenarios).sort().forEach(function (e) { if (CR.escenarios[e][vv]) paneles.push({ v: vv, e: e, d: CR.escenarios[e][vv] }); }); });
      if (!paneles.length) return false;
      var geoms = {}; reg.features.forEach(function (f) { geoms[f.properties.id] = f.geometry; });
      var ext = PV.mapas.ventana, cols = paneles.length >= 4 ? 2 : paneles.length, gap = 10, w = Math.min(80, (ANCHO - gap * (cols - 1)) / cols), r0 = rectMinimapa(0, 0, w, ext), filaH = r0.h + 18;
      var x0 = M.l + (ANCHO - cols * w - (cols - 1) * gap) / 2;
      asegurar(filaH + 14);
      leyendaFigura(t('p.b.fig_cmip', { ini: CR.decada[0], fin: CR.decada[1] }));
      y += 5;
      // clases comunes por variable para que los escenarios se comparen con la misma barra
      var Cv = {};
      ['tas', 'pr'].forEach(function (vv) { var vals = []; paneles.forEach(function (p2) { if (p2.v === vv) Object.keys(p2.d).forEach(function (r) { vals.push(p2.d[r].mediana); }); }); if (vals.length) Cv[vv] = clasesSimetricas(vals); });
      paneles.forEach(function (p2, k) {
        var c = k % cols;
        if (c === 0 && k > 0) y += filaH;
        if (c === 0 && asegurar(filaH)) y += 5;
        var f = function (lon, lat, q, W, H) {
          for (var r in p2.d) if (geoms[r] && mascaraGeom(geoms[r], ext, W, H, r)[q]) return p2.d[r].mediana;
          return null;
        };
        var esc = p2.e.toUpperCase().replace(/(\d)(\d)(\d)$/, '$1-$2.$3');
        var tit = (p2.v === 'tas' ? t('p.b.cmip_tas') : t('p.b.cmip_pr')) + ' · ' + esc;
        var rect = rectMinimapa(x0 + c * (w + gap), y, w, ext);
        var P = miniCampo(rect, ext, f, Cv[p2.v], p2.v === 'pr' ? 'lluvia' : 'temp', tit, p2.v === 'tas' ? '°C' : '%');
        // rótulos con la mediana y el rango de los modelos por región
        fuente(5.2, 'bold');
        Object.keys(p2.d).forEach(function (r) {
          var f2 = reg.features.filter(function (x) { return x.properties.id === r; })[0]; if (!f2) return;
          var b = f2.properties.bbox, q = P.p((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), d = p2.d[r], dd = p2.v === 'tas' ? 2 : 1;
          var txt = sgn(d.mediana, dd) + ' (' + n(d.min, dd) + '…' + n(d.max, dd) + ')';
          color([255, 255, 255], 'f'); var tw = doc.getTextWidth(limpio(txt)) + 1.2; doc.rect(q[0] - tw / 2, q[1] - 2, tw, 2.8, 'F');
          color(COL.texto); doc.text(limpio(txt), q[0], q[1], { align: 'center' });
        });
      });
      y += filaH + 1;
      pie(t('p.b.pie_cmip', { n: paneles[0].d[Object.keys(paneles[0].d)[0]].n_modelos }) + (CR.interpolado ? ' ' + t('p.a.cmip_interp') : ''));
      return true;
    }
    function grafIndicador(rect, o) {
      var obs = o.observaciones.filter(function (x) { return x.valor !== null; }), pr = o.proyeccion, h = PV.horizonte;
      var a0 = Math.max(1981, obs[0].anio), a1 = h.fin;
      var ys = obs.map(function (x) { return x.valor; });
      pr.trayectoria.forEach(function (x) { ys.push(x.p025, x.p975); });
      var cm = o.cmip6 && o.cmip6.escenarios, escs = cm ? Object.keys(cm) : [];
      escs.forEach(function (e) { if (cm[e].proyectado_min !== null) ys.push(cm[e].proyectado_min, cm[e].proyectado_max); });
      var mn = Math.min.apply(null, ys), mx = Math.max.apply(null, ys), pad = (mx - mn) * 0.08 || 1;
      var E = ejes(rect, a0 - 0.5, a1 + 0.5, mn - pad, mx + pad, uInd(o));
      // referencia
      color([238, 238, 238], 'f'); doc.rect(E.X(PV.referencia.inicio - 0.5), rect.y, E.X(PV.referencia.fin + 0.5) - E.X(PV.referencia.inicio - 0.5), rect.h, 'F');
      // bandas 95 y 80 %
      function bandaP(kInf, kSup, col) {
        var tr = pr.trayectoria, pts = tr.map(function (x) { return [E.X(x.anio), E.Y(x[kSup])]; }).concat(tr.slice().reverse().map(function (x) { return [E.X(x.anio), E.Y(x[kInf])]; }));
        var d = []; for (var i = 1; i < pts.length; i++) d.push([pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]]);
        color(col, 'f'); doc.lines(d, pts[0][0], pts[0][1], [1, 1], 'F', true);
      }
      bandaP('p025', 'p975', [253, 224, 197]); bandaP('p10', 'p90', [250, 190, 140]);
      // observaciones
      color(COL.acento, 'd'); doc.setLineWidth(0.25);
      for (var i = 1; i < o.observaciones.length; i++) { var p0 = o.observaciones[i - 1], p1 = o.observaciones[i]; if (p0.valor !== null && p1.valor !== null && p0.anio >= a0) doc.line(E.X(p0.anio), E.Y(p0.valor), E.X(p1.anio), E.Y(p1.valor)); }
      color(COL.acento, 'f'); obs.forEach(function (x) { if (x.anio >= a0) doc.circle(E.X(x.anio), E.Y(x.valor), 0.45, 'F'); });
      // trayectoria central (estimación, discontinua)
      color([196, 90, 20], 'd'); doc.setLineWidth(0.45); doc.setLineDashPattern([1.2, 0.8], 0);
      var last = obs[obs.length - 1], prev = [E.X(last.anio), E.Y(last.valor)];
      pr.trayectoria.forEach(function (x) { var q = [E.X(x.anio), E.Y(x.p50)]; doc.line(prev[0], prev[1], q[0], q[1]); prev = q; });
      doc.setLineDashPattern([], 0);
      // corte
      color([60, 60, 60], 'd'); doc.setLineWidth(0.25); doc.setLineDashPattern([0.6, 0.6], 0); doc.line(E.X(last.anio + 0.5), rect.y, E.X(last.anio + 0.5), rect.y + rect.h); doc.setLineDashPattern([], 0);
      fuente(5.4, 'normal'); color(COL.suave); doc.text(limpio(t('p.g.corte')), E.X(last.anio + 0.5) - 0.8, rect.y + 2.4, { align: 'right' });
      // CMIP6: rango entre modelos de la media de la década (barras), por escenario
      var colE = { ssp245: [46, 125, 50], ssp585: [123, 31, 162] };
      escs.forEach(function (e, k) {
        var c = cm[e]; if (c.proyectado_min === null) return;
        var x = E.X((h.inicio + h.fin) / 2) + (k - 0.5) * 3;
        color(colE[e] || [0, 0, 0], 'd'); doc.setLineWidth(0.7); doc.line(x, E.Y(c.proyectado_min), x, E.Y(c.proyectado_max));
        doc.setLineWidth(0.3); doc.line(x - 1.2, E.Y(c.proyectado_mediana), x + 1.2, E.Y(c.proyectado_mediana));
      });
      etiquetasAnios(rect, E.X, a0, a1);
    }
    function leyendaGraf(xx, yy, conCmip) {
      fuente(5.8, 'normal');
      var items = [[COL.acento, t('p.g.obs'), 'l'], [[196, 90, 20], t('p.g.central'), 'd'], [[250, 190, 140], t('p.g.b80'), 'f'], [[253, 224, 197], t('p.g.b95'), 'f'], [[220, 220, 220], t('p.g.ref', { ini: PV.referencia.inicio, fin: PV.referencia.fin }), 'f']];
      if (conCmip) items.push([[46, 125, 50], 'CMIP6 SSP2-4.5', 'l'], [[123, 31, 162], 'CMIP6 SSP5-8.5', 'l']);
      var x = xx;
      items.forEach(function (it) {
        var w = doc.getTextWidth(limpio(it[1])) + 8;
        if (x + w > M.l + ANCHO) { x = xx; yy += 3.6; }
        if (it[2] === 'f') { color(it[0], 'f'); doc.rect(x, yy - 1.8, 5, 2.2, 'F'); }
        else { color(it[0], 'd'); doc.setLineWidth(0.5); if (it[2] === 'd') doc.setLineDashPattern([1, 0.6], 0); doc.line(x, yy - 0.7, x + 5, yy - 0.7); doc.setLineDashPattern([], 0); }
        color(COL.texto); doc.text(limpio(it[1]), x + 6, yy); x += w;
      });
      return yy + 4;
    }
    function filaHorizonte() {
      var h = PV.horizonte, inds = PV.indicadores.filter(function (o) { return o.validacion && o.validacion.suficiente; });
      var o0 = inds[0] || PV.indicadores[0];
      var ultObs = PV.indicadores.map(function (o) { return o.id + ': ' + mesTxt(o); });
      return [
        [t('p.h.generacion'), String((op.generado_utc || res.generado_utc).slice(0, 10))],
        [t('p.h.ultima_obs'), ultObs.join(' · ')],
        [t('p.h.ultimo_completo'), String(PV.ultimo_anio_completo) + (PV.ultimo_anio_completo < h.generacion - 1 ? ' · ' + t('p.h.desfase', { n: h.generacion - PV.ultimo_anio_completo }) : '')],
        [t('p.h.entrenamiento'), o0 && o0.entrenamiento ? o0.entrenamiento.join('–') : t('na')],
        [t('p.h.validacion'), o0 && o0.validacion && o0.validacion.origenes ? t('p.h.validacion_txt', { o0: o0.validacion.origenes[0], o1: o0.validacion.origenes[1], n: o0.validacion.n_origenes, ind: o0.validacion.decadas_independientes, a: o0.anticipacion_inicio, b: o0.anticipacion_inicio + 9 }) : t('na')],
        [t('p.h.proyectado'), h.inicio + '–' + h.fin + ' · ' + t('p.h.anticipacion', { a: o0 ? o0.anticipacion_inicio : '–', b: o0 ? o0.anticipacion_inicio + 9 : '–' })]
      ];
    }
    function secP() {
      if (!PV) return;
      nuevaPagina();
      banda(t('p.bloque2'));
      seccion('P');
      var h = PV.horizonte, inds = PV.indicadores;
      var dest = PV.destacadas.map(function (id) { return inds.filter(function (o) { return o.id === id; })[0]; });
      var expl = inds.filter(function (o) { return o.clasificacion.clase === 'exploratorio'; }), nop = inds.filter(function (o) { return o.clasificacion.clase === 'no_proyectable'; });
      // A. Resumen
      titular('A. ' + t('p.a'), 2);
      parrafo(t('p.a.modalidades', { cmip: PV.cmip6_fuente ? t('p.a.cmip_si', { region: PV.cmip6_fuente.nombre }) : t('p.a.cmip_no') }));
      if (dest.length) {
        parrafo(t('p.a.destacadas'), { estilo: 'bold', despues: 0.6 });
        dest.forEach(function (o) {
          var c = o.proyeccion.cambio_vs_referencia;
          parrafo('• ' + nomInd(o) + ': ' + t('p.a.dest_txt', { c: sgn(c.prediccion.p50, o.decimales), u: uInd(o), i80: rango(c.prediccion, o.decimales), ic: o.proyeccion.respuesta_media_disponible === false ? t('p.sin_respuesta') : n(c.respuesta_media.p025, o.decimales) + ' … ' + n(c.respuesta_media.p975, o.decimales), hab: n(o.validacion.modelos[o.seleccion.modelo].habilidad, 2), ref: PV.referencia.inicio + '–' + PV.referencia.fin }), { tam: 9 });
        });
      } else parrafo(t('p.a.sin_destacadas'), { estilo: 'bold' });
      parrafo(t('p.a.inciertos', { lista: expl.map(function (o) { return nomInd(o) + ' (' + t('p.motivo.' + o.clasificacion.motivo) + ')'; }).join('; ') || t('na') }), { tam: 9 });
      parrafo(t('p.a.no_proy', { lista: nop.map(nomInd).concat(PV.excluidas.map(function (e) { return idioma === 'en' ? e.nombre_en : e.nombre; })).join('; ') }), { tam: 9 });
      var cmT = inds.filter(function (o) { return o.cmip6 && o.cmip6.escenarios; })[0];
      if (cmT) {
        var e2 = cmT.cmip6.escenarios;
        parrafo(t('p.a.cmip_txt', { ind: nomInd(cmT), region: cmT.cmip6.nombre_region, a: e2.ssp245 ? sgn(e2.ssp245.cambio_mediana, 2) : t('na'), a0: e2.ssp245 ? n(e2.ssp245.cambio_min, 2) : '', a1: e2.ssp245 ? n(e2.ssp245.cambio_max, 2) : '', b: e2.ssp585 ? sgn(e2.ssp585.cambio_mediana, 2) : t('na'), b0: e2.ssp585 ? n(e2.ssp585.cambio_min, 2) : '', b1: e2.ssp585 ? n(e2.ssp585.cambio_max, 2) : '', u: e2.ssp245 ? e2.ssp245.unidad_cambio : '', nm: e2.ssp245 ? e2.ssp245.n_modelos : '' }) + (PV.cmip6_fuente && PV.cmip6_fuente.interpolado ? ' ' + t('p.a.cmip_interp') : ''), { tam: 9 });
      }
      tabla([t('p.h.dato'), t('f.valor')], filaHorizonte(), [42, 128], { titulo: t('p.h.titulo'), tam: 7.6 });
      titular(t('p.a.definiciones'), 2);
      parrafo(t('p.a.definiciones_txt', { ini: h.inicio, fin: h.fin, ref: PV.referencia.inicio + '–' + PV.referencia.fin }), { tam: 8.6 });

      // B. Mapa del área y cobertura
      nuevaPagina();
      titular('B. ' + t('p.b'), 2);
      parrafo(t('p.b.txt'), { tam: 8.8 });
      if (PV.mapas && op.mundo !== undefined) {
        rejillaMinimapas('sen_decada', t('p.b.fig_sen', { ini: 1981, fin: PV.mapas.periodo_ultimo[1] }), function (o) { return uInd(o) + '/' + (idioma === 'en' ? 'decade' : 'década'); });
        rejillaMinimapas('anomalia_ultima_decada', t('p.b.fig_anom', { a: PV.mapas.periodo_ultimo[0], b: PV.mapas.periodo_ultimo[1], ini: PV.referencia.inicio, fin: PV.referencia.fin }), function (o) { return uInd(o); });
        pie(t('p.b.pie'));
        rejillaCmipRegiones();
      } else parrafo(t('p.b.sin_mapas'), { tam: 8.6 });
      var cob = inds.map(function (o) { return [nomInd(o), o.fuente, t('p.escala.' + (o.escala || 'area')), o.historico.n_validos + '/' + o.historico.n_esperados + ' · ' + n(o.historico.faltantes_pct, 1) + ' %', t('tipo.' + (o.tipo_dato === 'observacion' ? 'observacion' : 'reanalisis'))]; });
      tabla([t('f.indicador'), t('p.c.fuente'), t('p.c.escala'), t('p.c.validos'), t('p.c.tipo')], cob, [44, 52, 26, 26, 22], { titulo: t('p.b.cobertura'), tam: 7 });

      // C. Tabla de tendencias
      nuevaPagina();
      titular('C. ' + t('p.c'), 2);
      var filas = inds.map(function (o) {
        var hh = o.historico, pr = o.proyeccion, d = o.decimales, val = o.validacion, sm = val && val.modelos && o.seleccion ? val.modelos[o.seleccion.modelo] : null;
        return [nomInd(o) + ' (' + uInd(o) + ')',
          hh.periodo.join('–') + ' (n ' + hh.n_validos + ')',
          hh.sen ? sgn(hh.sen.pendiente_decada, d + 1) + '/' + (idioma === 'en' ? 'dec.' : 'déc.') + ' [' + n(hh.sen.ic_inf_decada, d + 1) + ' … ' + n(hh.sen.ic_sup_decada, d + 1) + ']; p ' + pf(hh.mann_kendall.p_modificado) + '; q ' + pf(hh.q_bh) : t('na'),
          pr ? sgn(pr.cambio_vs_referencia.prediccion.p50, d) : t('na'),
          pr ? t('p.c.int', { i80: rango(pr.cambio_vs_referencia.prediccion, d), i95: n(pr.cambio_vs_referencia.prediccion.p025, d) + ' … ' + n(pr.cambio_vs_referencia.prediccion.p975, d) }) : '—',
          sm ? t('p.c.hab', { m: t('p.modelo.' + o.seleccion.modelo), h: n(sm.habilidad, 2), c: n(100 * sm.cobertura80, 0) }) : t('na'),
          clase(o)];
      });
      tabla([t('f.indicador'), t('p.c.periodo'), t('p.c.hist'), t('p.c.cambio', { ini: h.inicio, fin: h.fin }), t('p.c.intervalo'), t('p.c.habilidad'), t('p.c.clasif')], filas, [30, 18, 36, 16, 30, 24, 18], { titulo: t('p.c.titulo', { ini: h.inicio, fin: h.fin }), tam: 6.6 });
      pie(t('p.c.notas', { ref: PV.referencia.inicio + '–' + PV.referencia.fin, n: PV.familia_hipotesis.pruebas, sim: PV.n_simulaciones, sem: PV.semilla }));
      var fc = [];
      inds.forEach(function (o) { if (!o.cmip6) return; Object.keys(o.cmip6.escenarios).forEach(function (e) { var c = o.cmip6.escenarios[e]; fc.push([nomInd(o), e.toUpperCase().replace('SSP', 'SSP').replace(/(\d)(\d)(\d)$/, '$1-$2.$3'), String(c.n_modelos), sgn(c.cambio_mediana, 2) + ' (' + n(c.cambio_min, 2) + ' … ' + n(c.cambio_max, 2) + ') ' + c.unidad_cambio, c.proyectado_mediana === null ? t('na') : n(c.proyectado_mediana, o.decimales) + ' (' + n(c.proyectado_min, o.decimales) + ' … ' + n(c.proyectado_max, o.decimales) + ')', c.cambio_vs_referencia_mediana === undefined ? t('na') : sgn(c.cambio_vs_referencia_mediana, o.decimales) + ' ' + uInd(o), c.modelos_aumento + ' / ' + c.modelos_disminucion]); }); });
      if (fc.length) {
        tabla([t('f.indicador'), t('p.c.escenario'), 'n', t('p.c.delta'), t('p.c.proyectado', { ini: h.inicio, fin: h.fin }), t('p.c.vs_ref', { ref: PV.referencia.inicio + '–' + PV.referencia.fin }), t('p.c.signo')], fc, [32, 18, 7, 38, 34, 24, 17], { titulo: t('p.c.cmip_titulo', { region: PV.cmip6_fuente ? PV.cmip6_fuente.nombre : '' }), tam: 6.8 });
        pie(t('p.c.cmip_pie') + (PV.cmip6_fuente && PV.cmip6_fuente.interpolado ? ' ' + t('p.a.cmip_interp') : ''));
      }
      var fv = [];
      inds.forEach(function (o) { if (!o.validacion || !o.validacion.suficiente) return; Object.keys(o.validacion.modelos).forEach(function (k) { var m = o.validacion.modelos[k]; fv.push([nomInd(o), t('p.modelo.' + k) + (o.seleccion.modelo === k ? ' *' : ''), n(m.mae_decada, o.decimales + 1), n(m.rmse_decada, o.decimales + 1), sgn(m.sesgo_decada, o.decimales + 1), n(m.habilidad, 2), n(100 * m.cobertura80, 0) + ' / ' + n(100 * m.cobertura95, 0) + ' %', n(m.anchura80, o.decimales)]); }); });
      if (fv.length) {
        var v0 = inds.filter(function (o) { return o.validacion && o.validacion.suficiente; })[0].validacion;
        tabla([t('f.indicador'), t('p.v.modelo'), 'MAE', 'RMSE', t('p.v.sesgo'), t('p.v.msss'), t('p.v.cobertura'), t('p.v.anchura')], fv, [36, 30, 14, 14, 14, 14, 22, 16], { titulo: t('p.v.titulo', { o0: v0.origenes[0], o1: v0.origenes[1], n: v0.n_origenes, ind: v0.decadas_independientes }), tam: 6.4 });
        pie(t('p.v.pie'));
      }

      // D. Ficha por indicador
      nuevaPagina();
      titular('D. ' + t('p.d'), 2);
      inds.forEach(function (o) {
        var hh = o.historico, pr = o.proyeccion, d = o.decimales, f = [];
        f.push([t('p.d.mide'), idioma === 'en' ? o.que_mide_en : o.que_mide]);
        f.push([t('p.d.fuente'), o.fuente + ' · ' + hh.periodo.join('–') + ' · ' + t('tipo.' + (o.tipo_dato === 'observacion' ? 'observacion' : 'reanalisis'))]);
        f.push([t('p.d.hist'), hh.sen ? t('p.d.hist_txt', { s: sgn(hh.sen.pendiente_decada, d + 1), u: uInd(o), i0: n(hh.sen.ic_inf_decada, d + 1), i1: n(hh.sen.ic_sup_decada, d + 1), p: pf(hh.mann_kendall.p_modificado), p0: pf(hh.mann_kendall.p_sin_correccion), q: pf(hh.q_bh), c: sgn(hh.cambio_absoluto, d), sens: hh.sensibilidad.map(function (z) { return z.inicio + '–' + z.fin + ': ' + (z.pendiente_decada === null ? t('na') : sgn(z.pendiente_decada, d + 1)); }).join('; ') }) : t('na')]);
        if (pr) {
          var sm = o.validacion.modelos[o.seleccion.modelo];
          f.push([t('p.d.modelo'), t('p.modelo.' + o.seleccion.modelo) + ' · ' + t('p.sel.' + o.seleccion.motivo)]);
          f.push([t('p.d.validacion'), t('p.d.val_txt', { n: sm.n, ind: o.validacion.decadas_independientes, rmse: n(sm.rmse_decada, d + 1), rc: n(o.validacion.modelos.climatologia.rmse_decada, d + 1), h: n(sm.habilidad, 2), sesgo: sgn(sm.sesgo_decada, d + 1), c80: n(100 * sm.cobertura80, 0), c95: n(100 * sm.cobertura95, 0), u: uInd(o) })]);
          var c = pr.cambio_vs_referencia, cu = pr.cambio_vs_ultima_decada;
          f.push([t('p.d.cambio'), t('p.d.cambio_txt', { m: n(pr.media_decada.p50, d), u: uInd(o), cr: sgn(c.prediccion.p50, d), ref: PV.referencia.inicio + '–' + PV.referencia.fin, cu: sgn(cu.prediccion.p50, d), ult: cu.periodo.join('–'), pd: sgn(pr.pendiente_en_decada.p50, d + 1), pd0: n(pr.pendiente_en_decada.p10, d + 1), pd1: n(pr.pendiente_en_decada.p90, d + 1), est: c.estandarizado === null ? t('na') : sgn(c.estandarizado, 2), pct: c.porcentaje === null ? '' : ' (' + sgn(c.porcentaje, 1) + ' %)' })]);
          f.push([t('p.d.incert'), t('p.d.incert_txt', { i80: rango(c.prediccion, d), i95: n(c.prediccion.p025, d) + ' … ' + n(c.prediccion.p975, d), ic: pr.respuesta_media_disponible === false ? t('p.sin_respuesta') : n(c.respuesta_media.p025, d) + ' … ' + n(c.respuesta_media.p975, d), icu: pr.respuesta_media_disponible === false ? t('p.sin_respuesta') : n(cu.respuesta_media.p025, d) + ' … ' + n(cu.respuesta_media.p975, d), u: uInd(o), pa: n(100 * pr.prob_aumento_vs_referencia, 0), det: n(100 * pr.deteccion_10_anios, 0), cal: o.clasificacion.calibrada ? t('p.d.calibrada') : t('p.d.no_calibrada') })]);
          if (o.cmip6) f.push(['CMIP6', Object.keys(o.cmip6.escenarios).map(function (e) { var z = o.cmip6.escenarios[e]; return e + ': ' + sgn(z.cambio_mediana, 2) + ' ' + z.unidad_cambio + ' (' + n(z.cambio_min, 2) + ' … ' + n(z.cambio_max, 2) + '; ' + z.n_modelos + ' ' + (idioma === 'en' ? 'models' : 'modelos') + ')'; }).join(' · ') + ' · ' + t('p.d.cmip_base')]);
          else if (o.contraste_fisico) f.push([t('p.d.fisico'), t('p.d.fisico_txt', { esc: Object.keys(o.contraste_fisico.escenarios).map(function (e) { var z = o.contraste_fisico.escenarios[e]; return e + ' ' + z.modelos_aumento + '/' + z.n_modelos; }).join(', ') })]);
        }
        f.push([t('p.d.interp'), t('p.interp.' + o.clasificacion.clase + (o.clasificacion.motivo === 'inhomogeneidad_lluvia_merra2' ? '_lluvia' : '') + (o.clasificacion.motivo === 'contradice_proyeccion_fisica' ? '_fisica' : ''))]);
        f.push([t('p.d.factores'), t('p.d.factores_txt.' + (/lluvia|prcp|rx|r95|cdd|PREC/.test(o.id) ? 'lluvia' : 'temp'))]);
        f.push([t('p.d.clasif'), clase(o) + ' · ' + t('p.motivo.' + o.clasificacion.motivo)]);
        f.push([t('p.d.datos'), (o.enlace_datos || '') + ' · observaciones_indicadores.csv · proyecciones.csv · validacion.csv']);
        tabla([nomInd(o), ''], f, [32, 138], { tam: 7.2 });
      });

      // E. Gráficos
      nuevaPagina();
      titular('E. ' + t('p.e'), 2);
      parrafo(t('p.e.txt'), { tam: 8.6 });
      var conP = inds.filter(function (o) { return o.proyeccion; });
      var gw = (ANCHO - 22) / 2, gh = 44;
      conP.forEach(function (o, k) {
        var col = k % 2;
        if (col === 0) { if (k > 0) y += gh + 16; asegurar(gh + 26); }
        var x0 = M.l + 12 + col * (gw + 12);
        fuente(7, 'bold'); color(COL.texto);
        figura++;
        doc.text(doc.splitTextToSize(limpio((idioma === 'en' ? 'Figure ' : 'Figura ') + figura + '. ' + nomInd(o) + ' · ' + clase(o)), gw + 8).slice(0, 2), x0 - 8, y + 2);
        grafIndicador({ x: x0, y: y + 6, w: gw - 4, h: gh - 4 }, o);
      });
      if (conP.length) y += gh + 16;
      y = leyendaGraf(M.l, y + 2, inds.some(function (o) { return o.cmip6; }));
      pie(t('p.e.pie', { sim: PV.n_simulaciones, sem: PV.semilla }));

      // F. Limitaciones
      asegurar(40);
      titular('F. ' + t('p.f'), 2);
      ['variabilidad', 'modelo', 'observacion', 'externos', 'validacion', 'confianza'].forEach(function (k) { parrafo('• ' + t('p.f.' + k, { ind: inds[0] && inds[0].validacion ? inds[0].validacion.decadas_independientes : '–' }), { tam: 8.8 }); });
      if (PV.cmip6_fuente && PV.cmip6_fuente.interpolado) parrafo('• ' + t('p.a.cmip_interp'), { tam: 8.8 });
      parrafo(t('p.f.id', { id: PV.perspectiva_id, v: PV.version }), { tam: 7.5, color: COL.suave });
    }

    var mapa = { B: secB, C: secC, D: secD, E: secE, F: secF, G: secG, P: secP, H: secH };
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
