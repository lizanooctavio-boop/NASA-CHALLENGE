"""Water extent from calibrated, terrain-corrected backscatter in dB.

Workflow inspired by CSA Synthetic_Aperture_Radar_Tutorial (MIT, 2022).
Thresholding is a demonstration, not an attribution or a climate trend.
"""
import numpy as np

PAPEL = "demostracion_registro_corto"


def potencia_a_db(power):
    """10 log10 of calibrated power. Zero/negative/nonfinite are not water."""
    x = np.asarray(power, dtype=float)
    out = np.full(x.shape, np.nan)
    np.log10(x, out=out, where=np.isfinite(x) & (x > 0))
    return 10 * out


def mascara_agua(db, valido=None, umbral_db=-17.0):
    """Return water mask; no-data must not become water. Threshold is site-specific."""
    x = np.asarray(db, dtype=float)
    if not np.isfinite(umbral_db):
        raise ValueError("Threshold must be finite")
    valid = np.isfinite(x)
    if valido is not None:
        valid &= np.asarray(valido, dtype=bool)
    return valid & (x < umbral_db)


def procesar(ruta, salida_mascara, umbral_db=-17.0):
    """Equal-area EPSG:6933 raster, metres, cropped to a fixed lake/wetland AOI.

    Input must be calibrated sigma0 dB (not raw DN or linear power), with
    noise removal and terrain correction already applied in SNAP/HyP3.
    Returns observed water area and valid area; partial coverage is explicit.
    """
    import rasterio
    with rasterio.open(ruta) as src:
        if src.crs is None or src.crs.to_epsg() != 6933:
            raise ValueError("Use EPSG:6933 equal-area input in metres")
        x = src.read(1, masked=True)
        valid = ~np.ma.getmaskarray(x) & np.isfinite(x.data)
        water = mascara_agua(x.data, valid, umbral_db)
        pixel = abs(src.transform.a * src.transform.e - src.transform.b * src.transform.d)
        if pixel <= 0:
            raise ValueError("Invalid pixel area")
        profile = src.profile.copy()
        profile.update(driver="GTiff", dtype="uint8", count=1, nodata=255)
        with rasterio.open(salida_mascara, "w", **profile) as dst:
            dst.write(np.where(valid, water, 255).astype("uint8"), 1)
        return {"area_agua_km2": float(water.sum()*pixel/1e6),
                "area_valida_km2": float(valid.sum()*pixel/1e6),
                "umbral_db": umbral_db, "papel": PAPEL}


def fechas_comunes(alturas, superficies):
    """Exact calendar-day joins only; no interpolation or SWOT-area substitution."""
    return [{"fecha": d, "altura_m": alturas[d], "area_km2": superficies[d]}
            for d in sorted(alturas.keys() & superficies.keys())]
