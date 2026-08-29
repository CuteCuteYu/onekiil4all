"""
========================================
Trends Parsers - 各平台热搜/新闻解析函数
========================================
功能: 纯函数解析各平台返回的 JSON/XML 文本，便于单元测试
 作者: 上古必斩必杀
"""

import html as html_mod
import json
import re
import urllib.parse

from web.intelligence.rss_parser import parse_feed

# 每个平台保留的条目数
_ITEM_LIMIT = 15


# ═══════════════════════════════════════════════════════════════════════
# 热搜榜单解析
# ═══════════════════════════════════════════════════════════════════════


def parse_weibo(text: str) -> list[dict]:
    """解析微博热搜（weibo.com/ajax/side/hotSearch）"""
    data = json.loads(text).get("data") or {}
    items = []
    for it in data.get("realtime") or []:
        if not isinstance(it, dict) or it.get("is_ad"):
            continue
        word = it.get("word") or it.get("note")
        if not word:
            continue
        items.append(
            {
                "word": word,
                "raw_word": word,
                "source": "微博",
                "url": f"https://s.weibo.com/weibo?q=%23{urllib.parse.quote(word)}%23",
                "hot": it.get("num"),
            }
        )
    return items[:_ITEM_LIMIT]


def parse_baidu(text: str) -> list[dict]:
    """解析百度热搜（top.baidu.com/api/board）"""
    data = json.loads(text).get("data") or {}
    raw: list[dict] = []

    def walk(items):
        for it in items:
            if not isinstance(it, dict):
                continue
            if isinstance(it.get("word"), str):
                raw.append(it)
            if isinstance(it.get("content"), list):
                walk(it["content"])

    for card in data.get("cards") or []:
        if isinstance(card, dict) and isinstance(card.get("content"), list):
            walk(card["content"])

    items = []
    for it in raw[:_ITEM_LIMIT]:
        word = it["word"]
        items.append(
            {
                "word": word,
                "raw_word": word,
                "source": "百度",
                "url": it.get("url")
                or f"https://www.baidu.com/s?wd={urllib.parse.quote(word)}",
                "hot": it.get("hotScore"),
            }
        )
    return items


def parse_toutiao(text: str) -> list[dict]:
    """解析头条热榜（toutiao.com/hot-event/hot-board）"""
    data = json.loads(text).get("data") or []
    items = []
    for it in data:
        title = it.get("Title") or it.get("QueryWord")
        if not title:
            continue
        items.append(
            {
                "word": title,
                "raw_word": title,
                "source": "头条",
                "url": it.get("Url", ""),
                "hot": it.get("HotValue"),
            }
        )
    return items[:_ITEM_LIMIT]


def parse_bilibili(text: str) -> list[dict]:
    """解析B站热搜词（api.bilibili.com/x/web-interface/search/square）"""
    data = json.loads(text).get("data") or {}
    lst = (data.get("trending") or {}).get("list") or []
    items = []
    for it in lst:
        word = it.get("keyword")
        if not word:
            continue
        items.append(
            {
                "word": word,
                "raw_word": word,
                "source": "B站",
                "url": f"https://search.bilibili.com/all?keyword={urllib.parse.quote(word)}",
                "hot": it.get("heat_score"),
            }
        )
    return items[:_ITEM_LIMIT]


def parse_douyin(text: str) -> list[dict]:
    """解析抖音热点榜（iesdouyin.com/web/api/v2/hotsearch/billboard/word）"""
    data = json.loads(text)
    items = []
    for it in data.get("word_list") or []:
        word = it.get("word")
        if not word:
            continue
        items.append(
            {
                "word": word,
                "raw_word": word,
                "source": "抖音",
                "url": f"https://www.douyin.com/search/{urllib.parse.quote(word)}",
                "hot": it.get("hot_value"),
            }
        )
    return items[:_ITEM_LIMIT]


# ═══════════════════════════════════════════════════════════════════════
# GitHub 解析（Search API，近7天新建仓库按star排序）
# ═══════════════════════════════════════════════════════════════════════


def parse_github_search(text: str) -> list[dict]:
    """解析 GitHub Search API 返回的仓库列表"""
    data = json.loads(text)
    items = []
    for it in data.get("items") or []:
        full_name = it.get("full_name", "")
        if not full_name:
            continue
        items.append(
            {
                "name": full_name.split("/")[-1],
                "full_name": full_name,
                "description": it.get("description") or "",
                "stars": it.get("stargazers_count", 0),
                "url": it.get("html_url", ""),
                "language": it.get("language") or "",
            }
        )
    return items[:10]


# ═══════════════════════════════════════════════════════════════════════
# 科技新闻解析
# ═══════════════════════════════════════════════════════════════════════


def parse_hn_ids(text: str) -> list[int]:
    """解析 HackerNews topstories 的 id 列表"""
    ids = json.loads(text)
    return [i for i in ids if isinstance(i, int)][:_ITEM_LIMIT]


def parse_hn_item(item: dict) -> dict:
    """将 HackerNews item JSON 转为科技新闻条目"""
    return {
        "title": item.get("title", ""),
        "url": item.get("url")
        or f"https://news.ycombinator.com/item?id={item.get('id', '')}",
        "source": "HackerNews",
    }


def parse_kr36(text: str) -> list[dict]:
    """解析36氪热榜（gateway.36kr.com rank/hot）"""
    data = json.loads(text).get("data") or {}
    items = []
    for it in data.get("hotRankList") or []:
        material = it.get("templateMaterial") or {}
        title = _strip_html(material.get("widgetTitle") or material.get("title") or "")
        if not title:
            continue
        item_id = it.get("itemId") or material.get("itemId") or ""
        url = f"https://36kr.com/p/{item_id}" if item_id else ""
        items.append({"title": title, "url": url, "source": "36氪"})
    return items[:_ITEM_LIMIT]


def rss_to_news_items(text: str, source_name: str) -> list[dict]:
    """将 RSS/Atom 内容解析为科技新闻条目（复用 rss_parser）"""
    articles = parse_feed(text)
    return [
        {"title": a["title"], "url": a["link"], "source": source_name}
        for a in articles
        if a.get("title")
    ][:_ITEM_LIMIT]


def _strip_html(text: str) -> str:
    """去掉文本中的 HTML 标签并反转义"""
    return html_mod.unescape(re.sub(r"<[^>]+>", "", text)).strip()