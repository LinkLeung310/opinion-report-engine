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

## `viewpoints` — 主要观点

Purpose: present the strongest observed concerns, neutral explanations, and
supportive/easing views from real source records without turning a small evidence
sample into a population estimate. The section groups representative records; it does
not claim that the selected examples are exhaustive themes or audience segments.

Inputs: no section-specific input.

Fixed query plan (`viewpoints.v1`):

- hard-filter articles with the shared tag and complete half-open timestamp scope;
- return total positive, neutral, and negative article counts alongside candidate
  records carrying real external ID, title, summary, platform, timestamp, sentiment,
  and total engagement;
- within each sentiment, rank candidates by total engagement descending,
  `published_at` descending, then `external_id` ascending;
- select the highest-ranked record first, then prefer the highest-ranked record from
  a different platform for the second slot when one exists; otherwise use the next
  record from the same platform;
- return at most two records per sentiment and six records overall, ordered as
  negative, neutral, positive and then by the deterministic within-category rank;
- use only bound `topic_tag` and timestamp boundaries. The query will live at
  `src/report_engine/data/queries/viewpoints.sql`; it does not use generated SQL,
  embeddings, a vector store, a reranker, RAG, or n8n.

Derived in Python:

- `articles`, the three sentiment counts, and their unrounded shares;
- `evidenceCount`, selected count by sentiment, and selected platform count;
- the display category labels `质疑/反对`, `中性/解释`, and `支持/缓和`;
- one `EvidenceSet` containing the selected records in the fixed display order.

Every count and percentage is a `FactSet` value sourced from `viewpoints.v1` or a named
Python calculation. `evidenceCount` carries every selected source record ID. Evidence
selection is deliberately not used to estimate viewpoint prevalence; population
sentiment counts and shares remain separate facts.

Evidence: required. Each record preserves its real external ID, title, summary,
platform, timestamp, and sentiment. The narrator may only group or describe these
records. Every evidence bullet must show `[Evidence: <id>]` and preserve the approved
title and summary verbatim. Missing, duplicate, reordered, or unknown citations, or
modified source text, cause the section to fail safely. This deterministic selector is
the non-RAG M1 baseline; any future D-17 retriever must keep the same EvidenceSet and
citation-validation boundary and requires explicit approval.

Charts: none. The existing metrics chart already quantifies sentiment distribution;
adding another sentiment chart would duplicate information. `viewpoints` is a compact,
evidence-first text section.

Narration contract:

- at most one narrator operation after successful query and fact/evidence construction;
- Chinese heading `主要观点`, followed by available category blocks in the fixed
  negative, neutral, positive order and at most two evidence bullets per block;
- each bullet contains one approved citation, original title, original summary, and
  platform; it may use the category heading as framing but may not add an uncited
  cause, demographic, recommendation, background fact, or new number;
- the opening sentence may state the approved total and sentiment counts/shares, but
  must disclose that selected records are representative evidence rather than a
  complete theme census;
- the deterministic stub renders the same facts, category order, exact source text,
  and citations in automated tests.

No-data rule: zero scoped articles returns `no_data`, renders a visible Chinese absence
message, and performs no narrator operation. A scoped article with unusable blank
title/summary is a data/calculation failure rather than no data. Query, calculation,
evidence validation, or narration errors return `failed` with a safe stage-specific
message while later sections continue.

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

## `risk` — 风险评估

Purpose: decompose observed risk pressure into a small set of auditable signals so an
executive can see what is driving the assessment. The result is a diagnostic index of
the monitored data, not a probability, forecast, or claim about real-world harm.

Inputs: no section-specific input.

Fixed query plan (`risk.v1`):

- hard-filter articles with the shared tag and complete half-open timestamp scope;
- return total and negative article counts, plus high/critical negative count;
- return total platform count and the number of platforms containing at least one
  negative article;
- return the number of distinct Asia/Shanghai calendar days containing negative
  articles;
- return total engagement and negative-article engagement, where engagement is the
  stored sum of likes, comments, shares, and favorites;
- use bound `topic_tag`, timestamp boundaries, and timezone only. The query will live
  at `src/report_engine/data/queries/risk.sql` and returns one aggregate row even when
  the scope is empty.

Derived in Python:

- `sentimentPressure` = negative articles / all articles;
- `severityPressure` = high/critical negative articles / negative articles, or zero
  when the scope contains no negative article;
- `spreadPressure` = negative platforms / all active platforms;
- `persistencePressure` = negative-active calendar days / all selected calendar days;
- `amplificationPressure` = negative engagement / all engagement, or zero when the
  scope has no engagement;
- each signal is `low` below 40%, `medium` from 40% through below 70%, and `high` at
  70% or above. Comparisons use unrounded decimals;
- `riskSignalIndex` is the unweighted arithmetic mean of the five unrounded signal
  ratios. `riskLevel` uses the same low/medium/high thresholds, and high/medium/low
  signal counts are derived in code;
- the selected calendar-day count is calculated from the immutable scope. The five
  signals receive equal weight because this synthetic fixture provides no calibrated
  outcome labels that would justify learned or subjective weights;
- every query count, ratio, band, signal count, and index is carried by `FactSet` with
  `risk.v1` or a named `risk.*.v1` Python calculation identifier.

Capability boundary: the project framework names executive association and rumor as
possible risk dimensions, but the received schema has no structured executive-link or
rumor-verification field. This section must disclose those dimensions as unavailable
and exclude them from the index. It may not guess them from title/summary keywords,
external knowledge, or model inference.

Evidence: none. This section compares structured aggregate signals only. It may not
quote an article, identify a cause, diagnose intent, assert a rumor, claim executive
involvement, or use RAG.

Charts: one `risk-signal-index.png` horizontal five-bar chart. Each bar shows one
unrounded signal formatted as a percentage on a shared 0–100% scale; low, medium, and
high bands use the shared green, amber, and red colors. The title states the computed
overall index and high-signal count, and the axis explicitly labels the index as a
non-probability diagnostic. The chart uses the shared white-background, 150 dpi theme
and embedded Chinese font.

Narration contract:

- at most one narrator operation after successful query, calculation, and charting;
- Chinese heading `风险评估`, followed by one concise overall paragraph and no more
  than three bullets grouping sentiment/severity, spread/persistence, and amplification;
- the text must call the result a signal index rather than a probability or forecast,
  and must disclose that executive association and rumor verification were unavailable;
- every number, percentage, band, and dimension label comes from approved facts; no
  new cause, recommendation, article claim, intent, rumor, executive claim, or external
  knowledge is allowed;
- the deterministic stub renders the same facts and capability disclosure in automated
  tests.

No-data rule: zero matching articles returns `no_data`, renders a visible Chinese
absence message, and performs no chart or narrator operation. A non-empty scope with
zero negative articles remains `complete` and renders five explicit zero-pressure
signals. Query, calculation, chart, or narration errors return `failed` with a safe
stage-specific message while later sections continue.

## Remaining project-defined sections

The authoritative IDs and user-facing purposes are defined in
`docs/final-framework.zh-CN.md`. Each section will be expanded here, before its code is
implemented, with inputs, fixed SQL, derived facts, evidence selection, charts,
narration contract, and no-data behavior.
