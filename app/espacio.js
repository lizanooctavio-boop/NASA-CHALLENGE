// Escena espacial de fondo: Tierra (Blue Marble y luces nocturnas VIIRS), Luna, Sol y estrellas.
// La Tierra usa un shader que interpola cada vértice entre la esfera y el plano Mercator de Leaflet,
// así el globo se aplana con América al centro y encaja píxel a píxel con el mapa 2D.
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js';

const RAD = Math.PI / 180;
const LON_CENTRO = -80;            // costura de la malla en 100° E: América queda al centro del plano
const DIST_REPOSO = 4.9, DIST_MIN = 1.28, DIST_MAX = 34, DIST_INTRO = 30, DIST_PLANO = 3.1;
const FOV = 38;
const reducido = matchMedia('(prefers-reduced-motion: reduce)').matches;

const canvas = document.getElementById('espacio');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.outputColorSpace = THREE.SRGBColorSpace;
const escena = new THREE.Scene();
escena.background = new THREE.Color(0x01030a);
const camara = new THREE.PerspectiveCamera(FOV, 1, 0.02, 4000);

// Iluminación artística: el Sol se ve arriba a la derecha, detrás del limbo, y la luz llega por delante
// para que la cara visible conserve el día.
const LUZ = new THREE.Vector3(0.62, 0.3, 0.72).normalize();
const SOL = new THREE.Vector3(0.17, 0.235, -0.96).normalize().multiplyScalar(900);

const cargador = new THREE.TextureLoader();
function textura(ruta, srgb = true) {
  return new Promise(ok => cargador.load(ruta, t => {
    if (srgb) t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = renderer.capabilities.getMaxAnisotropy();
    ok(t);
  }, undefined, () => ok(null)));
}
const vacia = new THREE.DataTexture(new Uint8Array([0, 0, 0, 0]), 1, 1);
vacia.needsUpdate = true;

// ---------------------------------------------------------------- estrellas
function estrellas(n, tam, brillo) {
  const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const u = Math.random() * 2 - 1, a = Math.random() * Math.PI * 2, r = 2600;
    const s = Math.sqrt(1 - u * u);
    pos.set([r * s * Math.cos(a), r * u, r * s * Math.sin(a)], i * 3);
    const t = Math.random(), b = brillo * (0.45 + Math.random() * 0.55);
    col.set(t < 0.15 ? [b, b * 0.86, b * 0.7] : t < 0.35 ? [b * 0.78, b * 0.86, b] : [b, b, b], i * 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return new THREE.Points(g, new THREE.PointsMaterial({ size: tam, sizeAttenuation: false, vertexColors: true, depthWrite: false }));
}
escena.add(estrellas(9000, 1.1, 0.75), estrellas(900, 2.1, 1));

// ---------------------------------------------------------------- Sol
function halo(stops, tam = 256) {
  const c = document.createElement('canvas');
  c.width = c.height = tam;
  const x = c.getContext('2d'), g = x.createRadialGradient(tam / 2, tam / 2, 0, tam / 2, tam / 2, tam / 2);
  stops.forEach(([p, color]) => g.addColorStop(p, color));
  x.fillStyle = g;
  x.fillRect(0, 0, tam, tam);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function sprite(tex, escala, opacidad = 1) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: opacidad }));
  s.scale.setScalar(escala);
  s.position.copy(SOL);
  return s;
}
const sol = new THREE.Group();
sol.add(
  sprite(halo([[0, 'rgba(255,190,120,.55)'], [.18, 'rgba(255,140,60,.18)'], [.5, 'rgba(255,110,40,.05)'], [1, 'rgba(0,0,0,0)']]), 900),
  sprite(halo([[0, 'rgba(255,255,250,1)'], [.12, 'rgba(255,248,225,1)'], [.3, 'rgba(255,210,150,.55)'], [.6, 'rgba(255,160,80,.12)'], [1, 'rgba(0,0,0,0)']]), 150)
);
escena.add(sol);

// ---------------------------------------------------------------- Luna
const luna = new THREE.Mesh(new THREE.SphereGeometry(0.27, 96, 64), new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, color: 0x4a4a4a }));
const luzLuna = new THREE.DirectionalLight(0xfff4e6, 3.2);
luzLuna.position.copy(LUZ).multiplyScalar(10);
escena.add(luna, luzLuna, new THREE.AmbientLight(0x223344, 0.08));
// La Luna queda abajo a la izquierda del globo, en el hueco entre el panel y la Tierra; deriva lentamente.
let anguloLuna = 0;
function moverLuna(dt) {
  anguloLuna += dt * 0.02;
  luna.position.set(-2.05 + Math.sin(anguloLuna) * 0.12, -1.05 + Math.cos(anguloLuna * 0.7) * 0.06, -2.6);
  luna.rotation.y += dt * 0.01;
}

// ---------------------------------------------------------------- Tierra
const NX = 360, NY = 180;
function mallaTierra() {
  const n = (NX + 1) * (NY + 1), lonlat = new Float32Array(n * 2), pos = new Float32Array(n * 3), idx = [];
  for (let j = 0; j <= NY; j++) for (let i = 0; i <= NX; i++) {
    const k = j * (NX + 1) + i, lon = (LON_CENTRO - 180 + 360 * i / NX) * RAD, lat = (90 - 180 * j / NY) * RAD;
    lonlat[k * 2] = lon;
    lonlat[k * 2 + 1] = lat;
    pos.set([Math.cos(lat) * Math.sin(lon), Math.sin(lat), Math.cos(lat) * Math.cos(lon)], k * 3);
  }
  for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
    const a = j * (NX + 1) + i, b = a + NX + 1;
    idx.push(a, b, a + 1, b, b + 1, a + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('aLonLat', new THREE.BufferAttribute(lonlat, 2));
  g.setIndex(idx);
  return g;
}

const uniformes = {
  uDia: { value: vacia }, uNoche: { value: vacia }, uMeteo: { value: vacia }, uViento: { value: vacia },
  uMeteoOp: { value: 0 }, uVientoOn: { value: 0 }, uMorph: { value: 0 }, uK: { value: 1 },
  uLonVista: { value: LON_CENTRO * RAD }, uMercVista: { value: 0 }, uRot: { value: new THREE.Matrix3() },
  uLuz: { value: LUZ }, uCamPos: { value: new THREE.Vector3() }, uListo: { value: 0 }
};
const materialTierra = new THREE.ShaderMaterial({
  glslVersion: THREE.GLSL3, side: THREE.DoubleSide, uniforms: uniformes,
  vertexShader: /* glsl */`
    in vec2 aLonLat;
    uniform mat3 uRot; uniform float uMorph, uK, uLonVista, uMercVista;
    out vec2 vLonLat; out vec3 vNormal; out vec3 vPos;
    void main() {
      float lon = aLonLat.x, lat = aLonLat.y;
      vec3 esfera = uRot * vec3(cos(lat) * sin(lon), sin(lat), cos(lat) * cos(lon));
      float y = log(tan(0.78539816 + clamp(lat, -1.4844, 1.4844) * 0.5));
      vec3 plano = vec3((lon - uLonVista) * uK, (y - uMercVista) * uK, 0.0);
      vec3 p = mix(esfera, plano, uMorph);
      vNormal = normalize(mix(esfera, vec3(0.0, 0.0, 1.0), uMorph));
      vLonLat = aLonLat;
      vPos = p;
      gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
    }`,
  fragmentShader: /* glsl */`
    precision highp float;
    uniform sampler2D uDia, uNoche, uMeteo, uViento;
    uniform float uMeteoOp, uVientoOn, uMorph, uListo;
    uniform vec3 uLuz, uCamPos;
    in vec2 vLonLat; in vec3 vNormal; in vec3 vPos;
    out vec4 colorSalida;
    void main() {
      float u = (vLonLat.x + 3.14159265) / 6.28318531;
      vec2 uv = vec2(fract(u), 0.5 + vLonLat.y / 3.14159265);
      vec2 dx = dFdx(vec2(u, uv.y)), dy = dFdy(vec2(u, uv.y));
      vec3 dia = textureGrad(uDia, uv, dx, dy).rgb;
      vec3 noche = textureGrad(uNoche, uv, dx, dy).rgb;
      vec3 n = normalize(vNormal), v = normalize(uCamPos - vPos);
      float d = dot(n, uLuz);
      float diurno = mix(smoothstep(-0.14, 0.3, d), 1.0, uMorph);
      vec3 col = dia * mix(0.05 + 1.12 * max(d, 0.0), 1.0, uMorph);
      float l = dot(noche, vec3(0.3, 0.59, 0.11));
      vec3 luces = noche * 0.35 + vec3(1.0, 0.78, 0.45) * smoothstep(0.06, 0.4, l) * 1.6;
      col = mix(luces, col, diurno);
      float agua = 1.0 - smoothstep(0.02, 0.07, max(dia.r, dia.g));
      float brillo = pow(max(dot(reflect(-uLuz, n), v), 0.0), 140.0) * agua * (1.0 - uMorph);
      col += vec3(1.0, 0.93, 0.8) * brillo * 0.22;
      vec4 m = textureGrad(uMeteo, uv, dx, dy);
      col = mix(col, m.rgb * mix(0.38, 1.0, diurno), m.a * uMeteoOp);
      float w = textureGrad(uViento, uv, dx, dy).a;
      col = mix(col, vec3(1.0), w * uVientoOn * mix(0.55, 0.95, diurno));
      float f = pow(1.0 - max(dot(n, v), 0.0), 2.6) * (1.0 - uMorph);
      col += vec3(0.32, 0.58, 1.0) * f * (0.12 + 0.9 * smoothstep(-0.25, 0.6, d));
      colorSalida = linearToOutputTexel(vec4(col * uListo, 1.0));
    }`
});
const tierra = new THREE.Mesh(mallaTierra(), materialTierra);
tierra.frustumCulled = false;
escena.add(tierra);

const atmosfera = new THREE.Mesh(new THREE.SphereGeometry(1.075, 96, 64), new THREE.ShaderMaterial({
  side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
  uniforms: { uOpacidad: { value: 1 }, uLuz: { value: LUZ } },
  vertexShader: `varying vec3 vN; varying vec3 vW;
    void main(){ vN = normalize(normalMatrix * normal); vW = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform float uOpacidad; uniform vec3 uLuz; varying vec3 vN; varying vec3 vW;
    void main(){ float i = pow(max(0.0, 0.74 - dot(vN, vec3(0.0,0.0,1.0))), 3.2);
      float lado = 0.25 + 0.75 * smoothstep(-0.4, 0.5, dot(vW, uLuz));
      gl_FragColor = vec4(vec3(0.3, 0.58, 1.0) * i * 2.4 * lado, 1.0) * uOpacidad; }`
}));
escena.add(atmosfera);

// ---------------------------------------------------------------- partículas de viento (lienzo equirectangular)
const VW = 1600, VH = 800;
const lienzoViento = document.createElement('canvas');
lienzoViento.width = VW;
lienzoViento.height = VH;
const ctxV = lienzoViento.getContext('2d');
const texViento = new THREE.CanvasTexture(lienzoViento);
const NP = reducido ? 1800 : 4200;
const pLon = new Float32Array(NP), pLat = new Float32Array(NP), pEdad = new Float32Array(NP);
let muestraU = null, muestraV = null, vientoActivo = false;
function muestreador(meta, M) {
  if (!M || !meta?.latitudes?.length) return null;
  const lat0 = meta.latitudes[0], lon0 = meta.longitudes[0], dy = meta.latitudes[1] - lat0, dx = meta.longitudes[1] - lon0, n = meta.longitudes.length;
  return (lon, lat) => {
    const y = (lat - lat0) / dy, x = (lon - lon0) / dx;
    if (y < 0 || y > M.length - 1) return null;
    const i = Math.min(Math.floor(y), M.length - 2), j0 = Math.floor(x), j = (j0 % n + n) % n, k = (j + 1) % n, a = y - i, b = x - j0;
    const q = [M[i][j], M[i][k], M[i + 1][j], M[i + 1][k]];
    if (q.some(v => v == null)) return null;
    return ((1 - b) * q[0] + b * q[1]) * (1 - a) + ((1 - b) * q[2] + b * q[3]) * a;
  };
}
function sembrar(k) {
  pLon[k] = Math.random() * 360 - 180;
  pLat[k] = Math.asin(Math.random() * 2 - 1) / RAD;
  pEdad[k] = 40 + Math.random() * 120;
}
for (let k = 0; k < NP; k++) sembrar(k);
function pasoViento() {
  if (!vientoActivo) return;
  ctxV.globalCompositeOperation = 'destination-out';
  ctxV.fillStyle = 'rgba(0,0,0,.075)';
  ctxV.fillRect(0, 0, VW, VH);
  ctxV.globalCompositeOperation = 'source-over';
  ctxV.strokeStyle = 'rgba(255,255,255,.9)';
  ctxV.lineWidth = 1.25;
  ctxV.beginPath();
  for (let k = 0; k < NP; k++) {
    if (--pEdad[k] <= 0 || Math.abs(pLat[k]) > 84) { sembrar(k); continue; }
    const a = muestraU(pLon[k], pLat[k]), b = muestraV(pLon[k], pLat[k]);
    if (a == null || b == null) { sembrar(k); continue; }
    const lon = pLon[k] + a * 0.05 / Math.max(0.2, Math.cos(pLat[k] * RAD)), lat = pLat[k] + b * 0.05;
    if (Math.abs(lon) < 180) {
      ctxV.moveTo((pLon[k] + 180) / 360 * VW, (90 - pLat[k]) / 180 * VH);
      ctxV.lineTo((lon + 180) / 360 * VW, (90 - lat) / 180 * VH);
      pLon[k] = lon;
    } else pLon[k] = ((lon + 540) % 360) - 180;
    pLat[k] = lat;
  }
  ctxV.stroke();
  texViento.needsUpdate = true;
}

// ---------------------------------------------------------------- estado de cámara y orientación
const estado = {
  lon: -150, lat: 12, dist: DIST_INTRO, desp: 0, despObjetivo: 0, morph: 0, zoom: 3,
  velLon: 0, velLat: 0, ultimoGesto: 0, animando: false, pausado: false, intro: true
};
const rotacion = new THREE.Matrix4();
function orientar() {
  rotacion.makeRotationY(-estado.lon * RAD).premultiply(new THREE.Matrix4().makeRotationX(estado.lat * RAD));
  uniformes.uRot.value.setFromMatrix4(rotacion);
}
function tamano() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false);
  camara.aspect = w / h;
  camara.updateProjectionMatrix();
}
addEventListener('resize', () => { tamano(); dibujar(); });
tamano();

function encuadrar() {
  camara.position.set(0, 0, estado.dist);
  camara.lookAt(0, 0, 0);
  const w = innerWidth, h = innerHeight;
  if (Math.abs(estado.desp) > 0.5) camara.setViewOffset(w, h, -estado.desp, 0, w, h);
  else camara.clearViewOffset();
  uniformes.uCamPos.value.copy(camara.position);
  // Unidades del mundo por radián Mercator, idénticas a la escala de Leaflet a este zoom
  const pxPorRad = 256 * 2 ** estado.zoom / (2 * Math.PI);
  uniformes.uK.value = pxPorRad * 2 * estado.dist * Math.tan(FOV * RAD / 2) / h;
  uniformes.uMorph.value = estado.morph;
  atmosfera.material.uniforms.uOpacidad.value = Math.max(0, 1 - estado.morph * 3);
  atmosfera.visible = estado.morph < 0.34;
  luna.visible = estado.morph < 0.05;
  sol.visible = estado.morph < 0.6;
  orientar();
}
function dibujar() {
  encuadrar();
  renderer.render(escena, camara);
}

let anterior = performance.now(), cuadro = 0;
function bucle(ahora) {
  cuadro = 0;
  if (estado.pausado || document.hidden) return;
  const dt = Math.min(0.1, (ahora - anterior) / 1000);
  anterior = ahora;
  if (!estado.animando) {
    if (Math.abs(estado.velLon) + Math.abs(estado.velLat) > 0.001) {
      estado.lon += estado.velLon;
      estado.lat = Math.max(-80, Math.min(80, estado.lat + estado.velLat));
      estado.velLon *= 0.93;
      estado.velLat *= 0.93;
    } else if (!reducido && !estado.intro && ahora - estado.ultimoGesto > 7000) {
      estado.lon += dt * 1.1;
    }
    estado.desp += (estado.despObjetivo - estado.desp) * Math.min(1, dt * 5);
  }
  moverLuna(dt);
  pasoViento();
  dibujar();
  cuadro = requestAnimationFrame(bucle);
}
function arrancar() {
  if (!cuadro && !estado.pausado) { anterior = performance.now(); cuadro = requestAnimationFrame(bucle); }
}
document.addEventListener('visibilitychange', arrancar);

// ---------------------------------------------------------------- animaciones
const suave = t => t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
const salida = t => 1 - (1 - t) ** 3;
function animar(ms, paso) {
  estado.animando = true;
  return new Promise(ok => {
    const t0 = performance.now();
    function f(ahora) {
      const t = Math.min(1, (ahora - t0) / (reducido ? Math.min(ms, 300) : ms));
      paso(t);
      if (t < 1) requestAnimationFrame(f);
      else { estado.animando = false; ok(); }
    }
    requestAnimationFrame(f);
  });
}
const lerp = (a, b, t) => a + (b - a) * t;
const corto = (a, b) => a + ((((b - a) % 360) + 540) % 360 - 180); // destino equivalente más cercano

function intro() {
  const l0 = estado.lon, l1 = -84;
  return animar(3600, t => {
    const e = salida(t);
    estado.dist = Math.exp(lerp(Math.log(DIST_INTRO), Math.log(DIST_REPOSO), e));
    estado.lon = lerp(l0, l1, e);
    estado.desp = lerp(0, estado.despObjetivo, e);
  }).then(() => { estado.intro = false; estado.ultimoGesto = performance.now(); });
}

// Lleva el globo al plano Mercator con el mismo centro y zoom que tendrá Leaflet.
function aMapa({ lon, lat, zoom }) {
  estado.velLon = estado.velLat = 0;
  const l0 = estado.lon, la0 = estado.lat, d0 = estado.dist, s0 = estado.desp;
  const lonVista = ((lon - LON_CENTRO + 540) % 360) - 180 + LON_CENTRO;
  const l1 = corto(l0, lon);
  estado.zoom = zoom;
  uniformes.uLonVista.value = lonVista * RAD;
  uniformes.uMercVista.value = Math.log(Math.tan(Math.PI / 4 + Math.max(-85, Math.min(85, lat)) * RAD / 2));
  return animar(1900, t => {
    const e = suave(Math.min(1, t / 0.75));
    estado.lon = lerp(l0, l1, e);
    estado.lat = lerp(la0, lat, e);
    estado.dist = lerp(d0, DIST_PLANO, e);
    estado.desp = lerp(s0, 0, e);
    estado.morph = suave(Math.max(0, (t - 0.28) / 0.72));
    dibujar();
  });
}

// Recorrido inverso: parte del plano que coincide con la vista actual de Leaflet.
function aGlobo({ lon, lat, zoom }) {
  estado.pausado = false;
  const lonVista = ((lon - LON_CENTRO + 540) % 360) - 180 + LON_CENTRO;
  estado.zoom = zoom;
  estado.lon = lon;
  estado.lat = Math.max(-60, Math.min(60, lat));
  estado.dist = DIST_PLANO;
  estado.desp = 0;
  estado.morph = 1;
  uniformes.uLonVista.value = lonVista * RAD;
  uniformes.uMercVista.value = Math.log(Math.tan(Math.PI / 4 + Math.max(-85, Math.min(85, lat)) * RAD / 2));
  dibujar();
  const la0 = estado.lat;
  return {
    listo: Promise.resolve(),
    animar: () => animar(1800, t => {
      estado.morph = 1 - suave(Math.min(1, t / 0.72));
      const e = suave(Math.max(0, (t - 0.25) / 0.75));
      estado.dist = lerp(DIST_PLANO, DIST_REPOSO, e);
      estado.lat = lerp(la0, Math.max(-25, Math.min(35, la0)), e);
      estado.desp = lerp(0, estado.despObjetivo, e);
      dibujar();
    }).then(() => { estado.ultimoGesto = performance.now(); arrancar(); })
  };
}

// ---------------------------------------------------------------- interacción
const punteros = new Map();
let gesto = null, alElegir = null;
function gradosPorPixel() { return (estado.dist - 0.75) * 0.075; }
canvas.addEventListener('pointerdown', e => {
  if (estado.animando || estado.morph > 0) return;
  canvas.setPointerCapture(e.pointerId);
  punteros.set(e.pointerId, { x: e.clientX, y: e.clientY });
  gesto = { x0: e.clientX, y0: e.clientY, movido: false, t: performance.now() };
  estado.velLon = estado.velLat = 0;
  estado.ultimoGesto = performance.now();
});
canvas.addEventListener('pointermove', e => {
  const p = punteros.get(e.pointerId);
  if (!p || !gesto) return;
  if (punteros.size === 2) {
    const [a, b] = [...punteros.values()], antes = Math.hypot(a.x - b.x, a.y - b.y);
    p.x = e.clientX; p.y = e.clientY;
    const [c, d] = [...punteros.values()], ahora = Math.hypot(c.x - d.x, c.y - d.y);
    if (antes > 0) acercar(antes / ahora);
    gesto.movido = true;
    return;
  }
  const dx = e.clientX - p.x, dy = e.clientY - p.y;
  p.x = e.clientX; p.y = e.clientY;
  if (Math.hypot(e.clientX - gesto.x0, e.clientY - gesto.y0) > 4) gesto.movido = true;
  const k = gradosPorPixel();
  estado.lon -= dx * k;
  estado.lat = Math.max(-80, Math.min(80, estado.lat + dy * k));
  estado.velLon = -dx * k * 0.6;
  estado.velLat = dy * k * 0.6;
  estado.ultimoGesto = performance.now();
});
function soltar(e) {
  if (!punteros.has(e.pointerId)) return;
  punteros.delete(e.pointerId);
  if (gesto && !gesto.movido && punteros.size === 0 && e.type === 'pointerup') elegir(e);
  if (!punteros.size) gesto = null;
}
canvas.addEventListener('pointerup', soltar);
canvas.addEventListener('pointercancel', soltar);
function acercar(factor) {
  estado.dist = Math.max(DIST_MIN, Math.min(DIST_MAX, estado.dist * factor));
  estado.ultimoGesto = performance.now();
}
canvas.addEventListener('wheel', e => {
  if (estado.animando || estado.morph > 0) return;
  e.preventDefault();
  acercar(Math.exp(e.deltaY * (e.deltaMode ? 0.05 : 0.0012)));
}, { passive: false });
canvas.addEventListener('keydown', e => {
  const m = { ArrowLeft: [-8, 0], ArrowRight: [8, 0], ArrowUp: [0, 6], ArrowDown: [0, -6] }[e.key];
  if (m) { e.preventDefault(); estado.lon += m[0]; estado.lat = Math.max(-80, Math.min(80, estado.lat + m[1])); }
  else if (e.key === '+' || e.key === '=') acercar(0.85);
  else if (e.key === '-') acercar(1.18);
  else if ((e.key === 'Enter' || e.key === ' ') && alElegir) { e.preventDefault(); alElegir(estado.lat, ((estado.lon + 540) % 360) - 180); return; }
  else return;
  estado.ultimoGesto = performance.now();
});

const rayo = new THREE.Raycaster(), esfera = new THREE.Sphere(new THREE.Vector3(), 1), impacto = new THREE.Vector3();
function elegir(e) {
  if (!alElegir) return;
  rayo.setFromCamera(new THREE.Vector2(e.clientX / innerWidth * 2 - 1, -e.clientY / innerHeight * 2 + 1), camara);
  if (!rayo.ray.intersectSphere(esfera, impacto)) return;
  const local = impacto.clone().applyMatrix4(rotacion.clone().invert());
  const lat = Math.asin(Math.max(-1, Math.min(1, local.y))) / RAD, lon = Math.atan2(local.x, local.z) / RAD;
  alElegir(lat, ((lon + 540) % 360) - 180);
}

// ---------------------------------------------------------------- arranque
const [dia, noche, mapaLuna] = await Promise.all([
  textura('assets/texturas/tierra-dia.jpg'), textura('assets/texturas/tierra-noche.jpg'), textura('assets/texturas/luna.jpg')
]);
if (dia) uniformes.uDia.value = dia;
if (noche) uniformes.uNoche.value = noche;
if (mapaLuna) { luna.material.map = mapaLuna; luna.material.color.set(0xffffff); luna.material.needsUpdate = true; }
uniformes.uListo.value = 1;
canvas.classList.add('listo');

let texMeteo = null;
window.Espacio = {
  meteo(lienzo, opacidad) {
    texMeteo?.dispose();
    texMeteo = null;
    if (lienzo) {
      texMeteo = new THREE.CanvasTexture(lienzo);
      texMeteo.colorSpace = THREE.SRGBColorSpace;
      uniformes.uMeteo.value = texMeteo;
    } else uniformes.uMeteo.value = vacia;
    uniformes.uMeteoOp.value = lienzo ? opacidad : 0;
  },
  opacidad(v) { if (texMeteo) uniformes.uMeteoOp.value = v; },
  viento(meta, campo, activo) {
    muestraU = campo ? muestreador(meta, campo.viento_u_ms) : null;
    muestraV = campo ? muestreador(meta, campo.viento_v_ms) : null;
    vientoActivo = Boolean(activo && muestraU && muestraV);
    uniformes.uVientoOn.value = vientoActivo ? 1 : 0;
    uniformes.uViento.value = vientoActivo ? texViento : vacia;
    if (!vientoActivo) ctxV.clearRect(0, 0, VW, VH);
  },
  desplazar(px) { estado.despObjetivo = px; if (estado.intro) estado.desp = 0; },
  alElegir(f) { alElegir = f; },
  aMapa,
  aGlobo,
  pausar(v) { estado.pausado = v; if (!v) arrancar(); },
  centro() { return { lon: ((estado.lon + 540) % 360) - 180, lat: estado.lat, dist: estado.dist }; },
  estado: () => ({ ...estado })
};
document.dispatchEvent(new CustomEvent('espacio:listo'));
arrancar();
if (reducido) { estado.dist = DIST_REPOSO; estado.lon = -84; estado.intro = false; estado.desp = estado.despObjetivo; }
else intro();
