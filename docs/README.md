# Documentation Map

本页说明每份文档的职责，避免框架、状态和原始要求互相覆盖。

## Binding source

- [`source/2026-07-11-舆情报告生成模块 — 开发任务书.md`](source/2026-07-11-舆情报告生成模块%20%E2%80%94%20开发任务书.md)：面试方任务书的本地副本；固定契约和工作约定的最高仓库内来源。

## Governance and current truth

- [`../AGENTS.md`](../AGENTS.md)：所有 Codex 工作的长期入口、来源优先级和不可越过的工程规则。
- [`current-state.md`](current-state.md)：最后一次确认过的实现状态、证据、未完成项和恢复步骤；不定义新需求。
- [`requirements-traceability.md`](requirements-traceability.md)：任务书条款到设计责任和验证证据的映射。

## Project-owned design

- [`design-decisions.md`](design-decisions.md)：任务书未规定部分的显式产品/架构决定。
- [`final-framework.zh-CN.md`](final-framework.zh-CN.md)：以用户体验为核心的完整中文框架。
- [`architecture.md`](architecture.md)：模块边界、执行流、失败语义和验证策略。
- [`api-contract.md`](api-contract.md)：M3 HTTP 端点、状态、错误、幂等、队列和重启恢复合同。
- [`02-report-spec.md`](02-report-spec.md)：本项目逐章补充的 19 章输入、固定 SQL、事实、证据、图表和无数据规则。该文件是项目产物，不是面试方原始附件。

## Audits and integration notes

- [`framework-audit.md`](framework-audit.md)：框架对任务书条款的覆盖审计。
- [`../n8n/README.md`](../n8n/README.md)：n8n Draft 工作流的职责边界和启用前条件。
- [`../fixtures/README.md`](../fixtures/README.md)：项目提供的合成 PostgreSQL fixtures 的启动与验证方式。

## Update rule

需求变化先更新追踪矩阵或设计决定；章节实现前更新 section spec；每次合并后更新 current state。不要在多份文档复制同一状态数字。
