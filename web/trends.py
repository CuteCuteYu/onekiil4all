"""
========================================
Trends - 热点资讯获取模块
========================================
功能: 获取并整合各类热点资讯数据
包括: 热搜榜单、GitHub趋势、科技新闻
作者: onekiil4all
"""

# ═══════════════════════════════════════════════════════════════
# 导入标准库
# ═══════════════════════════════════════════════════════════════

import requests


def get_trends() -> dict:
    """
    获取热门搜索和情报信息

    从多个平台获取热点数据：
    - 热搜平台: 百度、微博、知乎、抖音、B站
    - GitHub: GitHub趋势
    - 科技新闻: 少数派、钛媒体、掘金、V2EX、HackerNews

    返回:
        字典，包含以下键:
        - hot_search: 热搜列表
        - github: GitHub趋势列表
        - tech_news: 科技新闻列表
    """
    # 初始化返回数据结构
    trends_data = {"hot_search": [], "github": [], "tech_news": []}

    # 平台分类映射
    platform_map = {
        "hot_search": ["baidu", "weibo", "zhihu", "douyin", "bilibili"],
        "github": ["github"],
        "tech_news": ["sspai", "tskr", "juejin", "vtex", "hackernews"],
    }

    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # 合并所有平台
        platforms = (
            platform_map.get("hot_search", [])
            + platform_map.get("github", [])
            + platform_map.get("tech_news", [])
        )

        # 遍历每个平台获取数据
        for platform in platforms:
            try:
                # 发送HTTP GET请求
                res = requests.get(
                    f"https://orz.ai/api/v1/dailynews/?platform={platform}",
                    headers=headers,
                    timeout=15,  # 15秒超时
                )

                # 检查响应状态
                if res.status_code == 200:
                    json_data = res.json()
                    # 获取数据列表
                    data = (
                        json_data.get("data", [])
                        if isinstance(json_data, dict)
                        else json_data
                    )

                    # ═══════════════════════════════════════════════════════
                    # 处理热搜数据
                    # ═══════════════════════════════════════════════════════
                    if platform in platform_map["hot_search"]:
                        if isinstance(data, list):
                            trends_data["hot_search"].extend(
                                [
                                    {
                                        "word": item.get("title", ""),  # 标题
                                        "raw_word": item.get("title", ""),  # 原始标题
                                        "source": item.get("source", platform),  # 来源
                                        "url": item.get("url", ""),  # 链接
                                    }
                                    for item in data[:15]  # 取前15条
                                ]
                            )

                    # ═══════════════════════════════════════════════════════
                    # 处理GitHub趋势数据
                    # ═══════════════════════════════════════════════════════
                    elif platform in platform_map["github"]:
                        if isinstance(data, list):
                            trends_data["github"] = [
                                {
                                    "name": item.get("title", "").split("/")[-1]
                                    if "/" in item.get("title", "")
                                    else item.get("title", ""),  # 项目名称
                                    "full_name": item.get("title", ""),  # 完整名称
                                    "description": item.get("content", ""),  # 项目描述
                                    "stars": 0,  # 星级（暂无）
                                    "url": item.get("url", ""),  # 项目链接
                                    "language": item.get("source", ""),  # 编程语言
                                }
                                for item in data[:10]  # 取前10条
                            ]

                    # ═══════════════════════════════════════════════════════
                    # 处理科技新闻数据
                    # ═══════════════════════════════════════════════════════
                    elif platform in platform_map["tech_news"]:
                        if isinstance(data, list):
                            trends_data["tech_news"].extend(
                                [
                                    {
                                        "title": item.get("title", ""),  # 文章标题
                                        "url": item.get("url", ""),  # 文章链接
                                        "source": item.get("source", platform),  # 来源
                                    }
                                    for item in data[:10]  # 取前10条
                                ]
                            )
            except Exception:
                # 单个平台失败不影响其他平台
                pass

        # ═══════════════════════════════════════════════════════════════
        # 处理空数据情况
        # ═══════════════════════════════════════════════════════════════

        # 如果没有热搜数据，添加提示
        if not trends_data["hot_search"]:
            trends_data["hot_search"] = [
                {"word": "暂无数据", "raw_word": "", "source": "", "url": ""}
            ]
        # 如果没有GitHub数据
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
        # 如果没有科技新闻数据
        if not trends_data["tech_news"]:
            trends_data["tech_news"] = [{"title": "暂无数据", "url": "", "source": ""}]

        return trends_data

    except Exception as e:
        # 发生错误时返回错误信息
        return {
            "error": str(e),
            "hot_search": [],
            "github": [],
            "tech_news": [],
        }
