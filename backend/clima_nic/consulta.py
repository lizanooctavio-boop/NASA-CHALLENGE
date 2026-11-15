"""Consulta central: región + variable + años → tendencia, significancia, pronóstico estacional y escenarios.

Lee data/fenomenos_nicaragua.json. Si se pide un intervalo de años distinto del completo, recalcula la
tendencia sobre ese intervalo (las cifras cambian con la ventana; se informa cuál se usó).
"""
import json
from functools import lru_cache

import numpy as np

from .estadistica import modelo_estacional as me
from .estadistica import tendencia_robusta as tr
from .rutas import DATOS

ARCHIVO = DATOS / "fenomenos_nicaragua.json"
VARIABLES_ESTACIONALES = {"lluvia_jun_nov": (6, tuple(range(6, 12))), "lluvia_jun_nov_imerg": (6, tuple(range(6, 12)))}
NIVEL_RECIENTE = 15  # años: nivel de referencia cuando se quita la tendencia (series de MERRA-2)
ESCENARIO_DE = {"lluvia_anual": "lluvia_anual", "lluvia_jun_nov": "lluvia_jun_nov", "t2m_media": "t2m_media",
                "canicula_lluvia_15jul_15ago": "lluvia_jul_ago"}


class ConsultaInvalida(ValueError):
    pass


@lru_cache(maxsize=2)
def _cargar(ruta=str(ARCHIVO), _marca=None):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar():
    return _cargar(str(ARCHIVO), ARCHIVO.stat().st_mtime if ARCHIVO.exists() else None)


def regiones():
    return [{"id": r["id"], "nombre": r["nombre"]} for r in cargar()["regiones"]]


def variables(region="NIC"):
    r = _region(region)
    return [{"id": k, "titulo": v["titulo"], "unidad": v["unidad"], "fenomeno": v["fenomeno"],
             "definicion": v["definicion"], "anios": [v["anios"][0], v["anios"][-1]] if v["anios"] else None}
            for k, v in r["variables"].items()]


def _region(region):
    for r in cargar()["regiones"]:
        if r["id"] == region:
            return r
    raise ConsultaInvalida(f"Región desconocida: {region}. Opciones: {[x['id'] for x in cargar()['regiones']]}")


def tendencia(region, variable, desde=None, hasta=None):
    r = _region(region)
    if variable not in r["variables"]:
        raise ConsultaInvalida(f"Variable desconocida en {region}: {variable}")
    v = r["variables"][variable]
    anios, valores = v["anios"], v["valores"]
    if desde is not None or hasta is not None:
        pares = [(a, x) for a, x in zip(anios, valores) if (desde is None or a >= desde) and (hasta is None or a <= hasta)]
        if len(pares) < 10:
            raise ConsultaInvalida("Se necesitan al menos 10 años para estimar una tendencia.")
        anios, valores = [p[0] for p in pares], [p[1] for p in pares]
        t = tr.analizar(anios, valores, v["unidad"])
    else:
        t = v["tendencia"]
    sen = t.get("theil_sen", {})
    mmk = t.get("mann_kendall_modificado", {})
    return {
        "region": region, "variable": variable, "titulo": v["titulo"], "definicion": v["definicion"],
        "unidad": v["unidad"], "periodo": [anios[0], anios[-1]], "anios": anios, "valores": valores,
        "que": v["titulo"], "donde": r["nombre"],
        "cuanto": {"sen_por_decada": sen.get("por_decada"), "ic95": sen.get("ic_por_decada"),
                   "minimos_cuadrados_por_decada": t.get("minimos_cuadrados", {}).get("por_decada"),
                   "unidad": f"{v['unidad']}/década"},
        "significativo": {"veredicto": t.get("veredicto"), "mann_kendall_modificado_p": mmk.get("p_valor"),
                          "pettitt": t.get("pettitt"), "control_enos": t.get("controlada_por_indices")},
        "advertencias": v.get("advertencias", []),
        "tipo": "deteccion_de_tendencia",
    }


def pronostico_estacional(region, anio, variable="lluvia_jun_nov"):
    """Valor esperado de la lluvia de junio–noviembre de `anio` con Niño 3.4 y TNA de marzo–mayo de ese año.
    Solo si esos predictores ya existen en los datos; nunca extrapola años sin predictores."""
    if variable not in VARIABLES_ESTACIONALES:
        return {"disponible": False, "motivo": f"Sin modelo estacional para {variable} (solo {list(VARIABLES_ESTACIONALES)})."}
    d = cargar()
    r = _region(region)
    if variable not in r["variables"]:
        return {"disponible": False, "motivo": f"Sin datos de {variable} para la región {region}."}
    v = r["variables"][variable]
    idx = d["indices_climaticos"]["mensual"]
    mensual = {k: {(a, m): x for a, m, x in zip(idx["anios"], idx["meses"], idx[k]) if x is not None}
               for k in ("nino34", "tna")}
    inicio, _ = VARIABLES_ESTACIONALES[variable]
    preds = {k: me.serie_predictor(mensual[k], list(v["anios"]) + [anio], inicio, 0) for k in mensual}
    valores_por_anio = {a: val for a, val in zip(v["anios"], v["valores"]) if val is not None}
    entrenamiento = [a for a in v["anios"] if a != anio and a in valores_por_anio and all(a in p for p in preds.values())]
    if not all(anio in p for p in preds.values()):
        return {"disponible": False, "anio": anio,
                "motivo": (f"Aún no hay Niño 3.4 y TNA de marzo–mayo de {anio} en los datos. Ejecute "
                           "`python -m clima_nic actualizar --descargar` cuando estén publicados.")}
    y = np.array([valores_por_anio[a] for a in entrenamiento], float)
    X = np.array([[preds["nino34"][a], preds["tna"][a]] for a in entrenamiento])
    x_nuevo = np.array([preds["nino34"][anio], preds["tna"][anio]])
    sin_tendencia = not variable.endswith("_imerg")
    if sin_tendencia:
        # MERRA-2 tiene un salto artificial en la lluvia (ver advertencias): se ajusta sobre anomalías sin tendencia
        # (predictores y predictando) y se suma el nivel medio de los últimos años del entrenamiento.
        t = np.array(entrenamiento, float)
        A = np.column_stack([np.ones(len(t)), t - t.mean()])
        coef_y = np.linalg.lstsq(A, y, rcond=None)[0]
        coef_x = np.linalg.lstsq(A, X, rcond=None)[0]
        nivel = float(np.mean(y[-NIVEL_RECIENTE:]))
        ya = y - A @ coef_y
        Xa = X - A @ coef_x
        xa = x_nuevo - np.array([1.0, anio - t.mean()]) @ coef_x
        p = me.pronostico(ya + nivel, Xa, xa)
    else:
        p = me.pronostico(y, X, x_nuevo)
    observado = v["valores"][v["anios"].index(anio)] if anio in v["anios"] else None
    clave_region = f"{region} (IMERG)" if variable.endswith("_imerg") else region
    principal = next((e for e in d["modelo_estacional"]["principales"]
                      if e["region"] == clave_region and e["modelo"] == "nino34_tna_mam"), None)
    return {"disponible": True, "tipo": "pronostico_estacional", "anio": anio, "region": region, "variable": variable,
            "unidad": v["unidad"], "predictores": {"nino34_mam": preds["nino34"][anio], "tna_mam": preds["tna"][anio]},
            **p, "observado": observado,
            "producto": "IMERG" if not sin_tendencia else "MERRA-2 (POWER), ajustado sin tendencia sobre el nivel de los últimos 15 años",
            "habilidad_publicada": principal and {"msess": principal["bloque_1"]["msess"],
                                                  "p_permutacion": principal["p_permutacion_msess"]},
            "nota": ("Retrospectivo si el año ya se observó (el año se excluye del ajuste). Es un valor esperado con "
                     "intervalo del 80 % y probabilidades de tercil, no una cifra exacta.")}


def escenarios(region, variable):
    clave = ESCENARIO_DE.get(variable)
    e = cargar().get("escenarios_cmip6", {}).get(region, {})
    if not clave or clave not in e:
        return {"disponible": False, "motivo": f"Sin escenarios CMIP6 para {variable} en {region}."}
    return {"disponible": True, "tipo": "escenarios_no_pronostico", **e[clave]}


def consultar(region, variable, desde=None, hasta=None, anio=None):
    out = {"tendencia": tendencia(region, variable, desde, hasta)}
    if anio is not None:
        out["pronostico_estacional"] = pronostico_estacional(region, anio, variable)
    out["escenarios"] = escenarios(region, variable)
    out["aviso"] = ("Tres productos distintos: la tendencia describe el pasado; el pronóstico estacional da un valor "
                    "esperado con incertidumbre para una temporada; los escenarios son rangos de modelos para promedios "
                    "de 20 años. Ninguno es un pronóstico determinista de un año futuro.")
    return _limpio(out)


def _limpio(v):
    if isinstance(v, dict):
        return {k: _limpio(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_limpio(x) for x in v]
    if isinstance(v, (np.floating, float)):
        return None if not np.isfinite(v) else round(float(v), 4)
    if isinstance(v, np.integer):
        return int(v)
    return v
