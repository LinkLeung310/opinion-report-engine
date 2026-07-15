# Opinion Report Engine

Configuration-driven public-opinion analytics report generator for the take-home assignment.

Development follows the assignment milestones:

- M1: Chinese C-suite and PR report bundles via CLI
- M2: All 19 sections and English output
- M3: FastAPI report jobs and persistent downloads

The `main` branch is kept runnable. Feature work is developed on `codex/*` branches.

## First runnable slice

The repository currently implements one complete `metrics` section through the same boundaries
the full product will use: fixed PostgreSQL SQL, Python-owned facts, injected narration,
a 150 dpi chart, A4 Chinese PDF rendering, and atomic bundle publication. The remaining
section IDs are registered but deliberately reported as visible failures until their own
vertical slices are implemented.

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
docker compose -f fixtures\docker-compose.yml up -d --wait
$env:PG_DSN='postgresql://report:report_local_only@localhost:55432/opinion_fixture'
.\.venv\Scripts\report.exe generate --config examples\report-config.metrics.json --out out --stub-llm
```

The command prints the created `out/{id}` directory. It contains `report.md`,
`report.pdf`, `charts/*.png`, and `meta.json`. `--stub-llm` is an explicit offline mode
for deterministic review; the real OpenAI-compatible adapter is the next vertical slice.

Run all tests, including the real fixture SQL and CLI integration test:

```powershell
$env:PG_DSN='postgresql://report:report_local_only@localhost:55432/opinion_fixture'
.\.venv\Scripts\python.exe -m pytest
```

## Design documents

- [Documentation map](docs/README.md)
- [Current implementation state](docs/current-state.md)
- [最终版框架（中文）](docs/final-framework.zh-CN.md)
- [Section and SQL specification](docs/02-report-spec.md)
- [Architecture](docs/architecture.md)
- [Requirements traceability](docs/requirements-traceability.md)
- [Framework audit](docs/framework-audit.md)
- [Product and architecture decisions](docs/design-decisions.md)

## Local data fixture

The repository supplies a synthetic PostgreSQL dataset so every reported number can be
verified without production access. See [fixtures/README.md](fixtures/README.md).
