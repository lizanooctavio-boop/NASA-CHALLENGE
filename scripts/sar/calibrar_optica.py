"""Independent optical DSWx-HLS reference, calibration and spatial holdout.

Max optical offset 2 days, nearest clear observation per pixel; BWTR 0/1 only.
Five-km stripes separate training/test, with intervening unused stripes.
No tuning is performed on the held-out scores. No clouds are called dry land.
"""
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
import earthaccess
import requests
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import geometry_mask
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from clima_nic.fuentes.sar_agua import potencia_a_db, calibrar_umbral, evaluar_mascara, superficie_publicable


def main():
    earthaccess.login(strategy='netrc')
    session = earthaccess.get_requests_https_session()
    cache = ROOT.parent/'optical_validation'
    cache.mkdir(exist_ok=True)
    dates = ['2024-03-04','2024-04-21','2024-07-14']
    out = ROOT/'data/recursos/csa'
    with rasterio.open(ROOT.parent/'opera_rtc/gamma0_power_2024-03-04.tif') as first:
        profile, affine, crs = first.profile, first.transform, first.crs
        size = first.shape
    col = np.arange(size[1])[None,:]
    # 100 m grid: 50 columns = 5 km; unused stripes separate train/test.
    train_stripe = ((col//50)%4 == 0)
    test_stripe = ((col//50)%4 == 2)
    masks, powers, manifests, reports = [], [], [], []
    project = Transformer.from_crs(4326,6933,always_xy=True).transform
    domains = json.loads((out/'sar_dominios.geojson').read_text())['features']
    geometries = {f['properties']['id']:geometry_mask([mapping(transform(project,shape(f['geometry'])))],
                    out_shape=size,transform=affine,invert=True) for f in domains}
    for date in dates:
        day = dt.date.fromisoformat(date)
        r = requests.get('https://cmr.earthdata.nasa.gov/search/granules.json',params={
            'short_name':'OPERA_L3_DSWX-HLS_V1','page_size':100,
            'bounding_box':'-85.95,10.7,-84.4,12.3',
            'temporal':f'{day-dt.timedelta(days=2)}T00:00:00Z,{day+dt.timedelta(days=2)}T23:59:59Z'},timeout=60)
        r.raise_for_status()
        entries = r.json()['feed']['entry']
        rank = lambda e: (abs((dt.date.fromisoformat(e['time_start'][:10])-day).days),float(e.get('cloud_cover') or 100))
        entries.sort(key=rank)
        # Closest clear observation per pixel: do not discard another date's
        # clear pixels just because the nearest tile is cloudy at that location.
        selected = entries
        optical = np.full(size,255,dtype='uint8')
        for e in selected:
            url = next(l['href'] for l in e['links'] if l['href'].startswith('https://') and l['href'].endswith('_B02_BWTR.tif'))
            path = cache/url.rsplit('/',1)[-1]
            if not path.exists():
                r = session.get(url,timeout=90)
                r.raise_for_status()
                path.write_bytes(r.content)
            with rasterio.open(path) as src:
                target=np.full(size,255,dtype='uint8')
                reproject(src.read(1),target,src_transform=src.transform,src_crs=src.crs,
                    src_nodata=255,dst_transform=affine,dst_crs=crs,dst_nodata=255,resampling=Resampling.nearest)
                # Valid optical classification supersedes cloud/no-data at tile overlap.
                use = ((target==0)|(target==1)) & ~((optical==0)|(optical==1))
                optical[use] = target[use]
            manifests.append({'radar_date':date,'optical_time_utc':e['time_start'],
                'offset_days':rank(e)[0], 'product_id':e['title'],'url':url,
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        with rasterio.open(ROOT.parent/f'opera_rtc/gamma0_power_{date}.tif') as src:
            power=np.full(size,np.nan,dtype='float32')
            reproject(src.read(1),power,src_transform=src.transform,src_crs=src.crs,src_nodata=np.nan,
                dst_transform=affine,dst_crs=crs,dst_nodata=np.nan,resampling=Resampling.average)
        valid = np.isfinite(power)&(power>0)&((optical==0)|(optical==1))
        db = potencia_a_db(power)
        wet = optical==1
        threshold = calibrar_umbral(db,wet,valid&train_stripe)
        metrics = evaluar_mascara(db<threshold,wet,valid&test_stripe)
        original = evaluar_mascara(db < -17,wet,valid&test_stripe)
        # Explicit pre-specified gate; failing results remain candidates.
        passed = all(metrics[k] is not None and metrics[k]>=.90 for k in ['f1','recall_water','recall_land'])
        reports.append({'date':date,'threshold_db':threshold,'test_metrics':metrics,
            'baseline_minus17_test_metrics':original,'quality_gate_passed':passed,
            'reference_valid_pixels':int(valid.sum()),
            'train_pixels':int((valid&train_stripe).sum()),'test_pixels':int((valid&test_stripe).sum())})
        masks.append(optical)
        powers.append(power)
        with rasterio.open(cache/f'optical_reference_{date}.tif','w',**{**profile,'dtype':'uint8','nodata':255}) as dst:
            dst.write(optical,1)
        print(date,threshold,metrics,'passed',passed,flush=True)
    common=np.logical_and.reduce([np.isfinite(p)&(p>0) for p in powers])
    common_optical = common & np.logical_and.reduce([(m==0)|(m==1) for m in masks])
    rows=[]
    for date,power,report,optical in zip(dates,powers,reports,masks):
        prediction=potencia_a_db(power)<report['threshold_db']
        for name,domain in geometries.items():
            mask=domain&common
            reference_mask=domain&common_optical
            reference_fraction = float(reference_mask.sum()/mask.sum()) if mask.any() else 0.
            publishable = superficie_publicable(report['test_metrics'],reference_fraction)
            candidate = float((mask&prediction).sum()*.01)
            rows.append({'date':date,'domain':name,'threshold_db':report['threshold_db'],
                'area_candidate_km2':candidate,
                'area_common_radar_km2':float(mask.sum()*.01),
                'area_common_clear_reference_km2':float(reference_mask.sum()*.01),
                'area_optical_water_common_clear_km2':float((reference_mask&(optical==1)).sum()*.01),
                'area_radar_water_common_clear_km2':float((reference_mask&prediction).sum()*.01),
                'classifier_test_gate_passed':report['quality_gate_passed'],
                'reference_common_coverage_fraction':reference_fraction,
                'surface_quality_gate_passed':publishable,
                'area_water_validated_km2':candidate if publishable else 'NO_VALIDADA',
                'estado_superficie':'controles_superados' if publishable else 'estimacion_no_validada',
                'motivo_no_validacion':'no_aplica' if publishable else 'metricas_insuficientes_o_referencia_comun_menor_80pct',
                'papel':'demostracion_registro_corto'})
    (out/'sar_validacion_optica.json').write_text(json.dumps({
        'reference':'OPERA_L3_DSWX-HLS_V1 B02_BWTR; clear 0=land,1=water only',
        'reference_status':'provisional collection; independent optical product, not field truth',
        'maximum_optical_offset_days':2,'optical_composite':'nearest clear observation per pixel within +/-2 days',
        'spatial_split':'5 km column stripes: train 0 mod4, test2 mod4; 1/3 unused',
        'calibration_objective':'training balanced accuracy; no threshold tuning on test metrics',
        'quality_gate':'held-out F1, water recall and land recall all >=0.90',
        'surface_publication_gate':'classifier gate AND >=80% common clear optical reference coverage in AOI; necessary screening only',
        'reports':reports,'granules':manifests},indent=2),encoding='utf-8')
    with (out/'sar_superficie_calibrada.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)


if __name__=='__main__':main()
