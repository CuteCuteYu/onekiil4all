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


@tool
def read_text_file(filename: str, encoding: str = "utf-8") -> str:
    """读取文本文件内容并返回。

    Args:
        filename: 文件名（相对路径或绝对路径）
        encoding: 文件编码，默认为 utf-8

    Returns:
        文件的文本内容。如果文件不存在或读取失败，返回错误信息。
    """
    filepath = Path(filename)
    if not filepath.is_absolute():
        filepath = Path.cwd() / filename

    try:
        content = filepath.read_text(encoding=encoding)
        # 显示文件信息
        lines = content.count('\n') + 1
        chars = len(content)
        header = f"=== 文件: {filepath} ({lines} 行, {chars} 字符) ===\n\n"
        return header + content
    except FileNotFoundError:
        return f"[Error] 文件不存在: {filepath}"
    except UnicodeDecodeError:
        return f"[Error] 无法使用编码 {encoding} 解码文件，可能是二进制文件或编码不匹配"
    except Exception as e:
        return f"[Error] 读取文件失败: {e}"


@tool
def read_binary_file(filename: str, bytes_per_line: int = 16, max_bytes: int = 1024) -> str:
    """读取二进制文件并以十六进制格式显示。

    Args:
        filename: 文件名（相对路径或绝对路径）
        bytes_per_line: 每行显示的字节数，默认 16
        max_bytes: 最多读取的字节数，默认 1024（用于预览）

    Returns:
        文件的十六进制转储内容，包含偏移地址、十六进制值和 ASCII 表示。
        如果文件不存在或读取失败，返回错误信息。
    """
    filepath = Path(filename)
    if not filepath.is_absolute():
        filepath = Path.cwd() / filename

    try:
        data = filepath.read_bytes()
        file_size = len(data)

        # 限制读取大小用于预览
        if file_size > max_bytes:
            data = data[:max_bytes]
            truncated = True
        else:
            truncated = False

        header = f"=== 二进制文件: {filepath} ({file_size} 字节) ===\n\n"
        if truncated:
            header += f"=== 仅显示前 {max_bytes} 字节 ===\n\n"

        # 十六进制转储
        lines = []
        for offset in range(0, len(data), bytes_per_line):
            chunk = data[offset:offset + bytes_per_line]

            # 偏移地址
            offset_hex = f"{offset:08x}"

            # 十六进制值
            hex_bytes = " ".join(f"{b:02x}" for b in chunk)

            # ASCII 表示
            ascii_chars = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

            lines.append(f"{offset_hex}  {hex_bytes:<{bytes_per_line * 3 - 1}}  |{ascii_chars}|")

        return header + "\n".join(lines)
    except FileNotFoundError:
        return f"[Error] 文件不存在: {filepath}"
    except Exception as e:
        return f"[Error] 读取文件失败: {e}"


tools = [run_powershell, write_file, read_text_file, read_binary_file]
