"""pytest 共享配置"""

import os

# 部分模块导入链会初始化模型（model_set），缺凭据时直接失败；
# 测试不调用真实 API，设置占位凭据即可完成导入
os.environ.setdefault("ANTHROPIC_AUTH_TOKEN", "test-key-for-imports-only")
