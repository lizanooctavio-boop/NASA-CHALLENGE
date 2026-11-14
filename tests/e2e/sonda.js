(function () {
  var blobs = [];
  var descargasNombres = [];
  URL.createObjectURL = function (b) { blobs.push(b); return 'blob:x'; };
  HTMLAnchorElement.prototype.click = function () { descargasNombres.push(this.download || ''); };
  function txt(id) { var e = document.getElementById(id); return e ? e.textContent.replace(/\s+/g, ' ').trim() : null; }
  function escribir(id, v) {
    var p = document.createElement('pre'); p.id = id; p.textContent = v; document.body.appendChild(p);
    fetch('/__resultado', { method: 'POST', body: v }).catch(function () {});
  }

  // Dispara desde el inicio la carga de Climate indicators y de Investigate
  document.dispatchEvent(new CustomEvent('sicc:pestana', { detail: 'indicadores' }));
  document.dispatchEvent(new CustomEvent('sicc:pestana', { detail: 'investigar' }));

  async function correr() {
    var salida = { regiones: {}, indicadores: {}, enos: {}, textoCompleto: '' };

    // 1. Pestaña Rainfall trend (#tendencias)
    var btnTend = document.querySelector('nav button[data-tab="tendencias"]');
    if (btnTend) btnTend.click();

    var ids = ['nicaragua', 'caja_original', 'honduras', 'costa_rica'];
    var todoBlobs = [];
    ids.forEach(function (id) {
      var b = document.querySelector('#botones-region button[data-region="' + id + '"]');
      b.click();
      var svgSerie = document.querySelector('#serie svg');
      var o = {
        aria: b.getAttribute('aria-checked'),
        veredicto: txt('veredicto'),
        serieAria: svgSerie ? svgSerie.getAttribute('aria-label') : null,
        seriePuntos: document.querySelectorAll('#serie svg circle').length - 1,
        compFilas: document.querySelectorAll('#comparacion svg g[data-region]').length,
        descargas: []
      };
      blobs.length = 0;
      var bt = document.querySelectorAll('#descargas button');
      for (var j = 0; j < bt.length; j++) bt[j].click();
      var copia = blobs.slice();
      copia.forEach(function (bl, k) {
        todoBlobs.push(bl.text().then(function (t) { o.descargas[k] = t; }));
      });
      salida.regiones[id] = o;
    });

    // 2. Pestaña Climate indicators (#indicadores)
    var btnInd = document.querySelector('nav button[data-tab="indicadores"]');
    if (btnInd) btnInd.click();

    var regIds = ['NIC', 'pacifico', 'central', 'caribe'];
    for (var ri = 0; ri < regIds.length; ri++) {
      var rid = regIds[ri];
      var bReg = document.querySelector('#ind-regiones button[data-id="' + rid + '"]');
      if (!bReg) continue;
      bReg.click();
      var varsDisp = Array.from(document.querySelectorAll('#ind-variables button')).map(function (x) { return x.dataset.id; });
      var porVar = {};
      for (var vi = 0; vi < varsDisp.length; vi++) {
        var vid = varsDisp[vi];
        var bVar = document.querySelector('#ind-variables button[data-id="' + vid + '"]');
        bVar.click();
        blobs.length = 0;
        descargasNombres.length = 0;
        await document.getElementById('ind-csv').onclick();
        var csvTexto = blobs.length ? await blobs[0].text() : null;
        var artContraste = document.getElementById('ind-contraste');
        var bRegAct = document.querySelector('#ind-regiones button[data-id="' + rid + '"]');
        var bVarAct = document.querySelector('#ind-variables button[data-id="' + vid + '"]');
        porVar[vid] = {
          regAria: bRegAct ? bRegAct.getAttribute('aria-checked') : null,
          varAria: bVarAct ? bVarAct.getAttribute('aria-checked') : null,
          veredicto: txt('ind-veredicto'),
          serieTitulo: txt('ind-serie-titulo'),
          contrasteVisible: artContraste ? !artContraste.hidden : false,
          contrasteSub: txt('ind-contraste-sub'),
          contrasteTarjetas: txt('ind-contraste-tarjetas'),
          csvNombre: descargasNombres[0] || null,
          csvTexto: csvTexto
        };
      }
      salida.indicadores[rid] = { variablesDisponibles: varsDisp, variables: porVar };
    }
    salida.estacional = {
      sub: txt('ind-estacional-sub'),
      tarjetas: txt('ind-estacional')
    };

    // 3. Pestaña El Niño & cyclones (#fenomenos)
    var btnFen = document.querySelector('nav button[data-tab="fenomenos"]');
    if (btnFen) btnFen.click();
    salida.enos = {
      visible: !document.getElementById('fenomenos').hidden,
      tarjetas: txt('enos-tarjetas'),
      numTarjetas: document.querySelectorAll('#enos-tarjetas .tarjeta').length
    };

    // 4. Pestañas Investigate, Learn y Sources
    var btnInv = document.querySelector('nav button[data-tab="investigar"]');
    if (btnInv) btnInv.click();
    var datosInv = await fetch('data/recursos_integrados.json').then(function (r) { return r.json(); });
    salida.investigar = { categorias: Array.from(document.querySelectorAll('#inv-categorias button')).map(function (b) { return b.dataset.id; }), casos: {} };
    for (var ii = 0; ii < datosInv.investigaciones.length; ii++) {
      var caso = datosInv.investigaciones[ii];
      window.SICC_investigar.elegir({ categoria: caso.categoria, lugar: caso.lugar, investigacion: caso.id });
      blobs.length = 0; descargasNombres.length = 0;
      await document.getElementById('inv-csv').onclick();
      salida.investigar.casos[caso.id] = {
        seleccion: window.SICC_investigar.estado().sel.investigacion,
        estado: document.querySelector('#inv-veredicto .estado').textContent,
        detalle: document.querySelector('#inv-veredicto').textContent,
        serieAria: document.querySelector('#inv-serie').getAttribute('aria-label'),
        contrastes: document.querySelectorAll('#inv-contrastes-lista .contraste').length,
        csvNombre: descargasNombres[0] || null,
        csvTexto: blobs.length ? await blobs[0].text() : null
      };
    }
    salida.investigar.demos = Array.from(document.querySelectorAll('#inv-demos button')).map(function (b) { return b.dataset.demo; });
    document.querySelector('nav button[data-tab="fuentes"]').click();
    salida.investigar.fuentes = Array.from(document.querySelectorAll('#fuentes-recursos li')).map(function (li) { return Number(li.dataset.recurso); });
    salida.investigar.aprender = document.querySelectorAll('#aprender article[id^="aprender-"]').length;
    salida.investigar.error = document.getElementById('error').hidden ? null : txt('error-texto');

    await Promise.all(todoBlobs);
    salida.textoCompleto = document.body.textContent.replace(/\s+/g, ' ').trim();
    escribir('__out', JSON.stringify(salida));
  }

  var intentos = 0;
  function esperarTodo() {
    var tendOk = !!document.querySelector('#botones-region button[data-region="nicaragua"]');
    var indOk = !!(window.SICC_indicadores && window.SICC_indicadores.estado().cargado && document.querySelector('#ind-regiones button[data-id="NIC"]'));
    var enosOk = document.querySelectorAll('#enos-tarjetas .tarjeta').length > 0;
    if (!indOk && window.SICC_indicadores) {
      document.dispatchEvent(new CustomEvent('sicc:pestana', { detail: 'indicadores' }));
    }
    var invOk = !!(window.SICC_investigar && window.SICC_investigar.estado().cargado);
    if ((tendOk && indOk && enosOk && invOk) || ++intentos > 50) {
      correr().catch(function (e) { escribir('__out', 'ERROR ' + (e && e.stack ? e.stack : e)); });
    } else {
      setTimeout(esperarTodo, 200);
    }
  }
  setTimeout(esperarTodo, 500);
})();
