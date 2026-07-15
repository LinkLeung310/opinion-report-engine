WITH scoped AS (
    SELECT
        external_id,
        title,
        summary,
        platform,
        published_at,
        sentiment,
        (likes + comments + shares + favorites)::BIGINT AS total_engagement,
        COUNT(*) OVER ()::INTEGER AS article_count,
        COUNT(*) FILTER (WHERE sentiment = 'positive') OVER ()::INTEGER AS positive_articles,
        COUNT(*) FILTER (WHERE sentiment = 'neutral') OVER ()::INTEGER AS neutral_articles,
        COUNT(*) FILTER (WHERE sentiment = 'negative') OVER ()::INTEGER AS negative_articles
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY sentiment
            ORDER BY total_engagement DESC, published_at DESC, external_id ASC
        ) AS popularity_rank,
        FIRST_VALUE(platform) OVER (
            PARTITION BY sentiment
            ORDER BY total_engagement DESC, published_at DESC, external_id ASC
        ) AS leading_platform
    FROM scoped
),
selected AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY sentiment
            ORDER BY
                CASE
                    WHEN popularity_rank = 1 THEN 0
                    WHEN platform <> leading_platform THEN 1
                    ELSE 2
                END,
                total_engagement DESC,
                published_at DESC,
                external_id ASC
        ) AS evidence_rank
    FROM ranked
)
SELECT
    external_id,
    title,
    summary,
    platform,
    published_at,
    sentiment,
    total_engagement,
    article_count,
    positive_articles,
    neutral_articles,
    negative_articles,
    evidence_rank
FROM selected
WHERE evidence_rank <= 2
ORDER BY
    CASE sentiment
        WHEN 'negative' THEN 1
        WHEN 'neutral' THEN 2
        WHEN 'positive' THEN 3
    END,
    evidence_rank;
