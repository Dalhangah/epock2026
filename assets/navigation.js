/* Native details work without JavaScript; deep links reveal closed ancestors. */
(() => {
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
