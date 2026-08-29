"""
========================================
Trends Fetchers - 各平台网络抓取模块
========================================
功能: 并发抓取各平台热点数据，单平台失败不影响其他平台
 作者: 上古必斩必杀
"""

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta

import requests

from web.intelligence.trends.parsers import (
    parse_baidu,
    parse_bilibili,
    parse_douyin,
    parse_github_search,
    parse_hn_ids,
    parse_hn_item,
    parse_kr36,
    parse_toutiao,
    parse_weibo,
    rss_to_news_items,
)

logger = logging.getLogger(__name__)

# 创建线程池，全局复用
_executor = ThreadPoolExecutor(max_workers=8)

# GitHub Search API 无鉴权限 60 次/小时，单独用长缓存避开速率限制
_GITHUB_CACHE_TTL = 900.0

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

# 微博接口需要 Referer 才能匿名访问
_WB_HEADERS = {**_HEADERS, "Referer": "https://weibo.com/"}


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


def fetch_all_trends() -> dict:
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


def shutdown_executor():
    """关闭全局线程池（服务退出时调用）"""
    _executor.shutdown(wait=False)