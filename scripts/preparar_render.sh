#!/bin/sh
set -eu
mkdir -p public/src/datos public/data
cp index.html public/
cp src/app.js src/contrato.js src/estadistica.js src/estilos.css src/graficas.js public/src/
cp src/datos/contornos.js src/datos/ejemplo.js public/src/datos/
cp data/clima.json data/dominios.geojson public/data/
