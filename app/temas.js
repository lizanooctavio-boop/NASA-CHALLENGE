// Paletas de letras y tipografía. El cristal y la simbología científica se conservan.
(function () {
  'use strict';
  const CLAVE = 'gnomon-ui-theme';
  const PREDETERMINADO = 'pastel-lavanda';
  const PALETAS = [
    ['pastel-lavanda', '01 · Neblina lavanda'],
    ['pastel-menta', '02 · Menta iónica'],
    ['pastel-coral', '03 · Coral fotón'],
    ['pastel-orbita', '04 · Órbita azul pastel'],
    ['pastel-terracota', '05 · Terracota melocotón'],
    ['pastel-rosa', '06 · Cuarzo holográfico'],
    ['pastel-arena', '07 · Arena satelital'],
    ['pastel-lima', '08 · Lima de gravedad cero'],
    ['royal', '09 · Morado Real · Royal Dusk'],
    ['nordic', '10 · Azul Hielo · Nordic Frost']
  ];
  const valida = valor => PALETAS.some(([id]) => id === valor);
  let actual = PREDETERMINADO;
  try {
    const guardada = localStorage.getItem(CLAVE);
    if (valida(guardada)) actual = guardada;
  } catch (e) { /* Almacenamiento bloqueado: la selección funciona durante esta sesión. */ }
  // Se aplica antes de dibujar la página para evitar un destello con otra paleta.
  document.documentElement.dataset.uiTheme = actual;

  document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('style-select');
    const estado = document.getElementById('palette-status');
    if (!select || !estado) return;
    for (const [id, nombre] of PALETAS) {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = nombre;
      select.append(option);
    }
    select.value = actual;
    select.addEventListener('change', () => {
      if (!valida(select.value)) return;
      actual = select.value;
      document.documentElement.dataset.uiTheme = actual;
      try {
        localStorage.setItem(CLAVE, actual);
        estado.textContent = 'Preferencia guardada en este navegador.';
      } catch (e) {
        estado.textContent = 'Paleta aplicada para esta sesión.';
      }
    });

    const acciones = document.querySelector('header .acciones');
    if (!acciones) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.id = 'estilo-visual';
    button.textContent = 'Estilo visual';
    button.setAttribute('aria-controls', 'configuracion');
    button.addEventListener('click', () => {
      document.querySelector('nav [data-tab="configuracion"]')?.click();
      select.focus({ preventScroll: true });
    });
    const tour = document.getElementById('menu-tour');
    if (tour) tour.after(button);
    else acciones.append(button);

    // Las fuentes se cargan después de iniciar la interfaz: una conexión lenta no bloquea la app.
    const fuentes = document.createElement('link');
    fuentes.rel = 'stylesheet';
    fuentes.href = 'https://fonts.googleapis.com/css2?family=DM+Sans%3Awght%40400%3B500%3B600%3B700&family=IBM+Plex+Mono%3Awght%40400%3B500&family=IBM+Plex+Sans%3Awght%40400%3B500%3B600%3B700&family=Inter%3Awght%40400%3B500%3B600%3B700%3B800&family=JetBrains+Mono%3Awght%40400%3B500&family=Lora%3Awght%40400%3B600%3B700&family=Manrope%3Awght%40400%3B600%3B800&family=Merriweather%3Awght%40400%3B700&family=Open+Sans%3Awght%40400%3B500%3B600&family=Outfit%3Awght%40400%3B600%3B700&family=Plus+Jakarta+Sans%3Awght%40400%3B500%3B600%3B700&family=Rubik%3Awght%40400%3B500%3B600&family=Space+Grotesk%3Awght%40400%3B500%3B700&family=Syne%3Awght%40400%3B600%3B700&family=Work+Sans%3Awght%40400%3B500%3B600&display=swap';
    document.head.append(fuentes);
  });
})();
