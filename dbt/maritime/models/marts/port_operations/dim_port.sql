{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH expanded AS (
    SELECT
        port_id,
        port_name,
        country_code,
        latitude,
        longitude,
        bbox_min_lat,
        bbox_min_lon,
        bbox_max_lat,
        bbox_max_lon,
        NOW() AS created_at
    FROM {{ ref('int_ports') }}
)

SELECT * FROM expanded
