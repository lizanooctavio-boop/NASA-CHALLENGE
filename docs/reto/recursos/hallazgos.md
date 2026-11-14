# Frecuencia de la lluvia, ENSO, hielo marino y temperatura por latitud

Fecha: 14-11-2026. Datos en `data/recursos/hallazgos/`, generados con `generar_hallazgos.py` (fuentes públicas, sin cuenta).

## Por qué

El total anual de lluvia de Nicaragua no muestra tendencia con IMERG (2001-2024), CRU ni GPCC. Se revisaron tres
explicaciones: la variabilidad por ENSO (2020 con Eta e Iota frente a 2026, año de El Niño con déficit en el Pacífico
según INETER), cambios en la frecuencia e intensidad que el total no ve, y un registro corto.

## Fuentes descartadas

La serie diaria de NASA POWER (MERRA-2) no sirve para tendencias de lluvia: Nicaragua pasa de 803 mm/año en 1981-1990 a
1760 mm/año en 2015-2024, sin equivalente en IMERG. Es un efecto de los cambios en las observaciones asimiladas. La
pestaña de indicadores ya la usaba solo como contraste.

## Método

- CHIRPS v2.0 diario 0,25° (IRI Data Library), 1981-01-01 al último día publicado (30-09-2026 al generar).
  Concordancia con IMERG 2001-2024 en Nicaragua: r = 0,73, deriva +42 mm/década.
- Índices ETCCDI por celda con `estadistica/indicadores.indices_lluvia` (percentil 95 de 1991-2020) y media de las celdas
  cuyo centro cae en cada región (Nicaragua 160, Pacífico 23, Central 51, Caribe 86).
- Acumulado del 1 de enero al último día publicado de cada año, para comparar el año en curso.
- Efecto de ENSO: regresión lineal sobre el ONI medio de MJJ a ASO (NOAA CPC) y tendencia de los residuos.
- NSIDC Sea Ice Index v4: extensión media de marzo y septiembre. GISTEMP v4: bandas de latitud desde 1981.
- Tendencias con el mismo motor que el resto de la app (`recursos.tendencia_compacta`).

## Resultados (1981-2025)

| Serie | Pendiente de Sen | Veredicto | Sin ENSO | Desde 2001 |
|---|---|---|---|---|
| Lluvia anual, Nicaragua | −18 mm/década | insuficiente | insuficiente | insuficiente |
| Días ≥ 10 mm, Nicaragua | −2,2 días/década | detectada | detectada | insuficiente |
| Días ≥ 10 mm, Caribe | −3,8 días/década | detectada | detectada | insuficiente |
| Lluvia por día húmedo, Central | −0,35 mm/día/década | detectada | detectada | insuficiente |
| Máximo de 5 días, Caribe | +9 mm/década | detectada | detectada | métodos discrepan |

- 2026 (enero-septiembre): Pacífico −43 % frente a 1991-2020, el más seco de 46 años; Central −24 %; Caribe +4 %.
- Hielo ártico de septiembre −0,72 millones de km²/década; antártico sin tendencia desde 1979 y bajo desde 2016.
- Temperatura 1981-2025: Ártico +0,67 °C/década; 0-24° N +0,18 °C/década; global +0,21 °C/década.

## Límites

Las tendencias de frecuencia solo aparecen en el registro completo. CHIRPS combina pluviómetros cuyo número cambió con el
tiempo, así que se presentan con la comparación desde 2001 y como indicio por confirmar con estaciones de INETER. ENSO se
resta con una regresión lineal simple; no recoge efectos no lineales ni el retraso de la respuesta.

## En la interfaz

- *Investigate › Rain*: seis índices y el acumulado parcial en Nicaragua, Pacífico, Central y Caribe, con notas sobre ENSO
  y el periodo desde 2001.
- *Investigate › Ice & poles* (categoría nueva) y *Temperature* por bandas de latitud.
- Recorrido guiado «Same total, different rain?» y artículo de *Learn* «Record years, El Niño and how it rains».
- Corregidos dos textos de contrastes que mostraban «consulta» y una ruta interna del repositorio.
