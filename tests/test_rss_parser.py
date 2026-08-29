"""RSS/Atom 公共解析器测试"""

from web.intelligence.rss_parser import parse_feed

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>测试源</title>
    <item>
      <title>文章一</title>
      <link>https://example.com/1</link>
      <description>这是第一篇文章的摘要</description>
      <pubDate>Mon, 01 Apr 2026 00:00:00 GMT</pubDate>
    </item>
    <item>
      <title>文章二</title>
      <link>https://example.com/2</link>
      <description>概要</description>
    </item>
  </channel>
</rss>
"""

ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom测试源</title>
  <entry>
    <title>Atom条目一</title>
    <link href="https://example.com/atom/1"/>
    <updated>2026-04-01T00:00:00Z</updated>
    <summary>Atom摘要</summary>
  </entry>
  <entry>
    <title>Atom条目二</title>
    <link href="https://example.com/atom/2"/>
    <updated>2026-04-02T00:00:00Z</updated>
    <content>Atom内容充当摘要</content>
  </entry>
</feed>
"""

ATOM_NO_NS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <title>无命名空间Atom</title>
  <entry>
    <title>裸Atom条目</title>
    <link href="https://example.com/bare/1"/>
    <updated>2026-04-03T00:00:00Z</updated>
  </entry>
</feed>
"""


def test_parse_rss_2_0():
    articles = parse_feed(RSS_XML)
    assert len(articles) == 2
    assert articles[0]["title"] == "文章一"
    assert articles[0]["link"] == "https://example.com/1"
    assert articles[0]["pubDate"] == "Mon, 01 Apr 2026 00:00:00 GMT"
    assert articles[0]["description"] == "这是第一篇文章的摘要"


def test_parse_rss_max_items():
    articles = parse_feed(RSS_XML, max_items=1)
    assert len(articles) == 1
    assert articles[0]["title"] == "文章一"


def test_parse_atom_with_namespace():
    articles = parse_feed(ATOM_XML)
    assert len(articles) == 2
    assert articles[0]["title"] == "Atom条目一"
    assert articles[0]["link"] == "https://example.com/atom/1"
    assert articles[0]["pubDate"] == "2026-04-01T00:00:00Z"
    # summary 优先
    assert articles[0]["description"] == "Atom摘要"
    # 无 summary 时回退 content
    assert articles[1]["description"] == "Atom内容充当摘要"


def test_parse_atom_without_namespace():
    articles = parse_feed(ATOM_NO_NS_XML)
    assert len(articles) == 1
    assert articles[0]["title"] == "裸Atom条目"
    assert articles[0]["link"] == "https://example.com/bare/1"


def test_parse_feed_invalid_xml():
    assert parse_feed("这不是XML") == []


def test_parse_feed_unknown_root():
    assert parse_feed("<html><body>x</body></html>") == []


def test_description_truncated():
    long_desc = "长" * 500
    xml = f"""<?xml version="1.0"?>
<rss version="2.0"><channel><item>
      <title>t</title><link>https://e.com/1</link>
      <description>{long_desc}</description>
</item></channel></rss>"""
    articles = parse_feed(xml)
    assert len(articles[0]["description"]) == 200
