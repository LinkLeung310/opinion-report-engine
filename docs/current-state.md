# Current Project State

最后核对日期：2026-07-15  
最后实现基线：`main@9d14725`（PR #7，transparent risk assessment section）

本文件只记录已验证事实。任务要求以原始任务书为准，长期规则以根目录 `AGENTS.md` 为准。

## 已验证完成

- 固定 `ReportConfig` 的严格解析、未知 `reportType` 回退和 enabled 章节顺序规划。
- 19 个章节 ID 注册表；目前 `verdict`、`metrics`、`trend`、`platforms`、`severity` 与 `risk` 六章完成 stub 模式端到端实现。
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
- PR #4 的 trend slice 已用 merge commit 合并：`c35106f`。
- PR #5 的 platforms slice 已用 merge commit 合并：`5dd2c58`。
- PR #6 的 severity slice 已用 merge commit 合并：`01b0cef`。
- PR #7 的 risk slice 已用 merge commit 合并：`9d14725`。
- `main@9d14725` 的 GitHub CI：111 项测试通过。
- 本地真实 CLI 验收得到 12 篇、负面占比 58.3%、失败章节 0 的完整 metrics bundle。
- PR #3 本地真实 CLI 验收得到 `verdict` + `metrics` 2 章 complete、0 章 failed、1 张图表的完整 bundle；`generatedAt` 为 `+08:00`。
- PR #4 本地真实 CLI 验收得到 `verdict` + `metrics` + `trend` 3 章 complete、0 章 failed、2 张图表的完整 bundle；`generatedAt` 为 `+08:00`。
- PR #5 本地真实 CLI 验收得到 `verdict` + `metrics` + `trend` + `platforms` 4 章 complete、0 章 failed、3 张图表的完整 A4 两页 bundle；`generatedAt` 为 `+08:00`。
- PR #6 本地真实 CLI 验收得到前述 4 章 + `severity` 共 5 章 complete、0 章 failed、4 张图表的完整 A4 三页 bundle；`generatedAt` 为 `+08:00`。
- 当前 `codex/m1-risk-section` 本地真实 CLI 验收得到前述 5 章 + `risk` 共 6 章 complete、0 章 failed、5 张图表的完整 A4 四页 bundle；`generatedAt` 为 `+08:00`。
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

context recovery、verdict、trend、platforms、severity 和 risk slice 已经合并。当前分支 `codex/m1-viewpoints-section` 从绿色 `main@9d14725` 创建；下一切片只定义并实现可审计的观点章节，不引入 RAG。用户要求暂不开始 RAG，因此不会新增 embedding、vector store、retriever 或 reranker；n8n 继续保持 Draft/inactive，等待 M3 API。

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
- 新增的评审示例现已演进为 `examples/report-config.m1-slices.json`；README 提供三章节一命令复现路径，示例通过公共 `ReportConfig` 契约解析。
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

- PR #7 已合并，`main@9d14725` 的独立 CI 已通过 111 项测试；当前分支 `codex/m1-viewpoints-section` 已从该绿色基线创建。
- `risk` 纵向切片已经完整合并；下一小步先定义 `viewpoints` 的固定 SQL、真实 EvidenceSet、确定性选择规则、一次 narrator 与 no-data/failed 契约，再开始编码。
- 新分支第一次检查：工作区仅修改本状态文件；merge SHA、PR #7、章节边界与 RAG 延期声明一致，`git diff --check` 通过。
- 新分支第二次检查：健康 fixture PostgreSQL 下完整 pytest 111 项通过；`pip check` 无破损依赖。
- 真实 OpenAI-compatible narrator 只在最后做凭据门控的冒烟验证；开发与 CI 继续使用 stub。
- RAG 继续延期，不在当前 M1 `viewpoints` 阶段实现；n8n 保持 Draft，等待 M3 API。

## M1 `viewpoints` 规格切片

- `docs/02-report-spec.md` 已定义真实标题/摘要证据、每种情感最多两条、第二条优先跨平台的固定选择规则、人口情感占比与代表性样本分离、一次 narrator、引用验证以及 no-data/failed 行为。
- D-23 要求观点样本不得冒充主题流行度；所有观点条目必须显示真实 Evidence ID，并原样保留批准的标题和摘要。
- 本切片是非 RAG 的 M1 确定性基线，不使用 embedding、vector store、reranker 或 n8n；未来若经用户批准引入 D-17 检索器，仍必须保持 EvidenceSet 和引用验证契约。
- fixture 口径预查预计选择负面 `bili-007`/`bili-001`、中性 `bili-008`/`bili-002`、正面 `bili-010`/`bili-006`，同时披露总体情感计数 7/3/2。该预查只校准规格，尚未构成 `viewpoints` 实现证据。
- 规格小步第一次检查：必需规格段、`viewpoints.v1`、一次 narrator、真实 EvidenceSet、代表性样本披露、引用验证、无 RAG/n8n 边界、D-23 和 `git diff --check` 全部通过。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 111 项通过；`pip check` 无破损依赖。

## M1 `trend` 规格切片

- `docs/02-report-spec.md` 已定义完整日历序列、固定查询计划、Python 派生事实、堆叠情感图、一次 narrator 约束和 no-data/failed 行为。
- D-19 记录零文章日期必须保留，避免时间轴压缩造成传播节奏误读。
- 第一次检查（静态规格）：必需规格字段、长范围标签规则和 `git diff --check` 通过。
- 第二次检查（可执行回归）：健康的 fixture PostgreSQL 下完整 pytest 为 64 项通过；`pip check` 无破损依赖。
- 固定 `trend.sql`、`PostgresTrendRepository`、完整日历 `TrendSnapshot` 和可追溯 `FactSet` 已实现。
- SQL/计算小步第一次检查：Python 静态编译、SQL 六个绑定参数和 `git diff --check` 通过。
- SQL/计算小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 70 项通过；`pip check` 无破损依赖。
- fixture 集成测试验证七日文章量 `[2, 2, 2, 3, 1, 1, 1]`、3/20 峰值、25.0% 峰值占比和空话题七个显式零值日。
- `TrendChartBuilder`、fault-isolated `TrendSectionRunner`、确定性中英文 stub 文本、运行时接线和专属图片 alt 已实现。
- 图表/runner 小步第一次检查：Python 静态编译、最多十个日期标签、唯一 narrator 操作和 `git diff --check` 通过。
- 图表/runner 小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 76 项通过；`pip check` 无破损依赖。
- CLI 集成测试验证 `verdict`、`metrics`、`trend` 严格按配置顺序渲染，3 章 complete、0 章 failed，并生成 2 张有效图表。
- 评审入口已统一为 `examples/report-config.m1-slices.json`；README 提供三章节一命令复现路径，配置通过公共 `ReportConfig` 契约解析。
- 真实 fixture PostgreSQL + stub CLI 产物为 12 篇、负面占比 58.3%、3 章 complete、0 章 failed、2 张图表，`generatedAt` 为 Asia/Shanghai `+08:00`。
- PDF 经 Poppler 验证为 A4 两页；两页逐页人工复核无中文乱码、截断、重叠、图例/轴标签异常或内容丢失。第二页保留完整趋势图并因此存在合理留白。
- 分支最终第一次检查：三章节示例契约与中文字段、Python 静态编译、唯一 narrator 操作、旧评审路径清理和 `git diff --check` 全部通过。
- 分支最终第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 76 项通过；`pip check` 无破损依赖。
- 当前 stub 模式纵向切片、真实产物验收、Draft PR、分支 CI、merge commit 和合并后 main CI 均已完成。

## M1 `platforms` 规格切片

- `docs/02-report-spec.md` 已定义平台聚合固定查询、Python 派生占比/并列/集中度事实、最多八行的双面板图、一次 narrator 约束和 no-data/failed 行为。
- D-20 要求披露文章量并列，以负面文章数优先识别负面集中平台，并将图表第八行之后的长尾合并为 `其他`，避免假赢家、小样本比例误导和不可读长尾。
- 本章节只比较结构化聚合事实，明确不使用文章证据、RAG 或 n8n。
- 规格小步第一次检查：必需规格段、`platforms.v1`、一次 narrator、无 RAG 边界、D-20 和 `git diff --check` 全部通过。
- 规格小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 76 项通过；`pip check` 无破损依赖。
- fixture 口径预查确认 4 个平台、文章量 `[4, 4, 3, 1]`；微博与 B站并列量级第一，微博总互动 15,715 且负面文章 3 篇。该预查只校准规格，尚未构成 `platforms` 实现证据。
- 固定 `platforms.sql`、`PostgresPlatformsRepository`、`PlatformRow`、`PlatformsSnapshot`、可追溯 leader/tie `FactSet` 和最多七平台加 `其他` 的确定性 display rows 已实现。
- SQL/计算小步第一次检查：Python 静态编译、恰好三个 SQL 绑定参数、`git diff --check` 以及 platforms 单元/真实数据库专属测试 5 项通过。
- SQL/计算小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 81 项通过；`pip check` 无破损依赖。
- fixture 集成测试正式验证平台顺序 `微博、B站、新闻、知乎`、文章量 `[4, 4, 3, 1]`、负面文章 `[3, 2, 1, 1]`、互动 `[15,715, 6,610, 2,425, 1,420]`，并验证空话题返回空 snapshot。
- `PlatformsChartBuilder`、fault-isolated `PlatformsSectionRunner`、确定性中英文 stub、运行时接线、专属图片 alt 和四章节评审示例已实现。
- 图表/runner 专属检查验证规定情感颜色、互动强调色、150 dpi、最多八行、唯一 narrator 操作、no-data 跳过和 query/chart/LLM 安全失败；相关 13 项测试通过。
- 纵向接线后真实 fixture PostgreSQL 下完整 pytest 为 86 项通过；`pip check` 无破损依赖。
- 真实 CLI 产物为 4 章 complete、0 章 failed、3 张图表；平台正文准确包含并列 4 篇、微博负面集中 42.9%/平台内负面 75.0%、互动 15,715/占比 60.0%，`generatedAt` 为 `+08:00`。
- 首次视觉检查发现方法说明形成 A4 第三页孤页；缩短四平台图表高度后恢复为两页。随后修正图例对数值/标题的遮挡，最终 Poppler 页图逐页复核无孤页、乱码、截断、重叠或数据标签遮挡。
- 分支最终第一次检查：四章节示例契约、Python 静态编译、唯一 platforms narrator 操作、过期状态清理和 `git diff --check` 全部通过。
- 分支最终第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 86 项通过；`pip check` 无破损依赖。
- 当前完整 `platforms` stub 纵向切片已接通；真实 narrator、RAG、n8n 和其余 M1 章节仍未实现。

## M1 `severity` 规格切片

- `docs/02-report-spec.md` 已定义仅针对负面内容的固定查询、严重性/1–5 分数事实、真实高风险证据、双面板图、一次 narrator 和 no-data/failed 行为。
- D-21 将“零负面内容”定义为有效 no-data 结论，并规定最多三条证据按 severity、negative score、互动、时间和 ID 确定性排序，不使用 RAG。
- EvidenceSet 必须保留真实 external ID、标题、摘要、平台、时间和 sentiment；任何文章级叙述必须显示允许的 Evidence ID，未知引用或无来源解释使章节失败。
- 规格小步第一次检查：必需规格段、`severity.v1`、一次 narrator、真实证据/非 RAG 边界、D-21 和 `git diff --check` 全部通过。
- 规格小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 为 86 项通过；`pip check` 无破损依赖。
- fixture 口径预查确认 7 篇负面内容，低/中/高/危为 `[1, 2, 3, 1]`，负面分数 1–5 为 `[0, 2, 1, 3, 1]`。该预查只校准规格，尚未构成 `severity` 实现证据。
- 固定 `severity.sql`、`PostgresSeverityRepository`、`SeveritySnapshot`、可追溯 `FactSet` 和真实字段 `EvidenceSet` 已实现；空负面范围返回合法空 snapshot。
- 查询在 tag/完整日期硬过滤后仅保留负面记录，一次返回聚合及最多三条证据；证据按 D-21 的 severity、分数、互动、时间、ID 顺序确定性排名，不使用 RAG。
- SQL/计算小步第一次检查：Python 静态编译、恰好三个 SQL 绑定参数、`git diff --check` 以及 severity 单元测试 4 项通过。
- SQL/计算小步第二次检查：真实 fixture PostgreSQL 下 severity 专属集成测试 2 项通过、完整 pytest 92 项通过；`pip check` 无破损依赖。首次完整测试因沙箱无权访问系统临时目录产生 15 个 setup error，改用仓库内已忽略的 `tmp/` 后原范围全部通过，没有业务断言失败。
- fixture 集成测试正式验证 7 篇负面、低/中/高/危 `[1, 2, 3, 1]`、分数 1–5 `[0, 2, 1, 3, 1]`、负面总互动 20,620、高/危互动 16,115，以及证据顺序 `bili-007`、`bili-005`、`bili-003`。
- facts 保留未四舍五入的 PostgreSQL 平均分并仅显示为 3.4；高/危占比显示为 57.1%，高/危互动占比显示为 78.2%，证据事实保留三个真实 source record ID。
- `SeverityChartBuilder`、fault-isolated `SeveritySectionRunner`、确定性中英文 stub、运行时接线、专属图片 alt 和五章节评审示例已实现。
- narrator 每章只调用一次；runner 将三个真实 Evidence ID 与原始标题/摘要交给 narrator，并校验输出按批准顺序显示全部 ID 和原始证据文本。未知引用或篡改证据使本章安全进入 `failed`，不暴露模型错误内容。
- 图表/runner 专属检查验证绿色到红色风险色阶、critical 固定负面红、150 dpi、洞察标题、no-data 跳过、Evidence ID 校验以及 query/calculation/chart/LLM 安全失败；相关 severity 测试 10 项通过。
- 纵向接线后真实 fixture PostgreSQL 下完整 pytest 为 98 项通过；`pip check` 无破损依赖。
- 真实 CLI 产物为 5 章 complete、0 章 failed、4 张图表；severity 正文准确包含 7 篇负面、高/危 4 篇/57.1%、平均分 3.4、高/危互动占比 78.2%，并显示 `bili-007`、`bili-005`、`bili-003` 三个 Evidence ID；`generatedAt` 为 `+08:00`。
- PDF 经 Poppler 验证为 A4 三页；第三页完整承载 severity 文字、三条证据、双面板图和方法说明，不是孤页。逐页人工复核及图表原图检查均未发现中文乱码、截断、重叠、标签遮挡或风险色阶错误。

## M1 `risk` 规格切片

- `docs/02-report-spec.md` 已定义五个结构化风险压力信号、固定聚合查询、透明等权指数、分档阈值、五条横向图、一次 narrator 和 no-data/failed 行为。
- D-22 将综合结果明确为非概率的诊断信号指数；五项信号等权是因为合成 fixture 没有可用于校准权重的结果标签。
- 当前 schema 没有高管关联或谣言核验字段。规格要求显式披露并排除这两个维度，禁止从标题/摘要关键词、外部知识或模型推断中猜测。
- 本章节只使用结构化聚合事实，不使用文章证据、RAG 或 n8n。
- fixture 口径预查确认 12 篇内容、7 篇负面、4 篇高/危、4 个平台均出现负面、7 个日历日中 6 日出现负面、总互动 26,170、负面互动 20,620。五项压力显示为 58.3%、57.1%、100.0%、85.7%、78.8%，等权指数显示为 76.0%。该预查只校准规格，尚未构成 `risk` 实现证据。
- 规格小步第一次检查：必需规格段、`risk.v1`、一次 narrator、零负面 complete 分支、非概率披露、schema 缺口、无 RAG 边界、D-22 和 `git diff --check` 全部通过。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 为 98 项通过；`pip check` 无破损依赖。
- 固定 `risk.sql`、`PostgresRiskRepository`、`RiskSnapshot`、五个 `RiskSignal` 和可追溯 `FactSet` 已实现；空范围返回合法空 snapshot，非空但零负面范围返回五项明确零压力事实。
- SQL/计算小步第一次检查：Python 静态编译、恰好四个 SQL 绑定参数、`git diff --check` 以及 risk 单元测试 5 项通过。
- SQL/计算小步第二次检查：真实 fixture PostgreSQL 下 risk 专属集成测试 2 项通过、完整 pytest 105 项通过；`pip check` 无破损依赖。
- fixture 集成测试正式验证 12 篇内容、7 篇负面、4 篇高/危、4/4 个平台、6/7 个负面活跃日、总互动 26,170 和负面互动 20,620；空话题返回空 snapshot。
- FactSet 保留五项未四舍五入比率并仅显示为 58.3%、57.1%、100.0%、85.7%、78.8%；等权指数显示 76.0%，3 项高位、2 项中位、0 项低位，并携带非概率方法和 `高管关联、谣言核验` 不可评估披露。
- `RiskChartBuilder`、fault-isolated `RiskSectionRunner`、确定性中英文 stub、运行时接线、专属图片 alt 和六章节评审示例已实现；本章节不向 narrator 传入文章证据。
- risk 专属 11 项测试验证 150 dpi、绿/橙/红分档色、一次 narrator、非概率披露、schema 能力边界、零文章 no-data、非空零负面 complete，以及 query/calculation/chart/LLM 的安全失败隔离。
- 纵向接线后真实 fixture PostgreSQL 下完整 pytest 111 项通过；`pip check` 无破损依赖。
- 真实 CLI 产物为 6 章 complete、0 章 failed、5 张图表；risk 正文准确显示五项信号、76.0% 高位诊断指数、非概率说明以及高管关联/谣言核验未纳入的 schema 边界。
- PDF 经 Poppler 验证为 A4 四页；第三页承载 severity 图表与 risk 正文，第四页完整承载风险信号图和方法说明。逐页人工复核及图表原图检查未发现中文乱码、截断、重叠、标签遮挡或 100% 标签裁切。
- 图表/runner 小步第一次检查：Python 静态编译、配置契约、唯一 narrator 操作和 `git diff --check` 通过。
- 图表/runner 小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 111 项通过；`pip check` 无破损依赖。
