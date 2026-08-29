"""
========================================
Model Set - 模型配置模块
========================================
功能: 配置和管理AI大语言模型（Anthropic 兼容协议）
默认读取计算机中 ANTHROPIC_ 开头的环境变量:
- ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY: 认证凭据（二选一）
- ANTHROPIC_BASE_URL: API 端点（默认官方地址）
- ANTHROPIC_MODEL: 模型名称
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════════════
# 导入LangChain和标准库
# ═══════════════════════════════════════════════════════════════════════

import os

import dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.utils import convert_to_secret_str

# 加载环境变量（.env 中也可覆盖这些配置）
dotenv.load_dotenv()

# ═══════════════════════════════════════════════════════════════════════
# 模型初始化（Anthropic 兼容）
# ═══════════════════════════════════════════════════════════════════════

# 认证凭据：优先 AUTH_TOKEN（Bearer 场景，如智谱等兼容端点），其次 API_KEY
auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get(
    "ANTHROPIC_API_KEY"
)
if not auth_token:
    raise RuntimeError(
        "缺少 ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY 环境变量。"
        "请在环境变量或项目根目录 .env 文件中配置后重新启动。"
    )

# API 端点与模型名称（缺省时回退到 Anthropic 官方默认）
base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
model_name = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

# 创建 ChatAnthropic 模型实例
model = ChatAnthropic(
    model=model_name,
    api_key=convert_to_secret_str(auth_token),
    base_url=base_url,
)
