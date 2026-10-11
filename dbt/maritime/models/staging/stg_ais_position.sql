{{ config(
    materialized='view',
    tags=['staging', 'silver']
) }}

WITH source AS (
    SELECT *
    FROM {{ source('bronze', 'bronze_ais_position') }}
    WHERE quality_status = 'validated'
),

renamed AS (
    SELECT
        ingestion_row_id,
        ingestion_run_id,
        TRIM(mmsi)::VARCHAR(20)                                 AS mmsi,
        latitude::DOUBLE PRECISION                              AS latitude,
        longitude::DOUBLE PRECISION                             AS longitude,
        speed_over_ground::DOUBLE PRECISION                     AS speed_over_ground,
        course_over_ground::DOUBLE PRECISION                    AS course_over_ground,
        heading::INTEGER                                        AS heading,
        position_ts::TIMESTAMPTZ                                AS position_ts,
        COALESCE(vessel_name, 'UNKNOWN')::VARCHAR(255)          AS vessel_name,
        COALESCE(vessel_type, 'Unknown')::VARCHAR(100)          AS vessel_type,
        COALESCE(nav_status, 'Unknown')::VARCHAR(100)           AS nav_status,
        source_file,
        created_at
    FROM source
)

SELECT * FROM renamed
