// Buscador inmediato de países y ciudades (Natural Earth, sin servidor).
// Crea su interfaz dentro de <header> sin modificar estilos.css ni shell.js.
(function () {
  const header = document.querySelector('header');
  if (!header) return;

  // Normaliza texto sin tildes ni mayúsculas para búsquedas como «san jose» -> «San José».
  const normalizar = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

  let datos = null;
  let carga = null;
  let indice = []; // [{ tipo: 'pais'|'ciudad', norm, nombre, sub, pais, ciudad }]
  let opcionesActuales = [];
  let activoIdx = -1;
  let paisExpandido = null;

  function nodo(tag, cls, txt) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (txt !== undefined) el.textContent = txt;
    return el;
  }

  // Construcción de la caja de búsqueda en la cabecera.
  const wrap = nodo('div', 'buscador-envoltura');
  const caja = nodo('div', 'buscador-caja');
  const icono = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  icono.setAttribute('viewBox', '0 0 24 24');
  icono.setAttribute('aria-hidden', 'true');
  icono.setAttribute('class', 'buscador-icono');
  icono.innerHTML = '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>';

  const input = nodo('input', 'buscador-entrada');
  input.type = 'text';
  input.id = 'buscador-lugar';
  input.placeholder = 'Search a country or city…';
  input.setAttribute('aria-label', 'Search a country or city');
  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-autocomplete', 'list');
  input.setAttribute('aria-expanded', 'false');
  input.setAttribute('aria-controls', 'buscador-lista');
  input.autocomplete = 'off';

  const btnLimpiar = nodo('button', 'buscador-limpiar', '×');
  btnLimpiar.type = 'button';
  btnLimpiar.hidden = true;
  btnLimpiar.setAttribute('aria-label', 'Clear search');

  const lista = nodo('ul', 'buscador-lista');
  lista.id = 'buscador-lista';
  lista.setAttribute('role', 'listbox');
  lista.setAttribute('aria-label', 'Place suggestions');
  lista.hidden = true;

  caja.append(icono, input, btnLimpiar);
  wrap.append(caja, lista);

  const acciones = header.querySelector('.acciones');
  header.insertBefore(wrap, acciones || null);

  function construirIndice(doc) {
    const out = [];
    for (const p of (doc.paises || [])) {
      out.push({
        tipo: 'pais',
        norm: normalizar(p.nombre),
        isoNorm: normalizar(p.iso),
        nombre: p.nombre,
        sub: `${p.ciudades.length} cities`,
        pais: p,
        pob: 0
      });
      for (const c of (p.ciudades || [])) {
        out.push({
          tipo: 'ciudad',
          norm: normalizar(c.nombre),
          nombre: c.nombre,
          sub: p.nombre,
          pais: p,
          ciudad: c,
          pob: c.pob || 0
        });
      }
    }
    indice = out;
  }

  function cargarDatos() {
    if (datos) return Promise.resolve(datos);
    if (carga) return carga;
    carga = fetch('data/lugares_mundo.json')
      .then(r => {
        if (!r.ok) throw Error('HTTP ' + r.status);
        return r.json();
      })
      .then(doc => {
        datos = doc;
        construirIndice(doc);
        return doc;
      })
      .catch(err => {
        carga = null;
        throw err;
      });
    return carga;
  }

  function buscar(texto, limite = 12) {
    const q = normalizar(texto);
    if (q.length < 2) return [];
    const coinciden = [];
    for (const item of indice) {
      const enNombre = item.norm.includes(q);
      const enIso = item.tipo === 'pais' && item.isoNorm === q;
      if (!enNombre && !enIso) continue;
      let puntaje = 0;
      if (enIso || item.norm === q) puntaje += 1000;
      else if (item.norm.startsWith(q)) puntaje += 500;
      if (item.tipo === 'pais') puntaje += 200;
      puntaje += Math.min(180, Math.log10((item.pob || 0) + 10) * 20);
      coinciden.push({ item, puntaje });
    }
    coinciden.sort((a, b) => b.puntaje - a.puntaje || a.item.nombre.localeCompare(b.item.nombre));
    return coinciden.slice(0, limite).map(x => x.item);
  }

  function cerrarLista() {
    lista.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    activoIdx = -1;
  }

  function marcarActivo(idx) {
    const ops = lista.querySelectorAll('[role="option"]');
    if (!ops.length) { activoIdx = -1; input.removeAttribute('aria-activedescendant'); return; }
    activoIdx = ((idx % ops.length) + ops.length) % ops.length;
    ops.forEach((el, i) => {
      const es = i === activoIdx;
      el.classList.toggle('activo', es);
      el.setAttribute('aria-selected', String(es));
      if (es) {
        input.setAttribute('aria-activedescendant', el.id);
        el.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  function renderizarOpciones(items, cabecera) {
    lista.replaceChildren();
    opcionesActuales = items;
    activoIdx = -1;
    input.removeAttribute('aria-activedescendant');

    if (cabecera) {
      const cab = nodo('li', 'buscador-cabecera');
      cab.setAttribute('role', 'presentation');
      cab.append(nodo('span', undefined, cabecera));
      const volver = nodo('button', 'buscador-volver', 'Back');
      volver.type = 'button';
      volver.setAttribute('aria-label', 'Back to search results');
      volver.onclick = ev => {
        ev.stopPropagation();
        paisExpandido = null;
        actualizarSugerencias();
        input.focus();
      };
      cab.append(volver);
      lista.append(cab);
    }

    if (!items.length) {
      const vacio = nodo('li', 'buscador-vacio', 'No matching countries or cities.');
      vacio.setAttribute('role', 'presentation');
      lista.append(vacio);
    } else {
      items.forEach((it, idx) => {
        const li = nodo('li', 'buscador-opcion');
        li.id = 'buscador-op-' + idx;
        li.setAttribute('role', 'option');
        li.setAttribute('aria-selected', 'false');
        li.append(nodo('span', undefined, it.nombre));
        li.append(nodo('span', 'buscador-opcion-sub', it.tipo === 'pais' ? `Country · ${it.sub}` : it.sub));
        li.onmousedown = ev => ev.preventDefault();
        li.onclick = ev => { ev.stopPropagation(); elegirItem(it); };
        lista.append(li);
      });
    }

    lista.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  async function abrirPais(pais) {
    paisExpandido = pais;
    const ciudades = (pais.ciudades || []).map(c => ({
      tipo: 'ciudad',
      nombre: c.nombre,
      sub: pais.nombre,
      pais,
      ciudad: c,
      pob: c.pob || 0
    }));
    renderizarOpciones(ciudades, `Cities in ${pais.nombre}`);

    // Encuadra el país en el mapa 2D si está disponible.
    try {
      if (window.SICC_vista?.cambiar) await window.SICC_vista.cambiar('mapa');
      if (typeof mapa !== 'undefined' && mapa && Array.isArray(pais.bbox) && pais.bbox.length === 4) {
        const [minLon, minLat, maxLon, maxLat] = pais.bbox;
        mapa.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [24, 24], maxZoom: 7 });
      }
    } catch (_) { /* Si el mapa aún no inicia, el listado de ciudades sigue operativo. */ }
  }

  async function elegirCiudad(ciudad, pais) {
    cerrarLista();
    paisExpandido = null;
    input.value = `${ciudad.nombre}, ${pais.nombre}`;
    btnLimpiar.hidden = false;

    try {
      if (window.SICC_vista?.irA) await window.SICC_vista.irA(ciudad.lat, ciudad.lon, 9);
      window.SICC_vista?.marcar?.(ciudad.lat, ciudad.lon, ciudad.nombre);
    } catch (_) {}

    // Actualiza el panel de coordenadas y dispara el pronóstico puntual.
    document.dispatchEvent(new CustomEvent('sicc:punto', { detail: [ciudad.lat, ciudad.lon] }));
    const latEl = document.getElementById('lat');
    const lonEl = document.getElementById('lon');
    const form = document.getElementById('consulta-punto');
    if (latEl && lonEl) {
      latEl.value = ciudad.lat.toFixed(3);
      lonEl.value = ciudad.lon.toFixed(3);
      if (form) form.requestSubmit();
    }
  }

  function elegirItem(it) {
    if (!it) return;
    if (it.tipo === 'pais') abrirPais(it.pais);
    else elegirCiudad(it.ciudad, it.pais);
  }

  async function actualizarSugerencias() {
    const q = input.value;
    btnLimpiar.hidden = !q.length;
    if (normalizar(q).length < 2) {
      paisExpandido = null;
      cerrarLista();
      return;
    }
    try {
      await cargarDatos();
    } catch (_) {
      lista.replaceChildren(nodo('li', 'buscador-vacio', 'Place directory could not be loaded.'));
      lista.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      return;
    }
    const items = buscar(q);
    renderizarOpciones(items, null);
  }

  input.addEventListener('focus', () => {
    cargarDatos().catch(() => {});
    if (paisExpandido) {
      abrirPais(paisExpandido);
    } else if (normalizar(input.value).length >= 2) {
      actualizarSugerencias();
    }
  });
  input.addEventListener('input', () => {
    paisExpandido = null;
    actualizarSugerencias();
  });

  input.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') {
      if (!lista.hidden) {
        ev.preventDefault();
        cerrarLista();
      }
      return;
    }
    if (lista.hidden) return;
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      marcarActivo(activoIdx < 0 ? 0 : activoIdx + 1);
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      marcarActivo(activoIdx < 0 ? opcionesActuales.length - 1 : activoIdx - 1);
    } else if (ev.key === 'Enter') {
      if (opcionesActuales.length) {
        ev.preventDefault();
        const idx = activoIdx >= 0 ? activoIdx : 0;
        elegirItem(opcionesActuales[idx]);
      }
    }
  });

  btnLimpiar.onclick = () => {
    input.value = '';
    btnLimpiar.hidden = true;
    paisExpandido = null;
    cerrarLista();
    input.focus();
  };

  document.addEventListener('click', ev => {
    if (ev.target.isConnected && !wrap.contains(ev.target)) cerrarLista();
  });

  window.SICC_buscador = { normalizar, buscar, abrirPais, cargarDatos };
})();
