/**
 * 上古必斩必杀 技能和工具功能
 */

async function loadSkills() {
  try {
    const res = await fetch(`${API}/api/skills`);
    const data = await res.json();
    
    if (!data.skills || data.skills.length === 0) {
      $skillsList.innerHTML = '<div class="list-loading">no skills</div>';
      return;
    }
    
    $skillsList.innerHTML = data.skills.map(skill => `
      <div class="skill-item">
        <div class="skill-item-name">${escapeHtml(skill.id)}</div>
        <div class="skill-item-desc">${escapeHtml(skill.description || '')}</div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load skills:', e);
    $skillsList.innerHTML = '<div class="list-loading">load failed</div>';
  }
}

async function loadTools() {
  try {
    const res = await fetch(`${API}/api/tools`);
    const data = await res.json();
    
    if (!data.tools || data.tools.length === 0) {
      $toolsList.innerHTML = '<div class="list-loading">no tools</div>';
      return;
    }
    
    $toolsList.innerHTML = data.tools.map(tool => `
      <div class="tool-item">
        <div class="tool-item-name">${escapeHtml(tool.name)}</div>
        <div class="tool-item-desc">${escapeHtml(tool.description || '')}</div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load tools:', e);
    $toolsList.innerHTML = '<div class="list-loading">load failed</div>';
  }
}