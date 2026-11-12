"""Ciclo de retroalimentación: ingerir datos nuevos → recalcular → recalibrar → registrar la habilidad.

    python -m clima_nic actualizar [--descargar] [--tierra <admin1.geojson>]

1. (Opcional, --descargar) Vuelve a pedir POWER hasta el último año completo y GISTEMP; la caché evita repetir
   lo ya descargado. Los adaptadores con Earthdata se incluyen solo si hay credenciales.
2. Regenera data/fenomenos_nicaragua.json: tendencias, mapas con FDR y escenarios.
3. Recalibra el modelo estacional con todos los años disponibles (cada corrida reajusta los coeficientes y
   vuelve a validar fuera de muestra).
4. Añade una línea por experimento principal a data/historial/habilidad.csv y un registro de la corrida a
   data/historial/corridas.jsonl (fecha, SHA-256 de las entradas, años, habilidad). Así se ve si la habilidad
   se mantiene al crecer el registro, en lugar de reajustar en silencio.
"""
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .rutas import HISTORIAL


def registrar(resultado, carpeta=HISTORIAL):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    principales = resultado["modelo_estacional"]["principales"]
    ruta = carpeta / "habilidad.csv"
    nueva = not ruta.exists()
    with ruta.open("a", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        if nueva:
            w.writerow(["corrida", "region", "temporada", "modelo", "periodo", "n", "msess", "msess_bloque3", "r",
                        "aciertos_tercil", "p_permutacion"])
        for e in principales:
            w.writerow([ahora, e["region"], e["temporada"], e["modelo"], f"{e['periodo'][0]}-{e['periodo'][1]}", e["n"],
                        e["bloque_1"]["msess"], e.get("bloque_3", {}).get("msess"), e["bloque_1"]["r"],
                        e["bloque_1"]["aciertos_tercil"], e["p_permutacion_msess"]])
    previa = None
    corridas = carpeta / "corridas.jsonl"
    if corridas.exists():
        lineas = [l for l in corridas.read_text(encoding="utf-8").splitlines() if l.strip()]
        previa = json.loads(lineas[-1]) if lineas else None
    registro = {"corrida": ahora, "fecha": date.today().isoformat(),
                "entradas_sha256": resultado["metadatos"]["integridad_sha256"],
                "habilidad": {f"{e['region']}|{e['modelo']}": e["bloque_1"]["msess"] for e in principales}}
    cambios = {}
    if previa:
        for k, v in registro["habilidad"].items():
            if k in previa["habilidad"] and previa["habilidad"][k] is not None and v is not None:
                cambios[k] = round(v - previa["habilidad"][k], 4)
        registro["entradas_cambiaron"] = previa["entradas_sha256"] != registro["entradas_sha256"]
    registro["cambio_msess_vs_corrida_previa"] = cambios
    with corridas.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def actualizar(descargar=False, tierra=None, permutaciones=200, fin=None):
    pasos = []
    if descargar:
        from .fuentes.gistemp import escribir_derivados as gis
        from .fuentes.power import Power, escribir_derivados
        fin = fin or date.today().year - 1
        escribir_derivados(Power(), 1981, fin, tierra)
        pasos.append(f"POWER 1981–{fin}")
        gis()
        pasos.append("GISTEMP")
    from .productos import escribir
    resultado = escribir(permutaciones)
    pasos.append("productos y recalibración")
    registro = registrar(resultado)
    return {"pasos": pasos, "registro": registro}
