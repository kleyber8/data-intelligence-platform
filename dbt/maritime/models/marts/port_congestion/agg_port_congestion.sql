{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH vessel_positions AS (
    SELECT
        s.mmsi,
        s.latitude,
        s.longitude,
        s.speed_over_ground,
        s.position_ts,
        p.port_id,
        p.port_name
    FROM {{ ref('stg_ais_position') }} s
    INNER JOIN {{ ref('dim_port') }} p
        ON s.latitude  BETWEEN p.bbox_min_lat AND p.bbox_max_lat
       AND s.longitude BETWEEN p.bbox_min_lon AND p.bbox_max_lon
),

hourly_metrics AS (
    SELECT
        port_id,
        port_name,
        DATE_TRUNC('hour', position_ts) AS hour,
        COUNT(DISTINCT mmsi)                    AS unique_vessels,
        COUNT(*)                                AS num_positions,
        AVG(speed_over_ground)::DOUBLE PRECISION AS avg_speed_knots
    FROM vessel_positions
    GROUP BY port_id, port_name, DATE_TRUNC('hour', position_ts)
),

scored AS (
    SELECT
        port_id,
        port_name,
        hour,
        unique_vessels,
        num_positions,
        avg_speed_knots,
        LEAST(unique_vessels::DOUBLE PRECISION / 10.0, 1.0) AS density_score,
        LEAST(GREATEST((20.0 - avg_speed_knots) / 20.0, 0.0), 1.0) AS speed_score
    FROM hourly_metrics
)

SELECT
    port_id,
    port_name,
    hour,
    unique_vessels,
    num_positions,
    avg_speed_knots,
    ROUND(((density_score * 0.6 + speed_score * 0.4) * 100)::numeric, 2)::DOUBLE PRECISION AS congestion_score,
    CASE
        WHEN (density_score * 0.6 + speed_score * 0.4) >= 0.75 THEN 'critical'
        WHEN (density_score * 0.6 + speed_score * 0.4) >= 0.50 THEN 'high'
        WHEN (density_score * 0.6 + speed_score * 0.4) >= 0.25 THEN 'moderate'
        ELSE 'low'
    END AS congestion_level,
    NOW() AS created_at
FROM scored
