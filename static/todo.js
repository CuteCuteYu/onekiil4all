/**
 * 上古必斩必杀 待办事项功能
 */

async function loadTodo() {
  if (!threadId) return;
  
  try {
    const res = await fetch(`${API}/api/todo?thread_id=${threadId}`);
    const data = await res.json();
    
    if (!data.exists) {
      $todoContent.innerHTML = '<div class="todo-empty">no active task</div>';
      return;
    }
    
    renderTodoList(data.tasks, data.completed_count, data.total_count);
  } catch (e) {
    console.error('Failed to load todo:', e);
  }
}

function renderTodoList(tasks, completedCount, totalCount) {
  if (!tasks || tasks.length === 0) {
    $todoContent.innerHTML = '<div class="todo-empty">no active task</div>';
    return;
  }
  
  $todoContent.innerHTML = `
    <div class="todo-stats">
      <span class="todo-progress">${completedCount}/${totalCount}</span>
    </div>
    <div class="todo-items">
      ${tasks.map((task, i) => `
        <div class="todo-item ${task.completed ? 'completed' : ''}" data-index="${i}">
          <input type="checkbox" ${task.completed ? 'checked' : ''} data-index="${i}">
          <span class="todo-text">${escapeHtml(task.description)}</span>
        </div>
      `).join('')}
    </div>
  `;
  
  $todoContent.querySelectorAll('.todo-item input').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const index = parseInt(e.target.dataset.index);
      tasks[index].completed = e.target.checked;
      renderTodoList(tasks, tasks.filter(t => t.completed).length, tasks.length);
    });
  });
}