"""Real ASF OPERA RTC-S1 demonstration on fixed observed domains, not a trend.

Uses VV gamma0 power (not sigma0); average to 100 m in EPSG:6933 before dB.
Requires prior Earthdata/ASF authorization. Originals stay outside Git.
"""
import csv
import hashlib
import json
import netrc
import sys
from pathlib import Path
import numpy as np
import requests
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling, calculate_default_transform
from rasterio.features import geometry_mask
from shapely.geometry import shape, box, mapping
from shapely.ops import transform
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
from clima_nic.fuentes.earthdata import ruta_netrc
from clima_nic.fuentes.sar_agua import potencia_a_db
import asf_search as asf


def main():
    cache = ROOT.parent/'opera_rtc'
    cache.mkdir(exist_ok=True)
    user, _, password = netrc.netrc(str(ruta_netrc())).authenticators('urs.earthdata.nasa.gov')
    session = asf.ASFSession().auth_with_creds(user, password)
    dates = ['2024-03-04','2024-04-21','2024-07-14']
    manifests, datasets = [], []
    for date in dates:
        r = requests.get('https://cmr.earthdata.nasa.gov/search/granules.json', params={
            'short_name':'OPERA_L2_RTC-S1_V1','page_size':200,
            'bounding_box':'-85.95,10.7,-84.4,12.3',
            'temporal':f'{date}T00:00:00Z,{date}T23:59:59Z'}, timeout=60)
        r.raise_for_status()
        entries = [e for e in r.json()['feed']['entry'] if '_T092-' in e['title']]
        if not entries:
            raise ValueError(f'No T092 observations for {date}')
        paths = []
        for e in entries:
            url = next(l['href'] for l in e['links'] if l['href'].startswith('https://') and l['href'].endswith('_VV.tif'))
            path = cache/url.rsplit('/',1)[-1]
            if not path.exists():
                response = session.get(url,timeout=120)
                response.raise_for_status()
                path.write_bytes(response.content)
            paths.append(path)
            manifests.append({'date':date,'product_id':e['title'],'url':url,
                              'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        # Same CRS for this track/region. Mosaic prevents double-counting overlap.
        sources = [rasterio.open(p) for p in paths]
        try:
            mosaic, affine = merge(sources, nodata=np.nan)
            src_crs = sources[0].crs
            bounds = rasterio.transform.array_bounds(mosaic.shape[1],mosaic.shape[2],affine)
            dst_transform, width, height = calculate_default_transform(src_crs,'EPSG:6933',
                mosaic.shape[2],mosaic.shape[1],*bounds,resolution=100)
            target = np.full((height,width),np.nan,dtype='float32')
            reproject(mosaic[0],target,src_transform=affine,src_crs=src_crs,src_nodata=np.nan,
                dst_transform=dst_transform,dst_crs='EPSG:6933',dst_nodata=np.nan,resampling=Resampling.average)
            profile = dict(driver='GTiff',width=width,height=height,count=1,dtype='float32',
                           crs='EPSG:6933',transform=dst_transform,nodata=np.nan)
            path = cache/f'gamma0_power_{date}.tif'
            with rasterio.open(path,'w',**profile) as f:f.write(target,1)
            datasets.append(path)
        finally:
            for src in sources:src.close()
        print(date,len(paths),'bursts acquired',flush=True)

    # Align all dates to the first fixed 100 m grid; use intersection of valid pixels.
    with rasterio.open(datasets[0]) as first:
        affine,crs,profile = first.transform,first.crs,first.profile
        arrays = []
        for path in datasets:
            with rasterio.open(path) as src:
                target = np.full((first.height,first.width),np.nan,dtype='float32')
                reproject(src.read(1),target,src_transform=src.transform,src_crs=src.crs,
                    src_nodata=np.nan,dst_transform=affine,dst_crs=crs,dst_nodata=np.nan,
                    resampling=Resampling.average)
                arrays.append(target)
    valid = np.logical_and.reduce([np.isfinite(a)&(a>0) for a in arrays])
    lake_doc = json.loads((ROOT/'data/recursos/csa/cocibolca_naturalearth.geojson').read_text())
    lake = shape(lake_doc['features'][0]['geometry'])
    # Rectangles are analytical windows, not official protected-area boundaries.
    domains = {'cocibolca_observado':lake,
               'los_guatuzos_ventana':box(-85.2,10.9,-84.8,11.1),
               'san_juan_ventana':box(-84.8,10.8,-84.4,11.0)}
    project = Transformer.from_crs(4326,6933,always_xy=True).transform
    masks, geometries = {}, []
    for name,geom in domains.items():
        inside = geometry_mask([mapping(transform(project,geom))],out_shape=valid.shape,transform=affine,invert=True)
        masks[name] = inside&valid
        geometries.append({'type':'Feature','properties':{'id':name,'nota':'Fixed analytical domain; observed pixels only'},'geometry':mapping(geom)})
    rows = []
    for date,array in zip(dates,arrays):
        db = potencia_a_db(array)
        for name,mask in masks.items():
            for threshold in [-19.,-17.,-15.]:
                rows.append({'fecha':date,'dominio':name,'umbral_db':threshold,
                    'area_candidata_agua_km2':float(np.count_nonzero(mask&(db<threshold))*.01),
                    'area_valida_comun_km2':float(mask.sum()*.01),
                    'radiometria':'gamma0 VV dB','resolucion_m':100,
                    'papel':'demostracion_registro_corto', 'validacion':'sin_validar_no_equivale_a_superficie_real'})
        # Binary water mask plus explicit common-valid domain, outside raw data dir.
        mask_path = cache/f'water_common_{date}.tif'
        mask_profile = {**profile,'dtype':'uint8','nodata':255}
        with rasterio.open(mask_path,'w',**mask_profile) as f:
            f.write(np.where(valid,db < -17,255).astype('uint8'),1)
    out = ROOT/'data/recursos/csa'
    with (out/'sar_superficie.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    (out/'sar_fuentes.json').write_text(json.dumps({'source':'ASF OPERA_L2_RTC-S1_V1',
        'radiometry':'gamma0 power -> average 100 m -> 10*log10',
        'method':'fixed T092 orbit, VV, common valid pixels, thresholds -19/-17/-15 dB',
        'lake_boundary_source':'https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_lakes.geojson',
        'lake_boundary_license':'Natural Earth public domain', 'granules':manifests},indent=2),encoding='utf-8')
    (out/'sar_dominios.geojson').write_text(json.dumps({'type':'FeatureCollection','features':geometries}),encoding='utf-8')
    swot = list(csv.DictReader((out/'swot_observaciones.csv').open()))
    pairs=[]
    for row in rows:
        if row['dominio']!='cocibolca_observado' or row['umbral_db']!=-17:continue
        obs=[o for o in swot if o['lago']=='cocibolca' and o['time_str'][:10]==row['fecha']]
        for o in obs:pairs.append({**row,'swot_time_utc':o['time_str'],'swot_wse_m':o['wse'],'swot_wse_u_m':o['wse_u']})
    with (out/'comparacion_swot_sar.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=pairs[0]);w.writeheader();w.writerows(pairs)
    print('SAR rows',len(rows),'SWOT same-day pairs',len(pairs),flush=True)


if __name__=='__main__':main()
