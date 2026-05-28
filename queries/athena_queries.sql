-- Athena: movie_trusted_db
-- Tables: movies, movie_genres, movie_reviews, people, exchange, tv_shows
-- Run one question block at a time (one SELECT per execution).

-- Question 1: genres with highest revenue
SELECT
    g.genre,
    COUNT(DISTINCT g.tmdb_id)              AS movie_count,
    ROUND(AVG(m.revenue_usd), 2)           AS avg_revenue_usd,
    ROUND(SUM(m.revenue_usd), 2)           AS total_revenue_usd,
    ROUND(AVG(m.revenue_cop), 2)           AS avg_revenue_cop,
    ROUND(SUM(m.revenue_cop), 2)           AS total_revenue_cop
FROM movie_genres g
JOIN movies m ON g.tmdb_id = m.tmdb_id
WHERE m.revenue_usd IS NOT NULL
  AND m.revenue_cop IS NOT NULL
GROUP BY g.genre
ORDER BY total_revenue_usd DESC
LIMIT 20;


-- Question 2: actors in profitable movies
WITH profitable AS (
    SELECT tmdb_id, profit_usd, cast_ids
    FROM movies
    WHERE profit_usd IS NOT NULL
      AND profit_usd > 0
),
cast_expanded AS (
    SELECT
        r.tmdb_id,
        r.profit_usd,
        TRIM(actor_id_raw) AS actor_id_str
    FROM profitable r
    CROSS JOIN UNNEST(SPLIT(r.cast_ids, ',')) AS t(actor_id_raw)
    WHERE r.cast_ids IS NOT NULL
      AND TRIM(actor_id_raw) <> ''
)
SELECT
    p.tmdb_id,
    p.name                                 AS actor,
    COUNT(DISTINCT c.tmdb_id)              AS profitable_movie_count,
    ROUND(AVG(c.profit_usd), 2)            AS avg_profit_usd
FROM cast_expanded c
JOIN people p
  ON CAST(c.actor_id_str AS INTEGER) = p.tmdb_id
GROUP BY p.tmdb_id, p.name
ORDER BY profitable_movie_count DESC, avg_profit_usd DESC
LIMIT 25;


-- Question 3: COP-adjusted revenue by release year
SELECT
    release_year,
    COUNT(*)                               AS movie_count,
    ROUND(SUM(revenue_usd), 2)             AS total_revenue_usd,
    ROUND(SUM(revenue_cop), 2)             AS total_revenue_cop,
    ROUND(AVG(revenue_cop / NULLIF(revenue_usd, 0)), 4) AS cop_rate_applied
FROM movies
WHERE release_year IS NOT NULL
  AND revenue_usd IS NOT NULL
  AND revenue_cop IS NOT NULL
GROUP BY release_year
HAVING COUNT(*) >= 5
ORDER BY release_year;


-- Question 4: directors with best ROI
WITH fx AS (
    SELECT rate AS cop_rate
    FROM exchange
    WHERE currency = 'COP'
    LIMIT 1
),
by_director AS (
    SELECT
        TRIM(director_name)                AS director,
        m.tmdb_id,
        m.roi_pct,
        m.profit_usd,
        m.revenue_usd,
        m.budget_usd,
        m.revenue_usd * fx.cop_rate        AS revenue_cop_calc,
        m.budget_usd * fx.cop_rate         AS budget_cop,
        CASE
            WHEN m.budget_usd IS NOT NULL AND m.budget_usd > 0
            THEN (
                (m.revenue_usd * fx.cop_rate) - (m.budget_usd * fx.cop_rate)
            ) / (m.budget_usd * fx.cop_rate) * 100
        END                                AS roi_adjusted
    FROM movies m
    CROSS JOIN fx
    CROSS JOIN UNNEST(SPLIT(m.directors, ',')) AS t(director_name)
    WHERE m.directors IS NOT NULL
      AND TRIM(director_name) <> ''
)
SELECT
    director,
    COUNT(DISTINCT tmdb_id)                AS movie_count,
    ROUND(AVG(roi_pct), 2)                 AS avg_roi_pct,
    ROUND(AVG(roi_adjusted), 2)            AS avg_roi_adjusted_cop,
    ROUND(AVG(profit_usd), 2)              AS avg_profit_usd,
    ROUND(SUM(revenue_usd), 2)             AS total_revenue_usd
FROM by_director
WHERE roi_pct IS NOT NULL
GROUP BY director
HAVING COUNT(DISTINCT tmdb_id) >= 3
ORDER BY avg_roi_pct DESC
LIMIT 20;


-- Question 5: correlation between ratings and financial metrics
WITH review_agg AS (
    SELECT
        tmdb_id,
        AVG(rating)                          AS avg_review_rating
    FROM movie_reviews
    WHERE rating IS NOT NULL
    GROUP BY tmdb_id
    HAVING COUNT(*) >= 3
)
SELECT
    CORR(m.vote_average, m.revenue_usd)      AS corr_tmdb_rating_vs_revenue,
    CORR(m.vote_average, m.profit_usd)       AS corr_tmdb_rating_vs_profit,
    CORR(m.vote_average, m.roi_pct)          AS corr_tmdb_rating_vs_roi,
    CORR(r.avg_review_rating, m.revenue_usd) AS corr_review_rating_vs_revenue,
    CORR(r.avg_review_rating, m.profit_usd)  AS corr_review_rating_vs_profit,
    CORR(r.avg_review_rating, m.roi_pct)     AS corr_review_rating_vs_roi
FROM movies m
JOIN review_agg r ON m.tmdb_id = r.tmdb_id
WHERE m.vote_average IS NOT NULL
  AND m.revenue_usd IS NOT NULL;
