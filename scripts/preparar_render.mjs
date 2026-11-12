import { cpSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const leer = ruta => readFileSync(ruta, 'utf8');
let html = leer('index.html');

function insertar(marca, contenido) {
  if (!html.includes(marca)) throw new Error('Falta la referencia ' + marca);
  html = html.replace(marca, () => contenido);
}

insertar('<link rel="stylesheet" href="src/estilos.css">', '<style>\n' + leer('src/estilos.css') + '\n</style>');
const datos = [
  ['clima-publicado', 'data/clima.json'],
  ['mapa-publicado', 'data/dominios.geojson'],
].map(([id, ruta]) => {
  const json = JSON.stringify(JSON.parse(leer(ruta))).replace(/</g, '\\u003c');
  return '<script type="application/json" id="' + id + '">' + json + '</script>';
}).join('\n');
insertar('<script src="src/app.js"></script>', datos + '\n<script src="src/app.js"></script>');
html = html.replace(/<script src="(src\/[^"]+\.js)"><\/script>/g, (_marca, ruta) =>
  '<script>\n' + leer(ruta).replace(/<\/script/gi, '<\\/script') + '\n</script>');

mkdirSync('public', { recursive: true });
writeFileSync('public/index.html', html, 'utf8');
cpSync('visor', 'public/visor', { recursive: true });
mkdirSync('public/src', { recursive: true });
cpSync('src/fuentes-meteo.js', 'public/src/fuentes-meteo.js');
cpSync('src/meteo-paletas.js', 'public/src/meteo-paletas.js');
