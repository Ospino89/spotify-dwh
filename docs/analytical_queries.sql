-- =============================================================================
-- MI SPOTIFY WRAPPED — 5 consultas analíticas (DWH)
-- Ejecutar en Neon SQL Editor o psql conectado a tu base de datos.
-- Requisito: haber corrido el ETL varias veces para tener filas en fact_*.
-- =============================================================================

-- Opcional: filtrar por un solo usuario (descomenta y cambia el spotify_id)
-- AND u.spotify_id = 'TU_SPOTIFY_ID_AQUI'


-- -----------------------------------------------------------------------------
-- PREGUNTA 1: ¿A qué hora del día escuchas más música?
-- -----------------------------------------------------------------------------
SELECT
    f.hour_of_day,
    LPAD(f.hour_of_day::text, 2, '0') || ':00' AS hora_label,
    COUNT(*) AS total_reproducciones
FROM dwh.fact_listening_history f
-- JOIN dwh.dim_users u ON u.user_id = f.user_id  -- descomenta para filtrar por usuario
GROUP BY f.hour_of_day
ORDER BY total_reproducciones DESC;


-- -----------------------------------------------------------------------------
-- PREGUNTA 2: ¿Cuáles son tus 5 artistas más escuchados?
-- -----------------------------------------------------------------------------
SELECT
    a.name AS artista,
    a.spotify_id,
    COUNT(*) AS total_reproducciones
FROM dwh.fact_listening_history f
JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
-- JOIN dwh.dim_users u ON u.user_id = f.user_id
GROUP BY a.artist_id, a.name, a.spotify_id
ORDER BY total_reproducciones DESC
LIMIT 5;


-- -----------------------------------------------------------------------------
-- PREGUNTA 3: Popularidad promedio (y min/max) de tus top tracks en dim_tracks
-- -----------------------------------------------------------------------------
SELECT
    ROUND(AVG(popularity)::numeric, 2) AS popularidad_promedio,
    MIN(popularity) AS popularidad_minima,
    MAX(popularity) AS popularidad_maxima,
    COUNT(*) AS total_tracks
FROM dwh.dim_tracks
WHERE popularity IS NOT NULL;


-- -----------------------------------------------------------------------------
-- PREGUNTA 4: ¿Qué géneros dominan tu historial de escucha?
-- -----------------------------------------------------------------------------
SELECT
    g.genre AS genero,
    COUNT(*) AS total_reproducciones
FROM dwh.fact_listening_history f
JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
CROSS JOIN LATERAL UNNEST(COALESCE(a.genres, ARRAY[]::text[])) AS g(genre)
-- JOIN dwh.dim_users u ON u.user_id = f.user_id
GROUP BY g.genre
ORDER BY total_reproducciones DESC;


-- -----------------------------------------------------------------------------
-- PREGUNTA 5: Ranking de artistas por día de la semana.
-- -----------------------------------------------------------------------------
WITH reproducciones_por_dia AS (
    SELECT
        f.day_of_week,
        a.name AS artista,
        COUNT(*) AS total_reproducciones
    FROM dwh.fact_listening_history f
    JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
    -- JOIN dwh.dim_users u ON u.user_id = f.user_id
    WHERE f.day_of_week IS NOT NULL
    GROUP BY f.day_of_week, a.artist_id, a.name
)
SELECT
    day_of_week AS dia_semana,
    artista,
    total_reproducciones,
    RANK() OVER (
        PARTITION BY day_of_week
        ORDER BY total_reproducciones DESC
    ) AS ranking_en_el_dia
FROM reproducciones_por_dia
ORDER BY
    CASE day_of_week
        WHEN 'Monday'    THEN 1
        WHEN 'Tuesday'   THEN 2
        WHEN 'Wednesday' THEN 3
        WHEN 'Thursday'  THEN 4
        WHEN 'Friday'     THEN 5
        WHEN 'Saturday'  THEN 6
        WHEN 'Sunday'    THEN 7
        ELSE 8
    END,
    ranking_en_el_dia;


