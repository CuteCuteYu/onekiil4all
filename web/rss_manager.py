"""
========================================
RSS Manager - RSS订阅源管理模块
========================================
功能: 管理用户自定义RSS/Atom订阅源，定时抓取最新文章
 作者: 上古必斩必杀
"""

# ═══════════════════════════════════════════════════════════════════════
# 导入标准库
# ═══════════════════════════════════════════════════════════════════════

import threading
import time
import json
import uuid
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field

# ═══════════════════════════════════════════════════════════════════════
# 数据模型定义
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class RSSArticle:
    """RSS文章数据模型"""

    title: str = ""
    url: str = ""
    pubDate: str = ""
    description: str = ""


@dataclass
class RSSSource:
    """RSS订阅源数据模型"""

    id: str
    url: str
    name: str
    enabled: bool = True
    fetch_interval: int = 60
    last_fetch: str = ""
    articles: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# RSS Manager 类
# ═══════════════════════════════════════════════════════════════════════


class RSSManager:
    """
    RSS订阅源管理器

    负责管理用户添加的RSS/Atom订阅源，
    在后台线程中定时抓取最新文章并推送到队列
    """

    def __init__(self):
        """初始化RSS管理器"""
        self.sources_file = Path("data/rss_sources.json")
        self.sources: dict[str, RSSSource] = {}
        self._load_sources()
        self._thread = None
        self._running = False
        self._fetch_interval = 1  # 检查间隔1秒

    def _load_sources(self):
        """从文件加载RSS源列表"""
        if self.sources_file.exists():
            try:
                data = json.loads(self.sources_file.read_text(encoding="utf-8"))
                for item in data:
                    self.sources[item["id"]] = RSSSource(**item)
            except Exception:
                pass

    def _save_sources(self):
        """保存RSS源列表到文件"""
        data = [asdict(s) for s in self.sources.values()]
        self.sources_file.parent.mkdir(parents=True, exist_ok=True)
        self.sources_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_source(self, url: str, name: str = "") -> RSSSource:
        """
        添加新的RSS订阅源

        参数:
            url: RSS/Atom订阅地址
            name: 自定义名称，默认使用域名

        返回:
            新创建的RSSSource对象
        """
        url = url.strip()
        if not url:
            raise ValueError("URL不能为空")

        for source in self.sources.values():
            if source.url.lower() == url.lower():
                raise ValueError(f"URL '{url}' 已存在")

        if not name:
            try:
                name = url.split("//")[1].split("/")[0]
            except Exception:
                name = url

        source = RSSSource(id=str(uuid.uuid4()), url=url, name=name)
        self.sources[source.id] = source
        self._save_sources()
        return source

    def remove_source(self, source_id: str) -> bool:
        """
        删除RSS订阅源

        参数:
            source_id: 要删除的源ID

        返回:
            是否删除成功
        """
        if source_id in self.sources:
            del self.sources[source_id]
            self._save_sources()
            return True
        return False

    def toggle_source(self, source_id: str) -> RSSSource | None:
        """
        切换RSS源的启用/禁用状态

        参数:
            source_id: 源ID

        返回:
            更新后的RSSSource对象，如果不存在返回None
        """
        if source_id in self.sources:
            self.sources[source_id].enabled = not self.sources[source_id].enabled
            self._save_sources()
            return self.sources[source_id]
        return None

    def get_all_sources(self) -> list:
        """
        获取所有RSS订阅源

        返回:
            RSSSource对象列表
        """
        return list(self.sources.values())

    def get_source(self, source_id: str) -> RSSSource | None:
        """获取指定ID的RSS源"""
        return self.sources.get(source_id)

    def start(self, rss_queue):
        """
        启动RSS后台抓取线程

        参数:
            rss_queue: 异步队列，用于推送新文章
        """
        self._running = True
        self._thread = threading.Thread(
            target=self._fetch_loop, args=(rss_queue,), daemon=True
        )
        self._thread.start()

    def _fetch_loop(self, rss_queue):
        """
        RSS抓取主循环，每秒检查一次是否需要抓取

        参数:
            rss_queue: 异步队列
        """
        while self._running:
            now = datetime.now()

            for source in list(self.sources.values()):
                if not source.enabled:
                    continue

                last_time = None
                if source.last_fetch:
                    try:
                        last_time = datetime.fromisoformat(source.last_fetch)
                    except Exception:
                        pass

                if (
                    last_time
                    and (now - last_time).total_seconds() < source.fetch_interval
                ):
                    continue

                articles = self._fetch_rss(source)
                if articles:
                    source.articles = articles[:10]
                    source.last_fetch = now.isoformat()

                    for article in articles[:3]:
                        rss_queue.put(
                            {
                                "source_id": source.id,
                                "source_name": source.name,
                                "url": source.url,
                                "title": article.get("title", ""),
                                "link": article.get("link", ""),
                                "pubDate": article.get("pubDate", ""),
                                "description": article.get("description", ""),
                            }
                        )

            self._save_sources()
            time.sleep(self._fetch_interval)

    def _fetch_rss_by_url(self, url: str) -> list:
        """根据URL抓取RSS文章（不修改源对象）"""
        return self._fetch_rss_by_url_internal(url)

    def _fetch_rss_by_url_internal(self, url: str) -> list:
        """内部方法：根据URL抓取RSS"""
        try:
            import urllib.request
            import xml.etree.ElementTree as ET

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode("utf-8")

            root = ET.fromstring(content)
            articles = []

            if root.tag == "rss":
                channel = root.find("channel")
                if channel is not None:
                    for item in channel.findall("item")[:10]:
                        article = {}
                        title_elem = item.find("title")
                        article["title"] = (
                            title_elem.text if title_elem is not None else ""
                        )

                        link_elem = item.find("link")
                        article["link"] = (
                            link_elem.text if link_elem is not None else ""
                        )

                        desc_elem = item.find("description")
                        if desc_elem is not None and desc_elem.text:
                            article["description"] = (
                                desc_elem.text[:200].replace("\n", " ").strip()
                            )

                        pub_elem = item.find("pubDate")
                        article["pubDate"] = (
                            pub_elem.text if pub_elem is not None else ""
                        )

                        if article.get("title"):
                            articles.append(article)

            elif root.tag == "{http://www.w3.org/2005/Atom}feed" or root.tag == "feed":
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns)[:10]:
                    article = {}

                    title_elem = entry.find("atom:title", ns)
                    article["title"] = title_elem.text if title_elem is not None else ""

                    link_elem = entry.find("atom:link", ns)
                    if link_elem is not None:
                        href = link_elem.get("href")
                        article["link"] = href if href else ""

                    summary_elem = entry.find("atom:summary", ns)
                    if summary_elem is not None and summary_elem.text:
                        article["description"] = (
                            summary_elem.text[:200].replace("\n", " ").strip()
                        )
                    else:
                        content_elem = entry.find("atom:content", ns)
                        if content_elem is not None and content_elem.text:
                            article["description"] = (
                                content_elem.text[:200].replace("\n", " ").strip()
                            )

                    updated_elem = entry.find("atom:updated", ns)
                    article["pubDate"] = (
                        updated_elem.text if updated_elem is not None else ""
                    )

                    if article.get("title"):
                        articles.append(article)

            return articles

        except Exception:
            return []

    def update_source(self, source_id: str, articles: list):
        """更新源的 articles 和 last_fetch"""
        if source_id in self.sources:
            self.sources[source_id].articles = articles[:10]
            self.sources[source_id].last_fetch = datetime.now().isoformat()
            self._save_sources()

    def _fetch_rss(self, source: RSSSource) -> list:
        """
        抓取单个RSS源的最新文章

        参数:
            source: RSSSource对象

        返回:
            文章列表
        """
        try:
            import urllib.request
            import xml.etree.ElementTree as ET

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(source.url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode("utf-8")

            root = ET.fromstring(content)
            articles = []

            if root.tag == "rss":
                channel = root.find("channel")
                if channel is not None:
                    for item in channel.findall("item")[:10]:
                        article = {}
                        title_elem = item.find("title")
                        article["title"] = (
                            title_elem.text if title_elem is not None else ""
                        )

                        link_elem = item.find("link")
                        article["link"] = (
                            link_elem.text if link_elem is not None else ""
                        )

                        desc_elem = item.find("description")
                        if desc_elem is not None and desc_elem.text:
                            article["description"] = (
                                desc_elem.text[:200].replace("\n", " ").strip()
                            )

                        pub_elem = item.find("pubDate")
                        article["pubDate"] = (
                            pub_elem.text if pub_elem is not None else ""
                        )

                        if article.get("title"):
                            articles.append(article)

            elif root.tag == "{http://www.w3.org/2005/Atom}feed" or root.tag == "feed":
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns)[:10]:
                    article = {}

                    title_elem = entry.find("atom:title", ns)
                    article["title"] = title_elem.text if title_elem is not None else ""

                    link_elem = entry.find("atom:link", ns)
                    if link_elem is not None:
                        href = link_elem.get("href")
                        article["link"] = href if href else ""

                    summary_elem = entry.find("atom:summary", ns)
                    if summary_elem is not None and summary_elem.text:
                        article["description"] = (
                            summary_elem.text[:200].replace("\n", " ").strip()
                        )
                    else:
                        content_elem = entry.find("atom:content", ns)
                        if content_elem is not None and content_elem.text:
                            article["description"] = (
                                content_elem.text[:200].replace("\n", " ").strip()
                            )

                    updated_elem = entry.find("atom:updated", ns)
                    article["pubDate"] = (
                        updated_elem.text if updated_elem is not None else ""
                    )

                    if article.get("title"):
                        articles.append(article)

            return articles

        except Exception:
            return []

    def stop(self):
        """停止RSS后台抓取线程"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)


# ═══════════════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════════════

rss_manager = RSSManager()
