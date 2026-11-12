import { mkdir, writeFile } from 'node:fs/promises';

const origen = 'https://sicc952.onrender.com';
const salida = 'public/clima-base';
const variables = ['temperatura_c', 'precipitacion_mm', 'viento', 'rafagas_ms', 'nubes_pct', 'humedad_pct', 'presion_hpa'];
const capas = ['GOES-East_ABI_GeoColor', 'IMERG_Precipitation_Rate_30min',
  'GHRSST_L4_MUR_Sea_Surface_Temperature_Anomalies', 'MODIS_Combined_Value_Added_AOD'];
const csv = ['serie_cuenca', 'enos', 'tormentas', 'tormentas_historicas', 'tendencia_precipitacion_anual', 'tendencia_precipitacion_mensual_imerg'];

async function obtener(ruta) {
  const respuesta = await fetch(origen + '/api/' + ruta, { signal: AbortSignal.timeout(25000) });
  if (!respuesta.ok) throw Error(ruta + ': HTTP ' + respuesta.status);
  return respuesta;
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
const meta = await json('global_meta');
const tareas = meta.horas_utc.flatMap((_, paso) => variables.map(variable => async () => {
  const campo = await json(`global?var=${variable}&paso=${paso}`);
  if (campo.corrida_utc !== meta.corrida_utc || campo.hora_utc !== meta.horas_utc[paso]) {
    throw Error('El proveedor cambió de corrida: ' + variable + '/' + paso);
  }
  await guardar(`global-${variable}-${paso}`, campo);
}));
tareas.unshift(...['campo_nicaragua', 'territorio', 'tendencia_precipitacion', 'enos', 'tormentas', 'grilla'].map(n => () => guardarApi(n)));
tareas.push(...capas.map(capa => () => guardarApi('gibs-' + capa, 'gibs_hora?capa=' + encodeURIComponent(capa))));
tareas.push(...csv.map(nombre => async () => {
  const r = await obtener('exportar/' + nombre + '.csv');
  await writeFile(salida + '/' + nombre + '.csv', await r.text());
}));
tareas.push(async () => {
  const datos = await json('series');
  const ventanas = { 'maíz': 'Temporada de referencia 1', arroz: 'Temporada de referencia 2', frijol: 'Temporada de referencia 3' };
  const proyecciones = datos.escenarios_anuales.map(({ escenario, cultivo, anio, dT, dP }) =>
    ({ escenario, ventana: ventanas[cultivo], anio, dT, dP }));
  await guardar('series', { cuenca_mensual: datos.cuenca_mensual, proyecciones });
  await writeFile(salida + '/proyecciones.csv',
    '# CMIP6 / SCA; cambios estacionales vs. 1981–1995.\nescenario,ventana,anio,delta_t_c,delta_p_pct\n' +
    proyecciones.map(f => [f.escenario, f.ventana, f.anio, f.dT, f.dP].join(',')).join('\n') + '\n');
});
const fallos = await ejecutar(tareas);
await guardar('global_meta', { ...meta, instantanea_utc: new Date().toISOString() });
if (fallos.length) console.warn('Datos meteorológicos parciales:', fallos.join(' | '));
console.log(`Malla meteorológica ${meta.corrida_utc}: ${tareas.length - fallos.length}/${tareas.length} recursos.`);
