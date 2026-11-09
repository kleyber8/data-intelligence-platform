{{ config(
    post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_ais_mmsi_ts ON {{ this }}(mmsi, position_ts)",
      "CREATE INDEX IF NOT EXISTS idx_stg_ais_row_id ON {{ this }}(ingestion_row_id)"
    ]
) }}

WITH source AS (
    SELECT * FROM {{ source('bronze', 'bronze_ais_position') }}
    WHERE quality_status = 'validated'
),
renamed AS (
    SELECT
        ingestion_row_id, ingestion_run_id, mmsi, latitude, longitude,
        speed_over_ground, course_over_ground, heading, position_ts,
        COALESCE(vessel_name, 'UNKNOWN') AS vessel_name,
        COALESCE(vessel_type, 'Unknown') AS vessel_type,
        COALESCE(nav_status, 'Unknown') AS nav_status,
        source_file, created_at
    FROM source
)
SELECT * FROM renamed
