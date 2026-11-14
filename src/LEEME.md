# Interfaz climática (index.html y src/)

Demo web estática para Earth System Trend Detective: «¿Cambia la conclusión sobre la lluvia cuando ampliamos el mapa?».
Sin librerías externas, sin paso de compilación y sin conexión a internet.

## Abrir en local

- **Lo más rápido:** doble clic en `index.html`. Sin servidor, el navegador no deja leer `data/`, así que se ven los datos de ejemplo.
- **Con los datos reales:** desde la raíz del repo, `python -m http.server 8000` y abrir `http://localhost:8000/`.
  La página lee `data/clima.json` y `data/dominios.geojson` por sí sola.

| Parámetro de URL | Efecto |
|---|---|
| `?region=HND` | Abre otro dominio (`caja_sicc`, `NIC`, `HND`, `CRI`). Por defecto, `NIC`. |
| `?datos=otra/ruta.json` | Carga otro archivo con la forma del contrato (requiere servidor). |
| `?caso=faltantes` | Prueba el aviso de datos faltantes: quita Honduras y deja Costa Rica con 7 años. |

## Despliegue (Render, sitio estático)

- Publish directory: `.` (raíz del repo, donde está `index.html`).
- Build command: ninguno.
- Cuando `data/clima.json` esté en la rama publicada, la demo lo usa sin cambiar nada. Mientras no exista, muestra
  los datos de ejemplo con un aviso visible.

## Datos

- Contrato: `data/contrato.md` (versión 1.0.0, rama `codex/datos-climaticos`). `src/contrato.js` lo lee.
- La interfaz usa `veredicto` y `veredicto_texto` del JSON y **no recalcula tendencias**. Muestra los tres intervalos
  (mínimos cuadrados principal, HAC y Theil–Sen), la superposición entre dominios y los límites de `metadatos.limites`.
- Si `tendencia.estado` ≠ `ok` o faltan años, muestra `mensaje` y no dibuja tendencia.
- `NIC_fuera_caja` se lee pero no se muestra en el selector (rol auxiliar).
- Las rectas de la serie anual se trazan con la pendiente del JSON: la de mínimos cuadrados pasa por las medias,
  la de Theil–Sen por las medianas.
- `src/datos/ejemplo.js` contiene **datos sintéticos** con la forma del contrato. Imitan el patrón de los resultados de
  referencia (tres dominios con evidencia insuficiente y Costa Rica con métodos que discrepan), pero ninguna cifra es real.
- Sin `data/dominios.geojson`, el mapa usa contornos simplificados a mano (`src/datos/contornos.js`).

## Archivos

| Archivo | Contenido |
|---|---|
| `index.html` | Estructura de la página |
| `src/estilos.css` | Estilos, modo claro y oscuro, diseño móvil |
| `src/contrato.js` | Lectura y validación de `data/clima.json` (contrato 1.0.0) |
| `src/graficas.js` | Mapa, serie anual, comparación de intervalos y ONI, en SVG |
| `src/app.js` | Carga de datos, selección de dominio y descargas |
| `src/datos/contornos.js` | Contornos simplificados a mano (respaldo del mapa) |
| `src/datos/ejemplo.js` | Datos de ejemplo sintéticos |
