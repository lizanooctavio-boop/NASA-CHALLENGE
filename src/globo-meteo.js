(function () {
  'use strict';
  const RAD = Math.PI / 180;
  const TERMICA = {
    nombre: 'Temperatura a 2 m', unidad: '°C', etiquetas: [-45, -25, -10, 0, 15, 25, 35, 45],
    tramos: [[-50,[221,240,250]],[-35,[172,193,249]],[-20,[86,105,204]],[-8,[29,129,199]],
      [0,[63,196,218]],[10,[128,206,142]],[20,[254,218,90]],[28,[250,153,47]],
      [34,[229,71,42]],[40,[161,22,55]],[46,[85,12,42]]]
  };
  const escala = v => v === 'temperatura_c' ? TERMICA : window.PaletasMeteo.escalas[v];

  function muestreador(meta, matriz) {
    if (!matriz || !meta.latitudes?.length || !meta.longitudes?.length) return () => null;
    const lat0 = meta.latitudes[0], lon0 = meta.longitudes[0];
    const dy = meta.latitudes[1] - lat0, dx = meta.longitudes[1] - lon0;
    const n = meta.longitudes.length;
    return (lon, lat) => {
      const y = (lat - lat0) / dy, x = (lon - lon0) / dx;
      if (y < 0 || y > matriz.length - 1) return null;
      const i = Math.min(Math.floor(y), matriz.length - 2), j0 = Math.floor(x);
      const j = (j0 % n + n) % n, k = (j + 1) % n;
      const a = y - i, b = x - j0;
      const nw = matriz[i][j], ne = matriz[i][k], sw = matriz[i + 1][j], se = matriz[i + 1][k];
      if (nw == null || ne == null || sw == null || se == null) return null;
      return ((1 - b) * nw + b * ne) * (1 - a) + ((1 - b) * sw + b * se) * a;
    };
  }

  function textura(meta, datos, variable) {
    const paleta = escala(variable);
    if (!datos || !paleta) return null;
    const campo = muestreador(meta, datos[variable]);
    const u = muestreador(meta, datos.viento_u_ms), v = muestreador(meta, datos.viento_v_ms);
    const canvas = document.createElement('canvas');
    canvas.width = 720;
    canvas.height = 360;
    const ctx = canvas.getContext('2d'), img = ctx.createImageData(canvas.width, canvas.height);
    const tabla = Array.from({ length: 641 }, (_, i) =>
      window.PaletasMeteo.color(variable, i / 640, paleta, true));
    const minimo = paleta.tramos[0][0], maximo = paleta.tramos.at(-1)[0];
    for (let y = 0; y < canvas.height; y++) {
      const lat = 90 - (y + .5) * 180 / canvas.height;
      for (let x = 0; x < canvas.width; x++) {
        const lon = (x + .5) * 360 / canvas.width - 180;
        let valor = campo(lon, lat);
        if (variable === 'viento_ms') {
          const a = u(lon, lat), b = v(lon, lat);
          valor = a == null || b == null ? null : Math.hypot(a, b);
        }
        if (valor === null || (paleta.minimo !== undefined && valor < paleta.minimo)) continue;
        const i = (y * canvas.width + x) * 4;
        const c = tabla[Math.min(640, Math.max(0, Math.round((valor - minimo) * 640 / (maximo - minimo))))];
        img.data[i] = c[0];
        img.data[i + 1] = c[1];
        img.data[i + 2] = c[2];
        img.data[i + 3] = 255 * c[3];
      }
    }
    ctx.putImageData(img, 0, 0);
    return canvas;
  }

  function viento(canvas, proyectar) {
    const ctx = canvas.getContext('2d');
    const reducir = matchMedia('(prefers-reduced-motion: reduce)');
    const semillas = Array.from({ length: 820 }, () => ({}));
    let u, v, activo, frame = 0;
    function sembrar(p) {
      p.lon = Math.random() * 360 - 180;
      p.lat = Math.asin(2 * Math.random() - 1) / RAD;
      p.edad = 24 + Math.random() * 100;
    }
    function dibujar() {
      frame = 0;
      if (!canvas.isConnected || document.hidden || !activo || !u || !v) return;
      const estatica = reducir.matches;
      ctx.globalCompositeOperation = 'destination-out';
      ctx.fillStyle = estatica ? '#000' : 'rgba(0,0,0,.14)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.globalCompositeOperation = 'source-over';
      ctx.lineWidth = Math.max(1, canvas.width / 420);
      ctx.strokeStyle = 'rgba(255,255,255,.76)';
      ctx.beginPath();
      for (const p of semillas) {
        if (--p.edad <= 0 || Math.abs(p.lat) > 85) sembrar(p);
        for (let i = 0; i < (estatica ? 9 : 1); i++) {
          const antes = proyectar(p.lon, p.lat), a = u(p.lon, p.lat), b = v(p.lon, p.lat);
          if (a == null || b == null) { sembrar(p); break; }
          p.lon = ((p.lon + a * .045 / Math.max(.16, Math.cos(p.lat * RAD)) + 540) % 360) - 180;
          p.lat += b * .045;
          const despues = proyectar(p.lon, p.lat);
          if (!antes || !despues) continue;
          ctx.moveTo(antes[0], antes[1]);
          ctx.lineTo(despues[0], despues[1]);
        }
      }
      ctx.stroke();
      if (!estatica) frame = requestAnimationFrame(dibujar);
    }
    function renovar() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (!frame && activo && u && v) frame = requestAnimationFrame(dibujar);
    }
    reducir.addEventListener('change', renovar);
    document.addEventListener('visibilitychange', renovar);
    semillas.forEach(sembrar);
    return {
      actualizar(meta, campo, visible) {
        activo = visible && Boolean(campo);
        u = activo ? muestreador(meta, campo.viento_u_ms) : null;
        v = activo ? muestreador(meta, campo.viento_v_ms) : null;
        canvas.hidden = !activo;
        renovar();
      },
      renovar
    };
  }

  window.GloboMeteo = { escala, textura, viento };
})();
