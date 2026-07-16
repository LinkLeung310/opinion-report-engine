# n8n demonstration workflow

`report-generation-orchestrator.json` visualizes the M3 API orchestration:

```text
manual trigger
  -> POST /reports
  -> wait
  -> GET /reports/{taskId}/status
  -> completed / failed / continue polling
```

The FastAPI endpoints now exist, but the repository copy remains intentionally inactive.
Import and run it manually only while the local API is reachable. It contains no database
queries, LLM nodes, credentials, or report calculations; the Python engine remains the
source of truth required by the assignment.

Both HTTP nodes retry transient failures and route persistent failures to a visible
`API Error` terminal that marks the execution failed. A report-level `failed` status does
the same, while `completed` preserves the API response with its PDF and ZIP download
paths. After importing or updating the workflow, inspect its connections in n8n before
any manual execution.
