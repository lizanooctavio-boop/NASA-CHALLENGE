/*
 * Estado versionado de una investigación por área de interés («consulta») y su codificación en enlaces.
 *
 * Esquema etd-consulta v1 (ver docs/expediente/modelo_estado.md). Reglas:
 *  - Todo parámetro que llega por enlace o archivo se valida contra una lista blanca; lo desconocido se descarta.
 *  - La identidad científica de la consulta (consulta_id) es el SHA-256 de su forma canónica sin la vista del mapa,
 *    el idioma ni el título: dos enlaces con la misma zona y parámetros tienen el mismo identificador.
 *  - El resultado (resultado_id) es el SHA-256 de los datos procesados y cifras: si la fuente cambia, cambia el id
 *    y se trata como una revisión distinta.
 *  - Nunca se escriben credenciales ni claves en el enlace (no existen en este flujo).
 */
(function (raiz, fabrica) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) module.exports = fabrica();
  else raiz.ETDEstado = fabrica();
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';

  var ESQUEMA = 'etd-consulta', VERSION = 1, VERSION_CODIGO = 'expediente-1.0.0';
  var PREFIJO_HASH = 'inv=';
  var MAX_URL = 16000;
  var TIPOS_AREA = ['punto', 'circulo', 'rectangulo', 'poligono', 'administrativa', 'archivo'];
  var VARIABLES = ['T2M', 'PRECTOTCORR'];

  // ------------------------------------------------------------------ SHA-256 (sin dependencias: sirve en Node y en http://)
  var K = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2];
  function utf8(s) {
    if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(s);
    return Buffer.from(s, 'utf8');
  }
  function sha256(datos) {
    var m = typeof datos === 'string' ? utf8(datos) : datos;
    var l = m.length, nb = ((l + 9 + 63) >> 6) << 6, b = new Uint8Array(nb);
    b.set(m); b[l] = 0x80;
    var bits = l * 8;
    for (var i = 0; i < 8; i++) b[nb - 1 - i] = Math.floor(bits / Math.pow(2, 8 * i)) & 0xff;
    var h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19], w = new Array(64);
    for (var o = 0; o < nb; o += 64) {
      for (var t = 0; t < 16; t++) w[t] = (b[o + 4 * t] << 24) | (b[o + 4 * t + 1] << 16) | (b[o + 4 * t + 2] << 8) | b[o + 4 * t + 3];
      for (t = 16; t < 64; t++) {
        var s0 = ((w[t - 15] >>> 7) | (w[t - 15] << 25)) ^ ((w[t - 15] >>> 18) | (w[t - 15] << 14)) ^ (w[t - 15] >>> 3);
        var s1 = ((w[t - 2] >>> 17) | (w[t - 2] << 15)) ^ ((w[t - 2] >>> 19) | (w[t - 2] << 13)) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) | 0;
      }
      var a = h[0], bb = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
      for (t = 0; t < 64; t++) {
        var S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
        var ch = (e & f) ^ (~e & g), t1 = (hh + S1 + ch + K[t] + w[t]) | 0;
        var S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
        var mj = (a & bb) ^ (a & c) ^ (bb & c), t2 = (S0 + mj) | 0;
        hh = g; g = f; f = e; e = (d + t1) | 0; d = c; c = bb; bb = a; a = (t1 + t2) | 0;
      }
      h[0] = (h[0] + a) | 0; h[1] = (h[1] + bb) | 0; h[2] = (h[2] + c) | 0; h[3] = (h[3] + d) | 0;
      h[4] = (h[4] + e) | 0; h[5] = (h[5] + f) | 0; h[6] = (h[6] + g) | 0; h[7] = (h[7] + hh) | 0;
    }
    return h.map(function (x) { return ('00000000' + (x >>> 0).toString(16)).slice(-8); }).join('');
  }

  // JSON canónico: claves ordenadas, sin espacios. Los números se escriben como JSON.stringify.
  function canonico(v) {
    if (v === null || typeof v !== 'object') return JSON.stringify(v === undefined ? null : v);
    if (Array.isArray(v)) return '[' + v.map(canonico).join(',') + ']';
    return '{' + Object.keys(v).filter(function (k) { return v[k] !== undefined; }).sort()
      .map(function (k) { return JSON.stringify(k) + ':' + canonico(v[k]); }).join(',') + '}';
  }

  // ------------------------------------------------------------------ base64url
  function b64url(bytes) {
    var s = '';
    if (typeof btoa === 'function') { for (var i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]); s = btoa(s); }
    else s = Buffer.from(bytes).toString('base64');
    return s.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function desdeB64url(txt) {
    if (!/^[A-Za-z0-9_-]*$/.test(txt)) throw errorEstado('estado_corrupto', 'caracteres no válidos');
    var s = txt.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    if (typeof atob === 'function') { var bin = atob(s), out = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i); return out; }
    return new Uint8Array(Buffer.from(s, 'base64'));
  }
  function textoDe(bytes) { return typeof TextDecoder !== 'undefined' ? new TextDecoder('utf-8', { fatal: true }).decode(bytes) : Buffer.from(bytes).toString('utf8'); }

  async function comprimir(bytes) {
    if (typeof CompressionStream !== 'function') return null;
    var s = new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'));
    return new Uint8Array(await new Response(s).arrayBuffer());
  }
  async function descomprimir(bytes) {
    if (typeof DecompressionStream !== 'function') throw errorEstado('estado_no_soportado', 'el navegador no descomprime deflate');
    var s = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return new Uint8Array(await new Response(s).arrayBuffer());
  }

  function errorEstado(codigo, detalle) { var e = new Error(codigo + (detalle ? ': ' + detalle : '')); e.codigo = codigo; return e; }

  // ------------------------------------------------------------------ validación de la consulta
  function entero(v, min, max, nombre) {
    var n = Number(v);
    if (!Number.isInteger(n) || n < min || n > max) throw errorEstado('parametro_invalido', nombre);
    return n;
  }
  function texto(v, max) { return typeof v === 'string' ? v.replace(/[\u0000-\u001f]/g, ' ').slice(0, max || 200) : null; }
  function numero(v, min, max, nombre) {
    var n = Number(v);
    if (!isFinite(n) || n < min || n > max) throw errorEstado('parametro_invalido', nombre);
    return n;
  }

  function valoresPorDefecto() {
    var anioFin = new Date().getUTCFullYear() - 1;
    return {
      esquema: ESQUEMA, version: VERSION, version_codigo: VERSION_CODIGO,
      titulo: '', idioma: 'es',
      area: null,
      variable: 'T2M', fuente: 'nasa_power',
      periodo: { inicio: 1981, fin: Math.min(anioFin, 2024) },
      referencia: { inicio: 1991, fin: 2020 },
      meses: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
      calidad: { min_cobertura_espacial: 0.9, meses_completos: true, min_anios: 10, min_fraccion_referencia: 0.8 },
      estadistica: { metodos: ['sen_mann_kendall', 'mco'], nivel: 0.95 },
      vista: { centro: null, zoom: null, anio_visible: null, capa: 'anomalia_anual', estilo: 'divergente' },
      panel: 'resultados',
      // Perspectiva de la próxima década: fuera del núcleo de la consulta (no cambia C-/R-); tiene su propio P-.
      perspectiva: { activa: true, modelo: 'auto', escenarios: ['ssp245', 'ssp585'], semilla: 20261115, n_sim: 2000 }
    };
  }

  /*
   * Normaliza y valida una consulta recibida (enlace, archivo o interfaz). Devuelve una consulta nueva.
   * La geometría se valida aparte con ETDGeo.validar; aquí solo se comprueba su forma.
   */
  function validar(c) {
    if (!c || typeof c !== 'object') throw errorEstado('estado_corrupto', 'no es un objeto');
    if (c.esquema !== ESQUEMA) throw errorEstado('estado_corrupto', 'esquema');
    if (c.version !== VERSION) {
      if (Number(c.version) > VERSION) throw errorEstado('version_futura', String(c.version));
      c = migrar(c);
    }
    var d = valoresPorDefecto(), s = {};
    s.esquema = ESQUEMA; s.version = VERSION;
    s.version_codigo = texto(c.version_codigo, 40) || VERSION_CODIGO;
    s.titulo = texto(c.titulo, 160) || '';
    s.idioma = c.idioma === 'en' ? 'en' : 'es';
    if (VARIABLES.indexOf(c.variable) < 0) throw errorEstado('parametro_invalido', 'variable');
    s.variable = c.variable;
    if (c.fuente !== 'nasa_power') throw errorEstado('parametro_invalido', 'fuente');
    s.fuente = c.fuente;
    var p = c.periodo || {}, r = c.referencia || {};
    s.periodo = { inicio: entero(p.inicio, 1981, 2100, 'periodo.inicio'), fin: entero(p.fin, 1981, 2100, 'periodo.fin') };
    if (s.periodo.fin < s.periodo.inicio) throw errorEstado('parametro_invalido', 'periodo');
    s.referencia = { inicio: entero(r.inicio, 1981, 2100, 'referencia.inicio'), fin: entero(r.fin, 1981, 2100, 'referencia.fin') };
    if (s.referencia.fin < s.referencia.inicio) throw errorEstado('parametro_invalido', 'referencia');
    if (!Array.isArray(c.meses) || !c.meses.length) throw errorEstado('parametro_invalido', 'meses');
    var meses = {};
    c.meses.forEach(function (m) { meses[entero(m, 1, 12, 'meses')] = true; });
    s.meses = Object.keys(meses).map(Number).sort(function (a, b) { return a - b; });
    var q = c.calidad || {};
    s.calidad = {
      min_cobertura_espacial: q.min_cobertura_espacial === undefined ? d.calidad.min_cobertura_espacial : numero(q.min_cobertura_espacial, 0.5, 1, 'calidad.min_cobertura_espacial'),
      meses_completos: true,
      min_anios: q.min_anios === undefined ? 10 : entero(q.min_anios, 10, 200, 'calidad.min_anios'),
      min_fraccion_referencia: q.min_fraccion_referencia === undefined ? 0.8 : numero(q.min_fraccion_referencia, 0.5, 1, 'calidad.min_fraccion_referencia')
    };
    var e = c.estadistica || {};
    s.estadistica = { metodos: ['sen_mann_kendall', 'mco'], nivel: e.nivel === undefined ? 0.95 : numero(e.nivel, 0.8, 0.99, 'estadistica.nivel') };
    var v = c.vista || {};
    s.vista = {
      centro: Array.isArray(v.centro) && v.centro.length === 2 ? [numero(v.centro[0], -90, 90, 'vista.centro'), numero(v.centro[1], -540, 540, 'vista.centro')] : null,
      zoom: v.zoom === null || v.zoom === undefined ? null : entero(v.zoom, 1, 18, 'vista.zoom'),
      anio_visible: v.anio_visible === null || v.anio_visible === undefined ? null : entero(v.anio_visible, 1981, 2100, 'vista.anio_visible'),
      capa: ['anomalia_anual', 'tendencia_celda', 'peso_celda'].indexOf(v.capa) >= 0 ? v.capa : 'anomalia_anual',
      estilo: v.estilo === 'secuencial' ? 'secuencial' : 'divergente'
    };
    s.panel = ['resultados', 'serie', 'calidad', 'mapa'].indexOf(c.panel) >= 0 ? c.panel : 'resultados';
    var pp = c.perspectiva || {}, dp = d.perspectiva;
    if (pp.modelo !== undefined && ['auto', 'climatologia', 'persistencia', 'tendencia_ar1', 'tendencia_amortiguada'].indexOf(pp.modelo) < 0) throw errorEstado('parametro_invalido', 'perspectiva.modelo');
    var esc = Array.isArray(pp.escenarios) ? pp.escenarios.filter(function (x) { return x === 'ssp245' || x === 'ssp585'; }) : dp.escenarios;
    s.perspectiva = {
      activa: pp.activa === undefined ? dp.activa : pp.activa === true,
      modelo: pp.modelo || dp.modelo,
      escenarios: esc.length ? esc : dp.escenarios,
      semilla: pp.semilla === undefined ? dp.semilla : entero(pp.semilla, 0, 4294967295, 'perspectiva.semilla'),
      n_sim: pp.n_sim === undefined ? dp.n_sim : entero(pp.n_sim, 200, 20000, 'perspectiva.n_sim')
    };
    s.area = validarArea(c.area);
    if (c.resultado_ref) s.resultado_ref = /^R-[0-9a-f]{16,64}$/.test(c.resultado_ref) ? c.resultado_ref : undefined;
    return s;
  }

  function validarArea(a) {
    if (!a || typeof a !== 'object') throw errorEstado('parametro_invalido', 'area');
    if (TIPOS_AREA.indexOf(a.tipo) < 0) throw errorEstado('parametro_invalido', 'area.tipo');
    var s = { id: /^[A-Za-z0-9_.:-]{1,80}$/.test(a.id || '') ? a.id : null, nombre: texto(a.nombre, 120) || '', tipo: a.tipo };
    if (a.tipo === 'administrativa') {
      var ad = a.admin || {};
      if (['municipio', 'departamento'].indexOf(ad.nivel) < 0) throw errorEstado('parametro_invalido', 'area.admin.nivel');
      s.admin = { fuente: 'ineter', nivel: ad.nivel, codigo: ad.codigo === undefined || ad.codigo === null ? null : String(ad.codigo).slice(0, 20), nombre: texto(ad.nombre, 120) };
      if (!s.admin.codigo && !s.admin.nombre) throw errorEstado('parametro_invalido', 'area.admin');
    }
    if (a.tipo === 'circulo') s.radio_km = numero(a.radio_km, 0.1, 500, 'area.radio_km');
    if (a.geometria) s.geometria = a.geometria;
    else if (a.tipo !== 'administrativa') throw errorEstado('parametro_invalido', 'area.geometria');
    if (a.hash_geometria && /^[0-9a-f]{64}$/.test(a.hash_geometria)) s.hash_geometria = a.hash_geometria;
    if (a.procedencia && typeof a.procedencia === 'object') s.procedencia = { tipo: texto(a.procedencia.tipo, 30), fuente: texto(a.procedencia.fuente, 200), version: texto(a.procedencia.version, 120) };
    return s;
  }

  // Punto de entrada para esquemas antiguos. Hoy solo existe v1: cualquier otra versión es un estado no admitido.
  function migrar(c) { throw errorEstado('version_no_admitida', String(c.version)); }

  // Parte científica de la consulta (lo que define el resultado). Excluye vista, idioma, título y panel.
  function nucleo(c) {
    return {
      esquema: c.esquema, version: c.version, version_codigo: c.version_codigo,
      area: { tipo: c.area.tipo, geometria: c.area.geometria, radio_km: c.area.radio_km, admin: c.area.admin },
      variable: c.variable, fuente: c.fuente, periodo: c.periodo, referencia: c.referencia, meses: c.meses,
      calidad: c.calidad, estadistica: c.estadistica
    };
  }
  function consultaId(c) { return 'C-' + sha256(canonico(nucleo(c))).slice(0, 24); }
  function hashGeometria(g) { return sha256(canonico(g)); }

  // ------------------------------------------------------------------ enlaces
  function paraEnlace(c) {
    // Las unidades administrativas viajan por código + hash; la geometría se reconstruye del archivo de límites publicado.
    var x = JSON.parse(JSON.stringify(c));
    if (x.area && x.area.tipo === 'administrativa' && x.area.geometria) { x.area.hash_geometria = hashGeometria(x.area.geometria); delete x.area.geometria; }
    if (x.area && x.area.geometria) x.area.geometria = redondearGeom(x.area.geometria, 6);
    return x;
  }
  function redondearGeom(g, nd) {
    var f = Math.pow(10, nd);
    function r(c) { return typeof c[0] === 'number' ? [Math.round(c[0] * f) / f, Math.round(c[1] * f) / f] : c.map(r); }
    return { type: g.type, coordinates: r(g.coordinates) };
  }

  async function codificar(c) {
    var json = JSON.stringify(paraEnlace(c)), bytes = utf8(json), z = null;
    try { z = await comprimir(bytes); } catch (e) { z = null; }
    return z && z.length < bytes.length ? 'z' + b64url(z) : 'j' + b64url(bytes);
  }

  async function decodificar(txt) {
    if (typeof txt !== 'string' || txt.length < 2) throw errorEstado('estado_corrupto', 'vacío');
    if (txt.length > MAX_URL) throw errorEstado('estado_corrupto', 'demasiado largo');
    var tipo = txt[0], bytes = desdeB64url(txt.slice(1)), json;
    try {
      if (tipo === 'z') bytes = await descomprimir(bytes);
      else if (tipo !== 'j') throw errorEstado('estado_corrupto', 'formato');
      json = JSON.parse(textoDe(bytes));
    } catch (e) { if (e.codigo) throw e; throw errorEstado('estado_corrupto', 'no se puede leer'); }
    return json;
  }

  /*
   * Construye el enlace público. urlBase sale de SICC_CONFIG.url_publica; si la página corre en localhost y no hay
   * URL pública configurada, el enlace se marca como no compartible con terceros.
   */
  async function enlace(c, urlBase, opciones) {
    opciones = opciones || {};
    var cod = await codificar(c);
    var base = String(urlBase || '').replace(/#.*$/, '');
    var url = base + '#' + PREFIJO_HASH + cod + (opciones.resultado_ref ? '&r=' + opciones.resultado_ref : '');
    var local = /^https?:\/\/(localhost|127\.|0\.0\.0\.0|\[::1\])/i.test(base) || /^file:/i.test(base);
    return { url: url, longitud: url.length, demasiado_largo: url.length > MAX_URL, compartible: !local && /^https:\/\//i.test(base) };
  }

  // Lee el estado del fragmento (#inv=...&r=R-...). Devuelve null si el fragmento no es una investigación.
  function leerFragmento(hash) {
    var h = String(hash || '').replace(/^#/, '');
    if (h.indexOf(PREFIJO_HASH) !== 0) return null;
    var partes = h.slice(PREFIJO_HASH.length).split('&'), r = null;
    partes.slice(1).forEach(function (p) { if (/^r=R-[0-9a-f]{16,64}$/.test(p)) r = p.slice(2); });
    return { codigo: partes[0], resultado_ref: r };
  }

  return {
    ESQUEMA: ESQUEMA, VERSION: VERSION, VERSION_CODIGO: VERSION_CODIGO, MAX_URL: MAX_URL, TIPOS_AREA: TIPOS_AREA,
    sha256: sha256, canonico: canonico, valoresPorDefecto: valoresPorDefecto, validar: validar, nucleo: nucleo,
    consultaId: consultaId, hashGeometria: hashGeometria, codificar: codificar, decodificar: decodificar,
    enlace: enlace, leerFragmento: leerFragmento, paraEnlace: paraEnlace, b64url: b64url, utf8: utf8
  };
});
