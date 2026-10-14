{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH tracks AS (
    SELECT * FROM {{ ref('int_vessel_tracks') }}
)

SELECT
    ingestion_row_id  AS anomaly_id,
    mmsi              AS vessel_id,
    position_ts       AS timestamp,
    track_id,
    CASE
        WHEN is_speed_anomaly THEN 'speed_anomaly'
        ELSE 'none'
    END AS anomaly_type,
    CASE
        WHEN ABS(speed_delta_knots) >= 10 THEN 'high'
        WHEN ABS(speed_delta_knots) >= 5  THEN 'medium'
        ELSE 'low'
    END AS severity,
    ABS(speed_delta_knots)::DOUBLE PRECISION AS score,
    speed_over_ground::DOUBLE PRECISION      AS baseline,
    calculated_speed_knots::DOUBLE PRECISION AS observed_value,
    distance_km,
    time_delta_seconds,
    NOW() AS created_at
FROM tracks
WHERE is_speed_anomaly = TRUE
