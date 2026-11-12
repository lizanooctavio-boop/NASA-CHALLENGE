#!/bin/sh
set -eu
node scripts/preparar_render.mjs
node scripts/preparar_meteo.mjs
