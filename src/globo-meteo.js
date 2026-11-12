(function () {
  'use strict';
  const escala = v => window.PaletasMeteo.escalas[v];

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

  // Textura equirectangular (lon −180…180) de la capa meteorológica para el globo 3D.
  function textura(meta, datos, variable) {
    const paleta = escala(variable);
    if (!datos || !paleta) return null;
    const campo = muestreador(meta, datos[variable]);
    const u = muestreador(meta, datos.viento_u_ms), v = muestreador(meta, datos.viento_v_ms);
    const canvas = document.createElement('canvas');
    canvas.width = 1080;
    canvas.height = 540;
    const ctx = canvas.getContext('2d'), img = ctx.createImageData(canvas.width, canvas.height);
    for (let y = 0; y < canvas.height; y++) {
      const lat = 90 - (y + .5) * 180 / canvas.height;
      for (let x = 0; x < canvas.width; x++) {
        const lon = (x + .5) * 360 / canvas.width - 180;
        let valor = campo(lon, lat);
        if (variable === 'viento_ms') {
          const a = u(lon, lat), b = v(lon, lat);
          valor = a == null || b == null ? null : Math.hypot(a, b);
        }
        if (valor === null) continue;
        const c = window.PaletasMeteo.color(variable, valor, paleta);
        if (!c) continue;
        const i = (y * canvas.width + x) * 4;
        img.data[i] = c[0];
        img.data[i + 1] = c[1];
        img.data[i + 2] = c[2];
        img.data[i + 3] = 255 * c[3];
      }
    }
    ctx.putImageData(img, 0, 0);
    return canvas;
  }

  window.GloboMeteo = { escala, textura };
})();
