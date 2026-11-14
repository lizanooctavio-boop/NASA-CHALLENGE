"""API HTTP mínima (FastAPI). Solo lectura, sin credenciales; CORS abierto para la interfaz estática.

    pip install fastapi uvicorn
    python -m clima_nic api --puerto 8000

Rutas (todas GET, JSON):
    /salud
    /fuentes                                   catálogo de adaptadores y disponibilidad
    /regiones                                  ids y nombres
    /variables?region=NIC                      variables con definición sencilla
    /tendencia?region=&variable=&desde=&hasta= qué/dónde/cuánto/significativo
    /pronostico?region=&anio=                  lluvia jun–nov esperada con intervalo y terciles
    /escenarios?region=&variable=              rango CMIP6 por escenario
    /consulta?region=&variable=&desde=&hasta=&anio=   todo junto
    /mapa?variable=prcptot                     celdas MERRA-2 con FDR: demostración del método, no tendencias
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import consulta as c

app = FastAPI(title="clima_nic", version="0.1.0",
              description="Tendencias, pronóstico estacional y escenarios del clima de Nicaragua con datos NASA.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def _seguro(fn, *a):
    try:
        return fn(*a)
    except c.ConsultaInvalida as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail="Falta data/fenomenos_nicaragua.json: ejecute `python -m clima_nic productos`.") from e


@app.get("/salud")
def salud():
    return {"estado": "ok", "datos": c.ARCHIVO.exists()}


@app.get("/fuentes")
def fuentes():
    from .fuentes import catalogo
    return catalogo()


@app.get("/regiones")
def regiones():
    return _seguro(c.regiones)


@app.get("/variables")
def variables(region: str = "NIC"):
    return _seguro(c.variables, region)


@app.get("/tendencia")
def tendencia(region: str, variable: str, desde: int | None = None, hasta: int | None = None):
    return c._limpio(_seguro(c.tendencia, region, variable, desde, hasta))


@app.get("/pronostico")
def pronostico(region: str, anio: int, variable: str = "lluvia_jun_nov"):
    return c._limpio(_seguro(c.pronostico_estacional, region, anio, variable))


@app.get("/escenarios")
def escenarios(region: str, variable: str):
    return c._limpio(_seguro(c.escenarios, region, variable))


@app.get("/consulta")
def consulta(region: str, variable: str, desde: int | None = None, hasta: int | None = None, anio: int | None = None):
    return _seguro(c.consultar, region, variable, desde, hasta, anio)


@app.get("/mapa")
def mapa(variable: str = "prcptot"):
    # La respuesta lleva fuente, uso («demostracion_metodo») y advertencias: no son tendencias por celda.
    m = _seguro(c.cargar)["mapas_tendencia"]
    if variable not in m:
        raise HTTPException(status_code=400, detail=f"Opciones: {list(m)}")
    return m[variable]
