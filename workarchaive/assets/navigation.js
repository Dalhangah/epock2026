/* Native details work without JavaScript; deep links reveal closed ancestors. */
(() => {
  const header = document.querySelector('.site-header');
  const subnav = document.querySelector('.stage-subnav');
  function sizeHeader() {
    if (header) document.documentElement.style.setProperty('--sticky-header-offset', `${Math.ceil(header.getBoundingClientRect().height) + 20}px`);
  }
  sizeHeader();
  if (header && 'ResizeObserver' in window) new ResizeObserver(sizeHeader).observe(header);
  if (subnav) {
    const active = subnav.querySelector('[aria-current="page"]');
    if (active) {
      const item = active.getBoundingClientRect();
      const strip = subnav.getBoundingClientRect();
      subnav.scrollLeft += item.left - strip.left - Math.max(16, (strip.width - item.width) / 2);
    }
    subnav.addEventListener('keydown', event => {
      if (event.target !== subnav) return;
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
        event.preventDefault();
        subnav.scrollBy({left: event.key === 'ArrowRight' ? 180 : -180, behavior: 'auto'});
      }
    });
  }
  function revealHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    let node = target;
    while (node) {
      if (node.tagName === 'DETAILS') node.open = true;
      node = node.parentElement;
    }
    requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
  }
  window.addEventListener('hashchange', revealHash);
  revealHash();
  let previouslyClosed = [];
  window.addEventListener('beforeprint', () => {
    previouslyClosed = [...document.querySelectorAll('details:not([open])')];
    previouslyClosed.forEach(item => item.open = true);
  });
  window.addEventListener('afterprint', () => previouslyClosed.forEach(item => item.open = false));
})();
