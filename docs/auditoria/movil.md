# Auditoría de diseño adaptable y rendimiento (Agente C)

- **Rama:** `codex/audit-movil`
- **Dispositivos y resoluciones probadas (Edge headless / DevTools):** `360×740` (vertical y horizontal), `390×844` (vertical y horizontal), `768×1024` (vertical y horizontal) y `1366×768`.

## Métricas medidas

- **Peso de datos:**
  - `data/recursos_integrados.json`: **595.2 KB** (0.58 MB)
  - `data/fenomenos_nicaragua.json`: **904.2 KB** (0.88 MB)
- **Desbordamiento horizontal (`scrollWidth > innerWidth`):** `false` en las 7 combinaciones de resolución/orientación.
- **Gráfica en móvil (`360×740`):** `#inv-serie` mide `256 × 250 px` dentro de un panel de `340 px`; se lee sin recortes.
- **LCP y CLS medidos:**
  - `360×740`: LCP `1404 ms`, CLS `0`
  - `390×844`: LCP `328 ms`, CLS `0`
  - `768×1024`: LCP `384 ms`, CLS **`0.1726`** (> 0.10)
  - `1024×768`: LCP `384 ms`, CLS **`0.1758`** (> 0.10)
  - `1366×768`: LCP `424 ms`, CLS `0`

## Hallazgos

| ID | Gravedad | Dónde | Qué pasa | Cómo reproducirlo | Propuesta |
|---|---|---|---|---|---|
| C-01 | **alta** | `app/estilos.css` | En móvil y tablet (`360×740`, `390×844`, `768×1024`), varios botones interactivos miden menos de `44 px` de alto (`nav button`: 40 px; `#vista-globo`/`#vista-mapa`: 28 px; `#indicador-datos`: 32 px; `#solomapa`: 40–41 px). | Medir `getBoundingClientRect()` de controles visibles en `360×740` y `768×1024`. | Fijar `min-height: 44px` en `@media(max-width:700px),(max-height:500px) and (max-width:1000px)` y `@media(pointer:coarse)` para navegación, interruptor de vista, botones de acción y selectores. |
| C-02 | **alta** | `app/estilos.css`, `app/shell.js` | En tablet (`768×1024` y `1024×768`), el CLS inicial supera el umbral recomendado (`0.1726` y `0.1758` > `0.10`) por el reajuste tardío de la cabecera y ventanas al calcular variables de alto. | Cargar `/` en `768×1024` y observar `layout-shift` en `PerformanceObserver`. | Estabilizar las alturas por defecto en `app/estilos.css` (`--alto-cabecera`, `--alto-lt`, `contain: layout style` en ventanas fijas) y ajustar el cálculo en `app/shell.js`. |
| C-03 | **alta** | `index.html`, `app/estilos.css` | Los `<script>` síncronos en `index.html` no usan `defer`, y en red lenta (Slow 4G) mientras se descargan `recursos_integrados.json` (595 KB) y `fenomenos_nicaragua.json` (904 KB), `#inv-veredicto` e `#ind-veredicto` quedan vacíos sin indicador de carga. | Abrir `Investigate` o `Climate indicators` con throttling Slow 4G. | Añadir `defer` a los scripts en `index.html`, metadato `theme-color`, y mostrar un indicador visual de carga con CSS (`#inv-veredicto:empty::before`, `#ind-veredicto:empty::before`). |
| C-04 | media | `data/recursos_integrados.json` (595 KB) | El paquete integrado de 217 series se descarga completo en una sola petición al abrir `Investigate`, `Learn` o `Sources`. | Inspeccionar Network en DevTools con Slow 4G. | *(Propuesta)* Habilitar compresión Brotli/gzip en servidor o dividir metadatos de series por categoría. |
| C-05 | baja | `app/estilos.css` (`740×360` horizontal) | En móvil horizontal con `Hide panels`, la barra inferior de capas y línea de tiempo ocupa una fracción alta de la pantalla. | Activar `Hide panels` en `740×360`. | *(Propuesta)* Compactar la altura de `#controles-mapa` en `max-height: 500px`. |

## Capturas de referencia

- `docs/auditoria/img/movil-01.png` a `docs/auditoria/img/movil-06.png`.
