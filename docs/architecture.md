# Architecture Framework v1

This framework covers every binding requirement in the assignment brief. The project
owns the unspecified product-design space and will define the 19-section specification,
fixture schema, examples, metadata extensions, report CSS, and catalog behavior.

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
4. Resolve enabled section IDs through the `SectionRegistry`, preserving their original
   array order exactly. The registry never auto-adds a public section.
5. Validate global config before querying. Validate section-specific inputs at the
   section boundary: a missing `responseDate`, `comparisonTag`, or `notes` marks only
   that section failed and returns an actionable user prompt.
6. Produce an ordered `ExecutionPlan`.

### Phase B: run sections

Each section executes the same lifecycle:

```text
fetch fixed SQL
  -> calculate typed facts
  -> select evidence from real titles/summaries
  -> build deterministic charts
  -> request at most one model narration
  -> validate narrative
  -> return SectionResult
```

The engine catches errors at the section boundary and continues with the next section.
Internal shared calculations may be cached, but must never change which public sections
are rendered or their configured order.

### Phase C: assemble and publish

1. Assemble complete, no-data, and visible-failed section fragments in config order.
2. Render deterministic report metadata and data-quality notes.
3. Produce Markdown, HTML, A4 PDF, charts, and `meta.json` in a temporary directory.
4. Write visible no-data/failed fragments and failure metadata for section failures.
5. Atomically rename the temporary directory to `out/{id}` only after required bundle
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
internal data requirements
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
status: complete | no_data | failed
markdown
charts
facts
evidence references
warnings
failure stage and safe error metadata
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

The LLM does not receive raw responsibility for aggregation. Prompts use approved fact
references such as `[[fact:negative_ratio]]`; the renderer replaces them with
code-calculated values. Unknown references or unapproved numeric claims fail section
validation. Real quoted source text is carried as evidence and is not altered.

The LLM interface is injectable:

```text
Narrator protocol
  ├── OpenAICompatibleNarrator   # smoke tests and real generation
  └── StubNarrator               # deterministic automated tests
```

## 7. Failure semantics

| Failure | Section result | Report behavior |
|---|---|---|
| Valid query with no rows | `no_data` | Render a valid no-data finding and continue |
| Database/query error | `failed` | Record failure in metadata and continue |
| Chart error | `failed` | Render a visible failed-section note and continue |
| LLM timeout/error | `failed` | Render a visible failed-section note and continue |
| Invalid LLM fact reference | `failed` | Reject unsafe narrative, record failure, continue |
| PDF render error | report-level failure | Preserve Markdown and diagnostics |

Only failures that prevent the required bundle contract are report-level failures.

`meta.json` keeps the required frontend fields and adds a `generation` summary plus a
`failures` array when one or more sections fail. Each entry contains `sectionId`,
`stage`, and a safe message;
it never exposes DSNs, API keys, or raw provider errors. If the existing frontend type
already defines an equivalent field, that field takes precedence.

## 8. Technology choices

Technology choices:

- Python 3.12+
- Pydantic for config and result models
- Typer for the `report generate` CLI
- psycopg for parameterized fixed SQL
- matplotlib with a bundled CJK font for charts
- Jinja2 + Markdown-to-HTML templates
- Playwright Chromium for cross-platform A4 PDF output
- FastAPI with an in-process executor for M3
- pytest, with PostgreSQL fixture integration tests and an LLM stub

The bundled CJK font must be registered both by matplotlib and by the report CSS; a
browser-installed font is not a cross-platform guarantee. The synchronous engine remains
framework-independent. M3 can run generation jobs in a bounded thread/process executor
without rewriting section code as async code.

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

## 11. Adopted product decisions

These choices are deliberately explicit and form part of the project's product design.

1. **Date range:** interpret dates as `[from 00:00, to + 1 day 00:00)` in the fixture
   database timezone. This avoids excluding records on the final day.
2. **Unknown sections:** reject them as a global configuration error. The brief only
   grants a fallback for an unknown `reportType`, not for unknown section IDs.
3. **Section-specific input:** a known enabled section without its required input
   renders as failed with an actionable prompt; it does not invalidate unrelated sections.
4. **Report IDs:** use a human-readable base (`{tag}-{to-date}`), allocating a `-2`,
   `-3`, ... suffix when the same report is generated concurrently or repeatedly. A
   task ID remains separate from a report ID in M3.
5. **LLM attempts:** one narrator operation per section, with at most one bounded
   transport retry for transient failures; attempts are recorded in diagnostics.
6. **Generated-report list:** after atomic bundle publication, `CatalogPublisher`
   atomically updates `index.json` so the report appears immediately.
7. **Metadata failures:** append the safe `failures` array described above; preserve all
   existing required `ReportMeta` fields.
8. **Empty charts directory:** always create `charts/`, including when every enabled
   section is no-data or failed, so the bundle shape remains stable.

## 12. Verification strategy

1. **Config/planner unit tests**: fallback report type, enabled section filtering,
   ordering, and section-scoped validation.
2. **SQL integration tests**: start the supplied fixture PostgreSQL and assert each
   section's facts against direct parameterized SQL results.
3. **LLM contract tests**: use `StubNarrator` to make output deterministic and assert
   one request at most per rendered section.
4. **Failure-isolation tests**: inject empty SQL, query, chart, and LLM failures; assert
   remaining sections, bundle files, and `meta.json` failure details survive.
5. **Bundle/PDF tests**: assert A4 PDF, all referenced chart files, 150 dpi images, and
   a visual-render smoke check against the supplied gold report.
6. **M3 tests**: submit two concurrent jobs, assert separate paths/statuses, restart the
   service, and download already completed bundles.
