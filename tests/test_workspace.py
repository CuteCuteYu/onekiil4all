"""工作区（workspace）状态管理与 API 测试"""

import pytest
from fastapi.testclient import TestClient

from agent_set import workspace


@pytest.fixture(autouse=True)
def _reset_workspace(monkeypatch, tmp_path):
    """每个用例独立：清空工作区 + 记录文件重定向到临时目录"""
    record = tmp_path / "workspace.json"
    monkeypatch.setattr(workspace, "_WORKSPACE_RECORD", record)
    workspace.clear_workspace()
    yield
    workspace.clear_workspace()


class TestWorkspaceState:
    def test_initial_not_ready(self):
        assert workspace.get_workspace() is None
        assert workspace.is_ready() is False

    def test_set_workspace_roundtrip(self, tmp_path):
        ws = tmp_path / "my-ws"
        ws.mkdir()
        resolved = workspace.set_workspace(ws)
        assert resolved == ws.resolve()
        assert workspace.is_ready() is True
        assert workspace.get_workspace() == resolved

    def test_set_workspace_rejects_missing_dir(self, tmp_path):
        with pytest.raises(ValueError):
            workspace.set_workspace(tmp_path / "not-exist")

    def test_set_workspace_rejects_file(self, tmp_path):
        f = tmp_path / "afile.txt"
        f.write_text("x", encoding="utf-8")
        with pytest.raises(ValueError):
            workspace.set_workspace(f)

    def test_persist_and_restore(self, tmp_path):
        """选择写入记录文件后，新进程首次访问可恢复"""
        ws = tmp_path / "persist-ws"
        ws.mkdir()
        workspace.set_workspace(ws)

        # 模拟新进程：重置已加载标志
        workspace._current = None
        workspace._loaded = False
        assert workspace.get_workspace() == ws.resolve()

    def test_persist_ignores_deleted_dir(self, tmp_path):
        """记录的目录被删除后，恢复时视为未选择"""
        ws = tmp_path / "gone-ws"
        ws.mkdir()
        workspace.set_workspace(ws)
        ws.rmdir()

        workspace._current = None
        workspace._loaded = False
        assert workspace.get_workspace() is None

    def test_clear_workspace(self, tmp_path):
        ws = tmp_path / "clear-ws"
        ws.mkdir()
        workspace.set_workspace(ws)
        workspace.clear_workspace()
        assert workspace.is_ready() is False

    def test_resolve_in_workspace_relative(self, tmp_path):
        ws = tmp_path / "resolve-ws"
        ws.mkdir()
        workspace.set_workspace(ws)
        resolved = workspace.resolve_in_workspace("report.md")
        assert resolved == (ws / "report.md").resolve()

    def test_resolve_in_workspace_absolute_passthrough(self, tmp_path):
        ws = tmp_path / "resolve-abs"
        ws.mkdir()
        workspace.set_workspace(ws)
        abs_path = str(tmp_path / "elsewhere.txt")
        assert str(workspace.resolve_in_workspace(abs_path)) == abs_path

    def test_resolve_in_workspace_requires_workspace(self):
        with pytest.raises(RuntimeError):
            workspace.resolve_in_workspace("x.txt")


class TestWorkspaceAPI:
    @pytest.fixture()
    def client(self):
        from web.web_server import app

        return TestClient(app)

    def test_get_workspace_not_ready(self, client):
        resp = client.get("/api/workspace")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is False
        assert data["workspace"] is None

    def test_post_workspace_success(self, client, tmp_path):
        ws = tmp_path / "api-ws"
        ws.mkdir()
        resp = client.post("/api/workspace", json={"path": str(ws)})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True
        assert data["workspace"] == str(ws.resolve())

    def test_post_workspace_invalid_path(self, client, tmp_path):
        resp = client.post("/api/workspace", json={"path": str(tmp_path / "nope")})
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_delete_workspace(self, client, tmp_path):
        ws = tmp_path / "api-del"
        ws.mkdir()
        client.post("/api/workspace", json={"path": str(ws)})
        resp = client.delete("/api/workspace")
        assert resp.status_code == 200
        assert resp.json()["ready"] is False

    def test_chat_blocked_without_workspace(self, client):
        """未选择工作区时，聊天接口必须返回 409"""
        resp = client.post(
            "/api/chat",
            json={"message": "帮我创建一个文件", "thread_id": "ws-test-thread"},
        )
        assert resp.status_code == 409
        assert "工作区" in resp.json()["detail"]
