from langchain_openai import ChatOpenAI
from langchain_core.utils import convert_to_secret_str
import dotenv
import os

dotenv.load_dotenv()

# 使用 DeepSeek API (兼容 OpenAI SDK)
deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
model = ChatOpenAI(
    model="deepseek-chat",
    api_key=convert_to_secret_str(deepseek_api_key) if deepseek_api_key else None,
    base_url="https://api.deepseek.com",
)
