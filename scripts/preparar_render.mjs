import { cpSync, mkdirSync, rmSync } from 'node:fs';

// Sitio estático: la portada, sus módulos, las texturas NASA y los resultados IMERG empaquetados.
// public/clima-base (datos meteorológicos de preparar_meteo.mjs) se conserva entre compilaciones.
const rutas = ['index.html', 'app', 'src', 'assets', 'visor'];
for (const ruta of [...rutas, 'data']) rmSync('public/' + ruta, { recursive: true, force: true });
mkdirSync('public/data', { recursive: true });
for (const ruta of rutas) cpSync(ruta, 'public/' + ruta, { recursive: true });
for (const archivo of ['clima.json', 'dominios.geojson']) cpSync('data/' + archivo, 'public/data/' + archivo);
