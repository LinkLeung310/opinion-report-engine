WITH scoped AS (
    SELECT
        platform,
        published_at,
        sentiment,
        severity,
        (likes + comments + shares + favorites)::BIGINT AS total_engagement
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
)
SELECT
    COUNT(*)::INTEGER AS article_count,
    COUNT(*) FILTER (WHERE sentiment = 'negative')::INTEGER AS negative_articles,
    COUNT(*) FILTER (
        WHERE sentiment = 'negative'
          AND severity IN ('high', 'critical')
    )::INTEGER AS high_critical_negative_articles,
    COUNT(DISTINCT platform)::INTEGER AS platform_count,
    COUNT(DISTINCT platform) FILTER (
        WHERE sentiment = 'negative'
    )::INTEGER AS negative_platform_count,
    COUNT(DISTINCT (published_at AT TIME ZONE %(timezone_name)s)::DATE) FILTER (
        WHERE sentiment = 'negative'
    )::INTEGER AS negative_active_days,
    COALESCE(SUM(total_engagement), 0)::BIGINT AS total_engagement,
    COALESCE(
        SUM(total_engagement) FILTER (WHERE sentiment = 'negative'),
        0
    )::BIGINT AS negative_engagement
FROM scoped;
