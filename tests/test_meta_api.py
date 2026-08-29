"""技能描述提取测试"""

from web.api.meta_api import _extract_description


def test_extract_from_plain_title():
    assert _extract_description("# 我的技能\n\n正文", "fallback") == "我的技能"


def test_extract_skips_frontmatter():
    content = "---\nname: demo\ndescription: yaml头\n---\n\n# 真正的标题\n\n内容"
    assert _extract_description(content, "fallback") == "真正的标题"


def test_extract_frontmatter_without_title():
    # frontmatter 后没有 # 标题时取第一个非空行
    content = "---\nname: demo\n---\n\n这是一段普通描述文本"
    assert _extract_description(content, "fallback") == "这是一段普通描述文本"


def test_extract_empty_content_falls_back():
    assert _extract_description("", "fallback") == "fallback"
    assert _extract_description("---\nname: x\n", "fallback") == "fallback"
