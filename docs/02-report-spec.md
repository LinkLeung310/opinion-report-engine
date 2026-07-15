# Report Section Specification

This repository owns the section specification because the assignment references this
file but did not provide it. The document is developed incrementally with executable
SQL and tests; the assignment's public input and output contracts remain unchanged.

## Shared analysis scope

Every section uses the same immutable scope:

- `topic.tag` must be present in `articles.tags`;
- `dateRange.from` is inclusive at `00:00:00`;
- `dateRange.to` is inclusive through the end of the day, implemented as an exclusive
  boundary at the next day's `00:00:00`;
- fixture timestamps and day boundaries use `Asia/Shanghai`;
- SQL values are bound parameters and never interpolated into query text.

The fixture data is deliberately synthetic and deterministic. It resembles a plausible
multi-platform event only so that calculations, edge cases, and visual output can be
reviewed without leaking production data.

## `metrics` — 全网数据概览

Purpose: give the reader a compact, auditable overview of the selected monitoring scope.

Inputs: no section-specific input.

Raw query outputs:

- total article count;
- positive, neutral, and negative article counts;
- distinct platform count;
- summed likes, comments, shares, and favorites;
- peak calendar day and its article count.

Derived in Python:

- each sentiment ratio;
- total engagement;
- display formatting for counts, dates, and percentages.

No-data rule: zero matching articles returns `no_data`; ratios are not rendered as
invented zero-percent findings.

Traceability: the fixed query lives at
`src/report_engine/data/queries/metrics.sql`; fixture integration tests compare its
result with the known seeded scope.

## `verdict` — 核心结论

Purpose: open the report with a short, auditable executive judgment about current risk
and momentum. The model explains an already computed judgment; it does not choose the
risk level or infer causes.

Inputs: no section-specific input.

Fixed query plan (`verdict.v1`):

- hard-filter `articles` with the shared tag and complete date scope;
- count all, negative, high/critical negative, and critical-negative articles;
- count articles per Asia/Shanghai calendar day;
- return the peak day and peak count, plus the count on `dateRange.to`;
- use bound parameters only; the query will live at
  `src/report_engine/data/queries/verdict.sql` when the implementation slice begins.

Derived in Python:

- `negativeRatio` = negative articles / all articles;
- `highRiskNegativeRatio` = high-or-critical negative articles / negative articles;
- `latestVsPeakRatio` = articles on the final selected day / peak-day articles;
- `riskLevel` is `high` when `negativeRatio >= 50%` and
  `highRiskNegativeRatio >= 40%`; otherwise it is `medium` when
  `negativeRatio >= 30%` or at least one critical-negative article exists; all other
  non-empty scopes are `low`;
- `momentum` is `cooling` below 50% of the peak, `easing` from 50% through below 80%,
  and `sustained` at 80% or above.

Every displayed count, percentage, date, level, and momentum label is a `FactSet`
value sourced from `verdict.v1` or the named Python rule. Threshold comparisons use
unrounded decimal values; formatting happens only after classification.

Evidence: none. This section makes no article-level, causal, or thematic claim. Those
claims belong in evidence-backed sections such as `viewpoints` and must not leak into
the verdict prompt.

Charts: no standalone PNG. A decorative copy of the metrics chart would repeat the
next section without adding information. The verdict is a text-first decision block;
the report-level chart contract is fulfilled by analytical sections where a chart is
meaningful.

Narration contract:

- at most one narrator operation after successful query and calculation;
- Chinese heading `核心结论`, followed by one concise judgment paragraph and no more
  than three decision bullets;
- only approved facts may appear; no new number, cause, recommendation, quotation, or
  article claim is allowed;
- the deterministic stub renders the same structure for automated tests.

No-data rule: zero matching articles returns `no_data`, renders a visible Chinese
absence message, and performs no narrator or chart operation. A query, calculation,
or narration error returns `failed` with a safe stage-specific message while later
sections continue.

## `trend` — 热度趋势

Purpose: show how discussion volume and sentiment composition change across the full
selected calendar range, including quiet days that would otherwise disappear from the
timeline.

Inputs: no section-specific input.

Fixed query plan (`trend.v1`):

- generate every Asia/Shanghai calendar day from `dateRange.from` through
  `dateRange.to`;
- hard-filter articles with the shared tag and half-open timestamp scope;
- left-join daily article counts onto the complete calendar series;
- return total, positive, neutral, and negative counts for every day, with explicit
  zeros for days without matching articles;
- use bound `topic_tag`, timestamp boundaries, calendar boundaries, and timezone only;
  the query will live at `src/report_engine/data/queries/trend.sql`.

Derived in Python:

- `articles` = sum of all daily totals;
- `activeDays` = calendar days with at least one matching article;
- `peakDay` and `peakArticles`, with the earliest day winning an equal-count tie;
- `peakShare` = peak-day articles / all articles;
- `finalDayArticles` and `finalVsPeakRatio` = final selected day / peak day;
- display-ready daily labels and chart-title facts. Ratios use unrounded decimals and
  are formatted only after calculation.

Every aggregate and displayed number is a `FactSet` value sourced from `trend.v1` or a
named Python calculation. Daily rows remain deterministic chart data and retain the
query identifier.

Evidence: none. This section describes measured volume and sentiment composition only;
it must not infer causes or quote article-level claims.

Charts: one `daily-sentiment-trend.png` stacked bar chart. Each calendar day shows
positive, neutral, and negative counts using the required sentiment colors. The title
states the computed peak insight (for example, `3/20 达峰，单日 3 篇内容`), the y-axis is
article count, and long ranges thin x-axis labels to at most ten readable ticks without
dropping data points. The chart uses the shared white-background, 150 dpi theme and
embedded Chinese font.

Narration contract:

- at most one narrator operation after successful query, calculation, and charting;
- Chinese heading `热度趋势` and one concise paragraph covering the peak, peak share,
  active-day coverage, and final-day change;
- only approved facts may appear; no new number, event cause, recommendation, or
  article claim is allowed;
- the deterministic stub renders the same facts and structure in automated tests.

No-data rule: an all-zero calendar series returns `no_data`, renders a visible Chinese
absence message, and performs no chart or narrator operation. Query, calculation,
chart, or narration errors return `failed` with a safe stage-specific message while
later sections continue.

## Remaining project-defined sections

The authoritative IDs and user-facing purposes are defined in
`docs/final-framework.zh-CN.md`. Each section will be expanded here, before its code is
implemented, with inputs, fixed SQL, derived facts, evidence selection, charts,
narration contract, and no-data behavior.
