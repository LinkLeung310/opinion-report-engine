# Architecture (Draft)

## 1. Objective

Build a configuration-driven report engine that turns a fixed `ReportConfig` into a
traceable report bundle:

```text
ReportConfig -> query -> calculate -> chart -> narrate -> assemble -> PDF bundle
```

The engine is a modular monolith. The CLI and API are thin adapters around the same
application service. n8n may call the API for demonstration and automation, but is not
a runtime dependency of the report engine.

## 2. Design principles

1. **Code owns facts.** SQL and Python calculate every statistic. The LLM only writes
   narrative from approved facts and evidence.
2. **Sections are isolated.** One failed section never aborts unrelated sections.
3. **Configuration is the execution plan.** Enabled section IDs and their array order
   determine what runs and how it is rendered.
4. **One implementation, multiple audiences.** `csuite` / `pr` and `zh` / `en` select
   presets and prompt variants, not separate pipelines.
5. **Ports at the edges.** Database, LLM, PDF renderer, clock, and storage are
   injectable interfaces so tests remain deterministic.
6. **The fixed contracts stay fixed.** Internal models may evolve without changing the
   required input JSON or output bundle.

## 3. System boundaries

```text
CLI ───────────────┐
                   v
FastAPI ──> ReportApplicationService ──> ReportEngine
                                              |
                 ┌────────────────────────────┼──────────────────────────┐
                 v                            v                          v
          PostgreSQL adapter            LLM adapter              PDF renderer
                 |                            |                          |
             fixed SQL              real client / stub          HTML + Chromium

n8n (optional) -> FastAPI submit/status/download endpoints
```

## 4. Core execution flow

### Phase A: validate and plan

1. Parse `report-config.json` into typed models.
2. Normalize the report type according to the documented fallback rule.
3. Build one immutable `AnalysisScope` from tag, display name, event title, date range,
   language, and audience.
4. Resolve enabled section IDs through the `SectionRegistry`.
5. Validate required section inputs before querying data.
6. Produce an ordered `ExecutionPlan`.

### Phase B: run sections

Each section executes the same lifecycle:

```text
fetch fixed SQL
  -> calculate typed facts
  -> select evidence from real titles/summaries
  -> build deterministic charts
  -> request at most one logical narration
  -> validate narrative
  -> return SectionResult
```

The engine catches errors at the section boundary and continues with the next section.

### Phase C: assemble and publish

1. Assemble successful, partial, no-data, and failed section fragments in config order.
2. Render deterministic report metadata and data-quality notes.
3. Produce Markdown, HTML, A4 PDF, charts, and `meta.json` in a temporary directory.
4. Atomically rename the temporary directory to `out/{id}` only after required bundle
   files exist.

## 5. Core domain models

### `AnalysisScope`

An immutable, normalized filter shared by all sections. It owns date-boundary and topic
filter semantics so sections cannot implement scope differently.

### `SectionDefinition`

Declarative registration metadata:

```text
id
required inputs
dependencies
fetcher
calculator
chart builder
prompt template key
empty-data policy
```

### `FactSet`

A typed collection of code-calculated values with provenance:

```text
fact key
raw value
formatted value
query or calculation identifier
source record identifiers when applicable
```

Charts and prompts consume the same `FactSet`, preventing independent calculations.

### `EvidenceSet`

Representative source material used for qualitative claims. Evidence contains article
IDs, titles, summaries, platforms, dates, and sentiment labels. It never contains
model-invented examples.

### `SectionResult`

```text
status: success | partial | no_data | failed
markdown
charts
facts
evidence references
warnings
error metadata
```

### `ReportResult`

Contains the ordered section results, aggregate stats, output paths, timestamps, and
machine-readable warnings used to build the required bundle.

## 6. Fact-safe LLM boundary

The LLM receives:

- the section purpose;
- report audience and language;
- approved formatted facts;
- bounded real evidence;
- explicit output constraints.

The LLM does not receive raw responsibility for aggregation. To reduce numeric
hallucination, prompts may require fact references such as `[[fact:negative_ratio]]`.
The renderer replaces these tokens with code-calculated values. Unknown fact tokens or
unapproved numeric claims fail section validation.

The LLM interface is injectable:

```text
Narrator protocol
  ├── OpenAICompatibleNarrator   # smoke tests and real generation
  └── StubNarrator               # deterministic automated tests
```

## 7. Failure semantics

| Failure | Section result | Report behavior |
|---|---|---|
| Valid query with no rows | `no_data` | Render a deterministic no-data note |
| Database/query error | `failed` | Record error and continue |
| Chart error | `partial` | Keep facts and narrative where available |
| LLM timeout/error | `partial` | Keep deterministic facts and charts |
| Invalid LLM fact reference | `partial` or `failed` | Reject unsafe narrative |
| PDF render error | report-level failure | Preserve Markdown and diagnostics |

Only failures that prevent the required bundle contract are report-level failures.

## 8. Technology choices

Initial choices, subject to fixture and repository inspection:

- Python 3.12+
- Pydantic for config and result models
- Typer for the `report generate` CLI
- psycopg for parameterized fixed SQL
- matplotlib with a bundled CJK font for charts
- Jinja2 + Markdown-to-HTML templates
- Playwright Chromium for cross-platform A4 PDF output
- FastAPI with an in-process executor for M3
- pytest, with PostgreSQL fixture integration tests and an LLM stub

The synchronous engine remains framework-independent. M3 can run generation jobs in a
bounded thread/process executor without rewriting section code as async code.

## 9. Proposed package boundaries

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
│   ├── results.py
│   └── scope.py
├── sections/
│   ├── base.py
│   ├── registry.py
│   └── ... one module per public section
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

This is a package-boundary proposal, not permission to create empty abstraction files.
Modules should be added only when a vertical slice needs them.

## 10. Milestone slicing

### M1 vertical slice order

1. Config validation and execution plan
2. One deterministic statistics section
3. One evidence-backed narrative section
4. One chart-producing trend section
5. Report assembly and PDF
6. Section failure isolation
7. Complete default C-suite and PR configurations

### M2

Add remaining section definitions, section-specific inputs, and English prompt/template
variants without changing the core execution flow.

### M3

Wrap `ReportApplicationService` with job submission, status, and download endpoints.
Persist completed bundle state on disk so completed reports survive service restarts.

### n8n demonstration workflow

After M3 is stable:

```text
Manual/Webhook Trigger
  -> POST /reports
  -> poll GET /reports/{id}/status
  -> branch success/failure
  -> expose report download link
```

This workflow demonstrates integration but does not replace the required CLI or API.
