"""Une las series regionales mensuales de NEX-GDDP-CMIP6 para el expediente por área.

Entradas: data/fenomenos/cmip6_mensual.csv (histórico 1995–2014 y 2041–2060, ya en el repositorio) y, si se
pasan, otros CSV con el mismo formato (p. ej. la descarga 2015–2040 de clima_nic.fuentes.nex_gddp con
escenarios={"ssp245": (2015, 2040), "ssp585": (2015, 2040)}).
Salida: data/expediente/cmip6_regional_mensual.csv (valores a 3 decimales, sin duplicados) y
data/expediente/cmip6_regional.json (procedencia: modelos, escenarios, años, SHA-256 de las entradas).

Uso: python scripts/expediente/preparar_cmip6.py [otro.csv ...]
"""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "data" / "fenomenos" / "cmip6_mensual.csv"
SALIDA = RAIZ / "data" / "expediente"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(extra):
    filas, entradas = {}, []
    for ruta in [BASE, *map(Path, extra)]:
        entradas.append({"archivo": ruta.name, "sha256": sha(ruta)})
        with ruta.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                clave = (r["modelo"], r["escenario"], r["variable"], r["region"], int(r["anio"]), int(r["mes"]))
                filas[clave] = (r["miembro"], float(r["valor"]))
    SALIDA.mkdir(parents=True, exist_ok=True)
    with (SALIDA / "cmip6_regional_mensual.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["modelo", "miembro", "escenario", "variable", "region", "anio", "mes", "valor"])
        for k in sorted(filas):
            mi, v = filas[k]
            w.writerow([k[0], mi, k[1], k[2], k[3], k[4], k[5], f"{v:.3f}"])
    anios = {}
    for (mo, esc, var, reg, a, m) in filas:
        anios.setdefault(esc, set()).add(a)
    meta = {
        "fuente": "NASA NEX-GDDP-CMIP6 v2.0 (NCCS THREDDS/NCSS), medias regionales ponderadas por superficie (solo tierra)",
        "doi_producto": "10.1038/s41597-022-01393-4",
        "modelos": sorted({k[0] for k in filas}),
        "escenarios": {e: [min(a), max(a)] for e, a in sorted(anios.items())},
        "anios_por_escenario": {e: len(a) for e, a in sorted(anios.items())},
        "variables": {"pr": "mm/mes", "tas": "°C"},
        "regiones": sorted({k[3] for k in filas}),
        "entradas": entradas,
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "uso": "escenarios condicionados a forzamiento; la dispersión entre modelos no es un intervalo de confianza",
    }
    (SALIDA / "cmip6_regional.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(len(filas), "filas;", meta["escenarios"])


if __name__ == "__main__":
    main(sys.argv[1:])
