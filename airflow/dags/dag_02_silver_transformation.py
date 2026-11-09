from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from sqlalchemy import text
from src.storage.db import get_engine
from src.validation.quality_gate_2 import run_quality_gate_2
import logging

logger = logging.getLogger(__name__)
DBT_PROJECT_DIR = "/opt/airflow/dbt/maritime"
DBT_PROFILES_DIR = "/home/airflow/.dbt"

@dag(
    dag_id="dag_02_silver_transformation",
    start_date=datetime(2026, 1, 1),
    schedule="@daily", # Se ejecutará todos los días automáticamente
    catchup=False,
    default_args={"owner": "data-eng", "retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["dbt", "silver", "maritime"],
)
def silver_transformation_dag():
    @task(task_id="check_bronze_ready")
    def check_bronze_ready():
        with get_engine().begin() as conn:
            n = int(conn.execute(text("SELECT COUNT(*) FROM bronze.bronze_ais_position WHERE quality_status='validated'")).scalar_one())
        if n == 0:
            raise ValueError("Bronze no tiene registros validados. Ejecutar DAG 01 antes.")
        logger.info(f"Bronze listo: {n} registros validados")

    run_dbt_silver = BashOperator(
        task_id="run_dbt_silver",
        bash_command=f"cd {DBT_PROJECT_DIR} && DBT_PROFILES_DIR={DBT_PROFILES_DIR} dbt run --select tag:silver --no-version-check",
        append_env=True,
    )

    test_dbt_silver = BashOperator(
        task_id="test_dbt_silver",
        bash_command=f"cd {DBT_PROJECT_DIR} && DBT_PROFILES_DIR={DBT_PROFILES_DIR} dbt test --select tag:silver --no-version-check",
        append_env=True,
    )

    @task(task_id="run_quality_gate_2")
    def run_qg2():
        res = run_quality_gate_2()
        if not res["all_passed"]:
            raise ValueError(f"QG2 falló: {res}")
        return res

    check_bronze_ready() >> run_dbt_silver >> test_dbt_silver >> run_qg2()

silver_transformation_dag()
