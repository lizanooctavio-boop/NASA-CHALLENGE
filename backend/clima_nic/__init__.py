"""clima_nic: backend de detección de tendencias y predicción honesta del clima de Nicaragua con datos NASA.

Responde las cuatro preguntas del reto «Earth System Trend Detective» (NASA Space Apps 2026):
qué cambia (variable), dónde (región), cuánto (pendiente de Sen por década) y si es significativo
(Mann–Kendall modificado, intervalos de confianza, FDR en mapas).

Módulos:
    rutas          rutas del repositorio, de los datos derivados y de la caché local (fuera de git)
    regiones       polígonos de NIC, Pacífico, Central (con Corredor Seco), Caribe y caja SICC; pesos de malla
    fuentes        registro de adaptadores, uno por dataset NASA (POWER, IMERG, MERRA-2, MODIS, SMAP,
                   GRACE-FO, GISTEMP, NEX-GDDP-CMIP6)
    estadistica    indicadores (SPI, SPEI, ETCCDI, canícula), tendencias robustas, FDR, modelo estacional
    agro           ETo FAO-56 Penman–Monteith y Hargreaves, balance hídrico, grados-día
    proyecciones   corrección de sesgo por método delta y rango de escenarios CMIP6
    productos      genera data/fenomenos_nicaragua.json
    actualizar     ingiere datos nuevos, recalcula, recalibra y registra la habilidad (historial)
    consulta       función central: región + variable + años → tendencia, pronóstico estacional, escenarios
    api            API HTTP opcional (FastAPI)
"""
__version__ = "0.1.0"
