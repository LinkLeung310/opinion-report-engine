# Opinion Report Engine — Repository Instructions

本文件是本仓库所有 Codex 工作的长期入口。聊天记忆、历史总结和口头计划都不能替代仓库内文档。每次开始或恢复工作时，先按本文件重建上下文，再修改代码。

## 1. 开工前强制步骤

1. 完整读取本文件。
2. 完整读取任务书：`docs/source/2026-07-11-舆情报告生成模块 — 开发任务书.md`。
3. 读取 `docs/current-state.md`，确认已完成、仅计划和当前禁止扩展的范围。
4. 读取 `docs/README.md`，再按任务选择相关设计文档。
5. 检查 `git status -sb`、当前分支、最近提交和远程同步状态。
6. 修改前把本次工作映射到任务书条款或明确标为项目自主设计。
7. 若文档、代码、数据或当前状态互相冲突，先报告并记录决定；禁止静默绕过。

## 2. 信息优先级

发生冲突时按以下顺序处理：

1. 用户在当前任务中的明确要求；
2. 原始任务书的固定契约和工作约定；
3. 本 `AGENTS.md` 的仓库治理规则；
4. `docs/design-decisions.md` 中已记录的项目决定；
5. `docs/02-report-spec.md` 与 `docs/final-framework.zh-CN.md` 中的项目自主设计；
6. `docs/current-state.md` 中的实现状态；
7. 代码和测试所证明的现状。

`docs/02-report-spec.md`、fixtures、示例配置、19 章细节、报告视觉基准、RAG 和 n8n 都是本项目补充的设计空间，不得描述成面试方已提供或强制指定的内容。原始任务书建议的技术可以在有记录、有测试的情况下替换，但两个固定契约不可改变。

## 3. 任务书固定契约

### 输入

- 唯一公共输入是 `report-config.json`。
- 保留 `reportType`、`language`、`topic`、`dateRange`、`sections` 的字段和语义。
- 未知 `reportType` 回退为 `csuite`。
- 只执行 enabled 章节，并严格保留 `sections` 数组顺序。
- 不得为方便内部实现而改动前端契约或自动插入用户未选择的公共章节。

### 输出

每次成功发布必须形成独立的 `out/{id}/`：

- `report.md`
- `report.pdf`
- `charts/*.png`
- `meta.json`

`meta.json` 必须保留任务书给出的前端字段。项目扩展字段只能是向后兼容的，并在设计决定和测试中说明。发布过程必须避免向用户暴露半成品 bundle。

### 事实、证据和模型边界

- 每个章节遵循固定 SQL → Python 计算 → 图表 → 一次 narrator 操作 → 组装。
- 所有数字由 SQL/Python 计算，并通过 `FactSet` 保留来源；LLM 不计算、不补数字。
- 观点只能来自真实查询得到的标题、摘要等 `EvidenceSet` 内容。
- 一份报告的逻辑 LLM 调用次数不得超过启用章节数。
- 某章节无数据或失败不能中断其他章节；结果必须区分 `no_data` 与 `failed`，安全失败信息写入 metadata。
- 数据库、LLM、PDF、时钟和存储保持可注入，以便确定性测试。

### 配置、安全和视觉

- 运行配置只通过 `PG_DSN`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 注入。
- 永远不提交真实密钥、生产密码、内网地址或本地 `.env`。
- 图表保持白底、150 dpi、隐藏上/右边框，并使用任务书规定的三种情感颜色。
- PDF 必须是跨平台 A4 且中文正常。当前已记录的实现是 ReportLab + 项目内 Noto Sans SC，不得无记录地切回浏览器依赖。

### 里程碑

- M1：CLI；中文 csuite 7 章和 pr 11 章完整默认报告。
- M2：全部 19 章、3 类章节专属输入、英文和任意组合。
- M3：FastAPI 提交/状态/下载、并发任务隔离、重启后成品可下载。
- 上线部署、生产数据切换和前端发布不在当前范围。

不得因为一个纵向切片可运行就宣称 M1、M2 或 M3 已完成。完成度只以 `docs/current-state.md` 和可复现测试证据为准。

## 4. RAG 规则（计划项，不是当前已完成功能）

RAG 不是任务书硬要求，是用于证据密集章节的项目差异化设计。除非用户明确批准相应里程碑，否则只设计边界，不开始实现，也不得在 README、PR 或面试说明中声称已经具备 RAG。

允许的目标形态：

1. 固定、参数化 SQL 先按 tag 和完整日期范围做硬过滤；LLM 不生成 SQL。
2. Python retriever 从候选标题/摘要中选择有限证据，兼顾相关性、情感、平台和观点多样性。
3. embedding、reranker 和检索器必须通过接口注入；自动化测试使用确定性 fake/stub。
4. LLM 只接收批准的 `FactSet` 与带真实文章 ID 的 `EvidenceSet`。
5. 生成观点必须引用允许的 Evidence ID；未知引用、虚构证据或未批准数字导致该章节失败。
6. 真实 embedding/模型只做冒烟验证；检索质量需要固定 fixtures 和可重复评测样例。
7. 优先在 `viewpoints` 等证据密集章节形成一个纵向切片；不要给纯指标章节为了炫技强塞向量检索。

`pgvector` 只是候选方案，不是已决策依赖。引入向量扩展、额外环境变量、chunk 规则或 embedding provider 前，必须新增设计决定并更新追踪矩阵。

RAG 核心属于 Python 引擎，不能搬进 n8n AI 节点来绕过固定 SQL、测试或可追溯边界。

## 5. n8n 规则

n8n 是用户选择的可视化编排和演示层，不是原始任务书要求，也不是报告引擎的运行依赖。

- Python/FastAPI 始终拥有 SQL、事实计算、证据检索、RAG、图表、LLM 调用和 bundle 发布。
- n8n 只负责调用 M3 API、等待、轮询状态以及展示成功/失败路径。
- 仓库中的规范版本是 `n8n/report-generation-orchestrator.json`；本机 UI 不是唯一真相来源。
- 当前工作流在 M3 API 完成前保持 Draft/不激活，不得把 API Error 分支演示成端到端成功。
- n8n 中禁止硬编码 token、API key、密码或 DSN；秘密必须使用 credential system。
- 修改 n8n 前必须使用适用的 n8n skills 和 live node schema，不能凭记忆猜参数。
- 修改后必须先验证工作流，再重新读取并人工检查 `connections`；存在真实副作用时，测试执行前需取得用户确认。
- Code node 是最后手段；优先使用清晰表达式和标准节点。所有 HTTP/API 失败路径必须可见。
- 更新 UI 中的工作流后，同步导出 JSON、运行相关测试并小步提交。

## 6. Git、上传和小步提交

- `main` 必须随时可安装、可运行并保持 CI 绿色。
- 所有修改从最新 `main` 创建 `codex/<scope>` 功能分支。
- 一笔 commit 只表达一个可审查意图；提交信息用 `feat:`、`fix:`、`test:`、`docs:`、`ci:` 等前缀说明结果。
- 小步提交首先是本地 Git commit；只有 push 到 GitHub 后评审者才能看到。
- 推送前运行与风险相称的测试；涉及 SQL 时必须跑真实 fixture PostgreSQL 集成测试，涉及 LLM 时必须跑 stub 测试。
- 推送功能分支后开 Draft PR。PR 必须说明任务书映射、自主决定、当前未完成项和测试证据。
- CI 通过、无已知阻断项并取得用户确认后再合并。默认使用 merge commit 保留小步历史，不擅自 squash。
- 不提交 `.env`、`out/`、`tmp/`、本地数据库、缓存、日志或真实生成凭据。
- 不擅自创建/合并 PR、改变仓库可见性、删除分支或执行其他外部写操作；以用户授权范围为准。

## 7. 测试与完成证据

- SQL：真实 PostgreSQL fixtures 集成测试，不用 mock 代替 SQL 结果。
- LLM/RAG：可注入 stub/fake，断言调用次数、事实输入、Evidence ID 和失败隔离。
- 图表/PDF：断言 150 dpi、规定颜色、A4、中文文本和引用图片存在，并做必要的页图视觉检查。
- CLI：至少运行一条真实命令并检查完整 bundle。
- API：到 M3 时验证并发隔离、状态、下载和重启恢复。
- n8n：JSON 结构、连接、错误路径和 inactive 状态必须可验证。
- 推送前运行 `python -m pip check` 和完整 `pytest`；把实际结果写进 PR，不复制过期数字。

“文件存在”“进程启动”或“测试曾经通过”都不是当前完成证据。必须检查实际产物、健康状态或最新 CI。

## 8. 状态维护和 context recovery

- 每个合并 PR 后更新 `docs/current-state.md`：完成项、计划项、最新证据、已知差异和下一推荐目标。
- 状态文件只描述事实，不创造新需求；新产品决定写入 `docs/design-decisions.md`。
- 新章节在编码前先扩展 `docs/02-report-spec.md`，写明输入、固定 SQL、派生事实、证据、图表、叙述和 no-data 规则。
- 任务书要求与实现证据的映射维护在 `docs/requirements-traceability.md`。
- 即使聊天被压缩或换了新会话，也从第 1 节重新恢复，禁止凭模糊记忆继续。

## 9. 必须暂停并报告的情况

- 需要改变固定输入/输出契约；
- 文档、代码、fixtures 或前端类型不一致；
- 需要新增真实外部凭据、付费调用或有副作用的外部操作；
- 需要扩大到生产部署、生产数据或前端发布；
- 测试失败、CI 非绿色或无法验证 n8n connections；
- 用户的新决定与已记录决定冲突且会显著改变结果。

遇到规范未写清楚但不改变固定契约的细节，可以做最小、可逆判断，并必须在 PR 的“自主决定”中注明。
