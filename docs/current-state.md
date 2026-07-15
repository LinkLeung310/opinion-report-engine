# Current Project State

最后核对日期：2026-07-15  
最后实现基线：`main@3448aa3`（PR #12，auditable media-social analysis）

本文件只记录已验证事实。任务要求以原始任务书为准，长期规则以根目录 `AGENTS.md` 为准。

## 已验证完成

- 固定 `ReportConfig` 的严格解析、未知 `reportType` 回退和 enabled 章节顺序规划。
- 19 个章节 ID 注册表；中文 csuite 的 `verdict`、`metrics`、`trend`、`viewpoints`、`platforms`、`severity` 与 `risk` 七章，以及 PR 版新增的 `sentiment-evolution`、`keywords`、`engagement`、`media-social` 已完成 stub 模式端到端实现。
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
- `main@1ee06f4` 的 GitHub CI：146 项测试通过（run `29420845303`）。
- `main@9e157c5` 的 GitHub CI：160 项测试通过（run `29423229549`）。
- `main@3448aa3` 的 GitHub CI：175 项测试通过（run `29424655431`）。
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
- M2 未开始：其余章节、3 类章节专属输入的完整行为、英文和任意组合未完成。
- 真实 OpenAI-compatible narrator 未实现；真实模型未做冒烟验证。
- RAG 未实现：没有 embedding、vector store、retriever、reranker 或检索质量评测；现有 Evidence ID 引用验证属于非 RAG 的确定性证据边界。RAG 只在 `AGENTS.md` 和 D-17 中定义计划边界。
- M3 未开始：FastAPI、任务队列、并发隔离、状态和下载接口均不存在。
- n8n 不能端到端运行，因为其调用的 M3 API 尚不存在；不得激活或声称集成完成。
- `CatalogPublisher` / `index.json` 列表更新尚未实现。
- gold-report 视觉资产和完整默认配置尚未交付。

## 已知文档差异

- 任务书描述 fixtures 为真实历史话题数据，但仓库没有收到可发布的原始 fixtures；本项目根据 D-15 提供合成、确定性数据。对外必须明确“合成 fixture”，不得称为真实历史记录。
- 任务书引用的 `docs/02-report-spec.md` 和 gold-report HTML/CSS 没有作为原始附件进入当前仓库；section spec 由本项目逐步定义。用户另行提供的参考 PDF 用于视觉理解，但仓库内 gold-report 资产仍待交付。
- 任务书建议 Playwright/WeasyPrint；当前根据 D-16 使用 ReportLab + 内嵌字体，并已记录和测试该偏离。

## 当前范围约束

context recovery、完整中文 csuite 七章与 PR 版 `sentiment-evolution`、`keywords`、`engagement`、`media-social` slice 已经合并。当前分支 `codex/m1-default-configs` 从绿色 `main@3448aa3` 创建；下一阶段交付任务书指定文件名的两份标准默认配置并执行 M1 精确命令验收。用户要求暂不开始 RAG，因此不会新增 embedding、vector store、retriever 或 reranker；n8n 继续保持 Draft/inactive，等待 M3 API。

## Context recovery 规则强化小步

- 根目录继续使用 Codex 自动识别的标准文件名 `AGENTS.md`，不另建内容重复的 `agent.md`；它是所有新会话和上下文压缩后的唯一治理入口。
- `AGENTS.md` 已明确整理任务书、产品框架、引擎架构、逐章规格、设计决定、追踪矩阵和当前状态的文档职责，避免把项目自主设计误称为面试方要求，也避免在多处复制 19 章细节。
- RAG 继续冻结为计划边界，未开始 embedding、vector store、retriever、reranker 或检索评测；n8n 继续是 Draft/inactive 的 M3 API 可视化编排层，本小步没有修改本机工作流或导出 JSON。
- Git 闭环已写清：每步从规则恢复上下文、限定一个意图、做两轮检查、更新本文件、选择性提交并 push；阶段完成后才走 Draft PR/CI/merge，合并后的下一阶段必须从最新绿色 `main` 新建分支。
- 真实模型 API 只在全部本地功能与自动化验证完成后做凭据门控的最终冒烟测试；开发与 CI 使用可注入 stub/fake。
- 第一次检查（静态与一致性）：`git diff --check` 通过；`AGENTS.md` 引用的 7 份框架/状态文档全部存在，RAG 延期、n8n Draft 边界、每步两轮检查、GitHub push 和最终 API 冒烟规则均可定位；`n8n/` 无变更。
- 第二次检查（可执行回归）：真实 fixture PostgreSQL 下完整 pytest 160 项通过；`python -m pip check` 无破损依赖。

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

- PR #12 已合并，`main@3448aa3` 的独立 CI 已通过 175 项测试；当前分支 `codex/m1-default-configs` 已从该绿色基线创建。
- 中文 csuite 七章与 PR 十一章的纵向实现均已合并；下一小步创建 `examples/report-config.csuite.json` 与 `examples/report-config.pr.json`，并围绕任务书原命令增加端到端验收。
- 新分支第一次检查：分支与 `main@3448aa3` 基线、PR #12、175 项 main CI、两份固定配置文件名、RAG 延期和 n8n Draft 边界一致，`git diff --check` 通过；工作区只修改本状态文件。
- 新分支第二次检查：健康 fixture PostgreSQL 下完整 pytest 175 项通过；`pip check` 无破损依赖。
- 真实 OpenAI-compatible narrator 只在最后做凭据门控的冒烟验证；开发与 CI 继续使用 stub。
- RAG 继续延期，不在当前 M1 默认配置阶段实现；n8n 保持 Draft，等待 M3 API。

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
