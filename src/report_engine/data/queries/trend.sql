WITH calendar AS (
    SELECT generate_series(
        CAST(%(from_date)s AS DATE),
        CAST(%(to_date)s AS DATE),
        INTERVAL '1 day'
    )::DATE AS article_day
),
scoped AS (
    SELECT
        (published_at AT TIME ZONE %(timezone_name)s)::DATE AS article_day,
        sentiment
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
daily AS (
    SELECT
        article_day,
        COUNT(*)::INTEGER AS article_count,
        (COUNT(*) FILTER (WHERE sentiment = 'positive'))::INTEGER
            AS positive_articles,
        (COUNT(*) FILTER (WHERE sentiment = 'neutral'))::INTEGER
            AS neutral_articles,
        (COUNT(*) FILTER (WHERE sentiment = 'negative'))::INTEGER
            AS negative_articles
    FROM scoped
    GROUP BY article_day
)
SELECT
    calendar.article_day,
    COALESCE(daily.article_count, 0)::INTEGER AS article_count,
    COALESCE(daily.positive_articles, 0)::INTEGER AS positive_articles,
    COALESCE(daily.neutral_articles, 0)::INTEGER AS neutral_articles,
    COALESCE(daily.negative_articles, 0)::INTEGER AS negative_articles
FROM calendar
LEFT JOIN daily USING (article_day)
ORDER BY calendar.article_day;
