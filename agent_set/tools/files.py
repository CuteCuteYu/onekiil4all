"""
========================================
Tools Files - 文件操作工具
========================================
功能: 文件写入、文本读取、二进制读取
 作者: CuteCuteYu
"""

from pathlib import Path

from langchain_core.tools import tool


@tool
def write_file(filename: str, content: str) -> str:
    """
    在当前工作目录下创建文件并写入内容。如果文件已存在则覆盖

    参数:
        filename: 文件名（相对路径，基于当前工作目录）
        content: 要写入文件的内容

    返回:
        写入成功的确认信息，包含文件的绝对路径
    """
    filepath = Path.cwd() / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    return f"文件已写入: {filepath}"


@tool
def read_text_file(filename: str, encoding: str = "utf-8") -> str:
    """
    读取文本文件内容并返回

    参数:
        filename: 文件名（相对路径或绝对路径）
        encoding: 文件编码，默认为utf-8；指定编码解码失败时自动尝试常见编码

    返回:
        文件的文本内容。如果文件不存在或读取失败，返回错误信息
    """
    filepath = Path(filename)
    if not filepath.is_absolute():
        filepath = Path.cwd() / filename

    try:
        content = filepath.read_text(encoding=encoding)
    except UnicodeDecodeError:
        # 指定编码失败时自动尝试常见编码，避免 Windows 默认 GBK 环境下的解码问题
        content = None
        for enc in ("utf-8", "gbk", "gb18030", "latin-1"):
            if enc == encoding:
                continue
            try:
                content = filepath.read_text(encoding=enc)
                encoding = enc
                break
            except (UnicodeDecodeError, OSError):
                continue
        if content is None:
            return f"[Error] 无法使用编码 {encoding} 解码文件，可能是二进制文件或编码不匹配"
    except FileNotFoundError:
        return f"[Error] 文件不存在: {filepath}"
    except OSError as e:
        return f"[Error] 读取文件失败: {e}"

    # 显示文件信息
    lines = content.count("\n") + 1
    chars = len(content)
    header = f"=== 文件: {filepath} ({lines} 行, {chars} 字符, {encoding}) ===\n\n"
    return header + content


@tool
def read_binary_file(
    filename: str, bytes_per_line: int = 16, max_bytes: int = 1024
) -> str:
    """
    读取二进制文件并以十六进制格式显示

    参数:
        filename: 文件名（相对路径或绝对路径）
        bytes_per_line: 每行显示的字节数，默认16
        max_bytes: 最多读取的字节数，默认1024（用于预览）

    返回:
        文件的十六进制转储内容，包含偏移地址、十六进制值和ASCII表示。
        如果文件不存在或读取失败，返回错误信息
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
            chunk = data[offset : offset + bytes_per_line]

            # 偏移地址
            offset_hex = f"{offset:08x}"

            # 十六进制值
            hex_bytes = " ".join(f"{b:02x}" for b in chunk)

            # ASCII表示
            ascii_chars = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

            lines.append(
                f"{offset_hex}  {hex_bytes:<{bytes_per_line * 3 - 1}}  |{ascii_chars}|"
            )

        return header + "\n".join(lines)
    except FileNotFoundError:
        return f"[Error] 文件不存在: {filepath}"
    except OSError as e:
        return f"[Error] 读取文件失败: {e}"