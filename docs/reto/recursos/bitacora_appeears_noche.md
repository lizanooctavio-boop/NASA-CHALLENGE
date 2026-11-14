# Bitácora nocturna de AppEEARS

Horarios de Managua (UTC−06:00), 14 de noviembre de 2026. Rama `codex/herramientas-nasa`, PR #16. AppEEARS es el recurso n.º 3 del catálogo y el último que falta para alcanzar 13 de 13.

## 01:00 · Inicio y fase 1

- Rama limpia en `7ee9ea4`. Detectado el proceso Python 45096, iniciado a las 00:56 con `procesar-terminadas`. Se respeta esa descarga y su caché. Los cuatro JSON de salida todavía no existen.
- Primer bundle de Nicaragua (SMAP L4 v008, 2015) con 8.837 entradas de nombres únicos. A las 01:00, su carpeta contenía 7.425 archivos en total, incluido el manifiesto. El recuento de integridad por tamaño se registra en los controles siguientes.
- El encargo partía de 5 tareas terminadas, 2 en proceso y 143 pendientes. Se cotejará el estado con AppEEARS mediante consultas de lectura a los 150 IDs registrados.

## 01:07 · Primera consulta y control de rasteres

- Consulta de lectura a los 150 IDs: **5 done, 2 processing, 143 pending**. Las cinco tareas completadas son SPL4SMGP.008 para NIC (2015–2019). Los detalles de tarea no traen fecha de caducidad. El encargo registra 13–14 de diciembre de 2026; se conserva como fecha de referencia mientras no se pueda cotejar con el servicio.
- Primer bundle a las 01:06: 8.737 de 8.837 entradas con tamaño correcto, 100 faltantes, cero .parcial. El manifiesto lista 8.832 GeoTIFF y cinco archivos auxiliares.
- La muestra de 51 rasteres de fracción de nieve tiene 106.284 píxeles válidos: 5.741 ceros y 100.543 positivos por debajo de 1e−6. La exigencia nieve = 0 daba 1,36 % de área válida en el primer intervalo; con tolerancia de 1e−6 el mismo intervalo cubre 99,86 % y da 0,21783 m³/m³. Se mantiene la exclusión de suelo helado y de rellenos negativos. La tolerancia se basa en los rasteres examinados; se conserva el carácter físico del filtro de [SMAP L4 v008](https://nsidc.org/data/spl4smgp/versions/8).
- El Python global del proceso existente no tiene rasterio. Se preparó un entorno temporal con las dependencias del repo; al quedar libre la descarga se ejecutará el mismo comando con ese entorno para recuperar el recorte de ser necesario.
- Se preparó la auditoría reproducible, con comparación mensual de las dos capas superficiales y pendientes descriptivas de años completos comunes. La vista toma la serie mensual, limita la indicación de fechas a meses válidos y muestra el estado de validación en inglés.

## 01:10 · Primer bundle completo

- 2015: 8.837/8.837 archivos por tamaño, 8.832 GeoTIFF y cero .parcial. La descarga existente ya pasó a 2016: 610/11.717 entradas a las 01:10, cero .parcial.
- Recorte de control en memoria sobre 2015 con el filtro corregido: 2.208 valores superficiales válidos de 2.208 intervalos y 2.208 de zona radicular. Abril–diciembre dan nueve medias superficiales. Marzo solo incluye el día 31 y queda nulo por el mínimo mensual del 90 %.
- Base `7ee9ea4` verificada en clon nuevo: 197 pruebas y 130 subpruebas correctas, incluidas las de Chromium. En el directorio original, el archivo de GLDAS anual todavía tiene CRLF pese a su atributo LF. El clon nuevo materializa LF, así que será la fuente para regenerar y verificar huellas.

## 01:13 · Ensayo de integración con el bundle de 2015

- En el clon temporal, la serie superficial real pasó 198 pruebas y 131 subpruebas, incluido Chromium. La prueba de extremo a extremo comprobó fechas válidas, estado en inglés, CSV y fuente activa. Este ensayo usó exclusivamente 2015 y no se publicó.
- El control de 2015 da 0,1881–0,3751 m³/m³ para medias mensuales, r = 0,899 y una diferencia media SMAP − GLDAS de +0,0454 m³/m³ en nueve pares. El periodo incompleto deja solo tres meses de noviembre–abril, por lo que ese ensayo no caracteriza la estacionalidad interanual.
- Durante la interrupción del radiómetro del 19 de junio al 23 de julio de 2019, SPL4SMGP sigue disponible y se apoya principalmente en el modelo de tierra. Se conservarán esos valores L4 y se consignará la salvedad. [Guía oficial de SMAP L4 v008](https://nsidc.org/data/documentation/smap-l4-global-9-km-ease-grid-surface-and-root-zone-soil-moisture-version-8-user-guide).

## 01:16 · Revisión de la vista

- En Chrome local se recorrió **Investigate → Water bodies → Nicaragua → Surface soil moisture (SMAP)**. Se comprobó la gráfica con nueve puntos y el inicio sin dato en marzo, la unidad m³/m³, el periodo, el estado y el acceso al CSV. La gráfica ahora fija el formato decimal inglés para el registro SMAP.
- La descarga sigue en el PID 45096. A las 01:15, 2016 llevaba 1.855/11.717 entradas y 2015 seguía íntegro. Se dejó un observador local de solo lectura que guarda recuentos de integridad cada 10 minutos.

## 01:21 · Control de descarga

- PID 45096 activo. 2015: 8.837/8.837 archivos. 2016: 3.021/11.717 archivos. Cero .parcial en ambas carpetas. Las cifras refieren a archivos del manifiesto y tamaño comprobado.
- La suite de la vista de control volvió a pasar tras ajustar el formato decimal (198 pruebas y 131 subpruebas).

## 01:25 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 4.085/11717 archivos correctos. 4.085 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 01:26 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 4.303/11717 archivos correctos. 4.303 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 01:29 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 4.900/11.717 archivos correctos. 4.900 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 01:39 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 7.167/11.717 archivos correctos. 7.167 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 01:49 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 9.438/11.717 archivos correctos. 9.438 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 01:59 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.690/11.717 archivos correctos. 11.690 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 02:10 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 2.211/11.685 archivos correctos. 2.211 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 02:20 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 4.516/11.685 archivos correctos. 4.516 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 02:30 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 6.758/11.685 archivos correctos. 6.758 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 02:40 · Control de descarga

- Proceso activo: 45096.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 9.014/11.685 archivos correctos. 9.014 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 02:53 · Fase 1 · Reanudación

- Ejecución 1/6, código de salida 1.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.320/11.685 archivos correctos. 11.320 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 02:58 · Recuperación de red

- El proceso original terminó y el primer intento con el entorno temporal registró `WinError 10054` (conexión cerrada por el servidor), salida 1. La espera de 15 minutos quedó activa para los reintentos del control.
- A las 02:57 se comprobó otra instancia externa, PID 38548, iniciada a las 02:53. Se respeta como única descarga activa. 2017 ya está íntegro (11.685/11.685), y 2018 tiene 515/11.685 según su manifiesto. Ninguna carpeta cotejada tenía .parcial.
- Las pruebas de carga comprueban que un mes ausente se muestra como un hueco en la gráfica.

## 03:07 · Control científico de los tres primeros bundles

- Ensayo de solo lectura en clon temporal con 2015–2017. Resultado: 33 medias mensuales (abril de 2015 a diciembre de 2017), rango 0,1804–0,4227 m³/m³, media 0,3445 en mayo–octubre y 0,3045 en noviembre–abril. Los 33 pares GLDAS dan r = 0,9276 y +0,0584 m³/m³ de diferencia media SMAP − GLDAS. Son cifras provisionales.
- Continúa la descarga de los dos años restantes. Se aplicará la misma auditoría al conjunto completo antes de integrar.

## 03:10 · Fase 1 · Reanudación

- Ejecución 2/6, código de salida 4294967295.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 2.784/11.685 archivos correctos. 2.784 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 03:10 · Descarga única restablecida

- El proceso externo 38548 salió durante 2018. Cumplidos los 15 minutos desde la falla de red, el control lanzó un reintento a las 03:08:05. Un proceso de otro controlador arrancó a las 03:08:13, después de la comprobación previa. Al detectar el cruce se detuvo el proceso propio (43384/42868) y se verificó que quedó una sola descarga (8220). La caché se conserva y se cotejarán tamaños y .parcial antes del recorte.

## 03:29 · Fase 1 · Reanudación

- Ejecución 3/6, código de salida 4294967295.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 6.178/11.685 archivos correctos. 6.178 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 03:30 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 35544.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 6.413/11.685 archivos correctos. 6.413 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 03:30 · Seguimiento del controlador externo

- El controlador externo 38552 reinicia su descarga incluso entre dos comprobaciones de procesos Python. Al detectar un segundo cruce se detuvo la instancia propia y quedó 35544. A partir de este punto la comprobación incluye también al controlador padre 38552; durante sus esperas tampoco se lanza una descarga propia. La descarga de 2018 lleva más de 6.100 entradas verificadas.

## 03:40 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 46920.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 8.237/11.685 archivos correctos. 8.237 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 03:50 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 47656.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 10.025/11.685 archivos correctos. 10.025 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 0/sin manifiesto archivos correctos. 0 GeoTIFF. 0 .parcial.

## 04:00 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 4216.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 47/11.685 archivos correctos. 47 GeoTIFF. 0 .parcial.

## 04:11 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 23708.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 1.863/11.685 archivos correctos. 1.863 GeoTIFF. 0 .parcial.

## 04:21 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 23708.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 4.141/11.685 archivos correctos. 4.141 GeoTIFF. 0 .parcial.

## 04:31 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 23708.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 6.457/11.685 archivos correctos. 6.457 GeoTIFF. 0 .parcial.

## 04:41 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 23708.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 8.696/11.685 archivos correctos. 8.696 GeoTIFF. 0 .parcial.

## 04:52 · Control de descarga

- Procesos de descarga o su controlador: 38552 / 23708.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 11.020/11.685 archivos correctos. 11.020 GeoTIFF. 0 .parcial.

## 04:57 · Control de descarga

- Procesos de descarga o su controlador: 38552.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.

## 04:57 · Fase 1 · Bundles completos

- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- Recorte local desde manifiestos cotejados, sin volver a solicitar archivos completos.

## 05:00 · Estado de cola al terminar la descarga

- Consulta completa de los 150 IDs vía GET de tarea: 5 done, 2 processing y 143 pending. Los cinco IDs terminados coinciden con los bundles verificados y no hay otro bundle listo. La consulta no devuelve fecha de expiración.

## 05:15 · Fase 2 · Validación SMAP

- Comparación de meses comunes en m³/m³. Medias anuales con los 12 meses comunes. Las anomalías se calculan respecto de la media del mismo mes de calendario en la ventana común.
- NIC · SPL4SMGP.008 · 2015-03-31–2015-12-31: 8.837/8.837 archivos correctos. 8.832 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2016-01-01–2016-12-31: 11.717/11.717 archivos correctos. 11.712 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2017-01-01–2017-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2018-01-01–2018-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC · SPL4SMGP.008 · 2019-01-01–2019-12-31: 11.685/11.685 archivos correctos. 11.680 GeoTIFF. 0 .parcial.
- NIC: 57 meses válidos (2015-04 a 2019-12). Rango mensual 0,1804–0,4227 m³/m³, rango de medias regionales de 3 h 0,1532–0,4601 m³/m³. Mayo–octubre: 0,3394 (30 meses). Noviembre–abril: 0,2991 (27 meses).
- NIC 2015-03: 8/248 intervalos válidos, 8 presentes. El producto comenzó el 31 de marzo.
- GLDAS regional 0–10 cm frente a SMAP 0–5 cm en NIC: 57 pares mensuales, Pearson r = 0,9183, r de anomalías respecto al mes del calendario = 0,8813 (57 pares), sesgo SMAP − GLDAS 0,0555 m³/m³. Años completos comunes: 2016, 2017, 2018, 2019. Pendientes Sen descriptivas en m³/m³ por década, SMAP y GLDAS: -0,1391 y -0,0647. Mismo signo.
- Estado NO_VALIDADA: contraste entre productos, con distintas profundidades, resoluciones y modelos. Falta observación local para validar. Las pendientes de años completos se presentan como diagnóstico descriptivo.

## 05:15 · Fase 3 · Regeneración y pruebas

- JSON regenerado sobre clon nuevo de 7ee9ea4c9c07 con entradas LF y SHA-256 por archivo.
- 13 de 13 recursos activos. Cotejo estructural de investigaciones y contrastes previos.
- Suite, incluido Chromium: 198 passed, 3 warnings, 131 subtests passed in 15.27s.

## 05:15 · Fase 2 · Punto de control

- 378e89e2706322e9d5e35ad599f759054f7176bc: 197 passed, 3 warnings, 130 subtests passed in 12.09s.
