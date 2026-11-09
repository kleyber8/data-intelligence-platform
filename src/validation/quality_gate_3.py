import logging
from sqlalchemy import text
from src.storage.db import get_engine
logger = logging.getLogger(__name__)

def run_quality_gate_3() -> dict:
    with get_engine().begin() as conn:
        # Cross-layer consistency (una sola conexión)
        silver_total = float(conn.execute(text("SELECT COALESCE(SUM(distance_km), 0) FROM silver.int_vessel_tracks WHERE distance_km IS NOT NULL")).scalar_one())
        gold_total = float(conn.execute(text("SELECT COALESCE(SUM(total_distance_km), 0) FROM gold.fact_vessel_voyage")).scalar_one())
        diff = abs(silver_total - gold_total)
        tol = max(silver_total * 0.01, 0.001)
        passed_cross = diff <= tol

        # Completeness (nulos)
        nulls = int(conn.execute(text("""
            SELECT COUNT(*) FROM gold.fact_vessel_voyage
            WHERE mmsi IS NULL OR track_id IS NULL OR total_distance_km IS NULL
        """)).scalar_one())
        
    return {
        "all_passed": passed_cross and nulls == 0,
        "checks": [
            {"rule": "cross_layer", "violations": 0 if passed_cross else 1, "diff": diff},
            {"rule": "completeness", "violations": nulls}
        ]
    }
