// Real WebGL regression and screenshots. Run with NODE_PATH pointing to Playwright.
const { chromium } = require('playwright');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname,'../public');
const out = path.resolve(__dirname,'../reports/globo-detalle');
fs.mkdirSync(out,{recursive:true});
const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.geojson':'application/json','.jpg':'image/jpeg','.png':'image/png'};
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]==='/'?'/index.html':req.url.split('?')[0]));
  if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
  fs.readFile(file,(e,data)=>{if(e){res.writeHead(404).end();return;}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.end(data);});
});
(async()=>{
  await new Promise(r=>server.listen(8996,'127.0.0.1',r));
  const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  const errors=[], shaderErrors=[], tiles=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error' && /THREE|shader|WebGL/i.test(m.text()))shaderErrors.push(m.text());});
  page.on('response',r=>{if(r.url().includes('World_Imagery/MapServer/tile/'))tiles.push({url:r.url(),status:r.status()});});
  // Probe only: direct camera poses avoid dozens of wheel events in edge-case tests.
  await page.route('**/app/espacio.js',async route=>{
    const response=await route.fetch();let code=await response.text();
    code=code.replace('window.Espacio = {','window.__pose = (lon,lat,dist) => { Object.assign(estado,{lon,lat,dist,velLon:0,velLat:0,ultimoGesto:performance.now()}); dibujar(); };\nwindow.Espacio = {');
    await route.fulfill({response,body:code});
  });
  try{
    await page.goto('http://127.0.0.1:8996/',{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>window.Espacio,{timeout:45000});
    await page.screenshot({path:path.join(out,'01-global.png')});
    await page.evaluate(()=>{document.querySelector('main').style.display='none';document.querySelector('aside').style.display='none';window.Espacio.desplazar(0);window.__pose(-86.25,12.14,1.06);});
    await page.waitForFunction(()=>window.Espacio.detalle().visible>10,{timeout:45000});
    await page.waitForTimeout(8000);
    const regional=await page.evaluate(()=>window.Espacio.detalle());
    await page.screenshot({path:path.join(out,'02-regional.png')});
    await page.evaluate(()=>window.__pose(-86.25,12.14,1.0005));
    await page.waitForTimeout(15000);
    const local=await page.evaluate(()=>window.Espacio.detalle());
    await page.screenshot({path:path.join(out,'03-managua.png')});
    assert.ok(local.level>regional.level,'zoom must request finer tiles');
    assert.ok(local.cached<=320 && local.active<=6,'bounded cache and concurrency');
    assert.ok(tiles.some(t=>/\/tile\/1[4-7]\//.test(t.url)&&t.status===200),'local imagery must really download');
    const before=await page.evaluate(()=>window.Espacio.centro());
    await page.mouse.move(700,400); await page.mouse.wheel(0,-300);
    await page.waitForTimeout(300);
    const after=await page.evaluate(()=>window.Espacio.centro());
    assert.ok(after.dist<before.dist && after.dist>1,'real wheel zoom stays above the surface');
    await page.mouse.down(); await page.mouse.move(750,400,{steps:5}); await page.mouse.up();
    const dragged=await page.evaluate(()=>window.Espacio.centro());
    assert.ok(Math.abs(dragged.lon-after.lon)<.1,'local drag must not jump across a continent');
    // Exercise the same weather texture interface used by the actual field module.
    await page.evaluate(()=>{const c=document.createElement('canvas');c.width=512;c.height=256;const x=c.getContext('2d');x.fillStyle='rgba(0,100,255,.5)';x.fillRect(0,0,512,256);window.Espacio.meteo(c,.65);});
    await page.waitForTimeout(400);
    await page.screenshot({path:path.join(out,'06-weather-shader.png')});
    await page.evaluate(()=>window.Espacio.meteo(null,0));
    // Provider outage: retain cached parents / original globe, never blank the scene.
    await page.route('**/World_Imagery/MapServer/tile/**',r=>r.abort());
    await page.evaluate(()=>window.__pose(179.99,25,1.02));
    await page.waitForTimeout(2500);
    await page.screenshot({path:path.join(out,'04-fallback.png')});
    await page.unroute('**/World_Imagery/MapServer/tile/**');
    await page.evaluate(()=>window.__pose(-84,12,2.3));
    await page.waitForTimeout(5000);
    await page.screenshot({path:path.join(out,'07-sphere.png')});
    await page.evaluate(()=>window.SICC_vista.cambiar('mapa'));
    assert.equal(await page.evaluate(()=>window.SICC_vista.modo()),'mapa');
    await page.evaluate(()=>window.SICC_vista.cambiar('globo'));
    assert.equal(await page.evaluate(()=>window.SICC_vista.modo()),'globo');
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>window.__pose(-86.25,12.14,1.01));
    await page.waitForTimeout(8000);
    await page.screenshot({path:path.join(out,'05-mobile.png')});
    const report={regional,local,errors,shaderErrors,tiles:tiles.length,successfulTiles:tiles.filter(t=>t.status===200).length};
    fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
    assert.deepEqual(shaderErrors,[]);assert.deepEqual(errors,[]);
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
