// Local, dependency-free translations. Scientific datasets and exports stay unchanged.
// English message IDs are stable keys; legacy DOM is adapted without replacing elements.
(function () {
  'use strict';
  const KEY = 'gnomon-language';
  const englishTitle = document.title;
  const supported = new Set(['en', 'es']);
  const messages = window.GnomonSpanishMessages || {};
  const canonical = s => String(s).replace(/\s+/g, ' ').trim();
  const spanish = new Map(Object.entries(messages).map(([k, v]) => [canonical(k), v]));
  const english = new Map();
  for (const [en, es] of spanish) if (!english.has(canonical(es))) english.set(canonical(es), en);
  let language = 'en';
  try { const saved = window.localStorage.getItem(KEY); if (supported.has(saved)) language = saved; } catch (_) { /* Storage is optional. */ }
  const textState = new WeakMap(), attributeState = new WeakMap(), chartState = new WeakMap();
  const missing = new Set(), numberFormats = new Map();
  const attrs = ['aria-label', 'title', 'placeholder', 'alt', 'aria-valuetext'];
  const ignore = 'script,style,pre,code,textarea,[data-i18n-ignore],.leaflet-control-attribution';
  function source(value) { const clean = canonical(value); return spanish.has(clean) ? clean : (english.get(clean) || clean); }
  function dynamic(s) {
    let m;
    if (s === 'now') return 'ahora';
    if (s === 'Temperature at 2 m') return 'Temperatura a 2 m';
    if (s === 'Zoom in') return 'Acercar';
    if (s === 'Zoom out') return 'Alejar';
    if (s === 'mm/decade') return 'mm/década';
    if ((m = /^Archived run · (.+)$/.exec(s))) return `Pronóstico caducado · ${m[1]}`;
    if ((m = /^Step (\d+) of (\d+)$/.exec(s))) return `Paso ${m[1]} de ${m[2]}`;
    if ((m = /^(\d+) cities$/.exec(s))) return `${m[1]} ciudades`;
    if ((m = /^from ([-\d.]+)°$/.exec(s))) return `desde ${m[1]}°`;
    if ((m = /^Server responded (\d+)\.$/.exec(s))) return `El servidor respondió ${m[1]}.`;
    if ((m = /^(\d+) questions in (\d+) topics\.$/.exec(s))) return `${m[1]} preguntas en ${m[2]} temas.`;
    if ((m = /^Series: (.+)$/.exec(s))) return `Serie: ${translate(m[1])}`;
    if ((m = /^Trend data source: (.+) \(listed in Sources\)$/.exec(s))) return `Fuente de la tendencia: ${m[1]} (citada en Fuentes)`;
    if ((m = /^mean difference (.+)$/.exec(s))) return `diferencia media ${m[1]}`;
    if ((m = /^([-+−\d.,]+) (.+)\/decade$/.exec(s))) return `${m[1]} ${m[2]}/década`;
    if ((m = /^(.+) in (.+), (\d{4}) to (\d{4}), range (.+) to (.+) (.+), Theil–Sen trend (.+) per decade$/.exec(s))) return `${translate(m[1])} en ${translate(m[2])}, ${m[3]} a ${m[4]}, intervalo ${m[5]} a ${m[6]} ${m[7]}, tendencia Theil–Sen ${m[8]} por década`;
    if ((m = /^(.+) compared with (.+), (\d{4}) to (\d{4}), correlation r = (.+)$/.exec(s))) return `${translate(m[1])} comparado con ${translate(m[2])}, ${m[3]} a ${m[4]}, correlación r = ${m[5]}`;
    if ((m = /^Least-squares slope · (\d+) years$/.exec(s))) return `Pendiente de mínimos cuadrados · ${m[1]} años`;
    if ((m = /^(\d+)% confidence$/.exec(s))) return `${m[1]}% de confianza`;
    if ((m = /^(Observed|Least squares): (.+)$/.exec(s))) return `${m[1] === 'Observed' ? 'Observado' : 'Mínimos cuadrados'}: ${m[2]}`;
    if ((m = /^Reference season (\d+)$/.exec(s))) return `Temporada de referencia ${m[1]}`;
    if ((m = /^Annual precipitation in (.+) from (\d{4}) to (\d{4}), with least-squares \((.+)\) and Theil–Sen \((.+)\) trend lines, (.+)\. Use the left and right arrow keys to step through the years\.$/.exec(s))) return `Precipitación anual en ${translate(m[1])}, ${m[2]} a ${m[3]}, con tendencias de mínimos cuadrados (${m[4]}) y Theil–Sen (${m[5]}), ${translate(m[6])}. Usa las flechas izquierda y derecha para recorrer los años.`;
    if ((m = /^Oceanic Niño Index from (\d{4}) to (\d{4})\. Range (.+) to (.+) °C; latest (.+) is (.+) °C \((.+)\)$/.exec(s))) return `Índice Oceánico de El Niño de ${m[1]} a ${m[2]}. Intervalo ${m[3]} a ${m[4]} °C; el último dato, ${m[5]}, es ${m[6]} °C (${m[7]}).`;
    if ((m = /^Weekly sea temperature anomalies by Niño region from (.+) to (.+); Niño 3\.4 range (.+) to (.+) °C, latest (.+) °C$/.exec(s))) return `Anomalías semanales de temperatura del mar por región Niño, de ${m[1]} a ${m[2]}; intervalo Niño 3.4 ${m[3]} a ${m[4]} °C, último dato ${m[5]} °C`;
    if ((m = /^Projected (warming|precipitation change) from (\d{4}) to (\d{4}) for (.+), active scenario (.+) reaches (.+) by (\d{4}); range across scenarios (.+) to (.+)$/.exec(s))) return `${m[1] === 'warming' ? 'Calentamiento proyectado' : 'Cambio de precipitación proyectado'} de ${m[2]} a ${m[3]} para ${translate(m[4])}; el escenario activo ${m[5]} alcanza ${m[6]} en ${m[7]}; intervalo entre escenarios ${m[8]} a ${m[9]}`;
    if ((m = /^(95% CI|95% confidence interval):? (.+) to (.+)$/.exec(s))) return `IC del 95%: ${m[2]} a ${m[3]}`;
    if ((m = /^(.+) · (now|past|forecast)$/.exec(s))) return `${m[1]} · ${translate(m[2])}`;
    // Translate complete clauses only; never change numeric values or substrings of names.
    const parts = s.split(/( · |\n)/);
    if (parts.length > 1) return parts.map(p => p === ' · ' || p === '\n' ? p : translate(p)).join('');
    return s;
  }
  function translate(value) {
    if (typeof value !== 'string') return value;
    const id = source(value);
    if (language === 'en') return id;
    if (spanish.has(id)) return spanish.get(id);
    const result = dynamic(id);
    if (result === id && /[a-z]{3}/i.test(id) && missing.size < 1000) missing.add(id);
    return result;
  }
  function text(node, force = false) {
    if (!node.parentElement || node.parentElement.closest(ignore) || !node.nodeValue.trim()) return;
    const value = node.nodeValue;
    let record = textState.get(node);
    if (!record || (value !== record.output)) record = { original: value };
    if (!force && record.output === value && record.language === language) return;
    const original = record.original;
    const trimmed = original.trim();
    const translated = translate(trimmed);
    const output = original.slice(0, original.length - original.trimStart().length) + translated + original.slice(original.trimEnd().length);
    Object.assign(record, { output, language }); textState.set(node, record);
    if (output !== value) node.nodeValue = output;
  }
  function attributes(element, force = false) {
    if (element.closest(ignore)) return;
    let records = attributeState.get(element);
    if (!records) { records = {}; attributeState.set(element, records); }
    for (const attr of attrs) {
      const value = element.getAttribute(attr);
      if (value === null) continue;
      let record = records[attr];
      if (!record || value !== record.output) record = { original: value };
      if (!force && record.output === value && record.language === language) continue;
      const output = translate(record.original);
      Object.assign(record, { output, language }); records[attr] = record;
      if (value !== output) element.setAttribute(attr, output);
    }
  }
  function visit(root, force = false) {
    if (root.nodeType === Node.TEXT_NODE) { text(root, force); return; }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    if (root.nodeType === Node.ELEMENT_NODE) { if (root.closest(ignore)) return; attributes(root, force); }
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode(node) { return node.nodeType === Node.ELEMENT_NODE && node.matches(ignore) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; }
    });
    let n; while ((n = walker.nextNode())) n.nodeType === Node.TEXT_NODE ? text(n, force) : attributes(n, force);
  }
  const locale = () => language === 'es' ? 'es-NI' : 'en-US';
  function number(value, options = {}) {
    const key = locale() + JSON.stringify(options);
    if (!numberFormats.has(key)) numberFormats.set(key, new Intl.NumberFormat(locale(), options));
    return numberFormats.get(key).format(value);
  }
  function chartString(owner, key) {
    if (typeof owner?.[key] !== 'string') return;
    let state = chartState.get(owner); if (!state) { state = {}; chartState.set(owner, state); }
    let r = state[key]; if (!r || r.output !== owner[key]) r = { original: owner[key] };
    r.output = translate(r.original); state[key] = r; owner[key] = r.output;
  }
  function chartLabels(chart) {
    for (const dataset of chart.data.datasets || []) chartString(dataset, 'label');
    const options = chart.config.options;
    options.locale = locale();
    for (const axis of Object.values(options.scales || {})) chartString(axis.title, 'text');
    for (const key of ['title', 'subtitle']) chartString(options.plugins?.[key], 'text');
    const callbacks = options.plugins?.tooltip?.callbacks;
    if (callbacks) for (const key of ['label', 'title', 'afterLabel', 'footer']) {
      const fn = callbacks[key];
      if (typeof fn === 'function' && !fn.gnomonTranslated) {
        const wrapped = function (...args) { const result = fn.apply(this, args); return Array.isArray(result) ? result.map(translate) : translate(result); };
        wrapped.gnomonTranslated = true; callbacks[key] = wrapped;
      }
    }
  }
  function controls() {
    for (const button of document.querySelectorAll('[data-language]')) button.setAttribute('aria-pressed', String(button.dataset.language === language));
  }
  function setLanguage(next) {
    if (!supported.has(next)) return false;
    const changed = next !== language; language = next;
    try { window.localStorage.setItem(KEY, language); } catch (_) { /* Continue for this session. */ }
    document.documentElement.lang = language; controls();
    document.title = language === 'es' ? 'Gnomon · Explorador de tendencias de la Tierra' : englishTitle;
    if (changed) {
      document.dispatchEvent(new CustomEvent('gnomon:languagechange', { detail: { language, locale: locale() } }));
      if (window.Chart) for (const chart of Object.values(window.Chart.instances || {})) { chartLabels(chart); chart.update('none'); }
      visit(document.body, true);
      for (const button of document.querySelectorAll('nav button[data-tab]')) button.dataset.nombre = button.textContent.trim();
      const status = document.getElementById('language-status');
      if (status) status.textContent = language === 'es' ? 'Idioma cambiado a español.' : 'Language changed to English.';
      document.dispatchEvent(new CustomEvent('sicc:paneles'));
    }
    return true;
  }
  window.GnomonI18n = Object.freeze({ t: translate, setLanguage, locale, number, language: () => language, missing: () => [...missing] });
  document.documentElement.lang = language;
  document.title = language === 'es' ? 'Gnomon · Explorador de tendencias de la Tierra' : englishTitle;
  controls(); visit(document.body, true);
  document.getElementById('language-switcher')?.addEventListener('click', event => {
    const button = event.target.closest('button[data-language]'); if (button) setLanguage(button.dataset.language);
  });
  if (window.Chart) window.Chart.register({ id: 'gnomon-language', beforeUpdate: chartLabels });
  const pending = new Set(); let scheduled = false;
  new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'childList') for (const node of record.addedNodes) pending.add(node);
      else pending.add(record.target);
    }
    if (!scheduled) { scheduled = true; queueMicrotask(() => {
      scheduled = false; const nodes = [...pending]; pending.clear();
      for (const node of nodes) if (node.isConnected) visit(node);
    }); }
  }).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: attrs });
})();
