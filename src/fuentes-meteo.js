(function () {
  'use strict';
  // Traduce las rutas /api/* del visor a los archivos estáticos que guarda la compilación en /clima-base/.
  const archivos = new Set(['global_meta', 'campo_nicaragua', 'enos', 'tormentas', 'series']);
  const campos = new Set(['temperatura_c', 'precipitacion_mm', 'viento', 'rafagas_ms', 'nubes_pct', 'humedad_pct', 'presion_hpa']);
  const capas = new Set(['GOES-East_ABI_GeoColor', 'IMERG_Precipitation_Rate_30min',
    'GHRSST_L4_MUR_Sea_Surface_Temperature_Anomalies', 'MODIS_Combined_Value_Added_AOD']);

  // Pronóstico puntual en cualquier lugar del mundo (Open-Meteo, ECMWF IFS 0,25°).
  async function punto(q) {
    const lat = Number(q.get('lat')), lon = Number(q.get('lon'));
    if (!Number.isFinite(lat + lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      return Response.json({ error: 'Invalid coordinates.' }, { status: 400 });
    }
    const params = new URLSearchParams({
      latitude: lat, longitude: lon, models: 'ecmwf_ifs025', timezone: 'GMT', wind_speed_unit: 'ms', forecast_hours: 48,
      current: 'temperature_2m,precipitation,wind_speed_10m,wind_direction_10m',
      hourly: 'temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m'
    });
    const r = await fetch('https://api.open-meteo.com/v1/forecast?' + params, { signal: AbortSignal.timeout(12000) });
    if (!r.ok) return Response.json({ error: 'Forecast service responded ' + r.status }, { status: r.status });
    const datos = await r.json();
    return Response.json({ datos, fuente: 'Open-Meteo · ECMWF IFS 0.25°', consulta_utc: new Date().toISOString() });
  }

  function solicitud(ruta) {
    const url = new URL(ruta, location.origin), q = url.searchParams;
    const nombre = url.pathname.replace(/^\/api\//, '');
    if (nombre === 'tiempo') return punto(q);
    if (archivos.has(nombre)) return fetch('/clima-base/' + nombre + '.json');
    if (nombre === 'global' && campos.has(q.get('var')) && /^\d{1,2}$/.test(q.get('paso') || '')) {
      return fetch('/clima-base/global-' + q.get('var') + '-' + q.get('paso') + '.json');
    }
    if (nombre === 'gibs_hora' && capas.has(q.get('capa'))) return fetch('/clima-base/gibs-' + q.get('capa') + '.json');
    return Promise.resolve(Response.json({ error: 'Resource unavailable.' }, { status: 404 }));
  }

  window.FuentesMeteo = { fetch: solicitud };
})();
