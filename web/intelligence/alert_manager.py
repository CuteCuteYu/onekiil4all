"""
========================================
Alert Manager - 告警管理模块
========================================
功能: 管理监控关键词、触发告警、记录事件时间线
 作者: 上古必斩必杀
"""

import json
import logging
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from web.paths import DATA_DIR

logger = logging.getLogger(__name__)

ALERTS_FILE = DATA_DIR / "alerts.json"
HISTORY_FILE = DATA_DIR / "alert_history.json"


class Alert:
    """告警规则"""

    def __init__(
        self,
        id: str,
        keyword: str,
        created_at: str,
        enabled: bool = True,
    ):
        self.id = id
        self.keyword = keyword
        self.created_at = created_at
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "keyword": self.keyword,
            "created_at": self.created_at,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        return cls(
            id=data.get("id", ""),
            keyword=data.get("keyword", ""),
            created_at=data.get("created_at", ""),
            enabled=data.get("enabled", True),
        )


class AlertEvent:
    """告警事件"""

    def __init__(
        self,
        id: str,
        alert_id: str,
        keyword: str,
        title: str,
        source: str,
        url: str,
        triggered_at: str,
        event_type: str,
    ):
        self.id = id
        self.alert_id = alert_id
        self.keyword = keyword
        self.title = title
        self.source = source
        self.url = url
        self.triggered_at = triggered_at
        self.event_type = event_type

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "keyword": self.keyword,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "triggered_at": self.triggered_at,
            "type": self.event_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AlertEvent":
        return cls(
            id=data.get("id", ""),
            alert_id=data.get("alert_id", ""),
            keyword=data.get("keyword", ""),
            title=data.get("title", ""),
            source=data.get("source", ""),
            url=data.get("url", ""),
            triggered_at=data.get("triggered_at", ""),
            event_type=data.get("type", "hotsearch"),
        )


class AlertManager:
    """告警管理器"""

    def __init__(self, data_dir: Path | None = None):
        """
        初始化告警管理器

        参数:
            data_dir: 数据目录，默认使用项目根目录 data/（测试时可注入临时目录）
        """
        self.data_dir = data_dir or DATA_DIR
        self.alerts_file = self.data_dir / "alerts.json"
        self.history_file = self.data_dir / "alert_history.json"
        self.alerts: list[Alert] = []
        self.history: list[AlertEvent] = []
        self._processed_urls: set[tuple[str, str]] = set()
        # 后台告警检查线程与 API 事件循环线程共享本实例，用锁串行化状态修改
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        """加载告警配置和历史"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    alerts_list = data.get("alerts", [])
                    self.alerts = [Alert.from_dict(a) for a in alerts_list]
            except Exception:
                logger.warning("告警配置读取失败，已重置", exc_info=True)
                self.alerts = []

        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    history_list = data.get("history", [])
                    self.history = [AlertEvent.from_dict(h) for h in history_list]
                    self._processed_urls = {
                        (h.url, h.keyword) for h in self.history if h.url and h.keyword
                    }
            except Exception:
                logger.warning("告警历史读取失败，已重置", exc_info=True)
                self.history = []

    def save_alerts(self):
        """保存告警配置"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {"alerts": [a.to_dict() for a in self.alerts]}
        with open(self.alerts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_history(self):
        """保存告警历史"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {"history": [h.to_dict() for h in self.history]}
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_alert(self, keyword: str) -> Alert:
        """添加告警规则"""
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("关键词不能为空")

        with self._lock:
            for alert in self.alerts:
                if alert.keyword.lower() == keyword.lower():
                    raise ValueError(f"关键词 '{keyword}' 已存在")

            alert = Alert(
                id=f"alert_{uuid.uuid4().hex[:8]}",
                keyword=keyword,
                created_at=datetime.now(UTC).isoformat(),
                enabled=True,
            )
            self.alerts.append(alert)
            self.save_alerts()
        return alert

    def remove_alert(self, alert_id: str) -> bool:
        """删除告警规则"""
        with self._lock:
            original_count = len(self.alerts)
            self.alerts = [a for a in self.alerts if a.id != alert_id]
            if len(self.alerts) < original_count:
                self.save_alerts()
                return True
            return False

    def get_all_alerts(self) -> list[Alert]:
        """获取所有告警"""
        return self.alerts

    def get_enabled_alerts(self) -> list[Alert]:
        """获取已启用的告警"""
        return [a for a in self.alerts if a.enabled]

    def toggle_alert(self, alert_id: str) -> bool:
        """切换告警状态"""
        with self._lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.enabled = not alert.enabled
                    self.save_alerts()
                    return True
            return False

    def check_alerts(self, trends_data: dict) -> list[AlertEvent]:
        """检查趋势数据并触发告警

        匹配阶段无共享状态（锁外执行），只收集 (类型, 告警, 条目)；
        创建事件阶段统一在锁内执行，避免与 API 增删改并发写冲突。
        keyword 预小写、条目小写只算一次，避免热点数据大时的重复转换。
        """
        enabled_alerts = self.get_enabled_alerts()
        if not enabled_alerts:
            return []

        hot_search = trends_data.get("hot_search", [])
        github = trends_data.get("github", [])
        tech_news = trends_data.get("tech_news", [])

        matches: list[tuple[str, Alert, dict]] = []
        for alert in enabled_alerts:
            keyword = alert.keyword.lower()
            for item in hot_search:
                if keyword in (item.get("word") or "").lower():
                    matches.append(("hotsearch", alert, item))
            for item in github:
                title = item.get("name") or item.get("full_name") or ""
                desc = item.get("description") or ""
                if keyword in f"{title} {desc}".lower():
                    matches.append(("github", alert, item))
            for item in tech_news:
                if keyword in (item.get("title") or "").lower():
                    matches.append(("tech_news", alert, item))

        new_events: list[AlertEvent] = []
        with self._lock:
            for event_type, alert, item in matches:
                event = self._create_event(alert, item, event_type)
                if event:
                    new_events.append(event)
        return new_events

    def _check_keyword_match(self, keyword: str, text: str) -> bool:
        """检查关键词是否匹配（两侧统一小写）"""
        if not text:
            return False
        return keyword.lower() in text.lower()

    def _create_event(
        self, alert: Alert, item: dict, event_type: str
    ) -> AlertEvent | None:
        """创建告警事件"""
        title = item.get("word") or item.get("title") or item.get("name", "")
        url = item.get("url", "")
        source = item.get("source", "")

        if not title:
            return None

        if url and (url, alert.keyword) in self._processed_urls:
            return None

        event = AlertEvent(
            id=f"hist_{uuid.uuid4().hex[:8]}",
            alert_id=alert.id,
            keyword=alert.keyword,
            title=title,
            source=source,
            url=url,
            triggered_at=datetime.now(UTC).isoformat(),
            event_type=event_type,
        )

        self.history.insert(0, event)

        if url:
            self._processed_urls.add((url, alert.keyword))

        if len(self.history) > 500:
            self.history = self.history[:500]

        self.save_history()

        return event

    def get_history(self, limit: int = 50) -> list[AlertEvent]:
        """获取告警历史"""
        return self.history[:limit]

    def get_timeline(self, keyword: str) -> list[AlertEvent]:
        """获取关键词的事件时间线"""
        keyword = keyword.lower()
        return [e for e in self.history if e.keyword.lower() == keyword]

    def alert_stats(self) -> dict[str, dict]:
        """
        聚合每个告警规则的事件统计（供 API 直接返回，前端免二次请求）

        返回:
            {alert_id: {"event_count": int, "last_triggered_at": str | None}}
        """
        stats: dict[str, dict] = {}
        # history 新事件在前，首次遇到的即为该规则最近一次触发
        for event in self.history:
            entry = stats.get(event.alert_id)
            if entry is None:
                stats[event.alert_id] = {
                    "event_count": 1,
                    "last_triggered_at": event.triggered_at,
                }
            else:
                entry["event_count"] += 1
        return stats

    def clear_history(self):
        """清空告警历史"""
        with self._lock:
            self.history = []
            self._processed_urls.clear()
            self.save_history()


alert_manager = AlertManager()
