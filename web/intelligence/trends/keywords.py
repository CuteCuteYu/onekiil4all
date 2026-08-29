"""
========================================
Trends Keywords - 关键词提取模块
========================================
功能: 从文本中提取中英文关联词，供关联分析和热点回退使用
 作者: 上古必斩必杀
"""

import re

# 英文停用词(无信息量,常见于英文标题)
_EN_STOPWORDS = {
    'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'was',
    'were', 'you', 'your', 'not', 'but', 'what', 'why', 'how', 'when',
    'where', 'who', 'which', 'into', 'than', 'then', 'them', 'they',
    'have', 'has', 'had', 'will', 'would', 'can', 'could', 'should',
    'new', 'via', 'its', 'all', 'any', 'one', 'top', 'best', 'get',
    'make', 'made', 'using', 'use', 'used', 'app', 'apps', 'about',
    'after', 'before', 'over', 'under', 'also', 'been', 'being',
    'more', 'most', 'much', 'many', 'some', 'such', 'only', 'very',
}

# 中文停用词(无信息量的常见词/泛化词, 用于中文关联词提取过滤)
_ZH_STOPWORDS = {
    "我们", "你们", "他们", "这个", "那个", "这些", "那些", "什么", "怎么", "如何",
    "一个", "一种", "以及", "或者", "因为", "所以", "但是", "如果", "虽然", "而且",
    "没有", "可以", "进行", "通过", "对于", "关于", "根据", "目前", "现在", "今天",
    "今年", "最新", "相关", "其中", "同时", "已经", "成为", "不是", "就是", "还是",
    "还有", "包括", "主要", "重要", "基本", "一般", "一些", "很多", "发布", "推出",
    "宣布", "表示", "认为", "指出", "强调", "介绍", "提供", "使用", "中国", "全球",
    "世界", "国内", "国际", "行业", "领域", "市场", "企业", "公司", "产品", "技术",
    "平台", "系统", "服务", "用户", "数据", "信息", "内容", "功能", "问题", "方案",
    "发展", "建设", "管理", "应用", "研究", "分析", "报告", "新闻", "消息", "报道",
    "文章", "视频", "图片", "网友", "官方", "正式", "首次", "再次", "新增", "更新",
    "升级", "上线", "开放", "合作", "投资", "融资", "收购", "大会", "论坛", "峰会",
    "会议", "活动", "项目", "计划", "目标", "任务", "工作", "方面", "部分", "情况",
    "结果", "影响", "作用", "意义", "价值", "优势", "特点", "未来", "过去", "之前",
    "之后", "期间", "阶段", "过程", "方式", "方法", "途径", "等等", "东西", "事情",
    "的", "了", "是", "在", "和", "与", "及", "或", "被", "把", "让", "对", "从",
    "到", "为", "以", "于", "之", "其", "此", "该", "各", "每", "某", "这", "那",
    "也", "都", "很", "更", "最", "就", "才", "又", "再", "还", "并", "而", "但",
    "却", "虽", "若", "如", "因", "故", "即", "则", "所", "能", "会", "要", "想",
    "需", "应", "可", "须", "必", "将", "已", "曾", "正", "刚", "先", "后", "前",
    "内", "外", "上", "下", "中", "间", "里", "边", "处", "地", "时", "年", "月",
    "日", "天", "周", "次", "个", "种", "类", "项", "条", "件", "份", "张", "台",
    "部", "家", "位", "名", "人", "事", "物",
}


def extract_keywords(text: str) -> list:
    """
    从文本中提取关联词(英文 + 中文)

    英文: 3 个及以上字母的单词(小写), 过滤英文停用词。
    中文: jieba 分词(不可用时回退 2~4 字滑动窗口), 过滤中文停用词。
    返回去重后的关键词列表。
    """
    keywords = []
    # 英文单词
    for word in re.findall(r"[a-zA-Z]{3,}", text):
        w = word.lower()
        if w not in _EN_STOPWORDS:
            keywords.append(w)
    # 中文词
    keywords.extend(_extract_chinese_keywords(text))
    return list(dict.fromkeys(keywords))


def _extract_chinese_keywords(text: str) -> list[str]:
    """
    从文本中提取中文关键词(2字及以上, 含中文的词)

    优先使用 jieba 分词; 不可用时回退到 2~4 字滑动窗口。
    过滤中文停用词。
    """
    try:
        import jieba

        words = [w.strip() for w in jieba.cut(text) if w.strip()]
    except ImportError:
        words = []
        for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", text):
            if len(chunk) <= 4:
                words.append(chunk)
            else:
                for size in (4, 3, 2):
                    words.extend(
                        chunk[i : i + size] for i in range(len(chunk) - size + 1)
                    )

    result = []
    for w in words:
        if len(w) < 2:
            continue
        # 只保留含中文的词(英文由 extract_keywords 单独处理)
        if not re.search(r"[\u4e00-\u9fff]", w):
            continue
        if w in _ZH_STOPWORDS:
            continue
        result.append(w)
    return result


def chinese_bigrams(text: str) -> list[str]:
    """
    中文 2 字相邻组合(bigram), 仅用于热点回退链路的标题匹配

    生成中文长词的短变体, 使"人工智能"能匹配仅含"智能"的标题
    """
    bigrams: list[str] = []
    for chunk in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(chunk) < 2:
            continue
        for i in range(len(chunk) - 1):
            bigrams.append(chunk[i : i + 2])
    return bigrams


def keyword_units(keyword: str) -> set[str]:
    """
    将关键词拆成匹配单元(完整小写词 + 中文 bigram), 用于热点回退链路
    """
    units: set[str] = set()
    kw = keyword.strip().lower()
    if kw:
        units.add(kw)
    units.update(chinese_bigrams(keyword))
    return units