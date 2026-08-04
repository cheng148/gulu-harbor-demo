# 咕噜港 - AI选宠顾问

Phase 0已经完成并通过总验证：当前只有前后端空项目、测试工具和验证入口，不包含选宠业务功能，也没有部署。第二批Phase 1任务尚未获得用户批准。

## 当前技术地基

- 前端：Next.js 16、React 19、TypeScript 5.9、Tailwind CSS 4
- 后端：Python 3.12、FastAPI、uv
- 自动测试：Vitest、Playwright入口、pytest、Ruff、mypy
- 模型：默认`mock`；Phase 6获批后才接入DeepSeek真人演示

## 准备环境

```powershell
powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
```

## 一键验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

## 本地启动

```powershell
pnpm --dir frontend dev
```

```powershell
Push-Location backend
uv run fastapi dev app/main.py --port 8000
Pop-Location
```

前端默认地址为`http://localhost:3000`，后端健康检查为`http://localhost:8000/health`。

## DeepSeek Key安全

真实Key只放在本机`.env`，不要写进聊天、文档、前端代码或Git。`.env.example`只有字段示例，不包含真实秘密。

## 官方依据

- Next.js初始化：https://nextjs.org/docs/app/getting-started/installation
- Next.js Vitest：https://nextjs.org/docs/app/guides/testing/vitest
- Next.js Playwright：https://nextjs.org/docs/app/guides/testing/playwright
- FastAPI与uv：https://fastapi.tiangolo.com/tutorial/
- uv项目管理：https://docs.astral.sh/uv/guides/projects/
