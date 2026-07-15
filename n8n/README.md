# n8n demonstration workflow

`report-generation-orchestrator.json` visualizes the M3 API orchestration:

```text
manual trigger
  -> POST /reports
  -> wait
  -> GET /reports/{taskId}/status
  -> completed / failed / continue polling
```

The workflow is intentionally inactive until the FastAPI endpoints exist. It contains
no database queries, LLM nodes, credentials, or report calculations; the Python engine
remains the source of truth required by the assignment.

Both HTTP nodes retry transient failures and route persistent failures to a visible
`API Error` terminal node. After importing or updating the workflow, inspect its
connections in n8n before activation.
