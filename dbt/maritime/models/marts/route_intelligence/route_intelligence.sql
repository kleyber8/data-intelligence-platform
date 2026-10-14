{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH voyages AS (
    SELECT * FROM {{ ref('fact_vessel_voyage') }}
),

ports AS (
    SELECT * FROM {{ ref('dim_port') }}
),

voyage_with_ports AS (
    SELECT
        v.track_id,
        v.mmsi,
        v.total_distance_km,
        v.duration_seconds,
        origin.port_id AS origin_port_id,
        dest.port_id   AS destination_port_id
    FROM voyages v
    LEFT JOIN ports origin
        ON v.start_latitude  BETWEEN origin.bbox_min_lat AND origin.bbox_max_lat
       AND v.start_longitude BETWEEN origin.bbox_min_lon AND origin.bbox_max_lon
    LEFT JOIN ports dest
        ON v.end_latitude  BETWEEN dest.bbox_min_lat AND dest.bbox_max_lat
       AND v.end_longitude BETWEEN dest.bbox_min_lon AND dest.bbox_max_lon
)

SELECT
    COALESCE(origin_port_id, 'UNKNOWN')      AS origin_port_id,
    COALESCE(destination_port_id, 'UNKNOWN') AS destination_port_id,
    COUNT(*)::INTEGER                        AS frequency,
    ROUND(AVG(total_distance_km)::numeric, 2)::DOUBLE PRECISION AS avg_distance_km,
    ROUND(AVG(duration_seconds / 3600.0)::numeric, 2)::DOUBLE PRECISION AS avg_duration_hours,
    COUNT(DISTINCT mmsi)::INTEGER            AS unique_vessels,
    NOW() AS created_at
FROM voyage_with_ports
GROUP BY origin_port_id, destination_port_id
