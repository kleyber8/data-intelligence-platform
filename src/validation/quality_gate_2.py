import logging
from sqlalchemy import text
from src.storage.db import get_engine

logger = logging.getLogger(__name__)

def run_quality_gate_2() -> dict:
    with get_engine().begin() as conn:
        # 1. Contar total de filas en Silver
        total_rows = int(conn.execute(text("SELECT COUNT(*) FROM silver.stg_ais_position")).scalar_one())
        
        # 2. Contar duplicados
        dups = int(conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT 1 FROM silver.stg_ais_position
                GROUP BY mmsi, position_ts HAVING COUNT(*) > 1
            ) d
        """)).scalar_one())
        
        # 3. Contar velocidades imposibles
        over = int(conn.execute(text("""
            SELECT COUNT(*) FROM silver.int_vessel_position_deltas
            WHERE calculated_speed_knots > 60.0
        """)).scalar_one())
        
    total_violations = dups + over
    error_rate = total_violations / total_rows if total_rows > 0 else 0
    
    # Permitimos hasta un 1% de errores en datos reales (AIS es ruidoso)
    all_passed = error_rate <= 0.01

    result = {
        "all_passed": all_passed,
        "total_rows": total_rows,
        "violations": total_violations,
        "error_rate": round(error_rate * 100, 3),
        "checks": [
            {"rule": "temporal_duplicates", "violations": dups},
            {"rule": "spatial_speed", "violations": over}
        ]
    }
    
    logger.info(f"QG2 Resultado: {result}")
    return result
