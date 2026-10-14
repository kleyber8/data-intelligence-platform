{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH tracks AS (
    SELECT * FROM {{ ref('int_vessel_tracks') }}
),

first_position AS (
    SELECT DISTINCT ON (track_id)
        track_id,
        latitude    AS start_latitude,
        longitude   AS start_longitude,
        position_ts AS start_ts
    FROM tracks
    ORDER BY track_id, position_ts ASC
),

last_position AS (
    SELECT DISTINCT ON (track_id)
        track_id,
        latitude    AS end_latitude,
        longitude   AS end_longitude,
        position_ts AS end_ts
    FROM tracks
    ORDER BY track_id, position_ts DESC
),

aggregated AS (
    SELECT
        track_id,
        mmsi,
        MIN(vessel_name) AS vessel_name,
        MIN(vessel_type) AS vessel_type,
        MIN(position_ts) AS start_ts,
        MAX(position_ts) AS end_ts,
        EXTRACT(EPOCH FROM (MAX(position_ts) - MIN(position_ts)))::DOUBLE PRECISION AS duration_seconds,
        COALESCE(SUM(distance_km), 0)::DOUBLE PRECISION       AS total_distance_km,
        AVG(speed_over_ground)::DOUBLE PRECISION              AS avg_speed_knots,
        MAX(calculated_speed_knots)::DOUBLE PRECISION         AS max_speed_knots,
        COUNT(*)::INTEGER                                     AS num_positions
    FROM tracks
    GROUP BY track_id, mmsi
)

SELECT
    a.track_id,
    a.mmsi,
    a.vessel_name,
    a.vessel_type,
    a.start_ts,
    a.end_ts,
    a.duration_seconds,
    a.total_distance_km,
    a.avg_speed_knots,
    a.max_speed_knots,
    a.num_positions,
    f.start_latitude,
    f.start_longitude,
    l.end_latitude,
    l.end_longitude,
    NOW() AS created_at
FROM aggregated a
INNER JOIN first_position f USING (track_id)
INNER JOIN last_position  l USING (track_id)
