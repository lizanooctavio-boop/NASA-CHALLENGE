# Expediente por área: verificación (2026-11-15)

## Pruebas

| Conjunto | Resultado |
|---|---|
| `tests/test_expediente.py` (geometría, estado, análisis, ZIP, PDF, i18n, límites) | 21 pasan, 1 omitida (la de navegador, que se activa con `ETD_E2E=1`) |
| Suite completa `pytest tests` | 332 pasan con la perspectiva (314 del expediente + 18 nuevas). `test_e2e_navegador.py` da 7 errores de preparación también en la base `fc7cfbd`, sin estos cambios: lanza Chrome sin acceso a los CDN y termina el proceso con `taskkill` (Windows). Este fallo no lo causan estos cambios. |
| `tests/test_perspectiva.py` (perspectiva de la próxima década: Mann-Kendall modificado y Benjamini-Hochberg frente a Python, reglas de clasificación y de destacadas, faltantes, límites físicos, identificador `P-`, ZIP, PDF y márgenes) | 18 pasan |
| `tests/e2e/expediente_navegador.cjs` (Chromium, Playwright, datos reales de POWER desde fixture) | Todos los casos pasan (`fallo: null`). En la consola solo hay errores de teselas bloqueadas (Esri, GIBS), de `/clima-base/*` (ya existían) y los de POWER provocados a propósito en el caso de fallo de red. No hay errores de página. |

Áreas geodésicas: diferencia relativa con pyproj ≤ 2·10⁻⁴; mediana frente a la superficie publicada por INETER < 0,5 %.
Pendientes: iguales a `scipy.stats.theilslopes` y `linregress`, y a `src/estadistica.js`.

## Casos de aceptación (recorrido en navegador)

| Caso | Resultado |
|---|---|
| Municipio de Masaya (T2M, anual, 1981–2024) | 146,96 km² (INETER: 146,88). Una celda. Sen −0,172 °C/década (IC 95 % −0,303 … −0,028), Mann-Kendall p = 0,021. Veredicto: tendencia a la baja. `R-f7eac6973fbe9734db0105782d153981` |
| Restaurar el enlace en otra sesión | Misma consulta, misma vista y el mismo `R-…`. El mensaje dice que coincide. |
| Abrir `resultados.json` guardado | Mismo `R-…` y 0 peticiones nuevas a POWER. Si el archivo se altera, se rechaza. |
| Departamento de Matagalpa (ejemplo) | 6 836,17 km², 7 celdas. Sen −0,182 °C/década (IC −0,349 … −0,003), p = 0,044. MCO −0,180 ± 0,073. `R-5100608be50eeddca994fbc7f5421647` |
| Punto en Managua, inglés, móvil | No se calcula área. Huella de la celda: 3 765 km². Aviso «not an average of any municipality». |
| Polígono irregular en C, dibujado con clics, temporada lluviosa (precipitación) | 8 celdas. Los pesos suman 1. Superficie 9 312,18 km² (la intersección con las celdas suma lo mismo). Centro: centroide LAEA. Muestra el aviso de inhomogeneidad de la lluvia MERRA-2. |
| 2015–2020 | «Datos insuficientes: menos de 10 años válidos». No se calcula pendiente. |
| Fallo de red de POWER | Mensaje de error. Si había un resultado anterior, el mensaje avisa que el PDF, el ZIP y el enlace siguen siendo de esa consulta. |
| GeoJSON con lazo o latitud −95 | Se rechaza con un motivo. |
| Enlace dañado o de versión futura | Se rechaza con un motivo y la app no se rompe. |

## Ejemplo

Los archivos están en `/mnt/project-files/expediente_territorial_2026-11-15/` del proyecto: el PDF completo en español, el resumen en inglés, el ZIP y capturas.

Enlace de consulta (Matagalpa, T2M 1981–2024, referencia 1991–2020):

```
https://nasa-challenge-q6cx.onrender.com/#inv=zbVPBbtswDP0Vg2c5kFQ7tb3j2hU7dIe1wIAVhcFITErMljxJTocV-ap9wn5skJMFGbCbRZPvPZKPb0Dx-0wjQgeUbGm8i_OQEATsKUT2Djp1_u6Nt7zzOffHRJbJJSrVSq4kCEic5iH_e6RxooBpDlhYGgrkQAW5gobC0oQh4Ugu-cJScY8JdzhMKArVNqrUUlcggC37o6SYhWBg3AyUofU9CNjOmRg6cBixn_wrBRAwUWBvPXRvwI4Ne-gypoAtO-gy8kFAoC0Fcobx37z2Ik8eBIwUKUL3pIQWV6IStViLa9GIVigplBJKPwswOLBFm5FGzsPZUMhd9xQnNIwDdHLVnsB648dpoOQjdCnMJJYadJwDSh6f24DG5EFf6pSr5iCAYkLLMbFZpI-UvM2lTxDJ9SM6138jZ3EYQMBoPDwLcLyno4j6IGDPMS21hlwKPnenV1I3qhVls17JWurqWcBP78ejoiyu33PkZfhuHobc85QXg86PODD26GbMjBQTL9u3vKewWxZ0EDChywog0GKrrFgABjqO3-YdsikvbVHKChvTggDnx03Iaz67ZHHZlFnQjuw4poCJ9zm-BDLo2RzsKC3GOE0BLllAwF8vH_v6D1mWH7whe_bLifyMfOZ6jR8_3T7efi5v7u7edzcXRPHykuCBXbG8fv9yxTRvBjZo8XQckcI--_FdMWIw-XaKxDROvvjy4aHQUq9LpUpVP6qmq2Wnq5XS8muW-YLxpd-RHykFXu5GrQmbuqqv261sJFbr-spIRY2pKltpJZu11NgaktfbdX29adcb29aN1oR4hdrC4fAH&r=R-5100608be50eeddca994fbc7f5421647
```

El enlace funcionará cuando esta rama esté publicada en la demo. Ahora mismo la demo no tiene la pestaña «Area report».
No hay enlace a un resultado guardado en servidor, porque la app es estática. El resultado inmutable es `resultados.json`, dentro del ZIP.

## Comparación entre fuentes en el ejemplo

En Matagalpa, POWER (MERRA-2) da −0,18 °C/década. Para la Región Central, GISTEMP v4 da +0,29 °C/década (IC 0,21 … 0,37).
El informe presenta esta diferencia como una comparación entre fuentes. Las dos fuentes difieren en producto, escala y periodo. No se usa «los métodos no coinciden»: esa frase se reserva para Theil-Sen frente a MCO aplicados a la misma serie.

## Limitaciones y pendientes

- **Sin almacén persistente.** Para tener enlaces `/r/<id>` haría falta un servicio que guarde `resultados.json` por su hash. Ver `modelo_estado.md`.
- **Resolución gruesa.** POWER solo admite consultas puntuales y su resolución es de 0,5° × 0,625°. Un municipio pequeño equivale a una celda.
- **Precipitación.** La lluvia de MERRA-2 tiene una inhomogeneidad conocida que produce tendencias espurias. Se avisa en el informe, y el ejemplo usa temperatura por eso.
- **Autocorrelación.** No se corrige la autocorrelación de los residuos; solo se informa.
- **Límites INETER.** El servicio WFS no publica una versión de los límites, así que se registra la marca de tiempo del WFS.
- **Traducción.** Esta vista funciona en ES/EN. Traducir el resto de la app queda fuera de alcance.
- **Perspectiva de la próxima década.** Método, reglas y ejemplo en `perspectiva.md`. CMIP6 usa los años reales 2015–2040, descargados el 2026-11-15: 624 de 624 recortes. La imagen de portada (Esri World Imagery o, si falla, NASA Blue Marble de GIBS) se pide desde el navegador: en el contenedor de pruebas esos servicios están bloqueados, así que el ejemplo sale sin imagen y la prueba usa una imagen sintética.
- **Extensiones para Nicaragua aún no hechas.** SPI, canícula, comparación con boletines INETER/CRRH, lagos, incendios, imagen para WhatsApp y modo sin conexión.
