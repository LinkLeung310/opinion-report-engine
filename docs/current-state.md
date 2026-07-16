# Current Project State

最后核对日期：2026-07-16
最后实现基线：`main@eeeba95`（PR #20，auditable business impact）

本文件只记录已验证事实。任务要求以原始任务书为准，长期规则以根目录 `AGENTS.md` 为准。

## 已验证完成

- 固定 `ReportConfig` 的严格解析、未知 `reportType` 回退和 enabled 章节顺序规划。
- 19 个章节 ID 注册表；中文 csuite 的 `verdict`、`metrics`、`trend`、`viewpoints`、`platforms`、`severity` 与 `risk` 七章，PR 版新增的 `sentiment-evolution`、`keywords`、`engagement`、`media-social`，M2 的 `timeline`、`top-content`、`negative-themes`、`spread-path`、`response`、`benchmark`、`biz-impact` 与当前分支的 `recommendations` 已完成 stub 模式端到端实现。
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
- PR #8 的 viewpoints slice 已用 merge commit 合并：`7ca8f00`。
- PR #9 的 sentiment-evolution slice 已用 merge commit 合并：`13663e3`。
- PR #10 的 keywords slice 已用 merge commit 合并：`1ee06f4`。
- PR #11 的 engagement slice 已用 merge commit 合并：`9e157c5`。
- PR #12 的 media-social slice 已用 merge commit 合并：`3448aa3`。
- PR #13 的 M1 标准默认配置已用 merge commit 合并：`93f7d16`。
- PR #14 的 timeline slice 已用 merge commit 合并：`26814cf`。
- PR #15 的 top-content slice 已用 merge commit 合并：`9b5046d`。
- PR #16 的 negative-themes slice 已用 merge commit 合并：`d5d2120`。
- PR #17 的 spread-path slice 已用 merge commit 合并：`1a047b4`。
- PR #18 的 response slice 已用 merge commit 合并：`ad1e414`。
- PR #19 的 benchmark slice 已用 merge commit 合并：`542196c`。
- PR #20 的 biz-impact slice 已用 merge commit 合并：`eeeba95`。
- `main@1ee06f4` 的 GitHub CI：146 项测试通过（run `29420845303`）。
- `main@9e157c5` 的 GitHub CI：160 项测试通过（run `29423229549`）。
- `main@3448aa3` 的 GitHub CI：175 项测试通过（run `29424655431`）。
- `main@93f7d16` 的 GitHub CI：180 项测试通过（run `29425308622`）。
- `main@26814cf` 的 GitHub CI：196 项测试通过（run `29471052154`）。
- `main@9b5046d` 的 GitHub CI：211 项测试通过（run `29472151204`）。
- `main@d5d2120` 的 GitHub CI：227 项测试通过（run `29473309498`）。
- `main@1a047b4` 的 GitHub CI：243 项测试通过（run `29474436518`）。
- `main@ad1e414` 的 GitHub CI：274 项测试通过（run `29475994557`）。
- `main@542196c` 的 GitHub CI：289 项测试通过（run `29477030341`）。
- `main@eeeba95` 的 GitHub CI：317 项测试通过（run `29499194452`）。
- 本地真实 CLI 验收得到 12 篇、负面占比 58.3%、失败章节 0 的完整 metrics bundle。
- PR #3 本地真实 CLI 验收得到 `verdict` + `metrics` 2 章 complete、0 章 failed、1 张图表的完整 bundle；`generatedAt` 为 `+08:00`。
- PR #4 本地真实 CLI 验收得到 `verdict` + `metrics` + `trend` 3 章 complete、0 章 failed、2 张图表的完整 bundle；`generatedAt` 为 `+08:00`。
- PR #5 本地真实 CLI 验收得到 `verdict` + `metrics` + `trend` + `platforms` 4 章 complete、0 章 failed、3 张图表的完整 A4 两页 bundle；`generatedAt` 为 `+08:00`。
- PR #6 本地真实 CLI 验收得到前述 4 章 + `severity` 共 5 章 complete、0 章 failed、4 张图表的完整 A4 三页 bundle；`generatedAt` 为 `+08:00`。
- PR #7 本地真实 CLI 验收得到前述 5 章 + `risk` 共 6 章 complete、0 章 failed、5 张图表的完整 A4 四页 bundle；`generatedAt` 为 `+08:00`。
- PR #8 本地真实 CLI 验收得到完整 csuite 7 章 complete、0 章 failed、5 张图表的 A4 四页 bundle；`generatedAt` 为 `+08:00`。
- PR #9 本地真实 CLI 验收得到 csuite 7 章 + `sentiment-evolution` 共 8 章 complete、0 章 failed、6 张图表的 A4 五页 bundle；`generatedAt` 为 `+08:00`。
- PR #10 本地真实 CLI 验收得到前述 8 章 + `keywords` 共 9 章 complete、0 章 failed、7 张图表的 A4 六页 bundle；`generatedAt` 为 `+08:00`。
- PR #11 本地真实 CLI 验收得到前述 9 章 + `engagement` 共 10 章 complete、0 章 failed、8 张图表的 A4 七页 bundle；`generatedAt` 为 `+08:00`。
- PR #12 本地真实 CLI 验收得到完整 PR 11 章 complete、0 章 failed、9 张图表的 A4 七页 bundle；`generatedAt` 为 `+08:00`。
- wheel 已确认包含 CLI、PDF renderer 和中文字体。

测试数量会随实现增长；恢复工作时必须重新运行并记录最新结果，不得把 47 当成永久常量。

## 明确未完成

- M1 离线实现与验收已完成：中文 csuite 7 章与 PR 11 章的标准配置、stub CLI、真实 fixture SQL、图表和 PDF 均已通过；真实 OpenAI-compatible narrator 尚未实现和冒烟，仓库也未收到任务书引用的 gold-report HTML/CSS 资产用于直接像素对比。
- M2 已完成并合并 `timeline`、`top-content`、`negative-themes`、`spread-path`、`response`、`benchmark` 与 `biz-impact` 纵向切片；`recommendations` 已在当前功能分支完成本地验收但尚未经 PR/CI 合并。完整英文矩阵和任意组合仍未完成。
- 真实 OpenAI-compatible narrator 未实现；真实模型未做冒烟验证。
- RAG 未实现：没有 embedding、vector store、retriever、reranker 或检索质量评测；现有 Evidence ID 引用验证属于非 RAG 的确定性证据边界。RAG 只在 `AGENTS.md` 和 D-17 中定义计划边界。
- M3 未开始：FastAPI、任务队列、并发隔离、状态和下载接口均不存在。
- n8n 不能端到端运行，因为其调用的 M3 API 尚不存在；不得激活或声称集成完成。
- `CatalogPublisher` / `index.json` 列表更新尚未实现。
- gold-report 视觉资产尚未交付。

## 已知文档差异

- 任务书描述 fixtures 为真实历史话题数据，但仓库没有收到可发布的原始 fixtures；本项目根据 D-15 提供合成、确定性数据。对外必须明确“合成 fixture”，不得称为真实历史记录。
- 任务书引用的 `docs/02-report-spec.md` 和 gold-report HTML/CSS 没有作为原始附件进入当前仓库；section spec 由本项目逐步定义。用户另行提供的参考 PDF 用于视觉理解，但仓库内 gold-report 资产仍待交付。
- 任务书建议 Playwright/WeasyPrint；当前根据 D-16 使用 ReportLab + 内嵌字体，并已记录和测试该偏离。

## 当前范围约束

context recovery、完整 M1 离线实现与默认配置、以及 M2 `timeline`/`top-content`/`negative-themes`/`spread-path`/`response`/`benchmark`/`biz-impact` 纵向切片已经合并。当前分支 `codex/m2-recommendations-section` 从绿色 `main@eeeba95` 创建，并已完成 `recommendations` 的本地纵向验收；下一步是提交、PR/CI 与合并，不在本分支混入英文矩阵。用户要求暂不开始 RAG，因此不会新增 embedding、vector store、retriever 或 reranker；n8n 继续保持 Draft/inactive，等待 M3 API。

## Context recovery 规则强化小步

- 根目录继续使用 Codex 自动识别的标准文件名 `AGENTS.md`，不另建内容重复的 `agent.md`；它是所有新会话和上下文压缩后的唯一治理入口。
- `AGENTS.md` 已明确整理任务书、产品框架、引擎架构、逐章规格、设计决定、追踪矩阵和当前状态的文档职责，避免把项目自主设计误称为面试方要求，也避免在多处复制 19 章细节。
- RAG 继续冻结为计划边界，未开始 embedding、vector store、retriever、reranker 或检索评测；n8n 继续是 Draft/inactive 的 M3 API 可视化编排层，本小步没有修改本机工作流或导出 JSON。
- Git 闭环已写清：每步从规则恢复上下文、限定一个意图、做一次与风险相称的合并检查、更新本文件、选择性提交并 push；阶段完成后才走 Draft PR/CI/merge，合并后的下一阶段必须从最新绿色 `main` 新建分支。
- 真实模型 API 只在全部本地功能与自动化验证完成后做凭据门控的最终冒烟测试；开发与 CI 使用可注入 stub/fake。
- 第一次检查（静态与一致性）：`git diff --check` 通过；`AGENTS.md` 引用的 7 份框架/状态文档全部存在，RAG 延期、n8n Draft 边界、当时的每步两轮检查规则、GitHub push 和最终 API 冒烟规则均可定位；`n8n/` 无变更。
- 第二次检查（可执行回归）：真实 fixture PostgreSQL 下完整 pytest 160 项通过；`python -m pip check` 无破损依赖。

## 治理切片验证

- 第一次检查（静态一致性）：`git diff --check` 通过；README、AGENTS、状态文件和文档导航中的本地 Markdown 链接全部可解析；工作区只包含预期治理文件。
- 第二次检查（可执行回归）：真实 fixture PostgreSQL 环境下完整 pytest 为 47 项通过；`python -m pip check` 无破损依赖。
- 小步提交：context recovery 入口、RAG/fixture 边界和 PR 证据模板分别提交，没有混入 RAG 实现或 n8n 节点修改。

用户于 2026-07-16 将后续小步改为一次与风险相称的合并检查，以减少重复运行时间；专属 SQL/LLM/PDF 证据仍按变更风险保留，完整 pytest、`pip check` 和必要视觉检查集中在阶段收口。历史结果不能替代当前需要的验证。
- 单次检查规则更新小步只修改 `AGENTS.md` 与本状态文件：`git diff --check`、固定闭环中的单次检查表述、阶段收口完整回归门禁及变更范围检查通过；这是独立 docs commit，不混入业务实现，也未因文档变更重复运行刚通过的 317 项测试。

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

- PR #20 已用 merge commit `eeeba95` 合并；`main@eeeba95` 的独立 CI run `29499194452` 已通过 317 项测试。当前分支 `codex/m2-recommendations-section` 已从该绿色基线创建。
- `timeline`、`top-content`、`negative-themes`、`spread-path`、`response`、`benchmark` 与 `biz-impact` 的完整纵向切片已合并；下一小步只定义 `recommendations` 的事实来源、行动分类、优先级、证据、图表、一次 narrator 与 no-data 合同，不直接开始实现。
- 新分支单次检查：当前分支、`origin/main` 和 merge-base 均精确指向 `eeeba95`，创建时工作区干净；PR #20 merge commit 与独立 main CI 均可核验，没有从旧功能分支串联开发，也未修改实现、fixtures、RAG 或 n8n。
- 真实 OpenAI-compatible narrator 只在最后做凭据门控的冒烟验证；开发与 CI 继续使用 stub。
- RAG 继续延期，不在当前 `recommendations` 阶段实现；n8n 保持 Draft，等待 M3 API。

## M2 `top-content` 阶段入口

- 产品框架只把 `top-content` 定义为“真实高互动/高风险文章及其影响”；任务书没有给出代表性选择算法、互动与风险如何平衡、点数上限、所谓“影响”的可证明口径、图表或退化行为，必须标为项目自主设计。
- 本章与已实现的 `engagement` 高计数排行、`severity` 高风险证据、`viewpoints` 代表性样本和 `timeline` 里程碑存在明显重叠；规格小步已先定义独有用户价值和去重原则，没有简单拼接已有列表或重复同一结论。
- “影响”只能描述存储互动计数、严重性和跨平台/时间等可观测信号，不能从计数推断真实触达、支持度、业务后果或因果影响；所有内容必须保留真实标题、摘要和 Evidence ID。
- 用户要求 RAG 暂不开始，因此本阶段采用固定 SQL 与确定性 Python 基线；不修改 n8n，不调用真实模型 API，也不提前实现下一个章节。
- 重叠审计把本章限定为内容级双信号交叉：不重复 `engagement` 的总体计数组成/集中度，不重复 `severity` 的负面标签分布，也不把 `viewpoints` 或 `timeline` 的选择目标混入代表性排序。
- `docs/02-report-spec.md` 与 D-30 已定义 `top-content.v1`：去重合并存储互动前 3 与明确高风险信号前 3，分类为双信号、仅高互动、仅高风险；高风险信号只来自负面记录的 `high/critical` 严重性或 ≥4 负面分数，不从文本或模型猜测，也不合成为影响力分数。
- fixture 预查按固定展示顺序得到 `bili-007`、`bili-005`、`bili-010`、`bili-003`；双信号 2 篇、仅高互动 1 篇、仅高风险 1 篇，入选去重互动计数 16,890（占全量 64.5%），明确高风险候选共 4 篇。
- 规格小步第一次检查：`git diff --check`、唯一 `top-content` 章节、唯一 D-30、必需合同段和仅文档改动均通过；真实 PostgreSQL 预查精确复算上述 ID、分类、计数与占比。
- 规格小步第二次检查：项目 `.venv` 在健康 fixture PostgreSQL 下完整 pytest 196 项通过；`pip check` 无破损依赖。未修改实现、fixtures、RAG 或 n8n，也未调用真实模型 API。
- 固定 `top_content.sql`、`PostgresTopContentRepository`、`TopContentSnapshot`、去重双信号记录、`EvidenceSet` 和 `FactSet` 已实现；SQL 只绑定 tag 与半开时间边界，Python 验证最多六条记录、候选完整性、唯一排名和固定展示顺序。
- fixture 查询精确返回 12 篇、正互动记录 12 篇、高风险信号候选 4 篇、总存储互动 26,170；入选顺序为 `bili-007`、`bili-005`、`bili-010`、`bili-003`，分类计数 2/1/1，去重入选互动 16,890（64.5%），所有入选项保留真实 Evidence ID。
- SQL/事实小步第一次检查：变更范围仅为 PostgreSQL repository、固定 SQL、事实模型和两类测试；`git diff --check`、Python 静态编译、三个 SQL 绑定参数各出现一次及 `top-content` 单元测试 5 项通过。
- SQL/事实小步第二次检查：健康 fixture PostgreSQL 下专属集成测试 2 项通过，完整 pytest 实际收集并通过 203 项；`pip check` 无破损依赖。空话题返回合法空 snapshot；本小步未接 runner/图表、RAG、n8n 或真实模型 API。
- `TopContentSectionRunner`、`TopContentChartBuilder`、确定性中英文 stub、运行时注册和专属图片 alt 已接入；正常有候选路径先出图再恰好一次 narrator 操作，零文章为 `no_data`，非空但无候选为不出图/不调用模型的 `complete` 结论，查询、计算、图表和叙述失败均限制在本章节。
- 叙述验证要求四条 Evidence ID 顺序与固定清单完全一致，并逐条保留真实标题、摘要、平台、情感、双信号分类、两类排名、存储互动、严重性与负面分；乱序、未知引用或任一批准字段改写都会安全失败。
- `top-content-only` 真实 CLI bundle 得到 1 章 complete、0 章 failed、1 张 150 dpi 图；`meta.stats` 为 articles 12、negativeRatio `暂无`、peakDay `暂无`，没有自动插入未选章节。Markdown 按 `bili-007`、`bili-005`、`bili-010`、`bili-003` 顺序保留原文和 Evidence ID。
- PDF 页图验收先发现图表过高导致方法说明独占空白第 2 页，又发现缩高后图例覆盖右侧子图标题；两项均通过调整图表纵横比与顶部布局修复。最终 v4 为 A4 单页，中文、正文、四条证据、双面板、图例、坐标标签、方法框和页脚均清晰，无乱码、截断、重叠或空白尾页。
- 产物小步第一次检查：变更范围仅为 runner、图表、stub、运行时、图片 alt 和对应测试；`git diff --check`、Python 静态编译、唯一 narrator 调用点、唯一运行时注册及聚焦测试 12 项通过。
- 产物小步第二次检查：健康 fixture PostgreSQL 下 `top-content` SQL + CLI 集成测试 3 项通过，完整 pytest 实际收集并通过 211 项；`pip check` 无破损依赖。本小步未实现 RAG、修改 n8n 或调用真实模型 API。
- PR #15 分支 CI run `29472090570` 通过后转为 ready，并用 merge commit `9b5046d` 合并；合并后独立 main CI run `29472151204` 通过 211 项测试。功能分支保留，未 squash 或删除历史。

## M2 `negative-themes` 阶段入口

- 产品框架只把 `negative-themes` 定义为“负面摘要中的主要原因、诉求和风险主题”；任务书没有提供主题算法、主题数、覆盖率分母、证据上限、图表或无主题退化行为，这些必须标为项目自主设计。
- 本章与 `viewpoints` 的代表性观点、`keywords` 的精确短语覆盖、`severity` 的结构化风险分布存在重叠。下一小步必须先定义主题级独有用户价值和去重原则，不能把已有三章简单重排或让模型自由命名无证据主题。
- 任务书要求观点来自真实摘要，因此任何主题都必须能回指真实标题/摘要与 Evidence ID；数字仍由固定 SQL/Python 计算，模型最多做一次受限叙述。
- 用户要求 RAG 暂不开始，本阶段先设计确定性、可测试的非 RAG 基线；不引入 embedding、vector store、retriever 或 reranker，不修改 n8n，不调用真实模型 API，也不提前实现 `spread-path`。
- 去重审计将本章限定为负面人口的议题维度交叉表：不重复 `viewpoints` 的情感代表样本，不重复 `keywords` 的原文短语排行，也不重复 `severity` 的总体标签分布；固定维度只回答负面摘要聚焦什么，以及哪些维度承载明确诉求和 high/critical 标签。
- `docs/02-report-spec.md` 与 D-31 已定义 `negative-themes.v1` / `negative-themes.codebook.v1`：只用摘要的 NFKC 规范化文本和文档中公开的精确指标，将记录多标签映射为 `用户自主权`、`透明度与解释`、`反馈有效性`；主题与关注/诉求角色均可重叠，未分类负面记录必须显式披露。
- 显示主题至少覆盖两篇负面记录，最多三类；按覆盖篇数、high/critical 篇数、存储互动和固定代码本顺序排名。每类选择一条按严重性、负面分、互动、时间和 ID 排序的真实代表证据；模型不得重命名、合并或生成主题。
- fixture 预查得到三类负面覆盖 5/4/3 篇，关注/诉求计数分别为 4:2、2:2、2:1，high/critical 为 3/2/2，代表 Evidence ID 为 `bili-005`、`bili-003`、`bili-007`；7 篇负面均至少匹配一类，未分类为 0。重叠成员数不得相加解释为独立文章总量。
- 规格小步第一次检查：仅 `docs/02-report-spec.md` 与 `docs/design-decisions.md` 改动；`git diff --check`、唯一 `negative-themes` 章节、唯一 D-31、必需合同段、无实现/n8n 变更均通过，真实 fixture PostgreSQL 精确复算上述覆盖、角色、标签和代表证据。
- 规格小步第二次检查：项目 `.venv` 在健康 fixture PostgreSQL 下完整 pytest 实际收集并通过 211 项；`pip check` 无破损依赖。未实现主题 SQL/代码、RAG、n8n 或真实模型调用。
- 固定 `negative_themes.sql`、`PostgresNegativeThemesRepository`、`NegativeThemesSnapshot`、版本化主题定义/角色标记、`FactSet` 和去重 `EvidenceSet` 已实现；SQL 只做 tag、半开时间与负面情感过滤，Python 才执行公开代码本、重叠分类、排序和代表选择。
- fixture 查询正式验证 12 篇范围内内容、7 篇负面；显示主题顺序为用户自主权、透明度与解释、反馈有效性，覆盖 5/4/3，关注/诉求 4:2、2:2、2:1，high/critical 3/2/2，主题存储互动 8,965/5,405/13,020，代表 Evidence ID 为 `bili-005`、`bili-003`、`bili-007`，未分类为 0。
- `FactSet` 保留负面人口分母、代码本分类/未分类占比、12 次重叠主题成员关系、各主题全部来源 ID 和代表 ID；`EvidenceSet` 只保留真实标题/摘要并对共享代表去重。零文章/零负面与非空但不足两篇的无显示主题范围均保留可审计基础事实。
- SQL/事实小步第一次检查：变更范围仅为 PostgreSQL repository、固定 SQL、主题模型和两类测试；`git diff --check`、Python 静态编译、三个 SQL 绑定参数各出现一次及模型单元测试 5 项通过。
- SQL/事实小步第二次检查：健康 fixture PostgreSQL 下专属集成测试 2 项通过，完整 pytest 实际收集并通过 218 项；`pip check` 无破损依赖。空话题返回合法聚合 snapshot；本小步未接 runner/图表、RAG、n8n 或真实模型 API。
- `NegativeThemesSectionRunner`、`NegativeThemesChartBuilder`、确定性中英文 stub、运行时注册和专属图片 alt 已接入；正常路径先出图再恰好一次 narrator 操作，零负面为保留事实的 `no_data`，非空但无维度达到两篇门槛为不出图/不调用模型的 `complete` 结论，查询、计算、图表和叙述失败均限制在本章节。
- 叙述验证按显示主题顺序校验代表 Evidence ID，可在多标签主题共享同一代表时允许按主题重复引用，同时要求每一主题行保留固定中英文标签、负面分母覆盖、关注/诉求、高/危交叉、精确指标、平台、真实标题和摘要；乱序、未知引用、改写证据或把 `5/7` 改成 `6/7` 等组合数字篡改均安全失败。
- `negative-themes-only` 真实 CLI bundle 得到 1 章 complete、0 章 failed、1 张 150 dpi 图；`meta.stats` 为 articles 12、negativeRatio `暂无`、peakDay `暂无`，没有自动插入未选章节。Markdown 按 `bili-005`、`bili-003`、`bili-007` 顺序保留原文和 Evidence ID。
- PDF 经 Poppler 验证为 A4 单页；页图与图表原图人工复核显示中文、三条主题证据、洞察标题、重叠免责声明、图例、数值标签、方法框和页脚均清晰，无乱码、截断、重叠、标签遮挡或孤页。
- 产物小步第一次检查：变更范围仅为 runner、图表、stub、运行时、图片 alt 和对应测试；`git diff --check`、Python 静态编译、唯一 narrator 调用点、唯一运行时注册及聚焦测试 13 项通过。检查过程中加固了组合覆盖数字的原子校验。
- 产物小步第二次检查：健康 fixture PostgreSQL 下 `negative-themes` SQL + CLI 集成测试 3 项通过，完整 pytest 实际收集并通过 227 项；`pip check` 无破损依赖。本小步未实现 RAG、修改 n8n 或调用真实模型 API。
- PR #16 分支 CI run `29473253484` 通过后转为 ready，并用 merge commit `d5d2120` 合并；合并后独立 main CI run `29473309498` 通过 227 项测试。功能分支保留，未 squash 或删除历史。

## M2 `spread-path` 阶段入口

- 产品框架只把 `spread-path` 定义为“话题如何在平台与时间之间扩散”；任务书没有提供扩散边定义、跨平台因果证据、时间窗口、节点/边上限、证据选择、图表或退化行为，这些必须标为项目自主设计。
- 本章与 `timeline` 的代表性里程碑、`trend` 的总体时间序列和 `platforms` 的平台聚合存在明显重叠。下一小步必须先定义独有用户价值和去重原则，不能把三张已有视图拼接后称为传播路径，也不能把先后出现静默解释成转发或因果扩散。
- 任务书要求所有数字可追溯、观点来自真实摘要；因此任何可见的跨平台时序关系都必须由固定 SQL/Python 事实和真实 Evidence ID 支撑，模型最多做一次受限叙述。
- 阶段入口先审计 schema 是否足以支持文章级转发链/引用边；若只有平台与时间，就把结果命名为“可观测平台迁移顺序”或同等非因果口径，并在规格中明确数据能力边界。
- 用户要求 RAG 暂不开始，本阶段先设计确定性、可测试的非 RAG 基线；不引入 embedding、vector store、retriever 或 reranker，不修改 n8n，不调用真实模型 API，也不提前实现 `response`。
- schema 审计确认 `articles` 没有 parent、repost、quote、referral 或 canonical-source 关系字段；`docs/02-report-spec.md` 与 D-32 因此把本章限定为日期×平台文章量矩阵和平台首次收录证据，明确拒绝把时间先后描述为转载链、事件起源、受众迁移或平台间因果影响。
- 规格保留完整报告日历零值单元，统计多平台日与单日最大平台覆盖；物质性平台按文章量、存储互动、首次时间和名称排名，最多显示六个，再按首次时间展示。精确同刻首次收录共享 `entryWave`，不能用名称排序制造语义先后；单平台范围为不出图/不调用模型的 `complete` 结论。
- fixture 真实查询得到 12 篇、4 个平台；首次收录顺序为 B站/微博/知乎/新闻，对应 Evidence ID `bili-001`/`bili-002`/`bili-003`/`bili-004`，文章量 4/4/1/3、负面量 2/3/1/1、活跃日 4/4/1/3。最早到最后新平台首次收录间隔 32.5 小时，4 个日期有多平台记录，3 月 20 日以 3 个平台达到单日最大覆盖。
- 规格小步第一次检查：仅 `docs/02-report-spec.md` 与 `docs/design-decisions.md` 改动；`git diff --check`、唯一 `spread-path` 章节、唯一 D-32、必需合同段、无实现/n8n 变更均通过。
- 规格小步第二次检查：真实 fixture PostgreSQL 用 Unicode 安全断言精确复算上述平台、Evidence ID、计数、活跃日、32.5 小时和多平台日期；项目 `.venv` 完整 pytest 实际收集并通过 227 项，`pip check` 无破损依赖。首次内联断言因 PowerShell 转码中文源码产生假阴性，改用 Unicode 转义后同一数据断言通过，未发现产品口径冲突。
- 固定 `spread_path.sql`、`PostgresSpreadPathRepository`、`SpreadPathSnapshot`、平台观察对象、完整日历矩阵、物质性平台选择、首收录 EvidenceSet 和可追溯 FactSet 已实现；SQL 只绑定 tag 与半开时间边界，Python 才计算平台排名、显示顺序、同刻波次和非因果时序事实。
- fixture 集成测试正式验证 12 篇、B站/微博/知乎/新闻 4 个平台，首收录 Evidence ID `bili-001`/`bili-002`/`bili-003`/`bili-004`，文章量 4/4/1/3、负面量 2/3/1/1、活跃日 4/4/1/3、存储互动 6,610/15,715/1,420/2,425，以及 32.5 小时、4 个多平台日和 3 月 20 日 3 平台最大覆盖。
- `FactSet` 保留完整报告日历、显示/省略平台数、单日最大覆盖并列日期、首次收录间隔、首/末新平台并列、每平台全部来源 ID 和首记录 ID；`relationshipEdges` 明确为不可用。空话题返回 7 日合法空 snapshot，单平台与精确同刻首次收录均有确定性事实。
- SQL/事实小步第一次检查：变更范围仅为 PostgreSQL repository、固定 SQL、事实模型和两类测试；`git diff --check`、Python 静态编译、三个 SQL 绑定参数各出现一次及模型单元测试 6 项通过。
- SQL/事实小步第二次检查：提交前将并列日期/平台集合从 tuple 修正为符合 `FactValue` 的稳定字符串标量，并精确断言同刻平台的确定性显示顺序；修订后模型 + 真实数据库聚焦测试 8 项通过，完整 pytest 实际收集并通过 235 项，`pip check` 无破损依赖。本小步未接 runner/图表、RAG、n8n 或真实模型 API。
- `SpreadPathSectionRunner`、`SpreadPathChartBuilder`、确定性中英文 stub、运行时注册和专属图片 alt 已接入；正常多平台路径先出图再恰好一次 narrator 操作，零文章为保留事实的 `no_data`，单平台为不出图/不调用模型的 `complete` 结论，查询、计算、图表和叙述失败均限制在本章节。
- 叙述验证要求四条首收录 Evidence ID 按显示平台顺序出现，并逐条保留波次、平台、首末时间、文章/负面/活跃日/存储互动、首记录情感、真实标题和摘要；乱序、未知引用、证据改写、波次或组合计数篡改均安全失败。中英文正文都强制披露缺少转载/引用/父子/引流/来源关系边。
- `spread-path-only` 真实 CLI bundle 得到 1 章 complete、0 章 failed、1 张 150 dpi 图；`meta.stats` 为 articles 12、negativeRatio `暂无`、peakDay `暂无`，没有自动插入未选章节。Markdown 按 `bili-001`、`bili-002`、`bili-003`、`bili-004` 顺序保留首收录原文和 Evidence ID。
- 首次 PDF 视觉检查发现 3.59 英寸矩阵被整体推到 A4 第 2 页；缩短 4 行矩阵后恢复单页。v2 又发现图内“报告日历”轴标题与底部非因果注释重叠，移除冗余轴标题后 v3 页图与图表原图人工复核通过：正文、四条证据、矩阵、波次描边、图例、日期、非因果注释、图片说明、方法框和页脚均清晰，无乱码、截断、重叠或孤页。
- 产物小步第一次检查：变更范围仅为 runner、图表、stub、运行时、图片 alt 和对应测试；`git diff --check`、Python 静态编译、唯一 narrator 调用点、唯一运行时注册及聚焦测试 13 项通过。首次检查发现并移除了内嵌字体不支持的粗体请求。
- 产物小步第二次检查：健康 fixture PostgreSQL 下 `spread-path` SQL + CLI 集成测试 3 项通过；最终 v3 后完整 pytest 实际收集并通过 243 项，`pip check` 无破损依赖。本小步未实现 RAG、修改 n8n 或调用真实模型 API。
- PR #17 分支 CI run `29474385184` 通过后转为 ready，并用 merge commit `1a047b4` 合并；合并后独立 main CI run `29474436518` 通过 243 项测试。功能分支保留，未 squash 或删除历史。

## M2 `response` 阶段入口

- 产品框架只把 `response` 定义为“根据 `responseDate` 比较回应前后热度与情感”；任务书没有定义回应日归属、前后窗口长度、非对称日历、零样本侧、效果阈值、证据或图表，这些必须标为项目自主设计。
- `responseDate` 是任务书固定公共配置中该章节的专属输入，不能改名、移到环境变量或从 `official-response` 标签静默推断；缺失输入只让本章节进入可行动的 `failed`，不能影响其他章节。
- 本章与 `trend` 的总量时间序列、`sentiment-evolution` 的阶段情感构成和 `timeline` 的回应标签记录存在重叠。下一小步必须先定义“以用户给定切点做平衡前后比较”的独有价值，不能把时间先后或下降直接称为回应造成的效果。
- fixture 中 `responseDate=2026-03-19` 可与精确 `official-response` 标签记录 `bili-006` 对照，但用户输入仍是分析切点，标签只可作为数据覆盖说明，不能替代输入或证明发言权威性。
- 用户要求 RAG 暂不开始，本阶段先设计确定性、可测试的非 RAG 基线；不引入 embedding、vector store、retriever 或 reranker，不修改 n8n，不调用真实模型 API，也不提前实现 `benchmark`。
- `docs/02-report-spec.md` 与 D-33 已定义 `response.v1`：排除只有日期精度的回应日，以用户给定 `responseDate` 为切点，取范围内前后各最多 7 个且长度完全相同的完整自然日；只比较观察到的热度与情感，不把时间相关性表述为回应效果或因果。
- 规格明确披露回应日记录、回应日精确标签覆盖和平衡窗口外记录；一侧零样本仍可诚实完成但分母相关比例为 `unavailable`，两侧均无比较记录返回 `no_data`，非法/边界日期在查询前返回章节级 `INPUT` 失败。本章是聚合比较，不创建 `EvidenceSet`，不重复 `timeline` 的回应记录选择。
- 真实 fixture PostgreSQL 预查确认：`responseDate=2026-03-19` 时匹配窗口为 3/17–3/18 与 3/20–3/21，各 2 天、各 4 篇、各 2 篇负面（50%）；回应日 2 篇，其中 1 篇带精确 `official-response` 标签；3/22–3/23 的 2 篇因平衡窗口被明确排除。
- 规格小步第一次检查：仅 `docs/02-report-spec.md` 与 `docs/design-decisions.md` 改动；`git diff --check`、唯一 `response` 章节、唯一 D-33、必需合同段和无实现/n8n 变更均通过。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 实际收集并通过 243 项，`pip check` 无破损依赖。本小步未实现 runner/图表、RAG、n8n 或真实模型 API。
- 实现前审计发现 planner 已保留 `SectionConfig.input`，但 application service 当前未把章节 input 传给 runner。下一小步先以向后兼容的可选参数显式贯通该输入，再实现 `response.sql` 与 Python 事实；不得让 response runner 静默重读配置或从标签推断日期。
- 章节 input 贯通小步已修复上述断层：application service 现在把 planner 保留的原始章节 input 显式传给统一 runner lifecycle；全部 15 个现有 runner 以可选参数向后兼容原三参数调用，后续 `response`、`benchmark`、`biz-impact` 无需各自重读配置或建立隐藏执行路径。
- input 贯通小步第一次检查：`git diff --check`、17 个预期代码/测试文件范围、Python 静态编译、15/15 runner 签名覆盖和唯一 service 传递点均通过；新增测试覆盖配置 → planner → service → runner 的精确字典保留。
- input 贯通小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 实际收集并通过 244 项，`pip check` 无破损依赖。本小步未新增 SQL、response runner/图表、LLM、RAG、n8n 或真实 API 调用。
- 下一小步只实现固定 `response.sql`、输入日期解析/窗口校验、Python 聚合事实和真实 fixture PostgreSQL 集成测试；runner、图表与 narrator 仍留到后续提交。
- 固定 `response.sql`、`PostgresResponseRepository`、严格 `YYYY-MM-DD` 解析、`ResponseWindow`、逐篇情感/标签观察、平衡前后窗口统计和可追溯 `FactSet` 已实现。SQL 只绑定 tag、半开时间边界与报告时区；回应日期不进入 SQL，也不从标签推断，Python 在查询前验证日期必须严格位于报告范围内部。
- Python 最多取前后各 7 个完整自然日并排除回应日；事实完整保留前后日期、样本量、每日均量、三类情感计数/占比、量级差/变化率、情感占比百分点差、回应日及标签覆盖和平衡窗口外记录。单侧零样本的占比/变化率为 `不可用`，不会伪装成 0%；两侧均无比较记录仍保留可审计空事实供后续 runner 判为 `no_data`。
- 真实 fixture 集成测试正式验证范围内 12 篇，前窗口 0/2/2、后窗口 1/1/2（正/中/负），两侧各 4 篇且日均 2.0，回应日 2 篇/精确标签 1 篇，窗口外 2 篇，负面占比差 `+0.0 个百分点`；空话题返回窗口完整的零值 snapshot。
- SQL/事实小步第一次检查：`git diff --check`、Python 静态编译、四个 SQL 绑定参数各出现一次、无超长新增 Python 行及 response 领域 15 项测试通过；覆盖严格日期、范围边界、7 日上限、回应日排除、单侧零分母和范围外观察拒绝。
- SQL/事实小步第二次检查：健康 fixture PostgreSQL 下 response 专属集成测试 2 项通过，完整 pytest 实际收集并通过 261 项，`pip check` 无破损依赖。本小步未接 response runner/图表/stub/运行时、RAG、n8n 或真实模型 API。
- `ResponseSectionRunner`、`ResponseChartBuilder`、确定性中英文 stub、运行时注册和专属图片 alt 已接入。严格日期/范围输入错误在查询前进入章节级 `INPUT` 失败；零范围记录或等长窗口均无记录为保留事实的 `no_data`；单侧零样本仍完整生成并将无分母比例标为 `不可用`；query/calculation/chart/LLM 失败均限制在本章节。
- 正常路径只调用一次 narrator，输入仅为可追溯聚合 `FactSet` 与空 `EvidenceSet`；正文逐项披露前后日期、量级、日均、三类情感、回应日/精确标签/窗口外记录，并明确等长窗口差异不建立因果、反事实或回应效果。
- response-only 真实 fixture CLI bundle 得到 1 章 complete、0 章 failed、1 张 150 dpi 图；`meta.stats` 为 articles 12、negativeRatio `暂无`、peakDay `暂无`。Markdown 准确显示前后各 4 篇/日均 2.0、负面各 2 篇/50.0%，回应日 2 篇/精确标签 1 篇、窗口外 2 篇。
- 图表原图与 Poppler 渲染的 A4 单页 PDF 已逐项目视复核：标题、图例、堆叠情感计数、两侧注释、日期标签、回应日排除和非因果脚注完整清晰，无中文乱码、截断、重叠、图例遮挡或孤页。
- 产物小步第一次检查：`git diff --check`、Python 静态编译和 response 领域/runner/图表聚焦 27 项测试通过；项目未配置 Ruff 且虚拟环境未安装 Ruff，因此未把该命令作为虚假通过证据。
- 产物小步第二次检查：健康 fixture PostgreSQL 下 response-only CLI 集成测试通过，完整 pytest 实际收集并通过 274 项，`pip check` 无破损依赖，实际单页 bundle 与图表视觉验收通过。本小步未实现 RAG、修改 n8n 或调用真实模型 API。
- PR #18 分支 CI run `29475938832` 通过后转为 ready，并用 merge commit `ad1e414` 合并；合并后独立 main CI run `29475994557` 通过 274 项测试。功能分支保留，未 squash 或删除历史。

## M2 `benchmark` 阶段入口

- 产品框架只把 `benchmark` 定义为“根据 `comparisonTag` 比较另一历史事件”；任务书没有定义比较日期范围、是否复用当前窗口、话题不存在/重叠、可比指标、证据、图表或结论边界，这些必须标为项目自主设计。
- `comparisonTag` 是任务书固定公共配置中本章节的专属输入，不能改名、移到环境变量或由模型猜测；缺失或非法输入只让本章节进入可行动的 `failed`，不能影响其他章节。
- 下一小步只审计 schema 与合成 fixtures，确认是否存在可用于真实 SQL 对标的第二话题及其日期覆盖；在数据事实明确前不决定窗口对齐、归一化指标或样本不足门槛。
- 本阶段必须避免把不同采集规模、日期长度或平台覆盖造成的差异写成事件本身更严重/更成功；任何对标结论只能描述可审计的收录量、构成和存储互动差异。
- 用户要求 RAG 暂不开始，本阶段采用固定 SQL 与确定性 Python 基线；不修改 n8n，不调用真实模型 API，也不提前实现 `biz-impact`。
- schema/fixture 审计确认当前种子没有可用的独立历史事件：`algorithm` 与 `official-response` 都是当前话题记录的重叠标签，`other-topic` 只有 1 条专用于 tag 过滤的边界记录；不得把这些数据静默包装成历史案例。
- `docs/02-report-spec.md` 与 D-34 已定义 `benchmark.v1`：当前组使用用户选择的完整日期范围；历史组只取带 `comparisonTag` 且不带当前 tag 的独立记录，以其首次收录日为锚点，截取与当前范围完全等长的自然日窗口，并披露窗口外历史记录。
- 规格限定比较文章日均量、情感构成、高/危占全部样本比例、平台覆盖和篇均存储互动及其可用差值；不创建综合分数，不使用 EvidenceSet/RAG，也不得从收录差异推断事件客观重要性、严重性、成功或业务后果。
- 为使固定 SQL 集成测试有真实的双组数据，后续 SQL/事实小步将新增一个与现有标签完全不重叠、日期更早的合成历史事件 cohort；它必须明确标为 synthetic fixture，且不得改变现有主话题 12 篇及其所有已验证口径。
- 规格小步第一次检查：仅逐章规格、设计决定和状态文档改动；`git diff --check`、唯一 `benchmark` 章节、唯一 D-34、必需输入/等长窗口/独立 cohort/一次 narrator/no-data/无 RAG 边界均通过。真实 PostgreSQL 审计复现当前无可用独立历史 cohort 的数据缺口。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 实际收集并通过 274 项，`pip check` 无破损依赖。本小步未修改 fixtures/实现、RAG、n8n 或真实模型 API；下一小步才新增独立 synthetic cohort、固定 SQL、Python 事实和数据库集成测试。
- fixtures 新增完全独立的 `legacy-feed-controls` synthetic cohort：2026-02-10 至 2/16 共 8 篇，正/中/负 1/2/5，覆盖 4 个平台，高/危负面 3 篇，存储互动计数和 9,500；fixture README 明确两组均非生产或真实历史数据。现有 `bilibili-dislike` 报告范围仍为 12 篇且所有既有测试口径未改变。
- 固定 `benchmark.sql`、`PostgresBenchmarkRepository`、严格 `comparisonTag` 解析、`BenchmarkCohort`、`BenchmarkSnapshot` 和可追溯 `FactSet` 已实现。SQL 返回固定 current/comparison 两行，比较组排除任何同时带当前 tag 的记录，并用首次独立记录锚定 7 日等长窗口。
- Python 验证 cohort 顺序、tag 独立、等长日历、情感合计、高/危子集和非负计数；事实保留两侧日期/样本/日均/平台/情感/高危/存储互动及 current-minus-comparison 差值，零分母显示 `不可用`。
- 真实 fixture 集成测试正式验证当前/历史 12/8 篇、日均 1.7/1.1、负面 7/5（58.3%/62.5%）、高/危 4/3（33.3%/37.5%）、平台 4/4、存储互动 26,170/9,500，负面占比差与高/危占比差均为 `-4.2 个百分点`；重叠 `algorithm` tag 被排除为零比较样本。
- SQL/事实小步第一次检查：`git diff --check`、Python 静态编译、无超长新增 Python 行及 benchmark 专属单元/真实数据库测试 11 项通过；首次集成失败只因测试沿用占位 tag `layoff`，显式改为 fixture 主 tag 后同一 SQL 断言全部通过，未修改实现迎合错误输入。
- SQL/事实小步第二次检查：重建并健康启动仓库专用 fixture PostgreSQL 后，完整 pytest 实际收集并通过 285 项，`pip check` 无破损依赖。本小步未接 runner/图表/stub/运行时、RAG、n8n 或真实模型 API。
- `BenchmarkSectionRunner`、双面板 `BenchmarkChartBuilder`、确定性中英文 stub、运行时注册和专属图片 alt 已接入；正常路径只调用一次 narrator 并传空 EvidenceSet，缺失/相同 tag 在查询前失败，无独立样本为保留事实的 `no_data`，各阶段错误均限制在本章节。
- benchmark-only CLI 首次验收发现通用 `meta.stats` 未识别 `currentArticles` 而错误显示 0；按 D-29 将该可审计事实加入候选后为 12，没有插入未选 metrics 或复制计算。
- 实际 bundle 为 1 章 complete、0 failed、1 张 150 dpi 图和 A4 单页 PDF；正文准确披露 7 日等长窗口、12/8 篇、日均 1.7/1.1、负面 58.3%/62.5% 与篇均存储互动 2,180.8/1,187.5，并保留不可推断事件客观重要性/严重性/成败的边界。
- 首次图表视觉检查发现图例压住横轴标签；移至图外右上方并缩小绘图区后重新生成。最终图表原图与 Poppler PDF 页均无中文乱码、截断、重叠、图例遮挡或孤页。
- 产物小步第一次检查：Python 静态编译、`git diff --check` 和 benchmark 模型/SQL/runner/图表/CLI 聚焦 15 项通过。
- 产物小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 实际收集并通过 289 项，`pip check` 无破损依赖，最终 v2 bundle 视觉验收通过。本小步未实现 RAG、修改 n8n 或调用真实模型 API。
- PR #19 分支 CI run `29476953634` 通过后转为 ready，并用 merge commit `542196c` 合并；合并后独立 main CI run `29477030341` 通过 289 项测试。功能分支保留，未 squash 或删除历史。

## M2 `biz-impact` 阶段入口

- 产品框架只把 `biz-impact` 定义为“结合代码事实和用户 `notes` 分析业务影响”；任务书没有定义 notes 格式、事实选择、影响类别、图表、可信度或退化行为，这些必须标为项目自主设计。
- `notes` 是任务书固定公共配置中本章节的专属输入，不能改名、移到环境变量或让模型补写；缺失或非法输入只让本章节进入可行动的 `failed`，不能影响其他章节。
- 本章必须严格区分代码可观测的舆情压力信号与用户提供的业务背景。notes 只能作为“用户提供背景”原样进入批准上下文，不能被当成数据库验证事实，也不能据此生成收入、客户流失、股价、销量或因果数字。
- 下一小步先定义长度/空白/控制字符边界、结构化代码事实、固定影响维度、一次 narrator 与 no-data 行为；不修改 fixtures，不提前实现 recommendations。
- 用户要求 RAG 暂不开始，本阶段不引入 embedding、vector store、retriever 或 reranker，不修改 n8n，也不调用真实模型 API。
- `docs/02-report-spec.md` 与 D-35 已定义 `biz-impact.v1`：`notes` 经首尾裁剪和空白折叠后必须为 1–1000 个 Unicode 字符，并拒绝 NUL 与非空白控制字符；内容作为独立、未验证的用户上下文进入 narrator，不写入数据库 `FactSet` 或文章 `EvidenceSet`，其中的模型指令、数字和因果说法均不会升级为报告事实。
- 固定 SQL 只聚合当前 tag/完整日期范围内的文章、情感、高/危负面、平台、活跃日、峰值和四类存储互动计数；Python 形成“舆情声誉压力”“公开讨论应对复杂度”和“业务结果核验缺口”三个不评分的分析视角。正文只允许把代码事实与 notes 描述为待验证的同时观察/可能路径，不推断收入、销量、转化、流失、股价、客户、运营或声誉因果结果。
- 本章明确不生成图表：当前 schema 没有可验证的业务结果序列，重复已有舆情图会视觉上暗示商业效果。正常非空范围至多调用一次 narrator；零文章为不调用 narrator 的 `no_data`，非空且零负面仍诚实 `complete`；recommendations 继续由用户单独选择的后续章节负责。
- 规格小步第一次检查：变更范围仅为逐章规格与设计决定；`git diff --check`、唯一 `biz-impact` 章节、唯一 D-35，以及 notes/独立上下文/固定 SQL/无 EvidenceSet/无图表/一次 narrator/no-data/无 RAG/不越界 recommendations 合同均通过。首次检查发现一处行末空格并修正后重跑通过，没有把带警告结果记作成功。
- 规格小步第二次检查：仓库 fixture PostgreSQL 健康，项目 `.venv` 完整 pytest 实际收集并通过 289 项，`pip check` 无破损依赖。本小步未修改 fixtures/实现、RAG、n8n 或真实模型 API；下一小步才实现独立用户上下文类型、固定 SQL、Python 事实和真实数据库集成测试。
- 独立 `UserContext` / `VerificationStatus.UNVERIFIED` 与 `parse_biz_impact_notes` 已实现：notes 折叠普通空白、接受恰好 1000 字符、拒绝缺失/空白/超长/NUL/非空白 C0/C1 控制字符，并保留固定 report-config 来源；notes 不进入 `FactSet` 或 `EvidenceSet`。
- 固定 `biz_impact.sql`、`PostgresBizImpactRepository` 和 `BizImpactSnapshot` 已实现。Python 校验日期、情感合计、高/危负面子集、平台/活跃日/峰值和空范围一致性；事实保留情感占比、活跃日覆盖、峰值占比、高/危占负面与全量比例、四类存储互动、篇均值、两个描述性视角、业务结果数据缺口和未建立因果状态，不生成综合分数。
- 真实 synthetic fixture 集成测试验证 2026-03-17 至 3/23 共 12 篇、正/中/负 2/3/7、4 平台、7 个活跃日、3/20 峰值 3 篇、高/危负面 4 篇、赞/评/转/藏 15,460/4,705/4,620/1,385、存储互动合计 26,170、评论加转发 9,325；负面占比 58.3%、高/危占负面 57.1%、高/危占全量 33.3%、峰值占比 25.0%。空话题返回带完整日期范围的合法零值 snapshot，分母事实明确不可用。
- SQL/事实小步第一次检查：范围严格为独立上下文、biz-impact 模型、固定 SQL、PostgreSQL adapter 与两类测试共 7 个文件；`git diff --check`、Python 静态编译、四个 SQL 绑定参数各一次、SQL 不含 notes/模型术语、无超长 Python 行，以及单元/真实数据库聚焦 17 项测试均通过。初版范围脚本因 `git diff --name-only` 不列未跟踪文件而误报，改为已修改与未跟踪文件并集后重跑通过，没有改变实现来迎合检查器；最终 staged 检查另发现三个新文件末尾多余空白行，修正并重新暂存后通过。
- SQL/事实小步第二次检查：仓库 fixture PostgreSQL 健康，项目 `.venv` 完整 pytest 实际收集并通过 306 项，`pip check` 无破损依赖。本小步未接 biz-impact runner/stub/PDF、recommendations、RAG、n8n 或真实模型 API；下一小步才贯通独立上下文到一次 narrator 和完整 bundle。
- `BizImpactSectionRunner`、显式 `NarrationRequest.user_context`、确定性中英文 stub 与运行时注册已接通。正常非空范围恰好调用一次 narrator 并传空 `EvidenceSet`，正文固定分开可观测舆情信号、未验证用户背景和业务结果核验缺口；零文章保留事实并跳过 narrator，非空零负面诚实完成，输入/query/calculation/LLM 失败均限制在本章节。
- 用户 notes 经过规范化后以独立 `UserContext` 传入，Markdown 特殊字符编码为字面文本，PDF blockquote 在安全转义后恢复可读字符；runner 校验原文只出现一次、来源标签不丢失，并拒绝改写背景、Evidence ID 或图表注入。`biz-impact` 不生成图表，也不提供建议。
- 任意组合接线检查发现 `meta.stats.negativeRatio` 尚未识别本章可审计的 `negativeShare`，导致首轮完整回归中 business-impact-only bundle 显示 `暂无`；assembler 增加显式候选映射和专属回归后，最终产物准确显示 articles 12、negativeRatio 58.3%、peakDay 3/20，没有插入未选章节。
- 产物小步最终合并检查：变更范围严格为 11 个 biz-impact/通用上下文与测试文件；`git diff --check`、Python 静态编译、唯一 narrator 调用、唯一运行时注册、零图表路径、31 项聚焦测试均通过。健康 fixture PostgreSQL 下完整 pytest 实际收集并通过 317 项，`pip check` 无破损依赖。
- 真实 stub CLI 产物为 1 章 complete、0 failed、0 图表；Markdown 准确显示 12 篇、负面 7 篇/58.3%、高/危 4 篇、存储互动 26,170，以及原样且明确未验证的用户背景。Poppler 验证 PDF 为 A4 单页，页图目视无中文乱码、截断、重叠、Markdown 实体泄漏或孤页；页面留白来自本章按设计不生成误导性业务图表。
- 本小步未实现 `recommendations`、RAG，未修改 n8n，也未调用真实模型 API；真实 OpenAI-compatible 冒烟仍留到全部本地功能完成后。
- PR #20 分支 CI run `29498997274` 通过后转为 ready，并用 merge commit `eeeba95` 合并；合并后独立 main CI run `29499194452` 通过 317 项测试。功能分支保留，未 squash 或删除历史。

## M2 `recommendations` 阶段入口

- 产品框架只把 `recommendations` 定义为“根据事实和风险给出按优先级排列的行动方案”；任务书没有给出行动分类、优先级算法、负责人/时限、事实门槛、证据、图表或无数据行为，这些必须标为项目自主设计。
- 本章与 `risk` 的压力诊断、`response` 的非因果前后比较、`negative-themes` 的议题拆解及 `biz-impact` 的核验缺口存在重叠。下一规格小步必须先定义独有用户价值和去重原则，不能把现有结论改写成泛化公关建议，也不能让模型自由创造未被数据触发的行动。
- 当前 `docs/02-report-spec.md` 尚无 recommendations 技术合同。下一小步只做 schema/fixture 与已批准事实能力审计，再定义固定事实来源、透明行动代码本、优先级、一次 narrator、无数据和失败隔离；实现必须等规格决定完成后开始。
- 本阶段不使用 RAG 或 n8n，不调用真实模型 API；开发与 CI 继续使用可注入 stub，真实 API 留到全部本地功能完成后的最终冒烟测试。
- 新分支 `codex/m2-recommendations-section` 从已通过独立 main CI 的 `eeeba95` 创建；本入口小步只更新状态，不修改实现、fixtures 或公共输入/输出契约。
- `docs/02-report-spec.md` 与 D-36 已定义 `recommendations.v1`：固定 SQL 返回范围计数与全部真实负面记录，Python 复用公开的 `negative-themes.codebook.v1`，从高/危核验、用户自主权、透明度、反馈闭环和无候选回退五类版本化行动中最多选择四项；优先级是透明词典序，不创建综合分数。
- 每项行动固定建议角色、立即/24 小时/72 小时 playbook 目标、动作文本、核验清单、全部触发 source ID 和一条真实代表 Evidence ID；共享代表可在行动顺序中重复引用，但底层 `EvidenceSet` 去重。模型不得新增行动、改写原文、补数字、生成法律结论或执行外部操作。
- 本章不生成图表：排序文本卡片已经表达行动顺序，视觉分数/红绿灯会暗示未经验证的效果或置信度。零文章为不调用 narrator 的 `no_data`；非空零负面为不调用 narrator 的 `complete` 常规监测结论；存在负面时至少产生可审计回退行动并恰好调用一次 narrator。
- 固定 `recommendations.sql`、`PostgresRecommendationsRepository`、`RecommendationsSnapshot` 和版本化行动定义已实现；查询只绑定 tag 与半开时间范围，并复用已验证的负面记录模型和主题代码本，不调用模型、RAG、n8n 或外部服务。
- fixture PostgreSQL 正式验证四项行动依次为 `triage_high_risk`、`restore_user_control`、`explain_change`、`close_feedback_loop`，代表 Evidence ID 序列为 `bili-007`、`bili-005`、`bili-003`、`bili-007`；底层 `EvidenceSet` 按首次出现去重为三条。零文章返回合法空 snapshot，未命中主要行动的负面记录确定性进入人工复核回退。
- SQL/事实小步单次检查：新模块与 PostgreSQL repository 静态编译、`git diff --check`、三个 SQL 绑定参数各出现一次，以及 recommendations 单元/真实 fixture PostgreSQL 集成测试共 7 项通过。pytest 仅提示沙箱无法写 `.pytest_cache`，不影响测试结果；本小步尚未接 runner、stub、CLI 或 PDF。
- 规格小步单次检查：变更范围仅为逐章规格、设计决定与状态文档；`git diff --check`、唯一 `recommendations` 章节、唯一 D-36，以及固定 SQL/共享代码本/最多四项/确定性优先级/真实证据/无图表/一次 narrator/no-data/无 RAG/无外部执行合同均通过。未修改实现、fixtures 或 n8n，也未重复运行刚在 main CI 通过的 317 项测试。
- `RecommendationsSectionRunner`、确定性中英文 stub、运行时注册和 standalone 评审配置已接通；存在负面记录时恰好一次 narrator 操作，零文章为 `no_data`、非空零负面为无 narrator 的常规监测结论。runner 逐项校验固定优先级、角色、时限、动作、核验文本、触发事实、代表原文和可重复 Evidence ID，并拒绝未知/乱序/改写引用。
- recommendations-only 真实 fixture CLI bundle 为 1 章 complete、0 failed、0 图表，meta 显示 12 篇、负面占比 58.3%；正文按 `bili-007`、`bili-005`、`bili-003`、`bili-007` 顺序呈现四项行动，并明确建议角色、人工审核和无自动外部执行边界。
- 产物小步单次阶段检查：`git diff --check`、全仓 Python 静态编译、`pip check`、健康 fixture PostgreSQL 下完整 pytest 330 项、真实 CLI bundle 与 Poppler A4 检查均通过。PDF 为两页，逐页原图复核无中文乱码、截断、重叠、Markdown 泄漏或孤立标题；第二页完整承载第 4 项、人工审核边界和方法说明。
- 本小步未实现 RAG、未修改或激活 n8n，也未调用真实模型 API；真实 API 仍只留到全部本地功能完成后的最终凭据门控冒烟。

## M2 `timeline` 阶段入口

- 产品框架只把 `timeline` 定义为“用峰值和代表性内容还原事件阶段”；任务书没有给出里程碑选择算法、阶段命名、点数上限、图表或退化行为，这些都必须明确标为项目自主设计，而不是面试方原始要求。
- 本阶段坚持固定 SQL + Python 确定性计算 + 可审计 Evidence ID：模型最多做一次受约束叙述，不生成 SQL、不选择事实、不推断因果，也不把时间先后包装成因果关系。
- 下一小步只做 schema/fixture 预查与规格决策；实现前必须定义首次收录、峰值日代表、明确标记的官方回应、最后收录之间的去重/排序/上限，以及无数据、单点、同日多点和缺少官方回应时的行为。
- 本阶段不实现或暗示 RAG，不修改 n8n 工作流，不调用真实模型 API；开发与 CI 继续使用可注入 stub，真实 API 留到全部本地功能完成后的最终冒烟测试。
- schema 审计确认时间线可使用真实 `published_at`、结构化 `tags`、情感和四类非负互动计数；`official-response` 只作为精确标签信号，不足以独立验证发言者身份、权威性或回应效果。
- `docs/02-report-spec.md` 与 D-28 已定义 `timeline.v1`：最多选择首次收录、最早回应标签记录、峰值日最高互动代表和最后收录四个角色，同一 Evidence ID 合并角色后按时间排序；不推断因果、不使用 RAG，并完整规定无数据、单点、同日和缺少回应标签的退化行为。
- fixture 预查得到 12 篇范围内记录、峰值日 2026-03-20 共 3 篇；四个角色依次命中 `bili-001`、`bili-006`、`bili-007`、`bili-012`，与规格的排序和去重口径一致。
- 规格小步第一次检查：`git diff --check`、必需合同段、唯一 `timeline` 章节、唯一 D-28、仅文档改动均通过；真实 PostgreSQL 候选查询精确返回上述四个 Evidence ID。
- 规格小步第二次检查：项目 `.venv` 在健康 fixture PostgreSQL 下完整 pytest 180 项通过；`pip check` 无破损依赖。未修改实现、fixtures、RAG 或 n8n，也未调用真实模型 API。
- 固定 `timeline.sql`、`PostgresTimelineRepository`、角色行/去重里程碑模型、`EvidenceSet` 和 `FactSet` 已实现；查询只绑定 tag、半开时间边界与时区，最多返回四个固定角色，Python 按真实 Evidence ID 合并并验证完整角色顺序与重复记录字段一致性。
- 时间线事实包含范围内 12 篇、峰值日 3/20 共 3 篇、回应标签记录 1 篇、4 个里程碑和首末收录跨 7 个自然日；峰值日代表 `bili-007` 的存储互动计数和为 10,020，所有里程碑事实保留来源 ID。
- SQL/事实小步第一次检查：`git diff --check`、Python 静态编译、四个 SQL 绑定参数各出现一次、预期文件范围和 timeline 专属单元测试 5 项通过。
- SQL/事实小步第二次检查：健康 fixture PostgreSQL 下 timeline 集成测试 2 项通过，完整 pytest 187 项通过；`pip check` 无破损依赖。空话题返回合法 `no_data` snapshot；本小步未接 runner/图表、RAG、n8n 或真实模型 API。
- `TimelineChartBuilder`、fault-isolated `TimelineSectionRunner`、确定性中英文 stub、运行时注册和专属图片 alt 已接入；正常路径恰好一次 narrator 操作，引用乱序、原文/角色/时间/平台/情感改写以及未知 Evidence ID 均安全失败，no-data 不出图也不调用 narrator。
- timeline-only CLI 验收得到 1 章 complete、0 章 failed、1 张 150 dpi 图和 A4 单页 PDF；Markdown 按 `bili-001`、`bili-006`、`bili-007`、`bili-012` 顺序保留原始标题、摘要和 Evidence ID，页面目视无中文乱码、截断、重叠或图例遮挡。
- 任意组合验收发现旧 assembler 在未选择 `metrics` 时把 `meta.stats.articles` 误写为 0；D-29 已改为逐字段从用户实际选择章节的可审计事实解析。最终 timeline-only `stats` 为 articles 12、negativeRatio `暂无`、peakDay `3/20`，不插入未选章节也不伪造缺失负面占比。
- 产物小步第一次检查（修订后）：`git diff --check`、Python 静态编译、唯一运行时注册、唯一 narrator 调用点和 timeline/assembler 聚焦测试 16 项通过。
- 产物小步第二次检查（修订后）：健康 fixture PostgreSQL 下 timeline SQL + CLI 聚焦集成测试 3 项通过，完整 pytest 196 项通过，`pip check` 无破损依赖；最终 v2 PDF 渲染页与目视通过的 v1 逐像素一致。本小步未实现 RAG、修改 n8n 或调用真实模型 API。

## M1 标准默认配置阶段入口

- 任务书明确要求 `examples/report-config.csuite.json` 一条命令生成中文 csuite 七章报告，并要求 csuite 7 章与 pr 11 章两种默认配置均可生成；这两份文件名和章节数是本阶段的固定验收目标。
- 两份配置必须使用同一公共 `ReportConfig` 契约和相同 fixture 话题/日期，不复制引擎代码；章节顺序采用已经记录的 csuite 七章与 PR 在其后追加四章的项目自主默认组合。
- 本阶段只补配置、回归测试、README/追踪证据与真实 stub CLI/PDF 验收，不开始 M2、RAG、M3、真实模型调用或 n8n 修改。
- `examples/report-config.csuite.json` 与 `examples/report-config.pr.json` 已创建；两份均保留完整 19 章及三个禁用专属输入形状，只分别启用严格有序的 7/11 章，`reportType` 分别为 `csuite`/`pr`。
- 默认配置聚焦 5 项测试验证公共契约解析、19 ID 顺序、7/11 enabled 计划、三个禁用输入形状，以及两份配置各自生成完整有序 bundle；全部通过。
- 实际标准 CLI 的 csuite 产物为 7 章 complete、0 章 failed、5 张图、A4 四页；PR 产物为 11 章 complete、0 章 failed、9 张图、A4 七页。两者 `meta.reportType`、章节数、图表文件数和 PDF 文件均与配置一致。
- PR 默认产物 7 页与已逐页验收的 media-social 最终产物逐像素一致；csuite 前 3 页与同源 PR 前缀一致，第 4 页因报告在 risk 后结束而包含方法说明，单独复核无中文乱码、截断、重叠、图例遮挡或孤页。
- 默认配置小步第一次检查：两份 JSON 可解析、各含完整 19 ID、执行计划严格为 7/11 章、`git diff --check` 和聚焦 5 项测试通过。
- 默认配置小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 180 项通过；`pip check` 无破损依赖，两条标准 stub CLI 与 PDF 视觉验收通过。

## M1 `media-social` 阶段入口

- 任务书要求固定 SQL、Python 计算、统一图表、每章节至多一次 narrator、数字可追溯和章节级容错；`media-social` 的 B 端媒体/C 端社交划分与比较口径属于本项目自主设计，必须在编码前写入 `docs/02-report-spec.md` 和设计决定。
- 产品框架只把本章定义为“B 端媒体和 C 端社交内容的量级与情感差异”，没有提供平台分组映射、混合平台处理、样本量阈值、证据或图表细节；下一规格小步必须先核对 schema 与 fixtures，不能把平台名称的主观猜测静默写进 SQL。
- 本阶段不使用 RAG 或 n8n，不引入真实 API 调用；开发与 CI 使用可注入 stub，最终真实模型只做凭据门控的冒烟测试。
- schema 审计确认 `articles.source_type` 是受数据库约束的 `media` / `social` 字段，因此本章直接使用存储分类，不按平台名、作者或文本猜测；面向用户显示为“媒体内容/社交内容”，不扩张解释为 B2B/C 端人群或作者身份。
- `docs/02-report-spec.md` 已定义固定两行聚合、文章量/情感构成、两组均有样本时的社交减媒体负面占比差、双面板 150 dpi 图、一次 narrator、无 EvidenceSet 和 no-data/单组缺失/零负面行为。
- D-27 要求同时显示绝对量与组内构成，并把缺失组标记为“无样本/不可比较”，禁止将其伪装成 0% 负面或由模型补分类。
- fixture 口径预查得到媒体 3 篇（正/中/负 1/1/1，负面 33.3%，总量占 25.0%）与社交 9 篇（1/2/6，负面 66.7%，总量占 75.0%）；社交负面占比较媒体高 33.3 个百分点，7 篇负面中媒体/社交分别占 14.3%/85.7%。该预查只校准规格，尚未构成实现证据。
- 规格小步第一次检查：必需规格段、`media-social.v1`、存储分类、绝对量/组内构成、单组无样本、一次 narrator、无 EvidenceSet/RAG/n8n 边界、D-27、schema 约束和 `git diff --check` 全部通过；未修改实现、fixtures 或 n8n。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 160 项通过；`pip check` 无破损依赖。
- 固定 `media_social.sql`、`PostgresMediaSocialRepository`、`MediaSocialRow`、`MediaSocialSnapshot` 和可追溯 `FactSet` 已实现；查询无论有无数据都按固定顺序返回 `media`、`social` 两行，并校验行合计与查询总计一致。
- Python 校验 source type、情感加总、平台覆盖和两行顺序；分别保留文章占比、组内情感占比、负面总体来源占比、量级并列和两组均有样本时的负面占比差。单组缺失时不生成该组情感百分比、差值或假赢家；两组零负面仍是合法可比较并列。
- fixture 集成测试正式验证媒体/社交文章数 3/9、正面 1/1、中性 1/2、负面 1/6、平台数 1/3、组内负面 33.3%/66.7% 和差值 `+33.3 个百分点`；空话题仍返回两行显式零值并判定 `no_data`。
- SQL/事实小步第一次检查：Python 静态编译、恰好三个 SQL 绑定参数、`git diff --check` 以及 media-social 单元/真实数据库专属测试 7 项通过。
- SQL/事实小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 167 项通过；`pip check` 无破损依赖。
- `MediaSocialChartBuilder`、fault-isolated `MediaSocialSectionRunner`、确定性中英文 stub、运行时接线、专属图片 alt 和十一章节评审示例已实现；本章不传文章证据，只执行一次 narrator 操作。
- 图表/runner/CLI 聚焦 18 项测试验证双面板绝对量与 100% 组内构成、150 dpi、两组 `n`、单组无样本、叙述事实校验、no-data 跳过，以及 query/calculation/chart/LLM 安全失败隔离；全部通过且无布局 warning。
- 实际 CLI 产物为 11 章 complete、0 章 failed、9 张图表；正文准确披露媒体/社交 3/9 篇与 25.0%/75.0%，组内负面 1/3（33.3%）与 6/9（66.7%），以及社交减媒体 `+33.3 个百分点`。
- 正文明确分类直接来自数据库 `source_type`，结果只描述本次收录内容，不代表受众人群、差异原因或完整媒体生态；未引入 RAG、平台名推断、外部知识或 n8n。
- 首次 PDF 为 A4 八页，但第 8 页只有通用方法说明，构成孤页；缩短新图表高度后重新生成，最终为 A4 七页。逐页与图表原图复核确认 media-social 正文、双面板图和方法说明完整位于第 7 页，无中文乱码、截断、重叠、图例遮挡、比例失真或孤页。
- 图表/runner 小步第一次检查：Python 静态编译、十一章节配置顺序、唯一 media-social narrator 调用点、`git diff --check` 和聚焦 18 项测试通过。
- 图表/runner 小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 175 项通过；`pip check` 无破损依赖，实际十一章节 bundle 与七页 PDF 验收通过。

## M1 `engagement` 阶段入口

- 任务书要求固定 SQL、Python 计算、统一图表、每章节至多一次 narrator、数字可追溯和章节级容错；`engagement` 的具体统计口径属于本项目自主设计，编码前必须先写入 `docs/02-report-spec.md`。
- 框架将本章定义为点赞、评论、转发、收藏和高互动内容；当前 schema/fixture 能否可靠支持各字段、去重、排名与证据披露，须在规格小步中核对后记录决定，不能先写代码再补口径。
- 本阶段不使用 RAG 或 n8n，不引入真实 API 调用；开发与 CI 使用可注入 stub，最终真实模型只做凭据门控的冒烟测试。
- `docs/02-report-spec.md` 已定义存储互动计数快照、四类构成、评论+转发占比、单篇/前三篇集中度、最多五篇图表行、最多三篇真实证据、一次 narrator、全零 complete 分支和失败隔离。
- D-26 明确四类异质计数的简单求和只是可审计的运营快照；没有曝光、粉丝、独立用户或互动发生时间，因此不得声称互动率、真实触达、支持度、传播因果或互动时间趋势。
- 固定排名按总互动降序、发布时间降序、ID 升序；所有最高值并列必须披露。图表左侧展示四类计数与份额，右侧按真实情感颜色展示最多五篇高计数内容，并以 source record ID 和原始标题标识；前三篇进入 EvidenceSet。
- fixture 口径预查得到 12 篇、总互动 26,170，赞/评/转/藏为 15,460/4,705/4,620/1,385，评论+转发占 35.6%；最高单篇占 38.3%，前三篇占 59.1%，前三篇为 `bili-007`、`bili-005`、`bili-010`。该预查只校准规格，尚未构成实现证据。
- 规格小步第一次检查：必需规格段、`engagement.v1`、最高值并列、最多五篇图表行、最多三篇真实证据、一次 narrator、全零 complete 分支、无互动率/RAG/n8n 越界、D-26 和 `git diff --check` 全部通过。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 146 项通过；`pip check` 无破损依赖。
- 固定 `engagement.sql`、`PostgresEngagementRepository`、`EngagementRecord`、`EngagementSnapshot`、可追溯 `FactSet` 和前三篇真实 `EvidenceSet` 已实现；SQL 始终返回一个聚合快照并只带最多五条正互动记录。
- Python 校验文章数、正互动/零互动分区、四类聚合、连续确定性排名、最高值并列、展示记录不超过聚合和零互动分支；每条展示事实携带真实 source record ID，前三条进入 EvidenceSet；即使六篇以上并列也保留完整并列数而不伪造单一来源。
- fixture 集成测试正式验证 12 篇、赞/评/转/藏 15,460/4,705/4,620/1,385、总互动 26,170、唯一最高值和前五顺序 `bili-007`、`bili-005`、`bili-010`、`bili-001`、`bili-011`，并验证空话题返回合法空 snapshot。
- FactSet 保留未四舍五入的四类份额和集中度，仅显示为评论+转发 35.6%、最高单篇 38.3%、前三篇 59.1%；前三篇 Evidence ID 为 `bili-007`、`bili-005`、`bili-010`。
- SQL/事实小步第一次检查：Python 静态编译、恰好三个 SQL 绑定参数、`git diff --check` 以及 engagement 单元/真实数据库专属测试 8 项通过。
- SQL/事实小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 154 项通过；`pip check` 无破损依赖。
- `EngagementChartBuilder`、fault-isolated `EngagementSectionRunner`、确定性中英文 stub、运行时接线、专属图片 alt 和十章节评审示例已实现；正互动路径只调用一次 narrator，全零互动路径不生成图表、证据或模型成本。
- 图表/runner 专属 17 项测试验证双面板 150 dpi 图表、四类精确计数与占比、最多五篇情感着色内容、最高值并列、Evidence ID/标题/四项计数验证、全零 complete，以及 query/calculation/chart/LLM 安全失败隔离；全部通过且无布局 warning。
- 实际 CLI 产物为 10 章 complete、0 章 failed、8 张图表；互动正文准确披露总互动 26,170，赞/评/转/藏 15,460/4,705/4,620/1,385，评论+转发 9,325（35.6%），最高单篇 `bili-007` 10,020（38.3%），前三篇合计 59.1%，并按序引用 `bili-007`、`bili-005`、`bili-010` 的真实标题与计数。
- 正文明确这些是跨平台存储的原始计数快照，缺少曝光量和独立用户分母，不代表互动率、真实触达或支持度；未引入 RAG、外部知识或 n8n。
- PDF 经 Poppler 验证为 A4 七页。逐页和 engagement 图表原图视觉检查确认正文位于第 6 页、完整双面板图及方法说明位于第 7 页；无孤立章节标题、中文乱码、截断、重叠、图例遮挡或长标题裁切。第 7 页留白来自保持图表整体。
- 图表/runner 小步第一次检查：Python 静态编译、十章节配置顺序、唯一 engagement narrator 调用点、`git diff --check` 和 runner/图表/CLI 聚焦 9 项测试通过。
- 图表/runner 小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 160 项通过；`pip check` 无破损依赖，实际十章节 bundle 与七页 PDF 验收通过。

## M1 `keywords` 规格切片

- `docs/02-report-spec.md` 已定义标题/摘要固定查询、NFKC 标准化、3–6 字重复短语、相同来源集合的嵌套折叠、文档覆盖率、后半期新增阈值、堆叠情感图、一次 narrator 和两类 no-data 行为。
- D-25 要求短语至少覆盖两篇不同文章，负面文章数不参与排名；只有在前半期零出现且后半期至少覆盖两篇时才标记“后期新增”，并用可审查横向条形图替代不稳定词云。
- 每个短语事实必须携带真实 source record ID；narrator 只接收批准的短语与数字，不接收自由证据，不得创造语义主题名、原因或受众意图。本章节不使用 RAG 或 n8n。
- fixture 口径预查得到 6 个重复短语：`不喜欢`、`入口调整`、`反馈机制`、`控制感`、`透明度`、`负反馈入口`，均覆盖 2/12 篇；没有短语满足后半期至少两篇且前半期零出现的新增阈值。该预查只校准规格，尚未构成实现证据。
- 规格小步第一次检查：必需规格段、`keywords.v1`、短语阈值/嵌套折叠、source record ID、无词云、一次 narrator、两类 no-data、无 RAG 边界、D-25 和 `git diff --check` 全部通过。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 134 项通过；`pip check` 无破损依赖。
- 固定 `keywords.sql`、`PostgresKeywordsRepository`、`KeywordSourceRecord`、`KeywordPhrase`、`KeywordsSnapshot` 和可追溯 `FactSet` 已实现；SQL 只做 tag/完整日期过滤，短语提取与排名完全由 Python 负责。
- Python 对标题/摘要做 NFKC 标准化和 3–6 字/ASCII token 提取，同一文章只计一次；至少两篇才保留，相同来源集合保留最长嵌套短语，按文档数/标题文档数/首次日期/词面排序，最多显示八项。
- SQL/事实小步第一次检查：Python 静态编译、恰好四个 SQL 绑定参数、`git diff --check` 以及 keywords 单元/真实数据库专属测试 7 项通过。
- SQL/事实小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 141 项通过；`pip check` 无破损依赖。
- fixture 集成测试正式验证 12 篇内容、短语顺序 `不喜欢`、`入口调整`、`反馈机制`、`控制感`、`透明度`、`负反馈入口`，文档数均为 2，负面文档数为 `[2, 1, 2, 2, 2, 2]`，且无“后期新增”短语；空话题返回合法空 snapshot。
- FactSet 将 2/12 文档覆盖率显示为 16.7%，保留所有短语的未四舍五入占比、情感文档数、首末日期、后期新增标签和真实 supporting source record IDs；6 项并列第一被完整披露。
- `KeywordsChartBuilder`、fault-isolated `KeywordsSectionRunner`、确定性中英文 stub、运行时接线、专属图片 alt 和九章节评审示例已实现；本章使用空 `EvidenceSet`，只执行一次 narrator 操作。
- 图表/runner 专属 15 项检查验证横向堆叠情感构成、150 dpi、并列覆盖量、完整标签、无数据跳过，以及 query/calculation/chart/LLM 安全失败隔离；全部通过。
- 实际 CLI 产物为 9 章 complete、0 章 failed、7 张图表；正文准确披露 12 篇、6 个重复短语、6 项以 2 篇并列第一、`入口调整` 的 2 篇/16.7% 覆盖和 1/2 负面构成，并明确没有达到阈值的后期新增短语，不宣称语义聚类或支持度。
- PDF 经 Poppler 验证为 A4 六页。第一次产物检查确认 `meta.json`、Markdown 与 7 张图一致；第二次逐页和图表原图视觉检查确认关键词正文位于第 5 页、完整图表及方法说明位于第 6 页，无孤立标题、中文乱码、截断、重叠、图例遮挡或标签裁切。第 6 页留白来自保持图表整体。
- 图表/runner 小步第一次检查：Python 静态编译、九章节配置契约、唯一 keywords narrator 操作、`git diff --check` 和专属 15 项测试通过。
- 图表/runner 小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 146 项通过；`pip check` 无破损依赖，实际九章节 bundle 与六页 PDF 验收通过。

## M1 `sentiment-evolution` 规格切片

- `docs/02-report-spec.md` 已定义完整日历序列、最多三个平衡阶段、阶段情感构成、首末有效阶段比较、100% 堆叠图、一次 narrator 和 no-data/failed 行为。
- D-24 将本章与绝对量 `trend` 明确分工：情感演变只比较构成，所有百分比必须同时显示阶段样本量；负面占比变化达到正负 10 个百分点才标记上升/下降。
- 本章节只使用结构化日级情感计数，不使用文章证据、RAG 或 n8n，也不得解释情感变化原因。
- fixture 口径预查确认 7 日按 3/2/2 分为前/中/后期：情感计数分别为正/中/负 `1/2/3`、`1/1/2`、`0/0/2`，负面占比为 50.0%、50.0%、100.0%。后期增至 100.0% 但只有 2 篇，必须与热度变化分开解释。该预查只校准规格，尚未构成实现证据。
- 规格小步第一次检查：必需规格段、`sentiment-evolution.v1`、平衡阶段规则、样本量披露、10 点阈值、一次 narrator、无证据/RAG/n8n 边界、D-24 和 `git diff --check` 全部通过。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 121 项通过；`pip check` 无破损依赖。
- 固定 `sentiment_evolution.sql`、`PostgresSentimentEvolutionRepository`、`DailySentimentPoint`、`SentimentPhase`、`SentimentEvolutionSnapshot` 和可追溯 `FactSet` 已实现；空话题仍返回完整七日日历与三段零值阶段。
- Python 将任意完整日历确定性切为最多三个平衡阶段，保留零量阶段，并只比较首末有效阶段；单一有效阶段返回“仅单阶段有数据”，不伪造趋势。
- SQL/事实小步第一次检查：Python 静态编译、恰好六个 SQL 绑定参数、`git diff --check` 以及 sentiment-evolution 单元/真实数据库专属测试 7 项通过。
- SQL/事实小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 128 项通过；`pip check` 无破损依赖。
- fixture 集成测试正式验证阶段日数 `[3, 2, 2]`、样本量 `[6, 4, 2]`、正/中/负计数 `[(1,2,3), (1,1,2), (0,0,2)]`，以及负面占比变化 `+50.0 个百分点`。
- FactSet 同时携带每阶段日期范围、样本量、三类计数/占比、首末有效阶段、未四舍五入差值和“负面占比上升”方向，避免把后期 2 篇的 100.0% 误读为绝对热度上升。
- `SentimentEvolutionChartBuilder`、fault-isolated `SentimentEvolutionSectionRunner`、确定性中英文 stub、运行时接线、专属图片 alt 和八章节评审示例已实现；本章使用空 `EvidenceSet`，只执行一次 narrator 操作。
- 图表/runner 专属 16 项检查验证 150 dpi、规定情感颜色、阶段日期与样本量、全零 no-data 跳过、单有效阶段不虚构比较，以及 query/calculation/chart/LLM 安全失败隔离。
- 纵向接线后真实 fixture PostgreSQL 下完整 pytest 为 134 项通过；`pip check` 无破损依赖。
- 真实 CLI 产物为 8 章 complete、0 章 failed、6 张图表；情感演变正文准确显示前期 6 篇/负面 50.0%、后期 2 篇/负面 100.0%、变化 `+50.0 个百分点`，并明确构成变化不等于讨论量上升或热度回升。
- PDF 经 Poppler 验证为 A4 五页。首次页图检查发现新图表图例压在红色柱体上；移至图外并将日期范围统一为 ASCII 连字符后重新生成，前四页逐像素未变化，第五页与图表原图复核无中文乱码、截断、重叠、图例遮挡或孤立标题。
- 图表/runner 小步第一次检查：Python 静态编译、`git diff --check`、唯一 narrator 操作和专属 16 项测试通过。
- 图表/runner 小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 134 项通过，`pip check` 无破损依赖，实际 8 章节 bundle 与五页 PDF 视觉验收通过。

## M1 `viewpoints` 规格切片

- `docs/02-report-spec.md` 已定义真实标题/摘要证据、每种情感最多两条、第二条优先跨平台的固定选择规则、人口情感占比与代表性样本分离、一次 narrator、引用验证以及 no-data/failed 行为。
- D-23 要求观点样本不得冒充主题流行度；所有观点条目必须显示真实 Evidence ID，并原样保留批准的标题和摘要。
- 本切片是非 RAG 的 M1 确定性基线，不使用 embedding、vector store、reranker 或 n8n；未来若经用户批准引入 D-17 检索器，仍必须保持 EvidenceSet 和引用验证契约。
- fixture 口径预查预计选择负面 `bili-007`/`bili-001`、中性 `bili-008`/`bili-002`、正面 `bili-010`/`bili-006`，同时披露总体情感计数 7/3/2。该预查只校准规格，尚未构成 `viewpoints` 实现证据。
- 规格小步第一次检查：必需规格段、`viewpoints.v1`、一次 narrator、真实 EvidenceSet、代表性样本披露、引用验证、无 RAG/n8n 边界、D-23 和 `git diff --check` 全部通过。
- 规格小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 111 项通过；`pip check` 无破损依赖。
- 固定 `viewpoints.sql`、`PostgresViewpointsRepository`、`ViewpointsSnapshot`、`ViewpointEvidenceRecord`、可追溯 `FactSet` 和真实字段 `EvidenceSet` 已实现；空话题返回合法空 snapshot。
- 查询一次返回总体情感计数和最多六条证据；每种情感先选互动最高记录，第二条存在时优先选择不同平台，再按互动、时间和 ID 确定性排序，不使用 RAG。
- SQL/事实小步第一次检查：Python 静态编译、恰好三个 SQL 绑定参数、`git diff --check` 以及 viewpoints 单元/真实数据库专属测试 6 项通过。
- SQL/事实小步第二次检查：真实 fixture PostgreSQL 下完整 pytest 117 项通过；`pip check` 无破损依赖。
- fixture 集成测试正式验证总体负面/中性/正面计数 7/3/2，证据顺序为 `bili-007`、`bili-001`、`bili-008`、`bili-002`、`bili-010`、`bili-006`，并验证同类第二条来自不同平台及空话题行为。
- FactSet 保留未四舍五入情感占比并仅显示为负面 58.3%、中性 25.0%、正面 16.7%；`evidenceCount` 携带全部六个真实 source record ID，证据样本计数与总体占比保持分离。
- `ViewpointsSectionRunner`、确定性中英文 stub、运行时接线和七章节 csuite 评审示例已实现；本章节不生成重复情感图表。
- narrator 每章只调用一次；runner 要求全部六个 Evidence ID 按批准顺序各出现一次，并原样保留每条标题和摘要。未知、缺失、重排引用或篡改原文使本章安全进入 `failed`。
- viewpoints 数据/runner、PDF renderer 与 CLI 专属回归 15 项通过；验证 no-data、query/calculation/LLM 隔离、引用校验、七章配置顺序和 PDF 三级标题渲染。
- 纵向接线后真实 fixture PostgreSQL 下完整 pytest 121 项通过；`pip check` 无破损依赖。
- 真实 CLI 产物为 7 章 complete、0 章 failed、5 张图表；观点正文显示总体 7/3/2 情感计数与 58.3%/25.0%/16.7% 占比、代表性样本免责声明和六个批准 Evidence ID。
- 首次 PDF 视觉检查发现三级标题以原始 `###` 文本显示；ReportLab renderer 增加通用 subsection 样式并加入回归测试。最终 PDF 经 Poppler 验证为 A4 四页，逐页复核未发现 Markdown 标记泄漏、中文乱码、截断、重叠、标签遮挡或孤页。
- runner/产物小步第一次检查：七章节配置契约、Python 静态编译、唯一 narrator 操作、三级标题渲染和 `git diff --check` 通过。
- runner/产物小步第二次检查：健康 fixture PostgreSQL 下完整 pytest 121 项通过；`pip check` 无破损依赖。

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
