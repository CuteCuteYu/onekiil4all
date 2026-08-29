"""AlertManager 的关键词匹配与事件去重测试"""

import pytest

from web.intelligence.alert_manager import AlertManager


@pytest.fixture
def mgr(tmp_path):
    return AlertManager(data_dir=tmp_path)


def _trends(words, titles=None, github=None):
    return {
        "hot_search": [
            {"word": w, "url": f"https://example.com/{i}", "source": "test"}
            for i, w in enumerate(words)
        ],
        "tech_news": [
            {"title": t, "url": f"https://news.example.com/{i}", "source": "test"}
            for i, t in enumerate(titles or [])
        ],
        "github": github or [],
    }


def test_check_keyword_match_case_insensitive(mgr):
    assert mgr._check_keyword_match("ai", "AI 大模型发布") is True
    assert mgr._check_keyword_match("AI", "ai 助手") is True
    assert mgr._check_keyword_match("ai", "区块链") is False
    assert mgr._check_keyword_match("ai", "") is False


def test_check_alerts_creates_events(mgr):
    mgr.add_alert("深度学习")
    events = mgr.check_alerts(_trends(["深度学习入门指南", "无关词条"]))
    assert len(events) == 1
    assert events[0].keyword == "深度学习"
    assert events[0].title == "深度学习入门指南"
    assert len(mgr.history) == 1


def test_check_alerts_dedupes_by_url_and_keyword(mgr):
    mgr.add_alert("热搜")
    trends = _trends(["热搜第一条"])
    first = mgr.check_alerts(trends)
    second = mgr.check_alerts(_trends(["热搜第一条"]))

    assert len(first) == 1
    # 相同 URL + 关键词不重复触发
    assert second == []
    assert len(mgr.history) == 1


def test_check_alerts_skips_disabled(mgr):
    alert = mgr.add_alert("关键词")
    mgr.toggle_alert(alert.id)  # 禁用
    assert mgr.check_alerts(_trends(["关键词出现"])) == []


def test_check_alerts_no_enabled_alerts(mgr):
    assert mgr.check_alerts(_trends(["任何"])) == []


def test_add_alert_duplicate_raises(mgr):
    mgr.add_alert("重复")
    mgr.add_alert("REPEAT")  # 大小写不同仍视为重复
    with pytest.raises(ValueError):
        mgr.add_alert("重复")
    with pytest.raises(ValueError):
        mgr.add_alert("repeat")


def test_add_alert_empty_raises(mgr):
    with pytest.raises(ValueError):
        mgr.add_alert("   ")


def test_alert_persistence(tmp_path):
    mgr = AlertManager(data_dir=tmp_path)
    mgr.add_alert("持久化")

    reloaded = AlertManager(data_dir=tmp_path)
    assert [a.keyword for a in reloaded.get_all_alerts()] == ["持久化"]


def test_history_and_timeline(mgr):
    mgr.add_alert("时间线")
    mgr.check_alerts(_trends(["时间线事件A", "时间线事件B"]))
    assert len(mgr.get_history()) == 2
    assert len(mgr.get_timeline("时间线")) == 2
    mgr.clear_history()
    assert mgr.get_history() == []
    assert mgr.get_timeline("时间线") == []


def test_alert_stats_aggregates(mgr):
    mgr.add_alert("统计词")
    mgr.check_alerts(_trends(["统计词事件一", "统计词事件二"]))
    stats = mgr.alert_stats()
    alert = mgr.get_all_alerts()[0]
    assert alert.id in stats
    assert stats[alert.id]["event_count"] == 2
    # history 新事件在前，last_triggered_at 应为最近一次
    assert stats[alert.id]["last_triggered_at"] == mgr.history[0].triggered_at


def test_alert_stats_empty(mgr):
    mgr.add_alert("无事件")
    assert mgr.alert_stats() == {}
