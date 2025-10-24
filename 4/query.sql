WITH hourly_views AS
(SELECT campaign_id,
        phrase,
        toHour (dt) AS hour,
        max(views) - min(views) AS views_delta
FROM phrases_views
GROUP BY campaign_id,
            phrase,
            toHour (dt)
ORDER BY hour DESC)
SELECT phrase,
    groupArray ((hour, views_delta)) AS views_by_hour
FROM hourly_views
WHERE views_delta > 0
GROUP BY campaign_id,
        phrase;