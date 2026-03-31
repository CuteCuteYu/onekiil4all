"""
========================================
Model Set - 模型配置模块
========================================
功能: 配置和管理AI大语言模型
使用DeepSeek API（兼容OpenAI SDK）
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════
# 导入LangChain和标准库
# ═══════════════════════════════════════════════════════════════

from langchain_openai import ChatOpenAI
from langchain_core.utils import convert_to_secret_str
import dotenv
import os

# 加载环境变量
dotenv.load_dotenv()

# ═══════════════════════════════════════════════════════════════
# DeepSeek模型初始化
# ═══════════════════════════════════════════════════════════════

# 从环境变量获取DeepSeek API密钥
deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")

# 创建ChatOpenAI模型实例
# 使用DeepSeek的deepseek-chat模型
# 通过base_url指定使用DeepSeek API端点
model = ChatOpenAI(
    model="deepseek-chat",
    api_key=convert_to_secret_str(deepseek_api_key) if deepseek_api_key else None,
    base_url="https://api.deepseek.com",
)
