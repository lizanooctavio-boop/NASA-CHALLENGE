// Panel plegable de coordenadas en tiempo real bajo el puntero (o último clic en móvil)
// con conversión entre WGS84, UTM automático, MGRS, Web Mercator (EPSG:3857) y UTM 16N (EPSG:32616).
(function () {
  const SISTEMAS = [
    ['wgs84_dec', 'WGS84 · Decimal degrees'],
    ['wgs84_dms', 'WGS84 · DMS (deg/min/sec)'],
    ['wgs84_rad', 'WGS84 · Radians'],
    ['utm', 'UTM · Auto zone (m)'],
    ['mgrs', 'MGRS · Military grid'],
    ['epsg3857', 'Web Mercator · EPSG:3857 (m)'],
    ['epsg32616', 'Nicaragua · UTM 16N (EPSG:32616)']
  ];

  // Registra EPSG:32616 si proj4 ya está disponible.
  const PROJ_32616 = '+proj=utm +zone=16 +datum=WGS84 +units=m +no_defs';
  const PROJ_UPS_S = '+proj=stere +lat_0=-90 +lon_0=0 +k=0.994 +x_0=2000000 +y_0=2000000 +datum=WGS84 +units=m +no_defs';
  const PROJ_UPS_N = '+proj=stere +lat_0=90 +lon_0=0 +k=0.994 +x_0=2000000 +y_0=2000000 +datum=WGS84 +units=m +no_defs';

  function wrapLon(lon) {
    return ((((lon + 180) % 360) + 360) % 360) - 180;
  }

  function zonaUtm(lat, lon) {
    let z = Math.floor((wrapLon(lon) + 180) / 6) + 1;
    // Excepciones oficiales UTM para Noruega y Svalbard.
    if (lat >= 56 && lat < 64 && lon >= 3 && lon < 12) z = 32;
    if (lat >= 72 && lat < 84) {
      if (lon >= 0 && lon < 9) z = 31;
      else if (lon >= 9 && lon < 21) z = 33;
      else if (lon >= 21 && lon < 33) z = 35;
      else if (lon >= 33 && lon < 42) z = 37;
    }
    return z;
  }

  function bandaMgrs(lat) {
    if (lat < -80 || lat > 84) return null;
    const letras = 'CDEFGHJKLMNPQRSTUVWXX';
    const idx = Math.min(19, Math.max(0, Math.floor((lat + 80) / 8)));
    return letras[idx];
  }

  function aUtm(lat, lon) {
    if (typeof proj4 !== 'function') return null;
    const l = wrapLon(lon);
    if (lat < -80) {
      const [e, n] = proj4('EPSG:4326', PROJ_UPS_S, [l, lat]);
      return { polar: true, zona: l < 0 ? 'A' : 'B', hem: 'S', e, n };
    }
    if (lat > 84) {
      const [e, n] = proj4('EPSG:4326', PROJ_UPS_N, [l, lat]);
      return { polar: true, zona: l < 0 ? 'Y' : 'Z', hem: 'N', e, n };
    }
    const z = zonaUtm(lat, l);
    const hem = lat >= 0 ? 'N' : 'S';
    const def = `+proj=utm +zone=${z}${lat < 0 ? ' +south' : ''} +datum=WGS84 +units=m +no_defs`;
    const [e, n] = proj4('EPSG:4326', def, [l, lat]);
    return { polar: false, zona: z, hem, e, n };
  }

  function aMgrs(lat, lon) {
    const utm = aUtm(lat, lon);
    if (!utm) return null;
    const e5 = String(Math.floor(utm.e) % 100000).padStart(5, '0');
    const n5 = String(Math.floor(utm.n) % 100000).padStart(5, '0');
    if (utm.polar) {
      // MGRS polar (UPS) usa letras específicas en polos; reportamos designador UPS + 100 km.
      const colPolar = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
      const filaPolar = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
      const col = colPolar[Math.floor(utm.e / 100000) % colPolar.length];
      const fila = filaPolar[Math.floor(utm.n / 100000) % filaPolar.length];
      return `${utm.zona} ${col}${fila} ${e5} ${n5}`;
    }
    const banda = bandaMgrs(lat);
    const set = ((utm.zona - 1) % 6) + 1;
    const cols = ['ABCDEFGH', 'JKLMNPQR', 'STUVWXYZ'][(set - 1) % 3];
    const filas = set % 2 === 1 ? 'ABCDEFGHJKLMNPQRSTUV' : 'FGHJKLMNPQRSTUVABCDE';
    const colIdx = Math.floor(utm.e / 100000) - 1;
    const filaIdx = Math.floor(utm.n / 100000) % 20;
    const sq = (cols[colIdx] || 'A') + (filas[filaIdx] || 'A');
    return `${utm.zona}${banda} ${sq} ${e5} ${n5}`;
  }

  function gms(val, pos, neg) {
    const hemi = val >= 0 ? pos : neg;
    const abs = Math.abs(val);
    const d = Math.floor(abs);
    const mf = (abs - d) * 60;
    const m = Math.floor(mf);
    const s = ((mf - m) * 60).toFixed(1);
    return `${d}° ${String(m).padStart(2, '0')}' ${s.padStart(4, '0')}" ${hemi}`;
  }

  function formatear(lat, lon, sistema) {
    const l = wrapLon(lon);
    if (!Number.isFinite(lat) || !Number.isFinite(l)) return { texto: '—', nota: '' };
    switch (sistema) {
      case 'wgs84_dec':
        return { texto: `${lat.toFixed(4)}°, ${l.toFixed(4)}°`, nota: 'Geographic WGS84 (EPSG:4326)' };
      case 'wgs84_dms':
        return { texto: `${gms(lat, 'N', 'S')}, ${gms(l, 'E', 'W')}`, nota: 'Degrees, minutes, seconds (WGS84)' };
      case 'wgs84_rad':
        return {
          texto: `${(lat * Math.PI / 180).toFixed(6)} rad, ${(l * Math.PI / 180).toFixed(6)} rad`,
          nota: 'Latitude, longitude in radians'
        };
      case 'utm': {
        const u = aUtm(lat, l);
        if (!u) return { texto: 'Projection library unavailable', nota: '' };
        const etq = u.polar ? `UPS ${u.zona}` : `${u.zona}${u.hem}`;
        return {
          texto: `${etq} ${Math.round(u.e)} E, ${Math.round(u.n)} N m`,
          nota: u.polar ? 'Universal Polar Stereographic (WGS84)' : 'Universal Transverse Mercator (WGS84)'
        };
      }
      case 'mgrs': {
        const m = aMgrs(lat, l);
        if (!m) return { texto: 'Projection library unavailable', nota: '' };
        return { texto: m, nota: '1 m precision Military Grid Reference System' };
      }
      case 'epsg3857': {
        if (typeof proj4 !== 'function') return { texto: 'Projection library unavailable', nota: '' };
        const latClamped = Math.max(-85.05112878, Math.min(85.05112878, lat));
        const [x, y] = proj4('EPSG:4326', 'EPSG:3857', [l, latClamped]);
        return {
          texto: `${x.toFixed(1)} E, ${y.toFixed(1)} N m`,
          nota: lat !== latClamped ? 'Clamped to Web Mercator ±85.05° limit' : 'Web Mercator (EPSG:3857)'
        };
      }
      case 'epsg32616': {
        if (typeof proj4 !== 'function') return { texto: 'Projection library unavailable', nota: '' };
        const [e, n] = proj4('EPSG:4326', PROJ_32616, [l, lat]);
        const fuera = l < -90 || l > -84 || lat < 0;
        return {
          texto: `${Math.round(e)} E, ${Math.round(n)} N m`,
          nota: fuera ? 'Note: point is outside UTM 16N (90°W–84°W, N)' : 'Nicaragua official UTM zone 16N (EPSG:32616)'
        };
      }
      default:
        return { texto: `${lat.toFixed(4)}°, ${l.toFixed(4)}°`, nota: '' };
    }
  }

  // Construcción del panel plegable de coordenadas.
  function nodo(tag, cls, txt) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (txt !== undefined) el.textContent = txt;
    return el;
  }

  const panel = nodo('section', 'coords-panel');
  panel.id = 'panel-coordenadas';
  panel.setAttribute('aria-label', 'Coordinates and reference systems');

  const cab = nodo('div', 'coords-cabecera');
  const toggle = nodo('button', 'coords-toggle', 'Coords ▾');
  toggle.type = 'button';
  toggle.id = 'coords-toggle';
  toggle.setAttribute('aria-expanded', 'false');
  toggle.setAttribute('aria-controls', 'coords-cuerpo');

  const resumen = nodo('span', 'coords-resumen', '12.1364°, -86.2514°');
  cab.append(toggle, resumen);

  const cuerpo = nodo('div', 'coords-cuerpo');
  cuerpo.id = 'coords-cuerpo';
  cuerpo.hidden = true;

  const fila = nodo('div', 'coords-fila');
  const sel = nodo('select', 'coords-select');
  sel.id = 'coords-sistema';
  sel.setAttribute('aria-label', 'Coordinate reference system');
  SISTEMAS.forEach(([val, label]) => sel.add(new Option(label, val)));

  const btnCopiar = nodo('button', 'coords-copiar', 'Copy');
  btnCopiar.type = 'button';
  btnCopiar.id = 'coords-copiar';
  btnCopiar.setAttribute('aria-label', 'Copy formatted coordinates');

  fila.append(sel, btnCopiar);

  const valor = nodo('div', 'coords-valor', '12.1364°, -86.2514°');
  valor.id = 'coords-valor';
  valor.setAttribute('role', 'status');
  valor.setAttribute('aria-live', 'polite');

  const nota = nodo('p', 'coords-nota', 'Geographic WGS84 (EPSG:4326)');
  cuerpo.append(fila, valor, nota);
  panel.append(cab, cuerpo);

  // En la columna de capas (junto a la retícula), no flotando sobre las ventanas: fijo abajo a la izquierda
  // tapaba el pronóstico y las gráficas. Si la columna no existe, se queda al final de <main>.
  const columna = document.querySelector('#barra-capas .ventana-cuerpo');
  if (columna) { panel.classList.add('coords-en-capas'); columna.prepend(panel); }
  else (document.querySelector('main') || document.body).append(panel);
  // Opcional: apagado por defecto; solo aparece si el usuario marca «Coordinates» (se recuerda en este navegador).
  const opcion = nodo('label', 'chk coords-opcion');
  const casilla = nodo('input');
  casilla.type = 'checkbox';
  casilla.id = 'coords-visible';
  opcion.append(casilla, ' Coordinates');
  let activo = false;
  try { activo = localStorage.getItem('etd-coords-visible') === '1'; } catch (e) { /* sin almacenamiento */ }
  casilla.checked = activo;
  panel.hidden = !activo;
  casilla.onchange = () => {
    panel.hidden = !casilla.checked;
    try { localStorage.setItem('etd-coords-visible', casilla.checked ? '1' : '0'); } catch (e) { /* sin almacenamiento */ }
  };
  if (columna) columna.prepend(opcion);
  else panel.before(opcion);

  let punto = { lat: 12.1364, lon: -86.2514 };

  function pintar() {
    const res = formatear(punto.lat, punto.lon, sel.value);
    valor.textContent = res.texto;
    resumen.textContent = res.texto;
    nota.textContent = res.nota;
  }

  function actualizar(lat, lon) {
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
    punto = { lat, lon: wrapLon(lon) };
    pintar();
  }

  function setPlegado(plegado) {
    cuerpo.hidden = plegado;
    toggle.setAttribute('aria-expanded', String(!plegado));
    toggle.textContent = plegado ? 'Coords ▸' : 'Coords ▾';
  }
  setPlegado(true);

  toggle.onclick = () => setPlegado(!cuerpo.hidden);
  sel.onchange = pintar;

  panel.addEventListener('keydown', ev => {
    if (ev.key === 'Escape' && !cuerpo.hidden) {
      ev.preventDefault();
      setPlegado(true);
      toggle.focus();
    }
  });

  btnCopiar.onclick = async () => {
    const texto = valor.textContent;
    try {
      await navigator.clipboard.writeText(texto);
      btnCopiar.textContent = 'Copied!';
    } catch (_) {
      btnCopiar.textContent = 'Select & Ctrl+C';
    }
    setTimeout(() => { btnCopiar.textContent = 'Copy'; }, 1500);
  };

  // Escucha movimiento y clic en el mapa Leaflet global (y eventos sicc:punto).
  function enlazarMapa() {
    if (typeof mapa === 'undefined' || !mapa) return false;
    mapa.on('mousemove', ev => actualizar(ev.latlng.lat, ev.latlng.lng));
    mapa.on('click', ev => actualizar(ev.latlng.lat, ev.latlng.lng));
    return true;
  }
  if (!enlazarMapa()) {
    window.addEventListener('load', enlazarMapa, { once: true });
  }
  document.addEventListener('sicc:punto', ev => {
    if (Array.isArray(ev.detail) && ev.detail.length >= 2) {
      actualizar(Number(ev.detail[0]), Number(ev.detail[1]));
    }
  });

  // Inicializa tras carga de proj4 (script defer).
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', pintar);
  else setTimeout(pintar, 0);

  window.SICC_coordenadas = { actualizar, formatear, aUtm, aMgrs, zonaUtm, bandaMgrs };
})();
