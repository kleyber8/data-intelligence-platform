"""
DAG 03 — Transformación a Capa Gold con dbt + Quality Gate 3.

Orquesta la construcción de la capa Gold:

    check_silver_ready
        → run_dbt_gold
        → test_dbt_gold
        → run_quality_gate_3
        → notify_gold_completion
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from sqlalchemy import text

logger = logging.getLogger(__name__)

DBT_PROJECT_DIR = "/opt/airflow/dbt/maritime"
DBT_PROFILES_DIR = "/home/airflow/.dbt"

DEFAULT_ARGS: dict[str, Any] = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


@dag(
    dag_id="dag_03_gold_transformation",
    description="dbt Gold → Quality Gate 3",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["maritime", "gold", "dbt", "quality-gate-3"],
    doc_md=__doc__,
)
def dag_gold_transformation():

    @task(task_id="check_silver_ready")
    def check_silver_ready() -> dict[str, int]:
        """Verifica que Silver tenga datos antes de construir Gold."""
        from src.storage.db import get_engine
        with get_engine().begin() as conn:
            n = int(conn.execute(text(
                "SELECT COUNT(*) FROM silver.int_vessel_tracks"
            )).scalar_one())
        if n == 0:
            raise ValueError("Silver está vacío. Ejecutar DAG 02 antes.")
        logger.info("Silver listo: %d registros", n)
        return {"silver_rows": n}

    run_dbt_gold = BashOperator(
        task_id="run_dbt_gold",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"DBT_PROFILES_DIR={DBT_PROFILES_DIR} "
            f"dbt run --select tag:gold --no-version-check"
        ),
        append_env=True,
    )

    test_dbt_gold = BashOperator(
        task_id="test_dbt_gold",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"DBT_PROFILES_DIR={DBT_PROFILES_DIR} "
            f"dbt test --select tag:gold --no-version-check"
        ),
        append_env=True,
    )

    @task(task_id="run_quality_gate_3")
    def qg3() -> dict[str, Any]:
        from src.validation.quality_gate_3 import run_quality_gate_3
        return run_quality_gate_3()

    @task(task_id="notify_gold_completion")
    def notify(qg3_result: dict[str, Any]) -> None:
        status = "OK" if qg3_result["all_passed"] else "FAIL"
        logger.info("=== Gold pipeline finalizado: %s ===", status)
        logger.info("Violaciones totales: %d", qg3_result["total_violations"])
        for check in qg3_result["checks"]:
            logger.info("  - %s: %s (%d)", check["rule"],
                        "PASS" if check["passed"] else "FAIL", check["violations"])

    silver = check_silver_ready()
    qg3_result = qg3()
    done = notify(qg3_result)

    silver >> run_dbt_gold >> test_dbt_gold >> qg3_result >> done


dag_gold_transformation()
