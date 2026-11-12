"""Sensibilidad de las pendientes al contorno de los países (opcional: requiere los HDF5).

Recalcula las series con cada país dilatado y erosionado en ±DELTA grados (0,05° ≈ 5,5 km) y escribe
data/fuentes/sensibilidad_geometria.json. Uso:
    python scripts/datos/sensibilidad_geometria.py --hdf5 <carpeta con los 288 .HDF5>
"""
import argparse
import json
from pathlib import Path

import numpy as np

import tendencia
from comun import ANIOS, DATOS, PAISES
from extraer_series import CAJA_6933, cargar_geometrias, leer

DELTA = 0.05


def resumen(series, k):
    anual, _ = tendencia.agregar_anual([(a, m, mm) for a, m, mm, _ in series[k]])
    t = tendencia.analizar_tendencia(anual, anual.values())
    return {"mm_por_decada": t["mm_por_decada"], "ic_mm_por_decada": t["ic_mm_por_decada"],
            "veredicto": t["veredicto"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hdf5", required=True, type=Path)
    a = ap.parse_args()
    base = cargar_geometrias(DATOS / "dominios.geojson")
    resultado = {"delta_grados": DELTA, "escenarios": {}}
    for nombre, d in [("referencia", 0.0), ("dilatado", DELTA), ("erosionado", -DELTA)]:
        geoms = dict(base)
        for k in PAISES:
            geoms[k] = base[k].buffer(d) if d else base[k]
        geoms["NIC_fuera_caja"] = geoms["NIC"].difference(base["caja_sicc"])
        _, series, celdas = leer(a.hdf5, geoms)
        resultado["escenarios"][nombre] = {k: resumen(series, k) for k in (*PAISES, "NIC_fuera_caja")}
        print(nombre, {k: v["mm_por_decada"] for k, v in resultado["escenarios"][nombre].items()})
    destino = DATOS / "fuentes" / "sensibilidad_geometria.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destino)
