"""
========================================
Trends - 热点资讯获取模块
========================================
功能: 自建多平台热点抓取（不依赖第三方聚合站）

数据来源:
- 热搜榜单: 微博、百度、头条、B站、抖音 官方接口
- GitHub: GitHub Search API（近7天新建仓库按star排序，独立长缓存）
- 科技新闻: HackerNews、少数派、钛媒体、36氪、InfoQ
 作者: 上古必斩必杀
"""

import copy
import html as html_mod
import json
import logging
import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta

import requests

from web.intelligence.rss_parser import parse_feed

logger = logging.getLogger(__name__)

# 创建线程池，全局复用
_executor = ThreadPoolExecutor(max_workers=8)

# 趋势数据缓存（API请求、关联分析和后台告警检查共用，消掉大部分重复外呼）
_TRENDS_CACHE_TTL = 30.0
# GitHub Search API 无鉴权限 60 次/小时，单独用长缓存避开速率限制
_GITHUB_CACHE_TTL = 900.0

_trends_cache: dict | None = None
_trends_cache_time = 0.0
_trends_lock = threading.Lock()

_github_cache: list[dict] | None = None
_github_cache_time = 0.0
_github_lock = threading.Lock()

# 平台到数据分类的映射
_PLATFORM_MAP = {
    "hot_search": ["weibo", "baidu", "toutiao", "bilibili", "douyin"],
    "github": ["github"],
    "tech_news": ["hackernews", "sspai", "tmtpost", "kr36", "infoq"],
}

# 统一的浏览器 UA
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

# 每个平台保留的条目数
_ITEM_LIMIT = 15

# 微博接口需要 Referer 才能匿名访问
_WB_HEADERS = {**_HEADERS, "Referer": "https://weibo.com/"}


# ═══════════════════════════════════════════════════════════════════════
# 热搜榜单解析（纯函数，便于测试）
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


# ═══════════════════════════════════════════════════════════════════════
# 网络抓取函数
# ═══════════════════════════════════════════════════════════════════════


def _get_json(url: str, **kw) -> dict | list | None:
    """GET 请求并解析 JSON，失败返回 None"""
    try:
        headers = kw.pop("headers", _HEADERS)
        res = requests.get(url, headers=headers, timeout=8, **kw)
        res.raise_for_status()
        return res.json()
    except (requests.RequestException, ValueError) as e:
        logger.debug("请求失败 %s: %s", url, e)
        return None


def _fetch_weibo() -> list[dict]:
    data = _get_json("https://weibo.com/ajax/side/hotSearch", headers=_WB_HEADERS)
    return parse_weibo(json.dumps(data, ensure_ascii=False)) if data else []


def _fetch_baidu() -> list[dict]:
    data = _get_json("https://top.baidu.com/api/board?platform=wise&tab=realtime")
    return parse_baidu(json.dumps(data, ensure_ascii=False)) if data else []


def _fetch_toutiao() -> list[dict]:
    data = _get_json("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    return parse_toutiao(json.dumps(data, ensure_ascii=False)) if data else []


def _fetch_bilibili() -> list[dict]:
    data = _get_json("https://api.bilibili.com/x/web-interface/search/square?limit=10")
    return parse_bilibili(json.dumps(data, ensure_ascii=False)) if data else []


def _fetch_douyin() -> list[dict]:
    data = _get_json("https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/")
    return parse_douyin(json.dumps(data, ensure_ascii=False)) if data else []


def _fetch_github() -> list[dict]:
    """抓取 GitHub 热门新仓库（独立 15 分钟缓存避开 Search API 速率限制）"""
    global _github_cache, _github_cache_time

    with _github_lock:
        now = time.monotonic()
        if _github_cache is not None and now - _github_cache_time < _GITHUB_CACHE_TTL:
            return _github_cache

        since = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")
        url = (
            "https://api.github.com/search/repositories"
            f"?q=created:%3E{since}&sort=stars&order=desc&per_page=10"
        )
        data = _get_json(url)
        items = (
            parse_github_search(json.dumps(data, ensure_ascii=False)) if data else []
        )

        if items:
            _github_cache = items
            _github_cache_time = now
        return items


def _fetch_hackernews() -> list[dict]:
    """抓取 HackerNews 热帖（topstories + 并发取详情）"""
    ids_data = _get_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    ids = parse_hn_ids(json.dumps(ids_data, ensure_ascii=False)) if ids_data else []
    if not ids:
        return []

    def fetch_item(item_id: int) -> dict | None:
        item = _get_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
        return item if isinstance(item, dict) else None

    items = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(fetch_item, ids[:10]):
            if result:
                items.append(parse_hn_item(result))
    return items


def _fetch_sspai() -> list[dict]:
    res = requests.get("https://sspai.com/feed", headers=_HEADERS, timeout=8)
    res.raise_for_status()
    return rss_to_news_items(res.text, "少数派")


def _fetch_tmtpost() -> list[dict]:
    res = requests.get("https://www.tmtpost.com/rss", headers=_HEADERS, timeout=8)
    res.raise_for_status()
    return rss_to_news_items(res.text, "钛媒体")


def _fetch_infoq() -> list[dict]:
    res = requests.get("https://www.infoq.cn/feed", headers=_HEADERS, timeout=8)
    res.raise_for_status()
    return rss_to_news_items(res.text, "InfoQ")


def _fetch_kr36() -> list[dict]:
    res = requests.post(
        "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot",
        headers=_HEADERS,
        json={"partner_id": "wap", "param": {"siteId": 1, "platformId": 2}},
        timeout=8,
    )
    res.raise_for_status()
    return parse_kr36(res.text)


# 平台到抓取函数的分发表
_FETCHERS = {
    "weibo": _fetch_weibo,
    "baidu": _fetch_baidu,
    "toutiao": _fetch_toutiao,
    "bilibili": _fetch_bilibili,
    "douyin": _fetch_douyin,
    "github": _fetch_github,
    "hackernews": _fetch_hackernews,
    "sspai": _fetch_sspai,
    "tmtpost": _fetch_tmtpost,
    "infoq": _fetch_infoq,
    "kr36": _fetch_kr36,
}


def _fetch_platform(platform: str) -> tuple[str, list]:
    """获取单个平台的数据（单平台失败不影响其他平台）"""
    try:
        return platform, _FETCHERS[platform]()
    except Exception as e:  # noqa: BLE001 - 平台级兜底：单平台异常仅丢弃该平台数据
        logger.debug("平台 %s 抓取失败: %s", platform, e)
        return platform, []


def _fetch_all_trends() -> dict:
    """并发抓取所有平台数据并归类整理"""
    trends_data: dict = {"hot_search": [], "github": [], "tech_news": []}

    try:
        platforms = (
            _PLATFORM_MAP["hot_search"]
            + _PLATFORM_MAP["github"]
            + _PLATFORM_MAP["tech_news"]
        )

        futures = {_executor.submit(_fetch_platform, p): p for p in platforms}

        for future in as_completed(futures):
            platform, data = future.result()

            if platform in _PLATFORM_MAP["hot_search"]:
                trends_data["hot_search"].extend(data)
            elif platform in _PLATFORM_MAP["github"]:
                trends_data["github"] = data
            elif platform in _PLATFORM_MAP["tech_news"]:
                trends_data["tech_news"].extend(data)

        if not trends_data["hot_search"]:
            trends_data["hot_search"] = [
                {"word": "暂无数据", "raw_word": "", "source": "", "url": ""}
            ]
        if not trends_data["github"]:
            trends_data["github"] = [
                {
                    "name": "暂无数据",
                    "full_name": "",
                    "description": "",
                    "stars": 0,
                    "url": "",
                    "language": "",
                }
            ]
        if not trends_data["tech_news"]:
            trends_data["tech_news"] = [{"title": "暂无数据", "url": "", "source": ""}]

        return trends_data

    except Exception as e:
        logger.exception("趋势数据抓取异常")
        return {
            "error": str(e),
            "hot_search": [],
            "github": [],
            "tech_news": [],
        }


def get_trends(check_alerts: bool = False) -> dict:
    """
    获取热门搜索和情报信息（带 TTL 缓存）

    参数:
        check_alerts: 是否检查并触发告警，默认False

    返回:
        字典，包含以下键:
        - hot_search: 热搜列表
        - github: GitHub趋势列表
        - tech_news: 科技新闻列表
        - new_alerts: 新触发的告警事件（仅当check_alerts=True时）
    """
    global _trends_cache, _trends_cache_time

    with _trends_lock:
        if (
            _trends_cache is None
            or time.monotonic() - _trends_cache_time > _TRENDS_CACHE_TTL
        ):
            fresh = _fetch_all_trends()
            if "error" not in fresh:
                _trends_cache = fresh
                _trends_cache_time = time.monotonic()
            source = fresh if "error" in fresh else _trends_cache
        else:
            source = _trends_cache
        trends_data = copy.deepcopy(source)

    if check_alerts:
        from web.intelligence.alert_manager import alert_manager

        new_events = alert_manager.check_alerts(trends_data)
        if new_events:
            trends_data["new_alerts"] = [e.to_dict() for e in new_events]

    return trends_data


def get_keyword_associations(keyword: str) -> dict:
    """
    获取指定关键词的关联分析

    参数:
        keyword: 用户输入的关键词

    返回:
        包含关联词条和得分的字典
    """
    if not keyword or len(keyword.strip()) < 2:
        return {"keyword": keyword, "associations": []}

    keyword = keyword.strip().lower()
    keyword_lower = keyword

    trends = get_trends()

    titles = []

    for item in trends.get("hot_search", []):
        if item.get("word"):
            titles.append(item["word"])

    for item in trends.get("github", []):
        name = item.get("name", "")
        desc = item.get("description", "")
        if name:
            titles.append(name)
        if desc:
            titles.append(desc)

    for item in trends.get("tech_news", []):
        if item.get("title"):
            titles.append(item["title"])

    co_occur = {}

    for title in titles:
        title_lower = title.lower()

        if keyword_lower not in title_lower:
            continue

        words = extract_keywords(title)

        for word in words:
            if word != keyword and len(word) >= 2:
                if word not in co_occur:
                    co_occur[word] = 0
                co_occur[word] += 1

    associations = []
    for word, count in co_occur.items():
        score = min(count / 5, 1.0)
        associations.append({"keyword": word, "score": round(score, 2)})

    associations.sort(key=lambda x: x["score"], reverse=True)

    return {
        "keyword": keyword,
        "associations": associations[:15],
    }


def extract_keywords(text: str) -> list:
    """从文本中提取关键词"""
    chinese = re.findall(r"[\u4e00-\u9fff]+", text)
    english = re.findall(r"[a-zA-Z]{3,}", text)

    keywords = []

    for word in chinese:
        if len(word) >= 2:
            for i in range(len(word) - 1):
                keywords.append(word[i : i + 2])

    keywords.extend([w.lower() for w in english])

    return keywords


def shutdown_executor():
    """关闭全局线程池（服务退出时调用）"""
    _executor.shutdown(wait=False)
