"""
========================================
Tools - 工具集包
========================================
功能: 定义AI Agent可用的工具函数
按职责拆分:
- shell.py    PowerShell命令执行
- files.py    文件读写
- search.py   网络搜索与RSS获取
 作者: CuteCuteYu
"""

from agent_set.tools.files import read_binary_file, read_text_file, write_file
from agent_set.tools.graphrag import graphrag_query, graphrag_status
from agent_set.tools.search import fetch_rss_feed, web_search
from agent_set.tools.shell import run_powershell

# 所有可用工具的列表，供Agent使用
tools = [
    run_powershell,  # PowerShell命令执行
    write_file,  # 文件写入
    read_text_file,  # 文本文件读取
    read_binary_file,  # 二进制文件读取
    fetch_rss_feed,  # RSS订阅获取
    web_search,  # 网络搜索
    graphrag_status,  # 图谱画板接入状态检查
    graphrag_query,  # 图谱画板 GraphRAG 检索
]

__all__ = ["tools"]