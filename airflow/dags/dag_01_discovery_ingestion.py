from datetime import datetime, timedelta
from airflow.decorators import dag, task
import logging
from ingestion.ports.world_port_index import run as run_wpi
from ingestion.maritime.noaa_ais import run_ingestion, mark_run_completed
from src.storage.bronze_writer import write_bronze_from_landing
from src.validation.quality_gate_1 import run_quality_gate_1

logger = logging.getLogger(__name__)

@dag(
    dag_id="dag_01_discovery_ingestion", start_date=datetime(2026, 1, 1), schedule="@daily", catchup=False,
    default_args={"owner": "data-eng", "retries": 2, "retry_delay": timedelta(minutes=5)}, tags=["ingestion", "bronze"]
)
def discovery_ingestion_dag():
    @task(task_id="ingest_wpi_ports", execution_timeout=timedelta(minutes=15))
    def ingest_ports() -> dict:
        logger.info("Iniciando ingesta de Puertos (WPI via Hugging Face)...")
        return run_wpi()

    @task(task_id="ingest_noaa_ais", execution_timeout=timedelta(hours=2))
    def ingest_ais() -> dict:
        logger.info("Iniciando descarga de AIS real de NOAA...")
        return run_ingestion(source="noaa")

    @task(task_id="load_to_bronze", execution_timeout=timedelta(hours=2))
    def load_to_bronze(meta: dict) -> dict:
        if meta.get("status") == "already_processed":
            return {"ingestion_run_id": meta["ingestion_run_id"], "rows": 0, "status": "already_processed"}
        ing_id = meta["ingestion_run_id"]
        rows = write_bronze_from_landing(ing_id)
        mark_run_completed(ing_id, rows)
        return {"ingestion_run_id": ing_id, "rows": rows, "status": "created"}

    @task(task_id="run_quality_gate_1", execution_timeout=timedelta(minutes=30))
    def run_qg1(bronze_meta: dict) -> dict:
        if bronze_meta.get("status") == "already_processed":
            return {"status": "skipped", "reason": "already_processed"}
        return run_quality_gate_1(bronze_meta["ingestion_run_id"])

    puertos = ingest_ports()
    ais = ingest_ais()
    bronze = load_to_bronze(ais)
    qg1 = run_qg1(bronze)
    puertos >> qg1

discovery_ingestion_dag()
