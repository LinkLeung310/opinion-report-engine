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
    favorites
FROM articles
WHERE %(topic_tag)s = ANY(tags)
  AND published_at >= %(from_inclusive)s
  AND published_at < %(to_exclusive)s
ORDER BY published_at ASC, external_id ASC;
