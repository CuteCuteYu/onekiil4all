"""
========================================
Alert Models - 告警数据模型
========================================
功能: 告警规则与告警事件的数据模型定义
 作者: 上古必斩必杀
"""


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