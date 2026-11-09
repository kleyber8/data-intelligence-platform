import logging
import psycopg2
from src.config import settings

logger = logging.getLogger(__name__)

def run_quality_gate_1(ingestion_run_id: str) -> dict:
    logger.info(f"Quality Gate 1 → run_id={ingestion_run_id}")
    
    conn = psycopg2.connect(
        dbname=settings.postgres_db, user=settings.postgres_user,
        password=settings.postgres_password, host=settings.postgres_host, port=settings.postgres_port
    )
    cursor = conn.cursor()
    
    try:
        # SET LOCAL: Desactivamos synchronous_commit para velocidad y ponemos un timeout de bloqueo
        cursor.execute("SET LOCAL synchronous_commit = OFF;")
        cursor.execute("SET LOCAL lock_timeout = '15s';")
        
        # 1. Clasificar todas las filas en una sola pasada (UPDATE unificado)
        logger.info("Clasificando registros (validados vs cuarentena)...")
        cursor.execute("""
            UPDATE bronze.bronze_ais_position
            SET quality_status = CASE
                WHEN mmsi IS NULL OR mmsi !~ '^\\d{9}$' THEN 'quarantined'
                WHEN latitude IS NULL OR latitude NOT BETWEEN -90 AND 90 THEN 'quarantined'
                WHEN longitude IS NULL OR longitude NOT BETWEEN -180 AND 180 THEN 'quarantined'
                WHEN speed_over_ground IS NULL OR speed_over_ground < 0 OR speed_over_ground >= 100 THEN 'quarantined'
                WHEN position_ts IS NULL OR position_ts > NOW() THEN 'quarantined'
                ELSE 'validated'
            END,
            quality_checked_at = NOW()
            WHERE ingestion_run_id = %s
        """, (ingestion_run_id,))
        
        # 2. Insertar masivamente las filas en cuarentena
        logger.info("Insertando registros en cuarentena...")
        cursor.execute("""
            INSERT INTO quarantine.quarantine_records (
                source_record_id, failure_reason, quality_rule, 
                ingestion_run_id, source_table, original_payload
            )
            SELECT 
                ingestion_row_id,
                'Fallo en validación estructural',
                CASE
                    WHEN mmsi IS NULL OR mmsi !~ '^\\d{9}$' THEN 'valid_mmsi'
                    WHEN latitude IS NULL OR latitude NOT BETWEEN -90 AND 90 THEN 'valid_latitude'
                    WHEN longitude IS NULL OR longitude NOT BETWEEN -180 AND 180 THEN 'valid_longitude'
                    WHEN speed_over_ground IS NULL OR speed_over_ground < 0 OR speed_over_ground >= 100 THEN 'valid_speed'
                    WHEN position_ts IS NULL OR position_ts > NOW() THEN 'valid_timestamp'
                    ELSE 'unknown'
                END,
                ingestion_run_id,
                'bronze.bronze_ais_position',
                jsonb_build_object(
                    'mmsi', mmsi,
                    'latitude', latitude,
                    'longitude', longitude,
                    'speed_over_ground', speed_over_ground,
                    'position_ts', position_ts
                )
            FROM bronze.bronze_ais_position
            WHERE ingestion_run_id = %s
              AND quality_status = 'quarantined'
        """, (ingestion_run_id,))
        
        # 3. Obtener los conteos finales
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE quality_status = 'validated'),
                COUNT(*) FILTER (WHERE quality_status = 'quarantined')
            FROM bronze.bronze_ais_position
            WHERE ingestion_run_id = %s
        """, (ingestion_run_id,))
        
        res = cursor.fetchone()
        valid_count = res[0] if res else 0
        invalid_count = res[1] if res else 0
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en QG1: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
        
    result = {
        "ingestion_run_id": ingestion_run_id,
        "total": valid_count + invalid_count,
        "valid": valid_count,
        "invalid": invalid_count
    }
    
    logger.info(f"QG1 Resultado: {result}")
    return result
