"""
========================================
Tools Search - 搜索与资讯工具
========================================
功能: 网络搜索、RSS 订阅获取
 作者: CuteCuteYu
"""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

from web.intelligence.rss_parser import fetch_rss_articles

# 创建DuckDuckGo搜索工具实例
search = DuckDuckGoSearchRun()


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
    except Exception as e:  # noqa: BLE001 - 工具约定：任何失败都以错误字符串返回
        return f"[Error] 搜索失败: {e}"


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
    articles = fetch_rss_articles(url, max_items)

    if not articles:
        return f"[Error] 未能获取或解析 RSS 源: {url}"

    # 构建返回结果
    result = f"=== {url} (共 {len(articles)} 条) ===\n\n"
    for i, item in enumerate(articles, 1):
        result += f"{i}. {item.get('title', '无标题')}\n"
        if item.get("link"):
            result += f"   链接: {item['link']}\n"
        if item.get("pubDate"):
            result += f"   时间: {item['pubDate']}\n"
        if item.get("description"):
            desc = item["description"][:200].replace("\n", " ").strip()
            result += f"   摘要: {desc}\n"
        result += "\n"

    return result