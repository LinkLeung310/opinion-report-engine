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

## Shared language contract

`language` selects one presentation pipeline, not separate section implementations.
For `en`, every engine-owned report title suffix, scope/method note, section heading,
status or failure message, fact label, fixed playbook label, chart title, legend, axis,
annotation, and PDF metadata title is English. A missing English string must fail a
test; it must not silently fall back to Chinese.

The engine does not translate or rewrite provenance-bearing content. User-supplied
topic text and `biz-impact` notes, stored platform/proper names, exact source titles and
summaries, and exact phrases or indicators extracted from those sources may retain
their original language. English narration must frame such content as preserved source
material rather than presenting an engine-owned Chinese label as a quotation. Numeric
facts keep the same raw value and provenance in both languages; only their display
labels, unavailable markers, units, and surrounding prose change.

The same rule applies to visible partial results: `no_data` and `failed` fragments are
localized before report assembly, and one failed English section cannot cause a Chinese
generic fallback. Charts receive the configured language explicitly so that image text
follows the same contract as Markdown, PDF, and metadata.

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

## `sentiment-evolution` — 情感演变

Purpose: show how the composition of positive, neutral, and negative coverage changes
across the selected period without confusing a percentage shift with a change in
discussion volume. This section complements `trend`: `trend` shows daily item counts,
while `sentiment-evolution` compares phase composition and always discloses the sample
size behind each percentage.

Inputs: no section-specific input.

Fixed query plan (`sentiment-evolution.v1`):

- generate every Asia/Shanghai calendar day from `dateRange.from` through
  `dateRange.to`;
- hard-filter articles with the shared tag and complete half-open timestamp scope;
- left-join daily positive, neutral, negative, and total article counts onto the
  complete calendar series, retaining explicit zero-volume days;
- use bound `topic_tag`, calendar boundaries, timestamp boundaries, and timezone only;
  the query will live at
  `src/report_engine/data/queries/sentiment_evolution.sql` and will not use generated
  SQL, article evidence, RAG, or n8n.

Derived in Python:

- divide the complete calendar into at most three chronological phases. Three or more
  days use `前期` / `中期` / `后期`; two days use `前期` / `后期`; one day uses `全期`;
- phase lengths differ by at most one day, and any remainder is assigned to earlier
  phases. A seven-day scope therefore becomes 3 / 2 / 2 calendar days;
- for each phase, sum total and sentiment counts, then calculate positive, neutral,
  and negative shares from unrounded decimals. A zero-volume phase retains three
  explicit zero shares and is not silently removed;
- identify the first and last populated phases. When two or more populated phases
  exist, calculate `negativeShareDelta` as last minus first in percentage points;
- classify the change as `负面占比上升` at +10 percentage points or more,
  `负面占比下降` at -10 points or less, and `基本稳定` between those thresholds.
  With only one populated phase, use `仅单阶段有数据` and do not imply a temporal
  trend;
- retain total articles, phase count, populated phase count, phase date ranges,
  phase sample sizes, sentiment counts/shares, comparison endpoints, signed delta,
  and direction in `FactSet` using `sentiment-evolution.v1` or named
  `sentiment-evolution.*.v1` calculation identifiers.

Evidence: none. The section describes structured sentiment labels and phase totals
only. It may not quote an article, explain why sentiment changed, identify a new theme,
infer audience intent, or use external knowledge.

Charts: one `sentiment-evolution.png` 100% stacked phase bar chart. Positive, neutral,
and negative shares use the required green, amber, and red colors. Every bar displays
its phase date range and `n=<article count>` so a high share based on a small sample is
visible. Zero-volume phases remain on the chart. The title states the last populated
phase's negative share and sample size rather than a generic chart name. The chart uses
the shared white-background, 150 dpi theme and embedded Chinese font.

Narration contract:

- at most one narrator operation after successful query, calculation, and charting;
- Chinese heading `情感演变`, followed by one concise paragraph comparing the first
  and last populated phases and one caution sentence separating composition from
  volume;
- state both endpoint sample sizes, both negative shares, the signed percentage-point
  change, and the approved direction. A 100% share must never be described without its
  article count;
- every number, date range, percentage, and direction comes from approved facts; no
  cause, article claim, recommendation, demographic statement, or new number is
  allowed;
- the deterministic stub renders the same endpoint and low-sample caveat in automated
  tests.

No-data rule: an all-zero calendar series returns `no_data`, renders a visible Chinese
absence message, and performs no chart or narrator operation. A scope with one
populated phase remains `complete` but explicitly states that temporal comparison is
insufficient. Query, calculation, chart, or narration errors return `failed` with a
safe stage-specific message while later sections continue.

## `keywords` — 关键词与话题

Purpose: show which exact phrases recur across the selected article set, how broadly
each phrase is represented, and whether any recurring phrase appears only in the late
part of the monitoring window. This M1 baseline is a transparent phrase signal, not a
claim that character n-grams are semantic topic clusters.

Inputs: no section-specific input.

Fixed query plan (`keywords.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp
  scope;
- return `external_id`, `title`, `summary`, `published_at`, and `sentiment` in stable
  publication-time / ID order;
- use only bound `topic_tag`, `from_inclusive`, `to_exclusive`, and `timezone_name`;
- the query will live at `src/report_engine/data/queries/keywords.sql`. SQL performs
  scope filtering only; it does not generate phrases, call text-search extensions, or
  use generated SQL, RAG, embeddings, an LLM, or n8n.

Derived in Python:

- normalize title and summary text with Unicode NFKC while retaining original source
  records for provenance;
- split on non-text boundaries. From each contiguous CJK run, generate exact 3–6
  character candidates; retain normalized ASCII/alphanumeric tokens of 3–32
  characters. Do not use a topic-specific vocabulary or hidden stopword list;
- count at most one occurrence per candidate per article. A candidate is recurring
  only when it appears in at least two distinct articles;
- when nested candidates have exactly the same source-record set, retain the longest
  phrase. Equal-length ties prefer more title documents and then lexical order. This
  avoids showing `负反馈` and `负反馈入口` as separate signals when both are backed by
  exactly the same records;
- rank the remaining candidates by distinct document count, title-document count,
  earliest appearance, and lexical order. Negative documents never influence rank,
  so the method does not manufacture a risk-heavy keyword list;
- retain at most eight display phrases. For each, calculate distinct document count,
  population coverage, positive/neutral/negative document counts, negative share,
  first/last local day, and the exact supporting source record IDs;
- split the complete calendar into an early and late window, assigning an odd extra
  day to the early window. A seven-day range becomes 4 / 3 days. A displayed phrase is
  `late-emerging` only when it appears in at least two late-window articles and zero
  early-window articles; otherwise it is not labelled new;
- retain total article count, recurring/display phrase counts, leading phrase ties,
  emerging phrase count/list, extraction thresholds, and every display-phrase metric
  in `FactSet` using `keywords.v1` or named `keywords.*.v1` calculation identifiers.
  Each phrase fact carries its supporting `source_record_ids`.

Evidence: no free-form `EvidenceSet` is passed to the narrator. Exact extracted phrases
are approved facts whose provenance is the title/summary source IDs recorded on each
fact. The narrator may repeat those phrase labels and calculated metrics, but may not
quote unseen text, assign a semantic topic name, explain a cause, infer intent, or
claim that phrase frequency equals public support.

Charts: one `keyword-coverage.png` horizontal stacked bar chart for at most eight
phrases. Each bar is the number of distinct supporting articles split by positive,
neutral, and negative sentiment using the required colors. Labels disclose the total
document count; late-emerging phrases, when present, receive a visible `后期新增`
marker. The title discloses all top-coverage ties rather than naming a false winner.
Use the shared white-background, hidden top/right spines, 150 dpi theme and embedded
Chinese font. Do not produce a word cloud: area-based word clouds are harder to audit,
less accessible, and unstable under small text changes.

Narration contract:

- at most one narrator operation after successful query, calculation, and charting;
- Chinese heading `关键词与话题`, followed by a concise summary of article count,
  recurring phrase count, leading coverage ties, and late-emerging result;
- mention at most five approved display phrases, always with document count and
  coverage; if a negative share is stated, include its distinct-document denominator;
- when no phrase meets the late-emerging rule, explicitly say no recurring late-only
  phrase met the two-document threshold instead of inventing a new issue;
- every phrase, count, percentage, date, tie, and emergence label comes from approved
  facts. No semantic cluster label, causal claim, recommendation, or new number may be
  introduced.

No-data rule: zero scoped articles returns `no_data`. A non-empty article set with no
phrase repeated across at least two articles also returns `no_data` with a distinct
message explaining that records exist but no recurring exact phrase met the threshold;
both paths skip charting and narration. Query, extraction/calculation, chart, or
narration errors return `failed` with a safe stage-specific message while later
sections continue.

## `engagement` — 互动传播

Purpose: explain the composition and concentration of the stored interaction counters
without mistaking heterogeneous platform counters for unique people, reach, support,
or a time series of when interactions occurred. This section expands the single total
shown by `metrics`; it does not replace the later, evidence-focused `top-content`
section.

Inputs: no section-specific input.

Fixed query plan (`engagement.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp
  scope;
- for every scoped record, calculate `total_engagement` as the stored sum of likes,
  comments, shares, and favorites. The sum is an operational counter total, not a
  deduplicated audience size;
- return one aggregate snapshot containing article count, positive-total-engagement
  article count, zero-interaction article count, and summed likes, comments, shares,
  favorites, and total engagement;
- rank records with positive total engagement by total engagement descending,
  `published_at` descending, then `external_id` ascending. Return at most five ranked
  records with real external ID, title, summary, platform, publication time, sentiment,
  all four component counters, and total engagement;
- return the count of all records tied at the positive maximum so a tie beyond the
  five displayed records cannot be presented as one winner;
- use only bound `topic_tag`, `from_inclusive`, and `to_exclusive`. The query will live
  at `src/report_engine/data/queries/engagement.sql`; it does not generate SQL, infer
  missing counters, use RAG/embeddings, call an LLM, or use n8n.

Derived in Python:

- `totalEngagement` is the sum of the four stored action totals. Each action receives
  an unrounded share of that total; an all-zero total retains explicit zero shares;
- `commentsAndShares` and `commentsAndSharesShare` show the combined count and share
  of comment/redistribution actions. The label must not be shortened to reach,
  amplification, or conversation rate;
- `engagementPerArticle` is total engagement / scoped articles. It is a raw arithmetic
  mean and is not an engagement rate because the schema has no impression, follower,
  or unique-user denominator;
- `leadingRecordCount` preserves every positive maximum tie. When a unique leader
  exists, expose its real ID and total; when several records tie, narration and the
  chart title disclose the tie rather than naming a false winner;
- `topRecordShare` and `topThreeRecordsShare` divide the first one and first up-to-three
  positive ranked-record totals by all engagement. `topThreeRecordCount` discloses the
  actual numerator population when fewer than three positive records exist;
- the first five positive ranked records become display rows. The first up to three
  become the evidence shortlist. Ranking measures stored counter concentration only;
  it is not an influence, quality, impact, or importance score;
- every aggregate, ratio, tie, rank, and displayed record counter is carried by
  `FactSet` with `engagement.v1` or a named `engagement.*.v1` calculation identifier.
  Record facts retain their exact source record IDs.

Evidence: the first up to three positive ranked records form one deterministic
`EvidenceSet`. Each preserves its real external ID, title, summary, platform,
publication time, and sentiment. The narrator may identify the record only by its
approved ID and exact title and may repeat its approved platform, sentiment, and
interaction counters. It may not infer why it received interactions, describe the
audience, treat likes as support, claim real-world reach, quote unseen content, or
introduce a new article. This is a fixed ranking, not semantic retrieval or RAG.

Charts: one `engagement-composition.png` two-panel chart when total engagement is
positive. The left panel shows likes, comments, shares, and favorites as four labelled
horizontal bars with their exact counts and shares. The right panel shows total
engagement for at most five ranked records; each bar uses the required positive,
neutral, or negative sentiment color and displays the total. Y-axis labels include the
real source record ID and a legible title, not an invented topic label. The insight
title states the computed top-record and top-three concentration, or the positive maximum
tie when one exists. Use the shared white background, hidden top/right spines,
150 dpi theme, and embedded Chinese font. Do not draw a publication-date engagement
trend: the schema stores article publication time, not when its interactions occurred.

Narration contract:

- at most one narrator operation after successful query, calculation, evidence
  construction, and, when applicable, charting;
- Chinese heading `互动传播`, followed by one concise paragraph covering the four
  counter totals and comment-plus-share share, then one concentration sentence and no
  more than three ranked-record bullets;
- each record bullet shows `[Evidence: <id>]`, the exact approved title, total
  engagement, and the four approved component counters. It may state platform and
  sentiment but may not add an interpretation of why the record ranked highly;
- disclose that the figures are stored raw counters whose definitions can vary by
  platform and that no impression/unique-user denominator is available;
- every count, percentage, rank, tie, ID, title, platform, and sentiment comes from
  approved facts/evidence. No cause, recommendation, audience claim, support claim,
  reach claim, engagement-rate claim, or new number is allowed;
- the deterministic stub renders the same facts, evidence order, and limitation
  disclosure in automated tests.

No-data rule: zero scoped articles returns `no_data`, renders a visible Chinese absence
message, and performs no chart or narrator operation. A non-empty scope with zero total
engagement remains `complete` and renders a deterministic zero-counter finding plus the
denominator limitation without charting, evidence selection, or narrator cost. Query,
calculation, evidence, chart, or narration errors return `failed` with a safe
stage-specific message while later sections continue.

## `media-social` — 媒体与社媒对比

Purpose: compare the captured volume and sentiment composition of records already
classified by the dataset as `media` or `social`. The user-facing labels are
`媒体内容` and `社交内容`; the section does not reinterpret those stored categories as
company audiences, consumer demographics, professional-vs-personal authorship, or a
claim about the whole media ecosystem.

Inputs: no section-specific input.

Fixed query plan (`media-social.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp
  scope;
- use the schema's constrained `source_type` field directly. Never derive source type
  from platform names, author names, title/summary text, an LLM, or an external lookup;
- return exactly one aggregate row for `media` and one for `social`, retaining an
  explicit zero row when a source type is absent;
- for each source type, return article count, positive/neutral/negative counts, and
  distinct platform count. Also return the scoped total article count and total
  negative article count needed for denominators;
- use only bound `topic_tag`, `from_inclusive`, and `to_exclusive`. The query will live
  at `src/report_engine/data/queries/media_social.sql`; it does not generate SQL, read
  free text, select article evidence, use RAG/embeddings, call an LLM, or use n8n.

Derived in Python:

- `articleShare` is each source type's article count divided by all scoped articles;
  all calculations retain unrounded decimals and format percentages only for display;
- within each populated source type, calculate positive, neutral, and negative shares.
  An absent source type has unavailable composition rather than three fabricated zero
  percentages;
- `negativePopulationShare` is the source type's negative count divided by all scoped
  negative articles. When the scope has no negative articles, retain explicit zero
  negative-population shares and disclose the zero denominator;
- identify the article-volume leader or full tie. Only when both source types contain
  at least one article, calculate `socialMinusMediaNegativeShare` in percentage points
  and identify the higher-negative-share source type or tie;
- when either source type is absent, retain `insufficient_group_coverage` and do not
  present the populated group's composition as a comparison against 0%;
- retain source-type counts, article shares, sentiment counts/shares, platform counts,
  negative-population shares, comparison availability, signed percentage-point delta,
  and all leader/tie states in `FactSet` using `media-social.v1` or named
  `media-social.*.v1` calculation identifiers.

Evidence: none. This section compares structured aggregate labels only. It may not
quote or identify an article, infer what an audience believes, explain why the groups
differ, assign demographic meaning, or use external knowledge or RAG.

Charts: one `media-social-comparison.png` two-panel chart for a non-empty scope. The
left panel shows stacked positive/neutral/negative article counts for `媒体内容` and
`社交内容`; the right panel shows the corresponding 100% composition and labels every
bar with its sample size. Both panels use the required green, amber, and red sentiment
colors. An absent group remains visible with `n=0 / 无样本` instead of a false 0%
composition. The insight title states the volume split and, when comparable, the
signed social-minus-media negative-share difference; a missing group produces a
coverage title instead. Use the shared white background, hidden top/right spines,
150 dpi theme, and embedded Chinese font.

Narration contract:

- at most one narrator operation after successful query, calculation, and charting;
- Chinese heading `媒体与社媒对比`, followed by one concise volume paragraph and one
  sentiment-composition paragraph;
- state both group sample sizes and article shares. When both groups are populated,
  state both negative counts, both within-group negative shares, and the signed
  percentage-point difference; when one is absent, state that the comparison is
  unavailable rather than treating no sample as neutral or zero-negative evidence;
- disclose that `media`/`social` is the stored source classification and that results
  describe captured records only. Small group sizes must remain visible whenever a
  percentage is stated;
- every count, percentage, delta, group label, leader, and tie comes from approved
  facts. No cause, audience claim, platform-quality judgment, recommendation,
  demographic statement, article claim, or new number is allowed;
- the deterministic stub renders the same facts, sample sizes, comparison-availability
  state, and classification limitation in automated tests.

No-data rule: zero scoped articles returns `no_data`, renders a visible Chinese absence
message, and performs no chart or narrator operation. A non-empty scope containing only
one source type remains `complete`, renders the chart with an explicit absent group,
and states that cross-group sentiment comparison is unavailable. A non-empty scope
with zero negative records in both populated groups also remains `complete` and reports
the valid zero-negative finding. Query, calculation, chart, or narration errors return
`failed` with a safe stage-specific message while later sections continue.

## `timeline` — 事件时间线

Purpose: show a compact chronology of observable records from first capture through
the volume peak to the last capture, with an explicitly tagged response when present.
The section presents selected evidence milestones; it does not claim a complete event
history, infer causality from ordering, or treat engagement as reach or impact.

Inputs: no section-specific input.

Fixed query plan (`timeline.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp
  scope, using the report timezone for local calendar days;
- calculate scoped article count and daily counts, then choose the earliest
  highest-volume day when multiple days tie;
- emit four role candidates when available: the earliest scoped record
  (`first_observed`), the earliest record carrying the exact structured tag
  `official-response` (`tagged_response`), the peak-day record with the highest stored
  total engagement (`peak_day_representative`), and the latest scoped record
  (`last_observed`);
- rank the peak-day representative by total engagement descending, then timestamp
  ascending and external ID ascending, where total engagement is the stored
  `likes + comments + shares + favorites` counter sum. Rank first/tagged-response candidates by
  timestamp ascending and external ID ascending; rank the last candidate by timestamp
  descending and external ID ascending;
- return at most four role rows plus scoped total, peak day/count, and number of
  response-tagged records. A record may appear in more than one role row and is merged
  in Python rather than duplicated for readers;
- preserve each candidate's real external ID, title, summary, platform, timestamp,
  sentiment, and total engagement. Use only bound `topic_tag`, `from_inclusive`,
  `to_exclusive`, and report timezone values. The query will live at
  `src/report_engine/data/queries/timeline.sql`; it does not generate SQL, use text
  heuristics, embeddings, RAG, an LLM, external search, or n8n.

Derived in Python:

- deduplicate candidates by external ID, combine their role labels in fixed role
  priority, then display milestones by timestamp ascending and external ID ascending;
- `articles`, `milestoneCount`, `peakDay`, `peakArticles`,
  `responseTaggedArticles`, and `observedCalendarDays`, where the observed span is the
  inclusive count of report-timezone calendar days from the first to last scoped
  record;
- user-facing role labels `首次收录`, `回应标签记录`, `峰值日代表`, and `最后收录`.
  `回应标签记录` means only that the stored record has the exact
  `official-response` tag; it does not independently verify speaker identity,
  authority, or response effectiveness;
- one `EvidenceSet` containing the deduplicated milestones in chronological display
  order. Each fact uses `timeline.v1` or a named `timeline.*.v1` Python calculation
  source, and selected evidence facts retain their real source IDs.

Evidence: required. Every displayed milestone keeps its approved Evidence ID, exact
title, exact summary, platform, timestamp, sentiment, and role label(s). Each narrative
milestone must show `[Evidence: <id>]` and preserve the approved title and summary
verbatim. Unknown, duplicate, omitted, or reordered citations, modified source text,
or evidence outside the query result causes the section to fail safely. Selection is
deterministic and non-RAG; a future retriever may not replace this boundary without a
separate approved decision.

Charts: one `event-timeline.png` horizontal milestone chart. All selected points use
equal marker size on a chronological x-axis and no quantitative y-axis; marker color
uses the required sentiment palette. Labels show local date/time, role label(s), and
Evidence ID, with deterministic offsets for same-day or overlapping points. The title
states the approved first-to-last observed span and milestone count, never a causal or
effectiveness claim. The chart uses the shared white background, hidden top/right
spines, 150 dpi theme, and embedded Chinese font. A single-point scope renders one
clearly labelled point rather than a false multi-stage progression.

Narration contract:

- at most one narrator operation after successful query, calculation, evidence
  construction, and charting;
- Chinese heading `事件时间线`, one bounded context sentence with total records, peak
  day/count, observed span, and milestone count, followed by milestones in exact
  chronological EvidenceSet order;
- each milestone states only its approved local timestamp, role label(s), platform,
  exact title, exact summary, sentiment, and Evidence ID. Stored engagement may be
  shown only for the peak-day representative and must be labelled a captured counter
  snapshot rather than reach, support, or causal impact;
- if no candidate has the response tag, say only that no scoped record carried the
  exact `official-response` tag. Do not claim that no response occurred. If multiple
  tagged records exist, disclose the count and identify the earliest selected record;
- no invented phase name, cause, consequence, speaker identity, response
  effectiveness, recommendation, external background, new evidence, or unapproved
  number is allowed. The deterministic stub renders the same facts, source text,
  role labels, and citation order in automated tests.

No-data rule: zero scoped articles returns `no_data`, renders a visible Chinese absence
message, and performs no evidence selection, chart, or narrator operation. One scoped
article and an all-same-day scope remain `complete`, but explicitly describe the
limited observed sequence and never manufacture additional stages. A missing
response-tagged candidate also remains `complete` with the precise tag-coverage
limitation above. Blank required source text, or query, calculation, evidence, chart,
or narration errors return `failed` with a safe stage-specific message while later
sections continue.

## `top-content` — 代表性内容

Purpose: compare content-level attention and structured risk signals in one auditable
shortlist. Unlike `engagement`, this section does not explain aggregate counter
composition or concentration; unlike `severity`, it does not describe the population
distribution of negative labels. It answers whether the records prominent in stored
interaction counters are the same records prominent in explicit high-risk fields.
Neither signal is a measure of reach, support, business impact, or causality.

Inputs: no section-specific input.

Fixed query plan (`top-content.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp
  scope; return real external ID, title, summary, platform, timestamp, sentiment,
  severity, negative score, all four stored interaction counters, and their sum;
- rank records with positive total engagement by total engagement descending,
  timestamp descending, then external ID ascending. The first up to three are
  `engagement_representative` candidates;
- define an explicit high-risk-signal candidate as a negative record whose stored
  severity is `high` or `critical`, or whose stored negative score is at least 4.
  This is a project selection rule over supplied labels, not an independent diagnosis;
- rank all high-risk-signal candidates by severity order `critical > high > medium >
  low > missing`, negative score descending with missing last, total engagement
  descending, timestamp descending, then external ID ascending. The first up to three
  are `risk_representative` candidates;
- union both candidate sets by external ID, retaining the population engagement rank
  and high-risk-candidate rank for each selected record. Return at most six records,
  plus scoped article count, positive-engagement record count, high-risk-signal
  candidate count, and total stored engagement;
- order selected records by `dual_signal` first, then `engagement_only`, then
  `risk_only`. Within each group use risk rank, engagement rank, and external ID, with
  unavailable ranks sorted last;
- use only bound `topic_tag`, `from_inclusive`, and `to_exclusive`. The query will live
  at `src/report_engine/data/queries/top_content.sql`; it does not generate SQL, infer
  risk from free text, use embeddings/RAG, call an LLM, search externally, or use n8n.

Derived in Python:

- assign each selected record exactly one display category: `双信号代表` when it is
  in both top-three sets, `仅高互动代表`, or `仅高风险代表`;
- `articles`, `positiveEngagementArticles`, `highRiskSignalArticles`,
  `selectedCount`, `dualSignalCount`, `engagementOnlyCount`, and `riskOnlyCount`;
- `selectedEngagement` and `selectedEngagementShare`, where the numerator is the
  deduplicated selected records' stored counter sum and the denominator is all scoped
  stored engagement. Zero total engagement yields an explicit zero share rather than
  division by zero;
- retain each record's real ranks, counters, severity, negative score, category, and
  classification availability. Do not collapse severity and negative score into a
  composite probability or silently reconcile conflicting/missing labels;
- one `EvidenceSet` containing selected records in fixed display order. Every fact
  uses `top-content.v1` or a named `top-content.*.v1` calculation source and keeps
  selected source record IDs where applicable.

Evidence: required whenever records are selected. Each record preserves its real
external ID, exact title and summary, platform, timestamp, and sentiment. Every
narrative bullet must show `[Evidence: <id>]`, preserve the approved title/summary
verbatim, and show only its approved category, ranks, stored counters, severity, and
negative score. Unknown, duplicate, omitted, or reordered citations, modified source
text, or evidence outside the fixed query causes safe section failure. This is a
deterministic cross-signal shortlist, not semantic retrieval or RAG.

Charts: one `top-content-signals.png` aligned two-panel chart when at least one record
is selected. Rows use the fixed EvidenceSet order and labels containing category,
Evidence ID, and a legible title. The left panel shows each record's total stored
engagement as horizontal bars colored by sentiment. The right panel shows the stored
severity category (`未分类/低/中/高/危`) and labels the negative score when present;
non-negative records display `不适用` instead of a fabricated zero risk. The chart
does not combine both axes into an influence score. Its title states the computed
dual-signal count and selected-record count. Use the shared white background, hidden
top/right spines, 150 dpi theme, and embedded Chinese font.

Narration contract:

- at most one narrator operation after successful query, calculation, evidence
  construction, and charting;
- Chinese heading `代表性内容`, followed by one context paragraph stating scoped
  article count, positive-engagement and high-risk-signal candidate counts, selected
  count, category counts, selected stored-engagement total/share, and denominator
  limitation;
- follow with selected evidence bullets in exact order. Each bullet states the
  approved category, real ranks when available, platform, sentiment, exact title and
  summary, total stored engagement, severity, negative score, and Evidence ID;
- describe only observed signals. Do not explain why a record received interaction,
  equate likes with support, call counters reach, infer audience size, diagnose harm,
  claim business consequences, or turn the shortlist into a complete content census;
- disclose that interaction counters can differ by platform and that the high-risk
  role is triggered by supplied structured labels. The deterministic stub renders the
  same facts, exact source text, limitations, and citation order in tests.

No-data rule: zero scoped articles returns `no_data`, renders a visible Chinese absence
message, and performs no evidence, chart, or narrator operation. A non-empty scope
with neither positive engagement nor a high-risk-signal candidate remains `complete`
and renders a deterministic no-qualifying-signal message without chart or narrator
cost. A shortlist containing only one signal type remains `complete`; it explicitly
states that cross-signal overlap is unavailable/zero rather than inventing the missing
type. Query, calculation, evidence, chart, or narration errors return `failed` with a
safe stage-specific message while later sections continue.

## `negative-themes` — 负面议题拆解

Purpose: explain which decision-relevant issue dimensions appear in negative summaries,
how much of the negative population each dimension covers, what explicit concerns or
requests are present, and where supplied high/critical labels concentrate. Unlike
`viewpoints`, this is a population cross-tab rather than a representative sentiment
sample; unlike `keywords`, it maps synonymous exact indicators into versioned dimensions
rather than ranking raw recurring phrases; unlike `severity`, it asks which issue
dimension carries the structured labels rather than restating their overall distribution.
It does not establish root cause, audience intent, actual harm, or a universal taxonomy.

Inputs: no section-specific input.

Fixed query plan (`negative-themes.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp scope;
  return scoped article count and negative article count plus every negative record's real
  external ID, title, summary, platform, timestamp, severity, negative score, and four
  stored interaction counters;
- order negative records by timestamp ascending and external ID ascending. SQL performs
  scope/sentiment filtering only; it does not assign themes, generate labels, use text
  search extensions, call an LLM, use embeddings/RAG, search externally, or use n8n;
- use only bound `topic_tag`, `from_inclusive`, and `to_exclusive`. The query will live at
  `src/report_engine/data/queries/negative_themes.sql` and always returns one aggregate row
  so zero-article and zero-negative scopes remain distinguishable.

Derived in Python with versioned codebook `negative-themes.codebook.v1`:

- normalize summary text with Unicode NFKC; titles remain evidence but never drive theme
  assignment. Assign a negative record to each dimension whose exact indicator occurs in
  its normalized summary. One record counts at most once per dimension and may belong to
  multiple dimensions;
- fixed dimensions and exact indicators are:
  - `user_agency` / `用户自主权`: `负反馈入口`, `表达不喜欢`, `用户控制感`, `选择权`,
    `纠偏成本`, `恢复原入口`, `恢复入口`;
  - `transparency` / `透明度与解释`: `推荐透明度`, `推荐原因不透明`, `说明实验范围`,
    `公开推荐与实验规则`;
  - `feedback_effectiveness` / `反馈有效性`: `不愿听取负面反馈`, `反馈是否生效`,
    `反馈机制`;
- independently mark `concern` when the same summary contains any of `担心`, `认为`,
  `质疑`, `不满`, `焦虑`, `担忧`, `困难`, `削弱`, `不愿`, `影响`, `增加`; mark
  `demand` for any of `要求`, `呼吁`, `希望`, `应当`, `需要`, `诉求`, `恢复`, `公开`,
  `说明`. A record may carry both roles, so role counts are not stacked or treated as
  mutually exclusive;
- a display theme requires at least two distinct negative records. Rank display themes by
  matched negative records descending, high/critical matched records descending, summed
  stored interaction descending, then fixed codebook order; retain at most three;
- for each displayed theme calculate matched negative records and negative-population
  share, concern/demand record counts, high/critical count and within-theme share, stored
  interaction total, platform count, matched indicator list, and all supporting source
  IDs. Also calculate scoped `articles`, `negativeArticles`, codebook-classified and
  unclassified negative counts/shares, display theme count, and total theme memberships;
- choose one representative source per displayed theme by severity `critical > high >
  medium > low > missing`, negative score descending with missing last, total stored
  interaction descending, timestamp descending, and external ID ascending. A source may
  truthfully represent more than one multi-label theme; the underlying `EvidenceSet` is
  deduplicated while the expected per-theme citation sequence may repeat its ID;
- every number is a `FactSet` value sourced from `negative-themes.v1` or a named
  `negative-themes.*.v1` Python calculation. Theme facts carry every matching source ID;
  representative facts carry the selected real source ID.

Evidence: required whenever a display theme exists. Each representative preserves its
real external ID, exact title and summary, platform, timestamp, and negative sentiment.
Each theme block must show its approved fixed label and one `[Evidence: <id>]` citation,
preserve the representative title/summary verbatim, and cite IDs in fixed theme order.
Unknown, missing, extra, or reordered theme citations, modified source text, a generated
theme label, or a citation outside the query result causes safe section failure. Repeated
citations are permitted only when the deterministic representative ID is shared by
multiple themes. This baseline is rule-based classification, not RAG or semantic
clustering; unmatched negative records remain visible as a limitation.

Charts: one `negative-theme-coverage.png` horizontal stacked bar chart for displayed
themes. Each bar splits matched records into high/critical (`#DC2626`) and other negative
records (a lighter red), so the total remains the theme's negative-document coverage.
Labels show matched count / all negative records, percentage, concern count, and demand
count; they explicitly note that roles and themes overlap. The title states the leading
fixed dimension and its negative-population coverage rather than a generic chart name.
Use the shared white background, hidden top/right spines, 150 dpi theme, and embedded
Chinese font. Do not stack concern and demand counts because the same source may be both.

Narration contract:

- at most one narrator operation after successful query, classification, fact/evidence
  construction, and charting;
- Chinese heading `负面议题拆解`, followed by scoped/negative counts, codebook classified
  and unclassified counts/shares, displayed theme count, and explicit disclosure that
  theme memberships and concern/demand roles overlap;
- render theme blocks in fixed ranked order. Each states only approved label, matched
  count/share with the negative denominator, concern/demand counts, high/critical count
  and within-theme share, matched indicator(s), and its representative evidence bullet;
- call these `议题维度` or `摘要信号`, not root causes, audience segments, prevalence
  outside the monitored records, or verified harm. The model may not rename dimensions,
  merge/split themes, invent an explanation, recommendation, demographic, external fact,
  or new number;
- disclose that this is a versioned exact-indicator baseline whose unmatched count bounds
  coverage. The deterministic Chinese/English stub renders the same facts, labels,
  limitations, exact source text, and citation sequence in automated tests.

No-data rule: zero negative records returns `no_data` with `监测范围内未发现负面内容。`
and performs no theme classification output, chart, evidence narration, or narrator
operation. A non-empty negative scope in which no dimension reaches two records remains
`complete` and renders a deterministic no-qualifying-theme/codebook-coverage message
without chart or narrator cost. One or more displayed themes remain `complete` even when
some negative records are unclassified; the unmatched count/share must stay visible.
Blank required source text, or query, classification, evidence, chart, or narration
errors return `failed` with a safe stage-specific message while later sections continue.

## `spread-path` — 可观测平台迁移

Purpose: show when discussion first becomes observable on each material platform and how
platform participation changes across the report calendar. Unlike `timeline`, this is a
platform-by-time population matrix rather than a compact event chronology; unlike `trend`,
it preserves the platform dimension instead of summing daily volume; unlike `platforms`,
it preserves entry timing and active days instead of aggregating the whole period. The
current schema contains no repost, quote, parent, referral, or canonical-source relation,
so this section does not claim an article-level transmission chain, platform-to-platform
causality, or the true origin of the event.

Inputs: no section-specific input.

Fixed query plan (`spread-path.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp scope;
  return real external ID, title, summary, platform, timestamp, sentiment, and all four
  stored interaction counters for every scoped record;
- order records by timestamp ascending and external ID ascending. SQL performs only
  scope filtering and does not infer a parent, source edge, repost relationship, platform
  transition, origin, or influence; it does not use embeddings/RAG, call an LLM, search
  externally, or use n8n;
- use only bound `topic_tag`, `from_inclusive`, and `to_exclusive`. The query will live at
  `src/report_engine/data/queries/spread_path.sql`. The repository receives the shared
  report-calendar boundaries from `AnalysisScope`, so zero-volume dates can remain visible
  without changing the public config contract.

Derived in Python:

- construct the complete report-timezone calendar and a platform-by-day article-count
  matrix, retaining explicit zero cells. Calculate scoped `articles`, distinct
  `platforms`, observed calendar days, multi-platform days, the maximum distinct platforms
  observed on one day, and every tied day attaining that maximum;
- for every platform calculate first and last observed timestamps, article count, negative
  article count, distinct active days, total stored interaction, and the real first-observed
  record. "First observed" means earliest record captured inside this scope, not event
  origin or first publication anywhere;
- rank platforms for material display by article count descending, total stored interaction
  descending, first-observed timestamp ascending, then platform name ascending. Retain at
  most six; report total, displayed, and omitted platform counts. Render retained platforms
  in first-observed timestamp order, with platform name as the deterministic display-only
  tie-breaker;
- assign a dense `entryWave` by distinct first-observed timestamp. Platforms with identical
  timestamps share the same wave and are not ordered semantically. Calculate displayed
  entry-wave count and the elapsed hours from the earliest to latest first observation
  across all scoped platforms; one platform yields zero elapsed hours rather than an
  invented cross-platform transition;
- retain the earliest-observed platform set and latest-new-platform set with tie disclosure.
  Do not create graph edges or an arrow-separated "A spread to B" sequence from temporal
  adjacency alone;
- one `EvidenceSet` contains the first-observed record for each displayed platform in fixed
  display order. Every fact uses `spread-path.v1` or a named `spread-path.*.v1` Python
  calculation source; platform facts keep their supporting source IDs and first-record
  facts keep the selected real external ID.

Evidence: required whenever at least two platforms are displayed. Each first-observed record
preserves its real external ID, exact title and summary, platform, timestamp, and sentiment.
Every platform entry bullet must show one `[Evidence: <id>]`, preserve the exact source text,
and cite IDs in fixed display order. Unknown, duplicate, omitted, or reordered citations,
modified text, or evidence outside the query result causes safe section failure. This is
deterministic first-observation selection, not semantic retrieval or RAG.

Charts: one `platform-time-matrix.png` annotated heatmap when at least two platforms are
displayed. Columns are every report-calendar day; rows are displayed platforms in fixed
first-observed order; cell labels are article counts including zero. Count intensity uses a
single non-sentiment accent scale rather than the positive/neutral/negative palette, because
color represents volume, not sentiment. Each platform's first non-zero cell receives a
visible outline and its `entryWave` number; shared wave numbers expose exact-time ties. The
title states platform count and measured first-observation interval. A chart note says that
wave order is captured timing, not a repost edge or causal path. Use the shared white
background, hidden top/right spines, 150 dpi theme, embedded Chinese font, at most six rows,
and at most fourteen x-axis labels while retaining every daily matrix column.

Narration contract:

- at most one narrator operation after successful query, calculation, evidence construction,
  and charting;
- Chinese heading `传播路径（可观测顺序）`, followed by scoped article/platform counts,
  displayed/omitted counts, report-calendar span, multi-platform days, maximum same-day
  platform coverage with tied day(s), entry-wave count, and first-observation interval;
- render displayed platform bullets in fixed order. Each states only entry wave, approved
  local first/last timestamps, article/negative/active-day/stored-interaction facts, exact
  first-record title and summary, sentiment, and Evidence ID;
- call the result `首次收录顺序`, `平台参与轨迹`, or `可观测迁移`, never an origin, repost
  chain, referral route, audience journey, causal handoff, or proof that one platform drove
  another. Disclose omitted platforms and exact-time entry ties when present;
- explicitly state that the schema lacks relational propagation edges. The model may not
  invent a source node, transition arrow, cause, audience movement, recommendation, external
  fact, new evidence, or unapproved number. The deterministic Chinese/English stub renders
  the same facts, exact source text, limitations, and citation order in automated tests.

No-data rule: zero scoped articles returns `no_data`, renders a visible Chinese absence
message, and performs no evidence, chart, or narrator operation. A non-empty scope with only
one platform remains `complete` and renders a deterministic single-platform/no-cross-platform-
comparison message without chart or narrator cost. Two or more platforms first observed at
the exact same timestamp remain `complete` with a shared entry wave and explicit tie rather
than a fabricated order. Blank required source text, or query, calculation, evidence, chart,
or narration errors return `failed` with a safe stage-specific message while later sections
continue.

## `response` — 回应前后对比

Purpose: compare like-for-like observation windows immediately before and after a
user-supplied response date. Unlike `trend`, this is not a full-range time series;
unlike `sentiment-evolution`, it does not infer generic phases; unlike `timeline`, it
does not select response records or reconstruct chronology. It reports an observed
before/after association only and never claims that a response caused, resolved, or
failed to change public opinion.

Inputs: required section-specific `input.responseDate`, using strict ISO `YYYY-MM-DD`
syntax. The date must fall strictly inside the shared report range with at least one
complete report-timezone calendar day available on both sides. Missing input follows
the planner's existing section-local input failure. Invalid syntax, an out-of-range
date, or a boundary date returns a section-local `INPUT` failure with an actionable
message. The engine must not infer this input from an `official-response` tag.

Comparison-window decision:

- exclude the complete `responseDate` calendar day. The public input has date rather
  than time precision, so assigning same-day records to either side could silently mix
  content published before and after the response;
- set `windowDays` to the smaller of seven days, complete in-scope days before the
  response date, and complete in-scope days after it. The pre window is
  `[responseDate - windowDays, responseDate)` and the post window is
  `(responseDate, responseDate + windowDays]`, using report-timezone calendar dates;
- use equal-length windows even when more report days are available on one side. Report
  all response-day and outside-matched-window exclusions so the fair comparison does
  not masquerade as full-range coverage.

Fixed query plan (`response.v1`):

- hard-filter articles with the shared topic tag and complete half-open timestamp
  scope; return local `published_day`, sentiment, and whether each record has the exact
  `official-response` tag;
- order by local day and sentiment. SQL performs only scope filtering and exposes the
  exact tag signal; it does not choose the response date, assign comparison windows,
  calculate an effect, use embeddings/RAG, call an LLM, search externally, or use n8n;
- use only bound `topic_tag`, `from_inclusive`, `to_exclusive`, and `timezone_name`.
  The query will live at `src/report_engine/data/queries/response.sql`.

Derived in Python:

- retain scoped `articles`, `responseDate`, `windowDays`, the exact pre/post date
  boundaries, `comparisonArticles`, `responseDayArticles`,
  `responseDayOfficialTaggedArticles`, and `outsideMatchedWindowsArticles`;
- for each matched side calculate article count, daily average, and positive, neutral,
  and negative counts and shares. A share is unavailable when that side has zero
  articles; it is never rendered as a measured 0%;
- calculate post-minus-pre article delta, daily-average delta, and article percent
  change only when the pre count is non-zero. Calculate sentiment-share deltas in
  percentage points only when both side denominators are non-zero. Retain unrounded
  values for comparison and round only for display;
- an exact `official-response` tag is coverage metadata for the excluded response day,
  not a substitute for the user's date and not proof of speaker identity, authority,
  causality, or effectiveness;
- every fact uses `response.v1` or a named `response.*.v1` Python calculation source.
  This aggregate section has no `EvidenceSet`; qualitative response-record selection
  remains the distinct responsibility of `timeline`.

Evidence: none. The section does not quote or rank individual records and does not use
retrieval or RAG.

Charts: one `response-window-comparison.png` stacked sentiment bar chart when at least
one comparison window contains articles. The two bars represent the equal-length pre
and post windows and use the required positive/neutral/negative colors. Each bar labels
the total, daily average, and negative share, with unavailable displayed explicitly for
a zero-sample side. The title states the measured comparison rather than an effect. A
chart note gives both exact date ranges, says the response day was excluded, and says
that observed before/after difference is not causal attribution. Use the shared white
background, hidden top/right spines, embedded Chinese font, and 150 dpi theme.

Narration contract:

- at most one narrator operation after successful input validation, query,
  calculation, and charting;
- Chinese heading `回应前后对比`, followed by the user-supplied date, exact matched
  windows and `windowDays`, response-day exclusion, scoped/comparison/excluded counts,
  and exact response-day tag coverage;
- compare only approved pre/post article totals, daily averages, sentiment counts and
  shares, article percent change when available, and sentiment-share percentage-point
  deltas when available. State missing denominators as unavailable rather than filling
  in zero or asking the model to calculate;
- use terms such as `回应前观察窗口`, `回应后观察窗口`, and `观察到的差异`. Never say that
  the response caused, reduced, increased, resolved, failed, worked, or was ineffective.
  Do not invent a response time, speaker identity, recommendation, cause, external fact,
  evidence, or new number;
- disclose the date-only limitation and that equal windows improve comparability but do
  not establish a counterfactual. The deterministic Chinese/English stub renders the
  same facts, unavailable values, exclusions, and limitations in automated tests.

No-data rule: zero scoped articles, or no articles in either matched comparison window,
returns `no_data` with a visible absence message and performs no chart or narrator
operation. If exactly one side has zero articles, the section remains `complete`: it
reports the observed appearance/disappearance, keeps zero-denominator shares and rate
changes unavailable, and renders the chart honestly. Invalid input returns `failed`
before the query runs. Query, calculation, chart, or narration errors return `failed`
with a safe stage-specific message while later sections continue.

## `benchmark` — 历史事件对标

Purpose: compare the current user-selected event window with an independent historical
event over the same number of complete calendar days. Unlike `metrics`, this section
does not restate one population; unlike `response`, it has no intervention cutpoint;
unlike `spread-path`, it does not infer movement. It reports measured differences
between two captured cohorts and never ranks the intrinsic importance, success, or
severity of the underlying real-world events.

Inputs: required section-specific `input.comparisonTag`. It must be a non-blank string
without leading or trailing whitespace and must differ from `topic.tag`. Missing,
non-string, blank, padded, or identical input returns a section-local `INPUT` failure
before SQL. The engine must not invent, search for, or normalize a substitute event.

Equal-window and independence decision:

- the current cohort is the shared topic tag within the configured complete half-open
  `dateRange`; its calendar length is the inclusive configured day count;
- comparison candidates must contain the exact `comparisonTag` and must not contain the
  current topic tag. This disjoint rule prevents the same source record from appearing
  on both sides when a generic or nested tag is supplied;
- anchor the historical comparison window at the earliest local calendar day among
  disjoint comparison candidates, then include exactly the same number of complete
  calendar days as the current report range. Later comparison records are outside the
  matched lifecycle window and are counted/disclosed rather than silently included;
- these equal durations improve calendar comparability but do not equalize collection
  intensity, platform coverage, audience size, counterfactual conditions, or event
  meaning. The report must disclose both exact windows and sample sizes.

Fixed query plan (`benchmark.v1`):

- one parameterized statement returns two fixed cohort rows in `current`, `comparison`
  order. The current row aggregates the shared scope. A CTE finds the earliest disjoint
  comparison day, builds the equal-day historical window, and aggregates only that
  window while also counting later excluded comparison records;
- each row returns tag, window boundaries, calendar days, article count, positive,
  neutral and negative counts, distinct platform count, high/critical negative count,
  and stored like/comment/share/favorite sum. SQL never interpolates either tag;
- bind only `topic_tag`, `comparison_tag`, `from_inclusive`, `to_exclusive`,
  `calendar_days`, and `timezone_name`. SQL does not generate a conclusion, use text
  similarity, embeddings/RAG, an LLM, external search, or n8n;
- the query will live at `src/report_engine/data/queries/benchmark.sql`.

Derived in Python:

- validate the two-row order, disjoint tags, exact equal calendar length, non-negative
  counts, sentiment totals, high/critical subset, and comparison exclusion count;
- for each cohort retain tag, exact date range, calendar days, articles, daily average,
  sentiment counts/shares, platform count, high/critical-negative share of all articles,
  stored engagement total, and stored engagement per article. Any zero denominator is
  unavailable rather than a measured zero percentage or rate;
- calculate current-minus-comparison article and daily-average deltas, negative-share
  and high/critical-share percentage-point deltas, and stored-engagement-per-article
  delta only when required denominators exist. Raw values remain unrounded; formatting
  occurs only for display;
- every fact uses `benchmark.v1` or a named `benchmark.*.v1` Python source. This is an
  aggregate section with no `EvidenceSet`; it does not quote or rank individual records.

Evidence: none. The fixed tag cohorts and aggregate facts are the complete approved
context; retrieval and RAG are not used.

Charts: one `historical-benchmark-comparison.png` two-panel chart when both cohorts have
data. The left panel uses grouped bars for article daily average and stored engagement
per article, with exact sample sizes and separate axes/labels rather than combining
unlike units into one score. The right panel uses two 100% stacked sentiment bars in the
required colors and labels the negative share and high/critical share. The title states
one measured difference, both exact date ranges appear in a note, and the note says
equal windows do not prove equal collection conditions or intrinsic event severity.
Use the shared white background, hidden top/right spines, embedded Chinese font, and
150 dpi theme.

Narration contract:

- at most one narrator operation after successful input validation, query,
  calculation, and charting;
- Chinese heading `历史事件对标`, followed by current/comparison tags, exact equal-day
  windows, article sample sizes, platform coverage, and excluded later historical rows;
- compare only approved daily average, sentiment composition, high/critical share, and
  stored engagement per article with exact signed deltas when available. Always label
  interaction values as stored counters, not reach, engagement rate, or audience size;
- say `本次收录样本中` and `观察到的差异`. Never say one event was objectively larger,
  more important, more harmful, more successful, or caused a business outcome. Do not
  invent a historical event name, date, cause, audience, recommendation, source record,
  external fact, or new number;
- disclose that equal calendar length does not align collection intensity, platform
  coverage, audiences, or real-world context. The deterministic Chinese/English stub
  renders the same facts, unavailable values, and limitations in automated tests.

No-data rule: zero current-cohort articles, no disjoint comparison candidates, or zero
comparison articles inside the anchored equal window returns `no_data` with retained
facts where available and performs no chart or narrator operation. Later comparison
records outside the equal window alone do not change this rule. Invalid input returns
`failed` before SQL. Query, calculation, chart, or narration errors return `failed` with
a safe stage-specific message while later sections continue.

## `biz-impact` — 商业影响

Purpose: connect measured public-opinion pressure with business context supplied by
the user, while keeping the two provenance classes visibly separate. The section helps
an executive identify plausible impact paths and verification gaps; it does not claim
that captured discussion caused a commercial outcome or turn an unverified note into a
database fact.

Inputs: required section-specific `input.notes`.

- `notes` must be a string. The engine trims the ends, converts line breaks and other
  ordinary whitespace runs to one space, and then requires 1–1000 Unicode characters;
  this accepts normal pasted prose without accepting an unbounded prompt;
- NUL and non-whitespace C0/C1 control characters are rejected. Missing, non-string,
  empty-after-normalization, control-character, or over-limit input returns a
  section-local `INPUT` failure before SQL;
- the normalized text is preserved as user-supplied context. It is data, never model
  instructions: delimit it separately in the narrator request and ignore any request
  inside it to change rules, expose secrets, invent facts, or call tools;
- numeric or causal statements in `notes` remain allowed because they may be useful
  business context, but every display must label them `用户提供，数据库未验证` /
  `user-provided, not verified by the report database`. They must not become calculated
  facts, evidence citations, or assertions by the report.

Provenance boundary:

- fixed SQL and named Python calculations form the `FactSet`;
- normalized `notes` form a separate user-context object with source
  `report-config.sections[biz-impact].input.notes` and verification status
  `unverified`. They are not inserted into `FactSet` or `EvidenceSet`;
- this explicit separation must survive prompt construction, deterministic stub
  rendering, Markdown/PDF output, and tests. A narrator may relate an approved signal
  to the supplied context using conditional language, but may not merge their
  provenance or promote the context to a measured finding.

Fixed query plan (`biz-impact.v1`):

- hard-filter articles with the shared exact tag and complete half-open date scope;
- return total, positive, neutral, and negative article counts; distinct platform and
  active-day counts; peak local calendar day and its article count; high/critical
  negative count; and summed stored likes, comments, shares, and favorites;
- use only bound `topic_tag`, `from_inclusive`, `to_exclusive`, and `timezone_name`.
  SQL does not inspect `notes`, generate a conclusion, search external systems, use an
  LLM, embeddings/RAG, or n8n;
- the query will live at `src/report_engine/data/queries/biz_impact.sql`.

Derived in Python:

- validate non-negative counts, sentiment totals, high/critical subset constraints,
  calendar coverage, and peak consistency;
- retain `articles`, the three sentiment counts and shares, `platformCount`, selected
  calendar days, `activeDays`, active-day coverage, `peakDay`, `peakArticles`, peak
  share, high/critical-negative count, its share of negative records and of all
  records, four stored interaction counters, total stored interaction, stored
  interaction per article, and comments-plus-shares;
- organize, without scoring, two measured signal lenses: `舆情声誉压力` uses the
  negative and high/critical facts; `公开讨论应对复杂度` uses captured volume,
  platform spread, active-day/peak concentration, and stored comment/share counts.
  These are descriptive lenses, not probabilities, monetary exposure, customer-service
  workload, reach, audience size, or causal impact;
- attach a third `业务结果核验缺口` lens that names the internal outcome data absent
  from the report database. If the notes mention sales, conversion, churn, support
  demand, traffic, share price, or another outcome, the narration may say that the
  claim requires the corresponding internal time series and comparison baseline; it
  may not invent either one;
- every numeric value uses `biz-impact.v1` or a named `biz-impact.*.v1` Python source.
  Ratios remain unrounded until display. Zero denominators are unavailable rather than
  fabricated zero-percent findings.

Evidence: none. This is an aggregate section and does not quote, rank, or interpret
individual titles or summaries. `notes` are explicitly unverified user context, not an
article `EvidenceSet`; retrieval and RAG are not used.

Charts: none. The schema contains no sales, conversion, churn, support-volume, traffic,
market, or other verified business-outcome series to plot. Repeating sentiment,
timeline, platform, or engagement charts would duplicate other optional sections and
could visually imply a measured business effect. The chapter therefore uses a compact
text structure with provenance labels; a future outcome chart requires a new verified
data contract and design decision.

Narration contract:

- at most one narrator operation after successful input validation, query,
  calculation, and separate user-context construction;
- Chinese heading `商业影响`, followed by three visibly distinct blocks: `可观测舆情信号`,
  `用户提供的业务背景（未验证）`, and `业务结果核验缺口`. English uses equivalent
  headings and preserves the same provenance labels;
- disclose exact approved sample, pressure, coverage, peak, and stored-interaction
  facts. Label heterogeneous stored counters as a captured operational snapshot, not
  engagement rate, reach, unique users, support workload, or business loss;
- the relationship between facts and notes may be described only as a hypothesis or a
  condition to verify, using wording such as `与该背景同时观察到`, `可能的影响路径`, and
  `尚不能据此确认`. Never say the public discussion caused or proves a revenue, sales,
  conversion, churn, customer, market, operational, or reputational outcome;
- do not calculate from numbers embedded in `notes`, add external knowledge, invent a
  confidence/severity/impact score, prescribe response actions, or introduce an
  Evidence ID. Recommendations remain the responsibility of the separately selected
  `recommendations` section;
- the deterministic Chinese/English stub renders the same approved facts, normalized
  context, provenance labels, hypotheses, and limitations in automated tests.

No-data rule: zero scoped articles returns `no_data` with retained zero facts and a
visible message that the supplied context cannot be combined with an empty monitoring
scope; it performs no narrator operation. A non-empty scope with zero negative records
remains `complete` and states that the selected data shows no measured negative
pressure, while keeping the notes unverified. Invalid input returns `failed` before
SQL. Query, calculation, context construction, or narration errors return `failed`
with a safe stage-specific message while later sections continue. No path creates a
chart.

## `recommendations` — 行动建议

Purpose: turn approved, observable negative-pressure signals into a short, prioritized
human-review plan. The section answers what the responsible team should verify or
prepare next and why that action was selected. It is a versioned decision-support
playbook, not autonomous execution, legal advice, a guarantee of outcome, or a place for
the narrator to invent generic public-relations tactics.

Inputs: no section-specific input. The section uses only the shared exact tag and complete
date range. It must work when selected by itself and must not depend on another section
being enabled or silently read another section's rendered text.

Fixed query plan (`recommendations.v1`):

- hard-filter articles with the shared exact tag and half-open timestamp range;
- return scoped article count and every negative record's real external ID, title,
  summary, platform, timestamp, sentiment, supplied severity/negative score, and four
  stored interaction counters in chronological/ID order;
- use only bound `topic_tag`, `from_inclusive`, and `to_exclusive`. SQL does not create an
  action, priority, owner, deadline, theme, score, or conclusion; call an LLM; use
  embeddings/RAG; search externally; or use n8n;
- the query will live at `src/report_engine/data/queries/recommendations.sql`.

Derived in Python:

- validate population counts, unique chronological source records, non-empty source
  text, supplied labels/scores, and non-negative stored counters;
- reuse the public `negative-themes.codebook.v1` exact-indicator definitions and its
  minimum two-record display threshold. Reuse is deliberate: recommendations may act on
  an approved issue dimension but must not introduce a second hidden classifier or let
  the model rename/merge dimensions;
- calculate scoped and negative counts/shares, high/critical-negative count/share,
  codebook-classified and unclassified negative counts/shares, candidate/selected/
  omitted action counts, and at most four selected actions;
- build candidates from this fixed action codebook:
  - `triage_high_risk`: eligible when any negative record has supplied `high` or
    `critical` severity; suggested owners `公关负责人、事件责任人` / `PR lead, incident
    owner`; horizon `立即` / `immediate`; action is to assign each high/critical record an
    owner/status and document whether escalation is required;
  - `restore_user_control`: eligible when the `user_agency` dimension covers at least two
    negative records; suggested owners `产品/体验、客服` / `Product/UX, Support`; action is
    to validate the affected control path, prepare step-by-step guidance, and log
    unresolved cases;
  - `explain_change`: eligible when the `transparency` dimension covers at least two
    negative records; suggested owners `产品、公关` / `Product, PR`; action is to prepare
    one source of truth covering changed/unchanged scope and feedback or rollback
    boundaries;
  - `close_feedback_loop`: eligible when the `feedback_effectiveness` dimension covers
    at least two negative records; suggested owners `公关、客服运营` / `PR, Support
    operations`; action is to acknowledge the approved concern, publish an intake/
    response cadence, and maintain a visible status;
  - `review_unresolved_negative`: eligible only when negative records exist but none of
    the preceding candidates qualify; suggested owners `舆情分析、事件责任人` /
    `Analyst, incident owner`; horizon `72小时内` / `within 72 hours`; action is to
    manually review the highest-ranked unresolved record and decide whether a versioned
    playbook/codebook extension is warranted;
- select `triage_high_risk` first, then eligible theme actions in the existing transparent
  theme order (matched records, high/critical records, stored interaction, fixed codebook
  order). Use the fallback only if no other candidate exists, retain at most four, and
  expose omitted candidate count. This lexicographic order is the displayed priority; do
  not create a composite risk, confidence, impact, or expected-value score;
- theme-action horizon is `24小时内` / `within 24 hours` when its matched records include
  any high/critical label or explicit demand marker, otherwise `72小时内` / `within 72
  hours`. Horizon is a playbook response target, not an observed event deadline;
- choose the high-risk/fallback representative by supplied severity, negative score,
  stored interaction, recency, and ID; theme actions use their existing deterministic
  representative. Every action fact carries all trigger record IDs and the representative
  ID. Fixed action/owner/horizon/verification text is itself versioned codebook data.

Evidence: required for every selected action. Each action cites exactly one approved
representative and preserves its real external ID, title, summary, platform, timestamp,
and negative sentiment. The `EvidenceSet` deduplicates shared representatives, while the
expected action citation sequence may repeat an ID when the same record truthfully
supports multiple actions. Missing, unknown, extra, or reordered citations, changed
source text, or an action without its approved trigger records causes safe section
failure. This deterministic baseline does not use retrieval or RAG.

Charts: none. The ranked action blocks already express decision order. A bar, scorecard,
or traffic light would imply quantified effectiveness/confidence and duplicate risk/theme
charts without outcome data. Each text block shows priority rank, horizon, fixed action,
suggested role owners, trigger facts, representative evidence, and verification checklist.

Narration contract:

- at most one narrator operation after successful query, action construction, `FactSet`,
  and `EvidenceSet` validation;
- Chinese heading `行动建议` and English `Recommended actions`; disclose scoped/negative/
  high-critical sample facts, codebook coverage, selected/omitted action counts, the
  four-action maximum, and that priority is deterministic rather than a score;
- render every selected action in exact priority order without changing its approved ID,
  label, horizon, suggested role owners, action, trigger counts/shares, verification
  checklist, Evidence ID, title, or summary. The narrator may only add connective prose;
- state that role owners are suggestions, horizons are playbook targets, and a human must
  approve/adapt any action to operational, legal, policy, and business context before
  execution. The engine itself sends no message, changes no product, and opens no ticket;
- do not add an action, numeric target, named employee/vendor, causal claim, external fact,
  legal conclusion, guaranteed outcome, or advice derived only from the representative
  text. Do not prescribe a business claim that `biz-impact` left unverified;
- the deterministic Chinese/English stub renders the same approved plan, evidence,
  limitations, and shared-representative citation sequence in automated tests.

No-data rule: zero scoped articles returns `no_data` with retained zero facts and no
narrator operation. A non-empty scope with zero negative records remains `complete` and
renders a deterministic no-escalation finding plus routine-monitoring boundary without
evidence or narrator cost. Negative records always yield at least the deterministic
fallback action; one or more selected actions perform exactly one narrator operation.
Query, calculation/action-selection, evidence, or narration errors return `failed` with a
safe stage-specific message while later sections continue. No path creates a chart or
external side effect.
