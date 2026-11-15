# Correcciones al informe de investigaciones del 14 de noviembre de 2026

El informe original se conserva en `main` como documento recibido. Este registro corrige su interpretación para la implementación y reemplaza sus veredictos anticipados: únicamente el motor estadístico de la app puede asignar veredictos a una serie.

- Polvo: se retiran la atribución al Sahara central y +0,26 AOD/década. El DOI 10.5194/acp-24-2443-2024 corresponde a Oriente Medio y otra ventana temporal. El caso no se implementa: MERRA-2 (GES DISC), MODIS (LAADS) y Giovanni piden cuenta de NASA Earthdata, y la descarga CSV de NASA NEO ya no existe (redirige a science.nasa.gov). Queda pendiente para cuando haya cuenta.
- Sahel: se retira +0,17 mm/día/década como resultado observado (el DOI 10.1038/s43247-026-03474-3 es un estudio de modelos). La lluvia de junio a septiembre se calcula con CHIRPS y con CRU TS 4.10 por separado, en la misma caja (10–20° N, 17° O–20° E), y se cita la revisión observacional de Biasutti (2019), doi:10.1002/wcc.591.
- Sahel en el informe de Benjamin: el DOI 10.1016/j.gloplacha.2017.12.014 figura con el título «Assessing recovery and change in West Africa's rainfall regime from a 161-year record», pero en Crossref corresponde a Nicholson et al. (2018), «Rainfall over the African continent from the 19th through the 21st century». No se repite esa atribución.
- Mediterráneo: se retira el preprint 10.5194/sp-2024-4. La SST se calcula con NOAA OISST v2.1 diario; las olas de calor se cuentan sobre la media diaria de la cuenca (≥5 días seguidos sobre el percentil 90 de 1991–2020 para ese día del año, ventana de 11 días y suavizado de 31 días, como Hobday et al. 2016).
- Victoria: se retira el veredicto basado en 1993–2016. La serie G-REALM llega a 2025 e incluye la subida de 2019–2020 (doi:10.3390/s21134304, título verificado en Crossref).
- Desacuerdo: «los métodos no coinciden» se reserva al resultado de las pruebas sobre una misma serie. Comparar modelos con observaciones o CHIRPS con CRU no determina esa etiqueta; en la app CHIRPS y CRU del Sahel son dos series distintas.
- Glaciares: GlaMBIE región 11 permite calcular la tendencia del balance anual en m w.e. No debe confundirse con una pérdida porcentual acumulada ni convertirse un porcentaje de 23 años en una pendiente de Sen.

Todos los DOI de `ESTUDIOS` en `backend/clima_nic/recursos_europa_africa.py` se comprobaron en la API de Crossref el 14-11-2026 (autor, año y título coinciden con la cita).

Contraste consultado: `docs/reto/recursos/investigacion_europa_africa_oriente_medio.md` de `origin/codex/investigacion-global`. Sus expectativas se tratan como hipótesis, no como resultados de la app.
