# T42 真实浏览器与可访问性检查

- 检查日期：2026-09-06
- 检查对象：本地完整前端 + 确定性Mock后端
- 浏览器：Playwright自带Chromium
- 视口：手机`320×844`、`390×844`、`430×844`；桌面`1280×900`
- 真实性边界：这是浏览器运行证据，不是人工无障碍认证，也不是实体手机安装证明；未调用DeepSeek，未部署公开网址。

## 1. 检查结论

T42要求的桌面、手机、导航、响应式、键盘、控制台和网络错误检查均已完成。七个主要页面在手机和桌面浏览器中无页面级横向溢出；可见按钮、链接和输入框均有可读名称；图片均声明替代文字；每页只有一个`main`和一个主标题。完整五轮中文输入可进入双层推荐结果，运行期间没有浏览器控制台警告、错误或HTTP 4xx/5xx响应。

当前健康度：**通过，但保留一项实体设备手工检查**。PWA清单、标准安装图标和无需安装的普通链接路径均已验证；由于本次没有把完整前后端部署到可由实体手机访问的HTTPS地址，因此没有冒充“已在手机系统里点过安装”。

## 2. RED → GREEN记录

| 初次失败 | 最小修复 | 回归证据 |
| --- | --- | --- |
| 选宠对话页没有一级主标题 | 把动态页标题改成语义正确的`h1`，视觉不变 | 组件测试 + 七页结构审计 |
| Demo弹窗打开后焦点仍停在背景按钮，Escape不能关闭 | 打开后聚焦关闭按钮，Escape关闭，关闭后焦点回到原按钮，并为每个弹窗生成唯一标题ID | 组件测试 + 手机／桌面键盘E2E |
| 首屏图片触发LCP加载警告 | 只把各页面首屏候选图设为优先加载 | 手机／桌面控制台零警告 |
| Manifest只有`any`尺寸图标，无法证明满足常见安装图标要求 | 从已批准港湾插画生成真实`192×192`和`512×512`PNG并写入Manifest | PWA清单E2E |
| 截图动作在页面水合期间隐藏光标，制造假性水合警告 | 等待页面网络稳定，并保留真实光标后再截图 | 手机／桌面控制台零警告 |

## 3. 页面与交互检查

| 范围 | 手机 | 桌面 | 结果 |
| --- | --- | --- | --- |
| 首页、选宠、市场、用品、社区、我的、会员中心 | 已运行 | 已运行 | 通过 |
| 页面级横向溢出 | 320／390／430px | 1280px | 无 |
| 固定底栏和主要导航 | 已检查 | 已检查 | 可见且可达 |
| 中文自由输入 | 五轮按Enter发送 | 五轮按Enter发送 | 均进入推荐结果 |
| Demo弹窗键盘操作 | Enter打开、Escape关闭、焦点返回 | 同左 | 通过 |
| 控制台warning/error | 0 | 0 | 通过 |
| HTTP 4xx/5xx | 0 | 0 | 通过 |

## 4. 可访问性检查

- 七个主要页面均有一个`main`和一个一级标题。
- 所有当前可见的按钮、链接、输入框和文本框都有可读名称。
- 所有图片均有`alt`属性；纯装饰图标继续使用`aria-hidden`。
- Demo弹窗提供`role="dialog"`、`aria-modal`和唯一标题关联。
- 键盘可以打开弹窗、关闭弹窗并回到原来的操作位置。
- 本次没有使用屏幕阅读器，也没有声称达到完整WCAG等级；该项如成为正式上线要求，需要另做人工审查。

## 5. 视觉复查

优点：手机与桌面保持同一套430px手机App画布；首页主入口、分类、卡片、固定底栏层级清楚；选宠页问题、快捷回答、自由输入和画像顺序自然；社区、市场、用品、“我的”和会员中心延续同一视觉语言。

保留风险：长页面截图中固定底栏会覆盖截图经过位置的一小段内容，这是固定导航的正常截屏表现，实际滚动可继续查看；用品分类本身是横向滑动栏，并非整页溢出。实体手机的“添加到主屏幕”系统弹窗尚未手工点击验证。

## 6. 截图证据

- [手机首页](screenshots/t42/mobile-chromium/01-home.png)
- [手机选宠](screenshots/t42/mobile-chromium/02-agent.png)
- [手机市场](screenshots/t42/mobile-chromium/03-market.png)
- [手机用品](screenshots/t42/mobile-chromium/04-supplies.png)
- [手机社区](screenshots/t42/mobile-chromium/05-community.png)
- [手机我的](screenshots/t42/mobile-chromium/06-me.png)
- [手机会员中心](screenshots/t42/mobile-chromium/07-membership.png)
- [键盘弹窗](screenshots/t42/mobile-chromium/08-keyboard-dialog.png)
- [五轮推荐结果](screenshots/t42/mobile-chromium/09-recommendation-result.png)
- [320px首页首屏](screenshots/t42/mobile-chromium/10-home-320px.png)
- [430px首页首屏](screenshots/t42/mobile-chromium/10-home-430px.png)
- [桌面首页](screenshots/t42/desktop-chromium/01-home.png)

## 7. 可复现命令

```powershell
cd E:\project\frontend
pnpm exec playwright test e2e/t42-audit.spec.ts
```

最终结果：`9 passed, 1 skipped`；跳过项是桌面项目不重复运行手机宽度矩阵，不是功能失败。
