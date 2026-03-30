from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.checkpoint.memory import InMemorySaver

from .skill_set import create_skill_store
from .tools_set import tools

store = create_skill_store()


def create_agent():
    agent = create_deep_agent(
        memory=['./prompt/AGENTS.md'],
        backend=(lambda rt: StoreBackend(rt)),
        store=store,
        skills=["/skills/"],
        tools=tools,
        checkpointer=InMemorySaver()
    )
    return agent
