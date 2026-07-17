# M3 API Contract

本文件定义 M3 的 HTTP 合同。任务书固定了 `POST /reports`、状态查询与完成后下载；
具体状态码、响应体、错误体、幂等、队列和恢复语义属于项目自主设计，记录在 D-41/D-42。

## 1. 范围与调用方

- 调用方是同仓库前端与 Draft n8n 演示工作流。
- API 是同步报告引擎之外的薄适配层；SQL、事实、图表、LLM、PDF 与 bundle 发布仍由
  `ReportApplicationService` 拥有。
- M3 只面向单机、单 FastAPI 进程。上线网关、TLS、生产认证、跨进程队列和生产部署不在范围。
- 当前不提供报告列表 API；既有列表继续读取 D-40 `index.json`，因此没有分页接口。

## 2. 版本、认证与请求标识

- 保留任务书给出的无版本路径。当前合同只做向后兼容的字段扩展；需要破坏性变更时新增
  `/v2`，不原地改变现有字段语义。
- 本地 M3 不启用应用内认证，也不开放 CORS；n8n 当前使用 `authentication: none`。
  生产认证由部署方在网关或后续明确合同中增加，不能把本地无认证描述成生产安全方案。
- 服务为每个请求生成 UUID `requestId`，通过 `X-Request-ID` 响应头返回；错误体也包含同一值。

## 3. 提交报告

### `POST /reports`

请求体必须是原始任务书的完整 `ReportConfig`，不增加 API 外壳：

```json
{
  "reportType": "csuite",
  "language": "zh",
  "topic": {
    "tag": "bilibili-dislike",
    "displayName": "B站猜你不喜欢算法调整",
    "eventTitle": "B站猜你不喜欢算法调整事件"
  },
  "dateRange": {"from": "2026-03-17", "to": "2026-03-23"},
  "sections": [{"id": "metrics", "enabled": true}]
}
```

新任务返回 `202 Accepted`，并在 `Location` 指向状态资源：

```json
{
  "taskId": "4f7f7f38-a88f-4f70-b558-4798d0acef91",
  "status": "queued",
  "statusUrl": "/reports/4f7f7f38-a88f-4f70-b558-4798d0acef91/status"
}
```

可选请求头 `Idempotency-Key` 用于保护网络重试：

- 值为去除首尾空白后的 1–128 个可见 ASCII 字符；服务只持久化其 SHA-256，不保存原值。
- 相同 key 与相同规范化请求体返回原 task；非终态仍返回 `202`，终态返回 `200`。
- 相同 key 与不同请求体返回 `409 idempotency_conflict`。
- 未提供该头时，每次成功提交都创建独立任务和独立报告版本。

错误：

- `422 invalid_report_config`：请求体不符合固定 `ReportConfig`；详情只含字段位置和错误类型，
  不回显 `notes` 等原始输入。
- `422 invalid_idempotency_key`：幂等键不符合上述边界。
- `503 queue_full`：有界队列没有容量，同时返回 `Retry-After: 5`。

## 4. 查询状态

### `GET /reports/{taskId}/status`

已知任务始终返回 `200 OK`：

```json
{
  "taskId": "4f7f7f38-a88f-4f70-b558-4798d0acef91",
  "status": "running",
  "submittedAt": "2026-07-17T04:00:00Z",
  "startedAt": "2026-07-17T04:00:01Z",
  "finishedAt": null,
  "progress": {
    "currentSection": "trend",
    "completedSections": 2,
    "totalSections": 7
  },
  "reportId": null,
  "downloads": null,
  "error": null
}
```

`status` 只允许：

- `queued`：已持久化并等待工作线程；
- `running`：已开始生成；
- `completed`：bundle、catalog 和 ZIP 均已发布，可下载；
- `failed`：报告级失败，不再重试。

完成时 `reportId` 非空，`downloads` 为：

```json
{
  "pdf": "/reports/{taskId}/report.pdf",
  "bundle": "/reports/{taskId}/bundle.zip"
}
```

失败时 `error` 只含稳定 `code` 与安全 `message`。章节级 `no_data` / `failed` 仍属于成功
报告内的章节状态，不会自动把 API 任务改成 `failed`。未知 task UUID 返回 `404 task_not_found`；
非法 UUID 路径返回 `422 invalid_task_id`。

## 5. 下载

### `GET /reports/{taskId}/report.pdf`

- 完成任务返回 `200 application/pdf` 和 attachment 文件名 `{reportId}.pdf`。
- 文件来自该任务持久化记录所指向的已发布 bundle，不从用户路径参数拼接报告目录。

### `GET /reports/{taskId}/bundle.zip`

- 完成任务返回 `200 application/zip` 和 attachment 文件名 `{reportId}.zip`。
- ZIP 以 `{reportId}/` 为根，包含固定 bundle 的 `report.md`、`report.pdf`、`meta.json`
  与 `charts/`；不包含任务状态、凭据、缓存或 `index.json`。

两个下载端点对未知任务返回 `404 task_not_found`，对已知但非完成任务返回
`409 report_not_ready`。文件丢失或状态与磁盘矛盾返回安全的 `500 artifact_unavailable`，
不暴露绝对路径。

## 6. 统一错误体

所有 API JSON 错误使用同一形状，不返回 200 错误体，也不暴露 traceback、DSN、API key、
provider body、SQL 或绝对文件路径：

```json
{
  "error": {
    "code": "task_not_found",
    "message": "Report task was not found",
    "details": {},
    "requestId": "d0d20b6b-83a0-4371-ac9e-885c36cf40ef"
  }
}
```

## 7. 队列、隔离与持久化

- 默认两个工作线程，最多接受 16 个 `queued + running` 任务；两个数均为构造参数，测试可注入，
  不新增环境变量。
- 每个真实任务创建自己的 PostgreSQL 连接、narrator 与 application service；禁止并发任务共享
  psycopg connection。所有任务共享同一个 `out/`，但报告 ID 预留和 CatalogPublisher 必须避免覆盖。
- 每个任务在 `out/.report-jobs/tasks/{taskId}.json` 使用同目录临时文件 + 原子替换持久化。
  状态文件不保存 ReportConfig、用户 notes、DSN、模型密钥或 provider 响应。
- ZIP 缓存在 `out/.report-jobs/downloads/{taskId}.zip`，完成状态只在 bundle、catalog 和 ZIP
  全部可用后写入。
- 服务通过 FastAPI `lifespan` 启动/关闭 job manager。重启时重新加载任务记录：完整且文件存在的
  `completed` 任务继续查询和下载；遗留 `queued` / `running` 任务转成
  `failed/service_restarted`，不假装续跑。损坏的任务状态使启动明确失败，禁止静默丢记录。
- 关闭时停止接收新任务并等待已接受任务完成；意外进程终止由下一次启动按上述规则收口。

## 8. OpenAPI 与验收

- FastAPI 生成的 `/openapi.json` 是实现后的机器可读合同，必须与本文件一致。
- 自动化验收覆盖：202 提交、状态迁移、统一错误体、幂等重放/冲突、队列满、两个任务隔离、
  PDF/ZIP 下载、ZIP 内容、路径安全、章节局部失败仍完成、重启恢复 completed，以及中断任务转失败。
- 真实 fixture PostgreSQL + StubNarrator 验证至少两个并发 API 任务；真实模型不参与日常测试。
