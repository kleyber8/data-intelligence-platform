{{ config(
    tags=['staging', 'silver']
) }}

WITH source AS (
    SELECT *
    FROM {{ source('bronze', 'bronze_ports') }}
    WHERE latitude IS NOT NULL
      AND longitude IS NOT NULL
),

typed AS (
    SELECT
        port_index::VARCHAR(20)                                     AS port_id,
        COALESCE(NULLIF(TRIM(port_name), ''), 'UNKNOWN')::VARCHAR(255) AS port_name,
        COALESCE(NULLIF(TRIM(country), ''), 'UNK')::VARCHAR(10)        AS country_code,
        COALESCE(NULLIF(TRIM(region_name), ''), 'UNKNOWN')::VARCHAR(50) AS region_name,
        
        -- Conversión de Web Mercator (metros) a WGS84 (grados decimales)
        degrees(2.0 * atan(exp(latitude / 6378137.0)) - pi() / 2.0)::DOUBLE PRECISION AS latitude,
        degrees(longitude / 6378137.0)::DOUBLE PRECISION AS longitude,
        
        COALESCE(NULLIF(TRIM(harbor_size), ''), 'Unknown')::VARCHAR(50) AS harbor_size,
        COALESCE(NULLIF(TRIM(harbor_type), ''), 'Unknown')::VARCHAR(50) AS harbor_type
    FROM source
)

SELECT * FROM typed
