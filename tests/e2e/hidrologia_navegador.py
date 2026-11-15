"""Prueba opcional con datos reales, sin simular respuestas ni imágenes remotas.

pip install playwright && python -m playwright install chromium
python tests/e2e/hidrologia_navegador.py --url http://127.0.0.1:8765/ --api http://127.0.0.1:8000
El fondo 3D se pausa con la API de la app y se usa movimiento reducido.
"""
import json,pathlib
from playwright.sync_api import sync_playwright
import argparse, tempfile
args_parser=argparse.ArgumentParser(description='Recorrido real de cuencas, códigos, descargas y estaciones. Requiere playwright y public/ servido por HTTP.')
args_parser.add_argument('--url',default='http://127.0.0.1:8765/')
args_parser.add_argument('--api',help='Origen opcional de clima_nic para comprobar INETER real')
args_parser.add_argument('--salida',type=pathlib.Path,help='Carpeta opcional para capturas y exportaciones')
args=args_parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]
temporal=tempfile.TemporaryDirectory(prefix='hydrology-e2e-')
salida=args.salida or pathlib.Path(temporal.name)
salida.mkdir(parents=True,exist_ok=True)
m=json.loads((root/'data/hidrologia/procedencia.json').read_text())
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,args=['--no-sandbox','--ignore-certificate-errors','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(ignore_https_errors=True,viewport={'width':1440,'height':1000},device_scale_factor=.5,reduced_motion='reduce',accept_downloads=True)
 errores=[]
 page.on('pageerror',lambda e:errores.append(str(e)))
 page.on('console',lambda e:errores.append(e.text+' '+str(e.location)) if e.type=='error' else None)
 page.add_init_script("document.addEventListener('espacio:listo',()=>window.Espacio.pausar(true))")
 page.goto(args.url,wait_until='domcontentloaded')
 page.evaluate('window.Espacio?.pausar(true)')
 page.locator('nav [data-tab=hidrologia]').click()
 page.wait_for_function("document.querySelector('#hid-estado').textContent.startsWith('2,337')",timeout=60000)
 assert page.locator('#hid-estado').inner_text().startswith('2,337')
 page.locator('#hid-buscar').fill('9519581')
 page.locator('#hid-resultados button').first.click()
 assert '9519581' in page.locator('#hid-detalle').inner_text()
 assert '9519587' in page.locator('#hid-detalle').inner_text()
 page.locator('#hid-etiquetas').check()
 with page.expect_download() as dl:page.locator('#hid-csv').click()
 dl.value.save_as(str(salida/'codigos.csv'))
 assert '9519581' in pathlib.Path(str(salida/'codigos.csv')).read_text()
 with page.expect_download() as dl:page.locator('#hid-geojson').click()
 dl.value.save_as(str(salida/'cuencas.geojson'))
 assert len(json.loads(pathlib.Path(str(salida/'cuencas.geojson')).read_text())['features'])==2337
 print('NIC OK, discrepancy, labels, two downloads',flush=True)
 page.screenshot(path=str(salida/'nicaragua.png'),full_page=True)
 for region in m['regions']:
  for level in [4,6]:
   page.locator('#hid-region').select_option(region);page.locator('#hid-nivel').select_option(str(level));page.locator('#hid-ver').click()
   esperado=next(x['features'] for x in m['global'] if x['region']==region and x['level']==level)
   page.wait_for_function('(n)=>window.SICC_hidrologia.estado().poligonos===n',arg=esperado,timeout=60000)
   page.wait_for_function("(s)=>document.querySelector('#hid-estado').textContent.includes(s)",arg='level '+str(level),timeout=45000)
   print(region,level,esperado,'OK',flush=True)
 page.locator('#hid-region').select_option('world');page.locator('#hid-ver').click()
 page.wait_for_function('window.SICC_hidrologia.estado().poligonos===1342',timeout=60000)
 print('WORLD OK',flush=True)
 for id_,n in [('nivel_rio',37),('lluvia_24h',92),('temperatura',59),('viento',65)]:
  page.locator('#hid-estacion').select_option(id_);page.locator('#hid-estaciones-ver').click()
  page.wait_for_function('(n)=>window.SICC_hidrologia.estado().estaciones===n',arg=n,timeout=45000)
  page.wait_for_function("document.querySelector('#hid-estaciones-estado').textContent.includes('retrieved')")
  print('stations',id_,n,'OK',flush=True)
 page.locator('#hid-actualizar').click()
 page.wait_for_function("document.querySelector('#hid-estaciones-estado').textContent.includes('not configured')")
 if args.api:
  page.evaluate('(url)=>window.SICC_CONFIG.hidrologia_api=url',args.api)
  page.locator('#hid-estacion').select_option('nivel_rio');page.locator('#hid-actualizar').click()
  page.wait_for_function("document.querySelector('#hid-estaciones-estado').textContent.startsWith('INETER response')",timeout=45000)
  print('LIVE API OK',page.locator('#hid-estaciones-estado').inner_text(),flush=True)
 with page.expect_response(lambda r:'/geoserver/wms?' in r.url,timeout=45000) as respuesta_wms:
  page.locator('#hid-referencia-ver').click()
 imagen=respuesta_wms.value
 assert imagen.status==200 and imagen.body().startswith(b'\x89PNG')
 page.locator('#hid-referencia-ocultar').click()
 print('INETER WMS PNG OK',flush=True)
 page.locator('#hidrologia details summary').click()
 page.locator('#hid-catalogo-buscar').fill('corredor')
 page.locator('#hid-catalogo li').filter(has_text='SINAPRED').get_by_role('button',name='Show map').click()
 page.wait_for_function("document.querySelector('#hid-referencia-estado').textContent.includes('source features')",timeout=60000)
 print('SINAPRED VECTORS OK',page.locator('#hid-referencia-estado').inner_text(),flush=True)
 page.locator('#hid-referencia-ocultar').click()
 page.locator('#hid-region').select_option('nic');page.locator('#hid-ver').click()
 page.wait_for_function("document.querySelector('#hid-estado').textContent.startsWith('2,337')",timeout=45000)
 page.screenshot(path=str(salida/'estaciones.png'),full_page=True)
 print('ERRORS',json.dumps(errores,ensure_ascii=False),flush=True)
 assert not errores
 b.close()
temporal.cleanup()
