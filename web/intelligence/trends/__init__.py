"""
========================================
Trends - 热点资讯获取模块
========================================
功能: 自建多平台热点抓取（不依赖第三方聚合站）

数据来源:
- 热搜榜单: 微博、百度、头条、B站、抖音 官方接口
- GitHub: GitHub Search API（近7天新建仓库按star排序，独立长缓存）
- 科技新闻: HackerNews、少数派、钛媒体、36氪、InfoQ

模块结构:
- parsers.py      各平台解析纯函数
- fetchers.py     网络抓取与并发调度
- keywords.py     中英文关键词提取
- associations.py 关键词关联分析
 作者: 上古必斩必杀
"""

import copy
import logging
import threading
import time

from web.intelligence.trends.associations import get_keyword_associations
from web.intelligence.trends.fetchers import fetch_all_trends, shutdown_executor

logger = logging.getLogger(__name__)

# 趋势数据缓存（API请求、关联分析和后台告警检查共用，消掉大部分重复外呼）
_TRENDS_CACHE_TTL = 30.0

_trends_cache: dict | None = None
_trends_cache_time = 0.0
_trends_lock = threading.Lock()


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
            fresh = fetch_all_trends()
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


__all__ = [
    "get_keyword_associations",
    "get_trends",
    "shutdown_executor",
]