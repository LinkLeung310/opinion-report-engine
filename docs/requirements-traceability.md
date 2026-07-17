# 任务书需求追踪矩阵

来源：面试方在仓库外提供的开发任务书。原始文件不进入版本控制；本表保存任务书条款摘要，并将每一条约束映射为实现责任与可验证证据。没有证据的事项不视为完成。

本表的“状态”描述需求映射/决策成熟度，不代表代码已经完成。当前实现完成度以 [`current-state.md`](current-state.md) 和最新可复现测试证据为准。

| ID | 任务书要求 | 框架中的落实方式 | 最终验证证据 | 状态 |
|---|---|---|---|---|
| R-01 | `report-config.json` 是唯一输入；未知 `reportType` 按 `csuite` | `ReportConfig` 解析器；标准化后的类型进入执行计划 | 配置单测：未知类型生成 `csuite` 计划 | 已设计 |
| R-02 | 19 个章节按 `sections` 数组顺序渲染 | 本项目定义 19 章注册表；仅解析 enabled ID，并严格保留配置顺序 | 章节规范审查及任意乱序配置测试 | 已决策 |
| R-03 | 输出必须是 `out/{id}` bundle，含 md/pdf/charts/meta | `BundleWriter` 在临时目录完成后原子发布 | CLI 端到端测试检查目录及必需文件 | 已设计 |
| R-04 | `meta.json` 与前端类型对应，包含统计、数量、路径、时间 | 固定主体字段加项目定义的 `generation`、`failures` 和版本信息；摘要字段从用户实际选择章节的可用事实逐项解析，不为缺失 metrics 伪造 0 | JSON schema、任意单章摘要回退和报告列表集成测试 | 已决策 |
| R-05 | 每个启用章节：固定 SQL → 图表 → 一次 LLM 叙述 | 公共 Section 生命周期；SQL 不由 LLM 生成 | Stub 记录每节调用次数；集成测试验证 SQL | 已设计 |
| R-06 | 整份报告 LLM 调用不超过章节数 | 每章一次 narrator 逻辑操作；仅瞬时传输错误可受限重试并记录 attempts | Stub 断言逻辑调用数；适配器测试最多两次传输尝试 | 已实现（fake） |
| R-07 | 所有数字由代码计算且可追溯 | `FactSet` 统一承载数值、格式和查询/计算来源；图表和模板共用它 | 将 markdown 数字与 fixture SQL 结果逐项比对 | 已设计 |
| R-08 | 主要观点来自真实摘要、标题 | `EvidenceSet` 保留文章 ID、标题、摘要和平台；prompt 只接收这些证据 | Stub prompt 测试及证据引用测试 | 已设计 |
| R-09 | SQL 空结果/LLM 超时只影响该章节，章节标注缺失，失败写入 meta | 区分 `no_data` 与 `failed`；固定 SQL 使用短事务，查询错误先回滚再返回章节失败；两者均显示说明，失败写入安全 metadata | 真实 fixture PostgreSQL 故障注入：首章 SQL 失败后，同连接后续章节仍生成，meta 仅记录首章失败 | 已实现 |
| R-10 | `.env` 提供 PG/LLM 全部配置，仓库无真实凭据 | `Settings` 仅读取 `PG_DSN`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`；提交 `.env.example`；CLI 默认真实模式、显式 `--stub-llm` 离线 | 配置读取、缺配置启动错误、安全基址和 CLI narrator 构造集成测试 | 已实现（未做真实 provider 冒烟） |
| R-11 | PDF 跨平台、A4、中文、分页参照 gold report | ReportLab + 项目内 Noto Sans SC 字体；参考 PDF 作为视觉基准 | A4 尺寸断言、字体嵌入、页图视觉检查、跨平台冒烟 | 实现中 |
| R-12 | 图表 150 dpi、指定情感颜色、白底、隐藏上/右框、标题表达洞察 | `ChartTheme` 作为唯一图表入口 | 图表元数据/像素检查和视觉金样检查 | 已设计 |
| R-13 | M1：一条 CLI 命令；csuite 7 章和 pr 11 章中文报告 | 项目创建默认示例配置；Typer 调用同一 `ReportApplicationService` | 两份 examples 配置的完整端到端测试 | 已实现（stub） |
| R-14 | M2：19 章节、三类额外输入、英文、任意组合 | 项目定义 19 章、专属输入和 D-38 英文呈现边界；系统标签完整本地化，真实证据/用户输入/专名保留原文 | 真实 fixture PostgreSQL + stub 的 19 章完整英文、三类专属输入、混合重排、全量 no-data、局部失败、15 图和 A4 bundle 矩阵 | 已实现（stub） |
| R-15 | M3：提交、状态、下载；两个任务互不干扰；重启后成品可下载 | D-41 FastAPI task contract + D-42 有界进程内 manager；每任务独立数据库连接/引擎，原子磁盘状态和 ZIP 下载 | 真实 fixture PostgreSQL + StubNarrator 双并发 API 任务、独立 backend PID、PDF/ZIP、重建 manager 后 completed 查询与字节级下载；完整 pytest 452 项 | 已实现 |
| R-16 | 30 分钟开发环境：fixtures Docker、`.env`、样例 SQL、gold report | 项目创建 Docker fixtures、示例配置、视觉基准和 bootstrap 命令 | 干净环境计时跑通 | 已决策 |
| R-17 | 小步提交；SQL 集成测试；LLM stub；不静默绕过规范 | `main` 稳定、功能分支；测试分层；open-question/PR 假设记录 | Git 历史、测试报告、PR 描述 | 已启用 |
| R-18 | 前端发布、生产部署和数据源切换不在范围 | 核心不写部署逻辑；仅保持 API/Bundle 契约 | 范围审查 | 已设计 |
| R-19 | 最终报告应出现在读取 `index.json` 的既有列表 | `CatalogPublisher` 在 bundle 原子发布后原子更新 index | 真实 fixture CLI 生成后，目录立即包含与 bundle `meta.json` 完全相同的条目；失败注入保护旧目录并保留完整 bundle | 已实现 |

## 已采用的临时判断

- 日期范围使用包含起始日、不包含结束日次日零点的区间，避免漏掉结束日数据。
- 未知章节 ID 是全局配置错误；未知 `reportType` 依任务书回退为 `csuite`。
- 已知章节缺少其专属输入时，只生成该章节的缺失提示。
- 每章节调用一次 narrator；仅短暂传输错误最多重试一次，并记录 attempts。
- 同一 tag/截止日期的重复生成使用带序号的报告 ID，M3 的任务 ID 与报告 ID 分离。
- bundle 发布后由独立 `CatalogPublisher` 原子更新 `index.json`。

## 架构约束补充

- 公共章节之间不能因“依赖”而被自动加入报告。用户配置决定可见章节和顺序。
- 数据复用应通过内部 `AnalysisCache` 或分析块完成，不得改变 `sections` 的可见结果。
- 全局配置错误（例如无法解析的日期）可以拒绝任务；仅某章节缺少专属输入时，必须将该章节标为缺失并继续。
- `index.json`、metadata 扩展、报告 ID 和版本规则由项目的设计决策统一定义。
