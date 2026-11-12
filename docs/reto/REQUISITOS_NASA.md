# Requisitos del reto «Be An Earth System Trend Detective!» (NASA Space Apps 2026)

**Fuente:** <https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/>
**Consultado:** 12 de noviembre de 2026, desde el equipo de Angel con el navegador integrado (la descarga directa con `curl` falló por un certificado no confiable en la red local; no se forzó).
**Ficha:** dificultad *Advanced*; temas *Earth Science* y *Software*.
**Pestaña Resources:** al consultar decía que los recursos se publican el **viernes 13 de noviembre de 2026**. Hay que volver a revisarla y completar la sección 4.

> Lo que sigue es un resumen fiel en español, organizado para el proyecto; no es una copia literal del enunciado (la página es de NASA/Space Apps y se enlaza arriba). Las expresiones entre comillas son citas breves.

## 1. Problema

Las variables del sistema Tierra cambian; cuando lo hacen en una dirección sostenida hay una **tendencia**. La misma variable puede subir en una región y bajar en otra aunque la cause el mismo proceso, y hay tantas variables que es difícil elegir cuáles analizar. El reto pide una herramienta que permita **seleccionar variables** medidas por misiones de ciencias de la Tierra o producidas por modelos, **visualizar** su evolución en el tiempo y determinar:

1. **qué** está cambiando,
2. **dónde** está cambiando,
3. **cuánto** está cambiando, y
4. **si** esos cambios son lo que los científicos llaman «significativos».

Esto confirma las cuatro preguntas que resumían otros equipos. El enunciado no exige la pendiente de Sen en particular: pide la tasa de cambio y una prueba de significancia, y cita como ejemplos la prueba *t*, Mann–Kendall o intervalos de confianza. Aquí usamos Sen (con IC) y Mann–Kendall modificado como método principal, y mínimos cuadrados con su intervalo como referencia.

## 2. Objetivos (los cuatro elementos de una respuesta exitosa)

| # | Elemento | Qué implica |
|---|---|---|
| O1 | Identificar variables de ciencias de la Tierra que puedan mostrar tendencias. | Catálogo de variables NASA, comunes (temperatura, lluvia) y especializadas (evaporación, caudal, humedad del suelo). |
| O2 | Adquirir los datos de la variable para una **región** concreta. | La mayoría de las tendencias no son globales. Recorte regional. |
| O3 | Generar y **visualizar** una serie temporal suficientemente larga para el análisis estadístico. | Series largas; gráfico de la serie y su tendencia. |
| O4 | **Análisis estadístico básico**: tasa de cambio en el tiempo y **significancia** de la tendencia (prueba *t*, Mann–Kendall, intervalos de confianza). | Pendiente + prueba. «Visualización y análisis» juntos cubren el alcance completo. |

## 3. Consideraciones opcionales

- **Público:** estudiantes de secundaria y universidad, y público con algo de formación científica. Conviene dar **definiciones sencillas** de cada variable. La idea es que el usuario sea un «detective de datos».
- **Enfoque:** preguntas breves al usuario sobre qué y dónde investigar que lleven a las variables relacionadas; uno o dos **ejemplos de demostración** que el usuario pueda ver. Se sugiere, sin exigirlo, usar inteligencia artificial para proponer datos con potencial de mostrar tendencias en ciertas zonas (noticias, artículos, tipo de región).
- **Datos:** resoluciones horaria, trihoraria, diaria y mensual; las diarias y mensuales son las más fáciles. Una tendencia no significativa también es interesante: a veces solo falta un registro más largo. Se mencionan herramientas de graficado hidrológico de CUAHSI.
- **Análisis:** las tendencias pueden ser no lineales y algunas solo aparecen al **quitar el ciclo estacional**. Análisis más complejos quedan fuera del alcance; detectar tendencias **lineales** es un buen comienzo.

## 4. Datos y misiones que nombra el enunciado

MODIS, OMI (ozono), AIRS (sonda infrarroja), GPM (precipitación) y los modelos MERRA-2 y GLDAS. *Pendiente:* añadir aquí la lista de la pestaña Resources cuando se publique (13-11-2026).

## 5. Lectura para este proyecto

- El eje es responder las cuatro preguntas para Nicaragua con datos NASA, de forma reproducible y comprensible para el público.
- «Significativo» se trata con prudencia: intervalos de tres métodos, Mann–Kendall corregido por autocorrelación, control por ENOS y FDR en mapas. Una tendencia no detectada se informa como «evidencia insuficiente con esta ventana», no como «no hay cambio» (lo mismo que sugiere el enunciado).
- La predicción no la pide el reto; la añadimos separada de la detección y con límites explícitos (ver `docs/modelos/REVISION_MODELOS_NICARAGUA.md`).
