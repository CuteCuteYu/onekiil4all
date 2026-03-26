from langchain_openai import ChatOpenAI
import dotenv
import os
dotenv.load_dotenv()
model = ChatOpenAI(
    model="glm-4.7",
)