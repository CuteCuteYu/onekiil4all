from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.checkpoint.memory import InMemorySaver

from .skill_set import create_skill_store
from .tools_set import tools
from model_set import model_set

store = create_skill_store()


def create_agent():
    agent = create_deep_agent(
        model=model_set.model,  # 使用配置的 DeepSeek 模型
        memory=["./prompt/AGENTS.md"],
        backend=(lambda rt: StoreBackend(rt)),
        store=store,
        skills=["/skills/"],
        tools=tools,
        checkpointer=InMemorySaver(),
    )
    return agent
