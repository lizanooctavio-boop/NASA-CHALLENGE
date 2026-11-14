import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js';
import { bounds, point, MAX_ZOOM } from './teselas-geometria.mjs';

// Keep the existing Earth shader (weather, wind and night lights). Only its day
// image changes. Parents remain below children until more detailed tiles arrive.
export function crearTeselas({ escena, renderer, material, uniformes }) {
  const group = new THREE.Group();
  escena.add(group);
  const cache = new Map(), pending = new Map();
  const frustum = new THREE.Frustum(), matrix = new THREE.Matrix4();
  const MAX_CACHE = 320, MAX_ACTIVE = 6, MAX_LEAVES = 150;
  let queue = [], wanted = new Set(), active = 0, stamp = 0, last = -Infinity, enabled = false;
  let selected = [], generation = 0;
  const stats = { level: 0, visible: 0, cached: 0, active: 0, failed: 0 };
  const credit = document.getElementById('credito-globo');
  const fragment = material.fragmentShader
    .replace('uniform sampler2D uDia,', 'uniform sampler2D uTesela; uniform vec3 uTile; uniform float uDetalle;\n    uniform sampler2D uDia,')
    .replace('void main() {', 'void main() {\n      if (dot(normalize(vNormal), normalize(uCamPos - vPos)) <= 0.0) discard;')
    .replace('vec3 noche =', `
      float my = (1.0 - log(tan(0.78539816339 + clamp(vLonLat.y, -1.4844222297, 1.4844222297) * 0.5)) / 3.14159265359) * 0.5;
      vec2 tileUV = vec2((vLonLat.x + 3.14159265359) / 6.28318530718 * uTile.z - uTile.x,
                         1.0 - (my * uTile.z - uTile.y));
      dia = mix(dia, texture(uTesela, clamp(tileUV, 0.0, 1.0)).rgb, uDetalle);
      vec3 noche =`);
  function key(t) { return `${t.z}/${t.x}/${t.y}`; }
  function descriptor(z, x, y) {
    const b = bounds(z, x, y), lon = (b.west + b.east) / 2, lat = (b.north + b.south) / 2;
    const center = new THREE.Vector3(...point(lon, lat));
    // Angular path bound contains every point, including curved tile edges.
    const angle = Math.min(Math.PI, (b.east - b.west + b.north - b.south) / 2);
    return { z, x, y, b, center, angle, radius: 2 * Math.sin(angle / 2) };
  }
  function select(camera, rotation, height) {
    camera.updateMatrixWorld();
    matrix.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse).multiply(rotation);
    frustum.setFromProjectionMatrix(matrix);
    const eye = camera.position.clone().applyMatrix4(rotation.clone().invert());
    const distance = eye.length(), direction = eye.clone().normalize();
    const horizon = Math.acos(1 / distance);
    const focal = height / (2 * Math.tan(camera.fov * Math.PI / 360));
    let leaves, ancestorCount;
    let threshold = 300;
    do {
      leaves = [];
      function visit(z, x, y) {
        if (leaves.length > MAX_LEAVES) return;
        const t = descriptor(z, x, y);
        const angle = Math.acos(THREE.MathUtils.clamp(t.center.dot(direction), -1, 1));
        if (angle > horizon + t.angle) return;
        if (!frustum.intersectsSphere(new THREE.Sphere(t.center, t.radius))) return;
        const range = Math.max(distance - 1, eye.distanceTo(t.center) - t.radius);
        const width = Math.max((t.b.east - t.b.west) * Math.cos((t.b.north + t.b.south) / 2), t.b.north - t.b.south);
        if (z < MAX_ZOOM && width * focal / range > threshold) {
          for (let j = 0; j < 2; j++) for (let i = 0; i < 2; i++) visit(z + 1, x * 2 + i, y * 2 + j);
        } else { t.priority = angle; leaves.push(t); }
      }
      for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) visit(2, x, y);
      const ancestors = new Set();
      for (const t of leaves) for (let z = 2; z <= t.z; z++) {
        const factor = 2 ** (t.z - z);
        ancestors.add(`${z}/${Math.floor(t.x / factor)}/${Math.floor(t.y / factor)}`);
      }
      ancestorCount = ancestors.size;
      threshold *= 1.5;
    } while (leaves.length > MAX_LEAVES || ancestorCount > 280);
    return leaves;
  }
  function geometry(t) {
    const g = new THREE.BufferGeometry(), segments = 24, ll = [], positions = [], indices = [];
    for (let j = 0; j <= segments; j++) for (let i = 0; i <= segments; i++) {
      const lon = t.b.west + (t.b.east - t.b.west) * i / segments;
      const lat = Math.atan(Math.sinh(Math.PI * (1 - 2 * (t.y + j / segments) / 2 ** t.z)));
      ll.push(lon, lat); positions.push(...point(lon, lat));
    }
    for (let j = 0; j < segments; j++) for (let i = 0; i < segments; i++) {
      const a = j * (segments + 1) + i, b = a + segments + 1;
      indices.push(a, b, a + 1, b, b + 1, a + 1);
    }
    g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    g.setAttribute('aLonLat', new THREE.Float32BufferAttribute(ll, 2));
    g.setIndex(indices);
    return g;
  }
  function install(t, bitmap) {
    const texture = new THREE.Texture(bitmap);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    texture.needsUpdate = true;
    const mat = new THREE.ShaderMaterial({
      glslVersion: THREE.GLSL3, side: THREE.DoubleSide,
      uniforms: { ...uniformes, uTesela: { value: texture }, uTile: { value: new THREE.Vector3(t.x, t.y, 2 ** t.z) }, uDetalle: { value: 0 } },
      vertexShader: material.vertexShader, fragmentShader: fragment,
      // Paint ancestors then children. Depth comparison between coincident
      // curved meshes loses precision at street scale and causes z-fighting.
      // The fragment shader explicitly discards the far side of the sphere.
      depthTest: false, depthWrite: false
    });
    const mesh = new THREE.Mesh(geometry(t), mat);
    mesh.frustumCulled = false; mesh.visible = false; mesh.renderOrder = t.z;
    group.add(mesh);
    cache.set(key(t), { mesh, texture, bitmap, touched: stamp, born: performance.now() });
  }
  function evict() {
    const candidates = [...cache].filter(([k]) => !wanted.has(k)).sort((a, b) => a[1].touched - b[1].touched);
    while (cache.size > MAX_CACHE && candidates.length) {
      const [k, v] = candidates.shift();
      group.remove(v.mesh); v.mesh.geometry.dispose(); v.mesh.material.dispose();
      v.texture.dispose(); v.bitmap.close(); cache.delete(k);
    }
  }
  const failures = new Map();
  function pump() {
    while (enabled && active < MAX_ACTIVE && queue.length) {
      const t = queue.shift(), k = key(t);
      if (!wanted.has(k) || cache.has(k) || pending.has(k) || (failures.get(k) || 0) > performance.now()) continue;
      const controller = new AbortController(); pending.set(k, controller); active++;
      const timeout = setTimeout(() => controller.abort(), 12000);
      fetch(`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${t.z}/${t.y}/${t.x}?blankTile=false`, { signal: controller.signal })
        .then(r => { if (!r.ok) throw Error(`Imagery ${r.status}`); return r.blob(); })
        // ImageBitmap ignores Texture.flipY: orient explicitly for WebGL UVs.
        .then(blob => createImageBitmap(blob, { imageOrientation: 'flipY', premultiplyAlpha: 'none' }))
        .then(bitmap => { if (wanted.has(k) && enabled) install(t, bitmap); else bitmap.close(); })
        .catch(() => { if (wanted.has(k) && enabled) { failures.set(k, performance.now() + 60000); stats.failed++; } })
        .finally(() => { clearTimeout(timeout); active--; pending.delete(k); last = -Infinity; evict(); pump(); });
    }
  }
  return {
    update(camera, rotation, state, now) {
      enabled = state.dist < 4 && state.morph < 0.01 && !state.pausado && !document.hidden;
      group.visible = enabled;
      if (!enabled) {
        queue = []; wanted.clear();
        for (const controller of pending.values()) controller.abort();
        if (credit) credit.hidden = true;
        return;
      }
      if (now - last > 180) {
        last = now; stamp++; generation++;
        selected = select(camera, rotation, renderer.domElement.height);
        const requests = new Map();
        for (const leaf of selected) {
          // Request ancestors first so a slow/missing tile never leaves a hole.
          for (let z = 2; z <= leaf.z; z++) {
            const shift = 2 ** (leaf.z - z), t = descriptor(z, Math.floor(leaf.x / shift), Math.floor(leaf.y / shift));
            t.priority = leaf.priority;
            requests.set(key(t), t);
          }
        }
        wanted = new Set(requests.keys());
        for (const [k, until] of failures) if (!wanted.has(k) || until < now) failures.delete(k);
        for (const [k, controller] of pending) if (!wanted.has(k)) controller.abort();
        queue = [...requests.values()].filter(t => !cache.has(key(t))).sort((a, b) => a.z - b.z || a.priority - b.priority);
        for (const [k, v] of cache) if (wanted.has(k)) v.touched = stamp;
        evict(); pump();
      }
      // Render only the best available image for each visible leaf. Ancestors
      // need not be redrawn under fully loaded children (avoids deep overdraw).
      const visibleKeys = new Set();
      for (const leaf of selected) {
        let fading = false;
        for (let z = leaf.z; z >= 2; z--) {
          const factor = 2 ** (leaf.z - z), k = `${z}/${Math.floor(leaf.x / factor)}/${Math.floor(leaf.y / factor)}`;
          const v = cache.get(k);
          if (!v) continue;
          visibleKeys.add(k);
          if (fading || now - v.born >= 350) break;
          fading = true;
        }
      }
      for (const [k, v] of cache) v.mesh.visible = visibleKeys.has(k);
      let visible = 0;
      const blend = THREE.MathUtils.smoothstep(4 - state.dist, 0, 1);
      for (const v of cache.values()) if (v.mesh.visible) {
        v.mesh.material.uniforms.uDetalle.value = blend * Math.min(1, (now - v.born) / 350); visible++;
      }
      if (credit) credit.hidden = visible === 0;
      Object.assign(stats, { level: Math.max(0, ...selected.map(t => t.z)), visible, cached: cache.size, active, generation });
    },
    pause() { enabled = false; queue = []; wanted.clear(); for (const c of pending.values()) c.abort(); },
    stats: () => ({ ...stats })
  };
}
