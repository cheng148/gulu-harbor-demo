# T38 社区原型验证记录

日期：2026-08-14

## 范围

- 浏览3条明确标注为Demo虚拟内容的社区帖子。
- 点赞与收藏仅写入`gulu-harbor.prototype.v1`本地原型状态。
- 打开和关闭模拟帖子详情。
- 真实发帖统一提示“Demo演示功能，暂未开放”，不产生发布成功状态。
- 不接社区后台，不修改Agent、推荐规则或产品方案。

## TDD证据

### RED

命令：`pnpm --dir frontend test -- src/components/community/community-flow.test.tsx`

结果：目标测试因`../../app/community/page`不存在而在导入阶段失败；当时其他14个测试文件、43条测试通过。失败原因与“T38社区页面尚未实现”一致。

### GREEN

命令：`pnpm --dir frontend test`

结果：15个测试文件、46条测试全部通过；T38新增3条组件测试覆盖浏览、点赞、收藏、详情和受限发帖。

### REFACTOR与静态验证

- `pnpm --dir frontend lint`：通过。
- `pnpm --dir frontend typecheck`：通过。
- `pnpm --dir frontend build`：通过；生成静态`/community`路由。

## 真实浏览器验证

使用生产构建和真实Chromium，分别在390x844手机视口与1280x900桌面视口运行`frontend/e2e/community.spec.ts`：

- 2条浏览器用例通过，每条约1秒。
- 覆盖3条帖子、点赞、收藏、刷新恢复、详情弹窗、发帖未开放、底部社区选中状态和无横向溢出。
- 生产构建页面控制台没有错误或警告。
- Playwright用例完成后，Windows上的Next WebServer子进程没有按时退出，外层命令因此达到180秒超时；页面用例本身均已明确显示`ok`。

## 触及文件

- `frontend/src/app/community/page.tsx`
- `frontend/src/components/community/community-data.ts`
- `frontend/src/components/community/post-card.tsx`
- `frontend/src/components/community/post-dialog.tsx`
- `frontend/src/components/community/community.module.css`
- `frontend/src/components/community/community-flow.test.tsx`
- `frontend/e2e/community.spec.ts`

## 已知限制

- 首页现有“社区”按钮仍保持旧的未开放反馈；全站导航可达原计划属于T39。当前社区页可直接通过`/community`访问，且页面内底部导航正确标记社区为当前页。
- Windows `apply_patch`沙箱持续对所有既有文件返回`helper_unknown_error`，所以本轮不能同步更新`PROJECT_CONTEXT.md`、`START_HERE.md`和`specs/TASKS.md`，也不能删除浏览器验证时新增的两份专用配置文件。没有使用整文件覆盖绕过限制。
- 未调用DeepSeek、未上传GitHub、未发布分享版，未开始T39。
