"""Dual-polarization radar model with spatial AND leave-one-date-out tests.

Raw radar, optical masks, features and fitted models stay outside Git.
Hyperparameters and validation stripes are fixed before test evaluation.
"""
import concurrent.futures
import csv
import hashlib
import json
import netrc
import sys
import threading
import re
from pathlib import Path
import numpy as np
import requests
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling
from rasterio.features import geometry_mask
from pyproj import Transformer
from shapely.geometry import shape,mapping
from shapely.ops import transform
from sklearn.ensemble import RandomForestClassifier
import asf_search as asf

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from clima_nic.fuentes.earthdata import ruta_netrc
from clima_nic.fuentes.sar_agua import caracteristicas_dualpol,evaluar_mascara,superficie_publicable


def model():
    return RandomForestClassifier(n_estimators=80,max_depth=12,min_samples_leaf=30,
        class_weight='balanced_subsample',random_state=8687,n_jobs=2)


def main():
    out=ROOT/'data/recursos/csa'
    cache=ROOT.parent/'opera_rtc'
    dates=['2024-03-04','2024-04-21','2024-07-14']
    manifests=json.loads((out/'sar_fuentes.json').read_text(encoding='utf-8'))['granules']
    user,_,password=netrc.netrc(str(ruta_netrc())).authenticators('urs.earthdata.nasa.gov')
    auth=asf.ASFSession().auth_with_creds(user,password)
    local=threading.local()
    def get(g):
        url=g['url'].replace('_VV.tif','_VH.tif')
        p=cache/url.rsplit('/',1)[-1]
        if not p.exists():
            if not hasattr(local,'s'):
                local.s=requests.Session();local.s.headers.update(auth.headers);local.s.cookies.update(auth.cookies)
            r=local.s.get(url,timeout=120);r.raise_for_status();p.write_bytes(r.content)
        return {**g,'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        vh_sources=list(pool.map(get,manifests))
    print('VH acquisition',len(vh_sources),'bursts',flush=True)
    with rasterio.open(cache/f'gamma0_power_{dates[0]}.tif') as first:
        profile=first.profile;affine=first.transform;crs=first.crs;size=first.shape
    features=[];valids=[];refs=[];train=[];tests=[]
    columns=np.arange(size[1])[None,:]
    trstripe=np.broadcast_to((columns//50)%4==0,size)
    testripe=np.broadcast_to((columns//50)%4==2,size)
    rng=np.random.default_rng(8687)
    for date in dates:
        vh_path=cache/f'gamma0_vh_power_{date}.tif'
        if not vh_path.exists():
            paths=[cache/g['url'].rsplit('/',1)[-1] for g in vh_sources if g['date']==date]
            src=[rasterio.open(p) for p in paths]
            try:
                mosaic,t=merge(src,nodata=np.nan)
                vh=np.full(size,np.nan,dtype='float32')
                reproject(mosaic[0],vh,src_transform=t,src_crs=src[0].crs,src_nodata=np.nan,
                    dst_transform=affine,dst_crs=crs,dst_nodata=np.nan,resampling=Resampling.average)
                with rasterio.open(vh_path,'w',**profile) as dst:dst.write(vh,1)
            finally:
                for s in src:s.close()
        with rasterio.open(vh_path) as src:vh=src.read(1)
        with rasterio.open(cache/f'gamma0_power_{date}.tif') as src:
            vv=np.full(size,np.nan,dtype='float32')
            reproject(src.read(1),vv,src_transform=src.transform,src_crs=src.crs,src_nodata=np.nan,
                dst_transform=affine,dst_crs=crs,dst_nodata=np.nan,resampling=Resampling.average)
        x,valid=caracteristicas_dualpol(vv,vh)
        path=cache/f'features_dualpol_{date}.npy';np.save(path,x);del x,vv,vh
        x=np.load(path,mmap_mode='r').reshape(-1,7)
        with rasterio.open(ROOT.parent/f'optical_validation/optical_reference_{date}.tif') as src:ref=src.read(1)
        labelled=valid&((ref==0)|(ref==1))
        selected=[]
        for label in (0,1):
            idx=np.flatnonzero(labelled&trstripe&(ref==label))
            if len(idx)<50:raise ValueError('Insufficient optical training class')
            selected.extend(rng.choice(idx,min(10000,len(idx)),replace=False))
        idx=np.array(selected)
        train.append((np.array(x[idx]),ref.ravel()[idx]))
        test_idx=np.flatnonzero(labelled&testripe)
        tests.append((test_idx,ref.ravel()[test_idx]))
        features.append(path);valids.append(valid);refs.append(ref)
        print(date,'features and splits ready',flush=True)
    fitted=model()
    fitted.fit(np.concatenate([p[0] for p in train]),np.concatenate([p[1] for p in train]))
    common=np.logical_and.reduce(valids)
    clear_common=common&np.logical_and.reduce([(r==0)|(r==1) for r in refs])
    domains=json.loads((out/'sar_dominios.geojson').read_text(encoding='utf-8'))['features']
    projection=Transformer.from_crs(4326,6933,always_xy=True).transform
    masks={f['properties']['id']:geometry_mask([mapping(transform(projection,shape(f['geometry'])))],
        out_shape=size,transform=affine,invert=True)&common for f in domains}
    reports=[];rows=[]
    for i,date in enumerate(dates):
        x=np.load(features[i],mmap_mode='r').reshape(-1,7)
        idx,truth=tests[i]
        pred=fitted.predict(x[idx])
        spatial=evaluar_mascara(pred,truth,np.ones(len(idx),bool))
        # Held-out date was never used in this model's training.
        temporal_model=model()
        temporal_model.fit(np.concatenate([p[0] for j,p in enumerate(train) if j!=i]),
            np.concatenate([p[1] for j,p in enumerate(train) if j!=i]))
        temporal=evaluar_mascara(temporal_model.predict(x[idx]),truth,np.ones(len(idx),bool))
        probability=np.zeros(x.shape[0],dtype='float32')
        valid_idx=np.flatnonzero(valids[i])
        for start in range(0,len(valid_idx),100000):
            part=valid_idx[start:start+100000]
            probability[part]=fitted.predict_proba(x[part])[:,1]
        probability=probability.reshape(size)
        pred=probability>=.5
        reports.append({'date':date,'spatial_test':spatial,'leave_one_date_out_test':temporal,
            'test_pixels':len(idx),'training_pixels_by_date':[len(y) for _,y in train],
            'temporal_training_dates':[d for j,d in enumerate(dates) if j!=i]})
        for name,mask in masks.items():
            area=float(mask.sum()*.01)
            coverage=float((mask&clear_common).sum()/mask.sum()) if mask.any() else 0.
            ok=superficie_publicable(spatial,coverage) and superficie_publicable(temporal,coverage)
            estimate=float((mask&pred).sum()*.01)
            reasons=[]
            if coverage<.8:reasons.append('referencia_optica_comun_menor_80pct')
            for label,m in [('espacial',spatial),('temporal',temporal)]:
                if not all(m.get(k) is not None and m[k]>=.90 for k in ('f1','recall_water','recall_land')):
                    reasons.append('evaluacion_'+label+'_insuficiente')
            rows.append({'fecha':date,'dominio':name,'area_estimacion_modelo_km2':estimate,
                'area_dominio_comun_km2':area,
                'area_ambigua_prob_025_075_km2':float((mask&(probability>=.25)&(probability<=.75)).sum()*.01),
                'cobertura_referencia_comun':coverage,'estado':'validada_en_dominio_observado' if ok else 'estimacion_no_validada',
                'area_agua_validada_km2':estimate if ok else 'NO_VALIDADA',
                'motivo':'controles_superados' if ok else ';'.join(reasons),
                'papel':'demostracion_registro_corto'})
        with rasterio.open(cache/f'dualpol_prob_{date}.tif','w',**profile) as dst:
            dst.write(np.where(valids[i],probability,np.nan),1)
        print(date,'spatial',spatial,'temporal',temporal,flush=True)
    (out/'sar_dualpol_validacion.json').write_text(json.dumps({'model':fitted.get_params(),
        'features':['VV_db','VH_db','VV_minus_VH_db','VV_local_mean','VV_local_std','VH_local_mean','VH_local_std'],
        'predictor_exclusions':'No coordinates, optical labels, lake outlines, SWOT or date index as predictors',
        'split':'5 km training/test stripes, separated by unused stripes; same split on every date',
        'temporal_evaluation':'leave one date out; no hyperparameter tuning on test scores',
        'probability_note':'forest vote fraction; not a calibrated probability or confidence interval',
        'reports':reports,'vh_sources':vh_sources},indent=2),encoding='utf-8')
    with (out/'sar_dualpol_superficie.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    swot=list(csv.DictReader((out/'swot_observaciones.csv').open()))
    pairs=[]
    for row in rows:
        if row['dominio']!='cocibolca_observado':continue
        times=sorted(re.search(r'_(\d{8}T\d{6}Z)_',g['product_id']).group(1)
                     for g in manifests if g['date']==row['fecha'])
        for observation in swot:
            if observation['lago']=='cocibolca' and observation['time_str'][:10]==row['fecha']:
                pairs.append({**row,'radar_acquisition_start_utc':times[0],
                    'radar_acquisition_end_utc':times[-1],
                    'swot_time_utc':observation['time_str'],'swot_wse_m':observation['wse'],
                    'swot_wse_u_reported_m':observation['wse_u'],
                    'comparabilidad':'mismo_dia_no_simultaneo;superficie_modelada_no_validada'})
    with (out/'comparacion_swot_sar_dualpol.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=pairs[0]);w.writeheader();w.writerows(pairs)


if __name__=='__main__':main()
