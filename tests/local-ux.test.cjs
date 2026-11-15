// Unit regressions for the expiry bug. Built-in Node modules, no new dependencies.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = {window:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/soporte-meteo.js'),'utf8'),context);
const {vigente,utc} = context.window.SICC_soporte;
const hours=['2026-11-12T00:00:00Z','2026-11-12T03:00:00Z','2026-11-12T06:00:00Z'];
test('forecast within its window is current',()=>assert.equal(vigente(hours,utc('2026-11-12T04:00:00Z')),true));
test('last step remains valid only for its cadence',()=>assert.equal(vigente(hours,utc('2026-11-12T08:59:59Z')),true));
test('expiry boundary is exclusive',()=>assert.equal(vigente(hours,utc('2026-11-12T09:00:00Z')),false));
test('old cache is not current',()=>assert.equal(vigente(hours,utc('2026-11-15T12:00:00Z')),false));
test('a future window is not current',()=>assert.equal(vigente(hours,utc('2026-11-11T23:00:00Z')),false));
test('empty and invalid timestamps are not current',()=>{assert.equal(vigente([],0),false);assert.equal(vigente(['invalid'],0),false)});
test('explicit timezone is respected',()=>assert.equal(utc('2026-11-12T00:00:00-06:00'),utc('2026-11-12T06:00:00Z')));
test('single hourly timestamp expires after one hour',()=>{assert.equal(vigente([hours[0]],utc('2026-11-12T00:30:00Z')),true);assert.equal(vigente([hours[0]],utc('2026-11-12T01:00:00Z')),false)});
