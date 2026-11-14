// Carga src/estadistica.js y src/contrato.js tal como los usa el navegador y escribe en stdout
// (JSON) los datos normalizados que consume la interfaz. Lo usa tests/test_interfaz.py.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const raiz = path.resolve(__dirname, '..');
const ventana = {};
const ctx = vm.createContext({ window: ventana, console, Math, Number, Object, JSON, Array, Map, isFinite });
for (const f of ['src/estadistica.js', 'src/contrato.js']) {
  vm.runInContext(fs.readFileSync(path.join(raiz, f), 'utf8'), ctx, { filename: f });
}
const C = ventana.SofContrato;
const clima = JSON.parse(fs.readFileSync(path.join(raiz, 'data/clima.json'), 'utf8'));
const mapa = JSON.parse(fs.readFileSync(path.join(raiz, 'data/dominios.geojson'), 'utf8'));
const datos = C.normalizar(C.desdeClima(clima, mapa));
process.stdout.write(JSON.stringify({
  es_ejemplo: datos.es_ejemplo,
  avisos: datos.avisos,
  meta: { unidades: datos.meta.unidades, unidades_pendiente: datos.meta.unidades_pendiente, periodo: datos.meta.periodo, limites: datos.meta.limites },
  regiones: datos.regiones.map((r) => ({
    id: r.id, nombre: r.nombre, rol: r.rol, serie: r.serie, anios_sin_dato: r.anios_sin_dato,
    n_validos: r.analisis.n_validos, veredicto: r.analisis.veredicto, mco: r.analisis.mco,
    hac: r.analisis.hac || null, sen: r.analisis.sen, origen: r.origen_tendencias,
    ajustada_mco_2001: C.valorAjustado(r.analisis.mco, 2001), ajustada_mco_2024: C.valorAjustado(r.analisis.mco, 2024)
  }))
}));
