from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from pathlib import Path
from langgraph.store.memory import InMemoryStore
from deepagents.backends.utils import create_file_data
def load_skill()->dict:
    skills_dir = Path.home() / ".claude" / "skills"
    skills_dict = {}

    for folder in skills_dir.iterdir() if skills_dir.exists() else []:
        if folder.is_dir():
            skill_md = folder / "SKILL.md"
            if skill_md.exists():
                try:
                    skills_dict[folder.name] = skill_md.read_text(encoding="utf-8")
                except Exception as e:
                    skills_dict[folder.name] = f"Error: {e}"
    return skills_dict


store = InMemoryStore()
skills_dict=load_skill()

for skill_name, skill_content in skills_dict.items():
    store.put(
        namespace=("filesystem",),
        key=f"/skills/{skill_name}/SKILL.md",
        value=create_file_data(skill_content)
    )

def create_agent():
    agent = create_deep_agent(
        memory=['./prompt/AGENTS.md'],
        backend=(lambda rt: StoreBackend(rt)),
        store=store,
        skills=["/skills/"]
    )
    return agent