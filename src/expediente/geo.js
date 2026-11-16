/*
 * Geometría del área de interés (expediente territorial).
 *
 * - GeoJSON en EPSG:4326, orden [longitud, latitud] (RFC 7946).
 * - Superficies geodésicas sobre el elipsoide WGS84 con GeographicLib (Karney, 2013), nunca sobre grados
 *   ni sobre Web Mercator. Las aristas se densifican a ≤ 0,1° antes de medir para que el área siga los lados
 *   tal como están trazados en coordenadas geográficas.
 * - Antimeridiano: cada anillo se «desenvuelve» (longitudes continuas, pueden salir de ±180) para medir,
 *   recortar y enumerar celdas; la extensión se informa como en RFC 7946 (oeste > este si lo cruza).
 *
 * Sin dependencias salvo GeographicLib (window.geodesic o require). Navegador: window.ETDGeo. Node: module.exports.
 */
(function (raiz, fabrica) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) module.exports = fabrica(require('../../app/vendor/geographiclib-geodesic.min.js'));
  else raiz.ETDGeo = fabrica(raiz.geodesic);
})(typeof window !== 'undefined' ? window : this, function (geodesic) {
  'use strict';

  var WGS84 = geodesic && geodesic.Geodesic.WGS84;
  var LIMITES = { max_vertices: 20000, max_partes: 400, max_celdas: 64, densificar_grados: 0.1 };

  // ------------------------------------------------------------------ utilidades
  function esNum(v) { return typeof v === 'number' && isFinite(v); }
  function redondear(v, d) { var f = Math.pow(10, d); return Math.round(v * f) / f; }
  function envolverLon(lon) { var x = ((lon + 180) % 360 + 360) % 360 - 180; return x === -180 && lon > 0 ? 180 : x; }

  function errorGeo(codigo, detalle) { var e = new Error(codigo + (detalle ? ': ' + detalle : '')); e.codigo = codigo; e.detalle = detalle || ''; return e; }

  // Lista de polígonos [[anillo, agujero...], ...] a partir de Polygon/MultiPolygon.
  function poligonos(geom) {
    if (!geom) return [];
    if (geom.type === 'Polygon') return [geom.coordinates];
    if (geom.type === 'MultiPolygon') return geom.coordinates;
    return [];
  }

  // Desenvuelve un anillo: longitudes continuas (sin saltos de más de 180°).
  function desenvolver(anillo) {
    var sal = [], desplaz = 0;
    for (var i = 0; i < anillo.length; i++) {
      var lon = anillo[i][0], lat = anillo[i][1];
      if (i > 0) {
        var prev = anillo[i - 1][0], d = lon - prev;
        if (d > 180) desplaz -= 360; else if (d < -180) desplaz += 360;
      }
      sal.push([lon + desplaz, lat]);
    }
    return sal;
  }

  // Desenvuelve todos los anillos de un polígono alrededor de la longitud del primer vértice exterior.
  function desenvolverPoligono(pol) {
    var ext = desenvolver(pol[0]), ref = ext[0][0];
    var res = [ext];
    for (var k = 1; k < pol.length; k++) {
      var a = desenvolver(pol[k]), d = a[0][0] - ref;
      var s = d > 180 ? -360 : d < -180 ? 360 : 0;
      res.push(a.map(function (p) { return [p[0] + s, p[1]]; }));
    }
    return res;
  }

  function densificar(anillo, paso) {
    paso = paso || LIMITES.densificar_grados;
    var sal = [];
    for (var i = 0; i < anillo.length - 1; i++) {
      var a = anillo[i], b = anillo[i + 1];
      var n = Math.max(1, Math.ceil(Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1])) / paso));
      for (var k = 0; k < n; k++) sal.push([a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n]);
    }
    sal.push(anillo[anillo.length - 1]);
    return sal;
  }

  // Área geodésica firmada (m²) de un anillo [lon,lat] cerrado. Positiva en sentido antihorario.
  function areaAnillo(anillo) {
    if (!WGS84) throw errorGeo('sin_geodesia', 'GeographicLib no está cargado');
    if (!anillo || anillo.length < 4) return 0;
    var d = densificar(anillo), p = WGS84.Polygon(false);
    for (var i = 0; i < d.length - 1; i++) p.AddPoint(d[i][1], d[i][0]);
    var r = p.Compute(false, true);
    return r.area;
  }

  function areaPoligono(pol) {
    var u = desenvolverPoligono(pol), ext = Math.abs(areaAnillo(u[0])), aguj = 0;
    for (var k = 1; k < u.length; k++) aguj += Math.abs(areaAnillo(u[k]));
    return Math.max(0, ext - aguj);
  }

  // Superficie geodésica en km² de un Polygon/MultiPolygon. Para puntos devuelve null (no tiene superficie).
  function areaKm2(geom) {
    if (!geom || geom.type === 'Point') return null;
    return poligonos(geom).reduce(function (s, p) { return s + areaPoligono(p); }, 0) / 1e6;
  }

  // ------------------------------------------------------------------ validación
  function segmentosCruzan(p1, p2, p3, p4) {
    function o(a, b, c) { var v = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1]); return Math.abs(v) < 1e-14 ? 0 : v > 0 ? 1 : 2; }
    var o1 = o(p1, p2, p3), o2 = o(p1, p2, p4), o3 = o(p3, p4, p1), o4 = o(p3, p4, p2);
    return o1 !== o2 && o3 !== o4 && o1 && o2 && o3 && o4;
  }

  // Autointersección propia (no cuenta vértices compartidos por aristas contiguas). O(n²) acotado por max_vertices.
  function anilloSeCruza(anillo) {
    var n = anillo.length - 1;
    if (n > 4000) return false; // geometrías oficiales grandes: se confía en la fuente y se informa
    for (var i = 0; i < n; i++) {
      for (var j = i + 2; j < n; j++) {
        if (i === 0 && j === n - 1) continue;
        if (segmentosCruzan(anillo[i], anillo[i + 1], anillo[j], anillo[j + 1])) return true;
      }
    }
    return false;
  }

  function validarPosicion(p) {
    if (!Array.isArray(p) || p.length < 2 || !esNum(p[0]) || !esNum(p[1])) throw errorGeo('coordenada_invalida');
    if (Math.abs(p[1]) > 90) throw errorGeo('fuera_de_rango', 'latitud ' + p[1]);
    if (Math.abs(p[0]) > 540) throw errorGeo('fuera_de_rango', 'longitud ' + p[0]);
  }

  /*
   * Valida y normaliza una geometría GeoJSON (Point, Polygon, MultiPolygon, o Feature/FeatureCollection con una de ellas).
   * Devuelve { geometria, avisos } o lanza un Error con .codigo:
   *   vacia, tipo_no_admitido, coordenada_invalida, fuera_de_rango, anillo_abierto, anillo_corto,
   *   autointerseccion, demasiado_compleja, superficie_nula
   */
  function validar(entrada) {
    var avisos = [], g = entrada;
    if (g && g.type === 'FeatureCollection') {
      var feats = (g.features || []).filter(function (f) { return f && f.geometry; });
      if (!feats.length) throw errorGeo('vacia');
      var tipos = feats.map(function (f) { return f.geometry.type; });
      if (feats.length === 1) g = feats[0].geometry;
      else if (tipos.every(function (t) { return t === 'Polygon' || t === 'MultiPolygon'; })) {
        var partes = [];
        feats.forEach(function (f) { poligonos(f.geometry).forEach(function (p) { partes.push(p); }); });
        g = { type: 'MultiPolygon', coordinates: partes };
        avisos.push('union_entidades');
      } else throw errorGeo('tipo_no_admitido', tipos.join(','));
    } else if (g && g.type === 'Feature') g = g.geometry;
    if (!g || !g.type) throw errorGeo('vacia');
    if (g.type === 'Point') {
      validarPosicion(g.coordinates);
      return { geometria: { type: 'Point', coordinates: [redondear(envolverLon(g.coordinates[0]), 6), redondear(g.coordinates[1], 6)] }, avisos: avisos };
    }
    if (g.type !== 'Polygon' && g.type !== 'MultiPolygon') throw errorGeo('tipo_no_admitido', g.type);
    var pols = poligonos(g);
    if (!pols.length) throw errorGeo('vacia');
    if (pols.length > LIMITES.max_partes) throw errorGeo('demasiado_compleja', pols.length + ' partes');
    var nv = 0, salida = [];
    pols.forEach(function (pol) {
      if (!Array.isArray(pol) || !pol.length) throw errorGeo('vacia');
      var anillos = [];
      pol.forEach(function (anillo, k) {
        if (!Array.isArray(anillo)) throw errorGeo('coordenada_invalida');
        anillo.forEach(validarPosicion);
        // quita vértices consecutivos repetidos
        var a = anillo.filter(function (p, i) { return i === 0 || p[0] !== anillo[i - 1][0] || p[1] !== anillo[i - 1][1]; })
          .map(function (p) { return [redondear(p[0], 7), redondear(p[1], 7)]; });
        var pri = a[0], ult = a[a.length - 1];
        if (pri[0] !== ult[0] || pri[1] !== ult[1]) throw errorGeo('anillo_abierto', 'anillo ' + k);
        if (a.length < 4) throw errorGeo('anillo_corto', 'anillo ' + k);
        nv += a.length;
        if (anilloSeCruza(desenvolver(a))) throw errorGeo('autointerseccion', 'anillo ' + k);
        // orientación RFC 7946: exterior antihorario, agujeros horario (se corrige, no se rechaza)
        var u = desenvolver(a), s = areaAnillo(u);
        if ((k === 0 && s < 0) || (k > 0 && s > 0)) { a = a.slice().reverse(); if (k === 0) avisos.push('orientacion_corregida'); }
        anillos.push(a);
      });
      salida.push(anillos);
    });
    if (nv > LIMITES.max_vertices) throw errorGeo('demasiado_compleja', nv + ' vértices');
    var geom = salida.length === 1 ? { type: 'Polygon', coordinates: salida[0] } : { type: 'MultiPolygon', coordinates: salida };
    if (!(areaKm2(geom) > 1e-6)) throw errorGeo('superficie_nula');
    return { geometria: geom, avisos: avisos, vertices: nv };
  }

  // ------------------------------------------------------------------ extensión y centro
  function extension(geom) {
    if (geom.type === 'Point') { var c = geom.coordinates; return [c[0], c[1], c[0], c[1]]; }
    var oeste = Infinity, este = -Infinity, sur = Infinity, norte = -Infinity;
    // Se usan intervalos de longitud por polígono desenvueltos y se busca el arco mínimo que los contiene.
    var intervalos = [];
    poligonos(geom).forEach(function (pol) {
      var u = desenvolverPoligono(pol)[0], lo = Infinity, hi = -Infinity;
      u.forEach(function (p) { lo = Math.min(lo, p[0]); hi = Math.max(hi, p[0]); sur = Math.min(sur, p[1]); norte = Math.max(norte, p[1]); });
      intervalos.push([lo, hi]);
    });
    // Normaliza cada intervalo a un inicio en [-180,180) y prueba el hueco mayor entre ellos.
    var ints = intervalos.map(function (iv) { var w = envolverLon(iv[0]); if (w === 180) w = -180; return [w, w + (iv[1] - iv[0])]; })
      .sort(function (a, b) { return a[0] - b[0]; });
    var fusion = [];
    ints.forEach(function (iv) {
      var u = fusion[fusion.length - 1];
      if (u && iv[0] <= u[1]) u[1] = Math.max(u[1], iv[1]); else fusion.push([iv[0], iv[1]]);
    });
    // hueco mayor (incluido el que cruza el antimeridiano)
    var mejor = -1, ini = fusion[0][0], fin = fusion[fusion.length - 1][1];
    var huecoCirc = (ini + 360) - fin;
    oeste = ini; este = fin; mejor = huecoCirc;
    for (var i = 0; i < fusion.length - 1; i++) {
      var h = fusion[i + 1][0] - fusion[i][1];
      if (h > mejor) { mejor = h; oeste = fusion[i + 1][0]; este = fusion[i][1] + 360; }
    }
    return [redondear(envolverLon(oeste), 6), redondear(sur, 6), redondear(envolverLon(este), 6), redondear(norte, 6)];
  }

  function cruzaAntimeridiano(geom) { var b = extension(geom); return b[0] > b[2]; }

  // Proyección azimutal equivalente de Lambert (esfera de radio auténtico) para centroides.
  var R_AUT = 6371007.181;
  function laea(lon0, lat0) {
    var r = Math.PI / 180, f0 = lat0 * r, l0 = lon0 * r;
    return {
      fwd: function (lon, lat) {
        var f = lat * r, l = lon * r, k = Math.sqrt(2 / (1 + Math.sin(f0) * Math.sin(f) + Math.cos(f0) * Math.cos(f) * Math.cos(l - l0)));
        return [R_AUT * k * Math.cos(f) * Math.sin(l - l0), R_AUT * k * (Math.cos(f0) * Math.sin(f) - Math.sin(f0) * Math.cos(f) * Math.cos(l - l0))];
      },
      inv: function (x, y) {
        var rho = Math.sqrt(x * x + y * y);
        if (rho < 1e-9) return [lon0, lat0];
        var c = 2 * Math.asin(rho / (2 * R_AUT));
        var f = Math.asin(Math.cos(c) * Math.sin(f0) + y * Math.sin(c) * Math.cos(f0) / rho);
        var l = l0 + Math.atan2(x * Math.sin(c), rho * Math.cos(f0) * Math.cos(c) - y * Math.sin(f0) * Math.sin(c));
        return [l / r, f / r];
      }
    };
  }

  function puntoEnAnillo(x, y, anillo) {
    var dentro = false;
    for (var i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
      var xi = anillo[i][0], yi = anillo[i][1], xj = anillo[j][0], yj = anillo[j][1];
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) dentro = !dentro;
    }
    return dentro;
  }

  // ¿Contiene la geometría el punto [lon,lat]? Considera agujeros y el antimeridiano.
  function contiene(geom, lon, lat) {
    return poligonos(geom).some(function (pol) {
      var u = desenvolverPoligono(pol);
      return [-360, 0, 360].some(function (s) {
        var x = lon + s;
        if (!puntoEnAnillo(x, lat, u[0])) return false;
        for (var k = 1; k < u.length; k++) if (puntoEnAnillo(x, lat, u[k])) return false;
        return true;
      });
    });
  }

  /*
   * Centro representativo: centroide de superficie en proyección equivalente local (LAEA centrada en la extensión).
   * Si el centroide cae fuera (formas en «C», multipolígonos), se usa un punto interior: el punto medio del tramo
   * interior más largo de la horizontal que pasa por la latitud media. Devuelve { lon, lat, metodo }.
   */
  function centro(geom) {
    if (geom.type === 'Point') return { lon: geom.coordinates[0], lat: geom.coordinates[1], metodo: 'punto' };
    var b = extension(geom), lon0 = b[0] <= b[2] ? (b[0] + b[2]) / 2 : envolverLon((b[0] + b[2] + 360) / 2), lat0 = (b[1] + b[3]) / 2;
    var P = laea(lon0, lat0), sx = 0, sy = 0, sa = 0;
    poligonos(geom).forEach(function (pol) {
      desenvolverPoligono(pol).forEach(function (anillo) {
        var d = densificar(anillo).map(function (p) {
          var dl = p[0] - lon0; dl = dl > 180 ? dl - 360 : dl < -180 ? dl + 360 : dl;
          return P.fwd(lon0 + dl, p[1]);
        });
        for (var i = 0; i < d.length - 1; i++) {
          var cr = d[i][0] * d[i + 1][1] - d[i + 1][0] * d[i][1];
          sa += cr; sx += (d[i][0] + d[i + 1][0]) * cr; sy += (d[i][1] + d[i + 1][1]) * cr;
        }
      });
    });
    var c = P.inv(sx / (3 * sa), sy / (3 * sa)), lon = envolverLon(c[0]), lat = c[1];
    if (contiene(geom, lon, lat)) return { lon: redondear(lon, 6), lat: redondear(lat, 6), metodo: 'centroide_laea' };
    var pi = puntoInterior(geom);
    return { lon: redondear(pi[0], 6), lat: redondear(pi[1], 6), metodo: 'punto_interior' };
  }

  function puntoInterior(geom) {
    var mejor = null, largo = -1;
    poligonos(geom).forEach(function (pol) {
      var u = desenvolverPoligono(pol), lo = Infinity, hi = -Infinity;
      u[0].forEach(function (p) { lo = Math.min(lo, p[1]); hi = Math.max(hi, p[1]); });
      [0.5, 0.35, 0.65, 0.2, 0.8].forEach(function (fr) {
        var y = lo + (hi - lo) * fr, xs = [];
        u.forEach(function (anillo) {
          for (var i = 0; i < anillo.length - 1; i++) {
            var a = anillo[i], b = anillo[i + 1];
            if ((a[1] > y) !== (b[1] > y)) xs.push(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]));
          }
        });
        xs.sort(function (p, q) { return p - q; });
        for (var k = 0; k + 1 < xs.length; k += 2) {
          if (xs[k + 1] - xs[k] > largo) { largo = xs[k + 1] - xs[k]; mejor = [envolverLon((xs[k] + xs[k + 1]) / 2), y]; }
        }
      });
    });
    return mejor;
  }

  // ------------------------------------------------------------------ constructores de áreas
  // Círculo geodésico (radio en km) como polígono de n vértices: GeographicLib Direct desde el centro.
  function circulo(lon, lat, radioKm, n) {
    n = n || 72;
    var anillo = [];
    for (var i = 0; i < n; i++) {
      var az = 360 * i / n, r = WGS84.Direct(lat, lon, az, radioKm * 1000);
      anillo.push([redondear(r.lon2, 7), redondear(r.lat2, 7)]);
    }
    anillo.reverse(); // antihorario
    anillo.push(anillo[0].slice());
    // continuidad para áreas que crucen el antimeridiano
    return { type: 'Polygon', coordinates: [desenvolver(anillo).map(function (p) { return [envolverLon(p[0]), p[1]]; })] };
  }

  function rectangulo(oeste, sur, este, norte) {
    if (este < oeste) este += 360; // cruza el antimeridiano
    var a = [[oeste, sur], [este, sur], [este, norte], [oeste, norte], [oeste, sur]];
    return { type: 'Polygon', coordinates: [a.map(function (p) { return [envolverLon(p[0]) === -180 && p[0] > 0 ? 180 : envolverLon(p[0]), p[1]]; })] };
  }

  // ------------------------------------------------------------------ rejilla de un producto y fracciones de intersección
  // Recorte Sutherland-Hodgman de un anillo (desenvuelto) contra un rectángulo [x0,y0,x1,y1].
  function recortar(anillo, r) {
    var lados = [
      function (p) { return p[0] >= r[0]; }, function (p) { return p[0] <= r[2]; },
      function (p) { return p[1] >= r[1]; }, function (p) { return p[1] <= r[3]; }
    ];
    var corte = [
      function (a, b) { var t = (r[0] - a[0]) / (b[0] - a[0]); return [r[0], a[1] + t * (b[1] - a[1])]; },
      function (a, b) { var t = (r[2] - a[0]) / (b[0] - a[0]); return [r[2], a[1] + t * (b[1] - a[1])]; },
      function (a, b) { var t = (r[1] - a[1]) / (b[1] - a[1]); return [a[0] + t * (b[0] - a[0]), r[1]]; },
      function (a, b) { var t = (r[3] - a[1]) / (b[1] - a[1]); return [a[0] + t * (b[0] - a[0]), r[3]]; }
    ];
    var sal = anillo.slice(0, -1);
    for (var k = 0; k < 4 && sal.length; k++) {
      var ent = sal; sal = [];
      for (var i = 0; i < ent.length; i++) {
        var cur = ent[i], prev = ent[(i + ent.length - 1) % ent.length];
        var dc = lados[k](cur), dp = lados[k](prev);
        if (dc) { if (!dp) sal.push(corte[k](prev, cur)); sal.push(cur); }
        else if (dp) sal.push(corte[k](prev, cur));
      }
    }
    if (sal.length < 3) return null;
    sal.push(sal[0].slice());
    return sal;
  }

  /*
   * Celdas de una rejilla regular (dlat × dlon, con origen en lat0/lon0 como centros) que tocan el área.
   * Para un punto: la celda que lo contiene, con peso 1 y fraccion_area null.
   * Para polígonos: superficie de intersección geodésica (km²) y peso = intersección / suma de intersecciones.
   */
  function celdasRejilla(geom, rej) {
    var dlat = rej.dlat, dlon = rej.dlon, lat0 = rej.lat0 === undefined ? -90 : rej.lat0, lon0 = rej.lon0 === undefined ? -180 : rej.lon0;
    function centroCelda(lon, lat) {
      var i = Math.round((lat - lat0) / dlat), j = Math.round((lon - lon0) / dlon);
      return [lon0 + j * dlon, lat0 + i * dlat];
    }
    function cajaCelda(c) { return [c[0] - dlon / 2, c[1] - dlat / 2, c[0] + dlon / 2, c[1] + dlat / 2]; }
    function areaCaja(b) { return Math.abs(areaAnillo([[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]])) / 1e6; }
    if (geom.type === 'Point') {
      var c = centroCelda(geom.coordinates[0], geom.coordinates[1]), bb = cajaCelda(c);
      return { celdas: [{ id: celdaId(c), lon: redondear(envolverLon(c[0]), 4), lat: redondear(c[1], 4), caja: bb.map(function (v) { return redondear(v, 4); }), area_celda_km2: areaCaja(bb), interseccion_km2: null, peso: 1 }], area_solicitada_km2: null };
    }
    var mapa = {}, total = 0;
    poligonos(geom).forEach(function (pol) {
      var u = desenvolverPoligono(pol), lo = Infinity, hi = -Infinity, s = Infinity, n = -Infinity;
      u[0].forEach(function (p) { lo = Math.min(lo, p[0]); hi = Math.max(hi, p[0]); s = Math.min(s, p[1]); n = Math.max(n, p[1]); });
      var c0 = centroCelda(lo, s), c1 = centroCelda(hi, n);
      var ncel = (Math.round((c1[0] - c0[0]) / dlon) + 1) * (Math.round((c1[1] - c0[1]) / dlat) + 1);
      if (ncel > LIMITES.max_celdas * 40) throw errorGeo('demasiado_grande', ncel + ' celdas candidatas');
      for (var y = c0[1]; y <= c1[1] + 1e-9; y += dlat) {
        for (var x = c0[0]; x <= c1[0] + 1e-9; x += dlon) {
          var cx = redondear(x, 6), cy = redondear(y, 6), caja = cajaCelda([cx, cy]);
          var ext = recortar(u[0], caja);
          if (!ext) continue;
          var a = Math.abs(areaAnillo(ext));
          for (var k = 1; k < u.length; k++) { var h = recortar(u[k], caja); if (h) a -= Math.abs(areaAnillo(h)); }
          a /= 1e6;
          if (a <= 1e-6) continue;
          var id = celdaId([cx, cy]);
          if (!mapa[id]) mapa[id] = { id: id, lon: redondear(envolverLon(cx), 4), lat: redondear(cy, 4), caja: caja.map(function (v) { return redondear(v, 4); }), area_celda_km2: areaCaja(caja), interseccion_km2: 0 };
          mapa[id].interseccion_km2 += a; total += a;
        }
      }
    });
    var celdas = Object.keys(mapa).map(function (k) { return mapa[k]; });
    if (celdas.length > LIMITES.max_celdas) throw errorGeo('demasiado_grande', celdas.length + ' celdas');
    celdas.forEach(function (c) {
      c.peso = c.interseccion_km2 / total;
      c.fraccion_celda = Math.min(1, c.interseccion_km2 / c.area_celda_km2);
    });
    celdas.sort(function (a, b) { return b.lat - a.lat || a.lon - b.lon; });
    return { celdas: celdas, area_solicitada_km2: areaKm2(geom), suma_intersecciones_km2: total };
  }

  function celdaId(c) { return (c[1] >= 0 ? 'N' : 'S') + Math.abs(c[1]).toFixed(3) + '_' + (envolverLon(c[0]) >= 0 ? 'E' : 'W') + Math.abs(envolverLon(c[0])).toFixed(3); }

  // ------------------------------------------------------------------ distancias y escala (para mapas del informe)
  function distanciaKm(lon1, lat1, lon2, lat2) { return WGS84.Inverse(lat1, lon1, lat2, lon2).s12 / 1000; }

  return {
    LIMITES: LIMITES, validar: validar, areaKm2: areaKm2, extension: extension, centro: centro, contiene: contiene,
    cruzaAntimeridiano: cruzaAntimeridiano, circulo: circulo, rectangulo: rectangulo, celdasRejilla: celdasRejilla,
    poligonos: poligonos, desenvolver: desenvolver, desenvolverPoligono: desenvolverPoligono, envolverLon: envolverLon,
    distanciaKm: distanciaKm, areaAnillo: areaAnillo, redondear: redondear, version: '1.0.0'
  };
});
