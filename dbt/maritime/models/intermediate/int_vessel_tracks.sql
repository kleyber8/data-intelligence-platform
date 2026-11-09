{{ config(
    post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_tracks_track_id_ts ON {{ this }}(track_id, position_ts)",
      "CREATE INDEX IF NOT EXISTS idx_tracks_anomaly ON {{ this }}(ingestion_row_id) WHERE is_speed_anomaly = TRUE",
      "CREATE INDEX IF NOT EXISTS idx_tracks_distance ON {{ this }}(distance_km) WHERE distance_km IS NOT NULL"
    ]
) }}

WITH with_breaks AS (
    SELECT
        *,
        CASE
            WHEN time_delta_seconds IS NULL OR time_delta_seconds > 7200
            THEN 1
            ELSE 0
        END AS new_track_flag
    FROM {{ ref('int_vessel_position_deltas') }}
),
with_track_id AS (
    SELECT
        *,
        mmsi || '-' || CAST(
            SUM(new_track_flag) OVER (
                PARTITION BY mmsi
                ORDER BY position_ts
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS VARCHAR
        ) AS track_id
    FROM with_breaks
)
SELECT
    track_id, mmsi, ingestion_row_id, ingestion_run_id, latitude, longitude,
    speed_over_ground, course_over_ground, heading, position_ts,
    vessel_name, vessel_type, nav_status, time_delta_seconds, distance_km,
    calculated_speed_knots, speed_delta_knots, is_speed_anomaly
FROM with_track_id
