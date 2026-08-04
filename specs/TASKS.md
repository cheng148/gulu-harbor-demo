# TASKS.md

## 0. 文档状态

- 项目：咕噜港AI选宠顾问Demo
- 版本：0.1.0
- 创建日期：2026-08-04
- 输入：`specs/SDD_SPEC.md` 0.2.0、`specs/IMPLEMENTATION_PLAN.md` 0.1.0
- 状态：第一批Phase 0（T00至T05）已完成并通过检查点A、B
- 当前事实：工具链与空项目已编码、运行和测试；选宠业务功能尚未编码、运行、测试或部署
- 门禁：第二批Phase 1未获批准前，不得实施T06及后续业务任务

## 1. 小白阅读说明

这份清单不是让用户亲自操作，而是约束开发过程，防止一次写太多后无法判断哪里出了问题。

- **RED**：先写一个会失败的测试，用它证明“这个功能现在确实还没有”。
- **GREEN**：只写刚好能让测试通过的最小代码。
- **REFACTOR**：测试保持通过的前提下，把代码整理清楚。
- **Mock模型**：一个不会联网、每次答案都一样的“假模型演员”，专门用于自动测试；它只替代模型回答，不替代选宠规则。
- **检查点**：做完2至3个小任务就停下来跑一遍检查，失败就不进入下一组。

每个任务都写明“完成后看到什么”和验证方法。除脚手架自动生成文件外，单项原则上不改超过5个文件。

## 2. 全程硬规则

1. 业务行为一律执行RED -> GREEN -> REFACTOR，并保存失败与通过证据。
2. 默认自动测试强制使用Mock，不联网、不读取DeepSeek Key、不产生模型费用。
3. DeepSeek真实Key不进入聊天、文档、Git或前端，只放本机未提交的`.env`。
4. 页面和公开API不得出现内部数字分；只显示“高度匹配、较匹配、谨慎匹配”等等级。
5. 硬约束不能被软分抵消；过敏、住房限制、家庭安全等可导致排除、澄清或暂不建议。
6. 每个检查点的测试、类型检查、构建或静态检查有一项失败，就停止推进。
7. 新发现的业务行为先回写SDD并获批，再写测试和实现。

## 3. 第一批：Phase 0 地基（本次待批准范围）

这一批只准备可靠的工作环境。完成后能看到两个空项目可以启动、检查命令能工作；看不到选宠功能和正式页面。

### T00 修正文档入口并锁定门禁

- 做什么：修复`START_HERE.md`乱码，写清Gate 0、Gate 1已批准，第一批任务仍待批准。
- 为什么：避免新会话误以为可以跳过测试直接编码。
- 完成后看到什么：打开入口文档能读到清晰中文和当前真实进度。
- 主要文件：`START_HERE.md`、`PROJECT_CONTEXT.md`、`specs/SDD_SPEC.md`、`specs/IMPLEMENTATION_PLAN.md`、`specs/TASKS.md`
- 依赖：无
- 规格映射：SDD 27、28；计划Phase 0
- 验证：UTF-8读取无乱码；搜索旧状态表述结果为0；不产生生产代码。

### T01 建立前端空项目

- 做什么：建立Next.js、TypeScript、Tailwind的空外壳并锁定依赖。
- 为什么：以后页面、组件和浏览器测试需要统一落点。
- 完成后看到什么：本机能打开一个最简空白页，尚无业务功能。
- 主要文件：`frontend/`自动脚手架、`pnpm-lock.yaml`（机械生成例外，文件数可能超过5）
- 依赖：T00
- 规格映射：计划2.1、7.1、Phase 0
- 验证：`pnpm --dir frontend dev`可启动；`lint`、`typecheck`、`build`均通过。

### T02 建立后端空项目

- 做什么：建立FastAPI、Python 3.12、uv管理的空服务并锁定依赖。
- 为什么：Agent、会话和API需要一个可测试的服务容器。
- 完成后看到什么：本机访问健康检查得到成功响应，尚无选宠逻辑。
- 主要文件：`backend/pyproject.toml`、`backend/uv.lock`、`backend/app/main.py`、`backend/tests/test_health.py`
- 依赖：T00
- 规格映射：计划2.2、7.2、Phase 0
- RED：健康检查测试先因入口不存在而失败。
- GREEN：最小健康检查通过；`ruff`、`mypy`、`pytest`通过。

**检查点 A：** 前后端空项目分别能启动；锁文件存在；没有业务实现。

### T03 固化前端测试工具

- 做什么：配置单元测试、组件测试和浏览器测试入口。
- 为什么：以后每个按钮和流程都要有可重复证据。
- 完成后看到什么：一个示例测试能运行，浏览器测试命令能被识别。
- 主要文件：`frontend/vitest.config.ts`、`frontend/playwright.config.ts`、`frontend/src/test/setup.ts`、`frontend/package.json`
- 依赖：T01
- 规格映射：SDD 23；计划7.1、9
- 验证：`test`和空的`test:e2e`入口通过，不访问外网。

### T04 固化后端测试与Mock安全开关

- 做什么：配置pytest、覆盖率、可控时钟夹具，并让自动测试拒绝真实模型模式。
- 为什么：防止误用DeepSeek产生费用或不稳定结果。
- 完成后看到什么：测试环境固定为Mock；若强行指定DeepSeek，测试会明确失败。
- 主要文件：`backend/pyproject.toml`、`backend/tests/conftest.py`、`backend/tests/test_test_safety.py`、`backend/app/core/config.py`
- 依赖：T02
- 规格映射：SDD 12.3、AC-022；计划8
- RED：安全测试先证明真实模型模式未被拦截。
- GREEN：测试进程检测到真实模型配置时立即失败；Mock配置通过。

### T05 建立环境示例和一键检查入口

- 做什么：添加不含真实秘密的`.env.example`、初始化脚本和总验证脚本。
- 为什么：用户以后只需一个入口判断项目是否健康。
- 完成后看到什么：一条命令依次显示前端、后端和契约检查结果；无Key也能用Mock启动。
- 主要文件：`.env.example`、`.gitignore`、`scripts/bootstrap.ps1`、`scripts/verify.ps1`、`README.md`
- 依赖：T03、T04
- 规格映射：SDD 18、23；计划8、9、Phase 0
- 验证：真实Key不在Git跟踪文件；`scripts/verify.ps1`在当前空项目全绿。

**检查点 B / Phase 0出口：** 两端可启动，格式、类型、测试、构建和总验证实际通过；Mock模式不需要DeepSeek Key。检查结果交给用户确认后才进入第二批。

### Phase 0完成记录（2026-08-04）

- T00：UTF-8入口文档可正常读取，Gate状态已同步。
- T01：Next.js 16.2.12、React 19.2.4、TypeScript 5.9.3和Tailwind CSS 4已锁定；Lint、类型检查、生产构建通过。
- T02 RED：`tests/test_health.py`先因`app`不存在而失败。GREEN：最小`/health`接口通过；Python固定为3.12.13；Ruff与mypy通过。
- 检查点A：前端实际返回HTTP 200；后端实际返回`status=ok`与`service=gulu-port-agent`；验证后服务已关闭。
- T03：Vitest示例1条通过；Playwright测试发现入口通过，当前业务E2E用例为0，符合Phase 0范围。
- T04 RED：安全测试先因`app.core.config`不存在而失败。GREEN：2条安全测试通过；将`MODEL_PROVIDER`设为`deepseek`时，pytest进程按预期立即拒绝运行。
- T05：`scripts/bootstrap.ps1`复现锁定依赖成功；`scripts/verify.ps1`无警告通过前端Lint、类型、测试、构建及后端锁、Ruff、mypy、pytest和覆盖率。
- 已知限制：尚无OpenAPI漂移检查、真实浏览器业务用例、Mock Agent端到端或固定评测；它们分别属于后续未批准阶段。

## 4. 第二批：Phase 1 确定性选宠规则

这一批先实现“不靠大模型也必须正确”的规则。完成后，输入固定条件会得到固定的追问、排除和排序结果。

### T06 定义会话状态和画像字段

- 结果：年龄、住房、过敏、预算、照护时间等字段有明确格式，非法数据会被拒绝。
- 文件：`backend/app/domain/state.py`、`backend/app/domain/profile.py`、`backend/tests/domain/test_state_schema.py`
- 依赖：T05；映射：SDD 8、AC-001；RED/GREEN：Schema失败用例先红，最小模型后通过。

### T07 实现画像增量合并与证据等级

- 结果：区分用户明确说过、Agent推测、待确认和冲突信息；模型不能直接覆盖确认事实。
- 文件：`backend/app/domain/profile_merge.py`、`backend/tests/domain/test_profile_merge.py`、`backend/app/domain/profile.py`
- 依赖：T06；映射：SDD 7、8、AC-001/004；RED/GREEN：覆盖、跳过已知信息和冲突用例。

**检查点 C：** 状态可序列化；重复输入结果一致；确认事实不会被推测覆盖。

### T08 实现阻断条件与硬约束判断

- 结果：明确区分“暂不建议”“排除候选”“需要澄清”，软偏好不能抵消硬风险。
- 文件：`backend/app/domain/constraints.py`、`backend/tests/domain/test_constraints.py`、`backend/app/domain/state.py`
- 依赖：T07；映射：SDD 6、9、AC-005/006/007/014；RED/GREEN：硬约束违规推荐数必须为0。

### T09 实现信息冲突检测

- 结果：住房、家庭成员、过敏等前后矛盾时先澄清，不悄悄任选一个答案。
- 文件：`backend/app/domain/conflicts.py`、`backend/tests/domain/test_conflicts.py`、`backend/app/domain/profile.py`
- 依赖：T07；映射：SDD 9、AC-004/013；RED/GREEN：冲突集合和稳定顺序用例。

**检查点 D：** 阻断、排除、澄清三条路径互不混淆。

### T10 实现动态下一问选择

- 结果：每轮只问一个最有价值的问题，已知字段跳过，相同状态总选同一问。
- 文件：`backend/app/domain/questions.py`、`backend/app/data/question_rules.json`、`backend/tests/domain/test_question_selection.py`
- 依赖：T08、T09；映射：SDD 10、AC-002/003/004；RED/GREEN：不同首答分叉、稳定排序、跳过已知项。

### T11 实现推荐就绪和三种结果状态

- 结果：信息足够才给FINAL；不足时PROVISIONAL；风险过高时NOT_RECOMMENDED。
- 文件：`backend/app/domain/readiness.py`、`backend/tests/domain/test_readiness.py`、`backend/app/domain/state.py`
- 依赖：T10；映射：SDD 11、AC-008/009/010；RED/GREEN：边界表逐项测试。

**检查点 E：** 给定画像能稳定判断继续问、暂定建议、正式建议或暂不建议。

### T12 定义方向、宠物档案和知识格式

- 结果：“品种/类型方向”和“具体虚构宠物”分层，来源、代价、未知项为必填或显式空值。
- 文件：`backend/app/domain/catalog.py`、`backend/app/domain/knowledge.py`、`backend/tests/domain/test_catalog_schema.py`
- 依赖：T06；映射：SDD 12、13、AC-011/012；RED/GREEN：错误混层与缺来源数据先红后绿。

### T13 建立最小测试数据并实现过滤、排序、去分

- 结果：至少12个方向、24个虚构档案；硬过滤后稳定排序；公开结果只有等级，没有数字分。
- 文件：`backend/app/data/directions.json`、`backend/app/data/pets.json`、`backend/app/domain/matching.py`、`backend/tests/domain/test_matching.py`、`backend/tests/domain/test_public_result.py`
- 依赖：T08、T12；映射：SDD 12至14、AC-011至015；RED/GREEN：不匹配样本、并列排序和数字泄漏测试。

**检查点 F / Phase 1出口：** 所有规则测试不调用模型或HTTP；重复运行排序一致；公开序列化中不存在内部数字分。

## 5. 第三批：Phase 2 会话保存与重置

### T14 建立SQLite仓储和迁移

- 结果：会话、成功消息记录和版本号有唯一保存位置。
- 文件：`backend/app/repositories/sqlite.py`、`backend/app/repositories/base.py`、`backend/app/db/migrations/001_init.sql`、`backend/tests/repositories/test_sqlite_repository.py`
- 依赖：T06；映射：SDD 15、18；RED/GREEN：创建、读取、原子提交测试。

### T15 实现24小时滑动过期

- 结果：最近一次成功活动后保存24小时；失败请求不续期；可控时钟无需真实等待。
- 文件：`backend/app/services/session_service.py`、`backend/app/core/clock.py`、`backend/tests/services/test_session_ttl.py`、`backend/app/repositories/sqlite.py`
- 依赖：T14；映射：AC-017/018/024；RED/GREEN：边界前后1秒和失败不续期测试。

**检查点 G：** 时间行为在测试中可瞬间复现，不依赖系统真实等待。

### T16 实现主动重置和过期清除

- 结果：重置立即清除对话载荷；过期会话不能恢复旧画像；保留最少墓碑用于错误语义。
- 文件：`backend/app/services/session_service.py`、`backend/tests/services/test_session_reset.py`、`backend/app/repositories/sqlite.py`
- 依赖：T15；映射：AC-018/019；RED/GREEN：RESET、EXPIRED、重复重置测试。

### T17 实现revision与消息幂等

- 结果：重复发送同一消息只提交一次；旧页面不会覆盖新状态；失败不留下半状态。
- 文件：`backend/app/services/turn_service.py`、`backend/tests/services/test_revision_idempotency.py`、`backend/app/repositories/sqlite.py`、`backend/app/domain/errors.py`
- 依赖：T14；映射：AC-020/021/024；RED/GREEN：并发冲突、重复ID、回滚测试。

**检查点 H / Phase 2出口：** TTL、重置、幂等、冲突和回滚全绿，数据库是唯一会话事实来源。

## 6. 第四批：Phase 3 Mock多轮Agent

### T18 定义模型替换边界和确定性Mock

- 结果：DeepSeek和Mock共享同一输入输出格式；Mock只负责理解和措辞，不负责硬规则。
- 文件：`backend/app/providers/base.py`、`backend/app/providers/mock.py`、`backend/tests/providers/test_provider_contract.py`、`backend/tests/providers/test_mock_determinism.py`
- 依赖：T07；映射：SDD 12.3、AC-022；RED/GREEN：相同输入重复结果完全一致且无网络。

### T19 建立LangGraph显式流程

- 结果：节点和跳转可见；模型输出必须校验后才能合并进状态。
- 文件：`backend/app/agent/graph.py`、`backend/app/agent/nodes.py`、`backend/app/agent/routes.py`、`backend/tests/agent/test_graph_routes.py`
- 依赖：T10、T11、T18；映射：SDD 5、8；RED/GREEN：每个状态只走允许路径。

**检查点 I：** 图只负责编排，确定性规则仍由领域层负责。

### T20 串联提取、合并、冲突和追问

- 结果：自由文本能更新画像；跳过已知项；冲突时优先澄清。
- 文件：`backend/app/agent/nodes.py`、`backend/app/agent/graph.py`、`backend/tests/agent/test_question_flow.py`、`backend/tests/fixtures/dialogues.py`
- 依赖：T19；映射：AC-001至005；RED/GREEN：多分支对话夹具。

### T21 串联检索、双层推荐和风险说明

- 结果：先给方向，再给具体档案；无合适档案时不凑数；同时说明适合点和代价。
- 文件：`backend/app/services/retrieval.py`、`backend/app/agent/nodes.py`、`backend/tests/agent/test_recommendation_flow.py`、`backend/app/data/knowledge.json`
- 依赖：T13、T20；映射：AC-008至015、AC-025/026；RED/GREEN：来源、无结果扩大一次、仍无结果回滚。

**检查点 J：** 推荐事实有来源，方向和个体不混为保证。

### T22 建立5轮以上确定性集成测试

- 结果：至少一条完整流程、一个冲突流程、一个暂不建议流程可重复运行。
- 文件：`backend/tests/integration/test_mock_agent_dialogues.py`、`backend/tests/fixtures/dialogues.py`、`backend/tests/fixtures/expected_results.json`
- 依赖：T20、T21；映射：AC-002至013、AC-022/023/028；验证：连续运行三次结构结果一致。

**检查点 K / Phase 3出口：** Mock Agent端到端稳定，不访问DeepSeek，不读取Key。

## 7. 第五批：Phase 4 API契约

### T23 建立公共错误格式和配置启动检查

- 结果：健康、配置错误和统一错误结构可测试；DeepSeek模式缺Key时明确失败，Mock正常启动。
- 文件：`backend/app/main.py`、`backend/app/api/errors.py`、`backend/app/core/config.py`、`backend/tests/api/test_errors_and_config.py`
- 依赖：T05、T18；映射：SDD 17、18、AC-016/023；RED/GREEN：统一错误字段、缺Key启动失败和Mock正常启动测试。

### T24 实现创建、读取会话API

- 结果：无账户用户可创建会话并在24小时内恢复。
- 文件：`backend/app/api/conversations.py`、`backend/app/api/schemas.py`、`backend/tests/api/test_conversation_create_get.py`、`backend/app/main.py`
- 依赖：T15、T23；映射：AC-016至018；RED/GREEN：成功、过期、不存在状态码。

**检查点 L：** API只返回公共字段，不泄漏内部状态、Prompt或数字分。

### T25 实现发消息、改条件和重新推荐API

- 结果：消息幂等、revision冲突、修改条件、重新推荐都有明确响应。
- 文件：`backend/app/api/conversations.py`、`backend/app/api/schemas.py`、`backend/tests/api/test_turn_and_recommendation.py`、`backend/app/services/turn_service.py`
- 依赖：T17、T22、T24；映射：AC-020/021/028；RED/GREEN：全部成功与错误路径。

### T26 实现重置API和OpenAPI契约快照

- 结果：重置后旧数据不可恢复；API说明可生成前端类型；契约漂移会让检查失败。
- 文件：`backend/tests/api/test_reset.py`、`backend/tests/contracts/test_openapi.py`、`scripts/export-openapi.ps1`、`backend/app/api/conversations.py`
- 依赖：T16、T25；映射：AC-019、SDD 17；验证：OpenAPI中无内部数字分字段。

**检查点 M / Phase 4出口：** Mock模式下创建、对话、修改、推荐、恢复、重置全部API测试通过。

## 8. 第六批：Phase 5 AI选宠页面

### T27 建立视觉规则、首页和最突出入口

- 结果：温暖可信的首页，AI选宠按钮最明显，桌面和手机可用。
- 文件：`frontend/src/app/globals.css`、`frontend/src/app/page.tsx`、`frontend/src/components/home/agent-cta.tsx`、`frontend/src/app/layout.tsx`、`frontend/src/components/home/agent-cta.test.tsx`
- 依赖：T03；映射：SDD 4、20、AC-027；RED/GREEN：主入口可见和键盘可达。

### T28 建立类型安全的API连接与本地会话控制

- 结果：前端类型由OpenAPI生成；浏览器仅保存会话标识和到期信息，不保存Key。
- 文件：`frontend/src/lib/api/generated.ts`、`frontend/src/lib/api/client.ts`、`frontend/src/lib/session.ts`、`frontend/src/lib/session.test.ts`、`scripts/generate-api-types.ps1`
- 依赖：T26；映射：SDD 15、17、AC-016至021；RED/GREEN：会话恢复、过期和前端无Key字段测试。

**检查点 N：** 前后端字段一致；API变化未重新生成类型时检查会失败。

### T29 实现对话、快捷回复和画像摘要

- 结果：一轮只显示一个主要问题；用户能看到已确认、待确认和冲突项。
- 文件：`frontend/src/app/agent/page.tsx`、`frontend/src/components/agent/conversation.tsx`、`frontend/src/components/agent/quick-replies.tsx`、`frontend/src/components/agent/profile-summary.tsx`、`frontend/src/components/agent/conversation.test.tsx`
- 依赖：T28；映射：AC-001至005；RED/GREEN：组件和键盘操作测试。

### T30 实现双层结果卡和风险说明

- 结果：页面显示方向、具体档案、适合原因、代价、不匹配点和来源；绝不显示数字分。
- 文件：`frontend/src/app/agent/results/page.tsx`、`frontend/src/components/agent/direction-card.tsx`、`frontend/src/components/agent/pet-card.tsx`、`frontend/src/components/agent/risk-notes.tsx`、`frontend/src/components/agent/recommendation-results.test.tsx`
- 依赖：T29；映射：AC-008至015；RED/GREEN：数字泄漏、无个体不凑数、来源可见测试。

**检查点 O：** 用户能分清“方向倾向”和“这只虚构宠物的个体观察”。

### T31 实现修改条件、重试、过期和主动重置

- 结果：用户可改答案再推荐；网络/模型失败不丢旧状态；过期和重置有明确提示。
- 文件：`frontend/src/components/agent/session-actions.tsx`、`frontend/src/components/agent/error-feedback.tsx`、`frontend/src/components/agent/expired-dialog.tsx`、`frontend/src/lib/session.ts`、`frontend/src/components/agent/session-actions.test.tsx`
- 依赖：T30；映射：AC-018至021、AC-023/024/028；RED/GREEN：修改后重排、失败保留旧状态、过期和重置反馈测试。

### T32 完成Mock浏览器5轮主流程

- 结果：从首页进入，完成5轮以上动态对话，看到双层建议，再修改条件重新推荐。
- 文件：`frontend/e2e/agent-happy-path.spec.ts`、`frontend/e2e/agent-errors.spec.ts`、必要夹具
- 依赖：T31；映射：验收底线、AC-002/003/028；验证：桌面和移动视口、控制台和网络错误检查。

**检查点 P / Phase 5出口：** Mock全流程稳定后，才允许接真实DeepSeek。

## 9. 第七批：Phase 6 DeepSeek真人演示

### T33 实现DeepSeek适配器

- 结果：JSON Output、关闭thinking、超时、空响应和Schema校验遵守与Mock相同契约。
- 文件：`backend/app/providers/deepseek.py`、`backend/tests/providers/test_deepseek_provider.py`、`backend/app/core/config.py`、`backend/app/providers/base.py`
- 依赖：T18、T32；映射：SDD 12.3、AC-022/023；RED/GREEN：用假的HTTP响应测试，不发真实请求。

### T34 实现一次受控重试和失败回滚

- 结果：无效JSON或空内容最多重试一次；仍失败则不提交状态、不刷新TTL。
- 文件：`backend/app/providers/deepseek.py`、`backend/app/services/turn_service.py`、`backend/tests/integration/test_model_failure_rollback.py`
- 依赖：T33；映射：AC-023/024；RED/GREEN：超时、截断、无效Schema、二次失败测试。

**检查点 Q：** 自动测试仍全部使用Mock或假HTTP，无真实费用。

### T35 进行受控真人演示

- 结果：用户把Key仅放入本机`.env`后，完成至少一条5轮以上真人流程并记录模型、日期、结果和费用观察。
- 文件：本机`.env`（不提交）、`docs/evaluation/live-model-observations.md`、`docs/demo-script.md`
- 依赖：T34；映射：SDD 24、计划Phase 6；验证：先检查Key未被Git跟踪，再人工运行；真人结果不得冒充Mock回归结果。

**检查点 R / Phase 6出口：** 缺Key不影响Mock；有Key真人流程可完成；异常不污染会话。

## 10. 第八批：Phase 7 可点击前端外壳

### T36 建立原型专用数据和统一“暂未开放”反馈

- 结果：原型数据与Agent数据分开；支付、下单、发帖等动作统一提示“Demo演示功能，暂未开放”。
- 文件：`frontend/src/data/prototype.json`、`frontend/src/lib/prototype-store.ts`、`frontend/src/components/demo/demo-unavailable.tsx`、`frontend/src/components/demo/demo-unavailable.test.tsx`
- 依赖：T27；映射：SDD 4、AC-027；RED/GREEN：受限动作统一反馈且不产生成功状态的测试。

### T37 实现宠物市场与用品原型

- 结果：可导航、筛选、搜索、收藏、模拟购物车；没有假交易成功。
- 文件：`frontend/src/app/market/page.tsx`、`frontend/src/app/supplies/page.tsx`、`frontend/src/components/prototype/item-grid.tsx`、`frontend/src/components/prototype/cart-drawer.tsx`、`frontend/e2e/market-supplies.spec.ts`；依赖：T36；映射：AC-027；验证：组件和浏览器测试。

**检查点 S：** 所有明显按钮有反馈，真实与演示能力标签清楚。

### T38 实现社区原型

- 结果：可浏览、点赞、收藏、打开模拟详情；真实发帖明确未开放。
- 文件：`frontend/src/app/community/page.tsx`、`frontend/src/components/community/post-card.tsx`、`frontend/src/components/community/post-dialog.tsx`、`frontend/src/components/community/community-flow.test.tsx`
- 依赖：T36；映射：AC-027；RED/GREEN：浏览、点赞、收藏、详情和发帖受限反馈测试。

### T39 实现会员中心和“我的”原型

- 结果：可切换演示状态；会员开通、真实写入明确未开放；全站导航可达。
- 文件：`frontend/src/app/membership/page.tsx`、`frontend/src/app/me/page.tsx`、`frontend/src/components/layout/site-nav.tsx`、`frontend/src/components/account/demo-account-state.tsx`、`frontend/src/components/account/account-flow.test.tsx`
- 依赖：T36；映射：AC-027；RED/GREEN：路由可达、演示状态切换和会员开通受限测试。

**检查点 T / Phase 7出口：** 全部路由可达、无死按钮、AI选宠仍是首页最突出行动点。

## 11. 第九批：Phase 8 评测、加固与交付说明

### T40 建立至少30类固定评测案例

- 结果：覆盖正常、新手表达模糊、冲突、硬风险、不适合养宠、无个体候选和修改条件等场景。
- 文件：`evaluation/cases.jsonl`、`evaluation/schema.json`、`backend/tests/evaluation/test_dataset.py`
- 依赖：T22；映射：SDD 24、Gate 5指标；验证：案例数量、字段和覆盖标签自动检查。

### T41 建立评测运行器与Bad Case回归

- 结果：自动计算追问正确率、硬约束违规率、数字泄漏率等；每个修复的坏案例留下回归测试。
- 文件：`evaluation/run.py`、`evaluation/metrics.py`、`backend/tests/evaluation/test_metrics.py`、`docs/evaluation/report.md`
- 依赖：T40；映射：SDD 23、24；RED/GREEN：用已知小样本验证指标计算。

**检查点 U：** Mock评测可重复；真人与Mock结果分开标注。

### T42 完成真实浏览器与可访问性检查

- 结果：桌面、手机、导航、响应式、键盘、控制台和网络错误都有检查记录。
- 文件：E2E审计测试、`docs/qa/browser-check.md`、必要的最小修复文件
- 依赖：T35、T39；映射：SDD 20、25；验证：真实浏览器运行记录，修复均补测试。

### T43 补齐架构、决策、README和演示脚本

- 结果：用户能用通俗语言解释为什么先Mock、为什么数字分不展示、为什么SQLite是唯一真相，以及哪些只是原型。
- 文件：`README.md`、`docs/architecture.md`、`docs/decisions.md`、`docs/demo-script.md`、`docs/evaluation/report.md`
- 依赖：T41、T42；映射：SDD 25、计划18；验证：文档链接可解析，图示可渲染，关键术语与真实实现逐项核对。

### T44 执行最终全量验证并提交用户验收

- 结果：总验证全绿；未达指标明确列出，不把“已设计”说成“已测试”或“已部署”。
- 文件：`docs/qa/final-verification.md`及必要的证据索引
- 依赖：T43；映射：SDD 23至26、Gate 5；验证：`scripts/verify.ps1`、Mock E2E、固定评测、构建和静态检查全部通过。

**检查点 V / Phase 8出口：** 形成可展示Demo候选；仍需用户验收，部署和公开仓库另行批准。

## 12. 可执行测试证据规则

为避免“写了测试”却无法复现，实施时按下面的固定命令留证：

### 12.1 后端行为任务

T02、T04、T06至T26、T33、T34、T40、T41的RED命令统一为：

```powershell
Push-Location backend
uv run pytest <该任务列出的测试文件> -q
Pop-Location
```

第一次运行必须因为目标行为尚未实现而失败，并记录失败原因；写最小实现后原命令必须通过。REFACTOR后再运行相关目录，例如：

```powershell
Push-Location backend
uv run pytest tests/domain -q
uv run ruff check .
uv run mypy app tests
Pop-Location
```

如果测试意外一开始就通过，必须先判断行为是否早已存在或测试没有测到目标，不得伪造RED证据。

### 12.2 前端行为任务

T27至T31、T36、T38、T39的RED与GREEN使用：

```powershell
pnpm --dir frontend test -- <该任务的测试文件>
```

对应测试目标固定为：

- T27：`frontend/src/components/home/agent-cta.test.tsx`
- T28：`frontend/src/lib/session.test.ts`
- T29：`frontend/src/components/agent/conversation.test.tsx`
- T30：`frontend/src/components/agent/recommendation-results.test.tsx`
- T31：`frontend/src/components/agent/session-actions.test.tsx`
- T36：`frontend/src/components/demo/demo-unavailable.test.tsx`
- T38：`frontend/src/components/community/community-flow.test.tsx`
- T39：`frontend/src/components/account/account-flow.test.tsx`

T32、T37、T42使用真实浏览器测试：

```powershell
pnpm --dir frontend test:e2e -- <测试文件>
```

- T32：`frontend/e2e/agent-happy-path.spec.ts`和`agent-errors.spec.ts`
- T37：`frontend/e2e/market-supplies.spec.ts`
- T42：`frontend/e2e/accessibility-and-console.spec.ts`

### 12.3 不适用RED的基础任务

以下任务不新增业务行为，可以不制造失败测试，但必须实际验证：

- T00：UTF-8读取和旧状态搜索。
- T01：`lint`、`typecheck`、`build`和本地启动。
- T03：测试工具的示例测试与浏览器测试发现命令。
- T05：`scripts/verify.ps1`全绿，且仓库搜索不到真实Key。
- T35：受控真人演示记录；不进入自动回归。
- T43：链接、图示和术语校对。
- T44：总验证、Mock端到端、固定评测和生产构建全部通过。

### 12.4 每项任务的完整验证

每个任务完成时必须保存五项：RED结果、GREEN结果、REFACTOR结果、触及文件、已知限制。每2至3项到达检查点时执行当时可用的`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`；有红项就停，不带病进入下一组。

## 13. 批准方式与当前下一步

当前只请求批准第一批Phase 0（T00至T05）。批准它不代表批准后续功能批次，也不授权部署、公开仓库或产生外部费用。

用户可用一句话批准：

> 批准第一批任务，开始Phase 0。

收到这句批准后，才会从T00开始，小步实施并在检查点A、B报告真实结果。