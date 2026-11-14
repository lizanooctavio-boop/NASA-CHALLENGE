import test from 'node:test';
import assert from 'node:assert/strict';
import { bounds, point, tileAt, zoomDistance, dragDegrees, MIN_DISTANCE } from '../app/teselas-geometria.mjs';

test('known geographic points stay in their tile at every LOD', () => {
  for (const [lon, lat] of [[-86.25,12.14],[179.99,0],[-179.99,-30],[0,80],[140,-80]]) {
    for (let z=2;z<=17;z++) {
      const t=tileAt(lon,lat,z), b=bounds(z,t.x,t.y), rad=Math.PI/180;
      assert.ok(lon*rad>=b.west && lon*rad<=b.east);
      assert.ok(lat*rad>=b.south && lat*rad<=b.north);
      assert.equal(Math.floor(t.x/2),tileAt(lon,lat,z-1).x);
      assert.equal(Math.floor(t.y/2),tileAt(lon,lat,z-1).y);
    }
  }
});
test('Mercator boundary, dateline and pole handling remain finite', () => {
  assert.deepEqual(tileAt(180,0,8),tileAt(-180,0,8));
  for(const lat of [-90,90]) { const t=tileAt(0,lat,17); assert.ok(t.y>=0 && t.y<2**17); }
  const a=bounds(6,0,0), b=bounds(6,1,0);
  assert.equal(a.east,b.west);
  assert.ok(Math.abs(Math.hypot(...point(a.west,a.north))-1)<1e-12);
});
test('zoom scales altitude, never crosses the Earth and reverses without jumps', () => {
  const d=1.01;
  assert.ok(Math.abs(zoomDistance(zoomDistance(d,.8),1/.8)-d)<1e-12);
  assert.equal(zoomDistance(1.001,.001),MIN_DISTANCE);
  assert.equal(zoomDistance(30,10),34);
  assert.ok(dragDegrees(1.001,800)<dragDegrees(2,800)/900);
  assert.ok(dragDegrees(MIN_DISTANCE,800)>0);
});
