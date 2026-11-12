(function () {
  'use strict';

  const RAD = Math.PI / 180;
  const NICARAGUA = [-85.1, 12.8];
  const PUNTOS = [
    ['Nicaragua', -85.1, 12.8, 'nicaragua', 22, 5],
    ['Honduras', -86.6, 14.8, 'honduras', -17, -13],
    ['Costa Rica', -84.1, 9.9, 'costa_rica', -17, 22]
  ];
  const ANCHO = 2048, ALTO = ANCHO / 2;
  const limitar = (v, min, max) => Math.min(max, Math.max(min, v));

  function texturaMundial(ctx) {
    ctx.fillStyle = '#102523';
    ctx.fillRect(0, 0, ANCHO, ALTO);
    function trazar(tipo, relleno, borde) {
      window.SOF_BASE_MUNDIAL.filter(p => p.tipo === tipo).forEach(p => {
        trazarPoligono(ctx, p.anillos);
        ctx.fillStyle = relleno;
        ctx.fill('evenodd');
        ctx.strokeStyle = borde;
        ctx.lineWidth = 1;
        ctx.stroke();
      });
    }
    trazar('pais', '#54736a', '#66877d');
    trazar('lago', '#102523', '#45645e');

    ctx.beginPath();
    for (let x = 0; x <= ANCHO; x += ANCHO / 12) { ctx.moveTo(x, 0); ctx.lineTo(x, ALTO); }
    for (let y = 0; y <= ALTO; y += ALTO / 6) { ctx.moveTo(0, y); ctx.lineTo(ANCHO, y); }
    ctx.strokeStyle = 'rgba(195, 223, 201, .24)';
    ctx.stroke();
  }

  function trazarPoligono(ctx, anillos) {
    ctx.beginPath();
    for (const anillo of anillos) {
      anillo.forEach(([lon, lat], i) => {
        const x = (lon + 180) / 360 * ANCHO, y = (90 - lat) / 180 * ALTO;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
    }
  }

  function contiene(anillo, lon, lat) {
    let dentro = false;
    for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
      const [x, y] = anillo[i], [xx, yy] = anillo[j];
      if ((y > lat) !== (yy > lat) && lon < x + (lat - y) * (xx - x) / (yy - y)) dentro = !dentro;
    }
    return dentro;
  }

  function poligonos(r) {
    if (r.poligonos) return r.poligonos;
    if (r.id === 'caja_original' && r.bbox) {
      const [oeste, sur, este, norte] = r.bbox;
      return [[[[oeste, sur], [este, sur], [este, norte], [oeste, norte], [oeste, sur]]]];
    }
    const contorno = r.contorno || window.SOF_CONTORNOS.paises[r.id];
    return contorno ? [[contorno]] : [];
  }

  function crear(contenedor, alElegir) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    canvas.className = 'esfera';
    canvas.tabIndex = 0;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-describedby', 'ayuda-globo');
    canvas.textContent = 'Usa el selector de áreas para consultar las tendencias.';

    const atlas = document.createElement('canvas');
    atlas.width = ANCHO;
    atlas.height = ALTO;
    const mapa = atlas.getContext('2d', { willReadFrequently: true });
    const superficie = document.createElement('canvas');
    const pixelsContext = superficie.getContext('2d');
    texturaMundial(mapa);
    const base = mapa.getImageData(0, 0, ANCHO, ALTO);
    const trazas = document.createElement('canvas');
    trazas.className = 'trazas-viento';
    trazas.setAttribute('aria-hidden', 'true');
    const viento = window.GloboMeteo.viento(trazas, proyectar);

    let lon = NICARAGUA[0], lat = NICARAGUA[1];
    let regiones = [], seleccion = 'nicaragua', colores, pixeles, frame = 0, imagen;
    let marcas = [], centroX, centroY, radio, gesto = null;
    let ultimoCampo;

    function proyectar(lambda, phi) {
      const d = (lambda - lon) * RAD, p = phi * RAD, c = lat * RAD;
      const x = Math.cos(p) * Math.sin(d), y = Math.sin(p) * Math.cos(c) - Math.cos(p) * Math.cos(d) * Math.sin(c);
      const z = Math.sin(p) * Math.sin(c) + Math.cos(p) * Math.cos(d) * Math.cos(c);
      return z > .035 ? [centroX + radio * x, centroY - radio * y] : null;
    }

    function actualizar(nuevasRegiones, id, nuevosColores, textura) {
      if (!contenedor.contains(canvas)) contenedor.replaceChildren(canvas, trazas);
      if (regiones !== nuevasRegiones || seleccion !== id || !pixeles || ultimoCampo !== textura || colores.join() !== nuevosColores.join()) {
        regiones = nuevasRegiones;
        seleccion = id;
        colores = nuevosColores;
        ultimoCampo = textura;
        canvas.setAttribute('aria-label', 'Globo terrestre 3D. Área seleccionada: ' + regiones.find(r => r.id === id).nombre);
        mapa.putImageData(base, 0, 0);
        if (textura) {
          mapa.globalAlpha = .94;
          mapa.drawImage(textura, 0, 0, ANCHO, ALTO);
          mapa.globalAlpha = 1;
          mapa.strokeStyle = 'rgba(25,25,30,.55)';
          mapa.lineWidth = 1.25;
          window.SOF_BASE_MUNDIAL.forEach(p => { trazarPoligono(mapa, p.anillos); mapa.stroke(); });
        }
        regiones.slice().sort((a, b) => (a.id === 'caja_original') - (b.id === 'caja_original')).forEach(r => {
          poligonos(r).forEach(anillos => {
            trazarPoligono(mapa, anillos);
            mapa.fillStyle = colores[regiones.indexOf(r)];
            mapa.globalAlpha = textura ? 0 : r.id === id ? .95 : .62;
            if (!textura) mapa.fill('evenodd');
            mapa.globalAlpha = 1;
            mapa.strokeStyle = r.id === 'caja_original' ? '#ffd08a' : r.id === id ? '#f8efd5' : '#84a59b';
            mapa.lineWidth = r.id === id ? 2.1 : 1;
            mapa.stroke();
          });
        });
        pixeles = mapa.getImageData(0, 0, ANCHO, ALTO).data;
      }
      programar();
    }

    function programar() {
      if (!frame) frame = requestAnimationFrame(() => { frame = 0; dibujar(); });
    }

    function dibujar() {
      if (!canvas.isConnected || !canvas.clientWidth) return;
      const w = Math.min(620, Math.round(canvas.clientWidth * devicePixelRatio));
      const h = Math.round(w * canvas.clientHeight / canvas.clientWidth);
      if (!imagen || canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        superficie.width = w;
        superficie.height = h;
        trazas.width = w;
        trazas.height = h;
        imagen = ctx.createImageData(w, h);
      }
      const salida = imagen.data;
      salida.fill(0);
      centroX = w / 2;
      centroY = h / 2;
      radio = Math.min(w, h) * .462;
      const cl = Math.cos(lat * RAD), sl = Math.sin(lat * RAD);
      for (let y = Math.ceil(centroY - radio); y < centroY + radio; y++) {
        const norte = (centroY - y) / radio;
        const ancho = Math.sqrt(1 - norte * norte);
        for (let x = Math.ceil(centroX - radio * ancho); x < centroX + radio * ancho; x++) {
          const este = (x - centroX) / radio;
          const frente = Math.sqrt(Math.max(0, ancho * ancho - este * este));
          const phi = Math.asin(limitar(norte * cl + frente * sl, -1, 1));
          const lambda = Math.atan2(este, frente * cl - norte * sl) + lon * RAD;
          const u = ((Math.floor((lambda / Math.PI + 1) * ANCHO / 2) % ANCHO) + ANCHO) % ANCHO;
          const v = limitar(Math.floor((.5 - phi / Math.PI) * ALTO), 0, ALTO - 1);
          const origen = (v * ANCHO + u) * 4, destino = (y * w + x) * 4;
          const luz = .68 + Math.max(0, .75 * frente + .40 * norte - .34 * este) * .43;
          const borde = 1 - frente;
          salida[destino] = pixeles[origen] * luz + borde * 10;
          salida[destino + 1] = pixeles[origen + 1] * luz + borde * 25;
          salida[destino + 2] = pixeles[origen + 2] * luz + borde * 19;
          salida[destino + 3] = Math.min(255, (radio - Math.hypot(x - centroX, y - centroY)) * 255);
        }
      }
      ctx.clearRect(0, 0, w, h);
      ctx.beginPath();
      ctx.arc(centroX, centroY, radio + .4, 0, Math.PI * 2);
      ctx.strokeStyle = '#a7bda3';
      ctx.lineWidth = 1;
      ctx.stroke();
      pixelsContext.putImageData(imagen, 0, 0);
      ctx.drawImage(superficie, 0, 0);

      const escala = w / canvas.clientWidth;
      ctx.font = `600 ${12 * escala}px system-ui, sans-serif`;
      marcas = [];
      PUNTOS.forEach(([nombre, lambda, phi, id, dx, dy]) => {
        const d = (lambda - lon) * RAD, p = phi * RAD;
        const z = Math.sin(p) * sl + Math.cos(p) * Math.cos(d) * cl;
        if (z < .18) return;
        const x = centroX + radio * Math.cos(p) * Math.sin(d);
        const y = centroY - radio * (Math.sin(p) * cl - Math.cos(p) * Math.cos(d) * sl);
        const tx = x + dx * escala, ty = y + dy * escala, ancho = ctx.measureText(nombre).width;
        const izquierda = dx < 0 ? tx - ancho : tx;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(tx, ty);
        ctx.strokeStyle = id === seleccion ? '#ffd08a' : '#bdc7b4';
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(x, y, 2.5 * escala, 0, Math.PI * 2);
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();
        ctx.fillStyle = '#141d1b';
        ctx.fillRect(izquierda - 5 * escala, ty - 9 * escala, ancho + 10 * escala, 18 * escala);
        ctx.fillStyle = id === seleccion ? '#ffd08a' : '#f4eee0';
        ctx.textBaseline = 'middle';
        ctx.fillText(nombre, izquierda, ty);
        marcas.push({ id, izquierda, derecha: izquierda + ancho, y: ty });
      });
      viento.renovar();
    }

    function girar(dx, dy) {
      lon = ((lon + dx + 540) % 360) - 180;
      lat = limitar(lat + dy, -88, 88);
      programar();
    }

    function seleccionar(ev) {
      const rect = canvas.getBoundingClientRect(), escala = canvas.width / rect.width;
      const x = (ev.clientX - rect.left) * escala, y = (ev.clientY - rect.top) * escala;
      const marca = marcas.find(m => x >= m.izquierda - 7 * escala && x <= m.derecha + 7 * escala && Math.abs(y - m.y) < 10 * escala);
      if (marca) return alElegir(marca.id);
      const este = (x - centroX) / radio, norte = (centroY - y) / radio;
      if (este * este + norte * norte >= 1) return;
      const frente = Math.sqrt(1 - este * este - norte * norte);
      const cl = Math.cos(lat * RAD), sl = Math.sin(lat * RAD);
      const phi = Math.asin(limitar(norte * cl + frente * sl, -1, 1)) / RAD;
      const lambda = ((Math.atan2(este, frente * cl - norte * sl) / RAD + lon + 540) % 360) - 180;
      const caja = regiones.find(r => r.id === 'caja_original');
      const r = [caja, ...regiones.filter(r => r !== caja)].find(r => r && poligonos(r).some(anillos =>
        contiene(anillos[0], lambda, phi) && !anillos.slice(1).some(a => contiene(a, lambda, phi))));
      if (r) alElegir(r.id);
    }

    canvas.addEventListener('pointerdown', ev => {
      if (ev.button !== 0 || gesto) return;
      gesto = { id: ev.pointerId, x: ev.clientX, y: ev.clientY, movido: false };
      canvas.setPointerCapture(ev.pointerId);
    });
    canvas.addEventListener('pointermove', ev => {
      if (!gesto || gesto.id !== ev.pointerId) return;
      const dx = ev.clientX - gesto.x, dy = ev.clientY - gesto.y;
      if (!gesto.movido && Math.hypot(dx, dy) < 4) return;
      gesto = { id: ev.pointerId, x: ev.clientX, y: ev.clientY, movido: true };
      const paso = 180 / Math.min(canvas.clientWidth, canvas.clientHeight);
      girar(-dx * paso, dy * paso);
    });
    canvas.addEventListener('pointerup', ev => {
      if (!gesto || gesto.id !== ev.pointerId) return;
      if (!gesto.movido) seleccionar(ev);
      gesto = null;
    });
    canvas.addEventListener('lostpointercapture', () => { gesto = null; });
    canvas.addEventListener('keydown', ev => {
      const pasos = { ArrowLeft: [-12, 0], ArrowRight: [12, 0], ArrowUp: [0, 8], ArrowDown: [0, -8] };
      if (!pasos[ev.key]) return;
      ev.preventDefault();
      girar(...pasos[ev.key]);
    });

    return {
      actualizar,
      viento: viento.actualizar,
      centrar: () => {
        [lon, lat] = NICARAGUA;
        programar();
      }
    };
  }

  window.SofGlobo = { crear };
})();
