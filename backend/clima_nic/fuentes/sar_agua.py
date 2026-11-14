"""Water extent from calibrated, terrain-corrected backscatter in dB.

Workflow inspired by CSA Synthetic_Aperture_Radar_Tutorial (MIT, 2022).
Thresholding is a demonstration, not an attribution or a climate trend.
"""
import numpy as np

PAPEL = "demostracion_registro_corto"


def caracteristicas_dualpol(vv_power, vh_power):
    """Radar-only features: VV/VH dB, ratio, and 300 m local mean/std.

    No coordinates, shoreline prior or optical labels enter the predictors.
    """
    from scipy.ndimage import uniform_filter
    vv, vh = potencia_a_db(vv_power), potencia_a_db(vh_power)
    valid = np.isfinite(vv) & np.isfinite(vh)
    weights = uniform_filter(valid.astype(float),size=3,mode='constant')
    def local(x):
        mean = np.divide(uniform_filter(np.where(valid,x,0.),3,mode='constant'),
                         weights,out=np.zeros_like(x),where=weights>0)
        second = np.divide(uniform_filter(np.where(valid,x*x,0.),3,mode='constant'),
                           weights,out=np.zeros_like(x),where=weights>0)
        return mean, np.sqrt(np.maximum(second-mean*mean,0.))
    mv, sv = local(vv)
    mh, sh = local(vh)
    features = np.stack([vv,vh,vv-vh,mv,sv,mh,sh],axis=-1).astype('float32')
    features[~valid] = 0.
    return features, valid


def potencia_a_db(power):
    """10 log10 of calibrated power. Zero/negative/nonfinite are not water."""
    x = np.asarray(power, dtype=float)
    out = np.full(x.shape, np.nan)
    np.log10(x, out=out, where=np.isfinite(x) & (x > 0))
    return 10 * out


def calibrar_umbral(db, agua, entrenamiento):
    """Fit one lower-backscatter threshold on explicitly selected training pixels.

    Optimize balanced accuracy, not an area target or the held-out score.
    Reference water is optical BWTR=1; clear reference land is BWTR=0.
    """
    x, y, train = np.asarray(db), np.asarray(agua, bool), np.asarray(entrenamiento, bool)
    train = train & np.isfinite(x)
    wet, dry = x[train & y], x[train & ~y]
    if min(len(wet), len(dry)) < 50:
        raise ValueError('At least 50 training pixels of each class are required')
    thresholds = np.linspace(-45, 10, 551)
    wet, dry = np.sort(wet), np.sort(dry)
    sensitivity = np.searchsorted(wet, thresholds, side='left') / len(wet)
    specificity = 1 - np.searchsorted(dry, thresholds, side='left') / len(dry)
    return float(thresholds[np.argmax((sensitivity + specificity)/2)])


def evaluar_mascara(pred, ref, evaluacion):
    """Confusion metrics on a held-out mask; None for undefined denominators."""
    p, r, mask = np.asarray(pred, bool), np.asarray(ref, bool), np.asarray(evaluacion, bool)
    tp, fp = int((mask&p&r).sum()), int((mask&p&~r).sum())
    tn, fn = int((mask&~p&~r).sum()), int((mask&~p&r).sum())
    ratio = lambda a,b: a/b if b else None
    return {'tp':tp,'fp':fp,'tn':tn,'fn':fn,
            'precision':ratio(tp,tp+fp),'recall_water':ratio(tp,tp+fn),
            'recall_land':ratio(tn,tn+fp),'f1':ratio(2*tp,2*tp+fp+fn)}


def superficie_publicable(metrics, cobertura_referencia):
    """Conservative screening gate, not a claim of universal validation.

    Good scores on a tiny cloud-free sample do not validate a full AOI area.
    """
    return (np.isfinite(cobertura_referencia) and cobertura_referencia >= .80 and
            all(metrics.get(k) is not None and metrics[k] >= .90
                for k in ('f1','recall_water','recall_land')))


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
