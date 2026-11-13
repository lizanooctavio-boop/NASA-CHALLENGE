"""Validación de Prairies con GHCN-Daily público; sin token ni noaa_cdo.py.

Uso: python data/recursos/csa/noaa_canada.py --cache ../noaa_canada
Exige todos los días válidos del año; nunca rellena ausencias ni combina IDs.
"""
import argparse
import calendar
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
import requests
from shapely.geometry import Point,shape

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
from clima_nic.estadistica.tendencia_robusta import analizar
BASE='https://www.ncei.noaa.gov/pub/data/ghcn/daily/'
YEARS=range(2001,2025)


def leer_dly(texto):
    """Valores GHCN-D en décimas -> mm/°C; QFLAG no vacío y MFLAG P excluidos."""
    out={}
    for line in texto.splitlines():
        if len(line)<269:continue
        year,month=int(line[11:15]),int(line[15:17]);element=line[17:21]
        if element not in ('PRCP','TAVG','TMAX','TMIN') or not (1951<=year<=1980 or year in YEARS):continue
        for day in range(1,calendar.monthrange(year,month)[1]+1):
            start=21+(day-1)*8
            value=int(line[start:start+5]);mflag,qflag=line[start+5],line[start+6]
            if value==-9999 or qflag!=' ' or mflag=='P':continue
            if element=='PRCP' and value<0:continue
            out.setdefault(element,{}).setdefault(year,{})[f'{month:02d}-{day:02d}']=value/10
    return out


def anuales_completos(dias,modo='media'):
    out={}
    for year,values in dias.items():
        expected={f'{month:02d}-{day:02d}' for month in range(1,13)
                  for day in range(1,calendar.monthrange(year,month)[1]+1)}
        if set(values)!=expected or not all(math.isfinite(v) for v in values.values()):continue
        out[year]=float(sum(values.values()) if modo=='suma' else np.mean(list(values.values())))
    return out


def resumir(texto):
    data=leer_dly(texto)
    rain=anuales_completos(data.get('PRCP',{}),'suma')
    direct=anuales_completos(data.get('TAVG',{}))
    derived={}
    for year,hi in data.get('TMAX',{}).items():
        lo=data.get('TMIN',{}).get(year,{})
        derived[year]={d:(h+lo[d])/2 for d,h in hi.items() if d in lo and h>=lo[d]}
    derived=anuales_completos(derived)
    choices=[('TAVG',direct),('mean(TMAX,TMIN)',derived)]
    # Consistent temperature definition over the baseline and analysis period.
    method,temp=max(choices,key=lambda p:(min(sum(y in p[1] for y in YEARS),20),
        min(sum(y in p[1] for y in range(1951,1981)),20),sum(y in p[1] for y in YEARS),p[0]=='TAVG'))
    warm={}
    for year,values in data.get('PRCP',{}).items():
        expected={f'{m:02d}-{d:02d}' for m in range(5,10) for d in range(1,calendar.monthrange(year,m)[1]+1)}
        if expected<=values.keys():warm[year]=sum(values[d] for d in expected)
    baseline=[temp[y] for y in range(1951,1981) if y in temp]
    return {'prcp':rain,'may_sep':warm,'temp':temp,'temp_method':method,
            'baseline_years':len(baseline),'baseline_c':float(np.mean(baseline)) if len(baseline)>=20 else None,
            'complete_joint_years':[y for y in YEARS if y in rain and y in temp]}


def resumir_gsom(rows):
    """GSOM: año completo = doce resúmenes mensuales válidos publicados por NOAA.

    No se rellenan meses ni días; NOAA permite hasta cinco días ausentes por mes.
    Se conserva el número de meses con esa marca para declarar esta limitación.
    """
    monthly={};marked=0
    for row in rows:
        year,month=map(int,row['DATE'][:7].split('-'))
        if not (1951<=year<=1980 or year in YEARS):continue
        for variable in ('PRCP','TAVG'):
            if variable not in row:continue
            value=float(row[variable])
            if not math.isfinite(value) or value==-9999 or (variable=='PRCP' and value<0):continue
            attributes=row.get(variable+'_ATTRIBUTES','').split(',')
            # PRCP quality flag (third position) must be empty.
            if variable=='PRCP' and len(attributes)>2 and attributes[2].strip():continue
            if attributes and attributes[0].strip():marked+=1
            monthly.setdefault(variable,{}).setdefault(year,{})[month]=value
    rain={y:sum(v.values()) for y,v in monthly.get('PRCP',{}).items() if set(v)==set(range(1,13))}
    temp={y:float(np.mean(list(v.values()))) for y,v in monthly.get('TAVG',{}).items() if set(v)==set(range(1,13))}
    warm={y:sum(v[m] for m in range(5,10)) for y,v in monthly.get('PRCP',{}).items() if set(range(5,10))<=v.keys()}
    base=[temp[y] for y in range(1951,1981) if y in temp]
    normal_months={m:[values[m] for year,values in monthly.get('TAVG',{}).items()
                      if 1951<=year<=1980 and m in values] for m in range(1,13)}
    baseline=float(np.mean([np.mean(v) for v in normal_months.values()])) if all(len(v)>=15 for v in normal_months.values()) else None
    return {'prcp':rain,'temp':temp,'may_sep':warm,'temp_method':'GSOM TAVG: mean of 12 published monthly means',
        'baseline_years':len(base),'baseline_c':baseline,
        'baseline_month_counts':{str(m):len(v) for m,v in normal_months.items()},
        'complete_joint_years':[y for y in YEARS if y in rain and y in temp],
        'monthly_values_with_missing_day_flag':marked}


def escribir_json(path,datos):
    path.write_text(json.dumps(datos,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--gsom',action='store_true');args=parser.parse_args()
    args.cache.mkdir(parents=True,exist_ok=True)
    out=Path(__file__).parent
    provenance=[]
    def acquire(url,path):
        if not path.exists():
            r=requests.get(url,timeout=90);r.raise_for_status();path.write_bytes(r.content)
        return path.read_bytes()
    inventory=acquire(BASE+'ghcnd-inventory.txt',args.cache/'inventory.txt').decode()
    stations_text=acquire(BASE+'ghcnd-stations.txt',args.cache/'stations.txt').decode()
    names={line[:11]:line[41:71].strip() for line in stations_text.splitlines()}
    polygon=shape(json.loads((ROOT/'data/regiones_canada.geojson').read_text(encoding='utf-8'))['features'][0]['geometry'])
    candidates={}
    for line in inventory.splitlines():
        sid=line[:11]
        if not sid.startswith('CA'):continue
        lat,lon=float(line[12:20]),float(line[21:30]);element=line[31:35].strip()
        first,last=int(line[36:40]),int(line[41:45])
        potential=min(last,2024)-max(first,2001)+1
        if element in ('PRCP','TAVG','TMAX','TMIN') and potential>=20 and polygon.covers(Point(lon,lat)):
            candidates.setdefault(sid,{'id':sid,'lat':lat,'lon':lon,'nombre':names.get(sid,sid),'elementos':[]})['elementos'].append(element)
    candidates=[v for v in candidates.values() if 'PRCP' in v['elementos'] and ('TAVG' in v['elementos'] or {'TMAX','TMIN'}<=set(v['elementos']))]
    def station(item):
        try:
            if args.gsom:
                query=requests.Request('GET','https://www.ncei.noaa.gov/access/services/data/v1',params={
                    'dataset':'global-summary-of-the-month','stations':item['id'],'startDate':'1951-01-01',
                    'endDate':'2024-12-31','dataTypes':'PRCP,TAVG','units':'metric','format':'json','includeAttributes':'true'}).prepare()
                url=query.url;raw=acquire(url,args.cache/(item['id']+'_gsom.json'))
                summary=resumir_gsom(json.loads(raw))
            else:
                url=BASE+'all/'+item['id']+'.dly';raw=acquire(url,args.cache/(item['id']+'.dly'))
                summary=resumir(raw.decode())
            meta={**item,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),
                'anios_prcp':sum(y in summary['prcp'] for y in YEARS),
                'anios_tavg':sum(y in summary['temp'] for y in YEARS),
                'anios_conjuntos':len(summary['complete_joint_years']),
                'anios_base_1951_1980':summary['baseline_years'],'metodo_tavg':summary['temp_method'],
                'media_base_1951_1980_c':summary['baseline_c'],
                'anios_base_por_mes':summary.get('baseline_month_counts',{}),
                'valores_mensuales_con_marca_dias_ausentes':summary.get('monthly_values_with_missing_day_flag',0),'estado':'ok'}
            return meta,summary
        except Exception as e:return {**item,'estado':'bloqueado','motivo':type(e).__name__},None
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,res in enumerate(pool.map(station,sorted(candidates,key=lambda x:x['id'])),1):
            results.append(res)
            if i%10==0:print('NOAA stations assessed',i,'/',len(candidates),flush=True)
    eligible=[r for r in results if r[1] and r[0]['anios_conjuntos']>=20 and r[1]['baseline_c'] is not None]
    # A fixed 3-station network; pick coverage geographically, not by trend or correlation.
    eligible.sort(key=lambda r:(-r[0]['anios_conjuntos'],-r[0]['anios_base_1951_1980'],r[0]['id']))
    selected=[];common=set(YEARS)
    while eligible and len(selected)<3:
        possible=[r for r in eligible if len(common&set(r[1]['complete_joint_years']))>=20]
        if not possible:break
        if selected:
            distance=lambda r:min(((r[0]['lon']-s[0]['lon'])*math.cos(math.radians(52)))**2+(r[0]['lat']-s[0]['lat'])**2 for s in selected)
            choice=max(possible,key=distance)
        else:choice=possible[0]
        selected.append(choice);eligible.remove(choice);common&=set(choice[1]['complete_joint_years'])
    escribir_json(out/('noaa_canada_inventario_gsom.json' if args.gsom else 'noaa_canada_inventario.json'),{'fuente_inventario':BASE+'ghcnd-inventory.txt',
        'fuente_estaciones':BASE+'ghcnd-stations.txt','candidatas_evaluadas':len(candidates),
        'criterio':('Doce resúmenes mensuales válidos de NOAA GSOM por año; NOAA permite hasta cinco días ausentes por mes; sin relleno local; referencia estimada 1951–1980 con >=15 valores de cada mes calendario (no normal WMO completa)' if args.gsom else 'Todos los días válidos; >=20 años completos de referencia 1951–1980')+'; >=20 años conjuntos 2001–2024; red fija de hasta tres estaciones separadas geográficamente',
        'estaciones_evaluadas':[r[0] for r in results],'seleccionadas':[r[0] for r in selected]})
    if not selected:raise RuntimeError('No stations satisfy the complete-year/baseline requirements; see inventory')
    print('SELECTED',[r[0]['id'] for r in selected],'COMMON_YEARS',sorted(common),flush=True)
    years=sorted(common)
    network={k:{y:float(np.mean([r[1][k][y] for r in selected])) for y in years} for k in ['prcp','may_sep']}
    network['temp']={y:float(np.mean([r[1]['temp'][y]-r[1]['baseline_c'] for r in selected])) for y in years}
    # Preserve physical station series and baseline; no spatial or temporal infilling.
    with (out/'noaa_canada_estaciones_anuales.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['estacion','anio','prcp_mm','prcp_may_sep_mm','tavg_c','tavg_anomalia_1951_1980_c'])
        for meta,r in selected:
            for y in r['complete_joint_years']:w.writerow([meta['id'],y,r['prcp'][y],r['may_sep'][y],r['temp'][y],r['temp'][y]-r['baseline_c']])
    station_ids=[r[0]['id'] for r in selected]
    if args.gsom:
        with (out/'noaa_canada_mensual.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(['estacion','fecha','prcp_mm','tavg_c','atributos_prcp','atributos_tavg'])
            for meta,_ in selected:
                raw=json.loads((args.cache/(meta['id']+'_gsom.json')).read_text())
                for row in raw:
                    year=int(row['DATE'][:4])
                    if 1951<=year<=1980 or year in YEARS:
                        w.writerow([meta['id'],row['DATE'],row.get('PRCP','NA'),row.get('TAVG','NA'),
                            row.get('PRCP_ATTRIBUTES','sin_marca'),row.get('TAVG_ATTRIBUTES','sin_marca')])
    contrasts=[];csvrows=[];detail=[]
    for cid,file,key,unit,source in [
        ('noaa_canada_lluvia','canada_imerg.json','prcp','mm/década','NASA GPM IMERG Final V07B, Canadian Prairies'),
        ('noaa_canada_tavg','canada_gistemp.json','temp','°C/década','NASA GISTEMP v4 250 km, Canadian Prairies; anomalies vs 1951–1980')]:
        ours=json.loads((out/file).read_text(encoding='utf-8'));mapping=dict(zip(ours['anios'],ours['valores']))
        shared=[y for y in years if y in mapping]
        x=[mapping[y] for y in shared];external=[network[key][y] for y in shared]
        a,b=analizar(shared,x,'mm' if key=='prcp' else '°C'),analizar(shared,external,'mm' if key=='prcp' else '°C')
        correlation=float(np.corrcoef(x,external)[0,1]);bias=float(np.mean(np.array(external)-x))
        short=' Fewer than three eligible stations were available.' if len(selected)<3 else ''
        verdict_en={'evidencia_insuficiente':'insufficient evidence of a trend',
                    'tendencia_detectada':'trend detected','metodos_discrepan':'methods disagree',
                    'datos_insuficientes':'insufficient data'}
        unit_en='mm/decade' if key=='prcp' else '°C/decade'
        phrase=(f'{len(selected)} fixed Prairies stations, {len(shared)} complete common years'+(' (12 valid NOAA GSOM months/year)' if args.gsom else '')+f': r={correlation:.3f}, '
                f'mean station-minus-NASA difference={bias:+.3f} {"mm/year" if key=="prcp" else "°C"}; '
                f'Sen slopes NASA {a["theil_sen"]["por_decada"]:+.4f} versus stations {b["theil_sen"]["por_decada"]:+.4f} {unit_en}; '
                f'verdicts {verdict_en.get(a["veredicto"],a["veredicto"])} / {verdict_en.get(b["veredicto"],b["veredicto"])}.'+short)
        contrasts.append({'id':cid,'papel':'contraste','estado':'ok','region':'CAN_prairies','periodo':[min(shared),max(shared)],
            'serie_nuestra':{'fuente':source,'pendiente':a['theil_sen']['por_decada'],'unidad':unit,'veredicto':a['veredicto']},
            'serie_externa':{'fuente':f'Prairies weather stations (NOAA {"GSOM from GHCN-Daily" if args.gsom else "GHCN-Daily"}, {len(selected)} stations)',
                'pendiente':b['theil_sen']['por_decada'],'veredicto':b['veredicto'],'url':selected[0][0]['url'],
                'urls':[r[0]['url'] for r in selected],'estaciones':station_ids},
            'diferencia':{'media':bias,'r':correlation,'anios_comunes':len(shared)},'frase_en':phrase})
        detail.append({'id':cid,'anios':shared,'nuestra':a,'externa':b})
        csvrows.extend([{'contraste':cid,'serie':kind,'anio':y,'valor':v} for kind,values in [('nuestra',x),('externa',external)] for y,v in zip(shared,values)])
    # Warm-season cross-check retains requested two contrast IDs unchanged.
    warm=json.loads((out/'canada_imerg_may_sep.json').read_text(encoding='utf-8'));wm=dict(zip(warm['anios'],warm['valores']))
    shared=[y for y in years if y in wm];x=[wm[y] for y in shared];z=[network['may_sep'][y] for y in shared]
    detail.append({'id':'noaa_canada_lluvia_may_sep','anios':shared,'r':float(np.corrcoef(x,z)[0,1]),
        'diferencia_media_mm':float(np.mean(np.array(z)-x)),
        'nuestra':analizar(shared,x,'mm'),'externa':analizar(shared,z,'mm')})
    annual=json.loads((out/'canada_imerg.json').read_text(encoding='utf-8'))
    annual_map=dict(zip(annual['anios'],annual['valores']))
    cold_x=[annual_map[y]-wm[y] for y in shared]
    cold_z=[network['prcp'][y]-network['may_sep'][y] for y in shared]
    detail.append({'id':'noaa_canada_lluvia_fuera_may_sep','anios':shared,
        'definicion':'Meses octubre–abril del mismo año calendario; no es un invierno DJF continuo',
        'r':float(np.corrcoef(cold_x,cold_z)[0,1]),
        'diferencia_media_mm':float(np.mean(np.array(cold_z)-cold_x)),
        'nuestra':analizar(shared,cold_x,'mm'),'externa':analizar(shared,cold_z,'mm')})
    with (out/'noaa_canada_may_sep_series.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['serie','anio','valor'])
        for kind,values in [('nuestra',x),('externa',z)]:
            for year,value in zip(shared,values):w.writerow([kind,year,value])
    escribir_json(out/'contrastes_canada.json',{'esquema':'nasa-challenge/contrastes','version':'1.0.0',
        'generado':dt.datetime.now(dt.timezone.utc).date().isoformat(),'contrastes':contrasts})
    escribir_json(out/'noaa_canada_detalle.json',{'baseline_temperatura':('1951–1980, media de las 12 normales mensuales por estación; cada mes con >=15 observaciones anuales; no es una normal WMO completa' if args.gsom else '1951–1980, media por estación de >=20 años completos'),
        'red_fija':station_ids,'contrastes':detail})
    with (out/'contrastes_canada_series.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['contraste','serie','anio','valor']);w.writeheader();w.writerows(csvrows)
    print('CONTRASTS',[(c['id'],c['diferencia']) for c in contrasts],flush=True)


if __name__=='__main__':main()
