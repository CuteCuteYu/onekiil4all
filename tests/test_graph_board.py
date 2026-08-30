"""画板模块（web.intelligence.graph_board）单元测试。"""

import pytest

from web.intelligence import graph_board


@pytest.fixture(autouse=True)
def _isolated_boards(tmp_path, monkeypatch):
    """每个测试使用独立临时画板目录，并重置内存状态。"""
    monkeypatch.setattr(graph_board, "BOARDS_DIR", tmp_path)
    monkeypatch.setattr(graph_board, "DATA_FILE", tmp_path / "graph_data.json")
    monkeypatch.setattr(
        graph_board, "graph_data", {"types": {}, "nodes": [], "edges": []}
    )
    monkeypatch.setattr(graph_board, "current_board", "")
    graph_board.ensure_boards()


def _sample_node(node_id: str, name: str, type_: str = "ThreatActor") -> dict:
    return {
        "id": node_id,
        "name": name,
        "type": type_,
        "description": f"{name} 描述",
        "properties": {"alias": [name]},
        "source_chunks": [f"report_{node_id}"],
    }


def test_create_and_list_boards():
    result = graph_board.create_board("APT29 调查")
    assert result == {"status": "created", "name": "APT29 调查"}

    info = graph_board.get_boards()
    assert info["current"] == ""
    assert [b["name"] for b in info["boards"]] == ["APT29 调查"]
    assert info["boards"][0]["nodes"] == 0


def test_create_board_duplicate_and_invalid_name():
    graph_board.create_board("test")
    with pytest.raises(graph_board.GraphBoardError) as exc:
        graph_board.create_board("test")
    assert exc.value.status_code == 400

    with pytest.raises(graph_board.GraphBoardError):
        graph_board.create_board("bad/name")


def test_open_node_edge_and_cascade_delete():
    graph_board.create_board("graph-a")
    opened = graph_board.open_board("graph-a")
    assert opened["name"] == "graph-a"

    graph_board.upsert_node(_sample_node("ent_a", "A"))
    graph_board.upsert_node(_sample_node("ent_b", "B"))
    graph_board.upsert_edge(
        {
            "id": "rel_ab",
            "source": "ent_a",
            "target": "ent_b",
            "relation": "CONTROLS",
            "description": "A 控制 B",
            "weight": 0.9,
        }
    )

    data = graph_board.get_graph()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1

    # 1 跳展开：ent_a 的邻居应包含 ent_b
    expanded = graph_board.expand_node("ent_a")
    assert [n["name"] for n in expanded["nodes"]] == ["B"]

    # 删除节点级联清理边
    result = graph_board.delete_node("ent_a")
    assert result["removed_edges"] == 1
    assert graph_board.get_graph()["edges"] == []

    # 重复删除应报 404
    with pytest.raises(graph_board.GraphBoardError) as exc:
        graph_board.delete_node("ent_a")
    assert exc.value.status_code == 404


def test_types_management():
    graph_board.open_board(graph_board.create_board("types")["name"])

    created = graph_board.upsert_type("Person", "人物", "#22d3ee", "ellipse")
    assert created["status"] == "created"
    assert graph_board.get_types()["Person"]["label"] == "人物"

    # 内置类型不可删除
    with pytest.raises(graph_board.GraphBoardError) as exc:
        graph_board.delete_type("ThreatActor")
    assert exc.value.status_code == 400

    # 有节点使用时不可删除自定义类型
    graph_board.upsert_node(_sample_node("ent_p", "张三", "Person"))
    with pytest.raises(graph_board.GraphBoardError):
        graph_board.delete_type("Person")

    # 删除节点后可删除类型
    graph_board.delete_node("ent_p")
    assert graph_board.delete_type("Person")["status"] == "deleted"


def test_rag_context_two_hop():
    board = graph_board.create_board("rag")["name"]
    graph_board.open_board(board)
    graph_board.upsert_node(_sample_node("ent_center", "中心"))
    graph_board.upsert_node(_sample_node("ent_mid", "中间"))
    graph_board.upsert_node(_sample_node("ent_leaf", "叶子"))
    graph_board.upsert_edge(
        {
            "id": "r1",
            "source": "ent_center",
            "target": "ent_mid",
            "relation": "USES",
            "description": "中心使用中间",
            "weight": 0.8,
        }
    )
    graph_board.upsert_edge(
        {
            "id": "r2",
            "source": "ent_mid",
            "target": "ent_leaf",
            "relation": "RESOLVES_TO",
            "description": "中间解析到叶子",
            "weight": 0.7,
        }
    )

    resp = graph_board.rag_context("ent_center")
    assert "检索上下文：中心" in resp["context"]
    assert "1 跳关系" in resp["context"]
    assert "2 跳关系" in resp["context"]
    assert "USES" in resp["context"]
    assert "RESOLVES_TO" in resp["context"]
    assert "叶子" in resp["context"]
    assert "report_ent_center" in resp["context"]


def test_board_rename_and_delete_switch():
    graph_board.create_board("旧名字")
    graph_board.open_board("旧名字")
    renamed = graph_board.rename_board("旧名字", "新名字")
    assert renamed["name"] == "新名字"
    assert graph_board.get_boards()["current"] == "新名字"

    graph_board.create_board("另一个")
    graph_board.open_board("新名字")
    deleted = graph_board.delete_board("新名字")
    assert deleted["status"] == "deleted"
    # 删除当前画板后自动切换到第一个可用画板
    assert graph_board.get_boards()["current"] == "另一个"


def test_save_persists_to_file():
    graph_board.create_board("保存测试")
    graph_board.open_board("保存测试")
    graph_board.upsert_node(_sample_node("ent_x", "X"))

    result = graph_board.save()
    assert result["nodes"] == 1
    assert result["board"] == "保存测试"

    # 重新载入验证持久化内容
    graph_board.open_board("保存测试")
    assert graph_board.get_graph()["nodes"][0]["name"] == "X"


def test_graph_status_saved_flag():
    # 未打开画板
    assert graph_board.graph_status() == {
        "board": "",
        "has_board": False,
        "saved": False,
        "nodes": 0,
        "edges": 0,
    }

    graph_board.create_board("状态检查")
    graph_board.open_board("状态检查")
    # 刚打开（无修改）应视为已保存
    assert graph_board.is_board_saved() is True

    # 修改内存后变为未保存
    graph_board.upsert_node(_sample_node("ent_s", "S"))
    assert graph_board.is_board_saved() is False
    st = graph_board.graph_status()
    assert st["has_board"] is True and st["saved"] is False and st["nodes"] == 1

    # 保存后恢复已保存
    graph_board.save()
    assert graph_board.graph_status()["saved"] is True


def test_search_graph_keyword():
    graph_board.create_board("检索")
    graph_board.open_board("检索")
    graph_board.upsert_node(
        {
            "id": "ent_apt29",
            "name": "APT29",
            "type": "ThreatActor",
            "description": "俄罗斯 SVR 关联的 APT 组织",
            "properties": {"alias": "Cozy Bear"},
            "source_chunks": ["report_001"],
        }
    )
    graph_board.upsert_node(_sample_node("ent_mal", "Cobalt Strike Beacon", "Malware"))
    graph_board.upsert_edge(
        {
            "id": "rel1",
            "source": "ent_apt29",
            "target": "ent_mal",
            "relation": "CONTROLS",
            "description": "APT29 控制 Beacon",
            "weight": 0.9,
        }
    )

    # 按名称检索
    result = graph_board.search_graph("apt29")
    assert "APT29" in result
    assert "ThreatActor" in result
    assert "Cozy Bear" in result
    assert "CONTROLS" in result
    assert "Cobalt Strike Beacon" in result

    # 按描述关键词检索
    assert "APT29" in graph_board.search_graph("SVR")

    # 未命中
    assert "未找到" in graph_board.search_graph("不存在的实体")

    # 空关键词报错
    with pytest.raises(graph_board.GraphBoardError):
        graph_board.search_graph("   ")


def test_switch_board_syncs_agent_query_source():
    """切换画板后，graphrag 状态与检索应同步跟随新的当前画板。"""
    # 画板 A：实体 Alpha
    graph_board.create_board("画板A")
    graph_board.open_board("画板A")
    graph_board.upsert_node(_sample_node("ent_alpha", "Alpha 组织", "Organization"))
    graph_board.save()
    assert "Alpha 组织" in graph_board.search_graph("Alpha")

    # 画板 B：实体 Beta
    graph_board.create_board("画板B")
    graph_board.open_board("画板B")
    graph_board.upsert_node(_sample_node("ent_beta", "Beta 组织", "Organization"))
    graph_board.save()

    # 切回画板 A：状态与检索都指向 A
    graph_board.open_board("画板A")
    st = graph_board.graph_status()
    assert st["board"] == "画板A" and st["saved"] is True
    assert "Alpha 组织" in graph_board.search_graph("Alpha")
    assert "未找到" in graph_board.search_graph("Beta")

    # 再切到画板 B：自动跟随 B
    graph_board.open_board("画板B")
    assert graph_board.graph_status()["board"] == "画板B"
    assert "Beta 组织" in graph_board.search_graph("Beta")
    assert "未找到" in graph_board.search_graph("Alpha")


def test_search_graph_limit_and_truncate():
    graph_board.create_board("检索限制")
    graph_board.open_board("检索限制")
    # 多个匹配实体：验证 limit 生效
    for i in range(3):
        graph_board.upsert_node(
            _sample_node(f"ent_k{i}", f"关键词实体{i}", "Organization")
        )

    result = graph_board.search_graph("关键词实体", limit=2)
    assert "关键词实体0" in result
    assert "关键词实体1" in result
    assert "关键词实体2" not in result

    # 超长结果截断
    graph_board.upsert_node(
        {
            "id": "ent_long",
            "name": "超长实体",
            "type": "Organization",
            "description": "很长的描述，" * 500,
            "properties": {},
            "source_chunks": [],
        }
    )
    truncated = graph_board.search_graph("超长实体", max_chars=800)
    assert len(truncated) <= 850
    assert "已截断" in truncated

    # limit 参数归一化
    assert len(graph_board.search_graph("关键词实体", limit=0).splitlines()) >= 1
