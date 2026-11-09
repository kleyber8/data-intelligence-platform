{{ config(
    tags=['intermediate', 'silver']
) }}

SELECT
    port_id,
    port_name,
    country_code,
    region_name,
    latitude,
    longitude,
    latitude - 0.15 AS bbox_min_lat,
    longitude - 0.15 AS bbox_min_lon,
    latitude + 0.15 AS bbox_max_lat,
    longitude + 0.15 AS bbox_max_lon
FROM {{ ref('stg_ports') }}
