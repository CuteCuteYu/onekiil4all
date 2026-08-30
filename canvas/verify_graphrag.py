"""
GraphRAG 可用性验证脚本
========================
验证保存的图数据（graphs/默认画板.json）作为 GraphRAG 索引的真实可用性：

1. 加载保存的图数据，转换为 GraphRAG 索引格式（entities / relationships，与前端导出一致）
2. 构建 NetworkX 知识图谱
3. 用 Anthropic 兼容 API（读取 ANTHROPIC_* 环境变量）真实跑 GraphRAG 局部查询：
   实体识别 → 子图检索（1~2 跳）→ 上下文拼接 → LLM 生成回答
"""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
import networkx as nx

# ---------------------------------------------------------------------------
# Anthropic 兼容环境变量（智谱 GLM-4.7）
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "").rstrip("/")
AUTH_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
MODEL = os.environ.get("ANTHROPIC_MODEL", "GLM-4.7")

BOARD_FILE = Path(__file__).resolve().parent / "graphs" / "默认画板.json"


def call_llm(system: str, user: str, max_tokens: int = 1024) -> str:
    """调用 Anthropic 兼容 Messages API。"""
    headers = {
        "x-api-key": AUTH_TOKEN,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    with httpx.Client(timeout=120) as client:
        resp = client.post(f"{BASE_URL}/v1/messages", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"].strip()


# ---------------------------------------------------------------------------
# 数据加载与索引转换
# ---------------------------------------------------------------------------
def load_board() -> dict:
    with open(BOARD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def to_graphrag_index(data: dict) -> dict:
    """转换为 GraphRAG 索引格式（与前端「导出 GraphRAG 索引」一致）。"""
    return {
        "graph_name": "情报分析图谱",
        "exported_at": datetime.now(UTC).astimezone().isoformat(),
        "entities": data["nodes"],
        "relationships": data["edges"],
        "graphrag_compat": {
            "ms_graphrag": "entities 对应 entity 表，relationships 对应 relationship 表，source_chunks 对应 text_unit 关联",
            "llamaindex": "每条 relationship 可转换为 (head, relation, tail) 三元组",
        },
    }


def build_nx(data: dict) -> nx.DiGraph:
    G = nx.DiGraph()
    for n in data["nodes"]:
        G.add_node(n["id"], **n)
    for e in data["edges"]:
        G.add_edge(e["source"], e["target"], **e)
    return G


# ---------------------------------------------------------------------------
# GraphRAG 局部查询：实体识别 → 子图检索 → 上下文 → LLM
# ---------------------------------------------------------------------------
def extract_entities(question: str, node_names: list[str]) -> list[str]:
    """用 LLM 从问题中识别实体，并映射到图谱中存在的节点。"""
    system = (
        "你是情报图谱检索助手。从用户问题中提取提到的实体名称，"
        "只返回 JSON 数组（如 [\"APT29\", \"Cobalt Strike Beacon\"]），不要输出其他内容。"
    )
    user = (
        f"图谱中的实体包括：{', '.join(node_names)}\n"
        f"问题：{question}\n"
        "请提取问题中提到的实体名称（必须是图谱中存在的）："
    )
    try:
        resp = call_llm(system, user, max_tokens=200)
        m = re.search(r"\[.*?\]", resp, re.DOTALL)
        if m:
            names = json.loads(m.group(0))
            return [n for n in names if n in node_names]
    except (ValueError, json.JSONDecodeError) as e:
        print(f"  [实体识别失败] {e}")
    return []


def retrieve_subgraph(G: nx.DiGraph, node_ids: list[str], hops: int = 2):
    """提取 1~2 跳子图节点与三元组。"""
    nodes = set(node_ids)
    frontier = set(node_ids)
    for _ in range(hops):
        new = set()
        for n in frontier:
            new |= set(G.successors(n)) | set(G.predecessors(n))
        frontier = new - nodes
        nodes |= new
    triplets = []
    for u, v, data in G.edges(data=True):
        if u in nodes and v in nodes:
            triplets.append(
                (
                    G.nodes[u].get("name", u),
                    data.get("relation", "RELATED_TO"),
                    G.nodes[v].get("name", v),
                    data.get("description", ""),
                )
            )
    return nodes, triplets


def build_context(G: nx.DiGraph, node_ids: set, triplets: list) -> str:
    """拼接 GraphRAG 检索上下文（实体描述 + 语义三元组）。"""
    lines = []
    for nid in node_ids:
        n = G.nodes[nid]
        lines.append(f"实体：{n.get('name')}（{n.get('type')}）")
        lines.append(f"描述：{n.get('description', '')}")
    lines.append("关系三元组：")
    for s, r, t, d in triplets:
        lines.append(f"- ({s}) --[{r}]--> ({t})：{d}")
    return "\n".join(lines)


def graphrag_query(question: str, G: nx.DiGraph, node_names: list[str]) -> str:
    """GraphRAG 局部查询全流程。"""
    print(f"\n{'=' * 64}")
    print(f"问题：{question}")

    # 1. 实体识别
    entities = extract_entities(question, node_names)
    print(f"① 实体识别：{entities}")
    if not entities:
        return "（未能从问题中识别到图谱实体）"

    # 2. 子图检索
    node_ids = [nid for nid, n in G.nodes(data=True) if n.get("name") in entities]
    sub_nodes, triplets = retrieve_subgraph(G, node_ids, hops=2)
    print(f"② 子图检索：{len(sub_nodes)} 节点 / {len(triplets)} 三元组")

    # 3. 上下文拼接
    context = build_context(G, sub_nodes, triplets)

    # 4. LLM 生成
    system = (
        "你是基于情报知识图谱回答问题的分析助手。"
        "请严格基于提供的图谱上下文回答，不要编造图谱中不存在的信息。"
        "回答用中文，简洁准确。"
    )
    user = f"【知识图谱上下文】\n{context}\n\n【问题】{question}\n\n请基于图谱上下文回答："
    answer = call_llm(system, user, max_tokens=800)
    return answer


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 64)
    print("GraphRAG 可用性验证")
    print(f"模型：{MODEL}")
    print(f"Base URL：{BASE_URL}")
    print(f"数据文件：{BOARD_FILE}")

    data = load_board()
    index = to_graphrag_index(data)
    print(f"GraphRAG 索引：{len(index['entities'])} 实体 / {len(index['relationships'])} 关系")

    G = build_nx(data)
    node_names = [n.get("name") for n in data["nodes"]]

    questions = [
        "APT29 使用哪些恶意软件和工具？",
        "Cobalt Strike Beacon 通过什么域名和 IP 通信？",
        "Zerologon 漏洞被谁利用？它影响什么？",
    ]
    for q in questions:
        try:
            ans = graphrag_query(q, G, node_names)
            print(f"③ 回答：{ans}")
        except Exception as e:  # noqa: BLE001 - 验证脚本逐条尝试，失败不影响后续查询
            print(f"[查询失败] {e}")

    print("=" * 64)
    print("验证完成")


if __name__ == "__main__":
    main()