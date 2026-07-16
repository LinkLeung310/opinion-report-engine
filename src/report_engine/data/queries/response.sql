SELECT
    (published_at AT TIME ZONE %(timezone_name)s)::DATE AS published_day,
    sentiment,
    ('official-response' = ANY(tags)) AS response_tagged
FROM articles
WHERE %(topic_tag)s = ANY(tags)
  AND published_at >= %(from_inclusive)s
  AND published_at < %(to_exclusive)s
ORDER BY published_day ASC, sentiment ASC, external_id ASC;
