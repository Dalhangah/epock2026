/* NEW is an explicit editorial selection, not inferred from timestamps/status. */
(() => {
  const main = document.querySelector('main[data-new-task]');
  if (!main) return;
  const tasks = [...main.querySelectorAll(':scope > details.task-accordion')];
  if (!tasks.length) return;
  const priority = task => task.id === main.dataset.newTask ? -2000 : task.id === main.dataset.nextTask ? -1000 : Number(task.dataset.taskOrder);
  tasks.sort((a, b) => priority(a) - priority(b) || Number(a.dataset.taskNumber) - Number(b.dataset.taskNumber));
  const featured = tasks.find(task => task.id === main.dataset.newTask);
  const list = document.createElement('div');
  list.className = 'task-list';
  main.insertBefore(list, main.querySelector(':scope > details.task-accordion'));
  tasks.forEach((task, index) => {
    const badge = task === featured ? 'NEW' : task.id === main.dataset.nextTask ? 'NEXT' : '';
    if (badge) {
      const tag = document.createElement('span');
      tag.className = 'task-highlight';
      tag.textContent = badge;
      task.querySelector('.task-title').prepend(tag);
    }
    // Only the selected NEW starts open; without NEW every task starts closed.
    task.open = task === featured;
    task.style.order = index;
    list.appendChild(task);
  });
  // Same DOM/visual order; native toggles stay free. navigation.js reveals hash targets.
})();
