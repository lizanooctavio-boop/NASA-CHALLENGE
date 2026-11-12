# Interfaz climática (index.html y src/)

Demo web autónoma para Earth System Trend Detective: «¿Cambia la conclusión sobre la lluvia cuando ampliamos el mapa?».
No usa librerías externas ni conexión a internet.

## Abrir en local

- **Lo más rápido:** doble clic en `index.html`. Funciona sin servidor con los datos de ejemplo.
- **Con el JSON definitivo:** desde la raíz del repositorio, ejecuta `python -m http.server 8000` y abre
  `http://localhost:8000/?datos=ruta/al/archivo.json` (cambia la ruta por la del JSON).

Parámetros de la URL:

| Parámetro | Efecto |
|---|---|
| `?region=honduras` | Abre otra región (`caja_original`, `nicaragua`, `honduras`, `costa_rica`). Por defecto, Nicaragua. |
| `?datos=archivo.json` | Carga un JSON con la forma descrita abajo (requiere servidor HTTP). |
| `?caso=faltantes` | Prueba el mensaje de datos faltantes: quita Honduras y deja Costa Rica con 7 años. |

## Datos

`src/datos/ejemplo.js` contiene **datos sintéticos de ejemplo**, generados con semillas fijas para que cada región muestre
un estado distinto del resultado. No son mediciones de IMERG ni del ONI. La interfaz muestra un aviso mientras se usen.

`src/contrato.js` documenta la forma de JSON que la interfaz espera. Es una **propuesta**: el contrato acordado con
Octavio no estaba disponible al construir la demo. Si sus nombres difieren, solo hay que ajustar `normalizar()`.
Si el JSON trae `tendencias` precalculadas, la interfaz las usa; si no, las calcula en el navegador.

## Método

- `src/estadistica.js`: mínimos cuadrados con intervalo t al 95 % y Theil-Sen con intervalo de Sen (1968) basado en la
  varianza de Mann-Kendall. Comprobado contra `scipy.stats.linregress` y `scipy.stats.theilslopes` con la serie de
  Nicaragua del ejemplo (coinciden en pendientes e intervalos).
- Resultado por región:
  - **Aumento / Disminución:** los dos intervalos excluyen el cero con el mismo signo.
  - **Evidencia insuficiente:** los dos intervalos incluyen el cero.
  - **Los métodos discrepan:** un intervalo excluye el cero y el otro no (o signos opuestos).
  - **Datos faltantes:** menos de 10 años con dato o región ausente.
- El ONI se muestra en un bloque plegado y secundario, como asociación con la anomalía respecto a la recta de Theil-Sen.

## Archivos

| Archivo | Contenido |
|---|---|
| `index.html` | Estructura de la página |
| `src/estilos.css` | Estilos, modo claro y oscuro, diseño móvil |
| `src/estadistica.js` | Tendencias y criterio del resultado |
| `src/contrato.js` | Lectura y validación del JSON |
| `src/graficas.js` | Mapa, serie anual, comparación de pendientes y ONI en SVG |
| `src/app.js` | Selección de región, descargas, carga de datos |
| `src/datos/contornos.js` | Contornos simplificados a mano (solo orientación) |
| `src/datos/ejemplo.js` | Datos de ejemplo sintéticos |
