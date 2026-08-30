/**
 * 上古必斩必杀 - 图谱画板（GraphRAG Viz）
 * 功能: 多画板管理 / 图谱可视化（Cytoscape）/ 实体关系编辑 / 类型管理 /
 *       1 跳展开 / GraphRAG 上下文与索引导出
 * 说明: 由独立 canvas 应用前端整合而来，界面样式与主应用统一
 */

/* ============================================================
 * 常量与状态
 * ============================================================ */
const TYPES = {}; // 从后端 /api/types 动态加载（内置 + 用户自定义）
const DEFAULT_TYPE = { color: '#64748b', shape: 'ellipse', label: '未知' };

let selectedNodeId = null;   // 当前抽屉展示的节点
let ctxNodeId = null;        // 右键菜单对应的节点
let editingNodeId = null;    // 编辑实体模式下的节点 id
let currentBoardName = '';   // 当前画板名（用于列表高亮）
let graphReady = false;      // 首次渲染完成标记

/* ============================================================
 * Cytoscape 初始化
 * ============================================================ */
const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: [],
  style: [
    {
      selector: 'node',
      style: {
        'background-color': 'transparent',
        'shape': (ele) => (TYPES[ele.data('type')] || DEFAULT_TYPE).shape,
        'label': 'data(name)',
        'color': '#d4d4d8',
        'font-size': 11,
        'font-family': '"DM Mono", Consolas, monospace',
        'font-weight': 400,
        'text-valign': 'bottom',
        'text-margin-y': 7,
        'text-wrap': 'wrap',
        'text-max-width': 130,
        'text-background-color': '#09090b',
        'text-background-opacity': 0.85,
        'text-background-padding': 3,
        'width': 44,
        'height': 44,
        'border-width': 2,
        'border-color': (ele) => (TYPES[ele.data('type')] || DEFAULT_TYPE).color,
        'overlay-opacity': 0,
      },
    },
    {
      selector: 'edge',
      style: {
        'width': 1.5,
        'line-color': '#3f3f46',
        'target-arrow-color': '#52525b',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(relation)',
        'font-size': 8.5,
        'font-family': '"DM Mono", Consolas, monospace',
        'color': '#71717a',
        'text-background-color': '#09090b',
        'text-background-opacity': 0.85,
        'text-background-padding': 2,
        'text-rotation': 'autorotate',
        'overlay-opacity': 0,
      },
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 3,
        'border-color': '#d4d4d8',
        'overlay-opacity': 0.1,
        'overlay-color': '#d4d4d8',
      },
    },
    {
      selector: 'edge:selected',
      style: { 'line-color': '#a1a1aa', 'target-arrow-color': '#a1a1aa' },
    },
  ],
  layout: { name: 'preset' },
  wheelSensitivity: 0.2,
  minZoom: 0.08,
  maxZoom: 3,
  boxSelectionEnabled: false,
});

const COSE_LAYOUT = {
  name: 'cose',
  animate: true,
  animationDuration: 600,
  padding: 60,
  nodeRepulsion: 9000,
  idealEdgeLength: 130,
  edgeElasticity: 120,
  gravity: 0.35,
  randomize: true,
  fit: true,
};

/* ============================================================
 * 数据加载与渲染
 * ============================================================ */
async function loadGraph() {
  const res = await fetch('/api/graph');
  const data = await res.json();
  renderGraph(data);
}

/* ============================================================
 * 画板管理（独立文件管理）
 * ============================================================ */
async function loadBoards() {
  try {
    const res = await fetch('/api/boards');
    const data = await res.json();
    currentBoardName = data.current || '';
    renderBoards(data.boards);
    document.getElementById('board-name').textContent = data.current || '—';
    refreshGraphRagStatus();
  } catch (err) {
    toast('加载画板列表失败：' + err.message, true);
  }
}

/**
 * 刷新 GraphRAG 接入状态：检查当前画板是否已保存，
 * 已保存 → 聊天界面显示「GRAPH RAG · 画板名」，画板工具栏显示「已保存」；
 * 未保存 → 提示保存后接入。
 */
async function refreshGraphRagStatus() {
  try {
    const res = await fetch('/api/graph/status');
    const st = await res.json();
    const badge = document.getElementById('graphrag-badge');
    const saveBadge = document.getElementById('canvas-save-badge');

    if (saveBadge) {
      saveBadge.hidden = false;
      saveBadge.textContent = st.saved ? '● 已保存' : (st.has_board ? '○ 未保存' : '—');
      saveBadge.classList.toggle('saved', !!st.saved);
    }

    if (badge) {
      if (st.has_board && st.saved) {
        badge.hidden = false;
        badge.textContent = `● GRAPH RAG · ${st.board}`;
        badge.classList.add('active');
      } else if (st.has_board) {
        badge.hidden = false;
        badge.textContent = `○ GRAPH RAG · ${st.board} 未保存`;
        badge.classList.remove('active');
      } else {
        badge.hidden = true;
        badge.textContent = '';
        badge.classList.remove('active');
      }
    }
  } catch (err) {
    /* 后端不可用时静默，避免影响画布 */
  }
}

function renderBoards(boards) {
  const list = document.getElementById('boards-list');
  if (boards.length === 0) {
    list.innerHTML = '<div class="canvas-board-empty">暂无画板，请在上方创建</div>';
    return;
  }
  list.innerHTML = boards.map((b) => `
    <div class="canvas-board-item ${b.name === currentBoardName ? 'canvas-board-item-current' : ''}"
         onclick="openBoard('${b.name}')">
      <div class="canvas-board-icon">📁</div>
      <div class="canvas-board-main">
        <div class="canvas-board-name">${escapeHtml(b.name)}</div>
        <div class="canvas-board-meta">${b.nodes} 节点 · ${b.edges} 关系 · 更新于 ${b.updated_at}</div>
      </div>
      <div class="canvas-board-actions">
        <button class="canvas-btn canvas-btn-sm" onclick="event.stopPropagation(); renameBoard('${b.name}')">重命名</button>
        <button class="canvas-btn canvas-btn-sm canvas-btn-danger" onclick="event.stopPropagation(); deleteBoard('${b.name}')">删除</button>
      </div>
    </div>`).join('');
}

async function openBoard(name) {
  try {
    const res = await fetch('/api/boards/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '打开失败');
    }
    const data = await res.json();
    currentBoardName = name;
    document.getElementById('board-name').textContent = name;
    document.getElementById('welcome').classList.remove('open');
    hideDrawer();
    hideCtxMenu();
    document.getElementById('ragpanel').classList.remove('open');
    await loadTypes();
    renderGraph(data.graph);
    cy.resize();
    refreshGraphRagStatus();
    toast(`已打开画板「${name}」`);
  } catch (err) {
    toast('打开画板失败：' + err.message, true);
  }
}

async function createBoard() {
  const name = document.getElementById('new-board-name').value.trim();
  if (!name) { toast('请输入画板名称', true); return; }
  try {
    const res = await fetch('/api/boards', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '创建失败');
    }
    document.getElementById('new-board-name').value = '';
    await openBoard(name);
  } catch (err) {
    toast('创建画板失败：' + err.message, true);
  }
}

async function deleteBoard(name) {
  if (!confirm(`确定删除画板「${name}」？此操作不可恢复。`)) return;
  try {
    const res = await fetch(`/api/boards/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '删除失败');
    }
    await loadBoards();
    toast(`已删除画板「${name}」`);
  } catch (err) {
    toast('删除画板失败：' + err.message, true);
  }
}

async function renameBoard(name) {
  const newName = prompt(`重命名画板「${name}」为：`, name);
  if (!newName || newName.trim() === name) return;
  try {
    const res = await fetch('/api/boards/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_name: name, new_name: newName.trim() }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '重命名失败');
    }
    await loadBoards();
    toast(`已重命名为「${newName.trim()}」`);
  } catch (err) {
    toast('重命名失败：' + err.message, true);
  }
}

function renderGraph(data) {
  const elements = [];
  data.nodes.forEach((n) => elements.push({ data: n }));
  data.edges.forEach((e) => elements.push({ data: e }));
  cy.elements().remove();
  cy.add(elements);
  cy.layout(COSE_LAYOUT).run();
  graphReady = true;
}

/* ============================================================
 * 事件绑定
 * ============================================================ */
cy.on('tap', 'node', (evt) => {
  const node = evt.target;
  selectedNodeId = node.id();
  showDrawer(node.data());
});

cy.on('tap', (evt) => {
  if (evt.target === cy) {
    hideDrawer();
    hideCtxMenu();
  }
});

cy.on('cxttap', 'node', (evt) => {
  evt.preventDefault();
  const node = evt.target;
  ctxNodeId = node.id();
  showCtxMenu(evt.renderedPosition, node.data());
});

cy.on('cxttap', (evt) => {
  if (evt.target === cy) hideCtxMenu();
});

// 仅在画布区域内屏蔽浏览器右键菜单（不影响页面其他区域）
document.getElementById('canvas-stage').addEventListener('contextmenu', (e) => e.preventDefault());

/* ============================================================
 * 拖拽连线：长按节点拖动拖出箭头，松手到目标节点创建关系
 * ============================================================ */
let dragState = null;      // 拖拽连线状态
let lastMousePos = null;   // 最近一次鼠标位置（画布坐标）

cy.on('mousemove', (evt) => {
  lastMousePos = evt.position;
  if (dragState && dragState.mode === 'link') {
    cy.getElementById(dragState.tempNodeId).position(evt.position);
  }
});

cy.on('grabon', 'node', (evt) => {
  // 清理可能残留的临时元素（异常中断时）
  cy.getElementById('__drag_edge__').remove();
  cy.getElementById('__drag_target__').remove();
  const node = evt.target;
  dragState = {
    sourceId: node.id(),
    startTime: Date.now(),
    initialPos: { ...node.position() },
    mode: 'move',
  };
});

cy.on('drag', 'node', (evt) => {
  if (!dragState || dragState.sourceId !== evt.target.id()) return;
  const node = evt.target;
  if (dragState.mode === 'move' && Date.now() - dragState.startTime > 300) {
    // 长按超过阈值 → 进入连线模式
    dragState.mode = 'link';
    const tempNodeId = '__drag_target__';
    const tempEdgeId = '__drag_edge__';
    cy.add({ data: { id: tempNodeId, name: '', type: '__temp__' } });
    cy.getElementById(tempNodeId).style({
      'background-opacity': 0,
      'border-opacity': 0,
      'label': '',
      'width': 1,
      'height': 1,
      'overlay-opacity': 0,
    });
    cy.add({ data: { id: tempEdgeId, source: dragState.sourceId, target: tempNodeId, relation: '' } });
    cy.getElementById(tempEdgeId).style({
      'line-style': 'dashed',
      'line-color': '#a1a1aa',
      'width': 2,
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#a1a1aa',
      'label': '',
      'overlay-opacity': 0,
    });
    dragState.tempNodeId = tempNodeId;
    dragState.tempEdgeId = tempEdgeId;
    toast('拖动到目标节点松手以创建关系');
  }
  if (dragState.mode === 'link') {
    // 锁定源节点位置，避免被拖动
    node.position(dragState.initialPos);
  }
});

cy.on('free', 'node', (evt) => {
  if (!dragState || dragState.sourceId !== evt.target.id()) return;
  const node = evt.target;
  if (dragState.mode === 'link') {
    // 清理临时元素
    if (dragState.tempEdgeId) cy.getElementById(dragState.tempEdgeId).remove();
    if (dragState.tempNodeId) cy.getElementById(dragState.tempNodeId).remove();
    node.position(dragState.initialPos);
    // 查找鼠标位置的目标节点（遍历节点包围盒判断）
    const pos = lastMousePos || node.position();
    let target = null;
    cy.nodes().forEach((n) => {
      if (n.id() === dragState.sourceId || n.id().startsWith('__')) return;
      const bb = n.boundingBox();
      if (pos.x >= bb.x1 && pos.x <= bb.x2 && pos.y >= bb.y1 && pos.y <= bb.y2) {
        target = n;
      }
    });
    if (target) {
      openEdgeDialog(dragState.sourceId, target.id());
    }
  }
  dragState = null;
});

/* ============================================================
 * 右键菜单
 * ============================================================ */
function showCtxMenu(pos, nodeData) {
  const menu = document.getElementById('ctxmenu');
  menu.innerHTML = `
    <div class="ctx-head">
      ${escapeHtml(nodeData.name)} <span>· ${escapeHtml(nodeData.type)}</span>
    </div>
    <div class="ctx-sep"></div>
    <div class="ctx-item" onclick="expandNode('${nodeData.id}')">
      <span>◎</span> 展开邻居（1-Hop Expand）
    </div>
    <div class="ctx-item" onclick="showRagContext('${nodeData.id}')">
      <span>🧠</span> 生成 RAG 上下文
    </div>
    <div class="ctx-sep"></div>
    <div class="ctx-item danger" onclick="removeNode('${nodeData.id}')">
      <span>🗑</span> 删除节点（Remove）
    </div>
  `;
  menu.style.display = 'block';
  const mw = menu.offsetWidth;
  const mh = menu.offsetHeight;
  const stage = document.getElementById('canvas-stage');
  const sw = stage.clientWidth;
  const sh = stage.clientHeight;
  menu.style.left = Math.min(pos.x, sw - mw - 8) + 'px';
  menu.style.top = Math.min(pos.y, sh - mh - 8) + 'px';
}

function hideCtxMenu() {
  document.getElementById('ctxmenu').style.display = 'none';
}

/* 展开邻居：调用后端 1 跳展开，合并追加到画布 */
async function expandNode(nodeId) {
  hideCtxMenu();
  try {
    const res = await fetch(`/api/expand/${nodeId}`);
    if (!res.ok) throw new Error('展开失败');
    const sub = await res.json();
    const existingNodes = new Set(cy.nodes().map((n) => n.id()));
    const existingEdges = new Set(cy.edges().map((e) => e.id()));
    const newElems = [];
    sub.nodes.forEach((n) => {
      if (!existingNodes.has(n.id)) newElems.push({ data: n });
    });
    sub.edges.forEach((e) => {
      if (!existingEdges.has(e.id)) newElems.push({ data: e });
    });
    if (newElems.length === 0) {
      toast('该节点已无未展示的邻居');
      return;
    }
    cy.add(newElems);
    cy.layout(COSE_LAYOUT).run();
    toast(`已展开 ${newElems.length} 个新元素`);
  } catch (err) {
    toast('展开失败：' + err.message, true);
  }
}

/* 删除节点：内存 + 画布同步移除 */
async function removeNode(nodeId) {
  hideCtxMenu();
  if (!confirm(`确定删除节点「${cy.getElementById(nodeId).data('name')}」及其所有关联关系？`)) return;
  try {
    const res = await fetch(`/api/node/${nodeId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('删除失败');
    cy.getElementById(nodeId).remove();
    cy.edges().filter((e) => e.data('source') === nodeId || e.data('target') === nodeId).remove();
    if (selectedNodeId === nodeId) hideDrawer();
    refreshGraphRagStatus();
    toast('节点已从内存与画布移除（保存后落盘）');
  } catch (err) {
    toast('删除失败：' + err.message, true);
  }
}

/* ============================================================
 * 右侧抽屉面板
 * ============================================================ */
function showDrawer(nodeData) {
  const body = document.getElementById('drawer-body');
  const ts = TYPES[nodeData.type] || DEFAULT_TYPE;
  const props = nodeData.properties || {};
  const chunks = nodeData.source_chunks || [];

  // 关联关系（从画布中提取）
  const rels = [];
  cy.edges().forEach((e) => {
    const d = e.data();
    if (d.source === nodeData.id || d.target === nodeData.id) {
      const otherId = d.source === nodeData.id ? d.target : d.source;
      const other = cy.getElementById(otherId).data();
      rels.push({
        relation: d.relation,
        otherName: other.name || otherId,
        otherType: other.type || '?',
        direction: d.source === nodeData.id ? '→' : '←',
        weight: d.weight,
        desc: d.description || '',
      });
    }
  });

  body.innerHTML = `
    <div class="canvas-entity-head">
      <div class="canvas-entity-avatar"
           style="background:${ts.color}22; color:${ts.color}; border:1px solid ${ts.color}55">
        ${escapeHtml(nodeData.name.slice(0, 1))}
      </div>
      <div>
        <div class="canvas-entity-name">${escapeHtml(nodeData.name)}</div>
        <span class="canvas-badge"
              style="background:${ts.color}22; color:${ts.color}; border-color:${ts.color}55">
          ${escapeHtml(nodeData.type)} · ${escapeHtml(ts.label)}
        </span>
      </div>
    </div>

    <div class="canvas-section-label">GRAPH RAG 描述（Entity Description）</div>
    <div class="canvas-desc-box">${escapeHtml(nodeData.description || '（无描述）')}</div>

    <div class="canvas-section-label">结构化属性（Properties）</div>
    <div class="canvas-card" style="padding:2px 10px">
      ${Object.keys(props).length === 0
        ? '<div class="canvas-empty">（无属性）</div>'
        : Object.entries(props).map(([k, v]) => `
            <div class="canvas-kv-row">
              <div class="canvas-kv-key">${escapeHtml(k)}</div>
              <div class="canvas-kv-val">${escapeHtml(typeof v === 'object' ? JSON.stringify(v) : String(v))}</div>
            </div>`).join('')}
    </div>

    <div class="canvas-section-label">关联关系（${rels.length}）</div>
    ${rels.length === 0
      ? '<div class="canvas-empty">（暂无关联关系）</div>'
      : rels.map((r) => `
          <div class="canvas-card">
            <div class="canvas-rel-row">
              <span class="canvas-rel-rel">${escapeHtml(r.relation)}</span>
              <span class="canvas-rel-dir">${r.direction}</span>
              <span class="canvas-rel-name">${escapeHtml(r.otherName)}</span>
              <span class="canvas-rel-type">${escapeHtml(r.otherType)}</span>
              <span class="canvas-rel-weight">w=${r.weight}</span>
            </div>
            ${r.desc ? `<div class="canvas-empty" style="padding:2px 0 0; font-size:10px">${escapeHtml(r.desc)}</div>` : ''}
          </div>`).join('')}

    <div class="canvas-section-label">文本溯源（Source Chunks）</div>
    ${chunks.length === 0
      ? '<div class="canvas-empty">（无溯源）</div>'
      : chunks.map((c) => `
          <div class="canvas-chunk">${escapeHtml(String(c))}</div>`).join('')}
  `;
  document.getElementById('drawer').classList.add('open');
}

function hideDrawer() {
  document.getElementById('drawer').classList.remove('open');
  selectedNodeId = null;
}

/* ============================================================
 * RAG 上下文
 * ============================================================ */
async function showRagContext(nodeId) {
  hideCtxMenu();
  try {
    const res = await fetch(`/api/rag/context/${nodeId}`);
    if (!res.ok) throw new Error('生成失败');
    const data = await res.json();
    const name = cy.getElementById(nodeId).data('name') || nodeId;
    document.getElementById('rag-title').textContent = `· ${name}`;
    document.getElementById('ragtext').textContent = data.context;
    document.getElementById('ragpanel').classList.add('open');
  } catch (err) {
    toast('RAG 上下文生成失败：' + err.message, true);
  }
}

/* ============================================================
 * 模态框：添加实体 / 添加关系
 * ============================================================ */
function openModal(id) {
  if (id === 'modal-edge') fillEdgeSelects();
  document.getElementById(id).classList.add('open');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

/* 重置实体表单（工具栏「＋ 实体」点击时调用，避免残留编辑态） */
function resetNodeModal() {
  editingNodeId = null;
  document.getElementById('modal-node-title').textContent = '＋ 添加实体';
  const idInput = document.getElementById('node-id');
  idInput.value = '';
  idInput.disabled = false;
  document.getElementById('node-name').value = '';
  document.getElementById('node-desc').value = '';
  document.getElementById('node-props').value = '';
  document.getElementById('node-chunks').value = '';
}

function fillEdgeSelects() {
  const nodes = cy.nodes().map((n) => n.data());
  const opts = nodes
    .map((n) => `<option value="${n.id}">${escapeHtml(n.name)}（${escapeHtml(n.type)}）</option>`)
    .join('');
  document.getElementById('edge-source').innerHTML = opts;
  document.getElementById('edge-target').innerHTML = opts;
}

/* 拖拽连线松手后：预填源/目标节点并打开关系创建对话框 */
function openEdgeDialog(sourceId, targetId) {
  fillEdgeSelects();
  document.getElementById('edge-source').value = sourceId;
  document.getElementById('edge-target').value = targetId;
  document.getElementById('edge-id').value = '';
  document.getElementById('edge-relation').value = '';
  document.getElementById('edge-desc').value = '';
  document.getElementById('edge-weight').value = '0.8';
  // 直接打开模态框（避免 openModal 内重复 fillEdgeSelects 重置下拉）
  document.getElementById('modal-edge').classList.add('open');
}

async function submitNode() {
  const idInput = document.getElementById('node-id');
  const id = idInput.value.trim();
  const name = document.getElementById('node-name').value.trim();
  const type = document.getElementById('node-type').value;
  const desc = document.getElementById('node-desc').value.trim();
  const propsRaw = document.getElementById('node-props').value.trim();
  const chunksRaw = document.getElementById('node-chunks').value.trim();

  if (!name) { toast('请填写实体名称', true); return; }

  let properties = {};
  if (propsRaw) {
    try { properties = JSON.parse(propsRaw); }
    catch { toast('属性不是合法 JSON', true); return; }
  }
  const source_chunks = chunksRaw ? chunksRaw.split('\n').map((s) => s.trim()).filter(Boolean) : [];
  const nodeId = editingNodeId || id || `ent_${Date.now().toString(36)}`;

  try {
    const res = await fetch('/api/node', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: nodeId, name, type, description: desc, properties, source_chunks }),
    });
    if (!res.ok) throw new Error('保存失败');
    const wasEditing = editingNodeId !== null;
    closeModal('modal-node');
    resetNodeModal();
    await loadGraph();
    refreshGraphRagStatus();
    toast(wasEditing ? `已更新实体「${name}」` : `已添加实体「${name}」`);
  } catch (err) {
    toast('保存实体失败：' + err.message, true);
  }
}

async function submitEdge() {
  const id = document.getElementById('edge-id').value.trim();
  const source = document.getElementById('edge-source').value;
  const target = document.getElementById('edge-target').value;
  const relation = document.getElementById('edge-relation').value.trim().toUpperCase();
  const desc = document.getElementById('edge-desc').value.trim();
  const weight = parseFloat(document.getElementById('edge-weight').value) || 0.5;

  if (!source || !target) { toast('请选择源节点与目标节点', true); return; }
  if (!relation) { toast('请填写关系动词', true); return; }
  if (source === target) { toast('源节点与目标节点不能相同', true); return; }
  const edgeId = id || `rel_${Date.now().toString(36)}`;

  try {
    const res = await fetch('/api/edge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: edgeId, source, target, relation, description: desc, weight }),
    });
    if (!res.ok) throw new Error('添加失败');
    closeModal('modal-edge');
    document.getElementById('edge-id').value = '';
    document.getElementById('edge-relation').value = '';
    document.getElementById('edge-desc').value = '';
    await loadGraph();
    refreshGraphRagStatus();
    toast(`已添加关系 ${relation}`);
  } catch (err) {
    toast('添加关系失败：' + err.message, true);
  }
}

/* ============================================================
 * 工具栏：保存 / 导出 / 居中
 * ============================================================ */
async function saveGraph() {
  try {
    const res = await fetch('/api/save', { method: 'POST' });
    if (!res.ok) throw new Error('保存失败');
    const data = await res.json();
    toast(`已保存 ${data.nodes} 节点 / ${data.edges} 边 → ${data.board}`);
    await loadBoards();
  } catch (err) {
    toast('保存失败：' + err.message, true);
  }
}

async function exportGraphRag() {
  try {
    const res = await fetch('/api/graph');
    const data = await res.json();
    const payload = {
      graph_name: '情报分析图谱',
      exported_at: new Date().toISOString(),
      entities: data.nodes,
      relationships: data.edges,
      graphrag_compat: {
        ms_graphrag: 'entities 对应 entity 表（id/name/type/description），relationships 对应 relationship 表（source/target/relation/description/weight），source_chunks 对应 text_unit 关联，可直接作为 GraphRAG 索引输入。',
        llamaindex: '每条 relationship 可转换为 (head=source, relation, tail=target) 三元组，配合 entity.description 构建 KnowledgeGraphIndex。',
      },
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'graphrag_index.json';
    a.click();
    URL.revokeObjectURL(url);
    toast('已导出 GraphRAG 索引 JSON');
  } catch (err) {
    toast('导出失败：' + err.message, true);
  }
}

/* ============================================================
 * 工具函数
 * ============================================================ */
let toastTimer = null;
function toast(msg, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.toggle('error', !!isError);
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

function renderLegend() {
  const body = document.getElementById('legend-body');
  body.innerHTML = Object.entries(TYPES)
    .map(([type, s]) => `
      <div class="legend-item">
        <div class="legend-dot" style="border-color:${s.color}; box-shadow:0 0 6px ${s.color}44"></div>
        <span>${escapeHtml(type)}</span>
        <span style="color:var(--fg-dim)">${escapeHtml(s.label)}</span>
      </div>`)
    .join('');
}

/* ============================================================
 * 实体类型管理（支持用户自定义实体类型）
 * ============================================================ */
async function loadTypes() {
  try {
    const res = await fetch('/api/types');
    const data = await res.json();
    Object.keys(TYPES).forEach((k) => delete TYPES[k]);
    Object.assign(TYPES, data);
    renderLegend();
    fillTypeSelect();
    cy.style().update();
  } catch (err) {
    toast('加载类型失败：' + err.message, true);
  }
}

function fillTypeSelect() {
  const sel = document.getElementById('node-type');
  sel.innerHTML = Object.entries(TYPES)
    .map(([name, t]) => `<option value="${name}">${escapeHtml(name)} · ${escapeHtml(t.label)}</option>`)
    .join('');
}

function openTypeModal() {
  renderTypesList();
  document.getElementById('modal-types').classList.add('open');
}

function renderTypesList() {
  const list = document.getElementById('types-list');
  list.innerHTML = Object.entries(TYPES)
    .map(([name, t]) => `
      <div class="canvas-type-item">
        <div class="canvas-type-swatch" style="border-color:${t.color}; box-shadow:0 0 6px ${t.color}44"></div>
        <div class="canvas-type-name">${escapeHtml(name)}</div>
        <div class="canvas-type-label">${escapeHtml(t.label)}</div>
        <div class="canvas-type-shape">${escapeHtml(t.shape)}</div>
        ${t.builtin
          ? '<span class="canvas-type-tag">内置</span>'
          : `<button class="canvas-btn canvas-btn-sm canvas-btn-danger" onclick="deleteType('${name}')">删除</button>`}
      </div>`)
    .join('');
}

async function submitType() {
  const name = document.getElementById('type-name').value.trim();
  const label = document.getElementById('type-label').value.trim();
  const color = document.getElementById('type-color').value;
  const shape = document.getElementById('type-shape').value;
  if (!name) { toast('请填写类型名', true); return; }
  try {
    const res = await fetch('/api/types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, label, color, shape }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '添加失败');
    }
    document.getElementById('type-name').value = '';
    document.getElementById('type-label').value = '';
    await loadTypes();
    renderTypesList();
    refreshGraphRagStatus();
    toast(`已添加自定义类型「${name}」`);
  } catch (err) {
    toast('添加类型失败：' + err.message, true);
  }
}

async function deleteType(name) {
  if (!confirm(`确定删除自定义类型「${name}」？`)) return;
  try {
    const res = await fetch(`/api/types/${encodeURIComponent(name)}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '删除失败');
    }
    await loadTypes();
    renderTypesList();
    refreshGraphRagStatus();
    toast(`已删除类型「${name}」`);
  } catch (err) {
    toast('删除类型失败：' + err.message, true);
  }
}

/* ============================================================
 * 编辑实体
 * ============================================================ */
function openEditNode(nodeData) {
  editingNodeId = nodeData.id;
  document.getElementById('modal-node-title').textContent = '✎ 编辑实体';
  const idInput = document.getElementById('node-id');
  idInput.value = nodeData.id;
  idInput.disabled = true;
  document.getElementById('node-name').value = nodeData.name || '';
  document.getElementById('node-type').value = nodeData.type || '';
  document.getElementById('node-desc').value = nodeData.description || '';
  document.getElementById('node-props').value = JSON.stringify(nodeData.properties || {}, null, 2);
  document.getElementById('node-chunks').value = (nodeData.source_chunks || []).join('\n');
  openModal('modal-node');
}

/* ============================================================
 * 事件绑定与初始化
 * ============================================================ */
document.getElementById('btn-boards').addEventListener('click', () => {
  loadBoards();
  document.getElementById('welcome').classList.add('open');
});
document.getElementById('btn-fit').addEventListener('click', () => cy.fit(undefined, 60));
document.getElementById('btn-rag').addEventListener('click', () => {
  if (!selectedNodeId) { toast('请先单击选择一个节点', true); return; }
  showRagContext(selectedNodeId);
});
document.getElementById('btn-types').addEventListener('click', openTypeModal);
document.getElementById('btn-add-node').addEventListener('click', () => {
  resetNodeModal();
  openModal('modal-node');
});
document.getElementById('btn-add-edge').addEventListener('click', () => openModal('modal-edge'));
document.getElementById('drawer-edit').addEventListener('click', () => {
  if (selectedNodeId) {
    const nodeData = cy.getElementById(selectedNodeId).data();
    openEditNode(nodeData);
  }
});
document.getElementById('btn-export').addEventListener('click', exportGraphRag);
document.getElementById('btn-save').addEventListener('click', saveGraph);
document.getElementById('drawer-close').addEventListener('click', hideDrawer);
document.getElementById('rag-close').addEventListener('click', () => document.getElementById('ragpanel').classList.remove('open'));
document.getElementById('rag-copy').addEventListener('click', () => {
  const text = document.getElementById('ragtext').textContent;
  navigator.clipboard.writeText(text).then(() => toast('已复制 RAG 上下文'));
});

/**
 * 画板标签页被激活时调用（init.js 中标签切换触发）：
 * 容器从 display:none 变为可见后，需要让 Cytoscape 重新测量尺寸并自适应居中
 */
window.onCanvasTabShown = async () => {
  if (!graphReady) {
    try { await loadGraph(); } catch (err) { /* 后端不可用时静默 */ }
  }
  cy.resize();
  if (cy.elements().length > 0) {
    cy.fit(undefined, 60);
  }
};

// 初始化：加载类型、当前画板图数据与画板列表（预加载，标签页激活后即可见）
loadTypes()
  .then(() => loadGraph())
  .catch(() => {});
loadBoards();

// 定时刷新 GraphRAG 接入状态（画板保存状态变化后聊天界面自动同步）
// 仅在页面可见时轮询，避免后台标签页持续请求
setInterval(() => {
  if (document.visibilityState === 'visible') {
    refreshGraphRagStatus();
  }
}, 5000);
