# Current Project State

最后核对日期：2026-07-15  
最后实现基线：`main@8c2381d`（PR #3，auditable executive verdict section）

本文件只记录已验证事实。任务要求以原始任务书为准，长期规则以根目录 `AGENTS.md` 为准。

## 已验证完成

- 固定 `ReportConfig` 的严格解析、未知 `reportType` 回退和 enabled 章节顺序规划。
- 19 个章节 ID 注册表；目前 `verdict` 与 `metrics` 两章完成 stub 模式端到端实现。
- 项目提供的合成 PostgreSQL fixtures、固定 metrics SQL 和真实数据库集成测试。
- `FactSet`、章节级 `complete` / `no_data` / `failed` 语义及安全失败 metadata。
- metrics 的 150 dpi 图表、项目内 Noto Sans SC 字体和 A4 ReportLab PDF。
- 原子发布 `report.md`、`report.pdf`、`charts/*.png`、`meta.json` bundle。
- `report generate` CLI 的显式 `--stub-llm` 离线验证路径。
- GitHub Actions 在 Python 3.12 + PostgreSQL fixtures 上运行完整测试。
- n8n Draft 工作流 JSON：提交 M3 API、等待、轮询和成功/失败分支；未激活。
- 仓库级 context recovery：`AGENTS.md`、文档导航、状态快照和 PR 模板。

## 当前证据

- PR #1 的 metrics slice 已用 merge commit 合并：`0f514d1`。
- PR #2 的仓库治理已用 merge commit 合并：`286e6dc`。
- PR #3 的 verdict slice 已用 merge commit 合并：`8c2381d`。
- `main@8c2381d` 的 GitHub CI：64 项测试通过。
- 本地真实 CLI 验收得到 12 篇、负面占比 58.3%、失败章节 0 的完整 metrics bundle。
- PR #3 本地真实 CLI 验收得到 `verdict` + `metrics` 2 章 complete、0 章 failed、1 张图表的完整 bundle；`generatedAt` 为 `+08:00`。
- wheel 已确认包含 CLI、PDF renderer 和中文字体。

测试数量会随实现增长；恢复工作时必须重新运行并记录最新结果，不得把 47 当成永久常量。

## 明确未完成

- M1 未完成：尚未实现中文 csuite 7 章与 pr 11 章默认报告。
- M2 未开始：其余章节、3 类章节专属输入的完整行为、英文和任意组合未完成。
- 真实 OpenAI-compatible narrator 未实现；真实模型未做冒烟验证。
- RAG 未实现：没有 embedding、vector store、retriever、reranker 或引用验证。只在 `AGENTS.md` 和 D-17 中定义计划边界。
- M3 未开始：FastAPI、任务队列、并发隔离、状态和下载接口均不存在。
- n8n 不能端到端运行，因为其调用的 M3 API 尚不存在；不得激活或声称集成完成。
- `CatalogPublisher` / `index.json` 列表更新尚未实现。
- gold-report 视觉资产和完整默认配置尚未交付。

## 已知文档差异

- 任务书描述 fixtures 为真实历史话题数据，但仓库没有收到可发布的原始 fixtures；本项目根据 D-15 提供合成、确定性数据。对外必须明确“合成 fixture”，不得称为真实历史记录。
- 任务书引用的 `docs/02-report-spec.md` 和 gold-report HTML/CSS 没有作为原始附件进入当前仓库；section spec 由本项目逐步定义。用户另行提供的参考 PDF 用于视觉理解，但仓库内 gold-report 资产仍待交付。
- 任务书建议 Playwright/WeasyPrint；当前根据 D-16 使用 ReportLab + 内嵌字体，并已记录和测试该偏离。

## 当前范围约束

context recovery 和 verdict slice 已经合并。当前分支 `codex/m1-trend-section` 只定义 M1 `trend` 章节规格；尚未新增 trend SQL、Python、图表或 runner。用户要求暂不开始 RAG，因此本阶段没有新增 embedding、vector store、retriever 或 n8n 节点。

## 治理切片验证

- 第一次检查（静态一致性）：`git diff --check` 通过；README、AGENTS、状态文件和文档导航中的本地 Markdown 链接全部可解析；工作区只包含预期治理文件。
- 第二次检查（可执行回归）：真实 fixture PostgreSQL 环境下完整 pytest 为 47 项通过；`python -m pip check` 无破损依赖。
- 小步提交：context recovery 入口、RAG/fixture 边界和 PR 证据模板分别提交，没有混入 RAG 实现或 n8n 节点修改。

以后每个小步必须在本文件记录本次结果，并重新执行与该小步相称的两轮检查；历史结果不能替代当前验证。

## M1 `verdict` 规格切片

- `docs/02-report-spec.md` 已写明输入、固定查询计划、Python 派生事实、证据边界、图表决定、一次 narrator 约束和 no-data/failed 行为。
- D-18 记录透明风险/走势阈值由 Python 计算，并解释不生成重复装饰图表的决定。
- 第一次检查（静态规格）：必需规格字段、`verdict.v1` 查询标识和 narrator 次数约束检查通过；`git diff --check` 通过。
- 第二次检查（可执行回归）：健康的 fixture PostgreSQL 下完整 pytest 为 47 项通过；项目虚拟环境 `pip check` 无破损依赖。
- 固定 `verdict.sql`、`PostgresVerdictRepository`、`VerdictSnapshot`、可追溯 `FactSet` 和透明风险/走势规则已实现。
- SQL/计算小步第一次检查：Python 静态编译、SQL 五个绑定参数和 `git diff --check` 通过。
- SQL/计算小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 58 项通过；`pip check` 无破损依赖。
- fault-isolated `VerdictSectionRunner`、确定性中英文 stub 文本和运行时接线已实现；`verdict` 不产生重复图表。
- runner 小步第一次检查：Python 静态编译、唯一 narrator 操作和 `git diff --check` 通过。
- runner 小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 64 项通过；`pip check` 无破损依赖。
- CLI 集成测试验证 `verdict`、`metrics` 严格按配置顺序渲染，2 章 complete、0 章 failed，并只统计 metrics 的 1 张有效图表。
- 新增 `examples/report-config.verdict-metrics.json` 和 README 一命令复现路径；示例配置通过公共 `ReportConfig` 契约解析。
- 实际 CLI 产物的 `meta.json` 为 12 篇、负面占比 58.3%、2 章 complete、0 章 failed，并按 D-14 修正为 Asia/Shanghai `+08:00` 生成时间。
- PDF 通过 Poppler 检查为 A4 单页；最新页图人工复核无中文乱码、截断、重叠或图表颜色异常。
- 分支最终第一次检查：示例配置契约、Python 静态编译和 `git diff --check` 通过。
- 分支最终第二次检查：健康的 fixture PostgreSQL 下完整 pytest 为 64 项通过；`pip check` 无破损依赖。
- `verdict` 的 stub 模式纵向切片已接通；真实 narrator 仍未实现，M1 默认 7/11 章仍未完成。

## 恢复清单

1. 读取根目录 `AGENTS.md`。
2. 读取原始任务书、本文件、需求追踪矩阵和设计决定。
3. 检查 Git 分支、工作区、远程和最新 CI。
4. 重新运行与下一目标相关的测试。
5. 向用户报告已完成、未完成和任何冲突，再开始修改。

## 当前阶段与下一步

- 当前分支先小步提交 `trend` 规格；下一小步依据规格实现完整日期序列 SQL、确定性 Python 事实和真实 fixture 集成测试。
- 真实 OpenAI-compatible narrator 只在最后做凭据门控的冒烟验证；开发与 CI 继续使用 stub。
- RAG 继续延期，不在当前 M1 `trend` 阶段实现；n8n 保持 Draft，等待 M3 API。

## M1 `trend` 规格切片

- `docs/02-report-spec.md` 已定义完整日历序列、固定查询计划、Python 派生事实、堆叠情感图、一次 narrator 约束和 no-data/failed 行为。
- D-19 记录零文章日期必须保留，避免时间轴压缩造成传播节奏误读。
- 第一次检查（静态规格）：必需规格字段、长范围标签规则和 `git diff --check` 通过。
- 第二次检查（可执行回归）：健康的 fixture PostgreSQL 下完整 pytest 为 64 项通过；`pip check` 无破损依赖。
- 当前只完成规格；`trend.sql`、Python snapshot、图表 builder、runner 和测试仍未实现。
