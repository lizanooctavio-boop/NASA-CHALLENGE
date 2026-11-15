// Enlace entre los controles meteorológicos (capa, hora, partículas, opacidad) y el globo 3D.
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const cache = new Map();
  let turno = 0;

  function campoGlobal(variable, paso) {
    const clave = variable + '|' + paso;
    if (!cache.has(clave)) {
      const promesa = window.FuentesMeteo.fetch('/api/global?var=' + variable + '&paso=' + paso)
        .then(r => { if (!r.ok) throw Error('HTTP ' + r.status); return r.json(); })
        .catch(e => { cache.delete(clave); throw e; });
      if (cache.size >= 16) cache.delete(cache.keys().next().value);
      cache.set(clave, promesa);
    }
    return cache.get(clave);
  }

  async function sincronizar() {
    const E = window.Espacio, C = window.SICC_campo;
    if (!E || !C) return;
    const s = C.estado(), meta = C.meta?.();
    const variable = s.variable, paso = s.mundial?.paso;
    const opacidad = Number($('opacidad-temp').value) / 100;
    const mio = ++turno;
    if (!meta || paso == null) { E.meteo(null); E.viento(null, null, false); return; }
    try {
      const archivo = variable === 'viento_ms' ? 'viento' : variable;
      const [campo, viento] = await Promise.allSettled([
        variable === 'ninguna' ? Promise.resolve(null) : campoGlobal(archivo, paso),
        campoGlobal('viento', paso)
      ]);
      if (mio !== turno) return;
      const datos = campo.status === 'fulfilled' ? campo.value : null;
      E.meteo(datos ? window.GloboMeteo.textura(meta, datos, variable) : null, opacidad);
      const w = viento.status === 'fulfilled' ? viento.value : null;
      E.viento(meta, w, $('chk-particulas').checked);
    } catch (e) {
      if (mio === turno) E.meteo(null);
    }
  }

  // Centro del globo en el hueco libre entre el panel abierto y la barra de capas.
  function desplazar() {
    if (!window.Espacio) return;
    const ancho = innerWidth;
    if (ancho < 1000 || document.body.classList.contains('solo-mapa')) return window.Espacio.desplazar(0);
    const panel = [...document.querySelectorAll('.vista')].find(v => !v.hidden);
    const izquierda = panel && !panel.classList.contains('minimizada') ? panel.getBoundingClientRect().right : 0;
    const derecha = $('barra-capas').getBoundingClientRect().left;
    window.Espacio.desplazar(Math.max(0, ((izquierda + derecha) / 2 - ancho / 2) * 0.85));
  }

  function iniciar() {
    window.Espacio.alElegir((lat, lon) => window.elegirPunto?.(lat, lon) ?? (function () {
      $('lat').value = lat.toFixed(3); $('lon').value = lon.toFixed(3); $('consulta-punto').requestSubmit();
    })());
    desplazar();
    sincronizar();
  }
  ['sicc:hora', 'sicc:capa', 'sicc:campo'].forEach(ev => document.addEventListener(ev, sincronizar));
  $('chk-particulas').addEventListener('change', sincronizar);
  $('opacidad-temp').addEventListener('input', e => { e.target.setAttribute('aria-valuetext', `${e.target.value}%`); window.Espacio?.opacidad(Number(e.target.value) / 100); });
  ['sicc:paneles', 'sicc:pestana'].forEach(ev => document.addEventListener(ev, () => requestAnimationFrame(desplazar)));
  addEventListener('resize', desplazar);
  if (window.Espacio) iniciar(); else document.addEventListener('espacio:listo', iniciar, { once: true });
})();
