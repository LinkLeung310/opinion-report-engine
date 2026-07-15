WITH scoped AS (
    SELECT
        published_at,
        sentiment,
        platform,
        likes,
        comments,
        shares,
        favorites
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
totals AS (
    SELECT
        COUNT(*)::INTEGER AS article_count,
        COUNT(*) FILTER (WHERE sentiment = 'positive')::INTEGER AS positive_articles,
        COUNT(*) FILTER (WHERE sentiment = 'neutral')::INTEGER AS neutral_articles,
        COUNT(*) FILTER (WHERE sentiment = 'negative')::INTEGER AS negative_articles,
        COUNT(DISTINCT platform)::INTEGER AS platform_count,
        COALESCE(SUM(likes), 0)::BIGINT AS likes,
        COALESCE(SUM(comments), 0)::BIGINT AS comments,
        COALESCE(SUM(shares), 0)::BIGINT AS shares,
        COALESCE(SUM(favorites), 0)::BIGINT AS favorites
    FROM scoped
),
peak AS (
    SELECT
        (published_at AT TIME ZONE %(timezone_name)s)::DATE AS peak_day,
        COUNT(*)::INTEGER AS peak_article_count
    FROM scoped
    GROUP BY peak_day
    ORDER BY peak_article_count DESC, peak_day ASC
    LIMIT 1
)
SELECT
    totals.*,
    peak.peak_day,
    COALESCE(peak.peak_article_count, 0)::INTEGER AS peak_article_count
FROM totals
LEFT JOIN peak ON TRUE;
