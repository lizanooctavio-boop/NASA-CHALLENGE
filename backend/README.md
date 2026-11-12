# Backend `clima_nic`

Detección de tendencias, pronóstico estacional y escenarios del clima de Nicaragua con datos NASA. Responde las cuatro preguntas del reto *Be An Earth System Trend Detective!* (qué, dónde, cuánto, si es significativo). Requisitos y matriz de cumplimiento en [`docs/reto/`](../docs/reto/); resultados y límites en [`docs/modelos/REVISION_MODELOS_NICARAGUA.md`](../docs/modelos/REVISION_MODELOS_NICARAGUA.md).

## Instalar y ejecutar

```text
cd backend
pip install -r requirements.txt            # numpy, scipy, shapely, pyproj (+ fastapi/uvicorn para la API, h5py para HDF5)
python -m clima_nic fuentes                # catálogo y disponibilidad (sin red salvo CMR)
python -m clima_nic productos              # regenera data/fenomenos_nicaragua.json desde data/fenomenos/ (sin red)
python -m clima_nic consultar --region pacifico --variable lluvia_jun_nov --desde 1991 --hasta 2024 --anio 2023
python -m clima_nic api --puerto 8000      # http://127.0.0.1:8000/docs
python -m pytest ../tests -q
```

Descargas (crean `data/fenomenos/*.csv`; los crudos van a `backend/.cache/`, que no se versiona):

```text
python -m clima_nic preparar-power --tierra <ne_10m_admin_1_states_provinces.geojson>   # ~15 min
python -m clima_nic preparar-gistemp
python -m clima_nic preparar-modis
python -m clima_nic preparar-cmip6                                                    # ~20 min
python -m clima_nic actualizar --descargar --tierra <admin1>                          # ciclo completo + historial
```

## Estructura

| Módulo | Función |
|---|---|
| `rutas.py` | Rutas del repositorio y de la caché (`CLIMA_NIC_CACHE` para cambiarla). |
| `regiones.py` | `data/regiones_nicaragua.geojson`: NIC, Pacífico, Central (con Corredor Seco), Caribe y caja SICC; pesos de malla por área (EPSG:6933). |
| `fuentes/base.py` | Interfaz común `Adaptador` (`metadatos`, `disponible`, `descargar`, `recortar`, `agregar`) y `recortar_malla`. |
| `fuentes/power.py` | NASA POWER (MERRA-2, CERES/SRB) sin cuenta: 11 variables diarias por celda; Niño 3.4, TNA, AMO, PDO y CLLJ aproximado. |
| `fuentes/imerg.py`, `merra2.py`, `smap.py`, `grace.py` | Requieren Earthdata (`.netrc`): IMERG V07 1998–, MERRA-2 (TSM, U925 para CLLJ), SMAP L4, GRACE/GRACE-FO. Probados con datos sintéticos. |
| `fuentes/gistemp.py` | GISTEMP v4 250 km: temperatura observada para contrastar MERRA-2. |
| `fuentes/modis.py` | NDVI MOD13Q1 (y LST MOD11A2) por el servicio ORNL DAAC, dos sitios por región. |
| `fuentes/nex_gddp.py` | NEX-GDDP-CMIP6 v2.0 por THREDDS/NCSS de NCCS: 6 modelos, histórico, SSP2-4.5 y SSP5-8.5. |
| `fuentes/lagos.py` | Nivel de Cocibolca/Xolotlán (G-REALM, SWOT): implementado, sin datos todavía. |
| `estadistica/` | Indicadores (SPI, SPEI, ETCCDI, canícula), tendencias robustas (MK modificado, Sen, Pettitt, control por índices), FDR, modelo estacional. |
| `agro.py` | ETo FAO-56 Penman–Monteith y Hargreaves, balance P − ETo, grados-día. |
| `proyecciones.py` | Corrección de sesgo por delta y rango de escenarios. |
| `productos.py` | Construye `data/fenomenos_nicaragua.json`. |
| `actualizar.py` | Retroalimentación: ingesta → recálculo → recalibración → `data/historial/`. |
| `consulta.py`, `api.py`, `__main__.py` | Consulta central, API FastAPI y CLI. |

## Cómo puede consumirlo la interfaz (PR #2, sin modificarla)

La interfaz es estática y lee `data/clima.json` (contrato 1.0.0, que no cambia). Hay dos vías, ambas opcionales:

1. **Archivo estático:** leer `data/fenomenos_nicaragua.json` igual que `clima.json` (ver la sección 9 de `data/contrato.md`). Para el panel «qué/dónde/cuánto/significativo» basta `regiones[i].variables[v].respuesta_reto`; para la serie, `anios` y `valores`; para el mapa, `mapas_tendencia[var].celdas` (lat, lon, `sen_por_decada`, `significativo_fdr`).
2. **API:** con `python -m clima_nic api`, `fetch("http://127.0.0.1:8000/consulta?region=pacifico&variable=lluvia_jun_nov&anio=2023")` devuelve tendencia, pronóstico estacional y escenarios en un solo JSON. CORS está abierto solo para GET.

Reglas para mostrar: unidad e intervalo siempre junto a la pendiente; usar `veredicto` (no reinterpretar el signo); mostrar `advertencias` cuando existan; presentar `pronostico_estacional` como valor esperado con intervalo y terciles, y `escenarios` como rango con la leyenda «no es un pronóstico».
