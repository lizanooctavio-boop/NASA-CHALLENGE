/*
 * Perspectiva climática de la próxima década para un área de interés.
 *
 * Dos bloques que nunca se mezclan:
 *   historico  → lo observado: Sen + Mann-Kendall modificado por autocorrelación (Hamed y Rao, 1998),
 *                MCO, sensibilidad a periodos definidos de antemano y control de comparaciones múltiples
 *                (Benjamini y Hochberg, 1995) sobre la familia de indicadores evaluados.
 *   perspectiva → extrapolación estadística validada fuera de muestra (origen móvil), comparada con la
 *                proyección climática NEX-GDDP-CMIP6 (escenarios, no pronóstico). No hay predicción decenal
 *                inicializada en la app: se declara.
 *
 * Reglas: la selección de modelo se hace por error fuera de muestra del promedio decenal frente a la
 * climatología, nunca por la pendiente ni por el ajuste al pasado. Si ningún modelo supera a la
 * climatología, el indicador es «exploratorio» y la perspectiva central es la climatología. Las
 * probabilidades solo se llaman calibradas si la cobertura retrospectiva de los intervalos lo respalda.
 * Toda simulación usa un generador con semilla registrada: el resultado es reproducible.
 */
(function (raiz, fabrica) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) module.exports = fabrica(require('../estadistica.js'), require('./estado.js'));
  else raiz.ETDPerspectiva = fabrica(raiz.SofEstadistica, raiz.ETDEstado);
})(typeof window !== 'undefined' ? window : this, function (Est, Estado) {
  'use strict';

  var VERSION = 'perspectiva-1.0.0';
  var MIN_ANIOS_PROYECCION = 30, MIN_ENTRENAMIENTO = 20, VENTANA_CLIM = 30, VENTANA_PERS = 10;
  var PERIODOS_SENSIBILIDAD = [1981, 1991, 2001];

  // ------------------------------------------------------------------ utilidades numéricas
  function r(v, d) { if (v === null || v === undefined || !isFinite(v)) return null; var f = Math.pow(10, d); return Math.round(v * f) / f; }
  function media(a) { if (!a.length) return null; var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return s / a.length; }
  function desv(a) { if (a.length < 2) return null; var m = media(a), s = 0; for (var i = 0; i < a.length; i++) s += (a[i] - m) * (a[i] - m); return Math.sqrt(s / (a.length - 1)); }
  function cuantil(ordenado, q) {
    if (!ordenado.length) return null;
    var h = (ordenado.length - 1) * q, i = Math.floor(h), f = h - i;
    return i + 1 < ordenado.length ? ordenado[i] + f * (ordenado[i + 1] - ordenado[i]) : ordenado[i];
  }
  function ordenar(a) { return a.slice().sort(function (x, y) { return x - y; }); }
  function resumen(a) {
    var o = ordenar(a);
    return { media: media(a), p025: cuantil(o, 0.025), p10: cuantil(o, 0.10), p50: cuantil(o, 0.5), p90: cuantil(o, 0.90), p975: cuantil(o, 0.975) };
  }
  function phi(z) { // normal estándar acumulada (Abramowitz-Stegun 7.1.26)
    var t = 1 / (1 + 0.3275911 * Math.abs(z) / Math.SQRT2), y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-z * z / 2);
    return z >= 0 ? (1 + y) / 2 : (1 - y) / 2;
  }

  // Generador reproducible (mulberry32) y normal por Box-Muller.
  function generador(semilla) {
    var a = semilla >>> 0, reserva = null;
    function u() { a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
    function normal() {
      if (reserva !== null) { var x = reserva; reserva = null; return x; }
      var u1 = u() || 1e-12, u2 = u(), rr = Math.sqrt(-2 * Math.log(u1));
      reserva = rr * Math.sin(2 * Math.PI * u2); return rr * Math.cos(2 * Math.PI * u2);
    }
    return { u: u, normal: normal };
  }
  function semillaDe(texto) { return parseInt(Estado.sha256(String(texto)).slice(0, 8), 16) >>> 0; }

  // ------------------------------------------------------------------ diagnóstico histórico
  function lag1(res) {
    if (res.length < 3) return 0;
    var m = media(res), num = 0, den = 0;
    for (var i = 0; i < res.length; i++) { den += (res[i] - m) * (res[i] - m); if (i) num += (res[i] - m) * (res[i - 1] - m); }
    return den > 0 ? num / den : 0;
  }

  // Mann-Kendall modificado (Hamed y Rao, 1998): corrige la varianza de S con la autocorrelación significativa
  // de los rangos de la serie sin tendencia de Sen. El factor n/n* se acota a ≥ 1: la corrección solo hace la
  // prueba más conservadora.
  function mannKendallModificado(x, y, pendienteSen) {
    var n = y.length;
    if (n < 10) return null;
    var S = 0;
    for (var i = 0; i < n - 1; i++) for (var j = i + 1; j < n; j++) { var d = y[j] - y[i]; S += d > 0 ? 1 : d < 0 ? -1 : 0; }
    var cuenta = {}, empates = 0;
    y.forEach(function (v) { cuenta[v] = (cuenta[v] || 0) + 1; });
    Object.keys(cuenta).forEach(function (k) { var t = cuenta[k]; if (t > 1) empates += t * (t - 1) * (2 * t + 5); });
    var varS = (n * (n - 1) * (2 * n + 5) - empates) / 18;
    var det = y.map(function (v, k) { return v - pendienteSen * x[k]; });
    var orden = det.map(function (v, k) { return [v, k]; }).sort(function (a, b) { return a[0] - b[0]; }), rango = new Array(n);
    orden.forEach(function (p, k) { rango[p[1]] = k + 1; });
    var mr = media(rango), den = 0, suma = 0, lim = 1.959963984540054 / Math.sqrt(n);
    for (i = 0; i < n; i++) den += (rango[i] - mr) * (rango[i] - mr);
    for (var k = 1; k < n - 2; k++) {
      var num = 0;
      for (i = k; i < n; i++) num += (rango[i] - mr) * (rango[i - k] - mr);
      var rho = num / den;
      if (Math.abs(rho) > lim) suma += (n - k) * (n - k - 1) * (n - k - 2) * rho;
    }
    var factor = Math.max(1, 1 + 2 / (n * (n - 1) * (n - 2)) * suma);
    var v = varS * factor;
    var z = S > 0 ? (S - 1) / Math.sqrt(v) : S < 0 ? (S + 1) / Math.sqrt(v) : 0;
    var zSin = S > 0 ? (S - 1) / Math.sqrt(varS) : S < 0 ? (S + 1) / Math.sqrt(varS) : 0;
    return { S: S, factor_varianza: factor, p_modificado: 2 * (1 - phi(Math.abs(z))), p_sin_correccion: 2 * (1 - phi(Math.abs(zSin))) };
  }

  // Benjamini-Hochberg: valores q para una familia de valores p (los null se ignoran).
  function benjaminiHochberg(ps) {
    var idx = [];
    ps.forEach(function (p, i) { if (p !== null && p !== undefined && isFinite(p)) idx.push(i); });
    idx.sort(function (a, b) { return ps[a] - ps[b]; });
    var m = idx.length, q = ps.map(function () { return null; }), minimo = 1;
    for (var k = m - 1; k >= 0; k--) { minimo = Math.min(minimo, ps[idx[k]] * m / (k + 1)); q[idx[k]] = Math.min(1, minimo); }
    return q;
  }

  function historico(ind, ref) {
    var x = [], y = [];
    ind.anios.forEach(function (a, i) { if (ind.valores[i] !== null && isFinite(ind.valores[i])) { x.push(a); y.push(ind.valores[i]); } });
    var esperados = ind.anios.length, faltan = esperados - x.length;
    var out = {
      periodo: [ind.anios[0], ind.anios[ind.anios.length - 1]], n_validos: x.length, n_esperados: esperados,
      faltantes_pct: esperados ? r(100 * faltan / esperados, 1) : null,
      duplicados: ind.anios.length - Object.keys(ind.anios.reduce(function (o, a) { o[a] = 1; return o; }, {})).length
    };
    if (x.length < Est.MIN_ANIOS) { out.suficiente = false; return out; }
    var o = ordenar(y);
    out.descriptivos = { media: media(y), desv: desv(y), minimo: o[0], maximo: o[o.length - 1], mediana: cuantil(o, 0.5) };
    var s = Est.sen(x, y, 0.95), m = Est.mco(x, y, 0.95);
    var mk = mannKendallModificado(x, y, s.pendiente);
    var res = y.map(function (v, i) { return v - (m.intercepto + m.pendiente * x[i]); });
    var refv = y.filter(function (v, i) { return x[i] >= ref.inicio && x[i] <= ref.fin; });
    out.suficiente = true;
    out.sen = { pendiente_decada: s.pendiente * 10, ic_inf_decada: s.ic_inf * 10, ic_sup_decada: s.ic_sup * 10, intercepto: s.intercepto };
    out.mann_kendall = mk;
    out.mco = { pendiente_decada: m.pendiente * 10, ic_inf_decada: m.ic_inf * 10, ic_sup_decada: m.ic_sup * 10, p: m.p };
    out.autocorrelacion_residuos = lag1(res);
    out.cambio_absoluto = s.pendiente * (x[x.length - 1] - x[0]);
    out.referencia = { inicio: ref.inicio, fin: ref.fin, n: refv.length, media: refv.length ? media(refv) : null, desv: desv(refv) };
    out.sensibilidad = PERIODOS_SENSIBILIDAD.map(function (a0) {
      var xx = [], yy = [];
      x.forEach(function (a, i) { if (a >= a0) { xx.push(a); yy.push(y[i]); } });
      var t = xx.length >= Est.MIN_ANIOS ? Est.sen(xx, yy, 0.95) : null;
      return { inicio: a0, fin: x[x.length - 1], n: xx.length, pendiente_decada: t ? t.pendiente * 10 : null, ic_inf_decada: t ? t.ic_inf * 10 : null, ic_sup_decada: t ? t.ic_sup * 10 : null };
    });
    var signos = out.sensibilidad.filter(function (q) { return q.pendiente_decada !== null; }).map(function (q) { return Math.sign(q.pendiente_decada); });
    out.signo_estable = signos.length > 1 && signos.every(function (v) { return v === signos[0] && v !== 0; });
    return out;
  }

  // ------------------------------------------------------------------ modelos
  // Cada modelo: ajustar(anios, valores) → { centro(a), simular(aniosFuturos, gen) → trayectoria, parametros }.
  // Las series pueden tener huecos: los modelos trabajan con los pares válidos y el AR(1) solo con años consecutivos.
  function paresDe(anios, valores) {
    var x = [], y = [];
    anios.forEach(function (a, i) { if (valores[i] !== null && isFinite(valores[i])) { x.push(a); y.push(valores[i]); } });
    return { x: x, y: y };
  }
  function ar1Consecutivo(x, res) {
    var num = 0, den = 0, n = 0;
    var m = media(res);
    for (var i = 0; i < res.length; i++) den += (res[i] - m) * (res[i] - m);
    for (i = 1; i < res.length; i++) if (x[i] - x[i - 1] === 1) { num += (res[i] - m) * (res[i - 1] - m); n++; }
    // autocorrelación de orden 1 con los pares consecutivos (los huecos no se rellenan)
    var ph = den > 0 && n > 2 ? (num / n) / (den / res.length) : 0;
    return Math.max(-0.9, Math.min(0.9, ph));
  }

  function modeloNivel(id, ventana) {
    return {
      id: id,
      ajustar: function (anios, valores) {
        var p = paresDe(anios, valores), k = Math.max(0, p.y.length - ventana);
        var yv = p.y.slice(k), xv = p.x.slice(k), mu = media(yv);
        var resTodo = p.y.map(function (v) { return v - media(p.y); });
        var ph = ar1Consecutivo(p.x, resTodo), sd = desv(p.y.slice(Math.max(0, p.y.length - VENTANA_CLIM)));
        var sigmaE = sd * Math.sqrt(1 - ph * ph), neff = yv.length * (1 - ph) / (1 + ph);
        var seMu = sd / Math.sqrt(Math.max(2, neff));
        var ultimo = p.x[p.x.length - 1], eUlt = p.y[p.y.length - 1] - mu;
        return {
          nivel: true,
          parametros: { media: mu, ventana: [xv[0], xv[xv.length - 1]], phi: ph, sigma: sd, se_media: seMu },
          centro: function (a) { return mu + Math.pow(ph, a - ultimo) * eUlt; },
          media_respuesta: function (gen) { var m = mu + seMu * gen.normal(); return function () { return m; }; },
          simular: function (futuros, gen) {
            var m = mu + seMu * gen.normal(), e = eUlt, t = ultimo, out = [];
            futuros.forEach(function (a) {
              while (t < a) { e = ph * e + sigmaE * gen.normal(); t++; }
              out.push(m + e);
            });
            return out;
          }
        };
      }
    };
  }

  // Tendencia lineal con errores AR(1): Prais-Winsten de una iteración. La incertidumbre de parámetros entra
  // en la simulación como normal bivariante; la variabilidad interanual como AR(1).
  var modeloTendenciaAR1 = {
    id: 'tendencia_ar1',
    ajustar: function (anios, valores) {
      var p = paresDe(anios, valores), x = p.x, y = p.y, n = y.length, x0 = media(x);
      function ols(X1, X2, Y) { // Y = a·X1 + b·X2
        var s11 = 0, s12 = 0, s22 = 0, s1y = 0, s2y = 0;
        for (var i = 0; i < Y.length; i++) { s11 += X1[i] * X1[i]; s12 += X1[i] * X2[i]; s22 += X2[i] * X2[i]; s1y += X1[i] * Y[i]; s2y += X2[i] * Y[i]; }
        var det = s11 * s22 - s12 * s12, a = (s22 * s1y - s12 * s2y) / det, b = (s11 * s2y - s12 * s1y) / det;
        var sse = 0; for (i = 0; i < Y.length; i++) { var e = Y[i] - a * X1[i] - b * X2[i]; sse += e * e; }
        var s2 = sse / Math.max(1, Y.length - 2);
        return { a: a, b: b, cov: [[s2 * s22 / det, -s2 * s12 / det], [-s2 * s12 / det, s2 * s11 / det]], s2: s2 };
      }
      var uno = x.map(function () { return 1; }), xc = x.map(function (v) { return v - x0; });
      var f0 = ols(uno, xc, y);
      var res0 = y.map(function (v, i) { return v - f0.a - f0.b * xc[i]; });
      var ph = ar1Consecutivo(x, res0);
      // transformación de Prais-Winsten (solo pares consecutivos; el primer dato se escala por √(1−φ²))
      var T1 = [], T2 = [], TY = [], c = Math.sqrt(1 - ph * ph);
      T1.push(c); T2.push(c * xc[0]); TY.push(c * y[0]);
      for (var i = 1; i < n; i++) {
        if (x[i] - x[i - 1] === 1) { T1.push(1 - ph); T2.push(xc[i] - ph * xc[i - 1]); TY.push(y[i] - ph * y[i - 1]); }
        else { T1.push(c); T2.push(c * xc[i]); TY.push(c * y[i]); }
      }
      // Estimación final por MCO con la incertidumbre de los parámetros inflada por la autocorrelación
      // (n efectivo, factor (1 + φ)/(1 − φ)). Prais-Winsten se conserva solo para informar la pendiente transformada.
      var fpw = ols(T1, T2, TY), f = f0, gl = Math.max(1, n - 3), sigmaM = Math.sqrt(f0.s2);
      var L11 = Math.sqrt(Math.max(f.cov[0][0], 0)), L21 = L11 > 0 ? f.cov[1][0] / L11 : 0, L22 = Math.sqrt(Math.max(f.cov[1][1] - L21 * L21, 0));
      var ultimo = x[n - 1], eUlt = y[n - 1] - f.a - f.b * xc[n - 1];
      // φ de los residuos está sesgado hacia 0 en series cortas: corrección de primer orden para simular, y se propaga
      // su incertidumbre (≈ √((1 − φ²)/n)). La varianza se extrae de su distribución (χ² con n − 3 g.l.): colas t.
      var phC = Math.max(-0.5, Math.min(0.95, ph + (2 + 4 * ph) / n)), sePh = Math.sqrt(Math.max(1 - phC * phC, 0.01) / n);
      var inflPunto = Math.max(1, (1 + Math.max(phC, 0)) / (1 - Math.max(phC, 0)));
      function draw(gen) {
        var chi = 0; for (var k = 0; k < gl; k++) { var zz = gen.normal(); chi += zz * zz; }
        var phd = Math.max(-0.5, Math.min(0.97, phC + sePh * gen.normal()));
        var esc = Math.sqrt(gl / Math.max(chi, 1e-9)), inf = Math.sqrt(Math.max(1, (1 + Math.max(phd, 0)) / (1 - Math.max(phd, 0)))), z1 = gen.normal(), z2 = gen.normal();
        return { a: f.a + esc * inf * L11 * z1, b: f.b + esc * inf * (L21 * z1 + L22 * z2), s: sigmaM * esc * Math.sqrt(1 - phd * phd), ph: phd };
      }
      return {
        parametros: { intercepto_centrado: f.a, pendiente_anual: f.b, se_pendiente: Math.sqrt(Math.max(f.cov[1][1], 0) * inflPunto), pendiente_prais_winsten: fpw.b, anio_centro: x0, phi: ph, phi_corregido: phC, sigma_residual: sigmaM, grados_libertad: gl },
        centro: function (a) { return f.a + f.b * (a - x0) + Math.pow(ph, a - ultimo) * eUlt; },
        media_respuesta: function (gen) { var d = draw(gen); return function (a) { return d.a + d.b * (a - x0); }; },
        simular: function (futuros, gen) {
          var d = draw(gen), e = eUlt, t = ultimo, out = [];
          futuros.forEach(function (a) {
            while (t < a) { e = d.ph * e + d.s * gen.normal(); t++; }
            out.push(d.a + d.b * (a - x0) + e);
          });
          return out;
        }
      };
    }
  };

  // Tendencia amortiguada (Holt con amortiguamiento, ETS(A,Ad,N)). Parámetros por mínimos cuadrados del error a un
  // paso en una rejilla fija, dentro de cada entrenamiento. La simulación propaga el modelo de espacio de estados.
  var REJILLA_HOLT = { alfa: [0.05, 0.1, 0.2, 0.3, 0.5], beta: [0.01, 0.05, 0.1], phi: [0.8, 0.9, 0.95, 0.98] };
  var modeloAmortiguado = {
    id: 'tendencia_amortiguada',
    ajustar: function (anios, valores) {
      var p = paresDe(anios, valores), y = p.y, n = y.length;
      var mejor = null;
      REJILLA_HOLT.alfa.forEach(function (al) { REJILLA_HOLT.beta.forEach(function (be) { REJILLA_HOLT.phi.forEach(function (fi) {
        var l = media(y.slice(0, Math.min(10, n))), b = 0, sse = 0, k = 0;
        for (var i = 0; i < n; i++) {
          var pr = l + fi * b, e = y[i] - pr;
          if (i >= 5) { sse += e * e; k++; }
          var lN = pr + al * e; b = fi * b + al * be * e; l = lN;
        }
        if (!mejor || sse < mejor.sse) mejor = { alfa: al, beta: be, phi: fi, sse: sse, sigma: Math.sqrt(sse / Math.max(1, k)), l: l, b: b };
      }); }); });
      var ultimo = p.x[n - 1], m = mejor;
      function trayectoria(futuros, gen) {
        var l = m.l, b = m.b, t = ultimo, out = [];
        futuros.forEach(function (a) {
          while (t < a) { var e = gen ? m.sigma * gen.normal() : 0, pr = l + m.phi * b; l = pr + m.alfa * e; b = m.phi * b + m.alfa * m.beta * e; t++; var yv = pr + e; }
          out.push(yv);
        });
        return out;
      }
      return {
        parametros: { alfa: m.alfa, beta: m.beta, phi: m.phi, sigma: m.sigma, nivel_final: m.l, pendiente_final: m.b },
        centro: function (a) { return trayectoria([a], null)[0]; },
        // Modelo de espacio de estados: no tiene una función de respuesta media comparable con los años de referencia.
        // Su contraste con la referencia se juzga solo con el intervalo predictivo (más exigente).
        sin_respuesta: true,
        simular: trayectoria
      };
    }
  };

  var MODELOS = [modeloNivel('climatologia', VENTANA_CLIM), modeloNivel('persistencia', VENTANA_PERS), modeloTendenciaAR1, modeloAmortiguado];

  // ------------------------------------------------------------------ validación retrospectiva (origen móvil)
  function validar(ind, desfase, nSim, semilla) {
    var p = paresDe(ind.anios, ind.valores), x = p.x, y = p.y;
    var porAnio = {}; x.forEach(function (a, i) { porAnio[a] = y[i]; });
    var ultimo = x[x.length - 1], primero = x[0];
    var origenes = [];
    for (var T = primero + MIN_ENTRENAMIENTO - 1; T + desfase + 9 <= ultimo; T++) origenes.push(T);
    var out = { origenes: origenes.length ? [origenes[0], origenes[origenes.length - 1]] : null, n_origenes: origenes.length,
      decadas_independientes: origenes.length ? Math.floor((origenes.length - 1) / 10) + 1 : 0, desfase: desfase, modelos: {} };
    if (origenes.length < 3) { out.suficiente = false; return out; }
    out.suficiente = true;
    MODELOS.forEach(function (M) {
      var gen = generador(semilla ^ semillaDe(M.id));
      var errDec = [], errAnual = [], dentro80 = 0, dentro95 = 0, anch80 = [], anch95 = [], nCob = 0;
      origenes.forEach(function (T) {
        var ia = [], iv = [];
        ind.anios.forEach(function (a, i) { if (a <= T) { ia.push(a); iv.push(ind.valores[i]); } });
        var obs = [], fut = [];
        for (var a = T + desfase; a <= T + desfase + 9; a++) { fut.push(a); obs.push(porAnio[a] === undefined ? null : porAnio[a]); }
        var obsV = obs.filter(function (v) { return v !== null; });
        if (obsV.length < 8) return;
        var f = M.ajustar(ia, iv);
        var centro = fut.map(function (a) { return f.centro(a); });
        var mObs = media(obsV), mPred = media(centro.filter(function (v, k) { return obs[k] !== null; }));
        errDec.push(mPred - mObs);
        obs.forEach(function (v, k) { if (v !== null) errAnual.push(centro[k] - v); });
        var sims = [];
        for (var s = 0; s < nSim; s++) {
          var tr = f.simular(fut, gen), sm = 0, c = 0;
          tr.forEach(function (v, k) { if (obs[k] !== null) { sm += v; c++; } });
          sims.push(sm / c);
        }
        var o = ordenar(sims), q10 = cuantil(o, 0.1), q90 = cuantil(o, 0.9), q025 = cuantil(o, 0.025), q975 = cuantil(o, 0.975);
        nCob++; if (mObs >= q10 && mObs <= q90) dentro80++; if (mObs >= q025 && mObs <= q975) dentro95++;
        anch80.push(q90 - q10); anch95.push(q975 - q025);
      });
      var mse = media(errDec.map(function (e) { return e * e; }));
      out.modelos[M.id] = {
        n: errDec.length, mae_decada: media(errDec.map(Math.abs)), rmse_decada: Math.sqrt(mse), sesgo_decada: media(errDec),
        mae_anual: media(errAnual.map(Math.abs)), rmse_anual: Math.sqrt(media(errAnual.map(function (e) { return e * e; }))),
        cobertura80: nCob ? dentro80 / nCob : null, cobertura95: nCob ? dentro95 / nCob : null,
        anchura80: media(anch80), anchura95: media(anch95), mse_decada: mse
      };
    });
    var ref = out.modelos.climatologia;
    Object.keys(out.modelos).forEach(function (k) {
      var m = out.modelos[k];
      m.habilidad = ref && ref.mse_decada > 0 ? 1 - m.mse_decada / ref.mse_decada : null; // MSSS frente a la climatología
    });
    return out;
  }

  function seleccionar(val) {
    if (!val.suficiente) return { modelo: 'climatologia', motivo: 'validacion_insuficiente' };
    var cands = ['climatologia', 'persistencia', 'tendencia_ar1', 'tendencia_amortiguada'].filter(function (k) { return val.modelos[k] && val.modelos[k].n; });
    // se elige el menor RMSE decenal fuera de muestra; ante empate (≤ 2 %), el modelo más simple (orden de la lista)
    var mejor = cands[0];
    cands.forEach(function (k) { if (val.modelos[k].rmse_decada < val.modelos[mejor].rmse_decada * 0.98) mejor = k; });
    return { modelo: mejor, motivo: mejor === 'climatologia' ? 'ninguno_supera_climatologia' : 'menor_rmse_fuera_de_muestra' };
  }

  // ------------------------------------------------------------------ proyección física (CMIP6)
  // cmip: { region, nombre, fuente, interpolado, series: { escenario: { modelo: { anio: valor } } }, historico: { modelo: { anio: valor } } }
  function cmipDecada(ind, cmip, h, obsRef) {
    if (!cmip || !ind.cmip_variable) return null;
    var out = { region: cmip.region, nombre_region: cmip.nombre, variable: ind.cmip_variable, metodo: ind.cmip_variable === 'pr' ? 'delta_relativo' : 'delta_aditivo',
      base: [1995, 2014], decada: [h.inicio, h.fin], interpolado: !!cmip.interpolado, escenarios: {} };
    var fuente = ind.cmip_meses && ind.cmip_meses.length < 12 ? cmip.temporada : cmip.anual;
    var datos = fuente && fuente.variables[ind.cmip_variable];
    if (!datos) return null;
    Object.keys(datos.escenarios).filter(function (esc) { return !cmip.escenarios || cmip.escenarios.indexOf(esc) >= 0; }).forEach(function (esc) {
      var deltas = [], proy = [], modelos = [];
      Object.keys(datos.escenarios[esc]).forEach(function (mod) {
        var hist = datos.historico[mod], fut = datos.escenarios[esc][mod];
        if (!hist || !fut) return;
        var hv = [], fv = [];
        for (var a = 1995; a <= 2014; a++) if (hist[a] !== undefined) hv.push(hist[a]);
        for (a = h.inicio; a <= h.fin; a++) if (fut[a] !== undefined) fv.push(fut[a]);
        if (hv.length < 18 || fv.length < 8) return;
        var mh = media(hv), mf = media(fv);
        var d = out.metodo === 'delta_relativo' ? (mf / mh - 1) : (mf - mh);
        deltas.push(d); modelos.push(mod);
        if (obsRef !== null) proy.push(out.metodo === 'delta_relativo' ? obsRef * (1 + d) : obsRef + d);
      });
      if (!deltas.length) return;
      var o = ordenar(deltas), op = ordenar(proy);
      out.escenarios[esc] = {
        n_modelos: deltas.length, modelos: modelos, cambio_mediana: cuantil(o, 0.5), cambio_min: o[0], cambio_max: o[o.length - 1],
        unidad_cambio: out.metodo === 'delta_relativo' ? '%' : ind.unidad,
        proyectado_mediana: op.length ? cuantil(op, 0.5) : null, proyectado_min: op.length ? op[0] : null, proyectado_max: op.length ? op[op.length - 1] : null,
        modelos_aumento: deltas.filter(function (d) { return d > 0; }).length, modelos_disminucion: deltas.filter(function (d) { return d < 0; }).length
      };
      if (out.metodo === 'delta_relativo') ['cambio_mediana', 'cambio_min', 'cambio_max'].forEach(function (k) { out.escenarios[esc][k] *= 100; });
    });
    out.observado_base = obsRef;
    return Object.keys(out.escenarios).length ? out : null;
  }

  // ------------------------------------------------------------------ proyección de un indicador
  // Límites físicos (porcentajes de días entre 0 y 100; lluvia y días no negativos): las trayectorias se recortan.
  function acotar(ind, tr) {
    if (ind.minimo === undefined && ind.maximo === undefined) return tr;
    return tr.map(function (v) { if (ind.minimo !== undefined && v < ind.minimo) v = ind.minimo; if (ind.maximo !== undefined && v > ind.maximo) v = ind.maximo; return v; });
  }
  function proyectar(ind, hist, sel, h, nSim, semilla, ref) {
    var p = paresDe(ind.anios, ind.valores);
    var M = MODELOS.filter(function (m) { return m.id === sel.modelo; })[0];
    var f = M.ajustar(ind.anios, ind.valores);
    var ultimo = p.x[p.x.length - 1];
    var futuros = []; for (var a = ultimo + 1; a <= h.fin; a++) futuros.push(a);
    var dec = futuros.filter(function (a) { return a >= h.inicio; });
    var gen = generador(semilla);
    var refMedia = hist.referencia.media;
    var ultDec = p.y.filter(function (v, i) { return p.x[i] > ultimo - 10; });
    var mUltDec = media(ultDec), sdRef = hist.referencia.desv;
    var medias = [], cRef = [], cUlt = [], pend = [], detect = 0, trayect = futuros.map(function () { return []; }), respuesta = [];
    var aniosRef = []; for (a = ref.inicio; a <= ref.fin; a++) aniosRef.push(a);
    var aniosUlt = p.x.filter(function (x) { return x > ultimo - 10; });
    // Respuesta media: con un modelo de tendencia es el contraste del propio modelo entre la década y la referencia
    // (la dependencia entre ambas queda dentro del contraste). Con un modelo de nivel, la media del modelo menos la
    // media observada de la referencia, que se perturba con su error típico (n efectivo por AR(1)).
    var refPh = hist.autocorrelacion_residuos || 0, nRef = hist.referencia.n || 1;
    var seRef = sdRef ? sdRef / Math.sqrt(Math.max(2, nRef * (1 - refPh) / (1 + refPh))) : 0;
    var sdUlt = desv(ultDec) || 0, seUlt = sdUlt / Math.sqrt(Math.max(2, ultDec.length * (1 - refPh) / (1 + refPh)));
    for (var s = 0; s < nSim; s++) {
      var tr = acotar(ind, f.simular(futuros, gen));
      tr.forEach(function (v, k) { trayect[k].push(v); });
      var td = tr.slice(futuros.length - dec.length), md = media(td);
      medias.push(md); cRef.push(md - refMedia); cUlt.push(md - mUltDec);
      var sen = Est.sen(dec, td, 0.95);
      pend.push(sen.pendiente * 10);
      if (sen.p < 0.05) detect++;
      if (f.sin_respuesta) continue;
      var g0 = f.media_respuesta(gen), g = function (a) { return acotar(ind, [g0(a)])[0]; };
      respuesta.push(media(dec.map(g)) - (f.nivel ? refMedia + seRef * gen.normal() : media(aniosRef.map(g))));
    }
    var cmpUlt = []; // respuesta media frente a la última década (contraste dentro del mismo modelo)
    var gen2 = generador(semilla ^ 0x9e3779b9);
    for (s = 0; s < (f.sin_respuesta ? 0 : Math.min(nSim, 2000)); s++) { var g20 = f.media_respuesta(gen2), g2 = function (a) { return acotar(ind, [g20(a)])[0]; }; cmpUlt.push(media(dec.map(g2)) - (f.nivel ? mUltDec + seUlt * gen2.normal() : media(aniosUlt.map(g2)))); }
    var rRef = resumen(cRef), rResp = resumen(respuesta), rUltR = resumen(cmpUlt);
    return {
      modelo: sel.modelo, motivo_modelo: sel.motivo, parametros: f.parametros, semilla: semilla, n_simulaciones: nSim,
      anios: futuros, trayectoria: futuros.map(function (a, k) { var q = resumen(trayect[k]); return { anio: a, central: acotar(ind, [f.centro(a)])[0], p025: q.p025, p10: q.p10, p50: q.p50, p90: q.p90, p975: q.p975 }; }),
      media_decada: resumen(medias),
      respuesta_media_disponible: !f.sin_respuesta,
      cambio_vs_referencia: { prediccion: rRef, respuesta_media: rResp, estandarizado: sdRef ? rRef.p50 / sdRef : null, porcentaje: ind.porcentual && refMedia ? 100 * rRef.p50 / refMedia : null },
      cambio_vs_ultima_decada: { periodo: [ultimo - 9, ultimo], media_observada: mUltDec, prediccion: resumen(cUlt), respuesta_media: rUltR },
      pendiente_en_decada: resumen(pend),
      deteccion_10_anios: detect / nSim,
      prob_aumento_vs_referencia: cRef.filter(function (v) { return v > 0; }).length / nSim,
      prob_supera_ultima_decada: cUlt.filter(function (v) { return v > 0; }).length / nSim
    };
  }

  function clasificar(ind, hist, val, sel, proy, cmip) {
    var c = clasificarBase(ind, hist, val, sel, proy, cmip);
    // La lluvia de MERRA-2 (POWER) tiene cambios de sistema de observación que producen tendencias espurias:
    // un indicador de lluvia de esta fuente nunca pasa de exploratorio, aunque su validación sea buena.
    if (c.clase === 'validada' && ind.homogeneidad === 'lluvia_merra2') return { clase: 'exploratorio', motivo: 'inhomogeneidad_lluvia_merra2', calibrada: c.calibrada, validacion_superada: true };
    return c;
  }
  function clasificarBase(ind, hist, val, sel, proy, cmip) {
    if (!hist.suficiente || hist.n_validos < MIN_ANIOS_PROYECCION) return { clase: 'no_proyectable', motivo: 'serie_corta' };
    if (!val.suficiente) return { clase: 'no_proyectable', motivo: 'sin_ventanas_de_validacion' };
    var m = val.modelos[sel.modelo], calibrada = m.cobertura80 !== null && m.cobertura80 >= 0.6 && m.cobertura95 >= 0.8;
    if (sel.modelo === 'climatologia') return { clase: 'exploratorio', motivo: 'sin_habilidad_frente_a_climatologia', calibrada: calibrada };
    if (m.habilidad === null || m.habilidad < 0.1) return { clase: 'exploratorio', motivo: 'habilidad_baja', calibrada: calibrada };
    if (!calibrada) return { clase: 'exploratorio', motivo: 'intervalos_mal_calibrados', calibrada: false };
    if (cmip) {
      var cr = proy.cambio_vs_referencia, signo = Math.sign(proy.respuesta_media_disponible === false ? cr.prediccion.p50 : cr.respuesta_media.p50), contra = 0, tot = 0;
      Object.keys(cmip.escenarios).forEach(function (e) { var c = cmip.escenarios[e]; tot += c.n_modelos; contra += signo > 0 ? c.modelos_disminucion : c.modelos_aumento; });
      if (tot && contra / tot >= 0.8) return { clase: 'exploratorio', motivo: 'contradice_proyeccion_fisica', calibrada: calibrada };
    }
    return { clase: 'validada', motivo: 'supera_climatologia_y_calibrada', calibrada: true };
  }

  // ------------------------------------------------------------------ evaluación completa
  /*
   * entrada: { anio_generacion, referencia {inicio, fin}, indicadores: [...], cmip6, semilla, n_sim, n_sim_validacion,
   *            excluidas: [{id, motivo}] }
   * indicador: { id, nombre, nombre_en, unidad, decimales, anios, valores, fuente, tipo_dato, origen, cmip_variable,
   *              porcentual, ultima_observacion }
   */
  function evaluar(entrada) {
    var Y = entrada.anio_generacion, ref = entrada.referencia || { inicio: 1991, fin: 2020 };
    var nSim = entrada.n_sim || 2000, nVal = entrada.n_sim_validacion || 300, semilla = entrada.semilla >>> 0;
    var h = { generacion: Y, inicio: Y + 1, fin: Y + 10 };
    var inds = entrada.indicadores.map(function (ind) {
      var p = paresDe(ind.anios, ind.valores);
      var ultimoCompleto = p.x.length ? p.x[p.x.length - 1] : null;
      var desfase = ultimoCompleto === null ? null : h.inicio - ultimoCompleto; // años de anticipación del primer año de la década
      var hist = historico(ind, ref);
      var o = { id: ind.id, nombre: ind.nombre, nombre_en: ind.nombre_en, unidad: ind.unidad, decimales: ind.decimales, fuente: ind.fuente,
        tipo_dato: ind.tipo_dato, origen: ind.origen, escala: ind.escala || 'area', homogeneidad: ind.homogeneidad || null, unidad_en: ind.unidad_en || ind.unidad, que_mide: ind.que_mide, que_mide_en: ind.que_mide_en, enlace_datos: ind.enlace_datos,
        ultima_observacion: ind.ultima_observacion || (ultimoCompleto !== null ? ultimoCompleto + '-12-31' : null),
        ultimo_anio_completo: ultimoCompleto, anticipacion_inicio: desfase, entrenamiento: p.x.length ? [p.x[0], ultimoCompleto] : null,
        observaciones: ind.anios.map(function (a, i) { return { anio: a, valor: ind.valores[i] }; }), historico: hist };
      if (!hist.suficiente || p.x.length < MIN_ANIOS_PROYECCION) { o.clasificacion = { clase: 'no_proyectable', motivo: hist.suficiente ? 'serie_corta' : 'datos_insuficientes' }; return o; }
      var sem = semilla ^ semillaDe(ind.id);
      o.validacion = validar(ind, desfase, nVal, sem);
      o.seleccion = entrada.modelo && entrada.modelo !== 'auto' ? { modelo: entrada.modelo, motivo: 'elegido_por_el_usuario' } : seleccionar(o.validacion);
      o.proyeccion = proyectar(ind, hist, o.seleccion, h, nSim, sem, ref);
      o.cmip6 = cmipDecada(ind, entrada.cmip6, h, (function () {
        var v = p.y.filter(function (vv, i) { return p.x[i] >= 1995 && p.x[i] <= 2014; });
        return v.length >= 18 ? media(v) : null;
      })());
      if (!o.cmip6 && ind.cmip_signo) {
        o.contraste_fisico = cmipDecada(Object.assign({}, ind, { cmip_variable: ind.cmip_signo, cmip_meses: null }), entrada.cmip6, h, null);
        if (o.contraste_fisico) o.contraste_fisico.solo_signo = true;
      }
      o.clasificacion = clasificar(ind, hist, o.validacion, o.seleccion, o.proyeccion, o.cmip6 || o.contraste_fisico);
      if (o.cmip6 && hist.referencia.media !== null) Object.keys(o.cmip6.escenarios).forEach(function (e) {
        var c = o.cmip6.escenarios[e];
        if (c.proyectado_mediana === null) return;
        // mismo indicador y misma referencia que el bloque estadístico, para comparar en unidades originales
        c.cambio_vs_referencia_mediana = c.proyectado_mediana - hist.referencia.media;
        c.cambio_vs_referencia_min = c.proyectado_min - hist.referencia.media;
        c.cambio_vs_referencia_max = c.proyectado_max - hist.referencia.media;
      });
      return o;
    });
    // Familia de hipótesis: una prueba de tendencia histórica (MK modificado) por indicador evaluado en esta área.
    var ps = inds.map(function (o) { return o.historico.mann_kendall ? o.historico.mann_kendall.p_modificado : null; });
    var qs = benjaminiHochberg(ps);
    inds.forEach(function (o, i) { if (o.historico.mann_kendall) o.historico.q_bh = qs[i]; });
    // Controles de las tendencias destacadas, definidos antes de ordenar.
    var destacadas = inds.filter(function (o) {
      if (!o.clasificacion || o.clasificacion.clase !== 'validada') return false;
      var cr = o.proyeccion.cambio_vs_referencia, rm = o.proyeccion.respuesta_media_disponible ? cr.respuesta_media : cr.prediccion;
      return rm.p025 > 0 || rm.p975 < 0;
    }).sort(function (a, b) {
      var ha = a.validacion.modelos[a.seleccion.modelo].habilidad, hb = b.validacion.modelos[b.seleccion.modelo].habilidad;
      var ra = (a.historico.signo_estable ? 1 : 0), rb = (b.historico.signo_estable ? 1 : 0);
      if (ra !== rb) return rb - ra;
      if (Math.abs(ha - hb) > 0.05) return hb - ha;
      return Math.abs(b.proyeccion.cambio_vs_referencia.estandarizado || 0) - Math.abs(a.proyeccion.cambio_vs_referencia.estandarizado || 0);
    }).slice(0, 10).map(function (o) { return o.id; });
    var ult = inds.map(function (o) { return o.ultimo_anio_completo; }).filter(function (v) { return v !== null; });
    var out = {
      esquema: 'etd-perspectiva', version: VERSION, horizonte: h, referencia: ref, semilla: semilla, n_simulaciones: nSim, n_simulaciones_validacion: nVal,
      ultimo_anio_completo: ult.length ? Math.min.apply(null, ult) : null,
      modalidades: { extrapolacion_estadistica: true, proyeccion_climatica: !!entrada.cmip6, prediccion_decenal_inicializada: false },
      familia_hipotesis: { pruebas: ps.filter(function (p) { return p !== null; }).length, metodo: 'benjamini_hochberg', alfa: 0.05 },
      indicadores: inds, destacadas: destacadas, excluidas: entrada.excluidas || [], mapas: entrada.mapas || null,
      cmip6_fuente: entrada.cmip6 ? { region: entrada.cmip6.region, nombre: entrada.cmip6.nombre, interpolado: !!entrada.cmip6.interpolado, archivo: entrada.cmip6.archivo, modelos: entrada.cmip6.modelos } : null
    };
    out.perspectiva_id = 'P-' + Estado.sha256(Estado.canonico(redondearTodo(out))).slice(0, 32);
    return out;
  }

  // Redondeo para el hash y el JSON: evita que diferencias de coma flotante del motor cambien el identificador.
  function redondearTodo(o) {
    if (Array.isArray(o)) return o.map(redondearTodo);
    if (o && typeof o === 'object') { var c = {}; Object.keys(o).forEach(function (k) { if (k !== 'perspectiva_id' && typeof o[k] !== 'function') c[k] = redondearTodo(o[k]); }); return c; }
    if (typeof o === 'number') return isFinite(o) ? Math.round(o * 1e6) / 1e6 : null;
    return o;
  }
  function verificar(p) { return !!p && p.esquema === 'etd-perspectiva' && p.perspectiva_id === 'P-' + Estado.sha256(Estado.canonico(redondearTodo(p))).slice(0, 32); }

  // ------------------------------------------------------------------ insumos: índices por celda y CMIP6
  var INDICES = {
    t2m_media: { nombre: 'Temperatura media anual', nombre_en: 'Annual mean temperature', unidad: '°C', decimales: 2, cmip: 'tas', que: 'Media anual de la temperatura del aire a 2 m.', que_en: 'Annual mean 2 m air temperature.' },
    tmax_media: { signo: 'tas', nombre: 'Temperatura máxima media', nombre_en: 'Mean daily maximum temperature', unidad: '°C', decimales: 2, que: 'Promedio anual de la máxima diaria.', que_en: 'Annual mean of the daily maximum.' },
    tmin_media: { signo: 'tas', nombre: 'Temperatura mínima media', nombre_en: 'Mean daily minimum temperature', unidad: '°C', decimales: 2, que: 'Promedio anual de la mínima diaria.', que_en: 'Annual mean of the daily minimum.' },
    tx90p: { signo: 'tas', nombre: 'Días cálidos (TX90p)', nombre_en: 'Warm days (TX90p)', unidad: '% de días', unidad_en: '% of days', decimales: 1, que: 'Porcentaje de días con máxima por encima del percentil 90 diario de 1991–2020.', que_en: 'Share of days with maximum above the 1991–2020 daily 90th percentile.' },
    tn90p: { signo: 'tas', nombre: 'Noches cálidas (TN90p)', nombre_en: 'Warm nights (TN90p)', unidad: '% de días', unidad_en: '% of days', decimales: 1, que: 'Porcentaje de días con mínima por encima del percentil 90 diario de 1991–2020.', que_en: 'Share of days with minimum above the 1991–2020 daily 90th percentile.' },
    prcptot: { homog: 'lluvia_merra2', nombre: 'Lluvia anual (días ≥ 1 mm)', nombre_en: 'Annual rainfall (days ≥ 1 mm)', unidad: 'mm', decimales: 0, cmip: 'pr', porcentual: true, que: 'Suma anual de la lluvia de los días con al menos 1 mm.', que_en: 'Annual total of rainfall on days with at least 1 mm.' },
    rx1day: { homog: 'lluvia_merra2', nombre: 'Lluvia máxima en un día (Rx1day)', nombre_en: 'Maximum 1-day rainfall (Rx1day)', unidad: 'mm', decimales: 1, porcentual: true, que: 'El aguacero diario más fuerte del año.', que_en: 'Largest daily rainfall of the year.' },
    rx5day: { homog: 'lluvia_merra2', nombre: 'Lluvia máxima en 5 días (Rx5day)', nombre_en: 'Maximum 5-day rainfall (Rx5day)', unidad: 'mm', decimales: 1, porcentual: true, que: 'Mayor acumulado de 5 días seguidos en el año.', que_en: 'Largest 5-day total of the year.' },
    r95p: { homog: 'lluvia_merra2', nombre: 'Lluvia de días muy húmedos (R95p)', nombre_en: 'Very wet day rainfall (R95p)', unidad: 'mm', decimales: 0, porcentual: true, que: 'Lluvia de los días por encima del percentil 95 de los días húmedos de 1991–2020.', que_en: 'Rainfall on days above the 1991–2020 wet-day 95th percentile.' },
    cdd: { homog: 'lluvia_merra2', nombre: 'Racha seca más larga (CDD)', nombre_en: 'Longest dry spell (CDD)', unidad: 'días', unidad_en: 'days', decimales: 0, que: 'Máximo de días seguidos con menos de 1 mm.', que_en: 'Maximum number of consecutive days below 1 mm.' }
  };

  // CSV de índices anuales por celda (data/fenomenos/indices_anuales_celdas.csv) → {celda 'lat,lon': {indice: {anio: valor}}}
  function leerIndicesCeldas(texto) {
    var lineas = texto.trim().split(/\r?\n/), cab = lineas[0].split(','), out = {};
    for (var i = 1; i < lineas.length; i++) {
      var c = lineas[i].split(','), clave = Number(c[0]).toFixed(3) + ',' + Number(c[1]).toFixed(3), anio = Number(c[2]);
      var cel = out[clave] = out[clave] || {};
      for (var k = 3; k < cab.length; k++) { var v = c[k] === '' ? null : Number(c[k]); (cel[cab[k]] = cel[cab[k]] || {})[anio] = isFinite(v) ? v : null; }
    }
    return out;
  }

  // Media ponderada por superficie de intersección de los índices de cada celda del área (mismos pesos que el expediente).
  function indicadoresDeArea(celdas, indicesCeldas, minCobertura) {
    var claves = celdas.map(function (c) { return Number(c.lat).toFixed(3) + ',' + Number(c.lon).toFixed(3); });
    var pesoTotal = celdas.reduce(function (s, c) { return s + c.peso; }, 0), pesoDisp = 0;
    celdas.forEach(function (c, i) { if (indicesCeldas[claves[i]]) pesoDisp += c.peso; });
    var cobertura = pesoTotal ? pesoDisp / pesoTotal : 0;
    if (cobertura < (minCobertura || 0.9)) return { cobertura: cobertura, indicadores: [] };
    var anios = {};
    celdas.forEach(function (c, i) { var t = indicesCeldas[claves[i]]; if (t && t.t2m_media) Object.keys(t.t2m_media).forEach(function (a) { anios[a] = 1; }); });
    anios = Object.keys(anios).map(Number).sort(function (a, b) { return a - b; });
    var inds = Object.keys(INDICES).map(function (id) {
      var meta = INDICES[id];
      var valores = anios.map(function (a) {
        var s = 0, w = 0;
        celdas.forEach(function (c, i) { var t = indicesCeldas[claves[i]]; if (!t || !t[id]) return; var v = t[id][a]; if (v === null || v === undefined) return; s += v * c.peso; w += c.peso; });
        return w >= (minCobertura || 0.9) * pesoTotal ? s / w : null;
      });
      return { id: id, nombre: meta.nombre, nombre_en: meta.nombre_en, unidad: meta.unidad, unidad_en: meta.unidad_en || meta.unidad, decimales: meta.decimales,
        anios: anios, valores: valores, cmip_variable: meta.cmip || null, cmip_signo: meta.signo || null, homogeneidad: meta.homog || null,
        porcentual: !!meta.porcentual, minimo: meta.minimo, maximo: meta.maximo, que_mide: meta.que, que_mide_en: meta.que_en,
        fuente: 'NASA POWER diario (MERRA-2), índices ETCCDI por celda', tipo_dato: 'reanalisis', origen: 'indices_celdas',
        enlace_datos: 'data/fenomenos/indices_anuales_celdas.csv' };
    });
    return { cobertura: cobertura, indicadores: inds };
  }

  // Indicador a partir de la serie anual (o de temporada) del propio expediente.
  function indicadorDeConsulta(res, idioma) {
    var v = res.variable, meses = res.consulta.meses;
    var anual = meses.length === 12;
    return {
      id: 'consulta_' + v.id + (anual ? '' : '_m' + meses.join('-')),
      nombre: v.nombre + (anual ? '' : ' (meses ' + meses.join(', ') + ')'), nombre_en: v.nombre_en + (anual ? '' : ' (months ' + meses.join(', ') + ')'),
      unidad: v.unidad, decimales: v.decimales,
      anios: res.serie.map(function (p) { return p.anio; }), valores: res.serie.map(function (p) { return p.valor; }),
      cmip_variable: v.id === 'T2M' ? 'tas' : v.id === 'PRECTOTCORR' ? 'pr' : null, cmip_meses: meses, porcentual: v.id === 'PRECTOTCORR',
      homogeneidad: v.id === 'PRECTOTCORR' ? 'lluvia_merra2' : null, minimo: v.id === 'PRECTOTCORR' ? 0 : undefined,
      que_mide: 'Variable y temporada de esta consulta, agregadas sobre el área (mismo cálculo que el bloque histórico).',
      que_mide_en: 'This query\'s variable and season, aggregated over the area (same computation as the historical block).',
      fuente: 'NASA POWER mensual (MERRA-2)', tipo_dato: 'reanalisis', origen: 'consulta', enlace_datos: 'serie_temporal.csv',
      ultima_observacion: ultimaObservacion(res)
    };
  }
  function ultimaObservacion(res) {
    var m = res.mensual.filter(function (x) { return x.valor !== null; });
    if (!m.length) return null;
    var u = m[m.length - 1];
    return u.anio + '-' + (u.mes < 10 ? '0' : '') + u.mes;
  }

  // CSV mensual CMIP6 regional → estructura por variable/escenario/modelo/año (media anual o de los meses pedidos).
  function leerCmip6(texto, region, meses) {
    var lineas = texto.trim().split(/\r?\n/), cab = lineas[0].split(','), ix = {};
    cab.forEach(function (c, i) { ix[c] = i; });
    var acum = {};
    for (var i = 1; i < lineas.length; i++) {
      var c = lineas[i].split(',');
      if (c[ix.region] !== region) continue;
      var mes = Number(c[ix.mes]);
      if (meses && meses.indexOf(mes) < 0) continue;
      var k = [c[ix.variable], c[ix.escenario], c[ix.modelo], c[ix.anio]].join('|');
      (acum[k] = acum[k] || []).push(Number(c[ix.valor]));
    }
    var out = { variables: {}, modelos: {} };
    var nMeses = meses ? meses.length : 12;
    Object.keys(acum).forEach(function (k) {
      var p = k.split('|'), vals = acum[k];
      if (vals.length !== nMeses) return;
      var v = p[0] === 'pr' ? vals.reduce(function (s, x) { return s + x; }, 0) : media(vals);
      var V = out.variables[p[0]] = out.variables[p[0]] || { historico: {}, escenarios: {} };
      out.modelos[p[2]] = 1;
      if (p[1] === 'historical') (V.historico[p[2]] = V.historico[p[2]] || {})[p[3]] = v;
      else ((V.escenarios[p[1]] = V.escenarios[p[1]] || {})[p[2]] = V.escenarios[p[1]][p[2]] || {})[p[3]] = v;
    });
    out.modelos = Object.keys(out.modelos).sort();
    return out;
  }

  // Sin años 2015–2040 descargados: cambio de cada modelo interpolado linealmente en el tiempo entre 1995–2014 y
  // 2041–2060 (centros 2004,5 y 2050,5). Es una aproximación y se declara como tal.
  function interpolarCmip6(c, inicio, fin) {
    var f = ((inicio + fin) / 2 - 2004.5) / (2050.5 - 2004.5);
    Object.keys(c.variables).forEach(function (v) {
      var V = c.variables[v];
      Object.keys(V.escenarios).forEach(function (e) {
        Object.keys(V.escenarios[e]).forEach(function (m) {
          var fut = V.escenarios[e][m], hist = V.historico[m];
          if (!hist) return;
          var hv = [], fv = [];
          for (var a = 1995; a <= 2014; a++) if (hist[a] !== undefined) hv.push(hist[a]);
          for (a = 2041; a <= 2060; a++) if (fut[a] !== undefined) fv.push(fut[a]);
          if (!hv.length || !fv.length) return;
          var mh = media(hv), mf = media(fv), val = mh + f * (mf - mh);
          if (Object.keys(fut).some(function (k) { return k >= inicio && k <= fin; })) return;
          for (a = inicio; a <= fin; a++) fut[a] = val;
        });
      });
    });
    c.interpolado = true;
    return c;
  }

  // Minimapas: valores reales por celda de la malla de índices alrededor del área (tendencia de Sen y anomalía de la
  // última década frente a la referencia). Solo se dibuja lo que la malla resuelve: 0,5° × 0,625°.
  function mapasCeldas(indicesCeldas, celdasArea, ext, ref) {
    // Ámbito nacional: toda la malla de índices (Nicaragua), para dibujar campos continuos como los mapas de la OMM o
    // del IDEAM. El área consultada se dibuja encima; si queda fuera de la malla no hay minimapas.
    var e = ext.slice(); if (e[2] < e[0]) e[2] += 360;
    var enArea = {}; celdasArea.forEach(function (c) { enArea[Number(c.lat).toFixed(3) + ',' + Number(c.lon).toFixed(3)] = c.peso; });
    var claves = Object.keys(indicesCeldas);
    if (!claves.length) return null;
    var pts = claves.map(function (k) { return k.split(',').map(Number); });
    var la0 = Math.min.apply(null, pts.map(function (p) { return p[0]; })), la1 = Math.max.apply(null, pts.map(function (p) { return p[0]; }));
    var lo0 = Math.min.apply(null, pts.map(function (p) { return p[1]; })), lo1 = Math.max.apply(null, pts.map(function (p) { return p[1]; }));
    if (e[2] < lo0 - 1 || e[0] > lo1 + 1 || e[3] < la0 - 1 || e[1] > la1 + 1) return null;
    var v = [Math.min(lo0 - 0.45, e[0] - 0.1), Math.min(la0 - 0.4, e[1] - 0.1), Math.max(lo1 + 0.45, e[2] + 0.1), Math.max(la1 + 0.4, e[3] + 0.1)];
    var ultimo = 0;
    claves.forEach(function (k) { var t = indicesCeldas[k].t2m_media || {}; Object.keys(t).forEach(function (a) { if (t[a] !== null) ultimo = Math.max(ultimo, Number(a)); }); });
    var out = { ambito: 'nacional', ventana: v, rejilla: { dlat: 0.5, dlon: 0.625 }, periodo_ultimo: [ultimo - 9, ultimo], referencia: [ref.inicio, ref.fin],
      celdas: claves.map(function (k) { var p = k.split(',').map(Number); return { lat: p[0], lon: p[1], peso_area: enArea[k] || 0 }; }), indicadores: {} };
    Object.keys(INDICES).forEach(function (id) {
      var sen = [], anom = [];
      claves.forEach(function (k) {
        var serie = indicesCeldas[k][id] || {}, x = [], y = [], r = [], u = [];
        Object.keys(serie).forEach(function (a) { var val = serie[a]; a = Number(a); if (val === null) return; x.push(a); y.push(val); if (a >= ref.inicio && a <= ref.fin) r.push(val); if (a > ultimo - 10) u.push(val); });
        var t = x.length >= 30 ? Est.sen(x, y, 0.95) : null;
        sen.push(t ? t.pendiente * 10 : null);
        anom.push(r.length >= 24 && u.length >= 8 ? media(u) - media(r) : null);
      });
      out.indicadores[id] = { sen_decada: sen, anomalia_ultima_decada: anom };
    });
    return out;
  }

  // Cambio CMIP6 de la década por región (mediana, mínimo y máximo de los modelos) para los minimapas regionales.
  // Mismo método delta que cmipDecada: tas aditivo (°C) y pr relativo (%), frente a 1995–2014.
  function cmipRegiones(texto, regiones, h, escenarios) {
    if (!texto || !regiones || !regiones.length) return null;
    var out = { base: [1995, 2014], decada: [h.inicio, h.fin], interpolado: false, escenarios: {} };
    regiones.forEach(function (rg) {
      var c = leerCmip6(texto, rg.id, null);
      var tiene = Object.keys(c.variables).some(function (vv) { return Object.keys(c.variables[vv].escenarios).some(function (e) { return Object.keys(c.variables[vv].escenarios[e]).some(function (m) { return c.variables[vv].escenarios[e][m][h.inicio] !== undefined; }); }); });
      if (!tiene) { interpolarCmip6(c, h.inicio, h.fin); out.interpolado = true; }
      ['tas', 'pr'].forEach(function (vv) {
        var d = cmipDecada({ cmip_variable: vv, unidad: vv === 'tas' ? '°C' : 'mm' }, { region: rg.id, nombre: rg.nombre, anual: c, escenarios: escenarios || null }, h, null);
        if (!d) return;
        Object.keys(d.escenarios).forEach(function (e) {
          var x = d.escenarios[e], E = out.escenarios[e] = out.escenarios[e] || {}, V = E[vv] = E[vv] || {};
          V[rg.id] = { nombre: rg.nombre, mediana: x.cambio_mediana, min: x.cambio_min, max: x.cambio_max, n_modelos: x.n_modelos, unidad: x.unidad_cambio, modelos_aumento: x.modelos_aumento, modelos_disminucion: x.modelos_disminucion };
        });
      });
    });
    return Object.keys(out.escenarios).length ? out : null;
  }

  // GISTEMP v4 (250 km) por región: anomalía anual (base 1951–1980) solo con los 12 meses presentes.
  function indicadorGistemp(texto, region, nombreRegion) {
    var lineas = texto.trim().split(/\r?\n/), cab = lineas[0].split(','), col = cab.indexOf(region);
    if (col < 0) return null;
    var porAnio = {};
    for (var i = 1; i < lineas.length; i++) {
      var c = lineas[i].split(','), a = Number(c[0]), v = c[col] === '' ? null : Number(c[col]);
      (porAnio[a] = porAnio[a] || []).push(isFinite(v) ? v : null);
    }
    var anios = Object.keys(porAnio).map(Number).filter(function (a) { return a >= 1981; }).sort(function (a, b) { return a - b; });
    var valores = anios.map(function (a) { var m = porAnio[a]; return m.length === 12 && m.every(function (v) { return v !== null; }) ? media(m) : null; });
    return { id: 'gistemp_' + region, nombre: 'Anomalía de temperatura observada (GISTEMP v4, ' + nombreRegion + ')', nombre_en: 'Observed temperature anomaly (GISTEMP v4, ' + nombreRegion + ')',
      unidad: '°C', decimales: 2, anios: anios, valores: valores, cmip_variable: 'tas', escala: 'region',
      que_mide: 'Anomalía anual de temperatura de superficie respecto de 1951–1980, de estaciones interpoladas a 250 km; escala regional, no la del área.',
      que_mide_en: 'Annual surface temperature anomaly vs 1951–1980 from stations interpolated at 250 km; regional scale, not the area scale.',
      fuente: 'NASA GISS GISTEMP v4 (gistemp250_GHCNv4)', tipo_dato: 'observacion', origen: 'gistemp', enlace_datos: 'data/fenomenos/gistemp_nicaragua.csv' };
  }

  // Variables pedidas que esta versión no proyecta, con su motivo (se listan siempre para evitar sesgo de selección).
  ['prcptot', 'rx1day', 'rx5day', 'r95p', 'cdd', 'tx90p', 'tn90p'].forEach(function (id) { INDICES[id].minimo = 0; });
  ['tx90p', 'tn90p'].forEach(function (id) { INDICES[id].maximo = 100; });
  var EXCLUIDAS = [
    { id: 'olas_calor', nombre: 'Duración y frecuencia de olas de calor', nombre_en: 'Heatwave duration and frequency', motivo: 'Requiere la serie diaria por celda dentro de la app; los índices anuales disponibles (TX90p, TN90p) cubren el calor extremo, no las rachas.', motivo_en: 'Needs the daily series per cell inside the app; the available annual indices (TX90p, TN90p) cover hot extremes, not spells.' },
    { id: 'spi', nombre: 'Sequía (SPI/SPEI)', nombre_en: 'Drought (SPI/SPEI)', motivo: 'No implementado en esta versión: exige ajustar una distribución a la lluvia mensual y la lluvia MERRA-2 de POWER tiene inhomogeneidades conocidas. La racha seca (CDD) se evalúa como indicador de sequía meteorológica.', motivo_en: 'Not implemented in this version: it needs a distribution fitted to monthly rainfall and POWER MERRA-2 rainfall has known inhomogeneities. The dry spell (CDD) is evaluated as a meteorological drought indicator.' },
    { id: 'tsm', nombre: 'Temperatura superficial del mar y olas de calor marinas', nombre_en: 'Sea surface temperature and marine heatwaves', motivo: 'El área es terrestre y la app no tiene una serie de TSM a la escala del área; los índices oceánicos (Niño 3.4, TNA) son de cuenca.', motivo_en: 'The area is on land and the app has no SST series at the area scale; ocean indices (Niño 3.4, TNA) are basin-wide.' },
    { id: 'nivel_mar', nombre: 'Nivel del mar', nombre_en: 'Sea level', motivo: 'Sin datos de mareógrafo o altimetría para el área en la app.', motivo_en: 'No tide gauge or altimetry data for the area in the app.' },
    { id: 'lagos', nombre: 'Niveles de lagos y almacenamiento de agua', nombre_en: 'Lake levels and water storage', motivo: 'Dependen del balance hídrico, la gestión y las extracciones; no se extrapolan sin un modelo hidrológico.', motivo_en: 'They depend on the water balance, management and withdrawals; they are not extrapolated without a hydrological model.' },
    { id: 'vegetacion', nombre: 'Vegetación, humedad del suelo e incendios', nombre_en: 'Vegetation, soil moisture and fires', motivo: 'Sin serie por área ni modelo justificable en la app; los incendios individuales no son predecibles a diez años.', motivo_en: 'No area series or justifiable model in the app; individual fires are not predictable ten years ahead.' },
    { id: 'canicula', nombre: 'Canícula', nombre_en: 'Mid-summer drought (canícula)', motivo: 'Requiere lluvia diaria por área y una definición regional explícita (fechas de inicio y fin); no se calcula por celda en esta versión.', motivo_en: 'Needs daily rainfall per area and an explicit regional definition (onset and end dates); not computed per cell in this version.' },
    { id: 'huracanes', nombre: 'Trayectorias de huracanes y eventos individuales', nombre_en: 'Hurricane tracks and individual events', motivo: 'No son predecibles a diez años; no se intentan.', motivo_en: 'Not predictable ten years ahead; not attempted.' }
  ];

  return {
    VERSION: VERSION, INDICES: INDICES, EXCLUIDAS: EXCLUIDAS, MODELOS: MODELOS.map(function (m) { return m.id; }), ajustarModelo: function (id, anios, valores) { return MODELOS.filter(function (m) { return m.id === id; })[0].ajustar(anios, valores); },
    evaluar: evaluar, verificar: verificar, historico: historico, validar: validar, mannKendallModificado: mannKendallModificado,
    benjaminiHochberg: benjaminiHochberg, generador: generador, semillaDe: semillaDe,
    leerIndicesCeldas: leerIndicesCeldas, indicadoresDeArea: indicadoresDeArea, indicadorDeConsulta: indicadorDeConsulta,
    leerCmip6: leerCmip6, indicadorGistemp: indicadorGistemp, mapasCeldas: mapasCeldas, cmipRegiones: cmipRegiones, interpolarCmip6: interpolarCmip6, redondearTodo: redondearTodo
  };
});
