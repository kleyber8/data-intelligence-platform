"""
DAG 02 — Transformación a Capa Silver con dbt + Quality Gate 2.

Orquesta la construcción de la capa Silver:

    check_bronze_ready
        → run_dbt_silver
        → test_dbt_silver
        → run_quality_gate_2
        → notify_silver_completion
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
    dag_id="dag_02_silver_transformation",
    description="dbt Silver → Quality Gate 2",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["maritime", "silver", "dbt", "quality-gate-2"],
    doc_md=__doc__,
)
def dag_silver_transformation():

    @task(task_id="check_bronze_ready")
    def check_bronze_ready() -> dict[str, int]:
        """Verifica que existan registros validados en Bronze."""
        from src.storage.db import get_engine
        with get_engine().begin() as conn:
            n = int(conn.execute(text(
                "SELECT COUNT(*) FROM bronze.bronze_ais_position WHERE quality_status='validated'"
            )).scalar_one())
        if n == 0:
            raise ValueError("Bronze no tiene registros validados. Ejecutar DAG 01 antes.")
        logger.info("Bronze listo: %d registros validados", n)
        return {"validated_rows": n}

    run_dbt_silver = BashOperator(
        task_id="run_dbt_silver",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"DBT_PROFILES_DIR={DBT_PROFILES_DIR} "
            f"dbt run --select tag:silver --no-version-check"
        ),
        append_env=True,
    )

    test_dbt_silver = BashOperator(
        task_id="test_dbt_silver",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"DBT_PROFILES_DIR={DBT_PROFILES_DIR} "
            f"dbt test --select tag:silver --no-version-check"
        ),
        append_env=True,
    )

    @task(task_id="run_quality_gate_2")
    def qg2() -> dict[str, Any]:
        from src.validation.quality_gate_2 import run_quality_gate_2
        return run_quality_gate_2()

    @task(task_id="notify_silver_completion")
    def notify(qg2_result: dict[str, Any]) -> None:
        status = "OK" if qg2_result["all_passed"] else "FAIL"
        logger.info("=== Silver pipeline finalizado: %s ===", status)
        logger.info("Violaciones totales: %d", qg2_result["total_violations"])
        for check in qg2_result["checks"]:
            logger.info("  - %s: %s (%d)", check["rule"],
                        "PASS" if check["passed"] else "FAIL", check["violations"])

    bronze = check_bronze_ready()
    qg2_result = qg2()
    done = notify(qg2_result)

    bronze >> run_dbt_silver >> test_dbt_silver >> qg2_result >> done


dag_silver_transformation()
