import uuid

from model_set import model_set
from agent_set import agent_set

model = model_set.model
agent = agent_set.create_agent()
thread_id = str(uuid.uuid4())


def chat(content: str) -> str:
    global thread_id
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ]
        },
        config={"configurable": {"thread_id": thread_id}},
    )
    # 取最后一条 AI 消息作为回复（跳过 tool 消息）
    for msg in reversed(result['messages']):
        if hasattr(msg, 'content') and msg.type == 'ai' and msg.content:
            return msg.content
    return result['messages'][-1].content


def new_chat():
    global thread_id
    thread_id = str(uuid.uuid4())
    print(f"新对话已创建 (thread_id: {thread_id})")


if __name__ == '__main__':
    print("聊天已启动，输入 'quit'/'exit' 退出，'/new' 开始新对话")
    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() in ('quit', 'exit', 'q'):
            print("再见！")
            break
        if user_input.lower() == '/new':
            new_chat()
            continue
        response = chat(user_input)
        print(f"\n助手: {response}")