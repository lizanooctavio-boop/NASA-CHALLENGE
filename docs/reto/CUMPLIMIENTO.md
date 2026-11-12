# Matriz de cumplimiento: requisito del reto → módulo del backend → prueba

Requisitos tomados de [`REQUISITOS_NASA.md`](REQUISITOS_NASA.md) (consulta del 12-11-2026). Módulos bajo `backend/clima_nic/`; pruebas en `tests/`. La interfaz (PR #2) no se modificó: la columna «Interfaz» indica qué campo puede consumir.

## Las cuatro preguntas

| Pregunta | Módulo | Campo en `data/fenomenos_nicaragua.json` / API | Prueba |
|---|---|---|---|
| **Qué** cambia | `productos.VARIABLES` (40 variables con definición sencilla); `fuentes/*` (catálogo) | `regiones[*].variables[*].titulo`, `.definicion`; `GET /variables` | `test_producto_estructura_y_cuatro_preguntas` |
| **Dónde** cambia | `regiones.py` (NIC, Pacífico, Central, Caribe, caja SICC); `productos.mapa_celdas` | `regiones[*]`; `mapas_tendencia[*].celdas`; `GET /mapa` | `test_regiones_particion_de_nic`, `test_recortar_malla_*` |
| **Cuánto** cambia | `estadistica/tendencia_robusta.theil_sen` (Sen por década con IC 95 %), `tendencia.py` (MCO) | `variables[*].respuesta_reto.cuanto`; `GET /tendencia` → `cuanto` | `test_theil_sen_ic_contiene_pendiente_verdadera` |
| **¿Es significativo?** | `tendencia_robusta.mann_kendall_modificado` (Hamed y Rao), intervalos de tres métodos y veredicto, `pettitt`, `regresion_controlada` (ENOS/TNA/AMO/PDO/CLLJ), `estadistica/fdr.py` en mapas | `variables[*].tendencia.veredicto`, `.mann_kendall_modificado`, `.controlada_por_indices`; `mapas_tendencia[*].significativo_fdr` | `test_mann_kendall_modificado_*`, `test_pettitt_*`, `test_regresion_controlada_*`, `test_benjamini_hochberg`, `test_analizar_veredictos_y_campos` |

## Objetivos y consideraciones

| Requisito | Módulo | Prueba | Estado |
|---|---|---|---|
| O1 Identificar variables NASA con potencial de tendencia | `fuentes/__init__.REGISTRO` (POWER, IMERG, MERRA-2, MODIS, SMAP, GRACE-FO, GISTEMP, NEX-GDDP-CMIP6, lagos); `GET /fuentes` | `test_registro_tiene_todas_las_fuentes_pedidas` | Cumplido |
| O2 Adquirir datos de una región | `fuentes/base.recortar_malla` (ponderación por área EPSG:6933), `smap.recortar_puntos`, adaptadores | `test_recortar_malla_media_ponderada_por_area`, `test_recortar_malla_lon_0_360_y_nan`, `test_recortar_puntos_ease`, `test_power_leer_punto_sintetico` | Cumplido sin cuenta (POWER, GISTEMP, MODIS ORNL, NEX-GDDP); con Earthdata pendiente (IMERG 1998–2000, MERRA-2 directo, SMAP, GRACE-FO) |
| O3 Serie temporal larga y visualizable | `productos.series_region` (1981–2024 diario → anual/mensual); `consulta.tendencia` devuelve `anios`/`valores` | `test_a_mensual_y_anual`, `test_consulta_y_api` | Backend cumplido; la visualización es de la interfaz (PR #2) |
| O4 Tasa de cambio y significancia (*t*, Mann–Kendall, IC) | `tendencia.py` (t con gl ajustados), `tendencia_robusta` (MK modificado, Sen con IC, HAC) | ver arriba | Cumplido |
| Definiciones sencillas para el público | `productos.VARIABLES[*][3]` | `test_producto_estructura_y_cuatro_preguntas` | Cumplido |
| Preguntas guiadas qué/dónde | `GET /regiones`, `GET /variables?region=` | `test_consulta_y_api` | Backend listo; flujo de preguntas en la interfaz |
| Ejemplos de demostración | `docs/modelos/REVISION_MODELOS_NICARAGUA.md` §5 (Pacífico lluvia, canícula Central, temperatura) | — | Documentado |
| Quitar el ciclo estacional | Anomalías mensuales con base 1991–2020 (`fuentes/power.anomalia_mensual`); series anuales y por temporada | `test_spi_*`, `test_pdo_recupera_modo_principal` | Cumplido |
| Tendencias no lineales / cambios abruptos | `tendencia_robusta.pettitt` y advertencia de inhomogeneidad | `test_pettitt_localiza_salto` | Cumplido (descriptivo) |
| Tendencia no significativa también informa | Veredicto `evidencia_insuficiente` con texto «no demuestra que no haya cambio» | `test_analizar_veredictos_y_campos` | Cumplido |

## Ampliaciones propias (fuera del enunciado)

| Requisito del proyecto | Módulo | Prueba |
|---|---|---|
| Variables agroclimáticas (ETo Penman–Monteith, balance, grados-día, radiación, viento) | `agro.py` | `test_penman_monteith_ejemplo_fao56`, `test_grados_dia_y_balance` |
| Sequía (SPI/SPEI), canícula, ETCCDI | `estadistica/indicadores.py` | `test_spi_*`, `test_spei_*`, `test_canicula_*`, `test_indices_lluvia_*`, `test_indices_calor_*` |
| Pronóstico estacional 0–6 meses validado fuera de muestra | `estadistica/modelo_estacional.py`, `productos.modelo_estacional`, `consulta.pronostico_estacional` | `test_validacion_cruzada_*`, `test_ventana_predictor`, `test_serie_predictor_y_pronostico` |
| Escenarios CMIP6 como rango, con corrección de sesgo | `fuentes/nex_gddp.py`, `proyecciones.py` | `test_escenarios_delta`, `test_nex_calendarios_de_modelo` |
| Nunca un año futuro como pronóstico determinista | `consulta.pronostico_estacional` (rechaza años sin predictores), avisos en la respuesta | `test_consulta_y_api` (`pronostico_estacional(…, 2031)` → no disponible) |
| Retroalimentación con historial de habilidad | `actualizar.py` → `data/historial/` | ejecución documentada en la revisión |
| API | `api.py` (FastAPI) y CLI `python -m clima_nic` | `test_consulta_y_api` |
| Credenciales nunca expuestas | `fuentes/earthdata.py` | `test_hay_credenciales_lee_netrc_sin_exponerlo`, `test_adaptadores_earthdata_se_declaran` |
| Contrato 1.0.0 intacto | `scripts/datos/verificar_clima.py` sin cambios | `python scripts/datos/verificar_clima.py` (80/80) |
