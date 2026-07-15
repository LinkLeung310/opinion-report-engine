WITH scoped AS (
    SELECT
        published_at,
        sentiment,
        severity
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
totals AS (
    SELECT
        COUNT(*)::INTEGER AS article_count,
        (COUNT(*) FILTER (WHERE sentiment = 'negative'))::INTEGER
            AS negative_articles,
        (
            COUNT(*) FILTER (
                WHERE sentiment = 'negative'
                  AND severity IN ('high', 'critical')
            )
        )::INTEGER AS high_risk_negative_articles,
        (
            COUNT(*) FILTER (
                WHERE sentiment = 'negative'
                  AND severity = 'critical'
            )
        )::INTEGER AS critical_negative_articles
    FROM scoped
),
daily AS (
    SELECT
        (published_at AT TIME ZONE %(timezone_name)s)::DATE AS article_day,
        COUNT(*)::INTEGER AS article_count
    FROM scoped
    GROUP BY article_day
),
peak AS (
    SELECT
        article_day AS peak_day,
        article_count AS peak_article_count
    FROM daily
    ORDER BY article_count DESC, article_day ASC
    LIMIT 1
),
final_day AS (
    SELECT COALESCE(
        MAX(article_count) FILTER (WHERE article_day = %(to_date)s),
        0
    )::INTEGER AS final_day_article_count
    FROM daily
)
SELECT
    totals.*,
    peak.peak_day,
    COALESCE(peak.peak_article_count, 0)::INTEGER AS peak_article_count,
    final_day.final_day_article_count
FROM totals
CROSS JOIN final_day
LEFT JOIN peak ON TRUE;
