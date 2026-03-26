from model_set import model_set
from agent_set import agent_set
model=model_set.model
agent = agent_set.create_agent()



def chat(content:str)->str:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ]
        },
        config={"configurable": {"thread_id": "12345"}},
    )
    return result['messages'][1].content

if __name__ == '__main__':
    print(chat("你有哪些skills？"))