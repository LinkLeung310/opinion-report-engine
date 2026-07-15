WITH scoped AS (
    SELECT
        external_id,
        title,
        summary,
        platform,
        published_at,
        sentiment,
        negative_score,
        severity,
        (likes + comments + shares + favorites)::BIGINT AS total_engagement
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
      AND sentiment = 'negative'
),
ranked AS (
    SELECT
        external_id,
        title,
        summary,
        platform,
        published_at,
        sentiment,
        negative_score,
        severity,
        total_engagement,
        COUNT(*) OVER ()::INTEGER AS negative_articles,
        COUNT(*) FILTER (WHERE severity = 'low') OVER ()::INTEGER AS low_articles,
        COUNT(*) FILTER (WHERE severity = 'medium') OVER ()::INTEGER AS medium_articles,
        COUNT(*) FILTER (WHERE severity = 'high') OVER ()::INTEGER AS high_articles,
        COUNT(*) FILTER (WHERE severity = 'critical') OVER ()::INTEGER AS critical_articles,
        COUNT(*) FILTER (WHERE severity IS NULL) OVER ()::INTEGER AS missing_severity_articles,
        COUNT(*) FILTER (WHERE negative_score = 1) OVER ()::INTEGER AS score_1_articles,
        COUNT(*) FILTER (WHERE negative_score = 2) OVER ()::INTEGER AS score_2_articles,
        COUNT(*) FILTER (WHERE negative_score = 3) OVER ()::INTEGER AS score_3_articles,
        COUNT(*) FILTER (WHERE negative_score = 4) OVER ()::INTEGER AS score_4_articles,
        COUNT(*) FILTER (WHERE negative_score = 5) OVER ()::INTEGER AS score_5_articles,
        COUNT(negative_score) OVER ()::INTEGER AS scored_negative_articles,
        COUNT(*) FILTER (WHERE negative_score IS NULL) OVER ()::INTEGER AS missing_score_articles,
        AVG(negative_score) OVER () AS average_negative_score,
        COALESCE(SUM(total_engagement) OVER (), 0)::BIGINT AS negative_engagement,
        COALESCE(
            SUM(total_engagement) FILTER (
                WHERE severity IN ('high', 'critical')
            ) OVER (),
            0
        )::BIGINT AS high_critical_engagement,
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
        ) AS evidence_rank
    FROM scoped
)
SELECT
    external_id,
    title,
    summary,
    platform,
    published_at,
    sentiment,
    negative_score,
    severity,
    total_engagement,
    negative_articles,
    low_articles,
    medium_articles,
    high_articles,
    critical_articles,
    missing_severity_articles,
    score_1_articles,
    score_2_articles,
    score_3_articles,
    score_4_articles,
    score_5_articles,
    scored_negative_articles,
    missing_score_articles,
    average_negative_score,
    negative_engagement,
    high_critical_engagement,
    evidence_rank
FROM ranked
WHERE evidence_rank <= 3
ORDER BY evidence_rank;
