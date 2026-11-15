import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';

// Sitio estático: la portada, sus módulos, las texturas NASA y los resultados IMERG empaquetados.
// public/clima-base (datos meteorológicos de preparar_meteo.mjs) se conserva entre compilaciones.
const rutas = ['index.html', 'app', 'src', 'assets', 'visor'];
for (const ruta of [...rutas, 'data']) rmSync('public/' + ruta, { recursive: true, force: true });
mkdirSync('public/data/fuentes', { recursive: true });
for (const ruta of rutas) cpSync(ruta, 'public/' + ruta, { recursive: true });
for (const archivo of ['clima.json', 'dominios.geojson', 'lugares_mundo.json']) cpSync('data/' + archivo, 'public/data/' + archivo);
cpSync('data/fuentes/oni_2001_2024.csv', 'public/data/fuentes/oni_2001_2024.csv');

// Indicadores de clima_nic: solo lo que muestra la portada (las series, tendencias, contrastes,
// pronóstico estacional y escenarios); el JSON completo sigue en data/ del repositorio.
const VARIABLES = ['temperatura_gistemp', 'lluvia_anual_imerg', 'lluvia_jun_nov_imerg', 'ndvi', 't2m_media', 'lluvia_anual'];
const f = JSON.parse(readFileSync('data/fenomenos_nicaragua.json', 'utf8'));
const recorte = {
  esquema: f.esquema, version_esquema: f.version_esquema, generado: f.generado,
  regiones: f.regiones.map(r => ({ id: r.id, nombre: r.nombre, variables: Object.fromEntries(
    VARIABLES.filter(v => r.variables[v]).map(v => [v, r.variables[v]])) })),
  comparaciones_independientes: f.comparaciones_independientes,
  modelo_estacional: { principales: f.modelo_estacional.principales },
  escenarios_cmip6: f.escenarios_cmip6,
};
writeFileSync('public/data/fenomenos_nicaragua.json', JSON.stringify(recorte));
cpSync('data/regiones_nicaragua.geojson', 'public/data/regiones_nicaragua.geojson');
// Pestaña Investigate: solo el JSON integrado (clima_nic.recursos); data/recursos/ y sus fixtures no se publican.
cpSync('data/recursos_integrados.json', 'public/data/recursos_integrados.json');
// Vectores web y lecturas fechadas. Los ZIP/SHP de la caché nunca se publican.
cpSync('data/hidrologia', 'public/data/hidrologia', { recursive: true });
// Pestaña Help: las 100 preguntas frecuentes (app/ayuda.js).
cpSync('data/ayuda_preguntas.json', 'public/data/ayuda_preguntas.json');
