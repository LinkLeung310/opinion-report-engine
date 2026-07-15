SELECT
    platform,
    COUNT(*)::INTEGER AS article_count,
    COUNT(*) FILTER (WHERE sentiment = 'positive')::INTEGER AS positive_articles,
    COUNT(*) FILTER (WHERE sentiment = 'neutral')::INTEGER AS neutral_articles,
    COUNT(*) FILTER (WHERE sentiment = 'negative')::INTEGER AS negative_articles,
    COALESCE(SUM(likes), 0)::BIGINT AS likes,
    COALESCE(SUM(comments), 0)::BIGINT AS comments,
    COALESCE(SUM(shares), 0)::BIGINT AS shares,
    COALESCE(SUM(favorites), 0)::BIGINT AS favorites,
    COALESCE(SUM(likes + comments + shares + favorites), 0)::BIGINT AS total_engagement
FROM articles
WHERE %(topic_tag)s = ANY(tags)
  AND published_at >= %(from_inclusive)s
  AND published_at < %(to_exclusive)s
GROUP BY platform
ORDER BY article_count DESC, total_engagement DESC, platform ASC;
