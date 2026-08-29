"""
========================================
Trends Associations - 关键词关联分析模块
========================================
功能: 搜索相关网页标题 → AI 模型总结关键词，失败时回退到标题/热点提取
 作者: 上古必斩必杀
"""

import copy
import json
import logging
import re
import threading
import time
import urllib.parse

import requests

from web.intelligence.trends.fetchers import _HEADERS
from web.intelligence.trends.keywords import extract_keywords, keyword_units

logger = logging.getLogger(__name__)

# 关联分析结果缓存(keyword -> (时间戳, 结果)) —— 搜索 + LLM 调用较贵, 缓存 60 秒
_ASSOC_CACHE_TTL = 60.0
_assoc_cache: dict[str, tuple[float, dict]] = {}
_assoc_lock = threading.Lock()


def _web_search_titles(query: str, limit: int = 15) -> list[str]:
    """
    搜索与关键词相关的网页标题(先 DuckDuckGo, 失败回退 Bing HTML)

    返回:
        清洗后的标题列表(最多 limit 条), 两种源都失败返回空列表
    """
    titles = _search_ddg_titles(query, limit)
    if titles:
        return titles
    return _search_bing_titles(query, limit)


def _search_ddg_titles(query: str, limit: int) -> list[str]:
    """使用 DuckDuckGo 搜索(项目依赖 ddgs)获取网页标题"""
    try:
        from ddgs import DDGS

        with DDGS() as client:
            results = client.text(query, max_results=limit)
        titles = [r.get("title", "").strip() for r in results if r.get("title")]
        return titles[:limit]
    except Exception as e:  # noqa: BLE001 - 搜索源兜底
        logger.debug("DuckDuckGo 搜索失败: %s", e)
        return []


def _search_bing_titles(query: str, limit: int) -> list[str]:
    """回退: 直接抓取 Bing 搜索结果页并解析结果标题"""
    try:
        url = (
            "https://www.bing.com/search?q="
            + urllib.parse.quote(query)
            + "&count="
            + str(limit)
        )
        res = requests.get(url, headers=_HEADERS, timeout=8)
        res.raise_for_status()
        titles = []
        pattern = r'<li class="b_algo".*?<h2[^>]*>.*?<a[^>]*>(.*?)</a>'
        for m in re.finditer(pattern, res.text, re.DOTALL):
            title = _strip_html(m.group(1))
            if title:
                titles.append(title)
            if len(titles) >= limit:
                break
        return titles
    except Exception as e:  # noqa: BLE001 - 搜索源兜底
        logger.debug("Bing 搜索失败: %s", e)
        return []


def _strip_html(text: str) -> str:
    """去掉文本中的 HTML 标签并反转义"""
    import html as html_mod

    return html_mod.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _build_association_prompt(keyword: str, titles: list[str]) -> str:
    """构建提交给 LLM 的关键词总结提示词"""
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
    return f"""你是关键词分析助手。用户搜索的主题是："{keyword}"。
以下是从搜索引擎抓取到的相关网页标题（一行一条）：

{numbered}

请分析这些标题，提炼 5~12 个与主题高度相关的关键词，要求：
1. 关键词应覆盖标题中的核心概念（中文/英文均可，优先品牌名、产品名、技术名词、实体名）
2. 不要包含搜索词本身
3. 按相关度从高到低排列
只返回 JSON 数组（不要 Markdown 代码块、不要任何解释），例如：["关键词1","关键词2"]"""


def _parse_keywords_from_llm(text: str) -> list[str]:
    """
    解析 LLM 返回的关键词列表(容错 Markdown 代码块/前后杂文)

    参数:
        text: LLM 原始输出

    返回:
        关键词字符串列表, 无法解析时返回空列表
    """
    t = (text or "").strip()
    if not t:
        return []
    # 剥离 Markdown 代码块围栏
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    match = re.search(r"\[[\s\S]*\]", t)
    if not match:
        return []
    # 整体优先: 文本本身是 JSON 数组或 {"keywords": [...]} 对象
    whole = None
    try:
        whole = json.loads(t)
    except ValueError:
        pass  # 文本是带杂文的输出, 走下面的数组字面量提取

    if isinstance(whole, list):
        data = whole
    elif isinstance(whole, dict):
        # 对象格式: 仅接受带 keywords 列表的字典, 避免误取无关字段
        data = whole.get("keywords")
        if not isinstance(data, list):
            return []
    else:
        # 杂文输出: 提取其中的第一个数组字面量
        match = re.search(r"\[[\s\S]*\]", t)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except ValueError:
            return []
        if not isinstance(data, list):
            return []
    return [str(k).strip() for k in data if k is not None and str(k).strip()]


def _rank_score(index: int) -> float:
    """按排名生成递减相关度分数(首位 1.0, 最低 0.25)"""
    return round(max(1.0 - index * 0.08, 0.25), 2)


def _associations_via_search(keyword: str) -> list[dict]:
    """
    主链路: 网络搜索网页标题 → 项目 AI 模型总结关键词(中英文均可)

    LLM 被内容审核拦截/调用失败/解析为空时, 回退到直接从标题提取关键词,
    保证人名/地名等敏感词也能返回关联结果。
    """
    titles = _web_search_titles(keyword, limit=15)
    if not titles:
        return []

    words: list[str] = []
    try:
        # 延迟导入: 测试/无凭据环境下不会初始化模型
        from model_set import model_set

        prompt = _build_association_prompt(keyword, titles)
        result = model_set.model.invoke(prompt, max_tokens=200)
        content = getattr(result, "content", "")
        if isinstance(content, list):
            content = "".join(
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("text")
            )
        words = _parse_keywords_from_llm(str(content))
    except Exception as e:  # noqa: BLE001 - LLM 环节兜底
        logger.debug("AI 关联分析失败, 回退到标题关键词提取: %s", e)

    if words:
        return [{"keyword": w, "score": _rank_score(i)} for i, w in enumerate(words)]

    # LLM 失败或解析为空: 直接从搜索标题提取关键词(不依赖 LLM)
    return _associations_from_titles(keyword, titles)


def _associations_from_titles(keyword: str, titles: list[str]) -> list[dict]:
    """
    从网页标题直接提取关联词(英文 + 中文, 不依赖 LLM)

    用于 LLM 被内容审核拦截或解析失败时的兜底。
    按关键词在标题中的出现频次排序。
    """
    match_units = keyword_units(keyword)
    cache_key = keyword.lower()
    co_occur: dict[str, int] = {}

    for title in titles:
        for word in set(extract_keywords(title)):
            w = word.lower()
            if w == cache_key or w in match_units:
                continue
            # 与关键词互为子串的碎片也跳过(如关键词"人工智能"提取出"智能")
            if w in cache_key or cache_key in w:
                continue
            co_occur[word] = co_occur.get(word, 0) + 1

    associations = [
        {"keyword": word, "score": round(min(count * 0.25, 1.0), 2)}
        for word, count in co_occur.items()
    ]
    associations.sort(key=lambda x: (x["score"], x["keyword"]), reverse=True)
    return associations[:15]


def _associations_from_trends(keyword: str) -> list[dict]:
    """
    回退链路: 基于内置热点数据提取关联词(英文 + 中文)

    搜索或 AI 不可用时保证功能不中断。中文关键词通过 jieba 分词
    从匹配标题中提取中文关联词, 不再只产出英文词。
    """
    # 延迟导入避免循环依赖（get_trends 在 trends 包 __init__ 中）
    from web.intelligence.trends import get_trends

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

    match_units = keyword_units(keyword)
    cache_key = keyword.lower()
    co_occur: dict[str, int] = {}

    for title in titles:
        title_lower = title.lower()
        if not any(unit in title_lower for unit in match_units):
            continue
        for word in set(extract_keywords(title)):
            if word == cache_key or word in match_units:
                continue
            co_occur[word] = co_occur.get(word, 0) + 1

    associations = [
        {"keyword": word, "score": round(min(count * 0.25, 1.0), 2)}
        for word, count in co_occur.items()
    ]
    associations.sort(key=lambda x: (x["score"], x["keyword"]), reverse=True)
    return associations[:15]


def get_keyword_associations(keyword: str) -> dict:
    """
    获取指定关键词的关联分析

    主链路: 搜索相关网页标题 → 项目 AI 模型总结关键词(中英文均可);
    失败时回退: 内置热点数据的英文关联词。
    结果按 60 秒缓存(搜索 + LLM 调用较贵)。

    返回:
        {"keyword", "total", "associations": [{keyword, score}]}
    """
    if not keyword or len(keyword.strip()) < 2:
        return {"keyword": keyword, "total": 0, "associations": []}

    keyword = keyword.strip()
    cache_key = keyword.lower()

    with _assoc_lock:
        cached = _assoc_cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < _ASSOC_CACHE_TTL:
            return copy.deepcopy(cached[1])

    associations = _associations_via_search(keyword)
    if not associations:
        associations = _associations_from_trends(keyword)

    result = {
        "keyword": keyword,
        "total": len(associations),
        "associations": associations[:15],
    }

    with _assoc_lock:
        _assoc_cache[cache_key] = (time.monotonic(), result)
        if len(_assoc_cache) > 200:  # 简单防膨胀
            _assoc_cache.clear()

    return copy.deepcopy(result)