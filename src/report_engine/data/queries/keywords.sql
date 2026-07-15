SELECT
    external_id,
    title,
    summary,
    published_at,
    (published_at AT TIME ZONE %(timezone_name)s)::date AS published_day,
    sentiment
FROM articles
WHERE %(topic_tag)s = ANY(tags)
  AND published_at >= %(from_inclusive)s
  AND published_at < %(to_exclusive)s
ORDER BY published_at ASC, external_id ASC;
