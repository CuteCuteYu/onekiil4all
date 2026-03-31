"""
========================================
Trends - 热点资讯获取模块
========================================
功能: 获取并整合各类热点资讯数据
包括: 热搜榜单、GitHub趋势、科技新闻
 作者: 上古必斩必杀
"""

# ═══════════════════════════════════════════════════════════════
# 导入标准库
# ═══════════════════════════════════════════════════════════════

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 创建线程池，全局复用
_executor = ThreadPoolExecutor(max_workers=8)


def _fetch_platform(platform: str) -> tuple[str, list]:
    """获取单个平台的数据"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(
            f"https://orz.ai/api/v1/dailynews/?platform={platform}",
            headers=headers,
            timeout=15,
        )
        if res.status_code == 200:
            json_data = res.json()
            data = (
                json_data.get("data", []) if isinstance(json_data, dict) else json_data
            )
            return platform, data if isinstance(data, list) else []
        return platform, []
    except Exception:
        return platform, []


def get_trends(check_alerts: bool = False) -> dict:
    """
    获取热门搜索和情报信息

    参数:
        check_alerts: 是否检查并触发告警，默认False

    从多个平台获取热点数据：
    - 热搜平台: 百度、微博、知乎、抖音、B站
    - GitHub: GitHub趋势
    - 科技新闻: 少数派、钛媒体、掘金、V2EX、HackerNews

    返回:
        字典，包含以下键:
        - hot_search: 热搜列表
        - github: GitHub趋势列表
        - tech_news: 科技新闻列表
        - new_alerts: 新触发的告警事件（仅当check_alerts=True时）
    """
    trends_data = {"hot_search": [], "github": [], "tech_news": []}

    platform_map = {
        "hot_search": ["baidu", "weibo", "zhihu", "douyin", "bilibili"],
        "github": ["github"],
        "tech_news": ["sspai", "tskr", "juejin", "vtex", "hackernews"],
    }

    try:
        platforms = (
            platform_map.get("hot_search", [])
            + platform_map.get("github", [])
            + platform_map.get("tech_news", [])
        )

        futures = {_executor.submit(_fetch_platform, p): p for p in platforms}

        for future in as_completed(futures):
            platform, data = future.result()

            if platform in platform_map["hot_search"]:
                trends_data["hot_search"].extend(
                    [
                        {
                            "word": item.get("title", ""),
                            "raw_word": item.get("title", ""),
                            "source": item.get("source", platform),
                            "url": item.get("url", ""),
                        }
                        for item in data[:15]
                    ]
                )

            elif platform in platform_map["github"]:
                if data:
                    trends_data["github"] = [
                        {
                            "name": item.get("title", "").split("/")[-1]
                            if "/" in item.get("title", "")
                            else item.get("title", ""),
                            "full_name": item.get("title", ""),
                            "description": item.get("content", ""),
                            "stars": 0,
                            "url": item.get("url", ""),
                            "language": item.get("source", ""),
                        }
                        for item in data[:10]
                    ]

            elif platform in platform_map["tech_news"]:
                trends_data["tech_news"].extend(
                    [
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", platform),
                        }
                        for item in data[:10]
                    ]
                )

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

        if check_alerts:
            from web.alert_manager import alert_manager

            new_events = alert_manager.check_alerts(trends_data)
            if new_events:
                trends_data["new_alerts"] = [e.to_dict() for e in new_events]

        return trends_data

    except Exception as e:
        result = {
            "error": str(e),
            "hot_search": [],
            "github": [],
            "tech_news": [],
        }
        if check_alerts:
            result["new_alerts"] = []
        return result


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
    import re

    chinese = re.findall(r"[\u4e00-\u9fff]+", text)
    english = re.findall(r"[a-zA-Z]{3,}", text)

    keywords = []

    for word in chinese:
        if len(word) >= 2:
            for i in range(len(word) - 1):
                keywords.append(word[i : i + 2])

    keywords.extend([w.lower() for w in english])

    return keywords
