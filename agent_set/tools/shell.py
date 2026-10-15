"""
========================================
Tools Shell - 命令执行工具
========================================
功能: PowerShell 命令执行
 作者: CuteCuteYu
"""

import subprocess

from langchain_core.tools import tool

from agent_set import workspace


@tool
def run_powershell(command: str) -> str:
    """
    在当前工作区目录下运行PowerShell命令并返回输出结果

    参数:
        command: 要执行的PowerShell命令

    返回:
        命令的标准输出内容。如果执行失败（返回码非0），
        则在输出末尾附加"[Error]"前缀的错误信息（stderr）
    """
    # 相对路径命令统一在用户选择的工作区下执行
    cwd = workspace.get_workspace()
    if cwd is None:
        return "[Error] 尚未选择工作区，请先在页面右上角选择工作区文件夹"

    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # PowerShell 输出可能是 GBK，容错解码避免崩溃
            timeout=60,
            check=False,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        # 命令超时：返回错误信息而非抛出异常，避免中断 agent loop
        return "[Error] 命令执行超时（60秒），已终止"
    except OSError as e:
        return f"[Error] 命令执行失败: {e}"

    # stdout/stderr 可能为 None（如输出非文本时），统一转为空字符串
    output = (result.stdout or "").strip()
    if result.returncode != 0:
        output += f"\n[Error] {(result.stderr or '').strip()}"
    return output