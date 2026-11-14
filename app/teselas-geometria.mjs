// Web Mercator on a unit sphere. Pure functions shared by rendering and tests.
export const MAX_ZOOM = 17;
export const MIN_DISTANCE = 1.0002;
export function bounds(z, x, y) {
  const n = 2 ** z, west = x / n * 2 * Math.PI - Math.PI;
  const east = (x + 1) / n * 2 * Math.PI - Math.PI;
  const north = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n)));
  const south = Math.atan(Math.sinh(Math.PI * (1 - 2 * (y + 1) / n)));
  return { west, east, north, south };
}
export function point(lon, lat) {
  return [Math.cos(lat) * Math.sin(lon), Math.sin(lat), Math.cos(lat) * Math.cos(lon)];
}
export function tileAt(lon, lat, z) {
  const n = 2 ** z, phi = Math.max(-85.05112878, Math.min(85.05112878, lat)) * Math.PI / 180;
  return { z, x: Math.floor((((lon + 180) % 360 + 360) % 360) / 360 * n),
    y: Math.max(0, Math.min(n - 1, Math.floor((1 - Math.asinh(Math.tan(phi)) / Math.PI) / 2 * n))) };
}
export function zoomDistance(distance, factor) {
  return Math.max(MIN_DISTANCE, Math.min(34, 1 + (distance - 1) * factor));
}
export function dragDegrees(distance, height, fov = 38) {
  return 2 * (distance - 1) * Math.tan(fov * Math.PI / 360) / height * 180 / Math.PI;
}
