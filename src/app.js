/*
 * Orquestación de la demo: carga de datos, selección de región, descargas.
 *
 * Fuente de datos:
 *   - Por defecto, los datos de ejemplo de src/datos/ejemplo.js (funciona abriendo index.html sin servidor).
 *   - ?datos=ruta/al/archivo.json carga el JSON definitivo (requiere servir la carpeta por HTTP).
 *   - ?caso=faltantes reproduce el mensaje de datos faltantes con los datos de ejemplo.
 *   - ?region=honduras abre otra región (por defecto, Nicaragua).
 */
(function () {
  'use strict';
  var G = window.SofGraficas, C = window.SofContrato, F = G.formato;
  var params = new URLSearchParams(location.search);
  var estado = { datos: null, sel: 'nicaragua' };

  var $ = function (id) { return document.getElementById(id); };

  // ---------- carga ----------
  async function cargar() {
    if (location.protocol === 'file:' || params.has('caso')) {
      return params.get('caso') === 'faltantes' ? C.variarFaltantes(window.SOF_DATOS_EJEMPLO) : window.SOF_DATOS_EJEMPLO;
    }
    async function leer(ruta) {
      var respuesta = await fetch(ruta);
      if (!respuesta.ok) throw new Error('HTTP ' + respuesta.status + ' al pedir ' + ruta);
      return respuesta.json();
    }
    var clima = await leer(params.get('datos') || 'data/clima.json');
    if (clima.esquema !== 'nasa-challenge/clima') return clima;
    return C.desdeClima(clima, await leer('data/dominios.geojson'));
  }

  function mostrarAvisos(lista, error) {
    if (!lista.length) return;
    var div = document.createElement('div');
    div.className = 'aviso';
    div.setAttribute('role', error ? 'alert' : 'status');
    div.innerHTML = (error ? '<strong>Error de carga.</strong> ' : '<strong>Faltan datos.</strong> Las regiones afectadas se marcan como «Datos faltantes» y no se calcula su tendencia.') +
      '<ul>' + lista.map(function (a) { return '<li>' + G.escapar(a) + '</li>'; }).join('') + '</ul>';
    $('avisos').appendChild(div);
  }

  function mostrarAvisoEjemplo(d) {
    if (!d.es_ejemplo) return;
    var div = document.createElement('div');
    div.className = 'aviso';
    div.setAttribute('role', 'note');
    div.innerHTML = '<strong>Datos de ejemplo.</strong> Las cifras de esta vista son sintéticas y sirven solo para construir la interfaz. ' +
      'No son mediciones de IMERG ni del ONI y no deben citarse.';
    $('avisos').insertBefore(div, $('avisos').firstChild);
  }

  // ---------- selector de región ----------
  function construirSelector() {
    var cont = $('botones-region');
    cont.innerHTML = '';
    var roles = { original: 'caja de partida', principal: 'área principal', contexto: 'contexto' };
    estado.datos.regiones.forEach(function (r) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role', 'radio');
      b.dataset.region = r.id;
      b.innerHTML = '<span>' + G.escapar(r.nombre) + '</span><span class="rol">' + (roles[r.rol] || r.rol) + '</span>';
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

  // ---------- textos ----------
  function region() { return estado.datos.regiones.find(function (r) { return r.id === estado.sel; }); }

  var ICONOS = {
    aumento: '<path d="M4 15l6-6 4 4 6-7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    disminucion: '<path d="M4 7l6 6 4-4 6 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    insuficiente: '<path d="M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="12" r="0"/>',
    discrepan: '<path d="M5 8h9M10 16h9M14 5l3 3-3 3M10 13l-3 3 3 3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    faltan: '<path d="M12 6v8M12 18v.5" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>'
  };

  function ic(t, u) {
    return F.conSigno(t.pendiente) + ' ' + u + ' (IC ' + Math.round(estado.datos.meta.nivel_confianza * 100) + ' %: ' + F.conSigno(t.ic_inf) + ' a ' + F.conSigno(t.ic_sup) + ')';
  }

  function detalleVeredicto(r) {
    var a = r.analisis, v = a.veredicto.estado, u = estado.datos.meta.unidades_pendiente;
    if (v === 'faltan') {
      return r.faltante ? 'El archivo de datos no incluye esta región.' :
        'Solo hay ' + a.n_validos + ' años con dato; hacen falta al menos ' + window.SofEstadistica.MIN_ANIOS + ' para estimar una tendencia.';
    }
    var base = 'Mínimos cuadrados: ' + ic(a.mco, u) + '. Theil-Sen: ' + ic(a.sen, u) + '.';
    if (r.interpretacion) return base + " " + r.interpretacion;
    var lectura = {
      aumento: ' Los dos intervalos quedan por encima de cero: la lluvia anual tiende a aumentar en esta región durante el periodo.',
      disminucion: ' Los dos intervalos quedan por debajo de cero: la lluvia anual tiende a disminuir en esta región durante el periodo.',
      insuficiente: ' Los dos intervalos incluyen el cero. Los métodos coinciden: no hay evidencia suficiente para afirmar una tendencia.',
      discrepan: ' ' + (a.veredicto.sen_excluye_cero ? 'Theil-Sen excluye el cero, pero mínimos cuadrados no.' : 'Mínimos cuadrados excluye el cero, pero Theil-Sen no.') +
        ' El resultado depende del método, probablemente por algunos años extremos; no conviene afirmar una tendencia.'
    }[v];
    var huecos = r.anios_sin_dato && r.anios_sin_dato.length ? ' Años sin dato: ' + r.anios_sin_dato.join(', ') + '.' : '';
    return base + lectura + huecos;
  }

  function pintarVeredicto() {
    var r = region(), v = r.analisis.veredicto.estado, e = G.ESTADOS[v];
    $('veredicto').innerHTML =
      '<div class="veredicto"><span class="icono ' + e.clase + '" aria-hidden="true"><svg viewBox="0 0 24 24">' + ICONOS[v] + '</svg></span>' +
      '<div><p class="sub" style="margin:0">' + G.escapar(r.nombre) + ' · ' + estado.datos.meta.periodo.join('–') + '</p>' +
      '<p class="estado ' + e.clase + '">' + e.etiqueta + '</p></div>' +
      '<p class="detalle">' + G.escapar(detalleVeredicto(r)) + '</p></div>';

    var estados = estado.datos.regiones.map(function (q) { return q.analisis.veredicto.estado; });
    var conDatos = estados.filter(function (s) { return s !== 'faltan'; });
    var distintos = conDatos.filter(function (s, i) { return conDatos.indexOf(s) === i; });
    var sinDatos = estados.length - conDatos.length;
    var resp = conDatos.length < 2
      ? '<strong>No se puede responder:</strong> faltan datos en demasiadas regiones.'
      : distintos.length === 1
        ? '<strong>No:</strong> ' + (sinDatos ? 'las áreas con datos' : 'las cuatro áreas') + ' llevan a la misma conclusión.'
        : '<strong>Sí cambia:</strong> la conclusión depende del área que se mire.';
    if (estado.datos.meta.metodo && sinDatos === 0) {
      var caja = estado.datos.regiones.find(function (r) { return r.id === 'caja_original'; });
      var pais = estado.datos.regiones.find(function (r) { return r.id === 'nicaragua'; });
      var cambia = caja.analisis.veredicto.estado !== pais.analisis.veredicto.estado;
      resp = '<strong>De la caja a Nicaragua:</strong> ' + (cambia ? 'el resultado cambia.' : 'la conclusión se mantiene.') +
        ' Los países vecinos ofrecen contexto para la comparación.';
    }
    if (sinDatos && conDatos.length >= 2) resp += ' (Sin contar ' + sinDatos + (sinDatos === 1 ? ' región' : ' regiones') + ' con datos faltantes.)';
    $('respuesta').innerHTML = '<span>¿Cambia la conclusión al ampliar el mapa? ' + resp + '</span><ul class="chips">' +
      estado.datos.regiones.map(function (q) {
        var e2 = G.ESTADOS[q.analisis.veredicto.estado];
        return '<li' + (q.id === estado.sel ? ' aria-current="true" style="border-color:var(--texto)"' : '') + '><span class="punto ' + e2.clase + '" aria-hidden="true"></span>' +
          G.escapar(q.nombre) + ': ' + e2.etiqueta.toLowerCase() + '</li>';
      }).join('') + '</ul>';
  }

  function tablaSerie(r) {
    var u = estado.datos.meta.unidades, tm = r.analisis.mco, ts = r.analisis.sen;
    var filas = r.serie.map(function (p) {
      return '<tr><td>' + p.anio + '</td><td>' + (p.valor === null ? 'sin dato' : F.nf1.format(p.valor)) + '</td><td>' +
        (tm ? F.nf0.format(C.valorAjustado(tm, p.anio)) : '—') + '</td><td>' + (ts ? F.nf0.format(C.valorAjustado(ts, p.anio)) : '—') + '</td></tr>';
    }).join('');
    $('tabla-serie').innerHTML = '<table><caption class="solo-lector">Precipitación anual de ' + G.escapar(r.nombre) + '</caption><thead><tr><th scope="col">Año</th><th scope="col">Lluvia (' + u + ')</th><th scope="col">Recta MCO</th><th scope="col">Recta Theil-Sen</th></tr></thead><tbody>' +
      (filas || '<tr><td colspan="4">Sin datos</td></tr>') + '</tbody></table>';
  }

  function tablaComp() {
    var u = estado.datos.meta.unidades_pendiente;
    var filas = estado.datos.regiones.map(function (r) {
      var a = r.analisis, f = function (t) { return t ? F.conSigno(t.pendiente) + '</td><td>' + F.conSigno(t.ic_inf) + ' a ' + F.conSigno(t.ic_sup) : '—</td><td>—'; };
      return '<tr><th scope="row" style="text-align:left">' + G.escapar(r.nombre) + '</th><td>' + f(a.mco) + '</td><td>' + f(a.sen) + '</td><td style="text-align:left">' + G.ESTADOS[a.veredicto.estado].etiqueta + '</td></tr>';
    }).join('');
    $('tabla-comp').innerHTML = '<table><caption class="solo-lector">Pendientes por región (' + u + ')</caption><thead><tr><th scope="col">Región</th><th scope="col">MCO</th><th scope="col">IC MCO</th><th scope="col">Theil-Sen</th><th scope="col">IC Theil-Sen</th><th scope="col" style="text-align:left">Resultado</th></tr></thead><tbody>' + filas + '</tbody></table>';
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
    G.dibujarMapa($('mapa'), d, estado.sel, function (id) { elegir(id, false); });
    G.dibujarEscalaMapa($('escala-mapa'), d.regiones, d.meta);
    pintarVeredicto();
    $('sub-serie').textContent = r.nombre + ' · ' + d.meta.variable + ', ' + d.meta.unidades + '.';
    $('leyenda-serie').innerHTML =
      '<li><span class="muestra" style="border-color:var(--observado)"></span>Lluvia anual</li>' +
      (r.analisis.mco ? '<li><span class="muestra" style="border-color:var(--serie-mco)"></span>Recta de mínimos cuadrados</li>' +
        '<li><span class="muestra punteada" style="border-color:var(--serie-sen)"></span>Recta de Theil-Sen</li>' : '') +
      (r.anios_sin_dato && r.anios_sin_dato.length ? '<li>× año sin dato</li>' : '');
    G.dibujarSerie($('serie'), r, d.meta);
    tablaSerie(r);
    $('sub-comp').textContent = 'Punto: pendiente estimada. Barra: intervalo de confianza del ' + Math.round(d.meta.nivel_confianza * 100) +
      ' %. Si la barra cruza la línea vertical en cero, ese método no distingue la tendencia de la variación entre años. Pulsa una fila para seleccionar la región.';
    $('leyenda-comp').innerHTML =
      '<li><svg width="22" height="12" aria-hidden="true"><line x1="1" x2="21" y1="6" y2="6" stroke="var(--serie-mco)" stroke-width="2.5"/><circle cx="11" cy="6" r="4.5" fill="var(--serie-mco)"/></svg>Mínimos cuadrados (MCO)</li>' +
      '<li><svg width="22" height="12" aria-hidden="true"><line x1="1" x2="21" y1="6" y2="6" stroke="var(--serie-sen)" stroke-width="2.5" stroke-dasharray="5 3"/><rect x="7" y="2" width="8" height="8" fill="var(--serie-sen)" transform="rotate(45 11 6)"/></svg>Theil-Sen</li>';
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
      '# Periodo: ' + d.meta.periodo.join('-') + '; nivel de confianza: ' + d.meta.nivel_confianza + '; contrato: ' + d.version,
      '# Descargado: ' + new Date().toISOString()].join('\n') + '\n';
  }
  function n(v, dec) { return v === null || v === undefined || !isFinite(v) ? '' : Number(v).toFixed(dec === undefined ? 3 : dec); }

  function csvSerie() {
    var r = region(), tm = r.analisis.mco, ts = r.analisis.sen;
    var filas = r.serie.map(function (p) {
      return [p.anio, n(p.valor, 1), tm ? n(C.valorAjustado(tm, p.anio), 1) : '', ts ? n(C.valorAjustado(ts, p.anio), 1) : ''].join(',');
    });
    descargar('serie_anual_' + r.id + sufijo() + '.csv', cabeceraCsv() + 'anio,lluvia_mm,recta_mco_mm,recta_theil_sen_mm\n' + filas.join('\n') + '\n', 'text/csv;charset=utf-8');
  }
  function csvPendientes() {
    var filas = estado.datos.regiones.map(function (r) {
      var a = r.analisis;
      return [r.id, '"' + r.nombre + '"', a.n_validos,
        a.mco ? n(a.mco.pendiente) : '', a.mco ? n(a.mco.ic_inf) : '', a.mco ? n(a.mco.ic_sup) : '', a.mco && isFinite(a.mco.p) ? n(a.mco.p, 4) : '',
        a.sen ? n(a.sen.pendiente) : '', a.sen ? n(a.sen.ic_inf) : '', a.sen ? n(a.sen.ic_sup) : '', a.sen && isFinite(a.sen.p) ? n(a.sen.p, 4) : '',
        a.veredicto.estado].join(',');
    });
    descargar('pendientes_por_region' + sufijo() + '.csv', cabeceraCsv() +
      'region,nombre,anios_con_dato,mco_pendiente,mco_ic_inf,mco_ic_sup,mco_p,sen_pendiente,sen_ic_inf,sen_ic_sup,sen_p_mann_kendall,veredicto\n' + filas.join('\n') + '\n', 'text/csv;charset=utf-8');
  }
  function jsonEvidencia() {
    var d = estado.datos;
    var salida = {
      aviso: d.es_ejemplo ? 'DATOS DE EJEMPLO SINTÉTICOS: no son mediciones reales y no deben citarse.' : undefined,
      pregunta: '¿Cambia la conclusión sobre la lluvia cuando ampliamos el mapa?',
      version_contrato: d.version, meta: d.meta, descargado: new Date().toISOString(),
      criterio: d.meta.metodo ? d.meta.metodo.regla_veredicto : {
        aumento_o_disminucion: 'Los intervalos de MCO y Theil-Sen excluyen el cero con el mismo signo.',
        insuficiente: 'Ambos intervalos incluyen el cero.',
        discrepan: 'Un intervalo excluye el cero y el otro no, o ambos lo excluyen con signo opuesto.',
        faltan: 'Menos de ' + window.SofEstadistica.MIN_ANIOS + ' años con dato o región ausente.'
      },
      regiones: d.regiones.map(function (r) {
        return { id: r.id, nombre: r.nombre, rol: r.rol, bbox: r.bbox, veredicto: r.analisis.veredicto, origen_tendencias: r.origen_tendencias,
          anios_con_dato: r.analisis.n_validos, anios_sin_dato: r.anios_sin_dato, mco: r.analisis.mco, theil_sen: r.analisis.sen, serie: r.serie };
      }),
      avisos_de_carga: d.avisos
    };
    descargar('evidencia_lluvia' + sufijo() + '.json', JSON.stringify(salida, null, 2), 'application/json');
  }

  function construirDescargas() {
    var opciones = [
      ['Serie anual de la región seleccionada', 'CSV con lluvia anual y las dos rectas de tendencia', csvSerie],
      ['Pendientes de las cuatro regiones', 'CSV con pendientes, intervalos, valores p y resultado', csvPendientes],
      ['Evidencia completa', 'JSON con datos, método, criterio y avisos', jsonEvidencia]
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
  cargar().then(function (bruto) {
    try {
      estado.datos = C.normalizar(bruto);
    } catch (e) {
      mostrarAvisos(['El archivo de datos no tiene la forma esperada: ' + e.message], true);
      return;
    }
    var pedida = params.get('region');
    if (pedida && estado.datos.regiones.some(function (r) { return r.id === pedida; })) estado.sel = pedida;
    mostrarAvisoEjemplo(estado.datos);
    mostrarAvisos(estado.datos.avisos, false);
    $('pie-fuente').textContent = 'Fuente: ' + estado.datos.meta.fuente + '. Periodo ' + estado.datos.meta.periodo.join('–') +
      '. Contrato de datos: ' + estado.datos.version + '.';
    document.querySelectorAll('.nivel').forEach(function (n) { n.textContent = Math.round(estado.datos.meta.nivel_confianza * 100) + ' %'; });
    if (estado.datos.meta.metodo) {
      $('metodo-real').textContent = estado.datos.meta.metodo.tendencia_principal + ' ' +
        'El veredicto considera también el intervalo HAC de Newey–West. La caja original se solapa con Nicaragua y Costa Rica.';
      $('bloque-oni').closest('section').hidden = true;
    }
    construirSelector();
    construirDescargas();
    $('bloque-oni').addEventListener('toggle', function () { if ($('bloque-oni').open) G.dibujarOni($('oni'), estado.datos.oni, region(), estado.datos.meta); });
    pintar();
    var ancho = window.innerWidth, t = null;
    window.addEventListener('resize', function () {
      if (window.innerWidth === ancho) return;
      ancho = window.innerWidth;
      clearTimeout(t);
      t = setTimeout(pintar, 120);
    });
  }).catch(function (e) { mostrarAvisos([e.message], true); });
})();
