// Run this async function in DevTools on the local app after Investigate has loaded.
// Functional UX regression checks; this is not a security sandbox or exploit harness.
async function validarI18nLocal() {
  const checks = [];
  const check = (name, passed) => checks.push({ name, passed: !!passed });
  const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const i18n = window.GnomonI18n;
  if (!i18n || !window.SICC_investigar?.estado().cargado) throw Error('Open Investigate first.');
  const selection = JSON.stringify(window.SICC_investigar.estado().sel);
  const weather = JSON.stringify(window.SICC_campo.estado());
  const canvas = document.getElementById('espacio'), map = document.getElementById('mapa');
  document.getElementById('nav-configuracion').click();
  check('Settings opens from sidebar', !document.getElementById('configuracion').hidden && location.hash === '#configuracion');
  check('Preferences are in Settings', [...document.querySelectorAll('[data-language],[data-theme-choice]')].every(button => button.closest('#configuracion')));
  document.querySelector('[data-theme-choice="light"]').click(); await frame();
  check('Light theme selected', document.documentElement.dataset.theme === 'light' && document.querySelector('[data-theme-choice="light"]').getAttribute('aria-pressed') === 'true');
  document.querySelector('[data-theme-choice="dark"]').click(); await frame();
  check('Dark theme selected and saved', document.documentElement.dataset.theme === 'dark' && localStorage.getItem('gnomon-theme') === 'dark');
  document.querySelector('[data-language="en"]').click(); await frame();
  check('EN navigation', document.querySelector('nav [data-tab="investigar"]').textContent.trim() === 'Investigate');
  document.querySelector('[data-language="es"]').click(); await frame();
  check('ES navigation', document.querySelector('nav [data-tab="investigar"]').textContent.trim() === 'Investigar');
  check('Document lang', document.documentElement.lang === 'es');
  check('Selection preserved', JSON.stringify(window.SICC_investigar.estado().sel) === selection);
  check('Weather layer and time preserved', JSON.stringify(window.SICC_campo.estado()) === weather);
  check('Canvas and map identity preserved', canvas === document.getElementById('espacio') && map === document.getElementById('mapa'));
  check('Preference persisted', localStorage.getItem('gnomon-language') === 'es');
  check('Unsupported language rejected', i18n.setLanguage('fr') === false && i18n.language() === 'es');
  const dynamic = document.createElement('p'); dynamic.className = 'sr-only'; dynamic.textContent = 'Weather'; document.body.append(dynamic);
  await frame(); check('Dynamic text translated', dynamic.textContent === 'Tiempo');
  i18n.setLanguage('en'); await frame(); check('English restored', dynamic.textContent === 'Weather'); dynamic.remove();
  async function csv() {
    const original = URL.createObjectURL;
    let timer;
    try {
      return await new Promise((resolve, reject) => {
        timer = setTimeout(() => reject(Error('CSV export timeout')), 3000);
        URL.createObjectURL = function (blob) {
          if (blob.type.startsWith('text/csv')) blob.text().then(resolve, reject);
          return original.call(URL, blob);
        };
        document.getElementById('inv-csv').click();
      });
    } finally { clearTimeout(timer); URL.createObjectURL = original; }
  }
  document.querySelector('nav [data-tab="investigar"]').click(); await frame();
  const enCSV = await csv(); i18n.setLanguage('es'); await frame(); const esCSV = await csv();
  check('CSV scientific data unchanged', enCSV === esCSV && enCSV.includes('2001'));
  check('Spanish button pressed', document.querySelector('[data-language="es"]').getAttribute('aria-pressed') === 'true');
  await window.SICC_ayuda.cargar(); await frame();
  check('Help follows global language', document.getElementById('ayuda-titulo').textContent.includes('ayudarte'));
  const status = document.getElementById('indicador-texto').textContent;
  if (status.includes('caducado')) {
    check('Expired snapshot does not say now', !/\bnow\b|\bahora\b/i.test(document.getElementById('lt-etiqueta').textContent));
    check('Now disabled for expired snapshot', document.getElementById('lt-ahora').disabled);
  }
  return { checks, passed: checks.filter(c => c.passed).length, total: checks.length, language: i18n.language(), sourceDataUnchanged: enCSV === esCSV };
}
