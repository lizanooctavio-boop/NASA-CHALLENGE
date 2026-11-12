/*
 * Orquestación de la demo: carga de datos, selección de dominio, descargas.
 *
 * Fuente de datos (en este orden):
 *   1. ?datos=ruta/al/archivo.json, si se indica.
 *   2. data/clima.json junto a index.html, si la página se sirve por HTTP (Render o python -m http.server).
 *   3. Datos de ejemplo sintéticos de src/datos/ejemplo.js, rotulados como tales.
 * Las geometrías se leen de data/dominios.geojson (ruta en geometria.archivo, relativa a data/).
 *   ?caso=faltantes  prueba el aviso de datos faltantes con los datos de ejemplo.
 *   ?region=HND      abre otro dominio (caja_sicc, NIC, HND, CRI). Por defecto, NIC.
 */
(function () {
  'use strict';
  var G = window.SofGraficas, C = window.SofContrato, F = G.formato;
  var params = new URLSearchParams(location.search);
  var estado = { datos: null, sel: 'NIC', origen: '' };
  var RUTA_POR_DEFECTO = 'data/clima.json';

  var $ = function (id) { return document.getElementById(id); };

  // ---------- carga ----------
  function pedirJson(ruta) {
    return fetch(ruta, { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }
  function carpeta(ruta) { var i = ruta.lastIndexOf('/'); return i >= 0 ? ruta.slice(0, i + 1) : ''; }

  function cargar() {
    var pedida = params.get('datos');
    var porHttp = /^https?:$/.test(location.protocol);
    if (params.get('caso') === 'faltantes') {
      return Promise.resolve({ bruto: C.variarFaltantes(window.SOF_DATOS_EJEMPLO), origen: 'ejemplo', avisos: [] });
    }
    var ruta = pedida || (porHttp ? RUTA_POR_DEFECTO : null);
    if (!ruta) return Promise.resolve({ bruto: window.SOF_DATOS_EJEMPLO, origen: 'ejemplo', avisos: [] });
    return pedirJson(ruta).then(function (bruto) {
      return { bruto: bruto, origen: ruta, avisos: [] };
    }).catch(function (e) {
      var msg = pedida
        ? 'No se pudo cargar «' + ruta + '» (' + e.message + '). Se muestran los datos de ejemplo.'
        : 'Todavía no existe ' + RUTA_POR_DEFECTO + ' (' + e.message + '). Se muestran los datos de ejemplo.';
      return { bruto: window.SOF_DATOS_EJEMPLO, origen: 'ejemplo', avisos: [msg], error: !!pedida };
    });
  }

  function cargarGeometrias(datos, origen) {
    if (origen === 'ejemplo') return Promise.resolve(false);
    var con = datos.crudo.dominios.filter(function (d) { return d.geometria && d.geometria.archivo; });
    if (!con.length) return Promise.resolve(false);
    var ruta = carpeta(origen) + con[0].geometria.archivo;
    return pedirJson(ruta).then(function (gj) { C.unirGeometrias(datos, gj); return true; })
      .catch(function () { return false; });
  }

  function aviso(html, rol) {
    var div = document.createElement('div');
    div.className = 'aviso';
    div.setAttribute('role', rol || 'status');
    div.innerHTML = html;
    $('avisos').appendChild(div);
  }
  function lista(items) { return '<ul>' + items.map(function (a) { return '<li>' + G.escapar(a) + '</li>'; }).join('') + '</ul>'; }

  // ---------- selector ----------
  var ROLES = { referencia: 'caja de partida', principal: 'área principal', contexto: 'contexto', auxiliar: 'auxiliar' };

  function construirSelector() {
    var cont = $('botones-region');
    cont.innerHTML = '';
    estado.datos.regiones.forEach(function (r) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role', 'radio');
      b.dataset.region = r.id;
      b.innerHTML = '<span>' + G.escapar(r.nombre) + '</span><span class="rol">' + G.escapar(ROLES[r.rol] || r.rol) + '</span>';
      b.addEventListener('click', function () { elegir(r.id, false); });
      cont.appendChild(b);
    });
    cont.addEventListener('keydown', function (ev) {
      var teclas = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'];
      if (teclas.indexOf(ev.key) < 0) return;
      ev.preventDefault();
      var ids = estado.datos.regiones.map(function (r) { return r.id; });
      var i = ids.indexOf(estado.sel), n = ids.length;
      if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') i = (i + 1) % n;
      else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') i = (i - 1 + n) % n;
      else if (ev.key === 'Home') i = 0; else i = n - 1;
      elegir(ids[i], true);
    });
  }

  function elegir(id, enfocar) {
    if (!estado.datos.regiones.some(function (r) { return r.id === id; })) return;
    estado.sel = id;
    var url = new URL(location.href);
    url.searchParams.set('region', id);
    history.replaceState(null, '', url);
    pintar();
    if (enfocar) {
      var b = document.querySelector('#botones-region [data-region="' + id + '"]');
      if (b) b.focus();
    }
  }

  function region(id) { id = id || estado.sel; return estado.datos.regiones.find(function (r) { return r.id === id; }); }

  // ---------- textos ----------
  var ICONOS = {
    detectada: '<path d="M4 12l5 5L20 6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    insuficiente: '<path d="M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>',
    discrepan: '<path d="M5 8h9M10 16h9M14 5l3 3-3 3M10 13l-3 3 3 3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    faltan: '<path d="M12 6v8M12 18v.5" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>'
  };

  function ic(t) { return F.conSigno(t.pendiente) + ' (IC 95 %: ' + F.conSigno(t.ic_inf) + ' a ' + F.conSigno(t.ic_sup) + ')'; }

  function pintarVeredicto() {
    var r = region(), t = r.tendencia, e = G.ESTADOS[t.estado], u = estado.datos.meta.unidades_pendiente;
    var cuerpo;
    if (t.estado === 'faltan') {
      cuerpo = '<p class="detalle">' + G.escapar(t.mensaje) + '</p>';
    } else {
      var lineas = G.METODOS.filter(function (m) { return t[m.clave]; }).map(function (m) {
        return '<li>' + m.nombre + ': ' + ic(t[m.clave]) + '</li>';
      }).join('');
      var extra = [];
      if (t.media !== null) extra.push('Media anual: ' + F.nf0.format(t.media) + ' ' + estado.datos.meta.unidades + '.');
      if (t.mann_kendall && isFinite(t.mann_kendall.p_valor)) extra.push('Mann–Kendall: p = ' + F.nf2.format(t.mann_kendall.p_valor) + '.');
      if (t.omitir) extra.push('Al quitar un año cada vez, la pendiente va de ' + F.conSigno(t.omitir.ic_inf) + ' a ' + F.conSigno(t.omitir.ic_sup) + ' ' + u + '.');
      var sens = (t.sensibilidad || []).filter(function (s) { return s && Array.isArray(s.ic_mm_por_decada); }).map(function (s) {
        return '<li>' + G.escapar(s.periodo || s.nombre || s.ventana || '') + ': ' + F.conSigno(s.mm_por_decada) + ' (' + F.conSigno(s.ic_mm_por_decada[0]) + ' a ' + F.conSigno(s.ic_mm_por_decada[1]) + ')</li>';
      }).join('');
      cuerpo = '<p class="detalle">' + G.escapar(t.veredicto_texto) + (t.interpretacion ? ' ' + G.escapar(t.interpretacion) : '') + '</p>' +
        '<ul class="detalle" style="margin:6px 0 0;padding-left:20px">' + lineas + '</ul>' +
        '<p class="detalle">Pendientes en ' + G.escapar(u) + '. ' + G.escapar(extra.join(' ')) + '</p>' +
        (sens ? '<details class="sensibilidad detalle"><summary>Sensibilidad al periodo</summary><ul style="margin:4px 0 0;padding-left:20px">' + sens + '</ul></details>' : '');
    }
    $('veredicto').innerHTML =
      '<div class="veredicto"><span class="icono ' + e.clase + '" aria-hidden="true"><svg viewBox="0 0 24 24">' + ICONOS[t.estado] + '</svg></span>' +
      '<div><p class="sub" style="margin:0">' + G.escapar(r.nombre) + ' · ' + estado.datos.meta.periodo.join('–') + '</p>' +
      '<p class="estado ' + e.clase + '">' + e.etiqueta + '</p></div>' + cuerpo + '</div>';
    pintarRespuesta();
  }

  function frasePendiente(r) {
    var t = r.tendencia;
    return t.principal ? F.conSigno(t.principal.pendiente) + ' ' + estado.datos.meta.unidades_pendiente : 'sin tendencia calculable';
  }

  function pintarRespuesta() {
    var caja = region('caja_sicc'), nic = region('NIC');
    var resp;
    if (!caja || !nic || caja.tendencia.estado === 'faltan' || nic.tendencia.estado === 'faltan') {
      resp = '<strong>No se puede responder todavía:</strong> faltan datos de la caja original o de Nicaragua.';
    } else {
      var mismo = caja.tendencia.estado === nic.tendencia.estado;
      resp = 'Al pasar de la caja original a Nicaragua, la estimación cambia de ' + frasePendiente(caja) + ' a ' + frasePendiente(nic) + '. ' +
        (mismo ? '<strong>La conclusión se mantiene:</strong> ' + G.ESTADOS[nic.tendencia.estado].etiqueta.toLowerCase() + ' en ambos casos.'
          : '<strong>La conclusión cambia:</strong> de «' + G.ESTADOS[caja.tendencia.estado].etiqueta.toLowerCase() + '» a «' + G.ESTADOS[nic.tendencia.estado].etiqueta.toLowerCase() + '».');
    }
    var sup = estado.datos.superposicion, nota = '';
    if (sup) {
      var par = (sup.pares || []).find(function (p) { return (p.a === 'caja_sicc' && p.b === 'NIC') || (p.a === 'NIC' && p.b === 'caja_sicc'); });
      nota = (par && isFinite(par.interseccion_km2) ? 'La caja y Nicaragua comparten unos ' + F.nf0.format(par.interseccion_km2) + ' km²' +
        (isFinite(par.fraccion_de_a) ? ' (' + F.nf0.format(par.fraccion_de_a * 100) + ' % de la caja)' : '') + ', así que no son dos muestras independientes. ' : '') +
        'Honduras y Costa Rica dan contexto y comparten el mismo sistema climático: sus resultados no se suman como pruebas independientes.';
    }
    $('respuesta').innerHTML = '<span>¿Cambia la conclusión al ampliar el mapa? ' + resp + '</span><ul class="chips">' +
      estado.datos.regiones.map(function (q) {
        var e2 = G.ESTADOS[q.tendencia.estado];
        return '<li' + (q.id === estado.sel ? ' aria-current="true" style="border-color:var(--texto)"' : '') + '><span class="punto ' + e2.clase + '" aria-hidden="true"></span>' +
          G.escapar(q.nombre) + ': ' + e2.etiqueta.toLowerCase() + '</li>';
      }).join('') + '</ul>' + (nota ? '<p class="superposicion">' + G.escapar(nota) + '</p>' : '');
  }

  function tablaSerie(r) {
    var u = estado.datos.meta.unidades, tm = r.tendencia.principal, ts = r.tendencia.sen;
    var filas = r.serie.map(function (p) {
      return '<tr><td>' + p.anio + '</td><td>' + (p.valor === null ? 'sin dato' : F.nf1.format(p.valor)) + '</td><td>' +
        (tm && isFinite(tm.intercepto) ? F.nf0.format(G.recta(tm, p.anio)) : '—') + '</td><td>' + (ts && isFinite(ts.intercepto) ? F.nf0.format(G.recta(ts, p.anio)) : '—') + '</td></tr>';
    }).join('');
    $('tabla-serie').innerHTML = '<table><caption class="solo-lector">Precipitación anual de ' + G.escapar(r.nombre) + '</caption><thead><tr><th scope="col">Año</th><th scope="col">Lluvia (' + G.escapar(u) + ')</th><th scope="col">Recta MCO</th><th scope="col">Recta Theil–Sen</th></tr></thead><tbody>' +
      (filas || '<tr><td colspan="4">Sin datos</td></tr>') + '</tbody></table>';
  }

  function tablaComp() {
    var u = estado.datos.meta.unidades_pendiente;
    var f = function (t) { return t ? F.conSigno(t.pendiente) + '</td><td>' + F.conSigno(t.ic_inf) + ' a ' + F.conSigno(t.ic_sup) : '—</td><td>—'; };
    var filas = estado.datos.regiones.map(function (r) {
      var t = r.tendencia;
      return '<tr><th scope="row" style="text-align:left">' + G.escapar(r.nombre) + '</th><td>' + f(t.principal) + '</td><td>' + (t.hac ? F.conSigno(t.hac.ic_inf) + ' a ' + F.conSigno(t.hac.ic_sup) : '—') + '</td><td>' + f(t.sen) + '</td><td style="text-align:left">' + G.ESTADOS[t.estado].etiqueta + '</td></tr>';
    }).join('');
    $('tabla-comp').innerHTML = '<table><caption class="solo-lector">Pendientes por dominio (' + G.escapar(u) + ')</caption><thead><tr><th scope="col">Dominio</th><th scope="col">MCO</th><th scope="col">IC MCO</th><th scope="col">IC HAC</th><th scope="col">Theil–Sen</th><th scope="col">IC Theil–Sen</th><th scope="col" style="text-align:left">Resultado</th></tr></thead><tbody>' + filas + '</tbody></table>';
  }

  // ---------- pintado ----------
  function pintar() {
    var d = estado.datos, r = region();
    document.querySelectorAll('#botones-region button').forEach(function (b) {
      var on = b.dataset.region === estado.sel;
      b.setAttribute('aria-checked', on ? 'true' : 'false');
      b.tabIndex = on ? 0 : -1;
    });
    G.ocultarTip();
    var geo = G.dibujarMapa($('mapa'), d, estado.sel, function (id) { elegir(id, false); });
    $('nota-mapa').textContent = geo
      ? 'Geometrías de data/dominios.geojson: máscaras de referencia, no fronteras oficiales. La línea discontinua es la caja original de SICC.'
      : 'Contornos simplificados a mano, solo para orientarse. La línea discontinua es la caja original de SICC.';
    G.dibujarEscalaMapa($('escala-mapa'));
    pintarVeredicto();
    $('sub-serie').textContent = r.nombre + ' · lluvia anual acumulada, ' + d.meta.unidades + '.';
    var t = r.tendencia;
    $('leyenda-serie').innerHTML =
      '<li><span class="muestra" style="border-color:var(--observado)"></span>Lluvia anual</li>' +
      (t.principal ? '<li><span class="muestra" style="border-color:var(--serie-mco)"></span>Recta de mínimos cuadrados</li>' : '') +
      (t.sen ? '<li><span class="muestra punteada" style="border-color:var(--serie-sen)"></span>Recta de Theil–Sen</li>' : '') +
      (r.anios_sin_dato && r.anios_sin_dato.length ? '<li>× año sin dato</li>' : '');
    G.dibujarSerie($('serie'), r, d.meta);
    tablaSerie(r);
    $('sub-comp').textContent = 'Marca: pendiente estimada. Barra: intervalo de confianza del 95 %. Si una barra cruza la línea vertical en cero, ese método no distingue la tendencia de la variación entre años. Pulsa una fila para seleccionar el dominio.';
    $('leyenda-comp').innerHTML = G.METODOS.map(function (m) {
      var forma = m.forma === 'circulo' ? '<circle cx="11" cy="6" r="4.5" fill="' + m.color + '"/>'
        : m.forma === 'cuadrado' ? '<rect x="7" y="2" width="8" height="8" fill="' + m.color + '"/>'
        : '<rect x="7" y="2" width="8" height="8" fill="' + m.color + '" transform="rotate(45 11 6)"/>';
      return '<li><svg width="22" height="12" aria-hidden="true"><line x1="1" x2="21" y1="6" y2="6" stroke="' + m.color + '" stroke-width="2.5"' + (m.guiones ? ' stroke-dasharray="' + m.guiones + '"' : '') + '/>' + forma + '</svg>' + m.nombre + '</li>';
    }).join('');
    G.dibujarComparacion($('comparacion'), d.regiones, estado.sel, d.meta, function (id) { elegir(id, false); });
    tablaComp();
    if ($('bloque-oni').open) G.dibujarOni($('oni'), d.oni, r, d.meta);
  }

  // ---------- descargas ----------
  function sufijo() { return estado.datos.es_ejemplo ? '_EJEMPLO' : ''; }
  function descargar(nombre, contenido, tipo) {
    try {
      var blob = new Blob([contenido], { type: tipo });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = nombre;
      document.body.appendChild(a);
      a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
      $('estado-descarga').textContent = 'Descargado: ' + nombre;
    } catch (e) {
      $('estado-descarga').textContent = 'No se pudo generar la descarga: ' + e.message;
    }
  }
  function cabeceraCsv() {
    var d = estado.datos;
    return ['# ' + (d.es_ejemplo ? 'DATOS DE EJEMPLO SINTÉTICOS: no citar. ' : '') + 'Fuente: ' + d.meta.fuente,
      '# Periodo: ' + d.meta.periodo.join('-') + '; esquema ' + d.version + '; origen: ' + estado.origen,
      '# Descargado: ' + new Date().toISOString()].join('\n') + '\n';
  }
  function n(v, dec) { return v === null || v === undefined || !isFinite(v) ? '' : Number(v).toFixed(dec === undefined ? 3 : dec); }

  function csvSerie() {
    var r = region(), tm = r.tendencia.principal, ts = r.tendencia.sen;
    var filas = r.serie.map(function (p) {
      return [p.anio, n(p.valor, 1), tm && isFinite(tm.intercepto) ? n(G.recta(tm, p.anio), 1) : '', ts && isFinite(ts.intercepto) ? n(G.recta(ts, p.anio), 1) : ''].join(',');
    });
    descargar('serie_anual_' + r.id + sufijo() + '.csv', cabeceraCsv() + '# Dominio: ' + r.id + ' (' + r.nombre + ')\nanio,lluvia_mm,recta_mco_mm,recta_theil_sen_mm\n' + filas.join('\n') + '\n', 'text/csv;charset=utf-8');
  }
  function csvPendientes() {
    var filas = estado.datos.regiones.map(function (r) {
      var t = r.tendencia, p = t.principal, h = t.hac, s = t.sen;
      return [r.id, '"' + r.nombre + '"', r.n_validos, p ? n(p.pendiente) : '', p ? n(p.ic_inf) : '', p ? n(p.ic_sup) : '', p ? n(p.p, 4) : '',
        h ? n(h.ic_inf) : '', h ? n(h.ic_sup) : '', s ? n(s.pendiente) : '', s ? n(s.ic_inf) : '', s ? n(s.ic_sup) : '',
        t.estado === 'faltan' ? 'datos_faltantes' : (t.crudo && t.crudo.veredicto) || t.estado].join(',');
    });
    descargar('pendientes_por_dominio' + sufijo() + '.csv', cabeceraCsv() + '# Pendientes en mm/década; intervalos del 95 %. Los dominios se solapan: no son muestras independientes.\n' +
      'dominio,nombre,anios_validos,mco_mm_por_decada,mco_ic_inf,mco_ic_sup,mco_p_valor,hac_ic_inf,hac_ic_sup,theil_sen_mm_por_decada,theil_sen_ic_inf,theil_sen_ic_sup,veredicto\n' + filas.join('\n') + '\n', 'text/csv;charset=utf-8');
  }
  function jsonEvidencia() {
    var d = estado.datos, r = region();
    var salida = {
      aviso: d.es_ejemplo ? 'DATOS DE EJEMPLO SINTÉTICOS: no son mediciones reales y no deben citarse.' : undefined,
      pregunta: '¿Cambia la conclusión sobre la lluvia cuando ampliamos el mapa?',
      dominio_seleccionado: r.id, origen: estado.origen, descargado: new Date().toISOString(),
      esquema: d.crudo.esquema, version_esquema: d.version, estado: d.crudo.estado,
      metadatos: d.crudo.metadatos, dominio: r.original, superposicion: d.superposicion,
      oni: d.oni ? { temporada: d.oni.temporada, correlacion_descriptiva: d.oni.correlacion[r.id], advertencia: d.oni.advertencia } : undefined,
      avisos_de_carga: d.avisos
    };
    descargar('evidencia_' + r.id + sufijo() + '.json', JSON.stringify(salida, null, 2), 'application/json');
  }

  function construirDescargas() {
    var opciones = [
      ['Serie anual del dominio seleccionado', 'CSV con la lluvia anual y las rectas de tendencia', csvSerie],
      ['Pendientes de los cuatro dominios', 'CSV con las pendientes, los tres intervalos y el veredicto', csvPendientes],
      ['Evidencia del dominio seleccionado', 'JSON con el registro completo del dominio, metadatos, superposición y avisos', jsonEvidencia]
    ];
    var cont = $('descargas');
    cont.innerHTML = '';
    opciones.forEach(function (o) {
      var b = document.createElement('button');
      b.type = 'button';
      b.innerHTML = '<span class="n">' + o[0] + '</span><span class="d">' + o[1] + '</span>';
      b.addEventListener('click', o[2]);
      cont.appendChild(b);
    });
  }

  // ---------- arranque ----------
  cargar().then(function (res) {
    try {
      estado.datos = C.normalizar(res.bruto);
    } catch (e) {
      aviso('<strong>El archivo de datos no tiene la forma esperada.</strong> ' + G.escapar(e.message) + '. Revisa data/contrato.md.', 'alert');
      return;
    }
    estado.origen = res.origen;
    return cargarGeometrias(estado.datos, res.origen).then(function () {
      var d = estado.datos;
      if (d.es_ejemplo) {
        aviso('<strong>Datos de ejemplo.</strong> Las cifras de esta vista son sintéticas y sirven solo para construir la interfaz. No son mediciones de IMERG ni del ONI y no deben citarse.', 'note');
      }
      if (res.avisos.length) aviso((res.error ? '<strong>Error de carga.</strong>' : '<strong>Datos definitivos no disponibles.</strong>') + lista(res.avisos), res.error ? 'alert' : 'status');
      if (d.avisos.length) aviso('<strong>Faltan datos.</strong> Los dominios afectados se marcan como «Datos faltantes» y no se dibuja su tendencia.' + lista(d.avisos));
      var pedida = params.get('region');
      if (pedida && d.regiones.some(function (r) { return r.id === pedida; })) estado.sel = pedida;
      $('pie-fuente').textContent = 'Fuente: ' + d.meta.fuente + '. Periodo ' + d.meta.periodo.join('–') + '. Esquema ' + d.version +
        (d.estado ? ' (' + d.estado + ')' : '') + '. Datos: ' + (res.origen === 'ejemplo' ? 'ejemplo sintético' : res.origen) + '.';
      $('limites-datos').innerHTML = d.meta.limites.length ? d.meta.limites.map(function (l) { return '<li>' + G.escapar(l) + '</li>'; }).join('')
        : '<li>El archivo no trae la lista de límites.</li>';
      construirSelector();
      construirDescargas();
      $('bloque-oni').addEventListener('toggle', function () { if ($('bloque-oni').open) G.dibujarOni($('oni'), d.oni, region(), d.meta); });
      pintar();
      var ancho = window.innerWidth, t = null;
      window.addEventListener('resize', function () {
        if (window.innerWidth === ancho) return;
        ancho = window.innerWidth;
        clearTimeout(t);
        t = setTimeout(pintar, 120);
      });
    });
  });
})();
