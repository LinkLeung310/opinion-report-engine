# Open Questions and Assumptions

Do not silently work around these items. Confirm them from repository documentation,
fixtures, or stakeholder communication before locking behavior.

| ID | Question | Why it matters | Temporary position |
|---|---|---|---|
| OQ-001 | Does a retry count against “LLM calls per section <= 1”? | Cost and acceptance metrics conflict with the retry requirement. | Keep the LLM interface retry-capable; do not choose a default until clarified. |
| OQ-002 | What exact field records section failures in `meta.json`? | The example omits the required failure metadata. | Add an internal result model; map it only after confirming the frontend contract. |
| OQ-003 | Is a valid empty query a failure or a no-data result? | Empty periods are normal and should not look like system errors. | Treat as `no_data`, not an exception. |
| OQ-004 | Should an unknown `reportType` silently become `csuite` or emit a warning? | Silent fallback can hide frontend bugs. | Follow the required fallback and attach a warning internally. |
| OQ-005 | Are date boundaries inclusive, and which timezone owns timestamps? | Daily totals and peak dates depend on this. | Await schema/spec; prefer an explicit half-open timestamp interval. |
| OQ-006 | What is the exact `articles.tags` type and match rule? | Array, JSON, and text tags require different safe SQL. | Await fixture schema. |
| OQ-007 | How should repeated generation of the same tag/end date avoid output collisions? | M3 requires concurrent jobs not to interfere. | Generate in isolated temporary paths; confirm final ID convention. |
| OQ-008 | Who updates the frontend `index.json` after generation? | The stated final flow requires reports to appear in the existing list. | Keep outside core bundle writing until the repository contract is inspected. |
| OQ-009 | What are the exact 19 section IDs, default 7/11 sets, SQL, and dependencies? | The public section registry cannot be finalized without `docs/02-report-spec.md`. | Await the complete task repository. |
| OQ-010 | Are extra internal provenance files allowed in the output bundle? | They would improve auditability but may violate strict golden-file checks. | Keep provenance in memory/test artifacts unless the contract allows extras. |
