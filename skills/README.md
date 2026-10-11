# Skills （项目内技能目录）

本目录是**本项目专属**的技能目录，与 Claude Code 的 `~/.claude/skills` **完全独立**。
Agent 启动时会扫描本目录（见 `agent_set/skill_set.py` → `SKILLS_DIR`），并把技能写入
深代理的虚拟文件系统 `/skills/...`，供 `skills=["/skills/"]` 使用。

## 目录结构

每个技能是**一个子文件夹**，文件夹名即技能名，里面至少有一个 `SKILL.md`：

```
skills/
├── README.md              ← 本文件（不会被当作技能，只有子文件夹才会）
├── osint-recon/           ← 内置：OSINT 情报搜集流程（用户提到"搜集/搜索/查找/调查…"时触发）
│   ├── SKILL.md
│   └── references/
│       └── search-operators.md
└── <skill-name>/
    ├── SKILL.md           ← 必需：技能说明 + 使用时机
    ├── references/        ← 可选：细节文档（按需读取）
    └── scripts/           ← 可选：脚本/示例
```

> **触发机制**：模型只会看到每个技能的「名称 + description + 路径」索引，
> 需要时再 `read_file` 读取 SKILL.md 正文。因此**触发条件必须写在 frontmatter 的 `description` 里**
> （例如"当用户提到…时使用"），写进正文是无效的。

支持作为技能辅助文件的扩展名：`.md .txt .py .sh .json .yaml .yml .toml .js .ts`，
单个文件超过 200KB 会被跳过。

## SKILL.md 格式

推荐使用 YAML frontmatter 声明元信息，其后写清「什么时候用、怎么用」：

```markdown
---
name: osint-domain-recon
description: 对域名做公开信息梳理（WHOIS/证书/公开引用）时的标准流程
---

# 域名公开信息梳理

## 何时使用
用户要求对某个域名做公开信息收集时。

## 步骤
1. ...
```

> 说明：`description` 会被 `/api/skills` 用于列表展示（无 frontmatter 时取正文第一个非空行）。

> ⚠️ 若写了 frontmatter 的 `name`，**它必须与文件夹名完全一致**，否则启动时会提示
> “does not follow Agent Skills specification”。最省事的做法是 frontmatter 里只写 `description`。

## 覆盖目录

如需改用其他目录（例如共享技能库），设置环境变量：

```powershell
$env:SKILLS_DIR = "D:\shared\skills"
```
