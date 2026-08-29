"""
========================================
Background Tasks - 后台任务模块
========================================
功能: 告警检查与 RSS 抓取的后台循环任务
 作者: 上古必斩必杀
"""

import asyncio
import logging
import os
from datetime import UTC, datetime

from web.intelligence.rss_manager import rss_manager
from web.intelligence.rss_parser import fetch_rss_articles
from web.intelligence.trends import get_trends
from web.sse import EventBroadcaster

logger = logging.getLogger(__name__)

# 后台检查间隔（秒），可用环境变量覆盖
ALERT_CHECK_INTERVAL = float(os.environ.get("ALERT_CHECK_INTERVAL", "30"))
RSS_CHECK_INTERVAL = float(os.environ.get("RSS_CHECK_INTERVAL", "10"))


async def check_rss_sources(rss_broadcaster: EventBroadcaster):
    """
    检查所有到期的RSS源并推送新文章

    抓取失败时同样记录抓取时间，形成按 fetch_interval 的自然退避，
    避免源暂时不可用时的重试风暴
    """
    now = datetime.now(UTC)
    sources = await asyncio.to_thread(rss_manager.get_all_sources)

    for source in sources:
        if not source.enabled:
            continue

        last_time = None
        if source.last_fetch:
            try:
                last_time = datetime.fromisoformat(source.last_fetch)
            except (ValueError, TypeError):
                # 兼容旧数据中无时区的 naive 时间戳
                last_time = None

        if last_time and (now - last_time).total_seconds() < source.fetch_interval:
            continue

        articles = await asyncio.to_thread(fetch_rss_articles, source.url)

        # 只推送上次抓取之后新出现的文章
        old_links = {a.get("link") for a in source.articles}
        new_articles = [
            a for a in articles if a.get("link") and a["link"] not in old_links
        ]

        # 成功与失败都记录抓取时间（失败保留旧文章）
        await asyncio.to_thread(rss_manager.update_source, source.id, articles)

        for article in new_articles[:3]:
            rss_broadcaster.publish(
                {
                    "type": "rss",
                    "article": {
                        "source_id": source.id,
                        "source_name": source.name,
                        "url": source.url,
                        "title": article.get("title", ""),
                        "link": article.get("link", ""),
                        "pubDate": article.get("pubDate", ""),
                        "description": article.get("description", ""),
                    },
                }
            )


async def alert_checker(alert_broadcaster: EventBroadcaster):
    """后台告警检查任务，按 ALERT_CHECK_INTERVAL 间隔执行"""
    while True:
        try:
            await asyncio.sleep(ALERT_CHECK_INTERVAL)

            trends = await asyncio.to_thread(get_trends, check_alerts=True)
            for alert_event in trends.get("new_alerts", []):
                alert_broadcaster.publish({"type": "alert", "event": alert_event})

        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("告警检查异常")


async def rss_checker(rss_broadcaster: EventBroadcaster):
    """后台RSS抓取任务，按 RSS_CHECK_INTERVAL 间隔执行"""
    while True:
        try:
            await asyncio.sleep(RSS_CHECK_INTERVAL)
            await check_rss_sources(rss_broadcaster)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("RSS 抓取异常")