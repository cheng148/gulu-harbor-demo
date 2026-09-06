# TASKS.md

## 0. 文档状态

- 项目：咕噜港AI选宠顾问Demo
- 版本：0.3.7
- 创建日期：2026-08-04
- 输入：`specs/SDD_SPEC.md` 0.3.7、`specs/IMPLEMENTATION_PLAN.md` 0.2.2
- 状态：UX-01最终版已批准；T06R至T40和T35B已完成；下一项为T41评测运行器与Bad Case回归
- 当前事实：统一模型契约、确定性Mock、LangGraph显式流程、动态追问、知识检索、双层推荐和风险说明已串联；三类5轮以上Mock对话已稳定复现
- 门禁：T35真人演示与Mock证据已分开记录；Phase 8仍须完成固定评测、浏览器审查、展示材料和最终验证

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
4. 页面和公开API不得出现内部数字分；只显示“很合拍、值得认识、需要磨合”等等级，“暂不合适”不进入正式推荐列表。
5. 硬排除不能被软分抵消；首版只有物种过敏和用户明确说出的绝对底线属于硬排除，其他差距按已批准规则影响等级、排序和解释。
6. 每个检查点的测试、类型检查、构建或静态检查有一项失败，就停止推进。
7. 新发现的业务行为先回写SDD并获批，再写测试和实现。

## 3. 第一批：Phase 0 地基（历史已完成）

这一批只准备可靠的工作环境，已于2026-08-04完成。完成证据见本节末尾；它不代表后续业务规则已经满足当前规格。

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

## 4. 第二批修订：Phase 1 确定性选宠规则

这一批把已经批准的SDD 0.2.6变成“不靠大模型也必须正确”的规则。完成后，同一份用户信息会稳定得到相同的追问、等级、排序和候选结果。

### 4.1 历史完成记录（保留，不作为当前验收结论）

- 旧T06至T11曾按旧规格完成并通过当时的检查点C、D、E；这些测试证明旧实现曾可运行，但不能证明符合当前规则。
- 旧T12至T13曾获准开始，但目录、评分、等级、商家和候选档案随后发生了经用户批准的产品修订，因此不再按旧任务继续。
- 修订采用新编号T06R至T13R-C，避免抹掉历史，也避免把旧测试结果冒充新规格证据。

### 第一小批：状态、合并、底线和调整

#### T06R 对齐Agent状态与用户画像

- 做什么：补齐当前规格需要的画像槽位，以及核心问题数、第4问是否使用、重要未知项、用户已接受调整等状态。
- 为什么：后续追问和推荐必须知道“已经问了什么、什么仍可能改变结果、用户愿意为哪项调整”。
- 完成后看到什么：状态可以明确区分未知、推断、确认、拒答和冲突，非法状态会被测试拒绝。
- 主要文件：`backend/app/domain/profile.py`、`backend/app/domain/state.py`、`backend/tests/domain/test_state_schema.py`
- 依赖：T05；映射：SDD 7、8、AC-001/003/009/016。
- TDD验收：先写缺字段和非法组合的失败测试，再做最小Schema；重复序列化结果一致。

#### T07R 对齐画像合并、中立回答与未知项

- 做什么：让“都可以／没要求”成为已知中立，让没说过的内容保持未知；用户确认的信息不能被模型推测覆盖。
- 为什么：未知按一半权重不等于系统可以假装知道答案。
- 完成后看到什么：每项信息都有来源和状态，用户改口时保留新旧证据并进入可判断的冲突流程。
- 主要文件：`backend/app/domain/profile_merge.py`、`backend/app/domain/profile.py`、`backend/tests/domain/test_profile_merge.py`
- 依赖：T06R；映射：SDD 7、8、AC-001/004/009。
- TDD验收：覆盖中立、未知、拒答、确认覆盖推断、用户主动修改和重复输入。

#### T08R 修正明确底线与硬排除

- 做什么：只把猫狗物种过敏和用户明确说出的绝对底线作为硬排除；住房、预算、独处、活动、掉毛等普通差距不再被系统擅自升级成底线。
- 为什么：这是用户已批准的核心边界；生活差距应影响等级和解释，而不是一律禁止推荐。
- 完成后看到什么：触发过敏或明确底线的候选为“暂不合适”，其他差距继续参与匹配。
- 主要文件：`backend/app/domain/constraints.py`、`backend/app/domain/state.py`、`backend/tests/domain/test_constraints.py`
- 依赖：T07R；映射：SDD 6、8、AC-006/007/014。
- TDD验收：先用回归测试证明旧的自动排除行为不再成立，再实现新的硬规则；软分不能抵消真实硬排除。

#### T09R 对齐冲突和“愿意调整”规则

- 做什么：只澄清会改变推荐的重要冲突；用户明确愿意为某个差距调整时，该项按75%计算并记录成立条件，不追问具体改变计划。
- 为什么：既尊重用户的主观选择，也不能把一句愿意调整误写成所有问题都解决了。
- 完成后看到什么：同一差距可从未解决0%变为已接受调整75%，其他差距和底线保持不变。
- 主要文件：`backend/app/domain/conflicts.py`、`backend/app/domain/profile.py`、`backend/tests/domain/test_conflicts.py`、`backend/tests/domain/test_adjustments.py`
- 依赖：T07R、T08R；映射：SDD 8、10、AC-004/016。
- TDD验收：覆盖重要冲突、无关冲突不追问、单项调整、不得要求证明和不得清除其他差距。

**检查点 C-R：** 新状态、合并、底线和调整测试全部通过；旧的住房／预算等自动硬排除已有反向回归测试；不调用模型或HTTP。

#### 第一小批实施记录（2026-08-09）

- T06R RED：状态测试因`AcceptedAdjustment`不存在而在收集阶段失败；GREEN：补齐新画像槽位、核心问题计数、第4问标记、重要未知和具体调整记录。
- T07R RED：4条新画像合并测试因新槽位不在合并契约而失败；GREEN：已知中立、拒答、冲突双来源和明确修改均通过。
- T08R RED：7条新底线测试全部失败，证明旧代码仍在询问住房并按时间、预算自动排除；GREEN：仅物种过敏与明确绝对底线硬排除，生活差距保留给后续等级判断。
- T09R RED：调整测试因`accept_adjustment`不存在而在收集阶段失败；GREEN：只记录具体差距为75%成立条件，不要求改变计划，也不清除其他冲突。
- 本批验证：目标测试37条通过；Ruff通过；mypy通过；无模型或HTTP调用。
- 当时的完整领域回归为48条通过、5条失败；5条均来自旧T10/T11规则。该历史问题已在下一实施记录中关闭。

### 第二小批：3+1提问、就绪、目录、评分和公开结果

#### T10R 实现温和的“3+1”动态提问

- 做什么：按已知信息选择最多3个核心问题；只有未知答案可能替换当前前两名、改变重要等级或存在关键冲突时，才使用第4个针对性问题；过敏放在正式推荐前轻量确认。
- 为什么：既要收集足够信息，也不能把Agent做成长问卷。
- 完成后看到什么：简单描述不会收到12连问，已知信息会跳过，每轮只出现一个自然、不过度做作的问题。
- 主要文件：`backend/app/domain/questions.py`、`backend/app/data/question_rules.json`、`backend/tests/domain/test_question_selection.py`、`backend/tests/domain/test_question_limit.py`
- 依赖：T09R；映射：SDD 9、AC-002/003/004/005。
- TDD验收：覆盖第4问触发与不触发、已知跳过、过敏最后确认、固定状态固定问题；默认题库不询问住房许可、共同居住人同意和价格。

#### T11R 对齐推荐就绪与暂定结果

- 做什么：根据3+1上限、重要未知和用户“先推荐”的要求，稳定判断继续追问、暂定结果、正式结果或暂不合适。
- 为什么：问题数量本身不是目标，能否可靠判断才是停止提问的依据。
- 完成后看到什么：未知若仍可能改变前两名或重要等级，就标为待确认；不影响结果的未知不会全部展示给用户。
- 主要文件：`backend/app/domain/readiness.py`、`backend/app/domain/state.py`、`backend/tests/domain/test_readiness.py`
- 依赖：T10R；映射：SDD 8、9、AC-003/008/009/010。
- TDD验收：用边界表覆盖提前就绪、第4问后就绪、用户要求先推荐、重要未知和信息充分低于60分。

#### 第二小批前半实施记录（2026-08-09）

- T10R RED：两份问题测试因`QuestionImpact`不存在而在收集阶段失败；GREEN：改为3个核心问题、最多1个针对性问题和推荐前过敏确认，删除住房许可、共同居住者、家庭成员和价格默认提问。
- T10R边界：只有“替换前两名成员”或“改变重要等级”使用第4问；仅前两名互换或备选换位不追加；同一状态稳定选择同一问题。
- T11R RED：10条新就绪测试中8条失败；GREEN：根据核心问题数、结果稳定性、重要未知、第4问使用情况和过敏确认判断继续提问、暂定、正式或暂不合适。
- T11R边界：用户要求先推荐时只展示重要待确认项；住房等主动披露信息不成为推荐门槛；已确认单一物种过敏不阻断另一物种。
- 验证：T10R问题测试15条通过，T11R就绪测试10条通过，完整领域测试69条通过，完整后端测试72条通过，Ruff和mypy通过。
- 项目一键总检查：前端Lint、类型、单元测试、浏览器测试入口、生产构建以及后端依赖锁、Ruff、mypy、72条测试和94%覆盖率全部通过；无DeepSeek或其他网络模型调用。

#### T12R 定义方向、候选宠物、模拟商家和知识格式

- 做什么：建立方向、候选宠物、模拟商家三层格式，并要求数据性质、在售状态、成本等级、观察来源、未知项和平台披露语。
- 为什么：当前Demo连接的是模拟商家与预置模拟在售宠物，不能继续把候选当成模型临时编造的“虚拟角色”。
- 完成后看到什么：缺商家、缺模拟标记、缺来源或使用精确月费用的错误数据会被测试拒绝。
- 主要文件：`backend/app/domain/catalog.py`、`backend/app/domain/knowledge.py`、`backend/tests/domain/test_catalog_schema.py`
- 依赖：T06R；映射：SDD 10、11、AC-011/012/029。
- TDD验收：覆盖错误混层、无效商家关联、`DEMO_SIMULATED`、`SIMULATED_AVAILABLE`、获取与长期养护成本等级及披露语。

#### T13R-A 写入已批准的目录和模拟商家数据

- 做什么：写入8个方向、16只已确认候选宠物和2个模拟商家；每个方向固定2只，每个商家关联8只。
- 为什么：自动测试和DeepSeek都只能引用预置ID，不能临时生成新宠物或新商家。
- 完成后看到什么：目录中恰好包含小麦、栗子、年糕、奶盖、花生、星星、糯米、蓝莓、阿福、豆包、可可、泡芙、土豆、团子、大麦、乌龙。
- 主要文件：`backend/app/data/directions.json`、`backend/app/data/pets.json`、`backend/app/data/merchants.json`、`backend/tests/domain/test_catalog_data.py`
- 依赖：T12R；映射：SDD 11、AC-011/012/029。
- TDD验收：精确数量、名称、方向归属、商家归属、模拟状态、未知字段和披露语全部逐项校验。

#### T13R-B 实现已批准的100分内部评分

- 做什么：实现个人偏好40分、相处感觉30分、日常适配30分；子项使用100%／75%／50%／0%，猫狗方向只限定候选范围、不参与加权。
- 为什么：数字分只用于同等级内部排序，不能替代等级规则或用户底线。
- 完成后看到什么：品种／类型与体型按关联关系计分，互动节奏20分、陪伴距离10分，时间安排5分且为最低权重；未知按一半权重仍保持未知。
- 主要文件：`backend/app/domain/matching.py`、`backend/tests/domain/test_matching.py`、`backend/tests/domain/test_scoring_weights.py`
- 依赖：T08R、T09R、T13R-A；映射：SDD 10、AC-009/014/015/016。
- TDD验收：分项权重合计100；愿意调整只改对应项为75%；品种与体型不重复计分；同输入重复得分一致。

#### T13R-C 实现等级优先、稳定排序和公开去分

- 做什么：先判“很合拍、值得认识、需要磨合、暂不合适”，再在同等级内按内部数字分排序；最多展示4只且同方向最多1只。
- 为什么：高分不能掩盖已确认且未解决的明显差距，备选也可能是“很合拍”。
- 完成后看到什么：正式列表只含前三种等级，前两只只是排序靠前、后两只是备选；每只带适合点、代价／磨合原因、待确认项、模拟商家和平台披露语，绝不显示数字分。
- 主要文件：`backend/app/domain/matching.py`、`backend/tests/domain/test_matching.py`、`backend/tests/domain/test_public_result.py`
- 依赖：T11R、T13R-B；映射：SDD 10、13、14、AC-008至016、AC-029。
- TDD验收：覆盖80／60阈值、关系或生活0%导致需要磨合、低于60暂不合适、等级优先、同级分数排序、同方向去重、最多4只、全部需要磨合时禁用“优先推荐”和公开字段无数字分。

**检查点 F-R / Phase 1修订出口：** T06R至T13R-C全部测试通过；规则不调用模型或HTTP；重复运行结果一致；数据严格为8个方向、16只候选、2个模拟商家；公开结果无内部数字分；旧规则中已被新规格否定的行为都有回归测试。

后续依赖说明：T14以后凡依赖旧T06至T13的任务，必须改为依赖对应的修订任务；任何后续阶段都不得绕过检查点F-R。

## 5. 第三批：Phase 2 会话保存与重置

### T14 建立SQLite仓储和迁移

- 结果：会话、成功消息记录和版本号有唯一保存位置。
- 文件：`backend/app/repositories/sqlite.py`、`backend/app/repositories/base.py`、`backend/app/db/migrations/001_init.sql`、`backend/tests/repositories/test_sqlite_repository.py`
- 依赖：T06R、检查点F-R；映射：SDD 15、18；RED/GREEN：创建、读取、原子提交测试。

### T15 实现24小时滑动过期

- 结果：最近一次成功活动后保存24小时；失败请求不续期；可控时钟无需真实等待。
- 文件：`backend/app/services/session_service.py`、`backend/app/core/clock.py`、`backend/tests/services/test_session_ttl.py`、`backend/app/repositories/sqlite.py`
- 依赖：T14；映射：AC-019/020/024；RED/GREEN：边界前后1秒和失败不续期测试。

**检查点 G：** 时间行为在测试中可瞬间复现，不依赖系统真实等待。

### T16 实现主动重置和过期清除

- 结果：重置立即清除对话载荷；过期会话不能恢复旧画像；保留最少墓碑用于错误语义。
- 文件：`backend/app/services/session_service.py`、`backend/tests/services/test_session_reset.py`、`backend/app/repositories/sqlite.py`
- 依赖：T15；映射：AC-020/021；RED/GREEN：RESET、EXPIRED、重复重置测试。

### T17 实现revision与消息幂等

- 结果：重复发送同一消息只提交一次；旧页面不会覆盖新状态；失败不留下半状态。
- 文件：`backend/app/services/turn_service.py`、`backend/tests/services/test_revision_idempotency.py`、`backend/app/repositories/sqlite.py`、`backend/app/domain/errors.py`
- 依赖：T14；映射：AC-017/018/024；RED/GREEN：并发冲突、重复ID、回滚测试。

**检查点 H / Phase 2出口：** TTL、重置、幂等、冲突和回滚全绿，数据库是唯一会话事实来源。

#### Phase 2实施记录（2026-08-09）

- T14 RED：仓储测试因`app.domain.errors`与SQLite仓储尚不存在而在收集阶段失败；GREEN：完成迁移、创建、读取、按revision原子提交和冲突回滚，3条仓储测试通过。
- T15 RED：TTL测试因可控时钟不存在而在收集阶段失败；GREEN：创建、只读不续期、成功滑动24小时、失败不续期和精确到期边界共5条通过。
- T16 RED：4条重置／过期测试全部失败；GREEN：重置与过期均清除完整载荷并保留最少墓碑，重复重置幂等，新会话不继承旧画像。
- T17 RED：幂等测试因TurnService不存在而在收集阶段失败；GREEN：同一消息ID只提交一次，旧revision拒绝覆盖，失败不留半状态，消息ID按会话隔离。
- 安全边界：SQLite查询全部使用参数绑定；实际数据库路径位于已忽略的`backend/var/`；未增加账户、身份信息或外部服务。
- 验证：后端104条测试、Ruff、mypy全部通过，覆盖率93%；项目一键总检查的前端Lint、类型、单元测试、浏览器测试入口、生产构建和后端全套检查通过；未调用DeepSeek或网络模型。

## 6. 第四批：Phase 3 Mock多轮Agent

### T18 定义模型替换边界和确定性Mock

- 结果：DeepSeek和Mock共享同一输入输出格式；Mock只负责理解和措辞，不负责硬规则。
- 文件：`backend/app/providers/base.py`、`backend/app/providers/mock.py`、`backend/tests/providers/test_provider_contract.py`、`backend/tests/providers/test_mock_determinism.py`
- 依赖：T07R、检查点F-R；映射：SDD 12.3、AC-022；RED/GREEN：相同输入重复结果完全一致且无网络。

### T19 建立LangGraph显式流程

- 结果：节点和跳转可见；模型输出必须校验后才能合并进状态。
- 文件：`backend/app/agent/graph.py`、`backend/app/agent/nodes.py`、`backend/app/agent/routes.py`、`backend/tests/agent/test_graph_routes.py`
- 依赖：T10R、T11R、T18；映射：SDD 5、8；RED/GREEN：每个状态只走允许路径。

**检查点 I：** 图只负责编排，确定性规则仍由领域层负责。

完成证据（2026-08-09）：

- T18 RED：Provider模块不存在，6条契约与确定性测试在收集阶段失败；GREEN：四类模型操作共用严格输入输出Schema，Mock按精确夹具返回，禁止联网、读取DeepSeek Key或无夹具时编造结果。
- T19 RED：Agent流程模块不存在，路由测试在收集阶段失败；GREEN：LangGraph节点与条件边可见，10种会话阶段均有唯一入口路由，画像提取结果必须通过Pydantic校验且消息来源一致后才可交给后续合并。
- 检查点I：LangGraph只负责阶段路由和节点编排；画像合并、冲突、问题选择、硬约束、评分与排序仍在领域层，且本批没有接入T20/T21业务节点。
- 验证：后端123条测试、Ruff、mypy全部通过，覆盖率94%；项目一键总检查全部通过；未调用DeepSeek或其他网络模型。

### T20 串联提取、合并、冲突和追问

- 结果：自由文本能更新画像；跳过已知项；冲突时优先澄清。
- 文件：`backend/app/agent/nodes.py`、`backend/app/agent/graph.py`、`backend/tests/agent/test_question_flow.py`、`backend/tests/fixtures/dialogues.py`
- 依赖：T19；映射：AC-001至005；RED/GREEN：多分支对话夹具。

完成证据（2026-08-10）：

- RED：新增6条流程测试后，先因Provider输出缺少明确修改标记失败；补齐契约后，又因图尚未接收Provider并串联业务节点而失败。
- GREEN：模型只输出结构化画像增量和问题措辞；确定性代码负责Schema校验、画像合并、已确认值保护、明确修改覆盖、含糊冲突标记、冲突优先和3+1问题选择。模型不能把普通偏好擅自升级为硬底线。
- REFACTOR：把提取、校验、合并、约束/冲突检查、选题和措辞拆成可见节点；旧T19测试收窄为单独验证Provider输出校验边界。
- 验证：T20新增6条测试通过；后端全量129条测试、Ruff、mypy通过，覆盖率94%；项目一键总检查全部通过；未调用DeepSeek或其他网络模型。
- T20完成时的限制：当时尚未串联T21推荐流程和T22多轮集成；两项现均已完成并通过后续检查点。

### T21 串联检索、双层推荐和风险说明

- 结果：先给方向，再给具体档案；无合适档案时不凑数；同时说明适合点和代价。
- 文件：`backend/app/services/retrieval.py`、`backend/app/agent/nodes.py`、`backend/tests/agent/test_recommendation_flow.py`、`backend/app/data/knowledge.json`
- 依赖：T13R-C、T20；映射：AC-008至016、AC-025/026/029；RED/GREEN：来源、无结果扩大一次、仍无结果回滚。
- 已确认顺序（2026-08-10）：先独立判断和排序方向，再在每个入选方向内选择具体宠物；不得用单只宠物得分代表整个方向，方向合适但无合适个体时允许只展示方向。

完成证据（2026-08-10）：

- RED：推荐流程测试先因知识缺失错误类型不存在而无法收集；方向测试随后因独立方向匹配函数不存在而失败；流程串联测试又暴露候选节点仍为占位实现。
- GREEN：结构化知识先精确检索，缺失时只扩大一次，仍缺失则整体失败且不改旧状态；方向独立评分排序后，才在入选方向内选择具体宠物；方向可在无合适个体时单独展示；公开结果含来源、适合点、代价、风险、商家模拟状态和平台免责声明，不含内部数字分。
- 验证：T21相关30条测试通过；后端全量136条测试、Ruff、mypy通过，覆盖率94%；前端Lint、类型、单元测试、浏览器测试入口和生产构建通过；未调用DeepSeek或其他网络模型。

**检查点 J（已通过）：** 推荐事实有来源，方向和个体不混为保证。

### T22 建立5轮以上确定性集成测试

- 结果：至少一条完整流程、一个冲突流程、一个暂不建议流程可重复运行。
- 文件：`backend/tests/integration/test_mock_agent_dialogues.py`、`backend/tests/fixtures/dialogues.py`、`backend/tests/fixtures/expected_results.json`
- 依赖：T20、T21；映射：AC-002至013、AC-022/023/028；验证：连续运行三次结构结果一致。

完成证据（2026-08-10）：

- RED：新增集成测试后，先因三类完整对话场景和对话运行器不存在而在收集阶段失败；补齐场景后，固定预期结果文件仍不存在，保留3条预期失败。
- GREEN：建立5轮正常推荐、6轮冲突澄清后推荐、5轮猫过敏后暂不推荐三类固定夹具；每轮只由Mock提供结构化画像增量和问题措辞，LangGraph、画像合并、冲突、选题、知识检索、过滤、评分、排序和双层结果均走真实业务路径。
- REFACTOR：复用既有单轮Provider夹具构造，统一场景ID、轮次ID、消息ID和固定时间；把关键阶段、问题序列、冲突、方向和宠物ID锁入结果快照。
- 验证：T22专项7条测试通过；每个场景在测试内连续运行3次且结构一致；后端全量143条测试、Ruff、mypy通过，覆盖率94%；未调用DeepSeek、未读取真实Key、未访问网络模型。

**检查点 K / Phase 3出口（已通过）：** Mock Agent多轮流程稳定，不访问DeepSeek，不读取Key。

## 7. 第五批：Phase 4 API契约

### T23 建立公共错误格式和配置启动检查

- 结果：健康、配置错误和统一错误结构可测试；DeepSeek模式缺Key时明确失败，Mock正常启动。
- 文件：`backend/app/main.py`、`backend/app/api/errors.py`、`backend/app/core/config.py`、`backend/tests/api/test_errors_and_config.py`
- 依赖：T05、T18；映射：SDD 17、18、AC-016/023；RED/GREEN：统一错误字段、缺Key启动失败和Mock正常启动测试。

#### T23实施记录（2026-08-10）

- RED：新增API测试后，因`app.api`与公共错误模块不存在而在收集阶段失败，确认功能尚未实现。
- GREEN：Mock模式不读取也不要求DeepSeek Key；DeepSeek模式缺Key或提供方名称无效时启动校验明确失败；健康检查使用统一成功结构和请求ID；预期错误、参数错误、未知地址与未分类异常均使用统一错误结构。
- REFACTOR：配置值使用明确Schema，Key使用`SecretStr`保存；服务器内部异常只返回通用提示，不暴露栈、内部路径、模型名或敏感配置。
- 验证：T23专项9条测试通过；后端全量152条测试、Ruff、mypy通过，覆盖率95%；未调用DeepSeek、未访问网络模型、未写入真实Key。

### UX-01 核心手机页面原型审批（非生产代码任务）

- 做什么：提交可直接查看的手机端页面原型，至少覆盖首页、AI对话、画像摘要、推荐前过敏确认、双层推荐结果、修改条件，以及错误／过期／重置反馈。
- 为什么：页面结构会影响T24至T26的公共接口；先确认产品流程，可以避免接口和页面完成后再大幅返工。
- 完成后看到什么：用户可以逐页检查页面结构、功能位置和主要操作流程，并明确批准、要求修改或暂缓；不会看到已实现页面或可运行产品。
- 交付边界：不编写生产代码，不调用DeepSeek，不部署；具体制作工具、是否使用外部平台以及视觉素材来源，在开始UX-01前另行说明并确认。
- 验收标准：核心页面无缺页；3+1提问、过敏确认、双层结果、修改条件和异常恢复都能沿原型走通；真实Agent、Demo模拟数据和暂未开放动作在页面上可区分。
- 依赖：T23；映射：SDD 2.2、20、27；验证：用户逐页批准并记录修改意见。

#### UX-01制作记录（2026-08-11，进行中）

- 用户已批准独立的本地可点击手机端原型，并最终选择“港湾手账”换色前原版。
- 原型使用模拟内容和模拟状态，不连接真实Agent、SQLite、DeepSeek或交易后台，不修改正式frontend生产页面。
- 用户已确认App首页采用发现式布局，并允许展示明确标识的模拟销量、模拟好评和模拟店铺热度；页面级与卡片级都必须标为“Demo虚拟数据”，演示排序不得包装成真实榜单。
- 当前状态仅为已制作并进入验收，不是UX-01已通过；完成后仍需用户逐页确认。

**检查点 UX-A（已通过）：** 2026-08-12用户已批准UX-01最终版。若后续明显改变已批准的页面结构、主要流程或视觉方向，必须再次确认。

### T24 实现创建、读取会话API

- 结果：无账户用户可创建会话并在24小时内恢复。
- 文件：`backend/app/api/conversations.py`、`backend/app/api/schemas.py`、`backend/tests/api/test_conversation_create_get.py`、`backend/app/main.py`
- 依赖：T15、T23、检查点UX-A；映射：AC-016至018；RED/GREEN：成功、过期、不存在状态码。

**检查点 L：** API只返回公共字段，不泄漏内部状态、Prompt或数字分。

**T24完成记录（2026-08-12）：**

- RED：6条接口测试因应用尚不支持会话仓储和时钟注入而失败。
- GREEN：创建、24小时内只读恢复、不存在、整24小时过期、地区参数校验和公共字段边界共6条测试通过。
- REFACTOR：Ruff、mypy和后端全量158条测试通过。
- 触及文件：`backend/app/api/conversations.py`、`backend/app/api/schemas.py`、`backend/tests/api/test_conversation_create_get.py`、`backend/app/main.py`，并同步本记录与接口规格。
- 已知限制：本批未实现发消息、修改画像、重置或前端接入，也未调用DeepSeek；这些分别属于T25、T26和后续前端任务。

### T25 实现发消息、改条件和重新推荐API

- 结果：消息幂等、revision冲突、修改条件、重新推荐都有明确响应。
- 文件：`backend/app/api/conversations.py`、`backend/app/api/schemas.py`、`backend/tests/api/test_turn_and_recommendation.py`、`backend/app/services/turn_service.py`
- 依赖：T17、T22、T24；映射：AC-016至018、AC-024；RED/GREEN：全部成功与错误路径。

**T25完成记录（2026-08-12）：**

- RED：首批12条接口测试因应用入口尚未注入模型Provider而失败；补齐后，旧快捷选项重复提交回归测试暴露校验顺序错误；画像信息不足测试又证明修改后会过早推荐。
- GREEN：发消息、动态追问、同步推荐、消息幂等、旧快捷选项重放、revision冲突、输入与快捷选项校验、画像白名单修改、信息不足继续追问、重新排序、推荐未就绪和会话过期共14条测试通过。
- REFACTOR：Ruff、mypy和后端全量172条测试通过，覆盖率94.28%。
- 触及文件：`backend/app/api/conversations.py`、`backend/app/api/schemas.py`、`backend/app/main.py`、`backend/app/services/turn_service.py`、`backend/tests/api/test_turn_and_recommendation.py`，并同步本记录、项目上下文和接口规格。
- 已知限制：本批没有实现主动重置和OpenAPI契约快照，没有接前端或DeepSeek；这些属于T26及后续获批任务。
### T26 实现重置API和OpenAPI契约快照

- 结果：重置后旧数据不可恢复；API说明可生成前端类型；契约漂移会让检查失败。
- 文件：`backend/tests/api/test_reset.py`、`backend/tests/contracts/test_openapi.py`、`scripts/export-openapi.ps1`、`backend/app/api/conversations.py`
- 依赖：T16、T25；映射：AC-021、SDD 14.6与17；验证：OpenAPI中无内部数字分字段。

**T26完成记录（2026-08-12）：**

- RED：新增8条测试后，重置接口因路由不存在返回405，OpenAPI快照不存在且删除操作未公开，共6条测试按预期失败；已有内部字段防泄漏检查直接通过。
- GREEN：主动重置返回204且无响应体；旧ID不可恢复或继续使用；重复重置保持204；未知会话返回404；过期会话返回410；新会话不继承旧画像。OpenAPI固定快照包含重置契约，并拒绝内部数字分和Agent内部状态字段。
- REFACTOR：OpenAPI由确定性脚本直接以UTF-8生成；根验证脚本在Windows下固定使用项目内pytest临时目录，避免系统临时目录权限导致假失败。
- 验证：T26专项8条测试通过；后端全量180条测试、Ruff、mypy通过，覆盖率94%；前端Lint、类型、单元测试、浏览器测试入口和生产构建通过；检查点M通过。
- 触及文件：`backend/app/api/conversations.py`、`backend/openapi.json`、`backend/tests/api/test_reset.py`、`backend/tests/contracts/test_openapi.py`、`scripts/export-openapi.ps1`、`scripts/verify.ps1`，并同步项目状态与完成记录。
- 已知限制：OpenAPI前端类型将在T28生成；本批未实现Phase 5生产前端、DeepSeek、正式部署或公开仓库。
**检查点 M / Phase 4出口：** Mock模式下创建、对话、修改、推荐、恢复、重置全部API测试通过。

## 8. 第六批：Phase 5 AI选宠页面

### T27 建立视觉规则、首页和最突出入口

- 结果：温暖可信、手机优先的首页；AI选宠按钮最明显，桌面和手机可用，并明确第一版是Web App/PWA。
- 文件：`frontend/src/app/globals.css`、`frontend/src/app/page.tsx`、`frontend/src/components/home/agent-cta.tsx`、`frontend/src/app/layout.tsx`、`frontend/src/components/home/agent-cta.test.tsx`
- 依赖：T03、检查点UX-A；映射：SDD 4、20、AC-027/030；RED/GREEN：主入口可见、键盘可达和移动端布局；实现必须遵守已批准原型，明显变化先确认。

## T27完成记录（2026-08-12）

- Phase 5已获批准；T27首页与视觉基础已按TDD完成并通过验证，下一项T28尚未开始。
- RED：初始Next.js模板不含AI主入口、虚拟数据标记、猫狗／店铺筛选或固定底栏，T27专项4条测试全部失败。
- GREEN：实现港湾手账风发现式首页，复用已确认的咕噜港Logo、港湾插画和4只模拟宠物图片；AI选宠入口最突出；页面与每张相关卡均标记“Demo虚拟数据”，指标使用“模拟销量／模拟好评”。
- 交互：支持中文搜索、猫猫／狗狗／合作店铺筛选；未开放的宠物档案、店铺、社区和我的统一给出Demo提示，不产生成功状态。
- 验证：T27专项4条与前端全量5条测试通过；ESLint、TypeScript和Next.js生产构建通过；真实浏览器验证390×844手机与1280×900桌面均无横向溢出，固定底栏、筛选、搜索、提示和图片加载正常，控制台无错误。
- 已知限制：`/agent`页面与API连接属于T28至T29，本任务只完成首页和视觉基础；未接DeepSeek、未部署、未创建公开仓库。

### T28 建立类型安全的API连接与本地会话控制

- 结果：前端类型由OpenAPI生成；浏览器仅保存会话标识和到期信息，不保存Key。
- 文件：`frontend/src/lib/api/generated.ts`、`frontend/src/lib/api/client.ts`、`frontend/src/lib/session.ts`、`frontend/src/lib/session.test.ts`、`scripts/generate-api-types.ps1`
- 依赖：T26；映射：SDD 15、17、AC-016至021；RED/GREEN：会话恢复、过期和前端无Key字段测试。

## T28完成记录（2026-08-13）

- RED：会话与API客户端共7条专项测试最初因对应模块和生成类型不存在而失败，证明测试确实覆盖本任务新增能力。
- GREEN：从后端OpenAPI快照生成前端类型；新增统一API客户端；浏览器仅保存`conversationId`和`expiresAt`，失效或损坏记录会自动清除；客户端请求不携带DeepSeek Key或授权头。
- REFACTOR：生成脚本同时支持写入和`-Check`漂移检查，并接入总验证脚本；公共错误统一转换为带状态码、错误码、是否可重试和请求ID的前端错误对象。
- 验证：OpenAPI类型漂移检查通过；前端7个测试文件共18条测试、ESLint、TypeScript无增量检查和Next.js生产构建通过；后端OpenAPI契约3条测试通过。
- 触及文件：`frontend/src/lib/api/generated.ts`、`frontend/src/lib/api/client.ts`、`frontend/src/lib/session.ts`及对应测试、`scripts/generate-api-types.ps1`、前端依赖锁和总验证脚本。
- 已知限制：本任务只建立连接基础，不包含T29聊天页面，也未接入DeepSeek、部署或创建公开仓库；生成类型用于开发期字段校验，不替代后续真实响应的运行时验收。

**检查点 N：** 前后端字段一致；API变化未重新生成类型时检查会失败。

### T29 实现对话、快捷回复和画像摘要

- 结果：一轮只显示一个主要问题；用户能看到已确认、待确认和冲突项。
- 文件：`frontend/src/app/agent/page.tsx`、`frontend/src/components/agent/conversation.tsx`、`frontend/src/components/agent/quick-replies.tsx`、`frontend/src/components/agent/profile-summary.tsx`、`frontend/src/components/agent/conversation.test.tsx`
- 依赖：T28；映射：AC-001至005；RED/GREEN：组件和键盘操作测试。

## T29完成记录（2026-08-13）

- RED：新增3条对话组件测试后，首先因聊天组件不存在而在收集阶段失败；组件出现后，测试继续暴露标题语义和多项未知状态的断言边界，修正测试后进入GREEN。
- GREEN：实现`/agent`手机聊天页、单一当前问题、快捷回答、中文自由输入、Enter发送与Shift+Enter换行、问题标题动态变化，以及包含已确认、待确认和冲突项的相处画像。
- REFACTOR：沿用T28统一API客户端与24小时会话引用；默认使用同源`/api`并由Next开发服务器代理到Mock后端，避免浏览器跨域；新增港湾手账风画像人物与猫狗插画。
- 验证：前端8个测试文件共22条测试、ESLint、TypeScript、OpenAPI类型漂移和Next.js生产构建通过；390×844真实浏览器中顶部固定、底栏固定、无横向溢出、中文输入与画像插画正常。
- 已知限制：T29只验收页面与单轮交互组件；当前直接启动后端未装载演示Provider时，真实点击回答会得到明确错误且不丢旧状态。完整5轮Mock浏览器串联属于T32，结果卡、修改条件和重置分别属于T30至T31；未接DeepSeek、未部署。

### T30 实现双层结果卡和风险说明

- 结果：页面显示方向、具体档案、适合原因、代价、不匹配点和来源；绝不显示数字分。
- 文件：`frontend/src/app/agent/results/page.tsx`、`frontend/src/components/agent/direction-card.tsx`、`frontend/src/components/agent/pet-card.tsx`、`frontend/src/components/agent/risk-notes.tsx`、`frontend/src/components/agent/recommendation-results.test.tsx`
- 依赖：T29；映射：AC-008至015；RED/GREEN：数字泄漏、无个体不凑数、来源可见测试。

**检查点 O：** 用户能分清“方向倾向”和“这只虚构宠物的个体观察”。

## T30完成记录（2026-08-13）

- RED：先新增字体与字号3条回归测试，确认全站仍混用两套字体、快捷选项左对齐且问题引导语仅10px；再新增双层结果与会话连接6条测试，确认结果组件和结果页尚不存在。
- GREEN：全站沿用选宠页标题字体；四个快捷选项文字水平与垂直居中；问题引导语提升为正文级。新增`/agent/results`，分别展示品种／类型方向和模拟合作商家的具体候选档案，并包含匹配等级、合拍点、代价、不匹配点、待确认、成本等级、来源、风险与平台边界。
- 边界：页面不显示内部数字分；方向无合适个体时显示“当前Demo暂无合适候选”且不凑数；内部槽位名转换为普通中文；联系商家仍提示Demo未开放；推荐生成后从聊天页自动进入结果页。
- 验证：前端11个测试文件共31条测试、ESLint、TypeScript、OpenAPI类型漂移与Next.js生产构建通过。真实浏览器使用确定性Mock Provider完成聊天、过敏确认、推荐接口和结果页跳转；方向层、个体层、统一底栏均可见，无控制台错误，未调用DeepSeek。
- 视觉：以UX-01批准的“港湾手账”结果页为参考，保留暖纸色、深海军蓝、珊瑚橙、手写感字体和卡片语气；正式实现额外补齐已批准规格要求的方向层。`design-qa.md`最终结论为passed。
- 已知限制：T31修改条件、重试、过期和主动重置，以及T32完整5轮Mock浏览器流程尚未开始；未部署、未创建公开仓库。
### T31 实现修改条件、重试、过期和主动重置

- 结果：用户可改答案再推荐；网络/模型失败不丢旧状态；过期和重置有明确提示。
- 文件：`frontend/src/components/agent/session-actions.tsx`、`frontend/src/components/agent/error-feedback.tsx`、`frontend/src/components/agent/expired-dialog.tsx`、`frontend/src/lib/session.ts`、`frontend/src/components/agent/session-actions.test.tsx`
- 依赖：T30；映射：AC-018至021、AC-023/024/028；RED/GREEN：修改后重排、失败保留旧状态、过期和重置反馈测试。

## T31完成记录（2026-08-14）

- RED：先新增4条会话操作测试，因修改条件与过期提示组件不存在而在收集阶段失败；另补1条本地会话状态测试，确认现有实现不能区分“首次访问”和“旧会话已过期”。
- GREEN：结果页加入“修改条件再看看”，聊天页和结果页加入“重新开始”；修改页只提交用户选中的单项并同步重新推荐，使用与确定性评分规则一致的常用选项；重置前二次确认，成功后清除本地旧会话；过期后明确说明旧信息不再使用并由用户主动新建会话。
- 失败保护：发送消息、读取推荐、修改条件或重置失败时均保留既有对话／推荐和用户本次选择；可重试错误提供“再试一次”，Revision冲突提示刷新后再修改；不会因失败续期或偷偷创建新会话。
- 验证：前端12个测试文件共36条测试、ESLint、TypeScript、OpenAPI类型漂移与Next.js生产构建通过。390×844真实浏览器确认重置按钮、二次确认弹窗、取消操作、底部导航和横向布局正常，控制台无警告或错误；未调用DeepSeek。
- 已知限制：T31只完成前端条件修改和状态反馈；完整5轮Mock浏览器流程、修改后真实重排的端到端证据以及PWA安装边界属于T32，尚未部署或创建公开仓库。
### T32 完成Mock浏览器5轮主流程

- 结果：从首页进入，完成5轮以上动态对话，看到双层建议，再修改条件重新推荐；在支持的手机浏览器中可添加到主屏幕。
- 文件：`frontend/e2e/agent-happy-path.spec.ts`、`frontend/e2e/agent-errors.spec.ts`、必要夹具
- 依赖：T31；映射：验收底线、AC-002/003/028/030；验证：桌面和移动视口、PWA清单与添加主屏幕边界、控制台和网络错误检查。
- 状态：已完成（2026-08-14）。
- RED：先新增真实浏览器用例；初次运行分别暴露缺少浏览器运行文件、过度固定候选数量、失败提示定位不唯一，以及“修改互动节奏不必然改变第一名”等问题。
- GREEN：新增仅用于浏览器Demo的确定性`DemoMockProvider`和独立启动入口；模型替身只从已批准话术生成画像变化并原样保留规则选定的问题，不承载过滤、评分或排序。补充双视口Playwright配置、Web App Manifest、Apple Web App元数据及可配置后端转发地址。
- 验证：手机390×844与桌面1280×900各运行3条真实Chromium用例，共6条通过；覆盖从首页进入、5轮自由文本对话、方向与个体双层推荐、单项条件修改后API返回新推荐、模型失败保留旧会话并原地重试、Manifest可读取。自动化未调用DeepSeek。
- 边界说明：条件修改必须触发重新计算，但明确品种偏好的高权重可能使第一名保持不变，因此验收检查新推荐与变更说明，而不伪造“名次必须变化”。添加主屏幕只保证Manifest和浏览器基础元数据，不承诺离线使用。

**检查点 P / Phase 5出口：** Mock全流程稳定后，才允许接真实DeepSeek。

## 9. 第七批：Phase 6 DeepSeek真人演示

### T33 实现DeepSeek适配器

- 结果：JSON Output、关闭thinking、超时、空响应和Schema校验遵守与Mock相同契约。
- 文件：`backend/app/providers/deepseek.py`、`backend/tests/providers/test_deepseek_provider.py`、`backend/app/core/config.py`、`backend/app/providers/base.py`
- 依赖：T18、T32；映射：SDD 12.3、AC-022/023；RED/GREEN：用假的HTTP响应测试，不发真实请求。

## T33完成记录（2026-08-14）

- RED：先新增DeepSeek Provider测试，首次因`app.providers.deepseek`不存在而在收集阶段失败；配置测试随后证明模型名、接口地址和超时尚未被读取。补充应用装载与HTTPS测试后，又分别证明DeepSeek模式未装载真实Provider且不安全的HTTP地址未被拒绝。
- GREEN：新增DeepSeek适配器，四类模型操作共用T18的严格输入输出Schema；请求使用非流式JSON Output、显式`thinking=disabled`、2048最大输出和默认30秒可配置超时。模型名、HTTPS基础地址、超时和Key均由后端环境配置；Key使用`SecretStr`且错误不回显提供方响应。
- 契约边界：外部响应先校验DeepSeek响应外壳，再拒绝空内容、非正常结束、无效JSON和错误Schema；画像增量必须指回本轮消息，问题措辞不能改变确定性规则选定的`questionId`或快捷选项。T33超时或HTTP失败只返回统一Provider错误，不重试；最多一次受控重试与事务回滚仍留给T34。
- 验证：T33相关32条测试通过；后端全量203条测试、Ruff和mypy通过，整体覆盖率95%，DeepSeek适配器覆盖率100%。全量测试因Windows公共Pytest临时目录权限异常曾在准备阶段报41个错误，改用项目内隔离临时目录后203条原样通过。全部自动化使用`httpx.MockTransport`或既有Mock，不访问DeepSeek、不读取真实Key、不产生费用。
- T33完成时的限制：当时尚未使用用户真实Key运行真人对话，受控重试与失败回滚仍待T34；该缺口现已由下方T34完成记录关闭，T35真人演示仍未开始。

### T34 实现一次受控重试和失败回滚

- 结果：无效JSON或空内容最多重试一次；仍失败则不提交状态、不刷新TTL。
- 文件：`backend/app/providers/deepseek.py`、`backend/app/services/turn_service.py`、`backend/tests/integration/test_model_failure_rollback.py`
- 依赖：T33；映射：AC-023/024；RED/GREEN：超时、截断、无效Schema、二次失败测试。

**T34完成记录（2026-08-14）：**

- RED：先把空内容、截断、无效JSON和错误Schema用例改为必须发生两次假HTTP请求，并增加“第一次无效、第二次有效”的恢复用例；旧实现出现10条失败，证明当时没有重试。
- GREEN：DeepSeek适配器只对`INVALID_OUTPUT`执行一次立即重试，每次模型操作最多两次请求；第二次有效则继续原流程，第二次仍无效则返回`MODEL_INVALID_RESPONSE`。超时和HTTP／鉴权失败不自动重试，避免网络结果不明确时产生重复请求或额外费用。
- 回滚：新增真实SQLite + DeepSeek适配器假HTTP集成测试。连续两次无效响应或超时后，revision、消息、画像、推荐、24小时到期时间和成功幂等记录均保持处理前值；公共API返回可重试错误，原会话快照可继续读取。
- 验证：T34专项20条测试通过；后端全量210条测试、Ruff和mypy通过，覆盖率95%。全量格式检查仍报告26个T34范围外的既有文件未统一格式化，本任务触及的3个Python文件已通过格式检查。
- 费用边界：全部测试使用确定性Mock或`httpx.MockTransport`，不读取真实Key、不访问DeepSeek、不产生费用。
- 已知限制：尚未执行T35真人模型演示；T34不保证网络超时自动恢复，只保证失败不污染会话且用户可以安全重试。

**检查点 Q：** 自动测试仍全部使用Mock或假HTTP，无真实费用。

### T35 进行受控真人演示

- 结果：用户把Key仅放入本机`.env`后，完成至少一条5轮以上真人流程并记录模型、日期、结果和费用观察。
- 文件：本机`.env`（不提交）、`docs/evaluation/live-model-observations.md`、`docs/demo-script.md`
- 依赖：T34；映射：SDD 24、计划Phase 6；验证：先检查Key未被Git跟踪，再人工运行；真人结果不得冒充Mock回归结果。

**T35完成记录（2026-09-05）：**

- 安全准备：用户把Key保存在本机`.env`；Git忽略规则和跟踪状态检查确认`.env`未进入版本库。根据DeepSeek官方资料，API模型名`deepseek-v4-flash`对应用户指定的`DeepSeek-V4-Flash-0731`。
- RED：首次真人流程分别暴露多值槽位返回单个字符串、定性花费误写入数字预算、模型自创非匹配标签和已确认答案返回空值。每个生产修复前均先添加能够复现问题的失败测试。
- GREEN：多值槽位接受单个字符串并规范为单项元组；整数金额槽位拒绝定性文本；DeepSeek提示明确当前匹配标签、定性投入、无底线和无过敏的表达；语义不合格输出进入既有的一次受控重试，不能写入会话。旧测试夹具同步迁移到正式匹配标签，不改变原测试覆盖的业务行为。
- 真人结果：完成5轮自由文本流程并进入`RECOMMENDED`；生成英国短毛猫、成年本地／混种短毛猫、布偶猫和美国短毛猫四个方向，以及年糕、小麦、星星三个具体候选。真实DeepSeek推荐解释和安全复核分别调用成功，安全复核通过。
- 最终通过轮次：11次模型调用，输入14,276 Token（缓存命中6,400、未命中7,876），输出1,163 Token，总计15,439 Token；模型网络等待合计11.366秒。按当时空闲时段官方人民币价格估算约0.017元，实际扣费以DeepSeek控制台为准。此前Bad Case诊断调用未完整保留累计用量，因此不伪造总调试费用。
- 自动验证：新增回归后，后端214条测试、Ruff和mypy全部通过；自动化仍只使用Mock或假HTTP，真人调用只来自受控演示脚本。
- 已知边界：主API真人路径已使用DeepSeek做画像提取和问题措辞，确定性代码负责追问选择、过滤、评分与排序。推荐解释和安全复核本次为脚本中的独立真人调用，尚未接入主API推荐提交路径；最终验收前必须处理或明确保留，不能宣传为已端到端接线。
- 证据：`docs/evaluation/live-model-observations.md`、`docs/demo-script.md`；脱敏原始结果位于被Git忽略的`tmp/t35-live-result.json`。

**检查点 R / Phase 6出口：已通过。** 缺Key不影响Mock；有Key真人流程已完成；异常回滚和安全重试均有证据。

### T35B 将推荐解释与安全复核接入主API

- 结果：用户形成推荐时，确定性代码先锁定方向、宠物、顺序、匹配等级和事实；模型只生成总体说明及逐项说明，安全复核通过后作为`aiNarrative`随推荐保存和返回。
- 兼容：`aiNarrative`为新增可选字段，旧会话缺少该字段仍可读取；原结构化理由、代价、不匹配点和证据继续保留。
- 失败边界：解释与事实数量不一致，或安全复核拒绝且没有完整替换文案时，本轮返回可重试错误并整体回滚；替换文案也不能改变确定性结论。
- 文件：`specs/SDD_SPEC.md`、`backend/app/providers/base.py`、`backend/app/domain/matching.py`、`backend/app/api/conversations.py`、相关API与前端结果测试。
- 依赖：T35；映射：SDD 12、15、24、AC-024/031；RED/GREEN：先证明主API未调用两项模型操作，再以确定性Mock验证通过、拒绝、无效数量和回滚。
- 门禁：自动化不访问DeepSeek、不读取真实Key；本任务完成后才开始T40。

**T35B完成记录（2026-09-06）：**

- RED：主API专项测试先因公共推荐缺少`aiNarrative`失败；结果页组件测试先因没有“选宠搭子帮你捋一捋”区域失败。
- GREEN：主消息与修改条件后的重新推荐都调用同一解释和安全复核服务；公共推荐以向后兼容的可选字段保存总体说明与逐项说明。逐项说明按确定性方向和宠物顺序绑定`subjectId`，模型不能改动既有候选、排序、等级和事实字段。
- 失败保护：解释条数不对应，或安全复核拒绝且没有为每段文字提供完整替换时，返回`MODEL_INVALID_RESPONSE`并整轮回滚；完整安全替换可发布，复核标记保存在公共警告中。
- 验证：后端218条测试通过；T35B相关37条API与DeepSeek假响应测试通过；Ruff、mypy通过。前端16个测试文件52条测试、ESLint、TypeScript、OpenAPI类型漂移和生产构建通过；390×844手机Chromium五轮主流程通过且控制台无错误。全部自动化使用Mock或假HTTP，未调用DeepSeek。
- 真实性边界：T35已证明四类模型操作可分别使用真人DeepSeek；T35B证明主API接线可由同契约Mock稳定运行。接线完成后尚未再次消耗真实额度运行完整真人流程，公开分享网址也尚未更新本次代码。

## 10. 第八批：Phase 7 可点击前端外壳

### T36 建立原型专用数据和统一“暂未开放”反馈

- 结果：原型数据与Agent数据分开；支付、下单、发帖等动作统一提示“Demo演示功能，暂未开放”。
- 文件：`frontend/src/data/prototype.json`、`frontend/src/lib/prototype-store.ts`、`frontend/src/components/demo/demo-unavailable.tsx`、`frontend/src/components/demo/demo-unavailable.test.tsx`
- 依赖：T27；映射：SDD 4、AC-027；RED/GREEN：受限动作统一反馈且不产生成功状态的测试。

**T36完成记录（2026-08-14）：**

- RED：先为独立本地状态和统一受限动作弹窗补测试，首次因模块不存在失败；再为首页与推荐结果的旧提示补回归测试，分别暴露首页临时提示和联系商家`alert`尚未统一。
- GREEN：新增仅供前端原型使用的模拟数据文件和`gulu-harbor.prototype.v1`本地状态；收藏、点赞、模拟购物车与会员演示状态不会写入Agent会话。首页与联系商家等未开放动作统一使用同一弹窗，并明确不会产生真实联系、订单、费用或成功记录。
- 数据边界：首页原有模拟宠物、品种与商家内容移入原型数据文件；文件不得包含Agent内部评分、会话编号或画像结果，也不会反向参与推荐判断。
- 验证：前端14个测试文件共43条测试、ESLint、TypeScript与Next.js生产构建全部通过；未调用DeepSeek、未上传GitHub。

### T37 实现宠物市场与用品原型

- 结果：可导航、筛选、搜索、收藏、模拟购物车；没有假交易成功。
- 文件：`frontend/src/app/market/page.tsx`、`frontend/src/app/supplies/page.tsx`、`frontend/src/components/prototype/item-grid.tsx`、`frontend/src/components/prototype/cart-drawer.tsx`、`frontend/e2e/market-supplies.spec.ts`；依赖：T36；映射：AC-027；验证：组件和浏览器测试。

**T37完成记录（2026-08-14）：**

- 用户确认：宠物市场与宠物用品采用两个独立页面，首页只增加入口；底部四项主导航暂不改变。具体宠物只展示近期浏览，不把独一个体写成有销量或好评；用品可展示明确标注的模拟销量与好评率。
- RED：先新增手机与桌面真实浏览器路径，首次因首页不存在“逛宠物市场”和“看看宠物用品”入口而失败。收藏刷新测试随后暴露服务端初始页面与浏览器本地状态不一致的问题。
- GREEN：新增`/market`和`/supplies`静态页面。市场支持猫狗筛选、名字／品种搜索和本地收藏；用品支持分类筛选、加入本地模拟购物车、查看购物车。模拟结算统一提示暂未开放，不产生订单、支付或成功状态。
- 状态修复：原型本地状态改用浏览器订阅读取，收藏和购物车刷新后可恢复，同时避免React水合不一致和重复渲染警告；仍与Agent会话存储完全分开。
- 验证：390×844手机截图检查无越界或重叠；T37手机／桌面4条浏览器用例通过。前端完整浏览器10条用例、14个测试文件43条测试、ESLint、TypeScript、OpenAPI类型漂移和Next.js生产构建全部通过；未调用DeepSeek、未上传GitHub。
- 手机分享版：经用户单独批准，将同一信息逻辑同步到既有可点击手机原型并发布到原分享网址；分享版18条手机交互测试、4条Sites打包测试及生产构建通过。该发布用于手机检查，不替代T35或最终第一版验收。

**T37用户复查修订（2026-08-14，已批准）：**

- 首页恢复四个“本期热门品种”；首次打开默认进入首页，不再默认进入选宠。
- 宠物市场调整为“4个品种 → 每个品种2只模拟个体 → 个体所在模拟商家”，共8个个体；个体只展示关注指标。
- 空购物车不显示浮栏；加入后在底部导航上方固定显示，并反馈“已加入模拟购物车，本机共有 N 件用品”。
- RED/GREEN范围：先让主前端和手机分享版浏览器用例覆盖以上行为并确认旧实现失败，再做最小修改；两个版本测试、静态检查和构建全部通过后，重新发布到原分享网址。
- 完成证据：主前端14个测试文件43条测试、手机与桌面10条浏览器路径、ESLint、TypeScript和Next.js生产构建通过；手机分享版19条交互测试、4条Sites发布包测试及生产构建通过。
- 发布结果：同一公开网址已更新为Sites版本5；首次发布因平台侧“Completion token has already been consumed”失败，未改代码，使用同一已验证版本重试后成功；线上首页HTTP状态为200。

**检查点 S：** 所有明显按钮有反馈，真实与演示能力标签清楚。

### T38 实现社区原型

- 结果：可浏览、点赞、收藏、打开模拟详情；真实发帖明确未开放。
- 文件：`frontend/src/app/community/page.tsx`、`frontend/src/components/community/post-card.tsx`、`frontend/src/components/community/post-dialog.tsx`、`frontend/src/components/community/community-flow.test.tsx`
- 依赖：T36；映射：AC-027；RED/GREEN：浏览、点赞、收藏、详情和发帖受限反馈测试。

**T38完成记录（2026-08-14）：**

- 恢复处理：先精确删除上一对话未经单项确认创建的6个T38文件，确认T37文件、项目文档和线上分享版均未被该次误操作改变，再从失败测试重新开始。
- RED：先写4条社区行为测试；首次因`/community`页面不存在而失败，证明旧状态尚未实现T38。
- GREEN：新增社区页面和3条虚构改写的Demo帖子，支持本地点赞、收藏、打开/关闭详情；首页与社区底栏可以进入`/community`；“发布动态”统一提示“Demo演示功能，暂未开放”，不产生发布成功状态。
- 验证：主前端15个测试文件47条测试、手机与桌面12条真实浏览器路径、ESLint、TypeScript和Next.js生产构建全部通过；公开分享版新增1条T38端到端回归测试，累计20条手机运行测试与4条站点规则测试通过，正式构建通过，并于2026-08-14发布为Sites版本6。未调用DeepSeek、未上传GitHub。

### T39 实现会员中心和“我的”原型

- 结果：可切换演示状态；会员开通、真实写入明确未开放；全站导航可达。
- 文件：`frontend/src/app/membership/page.tsx`、`frontend/src/app/me/page.tsx`、`frontend/src/components/layout/site-nav.tsx`、`frontend/src/components/account/demo-account-state.tsx`、`frontend/src/components/account/account-flow.test.tsx`
- 依赖：T36；映射：AC-027；RED/GREEN：路由可达、演示状态切换和会员开通受限测试。

**T39完成记录（2026-08-14）：**

- 规格：补充会员中心与“我的”原型边界；月度／年度套餐不展示价格，普通／会员状态只在本机预览，“我的”只汇总本机原型数据。
- RED：先写4条账户与会员组件测试，首次因`/membership`、`/me`和统一导航组件不存在而失败。
- GREEN：新增会员中心、“我的”、会员展示状态组件和统一主导航；首页、选宠、社区、市场、用品及结果页均改用同一可达底栏，真实会员、订单和账户动作继续使用统一未开放提示。
- 验证：主前端16个测试文件51条测试、手机与桌面16条真实浏览器路径、ESLint、TypeScript和Next.js生产构建全部通过；公开分享版累计21条手机运行测试与4条站点规则测试通过，正式构建通过。T39于2026-08-14发布为Sites版本7；随后按用户复查意见提高社区、“我的”与会员页小字号，新增主前端和分享版回归断言并发布为Sites版本8。线上手机视口实测社区正文为11px、辅助文字为10px、“我的”菜单说明与本地提示为10px；“我的”、会员中心和会员展示状态均可达。未调用DeepSeek、尚未上传GitHub。

**检查点 T / Phase 7出口：** 全部路由可达、无死按钮、AI选宠仍是首页最突出行动点。

## 11. 第九批：Phase 8 评测、加固与交付说明

### T40 建立至少30类固定评测案例

- 结果：覆盖正常、新手表达模糊、冲突、硬风险、不适合养宠、无个体候选和修改条件等场景。
- 文件：`evaluation/cases.jsonl`、`evaluation/schema.json`、`backend/tests/evaluation/test_dataset.py`
- 依赖：T22；映射：SDD 24、Gate 5指标；验证：案例数量、字段和覆盖标签自动检查。

**T40完成记录（2026-09-06）：**

- RED：先新增4条数据集契约测试，首次因`evaluation/cases.jsonl`和`evaluation/schema.json`不存在而全部失败。
- GREEN：建立版本为`1.0.0`的固定题库Schema和36条机器可读案例，覆盖正常、新手模糊表达、冲突、硬风险、不适合养宠、无个体候选、修改条件及系统边界8类场景；SDD第22节35项最低覆盖均有可追踪编号。
- 可运行边界：每条案例都拆分为测试步骤与可观察预期，保留用户输入、Mock结构化夹具和结果断言位置，供T41运行器读取；T40本身只验证题库质量，尚未计算Gate 5指标。
- 验证：T40专项4条测试、Ruff及后端全量222条测试通过；全部使用本地数据，不读取DeepSeek Key、不调用模型或其他网络服务。

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

T02、T04、T06R至T13R-C、T14至T26、T33、T34、T40、T41的RED命令统一为：

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

T06R至T17已经完成，检查点H通过。当前本地SQLite数据库是会话唯一事实来源；24小时滑动过期、主动重置、消息幂等、revision冲突和失败回滚均有自动化证据。

验证证据：后端143条测试、Ruff、mypy通过，覆盖率94%；三类5轮以上Mock对话各自连续运行3次且结构一致。验证未调用DeepSeek或其他网络模型。

UX-01最终版已于2026-08-12获批，T24至T26已按TDD完成，Phase 4检查点M通过。T27至T32和Phase 5检查点P均已完成；T33 DeepSeek适配器与T34一次受控重试和失败回滚均已通过假HTTP测试；T35已使用`DeepSeek-V4-Flash-0731`完成5轮受控真人流程，Phase 6检查点R通过；T36至T39及Phase 7检查点T已完成，T39已同步到公开分享版；T40已建立36条固定评测案例并覆盖SDD第22节全部35项场景。当前证据为后端全量222条测试、Ruff和mypy通过；主前端16个测试文件共51条单元／组件测试、16条手机与桌面浏览器测试、Lint、类型、OpenAPI漂移检查与生产构建通过；公开分享版21条手机运行测试和4条站点规则测试通过。自动化未调用DeepSeek或其他网络模型，真人结果单独记录。下一项为T41评测运行器与Bad Case回归，之后仍有浏览器审查、展示材料和最终全量验证；公开GitHub仓库已存在，T35B及T40改动尚未推送，正式部署和外部付费仍需单独批准。
