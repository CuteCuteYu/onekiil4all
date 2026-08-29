"""TodoManager 的 Markdown 读写解析测试"""

from web.todo_manager import TodoManager


def _make_manager(tmp_path):
    return TodoManager("thread-abc", base_dir=tmp_path)


def test_save_and_read_roundtrip(tmp_path):
    mgr = _make_manager(tmp_path)
    tasks = [
        {"description": "第一步", "completed": True},
        {"description": "第二步", "completed": False},
    ]
    mgr.save_todo(tasks)

    assert mgr.exists()
    loaded, content = mgr.read_todo()
    assert len(loaded) == 2
    assert loaded[0] == {"description": "第一步", "completed": True}
    assert loaded[1] == {"description": "第二步", "completed": False}
    assert "[+] 第一步" in content
    assert "[-] 第二步" in content


def test_read_todo_missing_file(tmp_path):
    mgr = _make_manager(tmp_path)
    tasks, content = mgr.read_todo()
    assert tasks == []
    assert content == ""
    assert not mgr.exists()


def test_read_todo_ignores_non_task_lines(tmp_path):
    mgr = _make_manager(tmp_path)
    mgr.todo_dir.mkdir(parents=True, exist_ok=True)
    mgr.todo_file.write_text(
        "# TODO 列表 - Thread: t\n\n"
        "## 任务清单\n\n"
        "[+] 真实任务\n"
        "普通文本行\n"
        "[-] 另一个任务\n",
        encoding="utf-8",
    )

    tasks, _content = mgr.read_todo()
    assert [t["description"] for t in tasks] == ["真实任务", "另一个任务"]
    assert tasks[0]["completed"] is True
    assert tasks[1]["completed"] is False


def test_save_empty_tasks_writes_placeholder(tmp_path):
    mgr = _make_manager(tmp_path)
    mgr.save_todo([])
    tasks, content = mgr.read_todo()
    assert tasks == []
    assert "AI 正在分析任务" in content


def test_delete_todo(tmp_path):
    mgr = _make_manager(tmp_path)
    mgr.save_todo([{"description": "x", "completed": False}])
    assert mgr.exists()
    mgr.delete_todo()
    assert not mgr.exists()
    assert not mgr.todo_dir.exists()
