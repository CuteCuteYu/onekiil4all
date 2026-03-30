import subprocess
from pathlib import Path

from langchain_core.tools import tool


@tool
def run_powershell(command: str) -> str:
    """在 PowerShell 中运行命令并返回输出结果。

    Args:
        command: 要执行的 PowerShell 命令

    Returns:
        命令的标准输出内容。如果执行失败（返回码非0），
        则在输出末尾附加 "[Error]" 前缀的错误信息（stderr）。
    """
    result = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout.strip()
    if result.returncode != 0:
        output += f"\n[Error] {result.stderr.strip()}"
    return output


@tool
def write_file(filename: str, content: str) -> str:
    """在当前工作目录下创建文件并写入内容。如果文件已存在则覆盖。

    Args:
        filename: 文件名（相对路径，基于当前工作目录）
        content: 要写入文件的内容

    Returns:
        写入成功的确认信息，包含文件的绝对路径，格式为 "文件已写入: {绝对路径}"。
    """
    filepath = Path.cwd() / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    return f"文件已写入: {filepath}"


tools = [run_powershell, write_file]
