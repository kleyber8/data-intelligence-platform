from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor
from sqlalchemy import text
from src.storage.db import get_engine
from src.validation.quality_gate_3 import run_quality_gate_3
import logging

logger = logging.getLogger(__name__)
DBT_PROJECT_DIR = "/opt/airflow/dbt/maritime"
DBT_PROFILES_DIR = "/home/airflow/.dbt"

@dag(
    dag_id="dag_03_gold_transformation", start_date=datetime(2026, 1, 1), schedule="@daily", catchup=False,
    default_args={"owner": "data-eng", "retries": 1, "retry_delay": timedelta(minutes=2)}, tags=["dbt", "gold", "maritime"]
)
def gold_transformation_dag():
    wait_silver_qg2 = ExternalTaskSensor(
        task_id="wait_silver_qg2", external_dag_id="dag_02_silver_transformation", external_task_id="run_quality_gate_2",
        execution_delta=None, allowed_states=["success"], failed_states=["failed"], mode="reschedule", poke_interval=300, timeout=10800, soft_fail=False
    )

    @task(task_id="check_silver_ready")
    def check_silver_ready():
        with get_engine().begin() as conn:
            has_rows = conn.execute(text("SELECT EXISTS(SELECT 1 FROM silver.int_vessel_tracks LIMIT 1)")).scalar()
            has_ports = conn.execute(text("SELECT EXISTS(SELECT 1 FROM silver.stg_ports LIMIT 1)")).scalar()
        if not (has_rows and has_ports):
            raise ValueError("Silver incompleto.")
        logger.info("Silver listo con datos reales.")

    run_dbt_gold = BashOperator(
        task_id="run_dbt_gold", bash_command=f"cd {DBT_PROJECT_DIR} && DBT_PROFILES_DIR={DBT_PROFILES_DIR} dbt run --select tag:gold --no-version-check",
        append_env=True, execution_timeout=timedelta(hours=3)
    )

    test_dbt_gold = BashOperator(
        task_id="test_dbt_gold", bash_command=f"cd {DBT_PROJECT_DIR} && DBT_PROFILES_DIR={DBT_PROFILES_DIR} dbt test --select tag:gold --no-version-check",
        append_env=True, execution_timeout=timedelta(hours=1)
    )

    @task(task_id="run_quality_gate_3")
    def run_qg3():
        res = run_quality_gate_3()
        if not res["all_passed"]:
            raise ValueError(f"QG3 falló: {res}")
        return res

    wait_silver_qg2 >> check_silver_ready() >> run_dbt_gold >> test_dbt_gold >> run_qg3()

gold_transformation_dag()
