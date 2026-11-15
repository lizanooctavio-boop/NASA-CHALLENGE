# Auditoría de rigor científico y citas (Agente E)

- **Rama:** `codex/audit-ciencia`
- **Cobertura auditada:** 217 investigaciones en las 8 categorías (`lluvia`: 55, `temperatura`: 15, `vegetacion`: 10, `agua`: 65, `costa`: 32, `aire`: 2, `polos`: 31, `ciclones`: 7), 3 recorridos guiados (`lluvia_nicaragua`, `frecuencia_lluvia`, `nicaragua_vs_praderas`), pestaña `Learn`, pestaña `Sources`, 57 DOI únicos y 49 URLs de fuentes.
- **Distribución de veredictos observada (217 series):** `tendencia_detectada`: 79, `evidencia_insuficiente`: 85, `metodos_discrepan`: 48, `sin_tendencia` (registro corto): 5.

## Comprobación de DOI, enlaces y recorridos

- **Crossref (57 DOI únicos):** 57/57 devolvieron HTTP 200 (50 en el primer pase paralelo y 7 tras reintento secuencial por límite de tasa HTTP 429).
- **Recorridos guiados:** los 3 recorridos apuntan a IDs existentes; en `clorofila_golfo_fonseca`, la nota de `#aprender-autocorrelacion` (`p = 0.08`, 264 valores mensuales 2003–2024) coincide con el valor calculado (`mann_kendall_p = 0.0804`).
- **URLs externas (49 URLs):** 45 devolvieron 200/301/302; 4 devolvieron errores transitorios o de bloqueo automático (`doi.org/10.5281/zenodo.7668424` → 403, `psl.noaa.gov` → 429, `ipad.fas.usda.gov` → 503, `donnees-data.asc-csa.gc.ca` → timeout).

## Hallazgos

| ID | Gravedad | Dónde | Qué pasa | Cómo reproducirlo | Propuesta |
|---|---|---|---|---|---|
| E-01 | **alta** | `backend/clima_nic/recursos.py` (`clorofila_*`) | Las 5 series costeras de clorofila-a (`costa`) solo indican que más clorofila suele significar más algas, sin advertir en la ficha que en estuarios someros y turbios (como el Golfo de Fonseca) los sedimentos y la materia orgánica disuelta (CDOM) pueden inflar la señal satelital. | Abrir `Investigate` → `Coast` → `Gulf of Fonseca` y leer `definicion_en` y `notas`. | Añadir una nota metodológica clara sobre interferencia de sedimentos/CDOM y uso de medias anuales para evitar sesgo estacional. |
| E-02 | **alta** | `backend/clima_nic/recursos.py` (`lluvia_NIC`, `lluvia_HND`, `lluvia_CRI`, `lluvia_CAN_prairies`, `lluvia_jun_nov_NIC`, `lluvia_may_sep_CAN_prairies`, `ndvi_sitios_*`) | Estas series base carecen de `notas` y su `definicion_en` no especifica el alcance espacial (promedio nacional/de caja o sitios de muestreo MODIS) ni el producto/resolución, a diferencia del resto de módulos regionales. | Abrir `Investigate` → `Rainfall` → `Nicaragua` (`Annual rainfall`) o `Vegetation` → `Pacific lowlands` (`NDVI`). | Precisar en `definicion_en` y `notas` que son promedios espaciales sobre el polígono/sitios de muestreo y su agregación anual/estacional. |
| E-03 | **alta** | `index.html` (`#aprender-metodos`, `#aprender-registro-corto`) | `#aprender-registro-corto` solo menciona SWOT y SMAP, omitiendo las series cortas de radar SAR en Lake Cocibolca (`Sentinel-1` y `RCM`) que cubren solo una fracción parcial del lago y no están validadas; `#aprender-metodos` no explicita el nivel α = 0.05 bilateral ni que Theil–Sen usa un intervalo no paramétrico. | Abrir `Learn` y revisar `#aprender-metodos` y `#aprender-registro-corto`. | Completar `#aprender-registro-corto` con radar SAR (Sentinel-1 / RCM) y precisar α = 0.05 bilateral / carácter no paramétrico en `#aprender-metodos`. |
| E-04 | media | `backend/clima_nic/recursos.py` (`omi_no2_managua`, `omi_no2_rural`) | Las series de NO₂ mencionan días despejados, pero no detallan la resolución espacial gruesa de OMI (~13 × 24 km en nadir) ni el menor muestreo en estación lluviosa. | Abrir `Investigate` → `Air` → `Managua urban box`. | *(Propuesta)* Añadir nota sobre resolución de OMI y muestreo nuboso. |
| E-05 | baja | `data/recursos_integrados.json` (`Sources`) | Cuatro URLs de fuentes externas devolvieron 403/429/503 o timeout en comprobación automática por límites de tasa o mantenimiento temporal. | Ejecutar comprobación HTTP sobre URLs de `Sources`. | *(Propuesta)* Revisar periódicamente enlaces externos o preferir enlaces DOI persistentes cuando existan. |

## Capturas de referencia

- `docs/auditoria/img/ciencia-01.png` a `docs/auditoria/img/ciencia-03.png`.
