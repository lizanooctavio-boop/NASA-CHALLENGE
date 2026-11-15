# Correcciones al informe de investigaciones del 14 de noviembre de 2026

El informe original se conserva en `main` como documento recibido. Este registro corrige su interpretación para la implementación y reemplaza sus veredictos anticipados: únicamente el motor estadístico de la app puede asignar veredictos a una serie.

- Polvo: se retiran la atribución al Sahara central y +0,26 AOD/década. El DOI 10.5194/acp-24-2443-2024 corresponde a Oriente Medio y otra ventana temporal. No se implementará una tendencia de polvo sin descargar MERRA-2/MODIS y verificar la referencia correspondiente.
- Sahel: se retira +0,17 mm/día/década como resultado observado. El estudio de modelos no valida esa pendiente observacional. Se requiere calcular JJAS con CHIRPS y CRU TS por separado.
- Mediterráneo: se retira el preprint como contraste. La serie debe calcularse a partir de NOAA OISST; las olas de calor requieren resolución diaria y una definición documentada, no la serie mensual.
- Victoria: se retira el veredicto basado en 1993–2016. La comparación debe incluir 2019–2020 y finalizar en 2025, si el producto lo permite. El artículo doi:10.3390/s21134304 documenta esa subida; título verificado en Crossref.
- Desacuerdo: «los métodos no coinciden» se reserva al resultado de las pruebas sobre una misma serie. Comparar modelos con observaciones o productos entre sí no determina esa etiqueta.
- Glaciares: GlaMBIE región 11 permite calcular la tendencia del balance anual en m w.e. No debe confundirse con una pérdida porcentual acumulada ni convertirse un porcentaje de 23 años en una pendiente de Sen.

Contraste consultado: `docs/reto/recursos/investigacion_europa_africa_oriente_medio.md` de `origin/codex/investigacion-global`. Sus expectativas se tratan como hipótesis, no como resultados de la app.
