"""Serie corta DSWx-S1 oficial: cierre del radar sin ajustar clasificadores.

Conserva solo BWTR 0/1, excluye conflictos entre mosaicos y usa área común.
El producto comparte Sentinel-1 con el modelo: no es validación independiente.
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import requests
import earthaccess
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
import shapely
from shapely.geometry import shape,mapping

ROOT=Path(__file__).resolve().parents[2]


def main():
    out=ROOT/'data/recursos/csa';cache=ROOT.parent/'dswx_cierre';cache.mkdir(exist_ok=True)
    dates=['2024-09-24','2024-12-17','2026-01-17']
    lake=shape(json.loads((out/'cocibolca_naturalearth.geojson').read_text(encoding='utf-8'))['features'][0]['geometry'])
    transform=Transformer.from_crs(4326,6933,always_xy=True).transform
    projected=shapely.transform(lake,transform,interleaved=False)
    west,south,east,north=projected.bounds
    west,south=np.floor(np.array([west,south])/100)*100
    east,north=np.ceil(np.array([east,north])/100)*100
    affine=from_origin(west,north,100,100);size=(int((north-south)/100),int((east-west)/100))
    inside=geometry_mask([mapping(projected)],out_shape=size,transform=affine,invert=True)
    earthaccess.login(strategy='netrc');session=earthaccess.get_requests_https_session()
    arrays=[];provenance=[];summaries=[]
    for date in dates:
        params={'short_name':'OPERA_L3_DSWX-S1_V1','page_size':100,
            'bounding_box':'-85.95,10.7,-84.4,12.3','temporal':f'{date}T00:00:00Z,{date}T23:59:59Z'}
        r=requests.get('https://cmr.earthdata.nasa.gov/search/granules.json',params=params,timeout=60)
        r.raise_for_status();entries=r.json()['feed']['entry']
        if len(entries)>=100:raise ValueError('CMR necesita paginación; no se truncará la serie')
        grid=np.full(size,255,dtype='uint8');conflict=np.zeros(size,bool)
        for e in sorted(entries,key=lambda e:e['title']):
            url=next(l['href'] for l in e['links'] if l['href'].startswith('https://') and l['href'].endswith('_B02_BWTR.tif'))
            path=cache/url.rsplit('/',1)[-1]
            if not path.exists():
                response=session.get(url,timeout=90);response.raise_for_status();path.write_bytes(response.content)
            with rasterio.open(path) as src:
                target=np.full(size,255,dtype='uint8')
                reproject(src.read(1),target,src_transform=src.transform,src_crs=src.crs,src_nodata=255,
                    dst_transform=affine,dst_crs='EPSG:6933',dst_nodata=255,resampling=Resampling.nearest)
                tags=src.tags()
                valid=(target==0)|(target==1);old=(grid==0)|(grid==1)
                conflict|=valid&old&(grid!=target)
                grid[valid&~old]=target[valid&~old]
            provenance.append({'fecha':date,'id':e['title'],'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'orbita':tags.get('RTC_TRACK_NUMBER','no_indicada'),
                'inicio_utc':tags.get('RTC_SENSING_START_TIME',e['time_start']),
                'fin_utc':tags.get('RTC_SENSING_END_TIME',e.get('time_end',e['time_start']))})
        grid[conflict]=255;arrays.append(grid)
        summaries.append({'fecha':date,'productos':len(entries),'pixeles_conflictivos_excluidos':int((inside&conflict).sum()),
            'fraccion_lago_valida':float((inside&((grid==0)|(grid==1))).sum()/inside.sum())})
        with rasterio.open(cache/f'cocibolca_bwtr_{date}.tif','w',driver='GTiff',dtype='uint8',count=1,
            width=size[1],height=size[0],crs='EPSG:6933',transform=affine,nodata=255) as dst:dst.write(grid,1)
        print(date,summaries[-1],flush=True)
    common=inside&np.logical_and.reduce([(a==0)|(a==1) for a in arrays])
    rows=[]
    for date,array in zip(dates,arrays):
        rows.append({'fecha':date,'region':'cocibolca_dominio_comun_dswx_s1',
            'producto':'OPERA_L3_DSWX-S1_V1','papel':'demostracion_registro_corto',
            'superficie_clasificada_agua_km2':float((common&(array==1)).sum()*.01),
            'area_valida_comun_km2':float(common.sum()*.01),
            'cobertura_fraccion_lago':float(common.sum()/inside.sum()),
            'estado':'NO_VALIDADA','motivo':'registro_corto;sin_validacion_local_independiente;dominio_observado_parcial',
            'resolucion_analisis_m':100})
    with (out/'dswx_s1_serie_corta.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    (out/'dswx_s1_cierre.json').write_text(json.dumps({'estado':'cerrado_como_demostracion',
        'producto':'OPERA_L3_DSWX-S1_V1','papel':'demostracion_registro_corto','fechas':dates,
        'calidad':'Solo BWTR 0/1; exclusión de otras clases y conflictos; máscara común fija; sin extrapolación',
        'independencia':'Comparte Sentinel-1 con el modelo; NO es validación independiente de ese modelo',
        'resumen':summaries,'serie':rows,'fuentes':provenance},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
