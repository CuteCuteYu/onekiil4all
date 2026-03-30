"""
========================================
Tools Set - 工具集模块
========================================
功能: 定义AI Agent可用的工具函数
包括: 网络搜索、PowerShell命令执行、文件读写、RSS订阅获取等
作者: onekiil4all
"""

# ═══════════════════════════════════════════════════════════════
# 导入标准库
# ═══════════════════════════════════════════════════════════════

import subprocess  # 执行系统命令
from pathlib import Path  # 路径处理
import urllib.request  # 网络请求
import urllib.error  # 网络错误处理
import xml.etree.ElementTree as ET  # XML解析

# ═══════════════════════════════════════════════════════════════
# 导入LangChain工具
# ═══════════════════════════════════════════════════════════════

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun


# ═══════════════════════════════════════════════════════════════
# 初始化搜索工具
# ═══════════════════════════════════════════════════════════════

# 创建DuckDuckGo搜索工具实例
search = DuckDuckGoSearchRun()


# ═══════════════════════════════════════════════════════════════
# 工具函数定义
# ═══════════════════════════════════════════════════════════════


@tool
def web_search(query: str) -> str:
    """
    使用DuckDuckGo搜索网络，获取实时信息

    参数:
        query: 搜索关键词或问题

    返回:
        搜索结果列表，包含标题、链接和摘要
    """
    try:
        result = search.run(query)
        return result
    except Exception as e:
        return f"[Error] 搜索失败: {e}"


@tool
def run_powershell(command: str) -> str:
    """
    在PowerShell中运行命令并返回输出结果

    参数:
        command: 要执行的PowerShell命令

    返回:
        命令的标准输出内容。如果执行失败（返回码非0），
        则在输出末尾附加"[Error]"前缀的错误信息（stderr）
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
        encoding: 文件编码，默认为utf-8

    返回:
        文件的文本内容。如果文件不存在或读取失败，返回错误信息
    """
    filepath = Path(filename)
    if not filepath.is_absolute():
        filepath = Path.cwd() / filename

    try:
        content = filepath.read_text(encoding=encoding)
        # 显示文件信息
        lines = content.count("\n") + 1
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
    except Exception as e:
        return f"[Error] 读取文件失败: {e}"


@tool
def fetch_rss_feed(url: str, max_items: int = 10) -> str:
    """
    获取并解析RSS/Atom订阅源，返回最新文章列表

    参数:
        url: RSS或Atom订阅源的URL地址
        max_items: 最多返回的文章数量，默认10

    返回:
        订阅源的最新文章列表，每条包含标题、链接、发布时间和摘要。
        如果获取失败，返回错误信息
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode("utf-8")

        root = ET.fromstring(content)

        ns = {"atom": "http://www.w3.org/2005/Atom"}

        channel_title = ""
        items = []

        # 处理RSS格式
        if root.tag == "rss":
            channel = root.find("channel")
            if channel is not None:
                title_elem = channel.find("title")
                if title_elem is not None:
                    channel_title = title_elem.text or ""

                for item in channel.findall("item")[:max_items]:
                    item_data = {}
                    title_elem = item.find("title")
                    if title_elem is not None:
                        item_data["title"] = title_elem.text or ""

                    link_elem = item.find("link")
                    if link_elem is not None:
                        item_data["link"] = link_elem.text or ""
                    else:
                        item_data["link"] = ""

                    desc_elem = item.find("description")
                    if desc_elem is not None:
                        item_data["description"] = desc_elem.text or ""

                    pub_elem = item.find("pubDate")
                    if pub_elem is not None:
                        item_data["pubDate"] = pub_elem.text or ""

                    if item_data.get("title"):
                        items.append(item_data)

        # 处理Atom格式
        elif root.tag == "{http://www.w3.org/2005/Atom}feed" or root.tag == "feed":
            feed_ns = root
            title_elem = feed_ns.find("title")
            if title_elem is not None:
                channel_title = title_elem.text or ""

            entries = feed_ns.findall("entry")[:max_items]
            for entry in entries:
                item_data = {}

                title_elem = entry.find("title")
                if title_elem is not None:
                    item_data["title"] = title_elem.text or ""

                link_elem = entry.find("link")
                if link_elem is not None:
                    href = link_elem.get("href")
                    if href:
                        item_data["link"] = href
                    else:
                        item_data["link"] = ""
                else:
                    item_data["link"] = ""

                summary_elem = entry.find("summary")
                if summary_elem is not None:
                    item_data["description"] = summary_elem.text or ""
                else:
                    content_elem = entry.find("content")
                    if content_elem is not None:
                        item_data["description"] = content_elem.text or ""

                updated_elem = entry.find("updated")
                if updated_elem is not None:
                    item_data["pubDate"] = updated_elem.text or ""

                if item_data.get("title"):
                    items.append(item_data)

    except urllib.error.URLError as e:
        return f"[Error] 无法访问 RSS 源: {e}"
    except ET.ParseError as e:
        return f"[Error] RSS 解析失败: {e}"
    except Exception as e:
        return f"[Error] 获取 RSS 失败: {e}"

    if not channel_title:
        channel_title = url

    if not items:
        return f"[Error] 未能解析 RSS 源: {url}"

    # 构建返回结果
    result = f"=== {channel_title} (共 {len(items)} 条) ===\n\n"
    for i, item in enumerate(items, 1):
        result += f"{i}. {item.get('title', '无标题')}\n"
        if item.get("link"):
            result += f"   链接: {item['link']}\n"
        if item.get("pubDate"):
            result += f"   时间: {item['pubDate']}\n"
        if item.get("description"):
            desc = item["description"][:200].replace("\n", " ").strip()
            if len(item.get("description", "")) > 200:
                desc += "..."
            result += f"   摘要: {desc}\n"
        result += "\n"

    return result


# ═══════════════════════════════════════════════════════════════
# 工具列表导出
# ═══════════════════════════════════════════════════════════════

# 所有可用工具的列表，供Agent使用
tools = [
    run_powershell,  # PowerShell命令执行
    write_file,  # 文件写入
    read_text_file,  # 文本文件读取
    read_binary_file,  # 二进制文件读取
    fetch_rss_feed,  # RSS订阅获取
    web_search,  # 网络搜索
]
