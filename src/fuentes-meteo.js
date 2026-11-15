(function () {
  'use strict';
  // Traduce las rutas /api/* del visor a los archivos estáticos que guarda la compilación en /clima-base/.
  // Si /clima-base/enos.json no existe en modo desarrollo local, usa el ONI de data/fuentes/oni_2001_2024.csv.
  const archivos = new Set(['global_meta', 'campo_nicaragua', 'enos', 'tormentas', 'series']);
  const campos = new Set(['temperatura_c', 'precipitacion_mm', 'viento', 'rafagas_ms', 'nubes_pct', 'humedad_pct', 'presion_hpa']);
  const capas = new Set(['GOES-East_ABI_GeoColor', 'IMERG_Precipitation_Rate_30min',
    'GHRSST_L4_MUR_Sea_Surface_Temperature_Anomalies', 'MODIS_Combined_Value_Added_AOD']);
  const TEMPORADAS = ['', 'DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'];

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
    let r;
    try {
      r = await fetch('https://api.open-meteo.com/v1/forecast?' + params, { signal: AbortSignal.timeout(12000) });
    } catch (_) {
      return new Response(JSON.stringify({ error: 'Could not reach Open-Meteo weather service. Please try again later.' }), { status: 503, headers: { 'Content-Type': 'application/json' } });
    }
    if (!r.ok) return Response.json({ error: 'Forecast service responded ' + r.status }, { status: r.status });
    const datos = await r.json();
    return Response.json({ datos, fuente: 'Open-Meteo · ECMWF IFS 0.25°', consulta_utc: new Date().toISOString() });
  }

  async function fetchSeguro(url, msg) { try { return await fetch(url); } catch (_) { return Response.json({ error: msg || 'Resource temporarily unavailable.' }, { status: 503 }); } }
  async function enosLocal() {
    let r = null;
    try { r = await fetch('/clima-base/enos.json'); if (r.ok) return r; } catch (_) {}


    let csv;
    try { csv = await fetch('data/fuentes/oni_2001_2024.csv'); } catch (_) { return r || Response.json({ error: 'ENSO index is currently unavailable.' }, { status: 503 }); }
    if (!csv.ok) return r || Response.json({ error: 'ENSO index is currently unavailable.' }, { status: csv.status || 503 });
    const lineas = (await csv.text()).trim().split(/\r?\n/).slice(1);
    const oni_local = lineas.map(l => {
      const [a, m, v] = l.split(',');
      return { anio: Number(a), mes: Number(m), oni: Number(v) };
    }).filter(x => Number.isFinite(x.oni));
    if (!oni_local.length) return r || Response.json({ error: 'ENSO index is currently unavailable.' }, { status: 503 });
    const ult = oni_local.at(-1);
    const fase = ult.oni >= 0.5 ? 'El Niño' : ult.oni <= -0.5 ? 'La Niña' : 'Neutral';
    return Response.json({
      oni_local,
      fuente_local: 'NOAA CPC · data/fuentes/oni_2001_2024.csv',
      cpc: { ultimas: [{ temporada: TEMPORADAS[ult.mes] || 'NDJ', anio: ult.anio, oni: ult.oni }] },
      nino34_semanal: { semanas: [] },
      fase_actual: fase,
      oni_actual: ult.oni
    });
  }

  function solicitud(ruta) {
    const url = new URL(ruta, location.origin), q = url.searchParams;
    const nombre = url.pathname.replace(/^\/api\//, '');
    if (nombre === 'tiempo') return punto(q);
    if (nombre === 'enos') return enosLocal();
    if (archivos.has(nombre)) return fetchSeguro('/clima-base/' + nombre + '.json');
    if (nombre === 'global' && campos.has(q.get('var')) && /^\d{1,2}$/.test(q.get('paso') || '')) {
      return fetchSeguro('/clima-base/global-' + q.get('var') + '-' + q.get('paso') + '.json');
    }
    if (nombre === 'gibs_hora' && capas.has(q.get('capa'))) return fetchSeguro('/clima-base/gibs-' + q.get('capa') + '.json');
    return Promise.resolve(Response.json({ error: 'Resource unavailable.' }, { status: 404 }));
  }

  window.FuentesMeteo = { fetch: solicitud };
})();
