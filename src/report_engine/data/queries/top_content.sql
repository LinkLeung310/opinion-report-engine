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
        favorites,
        (likes + comments + shares + favorites)::BIGINT AS total_engagement
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
stats AS (
    SELECT
        COUNT(*)::INTEGER AS article_count,
        COUNT(*) FILTER (WHERE total_engagement > 0)::INTEGER
            AS positive_engagement_articles,
        COUNT(*) FILTER (
            WHERE sentiment = 'negative'
              AND (severity IN ('high', 'critical') OR negative_score >= 4)
        )::INTEGER AS high_risk_signal_articles,
        COALESCE(SUM(total_engagement), 0)::BIGINT AS total_engagement
    FROM scoped
),
engagement_ranked AS (
    SELECT
        external_id,
        ROW_NUMBER() OVER (
            ORDER BY total_engagement DESC, published_at DESC, external_id ASC
        )::INTEGER AS engagement_rank
    FROM scoped
    WHERE total_engagement > 0
),
risk_ranked AS (
    SELECT
        external_id,
        ROW_NUMBER() OVER (
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 4
                    WHEN 'high' THEN 3
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 1
                    ELSE 0
                END DESC,
                negative_score DESC NULLS LAST,
                total_engagement DESC,
                published_at DESC,
                external_id ASC
        )::INTEGER AS risk_rank
    FROM scoped
    WHERE sentiment = 'negative'
      AND (severity IN ('high', 'critical') OR negative_score >= 4)
),
selected_ids AS (
    SELECT external_id
    FROM engagement_ranked
    WHERE engagement_rank <= 3
    UNION
    SELECT external_id
    FROM risk_ranked
    WHERE risk_rank <= 3
),
selected AS (
    SELECT
        scoped.*,
        engagement_ranked.engagement_rank,
        risk_ranked.risk_rank,
        CASE
            WHEN engagement_ranked.engagement_rank <= 3
             AND risk_ranked.risk_rank <= 3 THEN 'dual_signal'
            WHEN engagement_ranked.engagement_rank <= 3 THEN 'engagement_only'
            ELSE 'risk_only'
        END AS category
    FROM selected_ids
    JOIN scoped USING (external_id)
    LEFT JOIN engagement_ranked USING (external_id)
    LEFT JOIN risk_ranked USING (external_id)
)
SELECT
    stats.article_count,
    stats.positive_engagement_articles,
    stats.high_risk_signal_articles,
    stats.total_engagement,
    selected.external_id,
    selected.title,
    selected.summary,
    selected.platform,
    selected.published_at,
    selected.sentiment,
    selected.severity,
    selected.negative_score,
    selected.likes,
    selected.comments,
    selected.shares,
    selected.favorites,
    selected.total_engagement AS record_total_engagement,
    selected.engagement_rank,
    selected.risk_rank,
    selected.category
FROM stats
LEFT JOIN selected ON TRUE
ORDER BY
    CASE selected.category
        WHEN 'dual_signal' THEN 1
        WHEN 'engagement_only' THEN 2
        WHEN 'risk_only' THEN 3
        ELSE 4
    END,
    selected.risk_rank NULLS LAST,
    selected.engagement_rank NULLS LAST,
    selected.external_id ASC;
