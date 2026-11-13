# SINAPRED e IMERG en Nicaragua

| Parte público | Fecha, ubicación y evento | Campos disponibles y faltantes |
| --- | --- | --- |
| [Managua](https://www.sinapred.gob.ni/index.php/noticias/autoridades-visitan-familias-afectadas-por-lluvias-en-barrios-de-managua) | 30 sep.–1 oct. 2022, noche y madrugada, anegaciones y desbordes por barrio y distrito | Cauces, viviendas y familias afectadas. Faltan horas y geometrías. |
| [Santo Domingo, Chontales](https://www.sinapred.gob.ni/index.php/noticias/gobierno-envia-ayuda-a-familias-afectadas-por-lluvias-en-santo-domingo-chontales) | Madrugada del 29 jul. 2021, lluvias intensas, escala municipal | Unos 150 mm en cuatro horas según el parte. Faltan intervalo exacto e identificación y ubicación del instrumento. |
| [Tipitapa](https://www.sinapred.gob.ni/index.php/noticias/gobierno-brinda-apoyo-solidario-a-familias-de-tipitapa-afectadas-por-lluvias) | Días previos al parte del 25 ago. 2022, afectaciones por lluvias, escala municipal | Viviendas afectadas y respuesta. Faltan fechas y desglose por barrio. |
| [El Rama](https://www.sinapred.gob.ni/index.php/noticias/gobierno-de-nicaragua-envia-nueva-caravana-de-alimentos-y-avituallamiento-para-familias-de-el-rama) | Octubre de 2022, inundación asociada a Julia, escala de ciudad | Proporción urbana inundada y respuesta. El 17 de octubre corresponde al envío de ayuda. Faltan inicio, pico y geometría. |

Los partes son de consulta pública. La licencia de redistribución está sin verificar. Se comparten enlaces y resúmenes. Los originales institucionales se conservan fuera del repositorio.

## Laureles Sur, Managua

SINAPRED reportó **17 viviendas anegadas y tres con daños parciales en sus muros** durante la noche del 30 de septiembre a la madrugada del 1 de octubre de 2022. Se desconoce si los conteos se solapan. [Parte de SINAPRED](https://www.sinapred.gob.ni/index.php/noticias/autoridades-visitan-familias-afectadas-por-lluvias-en-barrios-de-managua)

Se consultó NASA POWER Daily API v2.10.3 en 12.11672° N, 86.19696° O (parada Laureles Sur). El parámetro IMERG_PRECTOT corresponde a IMERG Final Run, rejilla de 0,1°. El JSON confirmó fuente IMERG, días UTC, unidades mm/day y cinco valores válidos del 29 de septiembre al 3 de octubre de 2022. [OpenStreetMap](https://www.openstreetmap.org/node/3275463518) · [Metodología NASA](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/) · [Consulta reproducible](https://power.larc.nasa.gov/api/temporal/daily/point?parameters=IMERG_PRECTOT&community=AG&longitude=-86.19696&latitude=12.11672&start=20220929&end=20221003&format=JSON&time-standard=UTC)

| Día UTC | Acumulado estimado |
| --- | ---: |
| 30 sep. 2022 | 34,45 mm |
| 1 oct. 2022 | 57,09 mm |
| **Total en 48 horas** | **91,54 mm** |

La suma corresponde a una celda y a una ventana del 29 de septiembre a las 18:00 al 1 de octubre a las 18:00 en Managua (UTC−6). Incluye lluvia anterior y posterior al episodio. Las viviendas documentan el impacto y la estimación satelital aporta contexto de precipitación. La respuesta de POWER no identifica la versión de IMERG subyacente.

## Pendientes

Solicitar el parte de incidencias o la evaluación de daños de Managua del 30 de septiembre al 1 de octubre de 2022 con detalle de Laureles Sur y el cauce. Con horas precisas, repetir el cruce con IMERG semihorario.

Para ampliar la cobertura, solicitar una exportación autorizada de SINAPRED o COMUPRED por incidente y localidad con ID, tipo, inicio y fin, zona horaria, fecha de reporte, departamento, municipio, distrito, barrio o comunidad, código territorial, coordenadas o geometría y su precisión, impactos agregados, fuente, estado y fecha de actualización. Adjuntar diccionario y condiciones para compartir derivados. Los anuarios sirven para el inventario. El cruce por evento requiere fecha y localidad.
