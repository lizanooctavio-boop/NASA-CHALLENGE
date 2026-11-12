"""Línea de órdenes de clima_nic. Ejecutar desde la carpeta backend/:

    python -m clima_nic fuentes                                  # catálogo y disponibilidad
    python -m clima_nic preparar-power --tierra <admin1.geojson> # descarga POWER y escribe data/fenomenos/
    python -m clima_nic preparar-cmip6                           # NEX-GDDP-CMIP6 → data/fenomenos/cmip6_mensual.csv
    python -m clima_nic preparar-gistemp                         # GISTEMP → data/fenomenos/gistemp_nicaragua.csv
    python -m clima_nic preparar-modis                           # NDVI MODIS (ORNL) → data/fenomenos/ndvi_modis.csv
    python -m clima_nic productos                                # data/fenomenos_nicaragua.json
    python -m clima_nic actualizar [--descargar]                 # ciclo de retroalimentación + historial
    python -m clima_nic consultar --region pacifico --variable lluvia_jun_nov [--desde 1981 --hasta 2024] [--anio 2025]
    python -m clima_nic api [--puerto 8000]                      # API HTTP (requiere fastapi y uvicorn)
"""
import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="clima_nic", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    sub.add_parser("fuentes")
    p = sub.add_parser("preparar-power")
    p.add_argument("--inicio", type=int, default=1981)
    p.add_argument("--fin", type=int, default=2024)
    p.add_argument("--tierra", type=Path, help="Natural Earth admin-1 (GeoJSON) para excluir tierra en los índices oceánicos")
    p = sub.add_parser("preparar-cmip6")
    p.add_argument("--hilos", type=int, default=6)
    sub.add_parser("preparar-gistemp")
    p = sub.add_parser("preparar-modis")
    p.add_argument("--hilos", type=int, default=8)
    p = sub.add_parser("productos")
    p.add_argument("--permutaciones", type=int, default=1000)
    p = sub.add_parser("actualizar")
    p.add_argument("--descargar", action="store_true")
    p.add_argument("--tierra", type=Path)
    p.add_argument("--permutaciones", type=int, default=1000)
    p = sub.add_parser("consultar")
    p.add_argument("--region", required=True)
    p.add_argument("--variable", required=True)
    p.add_argument("--desde", type=int)
    p.add_argument("--hasta", type=int)
    p.add_argument("--anio", type=int, help="año objetivo del pronóstico estacional")
    p = sub.add_parser("api")
    p.add_argument("--puerto", type=int, default=8000)
    a = ap.parse_args(argv)

    if a.orden == "fuentes":
        from .fuentes import catalogo
        print(json.dumps(catalogo(), ensure_ascii=False, indent=2))
    elif a.orden == "preparar-power":
        from .fuentes.power import Power, escribir_derivados
        print(escribir_derivados(Power(), a.inicio, a.fin, a.tierra))
    elif a.orden == "preparar-cmip6":
        from .fuentes.nex_gddp import escribir_derivados
        escribir_derivados(hilos=a.hilos)
    elif a.orden == "preparar-gistemp":
        from .fuentes.gistemp import escribir_derivados
        escribir_derivados()
    elif a.orden == "preparar-modis":
        from .fuentes.modis import escribir_derivados
        escribir_derivados(hilos=a.hilos)
    elif a.orden == "productos":
        from .productos import escribir
        escribir(a.permutaciones)
    elif a.orden == "actualizar":
        from .actualizar import actualizar
        print(json.dumps(actualizar(a.descargar, a.tierra, a.permutaciones), ensure_ascii=False, indent=2))
    elif a.orden == "consultar":
        from .consulta import consultar
        print(json.dumps(consultar(a.region, a.variable, a.desde, a.hasta, a.anio), ensure_ascii=False, indent=2))
    elif a.orden == "api":
        import uvicorn
        from .api import app
        uvicorn.run(app, host="127.0.0.1", port=a.puerto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
