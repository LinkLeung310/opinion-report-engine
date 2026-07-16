WITH scoped AS (
    SELECT
        external_id,
        title,
        summary,
        platform,
        published_at,
        sentiment,
        severity,
        negative_score,
        likes,
        comments,
        shares,
        favorites
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
stats AS (
    SELECT
        COUNT(*)::INTEGER AS article_count,
        COUNT(*) FILTER (WHERE sentiment = 'negative')::INTEGER
            AS negative_article_count
    FROM scoped
),
negative_records AS (
    SELECT *
    FROM scoped
    WHERE sentiment = 'negative'
)
SELECT
    stats.article_count,
    stats.negative_article_count,
    negative_records.external_id,
    negative_records.title,
    negative_records.summary,
    negative_records.platform,
    negative_records.published_at,
    negative_records.sentiment,
    negative_records.severity,
    negative_records.negative_score,
    negative_records.likes,
    negative_records.comments,
    negative_records.shares,
    negative_records.favorites
FROM stats
LEFT JOIN negative_records ON TRUE
ORDER BY negative_records.published_at ASC, negative_records.external_id ASC;
