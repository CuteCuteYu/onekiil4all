"""多平台热搜解析函数测试"""

import json

from web.intelligence.trends import (
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


def test_parse_weibo():
    payload = {
        "data": {
            "realtime": [
                {"word": "热搜词一", "num": 532647},
                {"word": "广告位", "is_ad": True, "num": 1},
                {"note": "备用标题", "num": 100},
            ]
        }
    }
    items = parse_weibo(json.dumps(payload))
    assert len(items) == 2
    assert items[0]["word"] == "热搜词一"
    assert items[0]["source"] == "微博"
    assert items[0]["hot"] == 532647
    assert "s.weibo.com" in items[0]["url"]
    # 广告条目被过滤
    assert "广告位" not in [i["word"] for i in items]


def test_parse_baidu_nested_structure():
    payload = {
        "data": {
            "cards": [
                {
                    "content": [
                        {
                            "content": [
                                {
                                    "word": "百度热一",
                                    "url": "https://m.baidu.com/s?word=x",
                                    "hotScore": 12345,
                                },
                                {"word": "百度热二"},
                            ]
                        }
                    ]
                }
            ]
        }
    }
    items = parse_baidu(json.dumps(payload))
    assert [i["word"] for i in items] == ["百度热一", "百度热二"]
    assert items[0]["source"] == "百度"
    assert items[0]["url"].startswith("https://m.baidu.com")
    assert items[0]["hot"] == 12345
    # 无 url 时构造百度搜索链接
    assert "baidu.com/s?wd=" in items[1]["url"]


def test_parse_toutiao():
    payload = {
        "data": [
            {
                "Title": "头条热一",
                "Url": "https://www.toutiao.com/trending/1",
                "HotValue": 41319528,
            },
            {"Title": "头条热二", "Url": "", "HotValue": 0},
        ]
    }
    items = parse_toutiao(json.dumps(payload))
    assert len(items) == 2
    assert items[0]["source"] == "头条"
    assert items[0]["hot"] == 41319528


def test_parse_bilibili():
    payload = {
        "data": {"trending": {"list": [{"keyword": "B站热一", "heat_score": 2747196}]}}
    }
    items = parse_bilibili(json.dumps(payload))
    assert items[0]["word"] == "B站热一"
    assert items[0]["source"] == "B站"
    assert "search.bilibili.com" in items[0]["url"]
    assert items[0]["hot"] == 2747196


def test_parse_douyin():
    payload = {"word_list": [{"word": "抖音热一", "hot_value": 11786146}]}
    items = parse_douyin(json.dumps(payload))
    assert items[0]["word"] == "抖音热一"
    assert items[0]["source"] == "抖音"
    assert items[0]["hot"] == 11786146
    assert "douyin.com/search" in items[0]["url"]


def test_parse_github_search():
    payload = {
        "items": [
            {
                "full_name": "owner/repo-a",
                "html_url": "https://github.com/owner/repo-a",
                "description": "一个示例仓库",
                "stargazers_count": 3868,
                "language": "Python",
            }
        ]
    }
    items = parse_github_search(json.dumps(payload))
    assert items[0]["name"] == "repo-a"
    assert items[0]["full_name"] == "owner/repo-a"
    assert items[0]["stars"] == 3868
    assert items[0]["language"] == "Python"


def test_parse_hn_ids_and_item():
    ids = parse_hn_ids('[49489982, 49415386, "ignored"]')
    assert ids == [49489982, 49415386]

    item = parse_hn_item({"id": 1, "title": "HN头条", "url": "https://example.com"})
    assert item["title"] == "HN头条"
    assert item["url"] == "https://example.com"
    # 无外链时回退到 HN 讨论页
    item2 = parse_hn_item({"id": 2, "title": "无链接"})
    assert "news.ycombinator.com/item?id=2" in item2["url"]


def test_parse_kr36_html_title():
    payload = {
        "data": {
            "hotRankList": [
                {
                    "itemId": 3940251648851332,
                    "templateMaterial": {
                        "widgetTitle": "AI时代<em>写作</em>红利 &amp; 未来",
                    },
                }
            ]
        }
    }
    items = parse_kr36(json.dumps(payload))
    assert items[0]["title"] == "AI时代写作红利 & 未来"
    assert items[0]["source"] == "36氪"
    assert items[0]["url"] == "https://36kr.com/p/3940251648851332"


def test_rss_to_news_items():
    rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>t</title>
<item><title>科技新闻一</title><link>https://example.com/1</link></item>
</channel></rss>"""
    items = rss_to_news_items(rss, "少数派")
    assert items[0] == {
        "title": "科技新闻一",
        "url": "https://example.com/1",
        "source": "少数派",
    }
    # 空/坏内容返回空列表
    assert rss_to_news_items("not xml", "少数派") == []


def test_item_limit():
    payload = {"data": {"realtime": [{"word": f"词{i}", "num": i} for i in range(30)]}}
    items = parse_weibo(json.dumps(payload))
    assert len(items) == 15

def test_extract_keywords_filters_english_stopwords():
    from web.intelligence.trends import extract_keywords

    words = extract_keywords("ChatGPT and the new AI era")
    assert "the" not in words
    assert "and" not in words
    assert "new" not in words
    assert "chatgpt" in words
    assert "era" in words


def test_extract_keywords_chinese_and_english():
    from web.intelligence.trends import extract_keywords

    # 中文产出关联词(修复: 回退链路对中文关键词返回空)
    words = extract_keywords("人工智能赋能电商发展")
    assert "人工智能" in words
    assert "电商" in words

    # 英文实词照常提取
    words = extract_keywords("ChatGPT and the new AI era")
    assert "chatgpt" in words
    assert "era" in words


def test_associations_from_titles_extracts_chinese_and_english():
    from web.intelligence.trends import _associations_from_titles

    titles = [
        "伊朗 - 维基百科，自由的百科全书",
        "伊朗戰爭 (2026年) - 维基百科",
        "伊朗伊斯兰共和国 | OHCHR",
        "Iran - Wikipedia",
    ]
    assoc = _associations_from_titles("伊朗", titles)
    keywords = [a["keyword"] for a in assoc]

    # 中文关联词被提取
    assert "维基百科" in keywords
    assert "戰爭" in keywords
    # 关键词本身被过滤(含关键词的复合词也被过滤)
    assert "伊朗" not in keywords
    assert "伊朗伊斯兰共和国" not in keywords
    # 返回按分数排序
    assert assoc == sorted(
        assoc, key=lambda x: (x["score"], x["keyword"]), reverse=True
    )


def test_chinese_bigrams_for_matching_only():
    from web.intelligence.trends import _chinese_bigrams, _keyword_units

    # bigram 仅用于匹配:中文长词拆出短变体
    assert "智能" in _chinese_bigrams("人工智能")
    assert "电商" in _chinese_bigrams("人工智能赋能电商发展")

    # 匹配单元组合:完整词 + 中文 bigram
    units = _keyword_units("人工智能")
    assert "人工智能" in units
    assert "智能" in units
    assert "ai" in _keyword_units("AI")

def test_parse_keywords_from_llm_various_formats():
    from web.intelligence.trends import _parse_keywords_from_llm

    # 裸数组
    assert _parse_keywords_from_llm('["AI","芯片","开源"]') == ["AI", "芯片", "开源"]
    # Markdown 代码块(带换行)
    assert _parse_keywords_from_llm('```json\n["a","b"]\n```') == ["a", "b"]
    # 前后杂文
    assert _parse_keywords_from_llm('分析结果如下: ["x", "y"] 完毕') == ["x", "y"]
    # 混合类型: null/数字处理, None 丢弃
    assert _parse_keywords_from_llm('["a", 123, null, "b"]') == ["a", "123", "b"]
    # 无法解析
    assert _parse_keywords_from_llm("") == []
    assert _parse_keywords_from_llm("抱歉,我无法分析") == []
    # 对象格式 {"keywords": [...]} 兼容提取
    assert _parse_keywords_from_llm('{"keywords": ["a"]}') == ["a"]
    # 对象无 keywords 字段
    assert _parse_keywords_from_llm('{"items": ["a"]}') == []
