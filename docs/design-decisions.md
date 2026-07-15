# Product and Architecture Decisions

The assignment's fixed contracts remain binding. Everything not specified by those
contracts is treated as product-design space owned by this project.

| ID | Decision | User-facing outcome |
|---|---|---|
| D-01 | Preset-first section builder with custom selection and ordering | Users start from C-suite/PR defaults without losing control |
| D-02 | Section status is `complete`, `no_data`, or `failed` | A real absence of data is not presented as a system error |
| D-03 | Show chapter progress and current stage | Users know what the generator is doing and how much remains |
| D-04 | One narrator operation with at most one bounded transport retry | Temporary failures recover without unbounded cost or waiting |
| D-05 | Add `generation` and safe `failures` metadata | The UI can show partial success without exposing technical secrets |
| D-06 | Separate UUID task IDs from versioned human-readable report IDs | Concurrent and repeated reports never overwrite each other |
| D-07 | Include the entire end date and disclose report timezone | Date-picker behavior matches user expectations |
| D-08 | Tag/date are hard filters; brand is optional context | The fixed input contract is preserved without inventing a brand field |
| D-09 | Internal FactSet plus concise methodology notes | Reports stay readable while every number remains auditable |
| D-10 | English narrative with preserved proper nouns and bilingual key quotes | Translation improves access without corrupting source evidence |
| D-11 | PDF is primary; ZIP bundle is secondary | Executives get one-click reading and reviewers retain full artifacts |
| D-12 | CatalogPublisher atomically updates `index.json` after bundle publication | A completed report immediately appears in report history |
| D-13 | n8n visualizes API submission, polling, and completion | Workflow observability improves without replacing required code |
| D-14 | Fixture timestamps, report day boundaries, and `generatedAt` use `Asia/Shanghai` | Chinese event dates and report-history timestamps use one explicit local timezone |
| D-15 | The repository supplies a synthetic, deterministic fixture dataset | Reviewers can verify every number without exposing production or claiming fabricated records are real |
| D-16 | ReportLab renders the first A4 PDF bundle with an embedded Noto Sans SC font | Reviewers get reproducible Chinese PDFs without installing a browser or system font |
| D-17 | Evidence-heavy sections may use Python-owned hybrid RAG after fixed SQL scope filtering, with validated Evidence ID citations | Qualitative findings remain relevant, diverse, testable, and traceable to real source records |
| D-18 | The `verdict` risk level and momentum use explicit Python thresholds, and the section has no redundant standalone chart | Executives get a stable, auditable opening judgment without model guesswork or decorative duplication |
| D-19 | The `trend` timeline includes zero-volume calendar days and stacks daily sentiment counts | Readers see real quiet periods and sentiment shifts instead of a compressed, misleading timeline |
| D-20 | `platforms` discloses volume ties, ranks negative concentration by negative count before rate, and groups chart rows after the top seven into `其他` | Readers see material platform differences without false winners, one-item rate distortion, or an unreadable long tail |
| D-21 | `severity` treats zero negative records as a valid no-data finding and selects at most three high-risk evidence records by deterministic severity/score/engagement/recency order without RAG | Readers see auditable risk concentration and real source examples without fabricated causes or opaque retrieval |
| D-22 | `risk` equally averages five transparent structured pressure ratios, labels the result a non-probability diagnostic index, and excludes/discloses executive-association and rumor dimensions absent from the schema | Readers can see which measured signals are elevated without false precision, keyword guessing, or invented risk claims |

The repository itself will define the 19-section specification, fixtures, examples,
gold-report visual baseline, metadata extensions, and catalog publishing behavior.
