{{ config(
    post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_int_deltas_mmsi_ts ON {{ this }}(mmsi, position_ts)",
      "CREATE INDEX IF NOT EXISTS idx_int_deltas_row_id ON {{ this }}(ingestion_row_id)",
      "CREATE INDEX IF NOT EXISTS idx_int_deltas_speed ON {{ this }}(calculated_speed_knots) WHERE calculated_speed_knots > 60.0"
    ]
) }}

WITH with_lag AS (
    SELECT
        ingestion_row_id, ingestion_run_id, mmsi, latitude, longitude,
        speed_over_ground, course_over_ground, heading, position_ts,
        vessel_name, vessel_type, nav_status,
        LAG(latitude)    OVER w AS prev_latitude,
        LAG(longitude)   OVER w AS prev_longitude,
        LAG(position_ts) OVER w AS prev_position_ts,
        EXTRACT(EPOCH FROM (position_ts - LAG(position_ts) OVER w))::DOUBLE PRECISION AS time_delta_seconds
    FROM {{ ref('stg_ais_position') }}
    WINDOW w AS (PARTITION BY mmsi ORDER BY position_ts)
),
with_distance AS (
    SELECT
        *,
        CASE
            WHEN prev_position_ts IS NULL THEN NULL
            ELSE 6371.0 * 2 * ASIN(SQRT(
                POWER(SIN(RADIANS(latitude - prev_latitude) / 2), 2) +
                COS(RADIANS(prev_latitude)) * COS(RADIANS(latitude)) *
                POWER(SIN(RADIANS(longitude - prev_longitude) / 2), 2)
            ))
        END AS distance_km
    FROM with_lag
),
with_speed AS (
    SELECT
        *,
        CASE
            WHEN time_delta_seconds IS NOT NULL AND time_delta_seconds > 0
            THEN (distance_km / (time_delta_seconds / 3600.0)) / 1.852
            ELSE NULL
        END AS calculated_speed_knots
    FROM with_distance
)
SELECT
    ingestion_row_id, ingestion_run_id, mmsi, latitude, longitude,
    speed_over_ground, course_over_ground, heading, position_ts,
    vessel_name, vessel_type, nav_status,
    time_delta_seconds, distance_km, calculated_speed_knots,
    CASE
        WHEN calculated_speed_knots IS NULL THEN NULL
        ELSE ABS(calculated_speed_knots - speed_over_ground)
    END AS speed_delta_knots,
    CASE
        WHEN calculated_speed_knots IS NULL THEN FALSE
        WHEN ABS(calculated_speed_knots - speed_over_ground) > 5.0 THEN TRUE
        ELSE FALSE
    END AS is_speed_anomaly
FROM with_speed
