# Opinion Report Engine

Configuration-driven public-opinion analytics report generator for the take-home assignment.

Development follows the assignment milestones:

- M1: Chinese C-suite and PR report bundles via CLI
- M2: All 19 sections and English output
- M3: FastAPI report jobs and persistent downloads

The `main` branch is kept runnable. Feature work is developed on `codex/*` branches.

## Runnable slices

The repository currently implements all seven C-suite sections: `verdict`, `metrics`,
`trend`, `viewpoints`, `platforms`, `severity`, and `risk`, through the same boundaries
the full product will use: fixed PostgreSQL SQL, Python-owned facts, injected narration,
a set of five meaningful 150 dpi charts, A4 Chinese PDF rendering, and atomic bundle publication.
It also implements the PR-oriented `sentiment-evolution` slice with a sixth chart:
phase composition is shown beside explicit sample sizes and is kept separate from
the absolute discussion volume already shown by `trend`.
The PR-oriented `keywords` slice adds a seventh chart based on distinct-document
coverage of deterministic recurring phrases; it reports tied leaders and an honest
absence of late-emerging phrases without claiming semantic clustering, a word cloud,
or RAG.
The PR-oriented `engagement` slice adds an eighth chart that separates the four stored
interaction counters from their concentration in high-count records. Its ranked source
evidence is auditable, while the text explicitly avoids engagement-rate, unique-reach,
support, and causal claims that the available schema cannot justify.
The PR-oriented `media-social` slice adds a ninth chart comparing absolute volume and
within-group sentiment for the database's stored `media`/`social` source types. It keeps
sample sizes visible, treats an absent group as unavailable rather than 0%, and does not
infer audiences or source type from platform names or text.
`verdict` adds an auditable Python-owned risk and momentum judgment without a redundant
decorative chart; `trend` preserves quiet calendar days in a stacked sentiment timeline.
`platforms` discloses volume ties and compares sentiment with engagement without
letting one-item percentage outliers dominate the risk story.
`severity` measures high-risk concentration and cites a deterministic shortlist of real
fixture records by Evidence ID without claiming RAG or semantic retrieval.
`risk` exposes a five-signal non-probability diagnostic index and discloses schema gaps
instead of guessing executive association or rumor status from text.
`viewpoints` separates population sentiment shares from a deterministic, cross-platform
evidence shortlist and validates every displayed Evidence ID plus the original source text;
this baseline does not claim RAG or semantic retrieval.
The M2 vertical slices now also implement `timeline`, `top-content`, `negative-themes`,
`spread-path`, `response`, `benchmark`, `biz-impact`, and `recommendations`. The last of
these converts fixed risk/theme signals into at most four evidence-linked, human-review
actions without assigning owners, executing work, or claiming an effectiveness score.
The deterministic M2 acceptance matrix now covers all 19 English sections, all three
section-specific inputs, a reordered mixed selection, all-section `no_data`, localized
partial failure, narrator call limits, the complete bundle, 15 charts, and A4 PDF output.
The real OpenAI-compatible narrator remains a separate unfinished integration; see
`docs/current-state.md` for the exact boundary.

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
docker compose -f fixtures\docker-compose.yml up -d --wait
$env:PG_DSN='postgresql://report:report_local_only@localhost:55432/opinion_fixture'
.\.venv\Scripts\report.exe generate --config examples\report-config.csuite.json --out out --stub-llm
```

The command prints the created `out/{id}` directory. It contains `report.md`,
`report.pdf`, `charts/*.png`, and `meta.json`. `--stub-llm` is an explicit offline mode
for deterministic review. Development and CI stay on the injectable stub; the real
OpenAI-compatible model is reserved for a final credential-gated smoke test.

The complete eleven-section PR default uses the same engine and fixture scope:

```powershell
.\.venv\Scripts\report.exe generate --config examples\report-config.pr.json --out out --stub-llm
```

Generate the complete 19-section English M2 review bundle:

```powershell
.\.venv\Scripts\report.exe generate --config examples\report-config.all-sections.en.json --out out --stub-llm
```

Review the recommendation playbook as a standalone selectable section:

```powershell
.\.venv\Scripts\report.exe generate --config examples\report-config.recommendations.json --out out --stub-llm
```

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
