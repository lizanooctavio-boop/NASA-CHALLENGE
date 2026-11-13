# Lista de comprobación de requisitos de entrega — NASA Space Apps 2026

> **Alcance y fuentes oficiales comprobadas (`13-11-2026`):**
> - *Project Submission Guide*: `https://www.spaceappschallenge.org/resources/project-submission-guide/`
> - *Judging & Awards Guide*: `https://www.spaceappschallenge.org/resources/judging-awards-guide/`
> - *Participant FAQs*: `https://www.spaceappschallenge.org/resources/participant-faqs/`
> - *Terms and Conditions / Legal*: `https://www.spaceappschallenge.org/legal/`
> - *Challenge Page («Be an Earth System Trend Detective!»)*: `https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/`

Leyenda de estado:
- **Cumple:** verificado en el repositorio o cubierto en `docs/entrega/`.
- **Pendiente:** falta ejecución, integración de ramas o decisión del equipo antes de enviar.
- **Riesgo / Riesgo crítico:** punto que puede invalidar la elegibilidad, bloquear la evaluación o reducir la calificación si no se resuelve.

---

## 1. Plazo, casillas de envío, sede e integrantes

| Requisito oficial | Estado | Evidencia / aplicación a este proyecto y acción necesaria |
| :--- | :--- | :--- |
| **Botón «Submit for Judging» antes del cierre local** | **Pendiente** | Cita oficial (*Project Submission Guide*): «You must click the "Submit for Judging" button prior to Sunday, November 15 at 11:59 p.m. local time of your Local Event.» En la sede **Managua (`UTC−6`)**, el límite es el **domingo `15-11-2026` a las `23:59` (`UTC−6`)**. Guardar borradores con antelación y enviar con al menos 2–3 horas de margen. |
| **Casillas obligatorias de envío (`Terms and Conditions` y `Confirm All Work is Original`)** | **Riesgo crítico** | *Project Submission Guide* exige marcar literalmente **`Terms and Conditions`** y **`Confirm All Work is Original`** al enviar. **Bloqueante:** el repositorio tiene `54` commits entre el `11-11` y el `13-11-2026` más antecedentes en `SICC-952` (ver sección 4). El equipo **no debe marcar `Confirm All Work is Original` a la ligera** ni ocultar fechas: debe consultar antes al *Local Lead* de Managua (`[DECISIÓN DEL EQUIPO]`). |
| **Todos los integrantes confirmados en la misma sede (Managua)** | **Pendiente / Riesgo** | `[CONFIRMAR]` Todos los autores/integrantes activos deben estar inscritos, verificados y unidos a la **misma sede local (Managua)** y al **mismo equipo** antes de pulsar **Submit for Judging**. |
| **Cuentas únicas y composición del equipo** | **Pendiente** | `[CONFIRMAR]` Verificar que los integrantes reales del equipo coincidan con las cuentas registradas en la plataforma, sin miembros omitidos ni cuentas duplicadas. |
| **Participantes menores de edad (`< 18` años)** | **Pendiente / Riesgo** | Cita oficial (*Participant FAQs*): «participants must be registered for the event by a parent or legal guardian and must be accompanied by a parent or legal guardian at all times during the event. […] Local Events may have additional requirements for persons under 18». Cita oficial (*Terms*): «Recognizable names, voices, and likenesses of persons under the age of 18 should not be included in any submission.»<br>**Acción:** `[CONFIRMAR]` las edades de todos los autores/integrantes. Si alguno tiene `< 18` años: (1) verificar registro y acompañamiento presencial/virtual permanente por madre/padre/tutor legal y requisitos locales de Managua; (2) excluir su nombre reconocible, voz e imagen de cualquier vídeo, audio, diapositiva, captura o formulario público. |

---

## 2. Visibilidad pública, enlaces, FortiGuard e idioma

| Requisito oficial | Estado | Evidencia / aplicación a este proyecto y acción necesaria |
| :--- | :--- | :--- |
| **Enlaces públicos sin acceso restringido durante evaluación** | **Riesgo crítico** | Cita oficial (*Project Submission Guide*): «share a publicly accessible link with no logins, permissions, or registrations required. If judges can't access your project, it can't be evaluated or judged.» **Comprobado el `13-11-2026`:** `https://github.com/lizanooctavio-boop/NASA-CHALLENGE` y su endpoint en la API de GitHub devuelven **HTTP `404`** sin autenticación (repositorio privado). **Acción obligatoria antes de enviar:** auditar secretos/tokens en historial y archivos, decidir licencia raíz, hacer público el repositorio (o espejo autorizado) y completar todos los `[ENLACE]`. |
| **Recomendación oficial de FortiGuard / filtros corporativos** | **Riesgo** | La guía advierte que filtros como **FortiGuard** en redes de jueces pueden bloquear dominios recién creados, acortadores (`bit.ly`, etc.), IPs sueltas o sitios mal categorizados. **Acción:** usar solo URLs HTTPS directas y reconocidas (`github.com`, `youtube.com`, `vimeo.com` o hosting consolidado) y probar cada `[ENLACE]` desde una conexión móvil/externa limpia sin sesión iniciada. |
| **Sin credenciales ni datos personales (PII) expuestos** | **Cumple (auditar antes de abrir)** | En `docs/entrega/` no hay credenciales, correos personales ni tokens. El código revisado (`scripts/datos/`) lee `.netrc` localmente sin fijar contraseñas. **Obligatorio antes de pasar a público:** revisar ramas y archivos ignorados/commits antiguos por si algún colaborador subió rutas personales o claves. |
| **Idioma del formulario y demo** | **Cumple en `docs/entrega/`** | Cita oficial (*Project Submission Guide*): «All content in the project form must be in English.» La interfaz (`index.html`, `app/`) y los borradores externos (`FORMULARIO_PROYECTO_EN.md`, `DEMO_VIDEO_30S_EN.md`, `DEMO_DIAPOSITIVAS_EN.md`, cuerpo de `DECLARACION_SI.md`) están en **inglés**. |

---

## 3. Formato del demo, marca, SI (*Super Intelligence*) y licencias

| Requisito oficial | Estado | Evidencia / aplicación a este proyecto y acción necesaria |
| :--- | :--- | :--- |
| **Formato exclusivo del demo (`<= 30 s` vídeo O `<= 7` diapositivas)** | **Pendiente (guiones listos)** | Cita oficial (*Project Submission Guide*): «Video (30 seconds or less) or slide deck (up to seven slides including title and intro slides)». En `docs/entrega/` quedan listas ambas opciones: `DEMO_VIDEO_30S_EN.md` (30 s máximos, locución cerrada en ~28 s) y `DEMO_DIAPOSITIVAS_EN.md` (7 diapositivas totales). `[DECISIÓN DEL EQUIPO]` elegir una de las dos piezas, producirla y comprobar su enlace público. |
| **Declaración de IA (*Super Intelligence*, SI), marca de agua y metadatos** | **Pendiente (`[CONFIRMAR]`)** | Toda asistencia de SI (**Claude Code (Opus)**, **Codex**, **Claude Opus**, **Gemini**) se documenta en `DECLARACION_SI.md`. Si el vídeo o las diapositivas usan voz sintética (p. ej. ElevenLabs) o visuales/clips generados por SI, es obligatorio colocar **marca de agua visible** en los fotogramas/diapositivas afectados, declararlo en el texto y consignarlo en los metadatos del archivo. |
| **Prohibición de usar logos/insignias de NASA (y emblemas oficiales de agencias)** | **Cumple (mantener al grabar)** | Ni la interfaz web ni los guiones de `docs/entrega/` usan los logotipos *meatball* o *worm* de la NASA, insignias de misiones ni banderas oficiales. La atribución a NASA, NOAA y CSA es exclusivamente textual. Mantener esa regla al editar capturas o portada del demo. |
| **Licencia abierta obligatoria e identificación de *Solution Materials*** | **Riesgo crítico / Pendiente** | Citas oficiales (*Terms*): «You agree that any original content […] is freely available without restriction or is licensed as open source as defined by the Open Source Initiative (OSI) […] If you do not specify a specific OSI compliant license, NASA will distribute your original content under an Apache 2.0 license.» Además: «Any licenses applicable to your Solution Materials must be identified in the documentation that you submit with your Solution. NASA will not accept or post any Solutions that do not include appropriate license documentation for your Solution Materials.»<br>**Estado real comprobado:** no hay archivo `LICENSE` en la raíz de `origin/codex/verificacion-entrega`. Hay código adaptado del tutorial CSA bajo MIT (`scripts/sar/LICENSE-CSA.txt`) y fuentes con condiciones particulares (`CRU TS 4.10` bajo `ODbL`, `RainViewer` solo uso personal/educativo, `Open-Meteo` capa gratuita no comercial, `SINAPRED` sin licencia abierta explícita, `RCM EODMS` pendiente de EULA). **Acción urgente:** elegir e incluir `LICENSE` OSI (p. ej. `Apache-2.0` o `MIT`) en la raíz del código, separar claramente código propio de datos/servicios de terceros en la documentación y resolver `RainViewer` / `Open-Meteo` según `PROPUESTAS.md`. |
| **Cita explícita de todas las fuentes** | **Cumple con verificaciones pendientes** | Cita oficial (*Terms*): «all resources, even open source resources, must be cited.» Inventario detallado en `FUENTES_Y_LICENCIAS.md`, incluyendo los nuevos recursos verificados (`AIRS3STM v7.0`, `OMNO2d v003`, `GES DISC OPeNDAP`, `Statsig` por Allon Korem `2025-08-07`, `NTRS 20090042747` Acker et al. `2009`), dejando con `[VERIFICAR]` solo los datos no confirmables (p. ej. `LECTURA_MEDIUM.md` con bloqueo HTTP `403` de Cloudflare). |

---

## 4. Riesgo crítico (`[DECISIÓN DEL EQUIPO]`): trabajo previo al evento (`11–13-11-2026` y `SICC-952`)

### Hechos verificados en el repositorio (`git log --all`) y reglas aplicables
1. **Regla oficial (*Participant FAQs*):** «Resources for each challenge will be published on November 13. Teams are not allowed to begin working on the challenges prior to the hackathon.»
2. **Casilla del formulario (*Project Submission Guide*):** al entregar se exige marcar **`Confirm All Work is Original`**.
3. **Historial Git comprobado (`54` commits únicos totales antes de la apertura de Managua el `14-11-2026`):**
   - **Primer commit:** `f5fad37` — `2026-11-11 22:34:36 -0600` (`lizanooctavio-boop`, *Initial commit*).
   - **Distribución por fecha (hora CST `UTC−6`):**
     - `2026-11-11`: **`15`** commits.
     - `2026-11-12`: **`15`** commits.
     - `2026-11-13` (madrugada, antes de la apertura del evento): **`24`** commits (último registrado en esta rama: `4c06fcd` a las `03:56:37 -0600`).
   - **Distribución por autor en Git (`--all`, desglose `11-11 / 12-11 / 13-11`):**
     - `lizanooctavio-boop`: **`27`** (`10 / 5 / 12`)
     - `benjaminhr8687`: **`11`** (`1 / 3 / 7`)
     - `AstralPiolinXD`: **`11`** (`4 / 5 / 2`)
     - `Manuel Paniagua`: **`4`** (`0 / 2 / 2`)
     - `JAVITHEARKHI`: **`1`** (`0 / 0 / 1`)
   - **Infraestructura anterior del equipo (`SICC-952`):** código base meteorológico y visor previo reutilizado y adaptado como contexto en vivo (`ECMWF IFS` / `Open-Meteo`).
   - **Qué se construyó entre el `11-11` y el `13-11`:** prácticamente todo el motor estadístico (`tendencia.py`, `tendencia_robusta.py`, `fdr.py`, `indicadores.py`, `modelo_estacional.py`), descargas y contrastes multi-fuente (`data/`), adaptadores CSA/SWOT/OPERA/RCM, la interfaz `Investigate / Learn / Sources` (`origin/codex/recursos-interfaz`) y esta documentación.

### Regla obligatoria de conducta y consulta al *Local Lead* de Managua
- **Prohibido minimizar u ocultar:** no redactar atenuantes ambiguos como «poco antes de la apertura» ni dar a entender que todo el núcleo técnico se programó dentro del fin de semana `14–15-11`. Tampoco reescribir ni manipular el historial Git (`rebase` / `commit --amend` de fechas) para aparentar otra cronología.
- **Acción bloqueante antes de enviar (`[DECISIÓN DEL EQUIPO]`):** contactar **hoy mismo** al *Local Lead* de Managua y exponer con total honestidad estos hechos para confirmar por escrito cómo proceder respecto a la regla *pre-event work* y la casilla `Confirm All Work is Original`:
  - Preguntar si el *Local Lead* autoriza continuar declarando `SICC-952` y las utilidades preparadas el `11–13-11` como herramientas/código previo abierto del equipo y acotando claramente qué análisis, integraciones y entregables se completan durante la hackatón (`14–15-11`), **o** si la política estricta de la sede exige partir durante el evento oficial limitando lo anterior a librerías/datos base permitidos.
- Usa las dos variantes del campo *Work Timeline / Development History* en `FORMULARIO_PROYECTO_EN.md` §8 solo después de esa confirmación.

> **Borrador de mensaje para enviar al *Local Lead* de Managua (listo para copiar y adaptar):**
>
> *Hola [Nombre del Local Lead],*
>
> *Somos parte del equipo inscrito en la sede Managua para el reto «Be an Earth System Trend Detective!». Antes de avanzar al envío oficial y con total transparencia, queremos consultarles un punto importante sobre elegibilidad y la casilla «Confirm All Work is Original».*
>
> *Parte de nuestro equipo reutilizó un visor meteorológico propio anterior (`SICC-952`) y adelantó desarrollo de código, ingesta de datos NASA/NOAA/CSA y pruebas en un repositorio privado de GitHub entre el 11 y el 13 de noviembre (54 commits totales antes de la apertura oficial del 14 de noviembre).*
>
> *Sabemos que las FAQ indican «Teams are not allowed to begin working on the challenges prior to the hackathon» y queremos cumplir al 100 % las reglas de la sede y de Space Apps. ¿Cómo nos recomiendan proceder para mantener plena validez: (a) declarar explícitamente el visor `SICC-952` y ese avance previo como código/herramientas anteriores abiertas del equipo diferenciando el trabajo e integración final realizados durante el 14–15 de noviembre, o (b) debemos acotar nuestra entrega únicamente a módulos reimplementados/integrados durante las fechas oficiales del evento?*
>
> *Agradecemos mucho su orientación por escrito para proceder correctamente antes del cierre del domingo 15 a las 23:59.*

---

## 5. Alineación con los 5 criterios de evaluación (escala `1` a `5`)

En *Judging & Awards Guide*, cada criterio recibe nota de **`1` a `5`** (*Very Poor* = 1, *Below Average* = 2, *Average* = 3, *Good* = 4, *Excellent* = 5):

| Criterio (`1–5`) | Qué buscan los jueces | Evidencia verificada de este proyecto | Brecha / riesgo actual que reduce la nota |
| :--- | :--- | :--- | :--- |
| **1. Impact** | Magnitud del problema resuelto, utilidad práctica real y claridad de beneficios. | Responde una necesidad crítica en Nicaragua y Centroamérica donde los registros terrestres son escasos o discontinuos (lluvia `NOAA GHCN-D` en Nicaragua se interrumpe hacia `1989–1991`; estaciones activas en `CRU TS 4.10` bajan de `3,7` a `1,8` tras `2015`) y ENOS domina la señal interanual (`IMERG` jun–nov vs. ONI `r = −0,561` en Nicaragua y `−0,591` en `caja_sicc`). Permite exportar series CSV/JSON con procedencia y leer límites reales en *Learn*. | En `origin/codex/recursos-interfaz`, `data/recursos_integrados.json` contiene hoy **solo las `12` investigaciones base de Nicaragua (`contrastes = []`)**; hasta fusionar los PRs abiertos (`#7`, `#9`, `#12`) y ejecutar `python -m clima_nic recursos` en `backend/`, la web no muestra Canadá, radar SAR, hidrología ni segundas opiniones. |
| **2. Creativity** | Originalidad del enfoque y forma en que combina recursos o comunica la historia. | Convierte las discrepancias entre fuentes en **pistas diagnósticas explícitas** (no defectos escondidos): `GISTEMP v4` (`+0,2939 °C/déc`, `p < 0,001`) frente a `MERRA-2/POWER` (`−0,1119 °C/déc`, quiebre `Pettitt 1999`, `p = 0,0077`); `GLDAS-2.1` frente a `MERRA-2 GWETTOP` (correlaciones `r = 0,025` en NIC y `0,075` en Central); `OMI NO2` urbano (`−0,0434`) vs. rural (`−0,0487`); y compara Nicaragua frente a las **Praderas de Canadá** (`467 127,9 km²`) mediante globo 3D `Three.js` que se despliega en Mercator sobre `Leaflet`. | El recorrido de 30 s debe abrir directo con ese contraste (`Nicaragua vs. Canadian Prairies`) y un choque entre fuentes; empezar explicando arquitectura genérica diluye el impacto inicial. |
| **3. Validity** | Rigor científico, viabilidad técnica y solidez estadística. | **Fuerte ventaja técnica:** combina `3` veredictos de tendencia (`Trend detected`, `Not enough evidence of a trend`, `Methods disagree`) mediante consenso simultáneo de 3 intervalos al 95 % (`MCO` con grados de libertad efectivos por `AR(1)`, `Newey–West HAC` y `Theil–Sen`) más `Mann–Kendall modificado` (`Hamed & Rao, 1998`), guardia de registro corto (`MIN_ANIOS = 10`, etiqueta `Record too short for a trend test` en `SWOT`), detección descriptiva de quiebres (`Pettitt, 1979`), control múltiple espacial `Benjamini–Hochberg FDR (q = 0,10)`, sensibilidad `±3 años` y `leave-one-year-out`. Documenta salvedades reales: `AIRS3STM v7` coincide en signo (`+0,1261 °C/déc`, `MK p = 0,0095`, `r = 0,9243` con GISTEMP) pero su MCO mensual crudo (`p = 0,0726`) no alcanza significación y solo marca ~1/3 de la tasa superficial; `GLDAS-2.1 Central` pierde el veredicto firme al excluir `2001–2002` (`Pettitt 2013 p = 0,0262`, advertencia forcing AGRMET); Golfo de Fonseca (`7,02 mg/m³`, `p = 0,0007` mensual crudo vs. `MK p = 0,0804`) contrastado con Pacífico abierto (`0,4361 mg/m³`, `MK p = 0,1278`, coherente con interferencia por turbidez); y `NO_VALIDADA` en máscaras SAR hasta tener verdad terreno o escenas `RCM #3787605`. | Existen discrepancias numéricas internas sin limpiar: `docs/auditoria.md` conserva valores antiguos de `CMIP6` (`+1,55 / +1,96 °C`, lluvia `+0,9 % / −4,3 %`) frente a `data/fenomenos_nicaragua.json` (`+1,399 / +1,980 °C`, lluvia `−5,446 % / −10,488 %`), y `0` de las `160` tareas `AppEEARS` han completado todavía. |
| **4. Relevance** | Respuesta directa a «Be an Earth System Trend Detective!» (*qué, dónde, cuánto, significancia* y uso de recursos del reto). | Contesta con precisión qué cambia (`lluvia, temperatura, vegetación, humedad de suelo, agua superficial/lagos, calidad del aire y clorofila costera`), dónde (`Nicaragua`, subregiones, Golfo de Fonseca, Pacífico abierto, Managua vs. Chontales y Praderas de Canadá), cuánto y con qué confianza estadística, sustituyendo el servicio retirado *Hydrology Data Rods* por `GES DISC Cloud OPeNDAP`. | Si el demo no incorpora los datos de Canadá, radar y contrastes (`PR #7`, `#9`, `#12`), parte central de los recursos del reto queda solo en ramas secundarias. |
| **5. Presentation** | Claridad comunicativa, narrativa y calidad de formulario/demo. | Diseño limpio en inglés, recorridos guiados (`Guided examples`), pestaña pedagógica *Learn* que advierte explícitamente que *«Not enough evidence of a trend» ≠ «no change»*, y materiales preparados en inglés sin marcas prohibidas. | `REVISION_ACCESIBILIDAD.md` reporta contraste bajo sobre sectores claros del globo (`rgba(..., .58)`), pérdida de foco en recorridos guiados, gráficas `<canvas>` sin `role="img"` ni tabla de respaldo, y barra lateral recortada a `390 px`. Corregir esos ajustes rápidos de CSS/JS mejora tanto accesibilidad como impresión visual. |

---

## 6. Pendiente del equipo (marcadores para resolver antes del envío)

- **`[DECISIÓN DEL EQUIPO]`** Consultar hoy al *Local Lead* de Managua sobre el trabajo del `11–13-11` (`54` commits) y `SICC-952` antes de marcar `Confirm All Work is Original`.
- **`[DECISIÓN DEL EQUIPO]`** Elegir licencia OSI raíz (`LICENSE`: `Apache-2.0` o `MIT`) y definir cómo aislar o documentar `CRU TS 4.10` (`ODbL`), `RainViewer` y `Open-Meteo`.
- **`[DECISIÓN DEL EQUIPO]`** Escoger entre vídeo `<= 30 s` (`DEMO_VIDEO_30S_EN.md`) o presentación `<= 7` diapositivas (`DEMO_DIAPOSITIVAS_EN.md`), y decidir título unificado (`Earth Trend Detective` frente a `Earth System Trend Detective`).
- **`[CONFIRMAR]`** Edades de todo el equipo (cumplimiento estricto `< 18` en sede y exclusión de identidad/voz/imagen en entrega si hubiera menores), pertenencia unificada a la sede **Managua**, ausencia de secretos antes de hacer público el repositorio y si se empleó voz/imagen generada por SI.
- **`[ENLACE]`** Hacer público el repositorio en GitHub, publicar la web demo en HTTPS limpio (apto para FortiGuard) y subir el vídeo o PDF público.
