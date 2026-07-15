WITH scoped AS (
    SELECT
        external_id,
        title,
        summary,
        platform,
        published_at,
        sentiment,
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
            AS positive_total_engagement_articles,
        COUNT(*) FILTER (WHERE total_engagement = 0)::INTEGER
            AS zero_engagement_articles,
        COALESCE(SUM(likes), 0)::BIGINT AS likes,
        COALESCE(SUM(comments), 0)::BIGINT AS comments,
        COALESCE(SUM(shares), 0)::BIGINT AS shares,
        COALESCE(SUM(favorites), 0)::BIGINT AS favorites,
        COALESCE(SUM(total_engagement), 0)::BIGINT AS total_engagement,
        COALESCE(MAX(total_engagement), 0)::BIGINT AS leading_engagement
    FROM scoped
),
ranked AS (
    SELECT
        scoped.*,
        ROW_NUMBER() OVER (
            ORDER BY total_engagement DESC, published_at DESC, external_id ASC
        )::INTEGER AS engagement_rank
    FROM scoped
    WHERE total_engagement > 0
),
leaders AS (
    SELECT COUNT(*)::INTEGER AS leading_record_count
    FROM scoped
    CROSS JOIN stats
    WHERE stats.leading_engagement > 0
      AND scoped.total_engagement = stats.leading_engagement
)
SELECT
    stats.article_count,
    stats.positive_total_engagement_articles,
    stats.zero_engagement_articles,
    stats.likes,
    stats.comments,
    stats.shares,
    stats.favorites,
    stats.total_engagement,
    stats.leading_engagement,
    leaders.leading_record_count,
    ranked.external_id,
    ranked.title,
    ranked.summary,
    ranked.platform,
    ranked.published_at,
    ranked.sentiment,
    ranked.likes AS record_likes,
    ranked.comments AS record_comments,
    ranked.shares AS record_shares,
    ranked.favorites AS record_favorites,
    ranked.total_engagement AS record_total_engagement,
    ranked.engagement_rank
FROM stats
CROSS JOIN leaders
LEFT JOIN ranked ON ranked.engagement_rank <= 5
ORDER BY ranked.engagement_rank NULLS LAST;
