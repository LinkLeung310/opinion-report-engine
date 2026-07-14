# 舆情报告生成引擎：最终版框架

> 本框架以任务书为唯一约束来源。19 个章节的精确 ID、SQL、前端类型和 gold-report CSS 必须在取得任务仓库后按原文件填入，本文不会虚构它们。

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
- 某章节失败时，`meta.json` 增加安全的 `failures` 数组；若前端已有同义字段，则使用前端字段名。
- 错误信息不得包含 DSN、API Key、完整 provider 响应或内部地址。
- bundle 先写入任务独立的临时目录；必需文件完成后原子发布到 `out/{id}`。
- 报告 ID 默认是 `{tag}-{to-date}`；发生重复或并发冲突时添加 `-2`、`-3` 等后缀。
- M3 的任务 ID 与报告 ID 分离，避免状态查询和报告命名耦合。

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

## 4. 总体架构

采用模块化单体：一条报告流水线、一个章节注册表、多个可注入外部适配器。

```text
CLI ───────────────┐
                   ├→ ReportApplicationService
FastAPI ───────────┘             │
                                 v
                          ReportEngine
                                 │
             ┌───────────────────┼───────────────────┐
             v                   v                   v
       SectionRegistry      BundleAssembler      Job/Storage
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
missing_policy
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
status: complete | missing
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
8. 返回 complete 或 missing
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

M1/M2 默认每章节最多发起一次实际模型请求，以满足可测量的调用上限。任务书同时要求“重试与退避”，与调用次数上限冲突；框架保留可注入的重试策略，但默认关闭，并在 PR 中明确说明此判断。真实模型只用于冒烟测试，自动化测试全部使用确定性 stub。

## 9. 章节级容错

| 失败场景 | 章节状态 | 报告行为 |
|---|---|---|
| 章节专属输入缺失 | missing | 显示缺失提示，继续 |
| SQL 合法但为空 | missing | 显示数据缺失提示，继续 |
| SQL/数据库异常 | missing | meta 记录 query 阶段错误，继续 |
| 图表失败 | missing | meta 记录 chart 阶段错误，继续 |
| LLM 超时/错误 | missing | meta 记录 llm 阶段错误，继续 |
| 模型输出违反事实约束 | missing | 拒绝不安全叙述，继续 |
| Markdown/PDF 无法组装 | 报告级失败 | 保留诊断和可用中间产物，不发布不完整 bundle |

缺失提示本身必须进入 `report.md` 和 PDF，因此用户能看见该章节为何没有生成。

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
  → Markdown/结构化章节
  → Jinja2 HTML
  → gold-report CSS
  → Playwright Chromium
  → A4 report.pdf
```

同一 CJK 字体同时通过 matplotlib 和 `@font-face` 注册，避免图表正常但 PDF 乱码。分页、页边距、表格断页和标题孤行规则按 gold-report CSS 落实。

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
GET  /reports/{id}/download    → completed bundle/report download
```

进程内有界队列负责调度；每个任务使用独立临时目录。已完成状态通过磁盘上的 bundle/meta 恢复，因此服务重启后仍可下载。

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
- 所有 Markdown/HTML 图片引用存在；
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
5. Markdown/HTML/PDF bundle；
6. 章节级故障隔离；
7. csuite 7 章与 pr 11 章完整生成。

### M2：全部章节和英文

- 根据 `docs/02-report-spec.md` 落实全部 19 章；
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

## 17. 当前仍需从任务仓库取得的权威信息

以下内容不影响总体框架，但决定具体实现，不能由我们臆造：

1. `docs/02-report-spec.md`：19 个章节 ID、SQL、输入、图表和叙述要求；
2. `fixtures/`：PostgreSQL schema、tags 类型、时间字段与数据时区；
3. `examples/report-config.*.json`：csuite 7 章和 pr 11 章的准确默认组合；
4. `examples/gold-report/`：HTML/CSS、字体和分页基准；
5. 前端 `ReportMeta` 类型及现有 `index.json` 发布逻辑；
6. 英文配置中的 `displayName/eventTitle` 是否已翻译。

取得这些文件后，只补充章节注册表、固定 SQL 和模板细节，不改变本文的核心执行协议。

## 18. 框架完成标准

框架只有在以下证据齐全后才进入实现阶段：

- 任务书每条要求均出现在需求追踪矩阵；
- 每条要求均有负责模块和验收证据；
- 所有已知矛盾都有显式临时判断；
- 输入输出固定契约没有被 n8n、API 或内部抽象改变；
- 缺少的仓库资产被列为权威待补信息，而不是被假设填充。
