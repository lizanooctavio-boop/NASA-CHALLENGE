import { mkdir, writeFile } from 'node:fs/promises';

const origen = 'https://sicc952.onrender.com';
const salida = 'public/clima-base';
const variables = ['temperatura_c', 'precipitacion_mm', 'viento', 'rafagas_ms', 'nubes_pct', 'humedad_pct', 'presion_hpa'];
const capas = ['GOES-East_ABI_GeoColor', 'IMERG_Precipitation_Rate_30min',
  'GHRSST_L4_MUR_Sea_Surface_Temperature_Anomalies', 'MODIS_Combined_Value_Added_AOD'];
const csv = ['enos', 'tormentas'];

// SICC-952 corre en Render gratuito: dormido responde 502/503 o se agota hasta que arranca (~1 min).
async function obtener(ruta, intentos = 6) {
  for (let i = 1; ; i++) {
    try {
      const respuesta = await fetch(origen + '/api/' + ruta, { signal: AbortSignal.timeout(25000) });
      if (respuesta.ok) return respuesta;
      if (respuesta.status < 500 || i >= intentos) throw Error(ruta + ': HTTP ' + respuesta.status);
    } catch (e) {
      if (i >= intentos || e.message.startsWith(ruta + ': HTTP 4')) throw e;
    }
    await new Promise(r => setTimeout(r, 15000));
  }
}

async function json(ruta) { return (await obtener(ruta)).json(); }
async function guardar(nombre, datos) { await writeFile(salida + '/' + nombre + '.json', JSON.stringify(datos)); }
async function guardarApi(nombre, ruta = nombre) { await guardar(nombre, await json(ruta)); }
async function ejecutar(tareas, concurrencia = 5) {
  const fallos = [];
  let i = 0;
  await Promise.all(Array.from({ length: concurrencia }, async () => {
    while (i < tareas.length) {
      try { await tareas[i++](); } catch (e) { fallos.push(e.message); }
    }
  }));
  return fallos;
}

await mkdir(salida, { recursive: true });
let meta;
try {
  meta = await json('global_meta');
} catch (e) {
  // Sin fuente no se tumba el despliegue: public/clima-base conserva la instantánea anterior.
  console.warn('Pronóstico no disponible; se conserva la instantánea anterior:', e.message);
  process.exit(0);
}
const tareas = meta.horas_utc.flatMap((_, paso) => variables.map(variable => async () => {
  const campo = await json(`global?var=${variable}&paso=${paso}`);
  if (campo.corrida_utc !== meta.corrida_utc || campo.hora_utc !== meta.horas_utc[paso]) {
    throw Error('El proveedor cambió de corrida: ' + variable + '/' + paso);
  }
  await guardar(`global-${variable}-${paso}`, campo);
}));
tareas.unshift(...['campo_nicaragua', 'enos', 'tormentas'].map(n => () => guardarApi(n)));
tareas.push(...capas.map(capa => () => guardarApi('gibs-' + capa, 'gibs_hora?capa=' + encodeURIComponent(capa))));
tareas.push(...csv.map(nombre => async () => {
  const r = await obtener('exportar/' + nombre + '.csv');
  await writeFile(salida + '/' + nombre + '.csv', await r.text());
}));
tareas.push(async () => {
  const datos = await json('series');
  const ventanas = { 'maíz': 'Reference season 1', arroz: 'Reference season 2', frijol: 'Reference season 3' };
  const proyecciones = datos.escenarios_anuales.map(({ escenario, cultivo, anio, dT, dP }) =>
    ({ escenario, ventana: ventanas[cultivo], anio, dT, dP }));
  await guardar('series', { proyecciones });
  await writeFile(salida + '/proyecciones.csv',
    '# CMIP6, Central America (SCA); seasonal change vs. 1981-1995.\nscenario,season,year,delta_t_c,delta_p_pct\n' +
    proyecciones.map(f => [f.escenario, f.ventana, f.anio, f.dT, f.dP].join(',')).join('\n') + '\n');
});
const fallos = await ejecutar(tareas);
await guardar('global_meta', { ...meta, instantanea_utc: new Date().toISOString() });
if (fallos.length) console.warn('Datos meteorológicos parciales:', fallos.join(' | '));
console.log(`Malla meteorológica ${meta.corrida_utc}: ${tareas.length - fallos.length}/${tareas.length} recursos.`);
