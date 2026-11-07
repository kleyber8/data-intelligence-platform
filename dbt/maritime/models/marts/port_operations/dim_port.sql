{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH raw_ports AS (
    SELECT * FROM {{ source('bronze', 'bronze_ports') }}
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
),

expanded AS (
    SELECT
        port_index AS port_id,
        port_name,
        country AS country_code,
        latitude,
        longitude,
        -- Bounding box de +/- 0.15 grados para geofencing
        latitude - 0.15 AS bbox_min_lat,
        longitude - 0.15 AS bbox_min_lon,
        latitude + 0.15 AS bbox_max_lat,
        longitude + 0.15 AS bbox_max_lon,
        NOW() AS created_at
    FROM raw_ports
)

SELECT * FROM expanded
