# Open Questions and Assumptions

Do not silently work around these items. Confirm them from repository documentation,
fixtures, or stakeholder communication before locking behavior.

| ID | Question | Why it matters | Temporary position |
|---|---|---|---|
| OQ-001 | Does a retry count against “LLM calls per section <= 1”? | Cost and acceptance metrics conflict with the retry requirement. | Default to one dispatched request for M1/M2; keep retries disabled but injectable, and explain this decision in the PR. |
| OQ-002 | Does the existing frontend type already name the required `meta.json` failure field? | The example omits the required failure metadata even though the brief requires it. | Use additive `failures: [{sectionId, stage, message}]` unless the frontend has an equivalent field. |
| OQ-003 | What exact visible text and metadata shape represent an empty result? | The brief requires the chapter be marked missing, even where an empty period is legitimate. | Always render a visible missing/data-unavailable fragment; settle wording from examples. |
| OQ-004 | Should an unknown `reportType` silently become `csuite` or emit a warning? | Silent fallback can hide frontend bugs. | Follow the required fallback and attach a warning internally. |
| OQ-005 | Are date boundaries inclusive, and which timezone owns timestamps? | Daily totals and peak dates depend on this. | Await schema/spec; prefer an explicit half-open timestamp interval. |
| OQ-006 | What is the exact `articles.tags` type and match rule? | Array, JSON, and text tags require different safe SQL. | Await fixture schema. The reference scope's brand filter is optional until the fixed SQL proves it is needed. |
| OQ-007 | Does the existing frontend require a particular report-ID format? | M3 requires concurrent jobs not to interfere. | Use `{tag}-{to-date}` with collision suffixes and isolated temporary paths unless the frontend requires another scheme. |
| OQ-008 | Does the repository explicitly assign `index.json` updates to this module? | The stated final flow requires reports to appear in the existing list, while publishing is stated as out of scope. | Treat bundle/meta publication as this module's responsibility and `index.json` updates as integration work unless code proves otherwise. |
| OQ-009 | What are the exact 19 section IDs, default 7/11 sets, SQL, and dependencies? | The public section registry cannot be finalized without `docs/02-report-spec.md`. | Await the complete task repository. |
| OQ-010 | Are extra internal provenance files allowed in the output bundle? | They would improve auditability but may violate strict golden-file checks. | Keep provenance in memory/test artifacts unless the contract allows extras. |
| OQ-011 | For English reports, are `topic.displayName` and `eventTitle` already translated? | The fixed input gives no locale-specific title fields, but M2 requires English output. | Preserve supplied strings as source labels; use English template text around them until examples specify translation behavior. |
| OQ-012 | Do `meta.sections` and `meta.charts` count visible missing placeholders? | The example describes actual rendered counts but does not define a failed-section case. | Count visible section fragments; count only emitted chart files. |
