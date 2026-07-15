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

## `platforms` — 平台表现

Purpose: compare where discussion volume, negative content, and audience interaction
are concentrated without mistaking a one-article platform for the dominant risk
channel.

Inputs: no section-specific input.

Fixed query plan (`platforms.v1`):

- hard-filter articles with the shared tag and complete half-open timestamp scope;
- group by the stored platform label;
- return article, positive, neutral, and negative counts for every platform;
- return summed likes, comments, shares, and favorites for every platform;
- order rows by article count descending, total engagement descending, then platform
  label ascending so equal-volume results remain deterministic;
- use only bound `topic_tag` and timestamp boundaries; the query will live at
  `src/report_engine/data/queries/platforms.sql`.

Derived in Python:

- `articles`, `platformCount`, and `totalEngagement` are sums across the returned rows;
- each platform receives `articleShare`, `negativeRatio`, `engagementShare`, and
  `engagementPerArticle`; ratios use unrounded decimals and are formatted only after
  calculation;
- `volumeLeaders` contains every platform tied for the highest article count, plus
  `leadingArticleCount` and `leadingArticleShare`; narration must disclose the tie
  rather than invent a single volume winner;
- `negativeLeader` is selected by negative article count, then platform negative ratio,
  total engagement, and platform label. Its facts include negative article count,
  share of all negative articles, and within-platform negative ratio. When the entire
  scope has no negative articles, these leader facts are absent instead of becoming a
  false zero-risk ranking;
- `engagementLeader` is selected by total engagement, then article count and platform
  label, with total engagement, engagement share, and engagement per article exposed
  as facts;
- display rows retain the first seven ranked platforms. Any remaining rows are summed
  into one explicit `其他` category, so totals and sentiment composition remain intact
  while the chart stays readable.

Raw platform counts and engagement components are sourced from `platforms.v1`.
Ratios, leaders, ties, and the optional `其他` row use named `platforms.*.v1`
calculation identifiers in the `FactSet`.

Evidence: none. This section compares structured platform aggregates only. It may not
infer why a platform performed differently, quote an article, characterize an audience,
or use RAG.

Charts: one `platform-performance.png` two-panel horizontal chart. The left panel
stacks positive, neutral, and negative article counts with the required sentiment
colors; the right panel shows total engagement for the same ordered display rows. The
title states the computed volume tie/winner and engagement leader, not a generic chart
name. Both panels use the shared white-background, 150 dpi theme and embedded Chinese
font; the chart displays at most eight rows including `其他`.

Narration contract:

- at most one narrator operation after successful query, calculation, and charting;
- Chinese heading `平台表现`, followed by one concise summary and no more than three
  comparison bullets covering volume concentration, negative concentration when it
  exists, and engagement concentration;
- every platform name, count, percentage, rank, and tie statement must come from the
  approved facts; no cause, demographic claim, article claim, recommendation, or new
  number is allowed;
- the deterministic stub renders the same facts and tie/no-negative branches in
  automated tests.

No-data rule: zero returned platform rows returns `no_data`, renders a visible Chinese
absence message, and performs no chart or narrator operation. Query, calculation,
chart, or narration errors return `failed` with a safe stage-specific message while
later sections continue.

## `severity` — 负面严重程度

Purpose: show how strongly negative coverage is classified, how concentrated the
high/critical risk is, and which real records make that risk concrete. The section
describes stored negative labels; it does not independently diagnose reputational harm.

Inputs: no section-specific input.

Fixed query plan (`severity.v1`):

- hard-filter articles with the shared tag and complete half-open timestamp scope,
  then retain only `sentiment = 'negative'` records;
- compute the total negative count; low, medium, high, critical, and missing severity
  counts; negative-score counts for 1 through 5; scored/missing-score counts; average
  negative score; total negative engagement; and high/critical engagement;
- rank evidence records by explicit severity order `critical > high > medium > low >
  missing`, then negative score descending, total engagement descending,
  `published_at` descending, and `external_id` ascending;
- return at most the first three ranked records with their real external ID, title,
  summary, platform, timestamp, and sentiment, alongside the repeated aggregate values;
- use only bound `topic_tag` and timestamp boundaries. The query will live at
  `src/report_engine/data/queries/severity.sql`; it does not use generated SQL,
  embeddings, similarity search, or a vector store.

Derived in Python:

- `highCriticalArticles` = high + critical articles and `highCriticalRatio` = that
  count / all negative articles;
- `criticalRatio` = critical articles / all negative articles;
- `highCriticalEngagementShare` = high/critical engagement / all negative engagement,
  with an explicit zero value when all engagement fields are zero;
- `averageNegativeScore` is formatted to one decimal only after PostgreSQL returns the
  unrounded average; missing score and severity counts remain visible data-quality facts;
- `highestObservedSeverity` follows the same explicit severity order and is absent only
  when every negative record lacks a severity label;
- every aggregate, percentage, average, category label, and evidence count is carried
  by `FactSet` with `severity.v1` or a named `severity.*.v1` calculation identifier.

Evidence: the query-approved top three records become one `EvidenceSet`. Each record
keeps its real external ID, title, summary, platform, publication time, and negative
sentiment. The shortlist is deterministic risk ranking, not semantic retrieval or RAG.
Any narrative claim about a record must include its allowed Evidence ID; an unknown ID,
unapproved title/summary, or unsupported explanation fails the section.

Charts: one `severity-distribution.png` two-panel chart. The left panel shows low,
medium, high, and critical severity counts; the right panel shows negative-score counts
from 1 through 5. A consistent green-to-red risk ramp is used, with critical anchored
to the required negative red. The title states the computed high/critical ratio, not a
generic chart name. The chart uses the shared white-background, 150 dpi theme and
embedded Chinese font. Missing-label counts are disclosed in narration rather than
silently drawn as a normal risk grade.

Narration contract:

- at most one narrator operation after successful query, calculation, evidence
  construction, and charting;
- Chinese heading `负面严重程度`, followed by one concise aggregate paragraph and no
  more than three evidence bullets;
- all numbers and severity labels come from approved facts; evidence bullets use only
  approved title/summary text and show the real Evidence ID;
- no new cause, audience intent, recommendation, diagnosis, external knowledge, or
  uncited article claim is allowed;
- the deterministic stub renders the same aggregate and approved-evidence structure in
  automated tests.

No-data rule: zero negative records returns `no_data`, renders the valid finding
`监测范围内未发现负面内容。`, and performs no chart or narrator operation. Query,
calculation, evidence, chart, or narration errors return `failed` with a safe
stage-specific message while later sections continue.

## Remaining project-defined sections

The authoritative IDs and user-facing purposes are defined in
`docs/final-framework.zh-CN.md`. Each section will be expanded here, before its code is
implemented, with inputs, fixed SQL, derived facts, evidence selection, charts,
narration contract, and no-data behavior.
