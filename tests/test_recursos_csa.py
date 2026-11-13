"""Pruebas sin red de los recursos de la CSA y del caso de contraste canadiense.

- data/regiones_canada.geojson: GeoJSON válido en EPSG:4326, al sur de 60° N, fuente y licencia presentes, tamaño.
- clima_nic.fuentes.lagos: parseo de un CSV de Hydrocron guardado como fixture, descarte de rellenos y de
  calidad, formato del lake_id de la PLD (10 dígitos).

    python -m pytest tests/test_recursos_csa.py -q
"""
import json
import math
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

REGION = RAIZ / "data" / "regiones_canada.geojson"
CAMPOS_COMUNES = {"id", "nombre", "tipo", "rol", "bbox", "area_km2"}  # mismo esquema que data/dominios.geojson


def _coordenadas(geom):
    """Itera todas las posiciones (lon, lat) de un Polygon o MultiPolygon GeoJSON."""
    anillos = geom["coordinates"] if geom["type"] == "Polygon" else [a for p in geom["coordinates"] for a in p]
    for anillo in anillos:
        yield from anillo


class RegionCanada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texto = REGION.read_text(encoding="utf-8")
        cls.doc = json.loads(cls.texto)
        cls.feat = cls.doc["features"][0]
        cls.props = cls.feat["properties"]

    def test_estructura_geojson(self):
        self.assertEqual(self.doc["type"], "FeatureCollection")
        self.assertEqual(len(self.doc["features"]), 1)
        self.assertEqual(self.feat["type"], "Feature")
        self.assertIn(self.feat["geometry"]["type"], ("Polygon", "MultiPolygon"))
        self.assertEqual(self.feat["id"], self.props["id"])

    def test_esquema_como_dominios(self):
        self.assertTrue(CAMPOS_COMUNES <= self.props.keys())
        self.assertEqual(self.props["tipo"], "ecozona")
        self.assertEqual(self.props["rol"], "contraste")

    def test_epsg4326_y_al_sur_de_60N(self):
        self.assertEqual(self.props["crs"], "EPSG:4326")
        lons, lats = zip(*[(c[0], c[1]) for c in _coordenadas(self.feat["geometry"])])
        self.assertTrue(all(-180 <= x <= 180 for x in lons))
        self.assertTrue(all(-90 <= y <= 90 for y in lats))
        # Cobertura completa de IMERG: 60° S–60° N.
        self.assertLess(max(lats), 60.0)
        self.assertGreater(min(lats), -60.0)
        # Coherente con el bbox declarado.
        oeste, sur, este, norte = self.props["bbox"]
        self.assertAlmostEqual(min(lons), oeste, places=2)
        self.assertAlmostEqual(max(lats), norte, places=2)

    def test_anillos_cerrados(self):
        g = self.feat["geometry"]
        poligonos = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for pol in poligonos:
            for anillo in pol:
                self.assertGreaterEqual(len(anillo), 4)
                self.assertEqual(anillo[0], anillo[-1])

    def test_fuente_y_licencia(self):
        lic = self.props["licencia"]
        self.assertEqual(lic["nombre"], "Open Government Licence – Canada")
        self.assertTrue(lic["url"].startswith("https://open.canada.ca/"))
        self.assertIn("Open Government Licence", lic["atribucion"])
        fuente = self.props["fuente"]
        for k in ("url_conjunto", "url_descarga", "url_geoca"):
            self.assertTrue(fuente[k].startswith("https://"), k)
        self.assertRegex(fuente["sha256_descarga"], r"^[0-9a-f]{64}$")
        self.assertRegex(self.props["fecha_descarga"], r"^\d{4}-\d{2}-\d{2}$")

    def test_simplificacion_y_areas(self):
        p = self.props
        self.assertTrue(0 < p["simplificacion"]["tolerancia_grados"] <= 0.02)
        self.assertLess(p["vertices_simplificado"], p["vertices_original"])
        # La simplificación no debe cambiar el área más de un 1 %.
        self.assertLess(abs(p["area_km2"] - p["area_km2_original"]) / p["area_km2_original"], 0.01)
        # Ecozona Prairies: ~4,7·10⁵ km².
        self.assertTrue(4.0e5 < p["area_km2"] < 5.5e5)

    def test_tamano(self):
        self.assertLess(REGION.stat().st_size, 300 * 1024)

    def test_geometria_valida_y_area(self):
        try:
            from shapely.geometry import shape
            from clima_nic.rutas import proyectar_6933
        except ImportError:
            self.skipTest("requiere shapely y pyproj")
        g = shape(self.feat["geometry"])
        self.assertTrue(g.is_valid)
        area = proyectar_6933(g).area / 1e6
        self.assertTrue(math.isclose(area, self.props["area_km2"], rel_tol=1e-3))


# ---------------------------------------------------------------- SWOT / Hydrocron

# Fixture: filas reales de la respuesta de Hydrocron para Cocibolca (7530096743), con un duplicado exacto, dos
# pasadas sin observación (relleno) y una observación con quality_f = 3 (mala).
CSV_HYDROCRON = (
    "lake_id,time_str,wse,wse_u,area_total,quality_f,partial_f,dark_frac,ice_clim_f,xovr_cal_q,cycle_id,pass_id,"
    "wse_units,wse_u_units,area_total_units,dark_frac_units\n"
    "7530096743,2023-07-28T22:17:15Z,31.743,0.0,2892.224042,0,1,0.006901,0,0,001,216,m,m,km^2,1\n"
    "7530096743,2023-08-04T09:35:50Z,31.613,0.0,947.743729,1,1,0.020464,0,0,001,397,m,m,km^2,1\n"
    "7530096743,2023-08-04T09:35:50Z,31.613,0.0,947.743729,1,1,0.020464,0,0,001,397,m,m,km^2,1\n"
    "7530096743,no_data,-999999999999.0,-999999999999.0,-999999999999.0,-999,-999,-999999999999.0,0,-999,002,397,"
    "m,m,km^2,1\n"
    "7530096743,no_data,-999999999999.0,-999999999999.0,-999999999999.0,-999,-999,-999999999999.0,0,-999,002,522,"
    "m,m,km^2,1\n"
    "7530096743,2023-09-15T03:06:01Z,31.801,0.0,944.905664,0,1,0.007183,0,0,003,397,m,m,km^2,1\n"
    "7530096743,2023-10-05T23:51:02Z,30.262,0.001,905.304859,3,1,0.002014,0,2,004,397,m,m,km^2,1\n"
    "7530096743,2023-10-10T10:55:13Z,31.723,0.0,3454.81382,0,1,0.003838,0,0,004,522,m,m,km^2,1\n"
)
DIR_CSA = RAIZ / "data" / "recursos" / "csa"


class Hydrocron(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from clima_nic.fuentes import lagos
        cls.lagos = lagos

    def test_lake_id_10_digitos(self):
        L = self.lagos
        for lago, lid in L.SWOT_LAKE_IDS.items():
            self.assertTrue(L.es_lake_id(lid), lago)
            self.assertEqual(len(lid), 10)
        self.assertEqual(L.SWOT_LAKE_IDS, {"cocibolca": "7530096743", "xolotlan": "7530093763"})
        for malo in ("753009674", "75300967430", "0530096743", "75300967a3", ""):
            self.assertFalse(L.es_lake_id(malo), malo)
        with self.assertRaises(ValueError):
            L.url_hydrocron("123", "2023-07-26", "2024-01-01")

    def test_url_peticion(self):
        u = self.lagos.url_hydrocron("7530096743", "2023-07-26", "2026-11-12")
        self.assertTrue(u.startswith("https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?"))
        for parte in ("feature=PriorLake", "feature_id=7530096743", "start_time=2023-07-26T00:00:00Z",
                      "end_time=2026-11-12T00:00:00Z", "output=csv", "fields=lake_id,time_str,wse"):
            self.assertIn(parte, u)

    def test_parseo_csv_y_sobre_json(self):
        L = self.lagos
        filas = L.leer_hydrocron(CSV_HYDROCRON)
        self.assertEqual(len(filas), 7)  # el duplicado exacto se elimina
        sobre = json.dumps({"status": "200 OK", "hits": 8, "results": {"csv": CSV_HYDROCRON}})
        self.assertEqual(L.leer_hydrocron(sobre), filas)
        self.assertEqual(filas[0]["wse"], 31.743)
        self.assertEqual(filas[0]["quality_f"], 0)
        self.assertEqual(filas[2]["quality_f"], -999)

    def test_filtro_relleno_y_calidad(self):
        L = self.lagos
        validas, conteo = L.filtrar_hydrocron(L.leer_hydrocron(CSV_HYDROCRON))
        self.assertEqual(conteo, {"total": 7, "relleno": 2, "calidad": 1, "validas": 4})
        self.assertTrue(all(f["wse"] > 0 and f["quality_f"] <= 1 for f in validas))
        self.assertNotIn(30.262, [f["wse"] for f in validas])
        estrictas, c0 = L.filtrar_hydrocron(L.leer_hydrocron(CSV_HYDROCRON), calidad_max=0)
        self.assertEqual(c0["validas"], 3)

    def test_mensual_y_tendencia_corta(self):
        L = self.lagos
        validas, _ = L.filtrar_hydrocron(L.leer_hydrocron(CSV_HYDROCRON))
        meses, medias, n = L.mensual_hydrocron(validas)
        self.assertEqual(meses, ["2023-07", "2023-08", "2023-09", "2023-10"])
        self.assertEqual(n, [1, 1, 1, 1])
        self.assertAlmostEqual(medias[1], 31.613)
        b, motivo = L.tendencia_si_suficiente(meses, medias)
        self.assertIsNone(b)
        self.assertIn("corta", motivo)
        # Con una serie larga sí se calcula.
        largos = [f"{a}-{m:02d}" for a in range(2001, 2025) for m in range(1, 13)]
        b, _ = L.tendencia_si_suficiente(largos, [0.01 * i / 12 for i in range(len(largos))])
        self.assertAlmostEqual(b, 0.01, places=6)

    def test_grealm_gsfc_compatible(self):
        L = self.lagos
        texto = ("000351 Nicaragua           : Target database id number and name\n"
                 "POSDN   1 19921002  14 54   -0.19  0.051  11.88 ERA NIC ERA 3 9 0    31.84   0\n"
                 "TOPEX   2 19921012  12 52  999.99 99.999 999.99 ERA DOR ERA 4 0 0  9999.99   0\n")
        self.assertEqual(L.leer_grealm(texto), (["1992-10-02"], [31.84]))
        self.assertEqual(L.leer_grealm_gsfc(texto)[0]["mision"], "POSDN")

    def test_respuestas_guardadas(self):
        """Las respuestas crudas guardadas en data/recursos/csa se leen y la tabla limpia es coherente."""
        L = self.lagos
        crudos = sorted(DIR_CSA.glob("hydrocron_*.json"))
        if not crudos:
            self.skipTest("sin respuestas de Hydrocron guardadas")
        meta = json.loads((DIR_CSA / "consultas_hydrocron.json").read_text(encoding="utf-8"))
        for c in meta["consultas"]:
            self.assertTrue(L.es_lake_id(c["lake_id"]))
            self.assertIn(f"feature_id={c['lake_id']}", c["url"])
            self.assertRegex(c["consulta_utc"], r"^\d{4}-\d{2}-\d{2}T")
        for ruta in crudos:
            validas, conteo = L.filtrar_hydrocron(L.leer_hydrocron(ruta.read_text(encoding="utf-8")))
            self.assertGreater(conteo["validas"], 0)
            self.assertTrue(all(L.es_lake_id(f["lake_id"]) for f in validas))
            self.assertTrue(all(25 < f["wse"] < 50 for f in validas), ruta.name)  # cotas de ambos lagos


class CanadaImerg(unittest.TestCase):
    def test_total_anual_bisiesto_y_falta_mes(self):
        import runpy
        import tempfile
        import numpy as np
        import h5py
        from shapely.geometry import box
        module = runpy.run_path(str(RAIZ / 'data/recursos/csa/canada.py'))
        with tempfile.TemporaryDirectory() as td:
            files = []
            for month in range(1, 13):
                path = Path(td) / f'3B-MO.MS.MRG.3IMERG.2020{month:02d}01-S000000.HDF5'
                with h5py.File(path, 'w') as f:
                    g = f.create_group('Grid')
                    g['lat'] = [50., 51., 52.]
                    g['lon'] = [-113., -112., -111.]
                    v = g.create_dataset('precipitation', data=np.ones((1, 3, 3)))
                    v.attrs['units'] = 'mm/hr'
                files.append(path)
            # Patch only the spatial domain; exercise real HDF5, weights, calendar and annual aggregation.
            module['lluvia_canada'].__globals__['cargar'] = lambda _: {'CAN_prairies': box(-112.5, 50.5, -111.5, 51.5)}
            result = module['lluvia_canada'](files, Path(td)/'annual.json')
            self.assertEqual(result['anios'], [2020])
            self.assertAlmostEqual(result['valores'][0], 366*24)
            self.assertIsNone(result['tendencia'])
            warm=module['lluvia_canada'](files[4:9],Path(td)/'warm.json',meses_objetivo=(5,6,7,8,9))
            self.assertEqual(warm['anios'],[2020])
            self.assertAlmostEqual(warm['valores'][0],153*24)
            incomplete=module['lluvia_canada'](files[4:8],Path(td)/'warm_missing.json',meses_objetivo=(5,6,7,8,9))
            self.assertEqual(incomplete['anios'],[])
            result = module['lluvia_canada'](files[:-1], Path(td)/'missing.json')
            self.assertEqual(result['anios'], [])
            with self.assertRaisesRegex(ValueError, 'Duplicate month'):
                module['lluvia_canada'](files + files[:1], Path(td)/'duplicate.json')

    def test_lectura_canadiense_y_relleno(self):
        import runpy
        import tempfile
        import numpy as np
        import h5py
        module = runpy.run_path(str(RAIZ / 'data/recursos/csa/canada.py'))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'test.HDF5'
            with h5py.File(path, 'w') as f:
                g = f.create_group('Grid')
                g['lat'] = [11., 49., 51.]
                g['lon'] = [-113., -111., -85.]
                values = np.ones((1, 3, 3))
                values[0, 0, 1] = -9999.9
                v = g.create_dataset('precipitation', data=values)
                v.attrs['units'] = 'mm/hr'
                v.attrs['_FillValue'] = -9999.9
            lat, lon, field = module['leer_imerg_canada'](path)
            self.assertEqual(lat.tolist(), [49., 51.])
            self.assertEqual(lon.tolist(), [-113., -111.])
            self.assertTrue(np.isnan(field[0, 0]))
            self.assertEqual(field[1, 1], 1.)
            with h5py.File(path, 'a') as f:
                f['Grid/precipitation'].attrs['units'] = 'mm/day'
            with self.assertRaises(ValueError):
                module['leer_imerg_canada'](path)


class SarAgua(unittest.TestCase):
    def test_caracteristicas_dualpol_excluyen_nodata(self):
        import numpy as np
        from clima_nic.fuentes.sar_agua import caracteristicas_dualpol
        vv=np.full((5,5),.01);vh=np.full((5,5),.001)
        features,valid=caracteristicas_dualpol(vv,vh)
        self.assertTrue(valid.all())
        np.testing.assert_allclose(features[2,2],[-20,-30,10,-20,0,-30,0],atol=1e-5)
        vh[2,2]=0
        features,valid=caracteristicas_dualpol(vv,vh)
        self.assertFalse(valid[2,2])
        self.assertTrue((features[2,2]==0).all())
        self.assertTrue(np.isfinite(features).all())

    def test_superficie_no_se_publica_con_nubes_o_error(self):
        from clima_nic.fuentes.sar_agua import superficie_publicable
        good = {'f1':.95,'recall_water':.95,'recall_land':.95}
        self.assertFalse(superficie_publicable(good,.01))
        self.assertTrue(superficie_publicable(good,.90))
        self.assertFalse(superficie_publicable({**good,'recall_water':.4},.99))
        self.assertFalse(superficie_publicable({**good,'f1':None},.99))

    def test_calibracion_no_usa_etiquetas_de_validacion(self):
        import numpy as np
        from clima_nic.fuentes.sar_agua import calibrar_umbral, evaluar_mascara
        db = np.r_[np.full(60,-20.),np.full(60,-5.),np.full(60,-15.)]
        labels = np.r_[np.ones(60,bool),np.zeros(60,bool),np.ones(60,bool)]
        train = np.r_[np.ones(120,bool),np.zeros(60,bool)]
        threshold = calibrar_umbral(db,labels,train)
        labels[120:] = False
        self.assertEqual(calibrar_umbral(db,labels,train),threshold)
        metrics = evaluar_mascara(db<threshold,labels,train)
        self.assertEqual(metrics['f1'],1.)
        with self.assertRaises(ValueError):
            calibrar_umbral(db,labels,np.zeros(180,bool))

    def test_metricas_indefinidas_no_son_exito(self):
        from clima_nic.fuentes.sar_agua import evaluar_mascara
        m = evaluar_mascara([False],[False],[True])
        self.assertIsNone(m['recall_water'])
        self.assertIsNone(m['f1'])

    def test_potencia_gamma0_sin_convertir_nodata_en_agua(self):
        import numpy as np
        from clima_nic.fuentes.sar_agua import potencia_a_db, mascara_agua
        db = potencia_a_db([1., .01, 0., -1., np.inf, np.nan])
        np.testing.assert_allclose(db[:2], [0., -20.])
        self.assertTrue(np.isnan(db[2:]).all())
        self.assertEqual(mascara_agua(db).tolist(), [False, True, False, False, False, False])

    def test_mascara_nodata_y_area(self):
        import numpy as np
        import rasterio
        import tempfile
        from rasterio.transform import from_origin
        from clima_nic.fuentes.sar_agua import procesar
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td)/'in.tif', Path(td)/'out.tif'
            with rasterio.open(src, 'w', driver='GTiff', width=2, height=2, count=1,
                               dtype='float32', crs='EPSG:6933', nodata=-9999,
                               transform=from_origin(0, 200, 100, 100)) as f:
                f.write(np.array([[-20, -10], [-9999, -22]], dtype='float32'), 1)
            r = procesar(src, dst)
            self.assertAlmostEqual(r['area_agua_km2'], .02)
            self.assertAlmostEqual(r['area_valida_km2'], .03)
            with rasterio.open(dst) as f:
                self.assertEqual(f.read(1).tolist(), [[1, 0], [255, 1]])

    def test_fechas_comunes_sin_interpolar(self):
        from clima_nic.fuentes.sar_agua import fechas_comunes
        self.assertEqual(fechas_comunes({'2023-01-01':32}, {'2023-01-02':8000}), [])


class ResultadosRealesCanadaSar(unittest.TestCase):
    def test_lector_noaa_marcas_y_meses_ausentes(self):
        import runpy
        reader=runpy.run_path(str(DIR_CSA/'noaa_canada.py'))
        blocks=[]
        for day in range(1,32):
            value,mflag,qflag=10,' ',' '
            if day==2:mflag='P'
            if day==3:qflag='X'
            if day==4:value,mflag=0,'T'
            blocks.append(f'{value:5d}{mflag}{qflag}C')
        d=reader['leer_dly']('CAN04013660200101PRCP'+''.join(blocks))
        self.assertEqual(len(d['PRCP'][2001]),29)
        self.assertEqual(d['PRCP'][2001]['01-04'],0.)
        self.assertNotIn('01-02',d['PRCP'][2001])
        rows=[{'DATE':f'2001-{m:02d}','PRCP':'5','TAVG':'10','PRCP_ATTRIBUTES':',,,C'} for m in range(1,13)]
        self.assertEqual(reader['resumir_gsom'](rows)['prcp'],{2001:60.})
        self.assertEqual(reader['resumir_gsom'](rows[:-1])['complete_joint_years'],[])

    def test_cierre_dswx_respeta_demostracion_y_dominio(self):
        import csv
        d=json.loads((DIR_CSA/'dswx_s1_cierre.json').read_text(encoding='utf-8'))
        self.assertEqual(d['estado'],'cerrado_como_demostracion')
        self.assertEqual(d['papel'],'demostracion_registro_corto')
        rows=list(csv.DictReader((DIR_CSA/'dswx_s1_serie_corta.csv').open(encoding='utf-8')))
        self.assertEqual(len(rows),3)
        self.assertEqual(len({r['area_valida_comun_km2'] for r in rows}),1)
        self.assertTrue(all(r['estado']=='NO_VALIDADA' for r in rows))
        self.assertTrue(all(0<=float(r['superficie_clasificada_agua_km2'])<=float(r['area_valida_comun_km2']) for r in rows))
        self.assertTrue(all(0<float(r['cobertura_fraccion_lago'])<=1 for r in rows))

    def test_estacion_calida_formato_y_24_anios(self):
        from scipy.stats import theilslopes
        d=json.loads((DIR_CSA/'canada_imerg_may_sep.json').read_text(encoding='utf-8'))
        self.assertTrue({'region','papel','producto','unidad','anios','valores','criterio','tendencia'}<=d.keys())
        self.assertEqual(d['region'],'CAN_prairies')
        self.assertEqual(d['papel'],'tendencia')
        self.assertEqual(d['unidad'],'mm/year')
        self.assertEqual(d['anios'],list(range(2001,2025)))
        self.assertEqual(len(d['valores']),24)
        slope=theilslopes(d['valores'],d['anios']).slope*10
        self.assertAlmostEqual(slope,d['tendencia']['theil_sen']['por_decada'],delta=.00006)

    def test_contrastes_canada_esquema_y_estaciones(self):
        from shapely.geometry import Point,shape
        d=json.loads((DIR_CSA/'contrastes_canada.json').read_text(encoding='utf-8'))
        self.assertEqual(d['esquema'],'nasa-challenge/contrastes')
        self.assertEqual(d['version'],'1.0.0')
        self.assertEqual({c['id'] for c in d['contrastes']},{'noaa_canada_lluvia','noaa_canada_tavg'})
        meta=json.loads((DIR_CSA/'noaa_canada_inventario_gsom.json').read_text(encoding='utf-8'))
        selected=meta['seleccionadas'];self.assertGreaterEqual(len(selected),3)
        polygon=shape(json.loads(REGION.read_text(encoding='utf-8'))['features'][0]['geometry'])
        for station in selected:
            self.assertTrue(polygon.covers(Point(station['lon'],station['lat'])))
            self.assertGreaterEqual(station['anios_conjuntos'],20)
            self.assertGreaterEqual(min(station['anios_base_por_mes'].values()),15)
        for c in d['contrastes']:
            self.assertEqual(c['papel'],'contraste');self.assertEqual(c['estado'],'ok')
            self.assertEqual(c['region'],'CAN_prairies');self.assertEqual(c['periodo'],[2001,2024])
            self.assertEqual(set(c['serie_externa']['estaciones']),{s['id'] for s in selected})
            self.assertNotIn('evidencia_insuficiente',c['frase_en'])

    def test_series_csv_reproducen_contrastes_json(self):
        import csv
        import numpy as np
        from scipy.stats import pearsonr,theilslopes
        rows=list(csv.DictReader((DIR_CSA/'contrastes_canada_series.csv').open(encoding='utf-8')))
        self.assertEqual(set(rows[0]),{'contraste','serie','anio','valor'})
        d=json.loads((DIR_CSA/'contrastes_canada.json').read_text(encoding='utf-8'))
        for c in d['contrastes']:
            pairs={kind:{int(r['anio']):float(r['valor']) for r in rows if r['contraste']==c['id'] and r['serie']==kind}
                   for kind in ['nuestra','externa']}
            self.assertEqual(set(pairs['nuestra']),set(pairs['externa']))
            years=sorted(pairs['nuestra']);self.assertEqual(len(years),c['diferencia']['anios_comunes'])
            self.assertGreaterEqual(len(years),20)
            x=np.array([pairs['nuestra'][y] for y in years]);z=np.array([pairs['externa'][y] for y in years])
            self.assertAlmostEqual(float(pearsonr(x,z).statistic),c['diferencia']['r'],places=12)
            self.assertAlmostEqual(float(np.mean(z-x)),c['diferencia']['media'],places=12)
            for values,field in [(x,'serie_nuestra'),(z,'serie_externa')]:
                self.assertAlmostEqual(float(theilslopes(values,years).slope*10),c[field]['pendiente'],delta=.00006)
            source=json.loads((DIR_CSA/('canada_imerg.json' if c['id'].endswith('lluvia') else 'canada_gistemp.json')).read_text(encoding='utf-8'))
            mapping=dict(zip(source['anios'],source['valores']))
            self.assertEqual(x.tolist(),[mapping[y] for y in years])

    def test_estaciones_no_rellenan_meses_ni_cambian_red(self):
        import csv
        from collections import defaultdict
        monthly=defaultdict(dict)
        for r in csv.DictReader((DIR_CSA/'noaa_canada_mensual.csv').open(encoding='utf-8')):
            monthly[(r['estacion'],int(r['fecha'][:4]))][int(r['fecha'][5:7])]=r
        annual=list(csv.DictReader((DIR_CSA/'noaa_canada_estaciones_anuales.csv').open(encoding='utf-8')))
        for r in annual:
            months=monthly[(r['estacion'],int(r['anio']))]
            self.assertEqual(set(months),set(range(1,13)))
            self.assertTrue(all(m['prcp_mm']!='NA' and m['tavg_c']!='NA' for m in months.values()))
            self.assertAlmostEqual(sum(float(m['prcp_mm']) for m in months.values()),float(r['prcp_mm']),places=9)
        grouped=defaultdict(list)
        for r in annual:grouped[int(r['anio'])].append(r)
        contrasts=json.loads((DIR_CSA/'contrastes_canada.json').read_text(encoding='utf-8'))['contrastes']
        series=list(csv.DictReader((DIR_CSA/'contrastes_canada_series.csv').open(encoding='utf-8')))
        for c in contrasts:
            field='prcp_mm' if c['id'].endswith('lluvia') else 'tavg_anomalia_1951_1980_c'
            for r in series:
                if r['contraste']==c['id'] and r['serie']=='externa':
                    source=grouped[int(r['anio'])]
                    self.assertEqual(len(source),len(c['serie_externa']['estaciones']))
                    self.assertAlmostEqual(sum(float(s[field]) for s in source)/len(source),float(r['valor']),places=12)

    def test_dualpol_campos_completos_y_evaluacion_temporal_separada(self):
        import csv
        report=json.loads((DIR_CSA/'sar_dualpol_validacion.json').read_text(encoding='utf-8'))
        for r in report['reports']:
            self.assertNotIn(r['date'],r['temporal_training_dates'])
            self.assertEqual(len(r['temporal_training_dates']),2)
        for name in ['sar_dualpol_superficie.csv','comparacion_swot_sar_dualpol.csv','sar_superficie_calibrada.csv']:
            rows=list(csv.DictReader((DIR_CSA/name).open()))
            self.assertGreater(len(rows),0)
            self.assertTrue(all(v not in ('',None) for row in rows for v in row.values()),name)
        rows=list(csv.DictReader((DIR_CSA/'sar_dualpol_superficie.csv').open()))
        self.assertEqual(len(rows),9)
        for row in rows:
            self.assertGreaterEqual(float(row['area_estimacion_modelo_km2']),0)
            self.assertLessEqual(float(row['area_estimacion_modelo_km2']),float(row['area_dominio_comun_km2']))
            if row['estado']=='estimacion_no_validada':
                self.assertEqual(row['area_agua_validada_km2'],'NO_VALIDADA')
                self.assertNotEqual(row['motivo'],'controles_superados')

    def test_canada_imerg_periodo_completo_y_cobertura(self):
        p = DIR_CSA / 'canada_imerg.json'
        self.assertTrue(p.exists(), 'Missing real Canadian IMERG result')
        d = json.loads(p.read_text(encoding='utf-8'))
        self.assertEqual(d['anios'], list(range(2001, 2025)))
        self.assertEqual(len(d['fuentes']), 288)
        self.assertEqual(len(set(d['meses'])), 288)
        self.assertTrue(all(c >= .95 for c in d['cobertura_valida']))
        self.assertTrue(all(math.isfinite(v) and v > 0 for v in d['valores']))

    def test_sar_dominio_constante_sensibilidad_y_pares_swot(self):
        import csv
        rows = list(csv.DictReader((DIR_CSA/'sar_superficie.csv').open()))
        self.assertEqual(len(rows), 27)
        for domain in {r['dominio'] for r in rows}:
            subset = [r for r in rows if r['dominio'] == domain]
            coverages = {float(r['area_valida_comun_km2']) for r in subset}
            self.assertEqual(len(coverages), 1)
            self.assertGreater(next(iter(coverages)), 0)
            for date in {r['fecha'] for r in subset}:
                seq = sorted([r for r in subset if r['fecha'] == date],key=lambda r:float(r['umbral_db']))
                areas = [float(r['area_candidata_agua_km2']) for r in seq]
                self.assertEqual(areas, sorted(areas))
                self.assertLessEqual(max(areas), next(iter(coverages)))
        pairs = list(csv.DictReader((DIR_CSA/'comparacion_swot_sar.csv').open()))
        self.assertEqual(len({r['fecha'] for r in pairs}), 3)
        for r in pairs:
            self.assertEqual(r['fecha'], r['swot_time_utc'][:10])
            self.assertEqual(r['dominio'], 'cocibolca_observado')


if __name__ == "__main__":
    unittest.main()
