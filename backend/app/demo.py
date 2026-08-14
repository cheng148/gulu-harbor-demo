"""T32 浏览器验收入口：只使用确定性 Mock，不访问任何真实模型。"""

from app.main import create_app
from app.providers.demo import DemoMockProvider

app = create_app(model_provider=DemoMockProvider())
