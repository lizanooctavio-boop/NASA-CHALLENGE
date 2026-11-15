// Apply the saved theme before rendering to avoid a flash of the default theme.
(() => {
  'use strict';
  const root = document.documentElement;
  const storageKey = 'gnomon-theme';
  const valid = value => value === 'light' || value === 'dark';
  let theme = 'dark';
  try {
    const saved = window.localStorage.getItem(storageKey);
    if (valid(saved)) theme = saved;
  } catch (_) { /* The theme also works when storage is blocked. */ }
  root.dataset.theme = theme;

  function updateButtons() {
    for (const button of document.querySelectorAll('[data-theme-choice]')) {
      button.setAttribute('aria-pressed', String(button.dataset.themeChoice === theme));
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    updateButtons();
    document.getElementById('theme-switcher').addEventListener('click', event => {
      const next = event.target.closest('button')?.dataset.themeChoice;
      if (!valid(next) || next === theme) return;
      theme = next;
      root.dataset.theme = next;
      try { window.localStorage.setItem(storageKey, next); } catch (_) { /* Keep the session choice. */ }
      updateButtons();
      document.getElementById('theme-status').textContent = next === 'light' ? 'Light theme selected.' : 'Dark theme selected.';
      for (const chart of Object.values(window.Chart?.instances || {})) chart.update('none');
    });

    window.Chart?.register({
      id: 'gnomon-theme',
      beforeUpdate(chart) {
        const style = getComputedStyle(root);
        const text = style.getPropertyValue('--tenue').trim();
        const border = style.getPropertyValue('--borde').trim();
        chart.options.color = text;
        chart.options.borderColor = border;
        if (chart.options.plugins.legend?.labels) chart.options.plugins.legend.labels.color = text;
        for (const axis of Object.values(chart.options.scales || {})) {
          if (axis.ticks) axis.ticks.color = text;
          if (axis.title) axis.title.color = text;
          if (axis.grid) axis.grid.color = border;
        }
      }
    });
    for (const chart of Object.values(window.Chart?.instances || {})) chart.update('none');
  });
})();
