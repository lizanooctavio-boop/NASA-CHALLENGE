# Lista de verificación para la entrega

Leyenda: `[x]` hecho y comprobado · `[ ]` pendiente · `[?]` requiere decisión o verificación humana.

## Formato (confirmar con la guía vigente)
- [?] **Confirmar en la fuente oficial antes de subir el video/diapositivas.** Dos búsquedas web coinciden en:
  - Demo: video de **hasta 30 s** con **subtítulos en inglés**, o **hasta 7 diapositivas** en inglés.
  - El video o las diapositivas no se suben al sitio: van en un enlace externo **público** (YouTube, Drive, OneDrive, Dropbox o GitHub), sin pedir acceso ni inicio de sesión.
  - El formulario pregunta si se usó IA («qué herramientas y cómo»); declararlo es obligatorio si se usó.
- [ ] Alguien del equipo abre la guía oficial del año y confirma estos puntos antes de cerrar la grabación.
- [ ] Ajustar [guion.md](guion.md) al formato final elegido (video de 30 s o 7 diapositivas).

## Enlaces públicos
- [?] Visibilidad del repositorio, licencia y despliegue en Render: decisión del administrador del repositorio (no fusionar en `codex/demo-render` sin autorización porque dispara el despliegue automático en Render).
- [ ] Demo y video o diapositivas se abren en una ventana de incógnito, sin iniciar sesión.
- [ ] Enlaces comprobados desde otra cuenta.
- [x] La demo sirve exclusivamente **datos reales** en todas sus pestañas (`data/clima.json`, `data/fenomenos_nicaragua.json`, `data/fuentes/oni_2001_2024.csv`).

## Citas (verificar cada una antes de publicar)
- [ ] NASA GPM IMERG Final Run, mensual, versión 07B (`GPM_3IMERGM.07`): Huffman et al. (2023), NASA GES DISC, DOI: `10.5067/GPM/IMERG/3B-MONTH/07`.
- [ ] NASA GISS Surface Temperature Analysis (GISTEMP v4): Lenssen et al. (2019), GISTEMP Team, `https://data.giss.nasa.gov/gistemp/`.
- [ ] NASA MODIS/Terra Vegetation Indices Monthly L3 Global 0.05Deg CMG V061 (`MOD13C2`): Didan (2021), NASA EOSDIS LP DAAC, DOI: `10.5067/MODIS/MOD13C2.061`.
- [ ] NASA POWER / GMAO MERRA-2: Gelaro et al. (2017) y proyecto NASA POWER (`https://power.larc.nasa.gov/`).
- [ ] NASA NCCS NEX-GDDP-CMIP6 v2.0: Thrasher et al. (2022), *Scientific Data*, DOI: `10.1038/s41597-022-01393-4`.
- [ ] NOAA CPC, Oceanic Niño Index (`oni.ascii.txt`) y NOAA PSL, Tropical Northern Atlantic (`tna.data`) y Atlantic Multidecadal Oscillation (`amon.us.data`), usados como validación externa de los índices oceánicos MERRA-2.
- [ ] Natural Earth 1:50 m (dominio público; citar igualmente).
- [ ] Métodos estadísticos: Santer et al. (2000), Newey y West (1987), Theil (1950), Sen (1968), Mann (1945), Kendall (1975) y Pettitt (1979).

## Licencias
- [?] Licencia del repositorio (decisión de Octavio).
- [ ] Confirmar atribuciones de redistribución de derivados de datos abiertos de NASA (política de datos abiertos Earthdata) y NOAA.
- [ ] Licencias de las bibliotecas usadas por la demo y los scripts (`numpy`, `scipy`, `shapely`, `pyproj`, `pytest`).

## Declaración del uso de IA
- [ ] Redactar la respuesta del formulario con las herramientas realmente usadas por **cada** integrante (código, texto, traducción, pruebas), qué se pidió y quién revisó el resultado.
- [x] Para esta rama (`codex/verificacion-v2`): las pruebas unitarias y extremo a extremo, las correcciones puntuales de contrato/descarga/ONI, la validación de índices oceánicos y la documentación de auditoría las escribió un asistente de IA (agente de código de Antigravity) bajo supervisión de un integrante del equipo.

## Trabajo previo y aporte del evento
- [ ] Declarar **SICC-952 como trabajo previo** (repositorio privado, fuera de este). Los polígonos de `data/dominios.geojson` y la caja de 10,7–12,6° N derivan de SICC-952 (`data/contrato.md`, sección 5).
- [ ] Listar lo hecho durante el evento: versión climática independiente; backend `clima_nic` con series ponderadas por área (IMERG, GISTEMP v4, MODIS NDVI, MERRA-2, NEX-GDDP-CMIP6); análisis de tendencias con tres métodos y control de saltos con Pettitt; cambio de escala a Nicaragua y sus tres macrorregiones; interfaz espacial 3D/2D en inglés; pruebas automatizadas y auditoría.
- [x] Sin HDF5 originales, credenciales, archivos `.pyc` ni módulos fuera del alcance climático en el repositorio (`tests/test_datos.py`, clase `SeparacionDeSICC`).

## Integridad técnica
- [x] `data/clima.json` con 24 años (2001–2024) en cada dominio y cifras recalculadas de forma independiente.
- [x] Sin archivos sintéticos ni fórmulas escritas a mano: las proyecciones provienen exclusivamente de `backend/clima_nic/fuentes/nex_gddp.py` y `proyecciones.py` (`data/fenomenos_nicaragua.json` y `data/fenomenos/cmip6_mensual.csv`).
- [x] Mapa, selección, gráfica y descargas del mismo dominio en `Rainfall trend`, e indicadores regionales, contraste con MERRA-2 y descarga CSV en `Climate indicators` (prueba E2E en navegador).
- [x] CSV de pendientes (`rainfall_trends_by_area.csv`) incluye el valor *p* de Mann–Kendall (`mann_kendall_p`).
- [x] Bloque ONI visible con datos reales en la pestaña `El Niño & cyclones`.
- [x] Costa Rica descrita como resultado que depende del método.
- [ ] Prueba presencial con una persona ajena al desarrollo ([prueba-persona-ajena.md](prueba-persona-ajena.md)).
