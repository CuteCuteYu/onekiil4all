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

RDF_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel rdf:about="https://example.com/feed">
    <title>RDF测试源</title>
    <link>https://example.com</link>
    <description>RDF描述</description>
  </channel>
  <item rdf:about="https://example.com/rdf/1">
    <title>RDF条目一</title>
    <link>https://example.com/rdf/1</link>
    <description>RDF摘要一</description>
    <dc:date>2026-04-01T00:00:00Z</dc:date>
  </item>
  <item rdf:about="https://example.com/rdf/2">
    <title>RDF条目二</title>
    <link>https://example.com/rdf/2</link>
  </item>
</rdf:RDF>
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


def test_parse_rss_1_0_rdf():
    articles = parse_feed(RDF_XML)
    assert len(articles) == 2
    assert articles[0]["title"] == "RDF条目一"
    assert articles[0]["link"] == "https://example.com/rdf/1"
    assert articles[0]["pubDate"] == "2026-04-01T00:00:00Z"
    assert articles[0]["description"] == "RDF摘要一"
    assert articles[1]["title"] == "RDF条目二"
    assert articles[1]["pubDate"] == ""


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
