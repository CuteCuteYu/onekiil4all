import requests


def get_trends() -> dict:
    """获取热门搜索和情报信息"""
    trends_data = {"hot_search": [], "github": [], "tech_news": []}

    platform_map = {
        "hot_search": ["baidu", "weibo", "zhihu", "douyin", "bilibili"],
        "github": ["github"],
        "tech_news": ["sspai", "tskr", "juejin", "vtex", "hackernews"],
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        platforms = (
            platform_map.get("hot_search", [])
            + platform_map.get("github", [])
            + platform_map.get("tech_news", [])
        )

        for platform in platforms:
            try:
                res = requests.get(
                    f"https://orz.ai/api/v1/dailynews/?platform={platform}",
                    headers=headers,
                    timeout=15,
                )
                if res.status_code == 200:
                    json_data = res.json()
                    data = (
                        json_data.get("data", [])
                        if isinstance(json_data, dict)
                        else json_data
                    )

                    if platform in platform_map["hot_search"]:
                        if isinstance(data, list):
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
                        if isinstance(data, list):
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
                        if isinstance(data, list):
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
            except Exception:
                pass

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
        return {
            "error": str(e),
            "hot_search": [],
            "github": [],
            "tech_news": [],
        }
