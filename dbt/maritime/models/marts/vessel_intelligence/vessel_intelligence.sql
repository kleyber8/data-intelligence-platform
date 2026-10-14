{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH voyages AS (
    SELECT * FROM {{ ref('fact_vessel_voyage') }}
),

anomaly_stats AS (
    SELECT
        mmsi,
        COUNT(*) FILTER (WHERE is_speed_anomaly = TRUE) AS total_speed_anomalies
    FROM {{ ref('int_vessel_tracks') }}
    GROUP BY mmsi
),

vessel_stats AS (
    SELECT
        mmsi,
        MAX(vessel_name)                            AS vessel_name,
        MAX(vessel_type)                            AS vessel_type,
        COUNT(DISTINCT track_id)::INTEGER           AS total_voyages,
        COALESCE(SUM(total_distance_km), 0)::DOUBLE PRECISION AS total_distance_km,
        COALESCE(SUM(duration_seconds) / 3600.0, 0)::DOUBLE PRECISION AS total_hours,
        AVG(avg_speed_knots)::DOUBLE PRECISION      AS avg_speed_knots,
        MIN(start_ts)                               AS first_seen,
        MAX(end_ts)                                 AS last_seen
    FROM voyages
    GROUP BY mmsi
)

SELECT
    v.mmsi,
    v.vessel_name,
    v.vessel_type,
    v.total_voyages,
    v.total_distance_km,
    v.total_hours,
    v.avg_speed_knots,
    v.first_seen,
    v.last_seen,
    COALESCE(a.total_speed_anomalies, 0) AS total_speed_anomalies,
    EXTRACT(EPOCH FROM (v.last_seen - v.first_seen)) / 86400.0 AS operating_days,
    NOW() AS created_at
FROM vessel_stats v
LEFT JOIN anomaly_stats a USING (mmsi)
