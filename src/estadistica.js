/*
 * Estadística de tendencias para la demo climática.
 * - Mínimos cuadrados ordinarios (MCO) con intervalo t al 95 %.
 * - Pendiente de Theil-Sen con intervalo basado en la varianza de Mann-Kendall (Sen, 1968).
 * - Veredicto que distingue «evidencia insuficiente» de «los métodos discrepan».
 *
 * Sin dependencias. Funciona en el navegador (window.SofEstadistica) y en Node (module.exports).
 * Ninguno de los dos métodos corrige la autocorrelación de la serie; se indica en la interfaz.
 */
(function (raiz) {
  'use strict';

  var MIN_ANIOS = 10; // por debajo de esto no se calcula tendencia

  // ---------- funciones especiales ----------
  function lnGamma(x) {
    var c = [76.18009172947146, -86.50532032941677, 24.01409824083091,
      -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    var y = x, tmp = x + 5.5;
    tmp -= (x + 0.5) * Math.log(tmp);
    var ser = 1.000000000190015;
    for (var j = 0; j < 6; j++) ser += c[j] / ++y;
    return -tmp + Math.log(2.5066282746310005 * ser / x);
  }

  function betacf(a, b, x) {
    var MAXIT = 200, EPS = 3e-14, FPMIN = 1e-300;
    var qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    d = 1 / d;
    var h = d;
    for (var m = 1; m <= MAXIT; m++) {
      var m2 = 2 * m;
      var aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d;
      var del = d * c; h *= del;
      if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  }

  function betaInc(a, b, x) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    var bt = Math.exp(lnGamma(a + b) - lnGamma(a) - lnGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(a, b, x) / a;
    return 1 - bt * betacf(b, a, 1 - x) / b;
  }

  // P(|T| > |t|) para t de Student con gl grados de libertad
  function pBilateralT(t, gl) {
    return betaInc(gl / 2, 0.5, gl / (gl + t * t));
  }

  // cuantil t (bilateral): t tal que P(|T| > t) = alfa
  function cuantilT(alfa, gl) {
    var lo = 0, hi = 100;
    for (var i = 0; i < 200; i++) {
      var mid = (lo + hi) / 2;
      if (pBilateralT(mid, gl) > alfa) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  // CDF normal estándar (Abramowitz-Stegun 7.1.26 vía erf)
  function phi(z) {
    var t = 1 / (1 + 0.3275911 * Math.abs(z) / Math.SQRT2);
    var y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-z * z / 2);
    return z >= 0 ? 0.5 * (1 + y) : 0.5 * (1 - y);
  }

  // ---------- utilidades ----------
  function paresValidos(serie) {
    var x = [], y = [];
    (serie || []).forEach(function (p) {
      if (p && isFinite(p.anio) && p.valor !== null && p.valor !== undefined && isFinite(p.valor)) {
        x.push(Number(p.anio)); y.push(Number(p.valor));
      }
    });
    return { x: x, y: y };
  }

  function media(a) { return a.reduce(function (s, v) { return s + v; }, 0) / a.length; }

  // ---------- MCO ----------
  function mco(x, y, nivel) {
    var n = x.length;
    if (n < MIN_ANIOS) return null;
    var mx = media(x), my = media(y), sxx = 0, sxy = 0;
    for (var i = 0; i < n; i++) { sxx += (x[i] - mx) * (x[i] - mx); sxy += (x[i] - mx) * (y[i] - my); }
    var b = sxy / sxx, a = my - b * mx, sse = 0;
    for (i = 0; i < n; i++) { var r = y[i] - (a + b * x[i]); sse += r * r; }
    var gl = n - 2, se = Math.sqrt(sse / gl / sxx);
    var tc = cuantilT(1 - nivel, gl);
    return {
      metodo: 'mco', pendiente: b, intercepto: a,
      ic_inf: b - tc * se, ic_sup: b + tc * se,
      p: se > 0 ? pBilateralT(b / se, gl) : 0, n: n
    };
  }

  // ---------- Theil-Sen + Mann-Kendall ----------
  function sen(x, y, nivel) {
    var n = x.length;
    if (n < MIN_ANIOS) return null;
    var pend = [], S = 0;
    for (var i = 0; i < n - 1; i++) {
      for (var j = i + 1; j < n; j++) {
        if (x[j] !== x[i]) pend.push((y[j] - y[i]) / (x[j] - x[i]));
        var d = y[j] - y[i];
        S += d > 0 ? 1 : d < 0 ? -1 : 0;
      }
    }
    pend.sort(function (a, b) { return a - b; });
    var N = pend.length;
    var b = N % 2 ? pend[(N - 1) / 2] : (pend[N / 2 - 1] + pend[N / 2]) / 2;
    // varianza de S con corrección por empates
    var cuenta = {};
    y.forEach(function (v) { cuenta[v] = (cuenta[v] || 0) + 1; });
    var empates = 0;
    Object.keys(cuenta).forEach(function (k) { var t = cuenta[k]; if (t > 1) empates += t * (t - 1) * (2 * t + 5); });
    var varS = (n * (n - 1) * (2 * n + 5) - empates) / 18;
    var z = S > 0 ? (S - 1) / Math.sqrt(varS) : S < 0 ? (S + 1) / Math.sqrt(varS) : 0;
    var zc = 1.959963984540054; // 95 %
    if (nivel !== 0.95) { // búsqueda simple del cuantil normal
      var lo = 0, hi = 10;
      for (var k = 0; k < 100; k++) { var m = (lo + hi) / 2; if (2 * (1 - phi(m)) > 1 - nivel) lo = m; else hi = m; }
      zc = (lo + hi) / 2;
    }
    var C = zc * Math.sqrt(varS);
    var M1 = Math.round((N - C) / 2), M2 = Math.round((N + C) / 2);
    var inf = pend[Math.max(0, Math.min(N - 1, M1 - 1))];
    var sup = pend[Math.max(0, Math.min(N - 1, M2))];
    var mx = x.slice().sort(function (a, c) { return a - c; }), my = y.slice().sort(function (a, c) { return a - c; });
    var medx = n % 2 ? mx[(n - 1) / 2] : (mx[n / 2 - 1] + mx[n / 2]) / 2;
    var medy = n % 2 ? my[(n - 1) / 2] : (my[n / 2 - 1] + my[n / 2]) / 2;
    return {
      metodo: 'sen', pendiente: b, intercepto: medy - b * medx,
      ic_inf: inf, ic_sup: sup, p: 2 * (1 - phi(Math.abs(z))), n: n
    };
  }

  // ---------- veredicto ----------
  function excluyeCero(t) { return t && (t.ic_inf > 0 || t.ic_sup < 0); }
  function signo(t) { return t.pendiente > 0 ? 1 : t.pendiente < 0 ? -1 : 0; }

  /*
   * Estados:
   *  'faltan'       → no hay datos suficientes para calcular (menos de MIN_ANIOS años válidos o sin tendencias)
   *  'insuficiente' → ambos intervalos incluyen el cero: no se puede afirmar una tendencia
   *  'discrepan'    → un método excluye el cero y el otro no, o ambos lo excluyen con signo opuesto
   *  'aumento' / 'disminucion' → ambos métodos excluyen el cero con el mismo signo
   */
  function veredicto(tMco, tSen) {
    if (!tMco || !tSen) return { estado: 'faltan' };
    var a = excluyeCero(tMco), b = excluyeCero(tSen);
    if (!a && !b) return { estado: 'insuficiente' };
    if (a && b && signo(tMco) === signo(tSen)) return { estado: signo(tMco) > 0 ? 'aumento' : 'disminucion' };
    return { estado: 'discrepan', mco_excluye_cero: a, sen_excluye_cero: b };
  }

  function analizar(serie, nivel) {
    nivel = nivel || 0.95;
    var p = paresValidos(serie);
    var tM = mco(p.x, p.y, nivel), tS = sen(p.x, p.y, nivel);
    return { mco: tM, sen: tS, n_validos: p.x.length, veredicto: veredicto(tM, tS) };
  }

  function pearson(a, b) {
    var n = a.length;
    if (n < 3) return null;
    var ma = media(a), mb = media(b), sab = 0, saa = 0, sbb = 0;
    for (var i = 0; i < n; i++) { sab += (a[i] - ma) * (b[i] - mb); saa += (a[i] - ma) * (a[i] - ma); sbb += (b[i] - mb) * (b[i] - mb); }
    var r = sab / Math.sqrt(saa * sbb), gl = n - 2;
    var t = r * Math.sqrt(gl / Math.max(1e-12, 1 - r * r));
    return { r: r, n: n, p: pBilateralT(t, gl) };
  }

  var api = {
    MIN_ANIOS: MIN_ANIOS, mco: mco, sen: sen, veredicto: veredicto, analizar: analizar,
    paresValidos: paresValidos, pearson: pearson, cuantilT: cuantilT, pBilateralT: pBilateralT
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else raiz.SofEstadistica = api;
})(typeof window !== 'undefined' ? window : this);
