# Auditoría del backend — 15 de noviembre de 2026

Repositorio NASA-CHALLENGE, commit `695efb9`, rama `codex/benjamin-arcgis-pro-interface`, basada en `codex/demo-render`. Revisión local de código y reproducciones con los datos incluidos y entradas sintéticas. No se modificaron archivos del repositorio ni se realizaron descargas o llamadas a proveedores externos. No es una certificación exhaustiva del backend.

## 1. P1 — El pronóstico IMERG publica la habilidad de MERRA-2

Ubicación: `backend/clima_nic/consulta.py:121–128`.

Reproducción con FastAPI TestClient: `GET /pronostico?region=NIC&anio=2024&variable=lluvia_jun_nov_imerg` devuelve HTTP 200, producto IMERG y `habilidad_publicada={"msess":0.3514,"p_permutacion":0.001}`.

En el JSON del proyecto esas cifras pertenecen al experimento `region=NIC`, `modelo=nino34_tna_mam` de MERRA-2. El experimento independiente `region=NIC (IMERG)` del mismo modelo tiene MSESS **0.1007** y p de permutación **0.0509**. La búsqueda del experimento no distingue el producto. Se presenta una habilidad superior y una significancia que el experimento IMERG no respalda.

Corrección sugerida: seleccionar por producto, región, temporada y configuración de modelo; el ajuste sin tendencia de MERRA-2 también debe identificar su experimento correspondiente.

## 2. P2 — Una variable no disponible provoca HTTP 500

Ubicación: `backend/clima_nic/consulta.py:85–93`, acceso `r["variables"][variable]`.

Reproducción: `GET /pronostico?region=pacifico&anio=2024&variable=lluvia_jun_nov_imerg` devuelve **500 Internal Server Error**. Llamar directamente a `pronostico_estacional` reproduce `KeyError('lluvia_jun_nov_imerg')`.

La variable figura entre las admitidas por el modelo estacional, pero no está en las variables de esa región en el JSON actual. El acceso directo omite la validación y `_seguro` no captura KeyError. Una combinación de parámetros de usuario no debe convertirse en error interno.

Corrección sugerida: comprobar disponibilidad de la variable en la región y responder con error de consulta 400 o `disponible:false`, según el contrato elegido.

## 3. P2 — Los meses duplicados pueden sustituir meses ausentes

Ubicación: `backend/clima_nic/fuentes/base.py:162–174`, función `a_anual`.

Reproducción mínima:

```python
meses = ['2001-01'] + [f'2001-{m:02}' for m in range(1, 12)]
a_anual(meses, [1] * 12)
# Actual: ([2001], [12.0])
```

Hay dos eneros y falta diciembre. La función solo cuenta doce valores; no comprueba los doce meses distintos. Acepta un año incompleto y calcula una suma con un mes repetido, pudiendo sesgar series anuales y tendencias.

Corrección sugerida: verificar claves año-mes únicas y la presencia exacta de los meses exigidos; rechazar duplicados y no rellenar huecos.

## 4. P2 — Se acepta un año bisiesto con un día ausente

Ubicación: `backend/clima_nic/estadistica/indicadores.py:234`, función `indices_lluvia`. La comprobación equivalente aparece en `indices_calor` en la línea 283.

Reproducción: construir las fechas diarias de 2004, eliminar `2004-07-01` y asignar 2 mm/día a los 365 días restantes. `indices_lluvia` acepta 2004 y devuelve PRCPTOT **730 mm** y CWD **365 días**. La función declara trabajar solo con años completos, pero 2004 necesita 366 días.

Además, comprueba el número de registros sin verificar continuidad ni unicidad: una fecha repetida puede ocultar otra ausente, y una racha puede atravesar un hueco temporal.

Corrección sugerida: contrastar fechas únicas con el calendario esperado de cada año antes de calcular totales y rachas; aplicar la validación a lluvia y calor.

## 5. P2 — Una referencia histórica de lluvia cero rompe los escenarios

Ubicación: `backend/clima_nic/proyecciones.py:77` y `:84`.

Reproducción sintética: un modelo con los doce meses históricos iguales a 0 y doce meses futuros iguales a 1, observado histórico igual a 0. `escenarios(..., variable='pr')` lanza **ZeroDivisionError: float division by zero** en `cf/ch`. Si el modelo histórico es positivo pero la referencia observada es cero, la segunda división `ch/obs` también necesita protección.

El cero es finito, por lo que supera la validación existente. En vez de declarar indefinido el cambio relativo o excluir el modelo con un motivo, se interrumpe el cálculo.

Corrección sugerida: validar denominadores antes de calcular cambios porcentuales y sesgos, y publicar el motivo de indisponibilidad sin fabricar porcentajes.

## Verificación ejecutada

```text
python -m pytest tests/test_backend_clima_nic.py tests/test_indicadores_nicaragua.py -q
54 passed, 1 warning in 11.18s
```

La advertencia es una deprecación de Starlette/TestClient con httpx. Las cinco reproducciones anteriores comprueban casos que estas pruebas no detectan. Los hallazgos 1 y 2 usan el JSON real del proyecto; los hallazgos 3–5 usan entradas sintéticas controladas. No se afirma que los datos publicados tengan meses duplicados, días ausentes o climatologías de lluvia cero.

Prioridad propuesta: corregir primero la atribución de habilidad y el error HTTP 500; después reforzar la integridad temporal y los denominadores de las proyecciones. Esta entrega es una auditoría, sin cambios de implementación ni PR nuevo.
