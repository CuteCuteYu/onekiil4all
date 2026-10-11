"""技能目录与加载测试（项目内 skills/，不依赖 ~/.claude/skills）"""

from agent_set import skill_set


def test_default_skills_dir_is_project_local():
    path = str(skill_set.SKILLS_DIR).replace("\\", "/")
    assert path.endswith("/skills")
    assert ".claude" not in path


def test_load_skill_reads_subfolders_only(tmp_path, monkeypatch):
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Demo", encoding="utf-8")
    # 技能目录根下的散文件不应被当作技能
    (tmp_path / "README.md").write_text("not a skill", encoding="utf-8")
    monkeypatch.setattr(skill_set, "SKILLS_DIR", tmp_path)

    assert skill_set.load_skill() == {"demo": "# Demo"}


def test_load_skill_files_includes_auxiliary_files(tmp_path, monkeypatch):
    skill = tmp_path / "demo"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Demo", encoding="utf-8")
    (skill / "references" / "extra.md").write_text("aux", encoding="utf-8")
    monkeypatch.setattr(skill_set, "SKILLS_DIR", tmp_path)

    files = skill_set.load_skill_files()["demo"]
    assert files["SKILL.md"] == "# Demo"
    assert files["references/extra.md"] == "aux"


def test_missing_skills_dir_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(skill_set, "SKILLS_DIR", tmp_path / "nope")
    assert skill_set.load_skill() == {}
    assert skill_set.load_skill_files() == {}


def test_all_project_skills_are_spec_compliant():
    """项目内每个技能都应符合 Agent Skills 规范

    规范要求：每个技能是子目录且含 SKILL.md；frontmatter 必须提供 description；
    若写了 name，必须与目录名完全一致（否则 SkillsMiddleware 会告警并降级处理）。
    """
    import re

    skills_dir = skill_set.SKILLS_DIR
    if not skills_dir.exists():
        return

    checked = 0
    for folder in skills_dir.iterdir():
        if not folder.is_dir():
            continue
        skill_md = folder / "SKILL.md"
        assert skill_md.exists(), f"{folder.name} 缺少 SKILL.md"

        text = skill_md.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{folder.name}/SKILL.md 缺少 YAML frontmatter"
        frontmatter = text.split("---", 2)[1]
        assert "description:" in frontmatter, f"{folder.name} 缺少 description"

        name_match = re.search(r"^name:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
        if name_match:
            assert name_match.group(1) == folder.name, (
                f"{folder.name} 的 frontmatter name 必须与目录名一致"
            )
        checked += 1

    assert checked >= 1, "skills/ 下至少应有一个技能"
