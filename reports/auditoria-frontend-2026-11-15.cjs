const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const out=path.join(__dirname,'frontend-2026-11-15');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
 const report={};
 try {
 const p=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
 const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8996/',{waitUntil:'networkidle'});
 await p.screenshot({path:path.join(out,'desktop.png')});
 report.initial={errors,espacio:await p.evaluate(()=>!!window.Espacio)};
 for(const tab of ['investigar','tendencias','indicadores','fenomenos','escenarios','aprender','fuentes']){
 await p.locator(`[data-tab="${tab}"]`).click();await p.waitForTimeout(350);
 report[tab]=await p.locator('#'+tab).innerText();
 }
 for(const width of [375,768,1280]){
 await p.setViewportSize({width,height:800});await p.locator('[data-tab="meteorologia"]').click();
 await p.screenshot({path:path.join(out,`width-${width}.png`)});
 report['width'+width]=await p.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:innerWidth,nav:[...document.querySelectorAll('nav button')].map(x=>({text:x.textContent.trim(),rect:x.getBoundingClientRect().toJSON(),name:x.getAttribute('aria-label')}))}));
 }
 await p.close();
 const no=await browser.newPage();
 await no.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type.includes('webgl')?null:original.call(this,type,...args)}});
 const noErrors=[];no.on('pageerror',e=>noErrors.push(e.message));
 await no.goto('http://127.0.0.1:8996/#map',{waitUntil:'networkidle'});
 await no.waitForTimeout(4200);
 report.noWebGL=await no.evaluate(()=>({mode:window.SICC_vista.modo(),mapVisibility:getComputedStyle(document.querySelector('#mapa')).visibility,globe:!!window.Espacio}));report.noWebGL.errors=noErrors;
 await no.screenshot({path:path.join(out,'no-webgl.png')});await no.close();
 const fail=await browser.newPage();let requests=0;
 await fail.route('**/data/recursos_integrados.json',route=>{requests++;return requests===1?route.fulfill({status:503,body:'Unavailable'}):route.continue()});
 await fail.goto('http://127.0.0.1:8996/',{waitUntil:'networkidle'});
 await fail.locator('[data-tab="investigar"]').click();await fail.waitForTimeout(500);
 await fail.locator('[data-tab="meteorologia"]').click();await fail.locator('[data-tab="investigar"]').click();await fail.waitForTimeout(500);
 report.retry={requests,text:await fail.locator('#investigar').innerText()};await fail.close();
 }finally{fs.writeFileSync(path.join(out,'resultados.json'),JSON.stringify(report,null,2));await browser.close()}
 console.log(JSON.stringify({initial:report.initial,noWebGL:report.noWebGL,retry:report.retry},null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
