WITH source_types(source_type, sort_order) AS (
    VALUES
        ('media'::TEXT, 1),
        ('social'::TEXT, 2)
),
scoped AS (
    SELECT
        source_type,
        platform,
        sentiment
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
aggregated AS (
    SELECT
        source_type,
        COUNT(*)::INTEGER AS article_count,
        COUNT(*) FILTER (WHERE sentiment = 'positive')::INTEGER AS positive_articles,
        COUNT(*) FILTER (WHERE sentiment = 'neutral')::INTEGER AS neutral_articles,
        COUNT(*) FILTER (WHERE sentiment = 'negative')::INTEGER AS negative_articles,
        COUNT(DISTINCT platform)::INTEGER AS platform_count
    FROM scoped
    GROUP BY source_type
),
totals AS (
    SELECT
        COUNT(*)::INTEGER AS total_article_count,
        COUNT(*) FILTER (WHERE sentiment = 'negative')::INTEGER
            AS total_negative_articles
    FROM scoped
)
SELECT
    source_types.source_type,
    COALESCE(aggregated.article_count, 0)::INTEGER AS article_count,
    COALESCE(aggregated.positive_articles, 0)::INTEGER AS positive_articles,
    COALESCE(aggregated.neutral_articles, 0)::INTEGER AS neutral_articles,
    COALESCE(aggregated.negative_articles, 0)::INTEGER AS negative_articles,
    COALESCE(aggregated.platform_count, 0)::INTEGER AS platform_count,
    totals.total_article_count,
    totals.total_negative_articles
FROM source_types
CROSS JOIN totals
LEFT JOIN aggregated USING (source_type)
ORDER BY source_types.sort_order;
