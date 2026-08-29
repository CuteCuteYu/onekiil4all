"""
========================================
RSS Parser - RSS/Atom 公共解析模块
========================================
功能: 抓取并解析 RSS/Atom 订阅源，
供 rss_manager（后台订阅）和 tools_set（Agent工具）共用，
避免三处复制的解析逻辑
 作者: CuteCuteYu
"""

import logging
import urllib.request
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# 抓取请求使用的 User-Agent
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Atom 命名空间
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

# 摘要保留的最大长度
_DESCRIPTION_LIMIT = 200


def fetch_rss_articles(url: str, max_items: int = 10) -> list[dict]:
    """
    抓取并解析 RSS/Atom 订阅源

    参数:
        url: 订阅源地址
        max_items: 最多解析的文章数

    返回:
        文章字典列表（title/link/pubDate/description），抓取失败返回空列表
    """
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode("utf-8", errors="replace")
        return parse_feed(content, max_items)
    except OSError as e:
        logger.warning("RSS 源抓取失败 %s: %s", url, e)
        return []


def parse_feed(content: str, max_items: int = 10) -> list[dict]:
    """
    解析 RSS/Atom XML 文本

    参数:
        content: XML 文本
        max_items: 最多解析的文章数

    返回:
        文章字典列表，解析失败返回空列表
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.warning("RSS 解析失败: %s", e)
        return []

    if root.tag == "rss":
        return _parse_rss(root, max_items)
    if root.tag == "feed" or root.tag == f"{{{_ATOM_NS['atom']}}}feed":
        return _parse_atom(root, max_items)
    return []


def _find(elem: ET.Element, path: str) -> ET.Element | None:
    """先按带命名空间查找，再退回不带命名空间的标签"""
    found = elem.find(path, _ATOM_NS)
    if found is None:
        found = elem.find(path.replace("atom:", ""))
    return found


def _clean_description(text: str | None) -> str:
    """清理并截断摘要文本"""
    if not text:
        return ""
    return text[:_DESCRIPTION_LIMIT].replace("\n", " ").strip()


def _parse_rss(root: ET.Element, max_items: int) -> list[dict]:
    """解析 RSS 2.0 格式"""
    channel = root.find("channel")
    if channel is None:
        return []

    articles = []
    for item in channel.findall("item")[:max_items]:
        title_elem = item.find("title")
        link_elem = item.find("link")
        desc_elem = item.find("description")
        pub_elem = item.find("pubDate")

        article = {
            "title": (title_elem.text or "").strip() if title_elem is not None else "",
            "link": (link_elem.text or "").strip() if link_elem is not None else "",
            "pubDate": (pub_elem.text or "").strip() if pub_elem is not None else "",
            "description": _clean_description(
                desc_elem.text if desc_elem is not None else None
            ),
        }
        if article["title"]:
            articles.append(article)

    return articles


def _parse_atom(root: ET.Element, max_items: int) -> list[dict]:
    """解析 Atom 格式"""
    articles = []

    for entry in (
        root.findall("atom:entry", _ATOM_NS)[:max_items]
        or root.findall("entry")[:max_items]
    ):
        title_elem = _find(entry, "atom:title")
        link_elem = _find(entry, "atom:link")
        updated_elem = _find(entry, "atom:updated")

        link = ""
        if link_elem is not None:
            link = link_elem.get("href") or (link_elem.text or "").strip()

        # 优先 summary，为空时取 content
        desc_elem = _find(entry, "atom:summary")
        if desc_elem is None:
            desc_elem = _find(entry, "atom:content")

        article = {
            "title": (title_elem.text or "").strip() if title_elem is not None else "",
            "link": link,
            "pubDate": (updated_elem.text or "").strip()
            if updated_elem is not None
            else "",
            "description": _clean_description(
                desc_elem.text if desc_elem is not None else None
            ),
        }
        if article["title"]:
            articles.append(article)

    return articles
