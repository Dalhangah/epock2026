/* Stage identity/number is permanent. NEW/NEXT only change display priority. */
(() => {
  const main = document.querySelector('main[data-new-task]');
  if (!main) return;
  const tasks = [...main.querySelectorAll(':scope > details.task-accordion')];
  if (!tasks.length) return;
  const list = document.createElement('div');
  list.className = 'task-list';
  main.insertBefore(list, tasks[0]);
  const priority = task => task.id === main.dataset.newTask ? -2000 : task.id === main.dataset.nextTask ? -1000 : Number(task.dataset.taskOrder);
  tasks.forEach(task => {
    task.style.order = priority(task);
    const badge = task.id === main.dataset.newTask ? 'NEW' : task.id === main.dataset.nextTask ? 'NEXT' : '';
    if (badge) {
      const tag = document.createElement('span');
      tag.className = 'task-highlight';
      tag.textContent = badge;
      task.querySelector('.task-title').prepend(tag);
    }
  });
  // Match DOM, keyboard, and screen-reader order to CSS; source HTML stays in place.
  tasks.sort((a, b) => priority(a) - priority(b) || Number(a.dataset.taskNumber) - Number(b.dataset.taskNumber));
  tasks.forEach(task => list.appendChild(task));
})();
