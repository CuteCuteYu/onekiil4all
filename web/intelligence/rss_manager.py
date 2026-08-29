"""
========================================
RSS Manager - RSS订阅源管理模块
========================================
功能: 管理用户自定义RSS/Atom订阅源，
抓取逻辑由 web_server 的后台任务驱动，解析复用 rss_parser
 作者: 上古必斩必杀
"""

# ═══════════════════════════════════════════════════════════════════════
# 导入标准库
# ═══════════════════════════════════════════════════════════════════════

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from web.paths import DATA_DIR

# ═══════════════════════════════════════════════════════════════════════
# 数据模型定义
# ═══════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)


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

    负责订阅源的增删改查与持久化，
    定时抓取由 web_server 的后台任务调用完成
    """

    def __init__(self, sources_file: Path | None = None):
        """
        初始化RSS管理器

        参数:
            sources_file: 订阅源持久化文件，默认为 data/rss_sources.json
        """
        self.sources_file = sources_file or DATA_DIR / "rss_sources.json"
        self.sources: dict[str, RSSSource] = {}
        self._load_sources()

    def _load_sources(self):
        """从文件加载RSS源列表"""
        if not self.sources_file.exists():
            return
        try:
            data = json.loads(self.sources_file.read_text(encoding="utf-8"))
            for item in data:
                source = RSSSource(**item)
                self.sources[source.id] = source
        except (json.JSONDecodeError, OSError, TypeError):
            logger.warning("RSS 订阅源文件读取失败，已重置", exc_info=True)
            self.sources = {}

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

        异常:
            ValueError: URL为空或已存在
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
            except (IndexError, ValueError):
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

    def update_source(self, source_id: str, articles: list):
        """
        更新源的文章和抓取时间

        抓取失败（空列表）时保留旧文章、仅记录本次抓取时间，
        避免源不可用时每次检查周期都重试

        参数:
            source_id: 源ID
            articles: 最新文章列表（可为空）
        """
        if source_id not in self.sources:
            return
        source = self.sources[source_id]
        if articles:
            source.articles = articles[:10]
        source.last_fetch = datetime.now(UTC).isoformat()
        self._save_sources()


# ═══════════════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════════════

rss_manager = RSSManager()
