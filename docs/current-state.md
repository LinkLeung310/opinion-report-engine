# Current Project State

最后核对日期：2026-07-15  
最后实现基线：`main@0f514d1`（PR #1，first runnable metrics report slice）

本文件只记录已验证事实。任务要求以原始任务书为准，长期规则以根目录 `AGENTS.md` 为准。

## 已验证完成

- 固定 `ReportConfig` 的严格解析、未知 `reportType` 回退和 enabled 章节顺序规划。
- 19 个章节 ID 注册表；目前只有 `metrics` 章节完成端到端实现。
- 项目提供的合成 PostgreSQL fixtures、固定 metrics SQL 和真实数据库集成测试。
- `FactSet`、章节级 `complete` / `no_data` / `failed` 语义及安全失败 metadata。
- metrics 的 150 dpi 图表、项目内 Noto Sans SC 字体和 A4 ReportLab PDF。
- 原子发布 `report.md`、`report.pdf`、`charts/*.png`、`meta.json` bundle。
- `report generate` CLI 的显式 `--stub-llm` 离线验证路径。
- GitHub Actions 在 Python 3.12 + PostgreSQL fixtures 上运行完整测试。
- n8n Draft 工作流 JSON：提交 M3 API、等待、轮询和成功/失败分支；未激活。
- 仓库级 context recovery：`AGENTS.md`、文档导航、状态快照和 PR 模板。

## 当前证据

- PR #1 已用 merge commit 合并：`0f514d1`。
- main 分支 CI：47 项测试通过。
- 本地真实 CLI 验收得到 12 篇、负面占比 58.3%、失败章节 0 的完整 metrics bundle。
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

context recovery 治理已经写入仓库。用户已明确要求暂不开始 RAG；本治理切片没有新增 embedding、vector store、retriever、模型调用或 n8n 节点。

## 恢复清单

1. 读取根目录 `AGENTS.md`。
2. 读取原始任务书、本文件、需求追踪矩阵和设计决定。
3. 检查 Git 分支、工作区、远程和最新 CI。
4. 重新运行与下一目标相关的测试。
5. 向用户报告已完成、未完成和任何冲突，再开始修改。

## 下一阶段候选（尚未授权）

- 在独立分支实现真实 OpenAI-compatible narrator；或
- 先为 `viewpoints` 编写完整 section spec，再实现可引用证据的 RAG 纵向切片。

开始任一候选前都需要用户明确选择；不得因为它写在这里就自动扩大范围。
