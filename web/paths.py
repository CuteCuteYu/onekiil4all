"""
========================================
Paths - 项目路径常量模块
========================================
功能: 集中定义项目内数据/静态资源目录，
所有路径锚定到项目根目录，避免依赖启动时的工作目录
 作者: CuteCuteYu
"""

from pathlib import Path

# 项目根目录（web/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent

# 前端静态资源目录
STATIC_DIR = BASE_DIR / "static"

# 运行时数据目录（告警规则、历史、RSS订阅源）
DATA_DIR = BASE_DIR / "data"

# 对话历史目录（JSONL 存储）
CHAT_HISTORY_DIR = BASE_DIR / "chat_history"

# TODO 任务文件目录
TODO_DIR = BASE_DIR / "todo"
