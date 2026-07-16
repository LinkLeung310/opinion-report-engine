WITH scoped AS (
    SELECT
        external_id,
        title,
        summary,
        platform,
        published_at,
        (published_at AT TIME ZONE %(timezone_name)s)::DATE AS published_day,
        sentiment,
        (likes + comments + shares + favorites)::BIGINT AS total_engagement,
        ('official-response' = ANY(tags)) AS response_tagged
    FROM articles
    WHERE %(topic_tag)s = ANY(tags)
      AND published_at >= %(from_inclusive)s
      AND published_at < %(to_exclusive)s
),
stats AS (
    SELECT
        COUNT(*)::INTEGER AS article_count,
        COUNT(*) FILTER (WHERE response_tagged)::INTEGER AS response_tagged_articles
    FROM scoped
),
daily AS (
    SELECT published_day, COUNT(*)::INTEGER AS article_count
    FROM scoped
    GROUP BY published_day
),
peak_day AS (
    SELECT published_day, article_count
    FROM daily
    ORDER BY article_count DESC, published_day ASC
    LIMIT 1
),
first_observed AS (
    SELECT *
    FROM scoped
    ORDER BY published_at ASC, external_id ASC
    LIMIT 1
),
tagged_response AS (
    SELECT *
    FROM scoped
    WHERE response_tagged
    ORDER BY published_at ASC, external_id ASC
    LIMIT 1
),
peak_day_representative AS (
    SELECT scoped.*
    FROM scoped
    CROSS JOIN peak_day
    WHERE scoped.published_day = peak_day.published_day
    ORDER BY total_engagement DESC, published_at ASC, external_id ASC
    LIMIT 1
),
last_observed AS (
    SELECT *
    FROM scoped
    ORDER BY published_at DESC, external_id ASC
    LIMIT 1
),
role_candidates AS (
    SELECT 1 AS role_priority, 'first_observed' AS role, first_observed.*
    FROM first_observed
    UNION ALL
    SELECT 2 AS role_priority, 'tagged_response' AS role, tagged_response.*
    FROM tagged_response
    UNION ALL
    SELECT
        3 AS role_priority,
        'peak_day_representative' AS role,
        peak_day_representative.*
    FROM peak_day_representative
    UNION ALL
    SELECT 4 AS role_priority, 'last_observed' AS role, last_observed.*
    FROM last_observed
)
SELECT
    role_candidates.role,
    role_candidates.external_id,
    role_candidates.title,
    role_candidates.summary,
    role_candidates.platform,
    role_candidates.published_at,
    role_candidates.published_day,
    role_candidates.sentiment,
    role_candidates.total_engagement,
    role_candidates.response_tagged,
    stats.article_count,
    peak_day.published_day AS peak_day,
    peak_day.article_count AS peak_articles,
    stats.response_tagged_articles
FROM role_candidates
CROSS JOIN stats
CROSS JOIN peak_day
ORDER BY role_candidates.role_priority;
