"""
========================================
Workspace - Agent 工作区状态管理
========================================
功能: 管理用户选择的工作区目录。
初始化时用户必须先选择一个文件夹作为工作区，
之后 Agent 的所有产物默认保存到该文件夹。
 作者: CuteCuteYu
"""

import threading
from pathlib import Path

# 项目根目录（agent_set/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 工作区选择记录文件（项目 data/ 下，运行时数据）
_WORKSPACE_RECORD = _PROJECT_ROOT / "data" / "workspace.json"

_lock = threading.Lock()
# 当前工作区绝对路径；None 表示尚未选择（Agent loop 拒绝启动）
_current: Path | None = None
# 已初始化标志：进程启动时从记录文件恢复
_loaded = False


def _persist(path: Path | None):
    """把当前工作区选择写入记录文件（best-effort，失败仅记录）"""
    import json
    import logging

    logger = logging.getLogger(__name__)
    try:
        _WORKSPACE_RECORD.parent.mkdir(parents=True, exist_ok=True)
        if path is None:
            _WORKSPACE_RECORD.write_text("{}", encoding="utf-8")
        else:
            _WORKSPACE_RECORD.write_text(
                json.dumps({"workspace": str(path)}, ensure_ascii=False),
                encoding="utf-8",
            )
    except OSError:
        logger.warning("工作区记录写入失败", exc_info=True)


def _load() -> Path | None:
    """从记录文件恢复上次选择的工作区（目录不存在时忽略）"""
    import json
    import logging

    if not _WORKSPACE_RECORD.exists():
        return None
    try:
        data = json.loads(_WORKSPACE_RECORD.read_text(encoding="utf-8"))
        raw = data.get("workspace")
        if not raw:
            return None
        path = Path(raw)
        if path.is_dir():
            return path.resolve()
    except (OSError, ValueError):
        logging.getLogger(__name__).warning("工作区记录读取失败", exc_info=True)
    return None


def _ensure_loaded():
    """首次访问时从磁盘恢复工作区选择（进程生命周期内只做一次）"""
    global _current, _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        _current = _load()
        _loaded = True


def get_workspace() -> Path | None:
    """
    获取当前工作区路径

    返回:
        工作区绝对路径；尚未选择时返回 None
    """
    _ensure_loaded()
    return _current


def is_ready() -> bool:
    """工作区是否已选择（Agent loop 是否允许启动）"""
    return get_workspace() is not None


def set_workspace(path: str | Path) -> Path:
    """
    设置工作区（用户在页面上选择文件夹后调用）

    参数:
        path: 用户选择的文件夹路径

    返回:
        规范化后的工作区绝对路径

    异常:
        ValueError: 路径不存在或不是目录
    """
    global _current
    target = Path(path)
    if not target.exists():
        raise ValueError(f"路径不存在: {target}")
    if not target.is_dir():
        raise ValueError(f"不是文件夹: {target}")
    resolved = target.resolve()
    with _lock:
        _current = resolved
        _persist(resolved)
    return resolved


def clear_workspace():
    """清除工作区选择（回到未初始化状态，主要用于测试）"""
    global _current
    with _lock:
        _current = None
        _loaded = True
        _persist(None)


def resolve_in_workspace(filename: str) -> Path:
    """
    把相对路径解析到当前工作区下（绝对路径原样返回）

    参数:
        filename: 文件名（相对或绝对）

    返回:
        解析后的绝对路径

    异常:
        RuntimeError: 尚未选择工作区
    """
    ws = get_workspace()
    if ws is None:
        raise RuntimeError("尚未选择工作区")
    filepath = Path(filename)
    if filepath.is_absolute():
        return filepath
    return ws / filename
