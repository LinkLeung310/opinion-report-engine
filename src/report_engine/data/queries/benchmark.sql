WITH comparison_candidates AS (
    SELECT
        (published_at AT TIME ZONE %(timezone_name)s)::date AS published_day,
        sentiment,
        severity,
        platform,
        likes + comments + shares + favorites AS engagement
    FROM articles
    WHERE tags @> ARRAY[%(comparison_tag)s]::text[]
      AND NOT tags @> ARRAY[%(topic_tag)s]::text[]
),
comparison_anchor AS (
    SELECT MIN(published_day) AS start_day
    FROM comparison_candidates
),
current_records AS (
    SELECT sentiment, severity, platform,
           likes + comments + shares + favorites AS engagement
    FROM articles
    WHERE tags @> ARRAY[%(topic_tag)s]::text[]
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
comparison_records AS (
    SELECT candidate.*
    FROM comparison_candidates AS candidate
    CROSS JOIN comparison_anchor AS anchor
    WHERE candidate.published_day >= anchor.start_day
      AND candidate.published_day < anchor.start_day + %(calendar_days)s
),
cohorts AS (
    SELECT
        1 AS cohort_order,
        'current'::text AS cohort,
        %(topic_tag)s::text AS tag,
        (%(from_inclusive)s AT TIME ZONE %(timezone_name)s)::date AS start_day,
        ((%(to_exclusive)s AT TIME ZONE %(timezone_name)s)::date - 1) AS end_day,
        COUNT(*)::integer AS article_count,
        COUNT(*) FILTER (WHERE sentiment = 'positive')::integer AS positive_articles,
        COUNT(*) FILTER (WHERE sentiment = 'neutral')::integer AS neutral_articles,
        COUNT(*) FILTER (WHERE sentiment = 'negative')::integer AS negative_articles,
        COUNT(DISTINCT platform)::integer AS platform_count,
        COUNT(*) FILTER (WHERE sentiment = 'negative' AND severity IN ('high', 'critical'))::integer AS high_critical_articles,
        COALESCE(SUM(engagement), 0)::bigint AS total_engagement,
        0::integer AS excluded_later_articles
    FROM current_records
    UNION ALL
    SELECT
        2,
        'comparison',
        %(comparison_tag)s::text,
        anchor.start_day,
        anchor.start_day + %(calendar_days)s - 1,
        COUNT(records.*)::integer,
        COUNT(records.*) FILTER (WHERE records.sentiment = 'positive')::integer,
        COUNT(records.*) FILTER (WHERE records.sentiment = 'neutral')::integer,
        COUNT(records.*) FILTER (WHERE records.sentiment = 'negative')::integer,
        COUNT(DISTINCT records.platform)::integer,
        COUNT(records.*) FILTER (WHERE records.sentiment = 'negative' AND records.severity IN ('high', 'critical'))::integer,
        COALESCE(SUM(records.engagement), 0)::bigint,
        (SELECT COUNT(*) FROM comparison_candidates AS later
         WHERE later.published_day >= anchor.start_day + %(calendar_days)s)::integer
    FROM comparison_anchor AS anchor
    LEFT JOIN comparison_records AS records ON TRUE
    GROUP BY anchor.start_day
)
SELECT * FROM cohorts ORDER BY cohort_order;
