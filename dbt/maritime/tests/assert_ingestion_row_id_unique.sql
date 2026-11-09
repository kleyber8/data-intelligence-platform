SELECT COUNT(*) - COUNT(DISTINCT ingestion_row_id) AS duplicates
FROM (
    SELECT ingestion_row_id FROM silver.stg_ais_position
    UNION ALL
    SELECT ingestion_row_id FROM silver.int_vessel_position_deltas
    UNION ALL
    SELECT ingestion_row_id FROM silver.int_vessel_tracks
) all_ids
