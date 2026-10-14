{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH voyages AS (
    SELECT * FROM {{ ref('fact_vessel_voyage') }}
),

ports AS (
    SELECT * FROM {{ ref('dim_port') }}
),

port_events AS (
    SELECT
        p.port_id,
        DATE_TRUNC('day', v.start_ts)::DATE AS day,
        v.mmsi,
        v.track_id,
        'departure' AS event_type
    FROM voyages v
    INNER JOIN ports p
        ON v.start_latitude  BETWEEN p.bbox_min_lat AND p.bbox_max_lat
       AND v.start_longitude BETWEEN p.bbox_min_lon AND p.bbox_max_lon

    UNION ALL

    SELECT
        p.port_id,
        DATE_TRUNC('day', v.end_ts)::DATE AS day,
        v.mmsi,
        v.track_id,
        'arrival' AS event_type
    FROM voyages v
    INNER JOIN ports p
        ON v.end_latitude  BETWEEN p.bbox_min_lat AND p.bbox_max_lat
       AND v.end_longitude BETWEEN p.bbox_min_lon AND p.bbox_max_lon
),

aggregated AS (
    SELECT
        port_id,
        day,
        COUNT(*) FILTER (WHERE event_type = 'arrival')   AS arrivals,
        COUNT(*) FILTER (WHERE event_type = 'departure') AS departures,
        COUNT(DISTINCT mmsi)                              AS active_vessels,
        COUNT(DISTINCT track_id)                          AS total_tracks
    FROM port_events
    GROUP BY port_id, day
)

SELECT
    a.port_id,
    p.port_name,
    p.country_code,
    a.day,
    a.arrivals,
    a.departures,
    a.active_vessels,
    a.total_tracks,
    NOW() AS created_at
FROM aggregated a
INNER JOIN ports p USING (port_id)
