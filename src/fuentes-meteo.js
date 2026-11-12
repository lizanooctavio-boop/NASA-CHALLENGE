(function () {
  'use strict';
  const archivos = new Set(['global_meta', 'campo_nicaragua', 'territorio', 'tendencia_precipitacion', 'enos', 'tormentas', 'series', 'grilla']);
  const campos = new Set(['temperatura_c', 'precipitacion_mm', 'viento', 'rafagas_ms', 'nubes_pct', 'humedad_pct', 'presion_hpa']);
  const capas = new Set(['GOES-East_ABI_GeoColor', 'IMERG_Precipitation_Rate_30min',
    'GHRSST_L4_MUR_Sea_Surface_Temperature_Anomalies', 'MODIS_Combined_Value_Added_AOD']);

  async function punto(q) {
    const lat = Number(q.get('lat')), lon = Number(q.get('lon'));
    if (lat < 5 || lat > 20 || lon < -95 || lon > -75 || !Number.isFinite(lat + lon)) {
      return Response.json({ error: 'La consulta puntual abarca Centroamérica.' }, { status: 400 });
    }
    const params = new URLSearchParams({
      latitude: lat, longitude: lon, models: 'ecmwf_ifs025', timezone: 'GMT', wind_speed_unit: 'ms',
      current: 'temperature_2m,precipitation,wind_speed_10m,wind_direction_10m'
    });
    const r = await fetch('https://api.open-meteo.com/v1/forecast?' + params, { signal: AbortSignal.timeout(10000) });
    if (!r.ok) return Response.json({ error: 'Open-Meteo respondió HTTP ' + r.status }, { status: r.status });
    const datos = await r.json();
    return Response.json({ datos, fuente: 'Open-Meteo · ECMWF IFS 0,25°', consulta_utc: new Date().toISOString(), hora_corrida: 'No publicada por el servicio puntual' });
  }

  function csvMeteorologico(nombre, q) {
    const visor = window.SICC_campo, datos = visor?.datos();
    if (!datos) return Response.json({ error: 'La malla regional no está disponible.' }, { status: 503 });
    const variables = Object.keys(datos.variables);
    const filas = [];
    let columnas;
    if (nombre === 'campo') {
      const hora = q.get('hora_utc') || datos.horas_utc[datos.indice_actual];
      const paso = datos.horas_utc.indexOf(hora);
      if (paso === -1) return Response.json({ error: 'La hora no está en la corrida guardada.' }, { status: 400 });
      columnas = ['hora_utc', 'latitud', 'longitud', ...variables];
      datos.latitudes.forEach((lat, i) => datos.longitudes.forEach((lon, j) => {
        filas.push([hora, lat, lon, ...variables.map(v => datos.variables[v][paso][i][j])]);
      }));
    } else {
      const lat = Number(q.get('lat')), lon = Number(q.get('lon'));
      const serie = visor.serie(lat, lon);
      if (!serie) return Response.json({ error: 'Punto fuera de la malla regional.' }, { status: 400 });
      columnas = ['hora_utc', 'latitud', 'longitud', ...variables];
      serie.horas.forEach((hora, i) => filas.push([hora, lat, lon, ...variables.map(v => serie[v][i])]));
    }
    const cabecera = ['# Fuente: ' + datos.fuente, '# Consulta original: ' + datos.consulta_utc,
      '# Estimaciones de modelo en UTC; instantánea guardada.'];
    const csv = '\uFEFF' + cabecera.concat(columnas.join(','), filas.map(f => f.join(','))).join('\r\n') + '\r\n';
    return new Response(csv, { headers: { 'Content-Type': 'text/csv; charset=utf-8' } });
  }

  function solicitud(ruta) {
    const url = new URL(ruta, location.origin), q = url.searchParams;
    const nombre = url.pathname.replace(/^\/api\//, '');
    if (nombre === 'tiempo') return punto(q);
    if (nombre === 'exportar/campo.csv') return Promise.resolve(csvMeteorologico('campo', q));
    if (nombre === 'exportar/pronostico_punto.csv') return Promise.resolve(csvMeteorologico('pronostico_punto', q));
    if (archivos.has(nombre)) return fetch('/clima-base/' + nombre + '.json');
    if (nombre === 'global' && campos.has(q.get('var')) && /^\d{1,2}$/.test(q.get('paso') || '')) {
      return fetch('/clima-base/global-' + q.get('var') + '-' + q.get('paso') + '.json');
    }
    if (nombre === 'gibs_hora' && capas.has(q.get('capa'))) return fetch('/clima-base/gibs-' + q.get('capa') + '.json');
    return Promise.resolve(Response.json({ error: 'Recurso climático no disponible.' }, { status: 404 }));
  }

  window.FuentesMeteo = { fetch: solicitud };
})();
