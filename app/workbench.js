// Presentación del espacio de trabajo. No modifica datos ni métodos estadísticos.
(function () {
  const root = document.documentElement;
  const themeButton = document.getElementById('tema-interfaz');
  const colors = [
    ['#6fd8ff', '#0078a8'], ['#f6c76b', '#996300'], ['#ff7b6b', '#bd3b30'],
    ['#6fe0a0', '#207849'], ['#b493ff', '#7651b5'], ['#b6c8de', '#63778b'],
    ['#6aa8ff', '#286bb8'], ['rgba(106,168,255,.82)', 'rgba(40,107,184,.82)'],
    ['rgba(106,168,255,.9)', 'rgba(40,107,184,.9)'],
    ['rgba(182,200,222,.68)', 'rgba(99,119,139,.68)'],
    ['rgba(255,123,107,.9)', 'rgba(189,59,48,.9)'],
    ['rgba(111,216,255,.15)', 'rgba(0,120,168,.12)']
  ];
  const dark = () => root.dataset.theme === 'dark';
  function datasetColor(value) {
    if (Array.isArray(value)) return value.map(datasetColor);
    const pair = colors.find(pair => pair.includes(value));
    return pair ? pair[dark() ? 0 : 1] : value;
  }
  function chartTheme(chart) {
    const style = getComputedStyle(root);
    const text = style.getPropertyValue('--tenue').trim();
    chart.options.color = text;
    Object.values(chart.options.scales || {}).forEach(scale => {
      if (scale.ticks) scale.ticks.color = text;
      if (scale.title) scale.title.color = text;
      if (scale.grid) scale.grid.color = style.getPropertyValue('--chart-grid').trim();
    });
    if (chart.options.plugins?.legend?.labels) chart.options.plugins.legend.labels.color = text;
    chart.data.datasets.forEach(dataset => {
      ['borderColor', 'backgroundColor', 'pointBackgroundColor', 'pointBorderColor'].forEach(key => {
        if (dataset[key] !== undefined) dataset[key] = datasetColor(dataset[key]);
      });
    });
  }
  if (window.Chart) {
    Chart.register({ id: 'workbenchTheme', beforeUpdate: chartTheme });
  }
  function updateTheme() {
    const isDark = dark();
    themeButton.textContent = isDark ? 'Light theme' : 'Dark theme';
    themeButton.setAttribute('aria-pressed', String(isDark));
    themeButton.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
    if (window.Chart) Object.values(Chart.instances).forEach(chart => chart.update('none'));
  }
  themeButton.addEventListener('click', () => {
    root.dataset.theme = dark() ? 'light' : 'dark';
    try { localStorage.setItem('etd-theme', root.dataset.theme); } catch (e) { /* Private browsing. */ }
    updateTheme();
  });
  updateTheme();
  themeButton.disabled = false;

  const resetButton = document.getElementById('restaurar-paneles');
  resetButton.addEventListener('click', () => {
    document.querySelectorAll('.vista').forEach(panel => panel.classList.remove('minimizada', 'ancha'));
    window.SICC_vista?.soloMapa(false);
    document.dispatchEvent(new CustomEvent('sicc:paneles'));
  });
  resetButton.disabled = false;
  function revealActiveTab() {
    document.querySelector('nav button.activo')?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }
  document.addEventListener('sicc:pestana', () => {
    document.getElementById('workspace-section').textContent = document.getElementById('titulo').textContent;
    revealActiveTab();
  });
  addEventListener('resize', revealActiveTab);
  document.addEventListener('sicc:vista', event => {
    document.getElementById('workspace-view').textContent = event.detail === 'mapa' ? 'World map · 2D' : 'Global scene · 3D';
  });
})();
