/* Stable identity/order; stage pages feature the latest recorded content update. */
(() => {
  const main = document.querySelector('main[data-new-task]');
  if (!main) return;
  const tasks = [...main.querySelectorAll(':scope > details.task-accordion')];
  if (!tasks.length) return;
  const priority = task => task.id === main.dataset.newTask ? -2000 : task.id === main.dataset.nextTask ? -1000 : Number(task.dataset.taskOrder);
  const byPriority = (a, b) => priority(a) - priority(b) || Number(a.dataset.taskNumber) - Number(b.dataset.taskNumber);
  const updatedAt = task => {
    const value = Date.parse(task.querySelector('.task-updated time')?.getAttribute('datetime') || '');
    return Number.isFinite(value) ? value : -Infinity;
  };
  const latestMode = main.dataset.taskDefault === 'latest';
  // Unknown timestamps never outrank known timestamps; ties use existing NEW/NEXT/order.
  const latest = latestMode ? [...tasks].sort((a, b) => {
    const aTime = updatedAt(a), bTime = updatedAt(b);
    return aTime === bTime ? byPriority(a, b) : aTime > bTime ? -1 : 1;
  })[0] : null;
  const list = document.createElement('div');
  list.className = 'task-list';
  main.insertBefore(list, tasks[0]);
  tasks.forEach(task => {
    const badge = task.id === main.dataset.newTask ? 'NEW' : task.id === main.dataset.nextTask ? 'NEXT' : '';
    if (badge) {
      const tag = document.createElement('span');
      tag.className = 'task-highlight';
      tag.textContent = badge;
      task.querySelector('.task-title').prepend(tag);
    }
    if (latestMode) task.open = task === latest;
  });
  tasks.sort((a, b) => a === latest ? -1 : b === latest ? 1 : byPriority(a, b));
  // Same visual, DOM, keyboard and screen-reader order. Do not lock manual toggles.
  tasks.forEach((task, index) => { task.style.order = index; list.appendChild(task); });
  // navigation.js runs afterward: a hash target is opened without closing other choices.
})();
