# 舆情报告生成引擎：最终版框架

> 本框架以任务书的固定契约为边界，以用户体验为核心。任务书未提供的章节规范、fixtures、示例配置、报告样式和目录发布逻辑均由我们设计并作为项目产物交付。

## 1. 要解决的问题

引擎接收唯一输入 `report-config.json`，按用户启用的章节和顺序查询 PostgreSQL、计算事实、生成图表、调用大模型撰写叙述，最终输出固定报告包：

```text
ReportConfig
  → 配置校验与执行计划
  → 各章节独立执行
  → 报告组装
  → Markdown / charts / meta.json
  → A4 PDF
  → out/{id}/
```

核心交付是可独立运行的 Python 引擎。CLI 是 M1/M2 的入口，FastAPI 是 M3 的适配层；n8n 只在 M3 后调用 API 做可视化触发、轮询和演示，不成为核心运行依赖。

## 2. 不可更改的输入契约

使用 Pydantic 定义 `ReportConfig`，字段保持任务书原样：

```text
reportType
language
topic.tag
topic.displayName
topic.eventTitle
dateRange.from / dateRange.to
sections[]: id / enabled / input
```

规则：

- 未知 `reportType` 标准化为 `csuite`，并在内部记录 warning。
- `language` 只接受 `zh` 或 `en`。
- 只渲染 `enabled: true` 的章节，严格保持数组顺序。
- 未知章节 ID 是全局配置错误，因为任务书只规定了 `reportType` 的回退行为。
- 全局字段错误会拒绝整个任务。
- 已知章节缺少其专属输入时，仅该章节标记缺失。
- 日期暂按 `[from 00:00, to + 1 day 00:00)` 处理，以包含完整结束日；最终时区服从 fixture 数据库约定。

### 章节产品设计

前端采用“模板起步 + 自定义”：用户先选择决策版或公关版，再自由增删、排序章节；需要额外输入的章节在启用时展开对应表单。

| 顺序 | ID | 用户看到的章节 | 核心分析 |
|---:|---|---|---|
| 1 | `verdict` | 核心结论 | 用确定性事实给出事件判断、关键变化和风险结论 |
| 2 | `metrics` | 全网数据概览 | 总量、情感、平台、互动和数据覆盖情况 |
| 3 | `trend` | 热度趋势 | 日/小时传播量、峰值和生命周期变化 |
| 4 | `viewpoints` | 主要观点 | 基于真实标题与摘要归纳支持、中性和反对观点 |
| 5 | `platforms` | 平台表现 | 各平台文章量、占比、情感和互动差异 |
| 6 | `severity` | 负面严重程度 | 负面等级、严重性分布和高风险内容 |
| 7 | `risk` | 风险评估 | 传播、情绪、持续时间、高管关联和谣言等维度 |
| 8 | `sentiment-evolution` | 情感演变 | 情感随时间和传播阶段的变化 |
| 9 | `keywords` | 关键词与话题 | 高频词、核心话题和新出现议题 |
| 10 | `engagement` | 互动传播 | 点赞、评论、转发、收藏和高互动内容 |
| 11 | `media-social` | 媒体与社媒对比 | B 端媒体和 C 端社交内容的量级与情感差异 |
| 12 | `timeline` | 事件时间线 | 用峰值和代表性内容还原事件阶段 |
| 13 | `top-content` | 代表性内容 | 真实高互动/高风险文章及其影响 |
| 14 | `negative-themes` | 负面议题拆解 | 负面摘要中的主要原因、诉求和风险主题 |
| 15 | `spread-path` | 传播路径 | 话题如何在平台与时间之间扩散 |
| 16 | `response` | 回应效果 | 根据 `responseDate` 比较回应前后热度与情感 |
| 17 | `benchmark` | 历史对标 | 根据 `comparisonTag` 比较另一历史事件 |
| 18 | `biz-impact` | 商业影响 | 结合代码事实和用户 `notes` 分析业务影响 |
| 19 | `recommendations` | 行动建议 | 根据事实和风险给出按优先级排列的行动方案 |

默认组合：

- `csuite` 7 章：`verdict`、`metrics`、`trend`、`viewpoints`、`platforms`、`severity`、`risk`。
- `pr` 11 章：csuite 7 章，加 `sentiment-evolution`、`keywords`、`engagement`、`media-social`。
- 其余章节由用户按需要启用；`response`、`benchmark`、`biz-impact` 启用时要求额外输入。

## 3. 不可更改的输出契约

```text
out/{id}/
├── report.md
├── report.pdf
├── charts/
└── meta.json
```

输出规则：

- 即使没有成功图表，也创建空的 `charts/`，保持 bundle 结构稳定。
- `meta.json` 保留任务书给出的全部 `ReportMeta` 字段。
- `sections` 统计实际可见的章节片段，包括显式缺失提示；`charts` 只统计实际写出的 PNG。
- `meta.json` 增加我们定义的 `generation` 摘要和安全的 `failures` 数组。
- 错误信息不得包含 DSN、API Key、完整 provider 响应或内部地址。
- bundle 先写入任务独立的临时目录；必需文件完成后原子发布到 `out/{id}`。
- 报告 ID 默认是 `{tag}-{to-date}-v{version}`，同一范围重复生成形成清晰版本历史。
- M3 的任务 ID 与报告 ID 分离，避免状态查询和报告命名耦合。
- bundle 原子发布完成后，由独立 `CatalogPublisher` 更新 `index.json`，让报告立即出现在列表中。

`meta.json` 的固定主体字段为：

```jsonc
{
  "id": "layoff-2026-03-23",
  "title": "××\"裁员60%\"事件舆情分析报告",
  "reportType": "csuite",
  "language": "zh",
  "topic": "裁员",
  "dateRange": { "from": "2026-03-17", "to": "2026-03-23" },
  "sections": 7,
  "charts": 8,
  "stats": {
    "articles": 171,
    "negativeRatio": "81.8%",
    "peakDay": "3/21"
  },
  "file": "/reports/layoff-2026-03-23.pdf",
  "generatedAt": "2026-07-15T10:00:00+08:00"
}
```

这里的数值仅用于说明字段形状；真实值必须由本次查询计算。

建议失败元数据：

```json
{
  "failures": [
    {
      "sectionId": "response",
      "stage": "llm",
      "message": "Narration timed out"
    }
  ]
}
```

生成摘要：

```json
{
  "generation": {
    "requested": 7,
    "complete": 5,
    "noData": 1,
    "failed": 1
  }
}
```

## 4. 总体架构

采用模块化单体：一条报告流水线、一个章节注册表、多个可注入外部适配器。

```text
CLI ───────────────┐
                   ├→ ReportApplicationService
FastAPI ───────────┘             │
                                 v
                          ReportEngine
                                 │
             ┌───────────────────┼──────────────────────────┐
             v                   v                          v
       SectionRegistry      BundleAssembler        Job/Storage/Catalog
             │
     ┌───────┼────────┬───────────────┐
     v       v        v               v
 PostgreSQL Facts   Charts         Narrator
  固定 SQL  Python  matplotlib   OpenAI-compatible
                                       │
                              Real client / Stub
```

设计边界：

- CLI 和 FastAPI 只负责输入输出，不包含章节业务逻辑。
- SQL、模型、PDF、时钟和存储均通过接口注入，便于测试。
- csuite/pr 与 zh/en 是模板参数和默认配置，不形成四套代码。
- 公共章节不会自动添加其他公共章节；内部数据复用通过缓存或分析块完成。
- `CatalogPublisher` 与报告计算解耦，但属于完整用户流程的一部分。
- 不采用微服务、Agent 框架或由 LLM 生成 SQL。

## 5. 核心对象

### `AnalysisScope`

由配置一次性构建并冻结，包含 tag、显示名、事件标题、日期范围、语言和报告受众。所有 SQL 必须使用同一 scope，不能各章节自行解释时间或话题过滤。

### `ExecutionPlan`

保存本次报告的标准化配置和有序章节列表。它只描述用户真正启用的章节，不把内部依赖暴露为报告章节。

### `SectionDefinition`

章节注册项包含：

```text
id
required_inputs
fetcher
calculator
chart_builder
prompt_template_key
no_data_policy
error_policy
internal_data_requirements
```

### `FactSet`

保存代码计算结果及来源：

```text
key
raw_value
formatted_value
query/calculation identifier
source record IDs（适用时）
```

图表、确定性数据段和 LLM prompt 必须消费同一个 `FactSet`，不允许三处重复计算。

### `EvidenceSet`

保存观点所需的真实文章 ID、标题、摘要、平台、日期和情感。模型只能基于这个集合总结、引用或转述观点。

### `SectionResult`

```text
status: complete | no_data | failed
markdown
charts
facts
evidence references
warnings
failure stage / safe error
```

### `ReportResult`

保存有序章节结果、汇总统计、输出路径、生成时间和失败信息，是 bundle 与 API 状态的唯一来源。

## 6. 单章节执行协议

每个启用章节严格执行：

```text
1. 校验该章节的专属 input
2. 使用固定、参数化 SQL 取数
3. 用 SQL/Python 计算 FactSet
4. 从真实 title/summary 构建 EvidenceSet
5. 用 FactSet 生成确定性图表
6. 最多发起一次模型叙述请求
7. 校验模型只能使用批准事实与证据
8. 返回 complete、no_data 或 failed
```

一章的异常在步骤边界内捕获，之后继续执行下一章。

## 7. 数字与观点的可信边界

### 数字

- 总量、占比、峰值、排名和风险分值全部由 SQL/Python 计算。
- prompt 使用 `[[fact:key]]` 一类事实引用，渲染器再替换成代码值。
- 图表标签和标题中的数字同样来自 `FactSet`。
- 出现未知事实引用或未经批准的模型数字时，拒绝该叙述并将章节标记缺失。
- 原始标题或摘要中的数字属于证据，保留其来源 ID。

### 观点

- “主要观点”等章节必须接收真实 summary/title。
- prompt 不提供无来源的背景知识。
- 代表性文章的选择规则由代码控制，例如情感、互动量、平台覆盖和时间范围。
- 报告中的观点可追溯到 EvidenceSet，模型不创造案例。

## 8. LLM 策略

统一接口：

```text
Narrator
├── OpenAICompatibleNarrator
└── StubNarrator
```

配置只来自：

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

每个章节只调用一次 `Narrator.narrate()`。适配器只对连接中断、429、502/503/504 等短暂错误做最多一次传输重试，并设置总超时；逻辑调用次数仍不超过章节数，实际传输尝试数写入诊断信息。真实模型只用于冒烟测试，自动化测试全部使用确定性 stub。

## 9. 章节级容错

| 失败场景 | 章节状态 | 报告行为 |
|---|---|---|
| 章节专属输入缺失 | failed | 显示需要补充的输入，继续 |
| SQL 合法但为空 | no_data | 显示“监测范围内暂无相关数据”，继续 |
| SQL/数据库异常 | failed | meta 记录 query 阶段错误，继续 |
| 图表失败 | failed | meta 记录 chart 阶段错误，继续 |
| LLM 超时/错误 | failed | meta 记录 llm 阶段错误，继续 |
| 模型输出违反事实约束 | failed | 拒绝不安全叙述，继续 |
| Markdown/PDF 无法组装 | 报告级失败 | 保留诊断和可用中间产物，不发布不完整 bundle |

`no_data` 与失败提示都必须进入 `report.md` 和 PDF；前者是有效分析结论，后者说明可恢复问题。

## 10. 图表与 PDF

### 图表统一入口

`ChartTheme` 强制：

- 白底；
- 隐藏上、右边框；
- 150 dpi；
- 负面 `#DC2626`；
- 中性 `#F59E0B`；
- 正面 `#10B981`；
- 标题表达洞察，不使用纯图名；
- 使用随项目分发的中文字体。

### PDF

```text
report.md
  → 受控 Markdown/结构化章节
  → ReportLab 流式排版
  → 项目内嵌 Noto Sans SC 字体
  → A4 report.pdf
```

同一 CJK 字体同时注册到 matplotlib 和 ReportLab，避免图表正常但 PDF 乱码。参考 PDF 用作视觉基准；渲染器自身控制 A4 页边距、分页、页眉页脚、章节样式和图表缩放，不依赖评审机器安装浏览器或字体。

## 11. 配置与安全

`.env.example` 只包含变量名和安全示例：

```text
PG_DSN
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

规则：

- 数据库切换只改变 `PG_DSN`，章节代码不包含环境地址。
- 不提交 `.env`、真实密钥、密码或内网地址。
- 日志和 `meta.json` 对错误做脱敏。
- SQL 全部参数化，tag、日期和比较 tag 不拼接进 SQL 字符串。
- 模型永远无权生成或执行 SQL。

## 12. 包结构

```text
src/report_engine/
├── cli.py
├── config.py
├── settings.py
├── application/
│   ├── planner.py
│   └── service.py
├── domain/
│   ├── facts.py
│   ├── evidence.py
│   ├── results.py
│   └── scope.py
├── sections/
│   ├── base.py
│   ├── registry.py
│   └── <19 个章节模块>
├── data/
│   ├── postgres.py
│   └── queries/
├── llm/
│   ├── protocol.py
│   ├── openai_compatible.py
│   ├── stub.py
│   └── prompts/
├── charts/
│   └── theme.py
├── rendering/
│   ├── assembler.py
│   ├── pdf.py
│   └── templates/
├── storage/
│   └── bundle.py
└── api/
    ├── app.py
    └── jobs.py
```

只在纵向切片需要时创建模块，不预先生成一批空抽象文件。

## 13. CLI、API 与 n8n

### M1/M2 CLI

```bash
report generate --config examples/report-config.csuite.json --out ./out/
```

CLI 只负责读取配置、调用 `ReportApplicationService`、输出报告路径和适当退出码。

### M3 API

```text
POST /reports                  → task id
GET  /reports/{id}/status      → queued/running/completed/failed
GET  /reports/{id}/report.pdf  → 主下载入口
GET  /reports/{id}/bundle.zip  → 完整报告包
```

进程内有界队列负责调度；状态响应包含当前章节和 `completedSections/totalSections`。每个任务使用独立临时目录。已完成状态通过磁盘上的 bundle/meta 恢复，因此服务重启后仍可下载。

### n8n 演示

```text
Manual/Webhook Trigger
  → POST /reports
  → 定时轮询 status
  → success/failure 分支
  → 返回下载链接
```

n8n 演示集成能力，但不替代 CLI、FastAPI、fixtures 集成测试或 Python 核心引擎。

## 14. 测试与验收证据

### 单元测试

- 配置解析与 `reportType` 回退；
- enabled 过滤与章节顺序；
- 全局/章节级输入错误边界；
- FactSet 计算和格式化；
- 报告 ID 冲突分配；
- metadata 计数和失败字段。

### SQL 集成测试

- 启动任务书提供的 fixture PostgreSQL；
- 对每章执行真实固定 SQL；
- 将 FactSet 与直接 SQL 结果逐项比较；
- 不 mock 数据库结果。

### LLM 测试

- 注入 `StubNarrator`；
- 输出完全确定；
- 记录调用次数并断言不超过成功取数章节数；
- 注入超时、错误和非法事实引用；
- 真实模型仅做一两个冒烟用例。

### 图表/PDF 测试

- PNG 为 150 dpi，颜色和字体正确；
- 所有 Markdown 图片引用存在；
- PDF 为 A4；
- 中文无乱码、表格不截断、章节分页合理；
- 将渲染页与 gold report 做人工/视觉烟测。

### API 测试

- 并发提交两个任务，输出目录和状态互不干扰；
- 服务重启后，已完成任务状态可恢复；
- 已完成报告仍可下载。

## 15. 里程碑

### M1：中文纵向切片到完整默认报告

1. 配置与执行计划；
2. 一个纯统计章节；
3. 一个基于真实摘要的观点章节；
4. 一个带图表的趋势章节；
5. Markdown/PDF bundle；
6. 章节级故障隔离；
7. csuite 7 章与 pr 11 章完整生成。

### M2：全部章节和英文

- 按本框架的章节产品设计编写 `docs/02-report-spec.md`，并落实全部 19 章；
- response/benchmark/biz-impact 的专属输入；
- zh/en 模板；
- 任意启用组合和顺序。

### M3：API

- 提交、状态、下载；
- 两任务并发隔离；
- 已完成报告磁盘恢复；
- n8n 演示工作流。

## 16. Git 与沟通规则

- `main` 始终可运行；所有工作在 `codex/*` 功能分支进行。
- 每个提交只做一个可验证变化，提交信息说明结果。
- 文档、代码和 fixture 不一致时，先记录 issue/沟通，不静默修改口径。
- 未明确规范采用显式判断，记录选择、原因、替代方案和影响，并写入 PR 描述。
- 每个里程碑合并前运行对应测试和报告渲染检查。

## 17. 我们主动交付的设计资产

任务书提及但未提供的内容属于实现范围，由我们创建：

1. `docs/02-report-spec.md`：上述 19 章的输入、SQL、事实、图表、叙述和无数据规则；
2. `fixtures/`：可启动的 PostgreSQL schema、种子数据和 Docker Compose；
3. `examples/report-config.csuite.json` 与 `examples/report-config.pr.json`；
4. `examples/gold-report/`：根据参考 PDF 创建的视觉基准；
5. `ReportMeta` 扩展：`generation`、`failures` 和版本信息；
6. `CatalogPublisher`：原子维护 `index.json`；
7. 中英文模板：英文叙述、专有名词保留、关键引用可双语展示。

## 18. 框架完成标准

框架只有在以下证据齐全后才进入实现阶段：

- 任务书每条要求均出现在需求追踪矩阵；
- 每条要求均有负责模块和验收证据；
- 所有已知矛盾都有显式临时判断；
- 输入输出固定契约没有被 n8n、API 或内部抽象改变；
- 任务书未提供的设计空间均形成明确的项目产物和验收标准。
