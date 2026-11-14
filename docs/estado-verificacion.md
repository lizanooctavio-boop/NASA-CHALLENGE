# Estado de verificación

Fecha: 2026-11-12 · Rama: `codex/verificacion-v2` (creada desde `origin/codex/demo-render` en `a61ecbc`).

| Requisito | Estado | Detalle |
|---|---|---|
| Clonar, abrir demo y reproducir | **Verificado** | Reproducible compilando con `node scripts/preparar_render.mjs` y sirviendo `public/` por HTTP local (`docs/reproduccion.md`). |
| Mapa, selección, gráfica y descarga en el mismo dominio | **Verificado** | Auditado en navegador headless (Edge/Chrome) en las pestañas **Rainfall trend** (4 áreas) y **Climate indicators** (4 regiones × variables disponibles) (`tests/test_e2e_navegador.py`). |
| Cotejar cifras con `data/clima.json` y `data/fenomenos_nicaragua.json` | **Verificado** | Series, pendientes, intervalos t (Santer et al., 2000), HAC, Theil–Sen, Mann–Kendall clásico y modificado, Pettitt, FDR y escenarios CMIP6 verificados (`tests/test_datos.py`, `tests/test_interfaz.py`, `tests/test_backend_clima_nic.py`, `tests/test_indicadores_nicaragua.py`). |
| Verificar 24 años de IMERG (2001–2024) | **Verificado** | 288 meses sin huecos, cobertura 1,0 y sin valores negativos en los 5 dominios (`data/clima.json`). |
| Costa Rica como resultado dependiente del método | **Verificado** | MCO (−201,2 mm/década) y HAC excluyen cero; Theil–Sen ([−369,5; 20,8]) lo incluye y Mann–Kendall da $p = 0{,}0972$. Veredicto en datos: `metodos_discrepan`; en la interfaz: `Methods disagree`. |
| Pestaña «Climate indicators» probada de extremo a extremo | **Verificado** | `tests/test_e2e_navegador.py` recorre las regiones (`NIC`, `pacifico`, `central`, `caribe`), cambia de variable (`temperatura_gistemp`, `lluvia_anual_imerg`, `lluvia_jun_nov_imerg`, `ndvi`), verifica la tarjeta y gráfica de contraste con MERRA-2 (`#ind-contraste`) y valida cada CSV descargado contra `data/fenomenos_nicaragua.json`. |
| Bloque ONI visible con datos reales | **Verificado** | Comprobado en la pestaña **El Niño & cyclones** (`#fenomenos`, `#enos-tarjetas`), tanto con `/clima-base/enos.json` como con el respaldo local de `data/fuentes/oni_2001_2024.csv`. |
| CSV de pendientes con $p$ de Mann–Kendall | **Verificado** | `rainfall_trends_by_area.csv` exporta la columna `mann_kendall_p` y coincide con `t.controles.mann_kendall.p_valor` de `data/clima.json`. |
| Limpieza de datos sintéticos, puntos POWER no ponderados y `.pyc` | **Verificado** | Sin `proyecciones_cmip6_nicaragua_2025_2100.json`, sin los 4 CSV puntuales de POWER, sin referencias a estrés térmico de cultivos y sin `.pyc` versionados. Comparación punto vs. área y validación NOAA vs. MERRA-2 documentadas en `docs/auditoria.md`. |
| Guía de reproducción, guion ES/EN, tabla de criterios y checklist | **Completos** | Actualizados en `docs/reproduccion.md`, `docs/guion.md`, `docs/criterios.md` y `docs/checklist-entrega.md`. |
| Prueba con persona ajena | **Pendiente** | Protocolo listo en `docs/prueba-persona-ajena.md` para ejecutarse con un participante externo. |
| Separación de SICC-952 | **Verificado** | Sin HDF5, sin credenciales y sin módulos de cultivos (`SeparacionDeSICC` en `tests/test_datos.py`). |
