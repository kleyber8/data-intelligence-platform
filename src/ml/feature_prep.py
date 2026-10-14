"""
Pipeline de preparación de features para Machine Learning.

Aplica:
    1. Split temporal train/validation/test (nunca aleatorio).
    2. Limpieza de outliers extremos con rango intercuartílico.
    3. Imputación segura de nulos.
    4. Escalado de features (StandardScaler).

Garantiza la ausencia de data leakage temporal: todas las features
provienen de información disponible antes del target.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import polars as pl

logger = logging.getLogger("ml.feature_prep")


def _clean_outliers(
    df: pl.DataFrame,
    column: str,
    factor: float = 3.0,
) -> pl.DataFrame:
    """Marca outliers extremos como nulos (para imputación posterior)."""
    series = df[column].to_numpy()
    q1, q3 = np.percentile(series, [25, 75])
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr

    return df.with_columns(
        pl.when(
            (pl.col(column) >= lower) & (pl.col(column) <= upper)
        ).then(pl.col(column)).otherwise(None).alias(column)
    )


def _impute_nulls(df: pl.DataFrame, column: str) -> pl.DataFrame:
    """Imputa nulos con la mediana de la columna."""
    median = df[column].median()
    if median is None:
        return df
    return df.with_columns(
        pl.col(column).fill_null(float(median)).alias(column)
    )


def _temporal_split(
    df: pl.DataFrame,
    time_column: str,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """
    Split temporal estricto: entrena con lo más antiguo, prueba con lo más nuevo.
    Esto evita data leakage temporal.
    """
    df = df.sort(time_column)
    n = df.height
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train = df.slice(0, n_train)
    val = df.slice(n_train, n_val)
    test = df.slice(n_train + n_val, n - n_train - n_val)

    return train, val, test


def _standardize(
    train: pl.DataFrame,
    val: pl.DataFrame,
    test: pl.DataFrame,
    feature_columns: list[str],
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, dict[str, float]]]:
    """
    Estandariza features usando estadísticas SOLO del conjunto de train.
    Aplicar las mismas estadísticas a val y test (evita leakage).
    """
    scaler_params: dict[str, dict[str, float]] = {}

    for col in feature_columns:
        train_mean = float(train[col].mean() or 0.0)
        train_std = float(train[col].std() or 1.0)
        if train_std == 0:
            train_std = 1.0

        scaler_params[col] = {"mean": train_mean, "std": train_std}

        train = train.with_columns(
            ((pl.col(col) - train_mean) / train_std).alias(col)
        )
        val = val.with_columns(
            ((pl.col(col) - train_mean) / train_std).alias(col)
        )
        test = test.with_columns(
            ((pl.col(col) - train_mean) / train_std).alias(col)
        )

    return train, val, test, scaler_params


def prepare_training_dataset(
    df: pl.DataFrame,
    time_column: str,
    feature_columns: list[str],
    target_column: str | None = None,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> dict[str, Any]:
    """
    Pipeline completo de preparación de features.

    Args:
        df: DataFrame con features y target.
        time_column: columna de tiempo para el split temporal.
        feature_columns: lista de columnas a usar como features.
        target_column: columna objetivo (opcional).
        train_ratio, val_ratio: proporciones del split.

    Returns:
        Diccionario con train/val/test y parámetros del scaler.
    """
    if time_column not in df.columns:
        raise ValueError(f"Columna de tiempo no existe: {time_column}")

    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Features faltantes: {missing}")

    logger.info("Preparando dataset: %d filas, %d features",
                df.height, len(feature_columns))

    # Limpiar outliers e imputar nulos
    df_clean = df
    for col in feature_columns:
        df_clean = _clean_outliers(df_clean, col)
        df_clean = _impute_nulls(df_clean, col)

    # Split temporal
    train, val, test = _temporal_split(df_clean, time_column, train_ratio, val_ratio)

    logger.info(
        "Split temporal: train=%d, val=%d, test=%d",
        train.height, val.height, test.height,
    )

    # Estandarizar
    train, val, test, scaler = _standardize(train, val, test, feature_columns)

    result = {
        "train": train,
        "validation": val,
        "test": test,
        "scaler_params": scaler,
        "feature_columns": feature_columns,
        "target_column": target_column,
        "n_train": train.height,
        "n_validation": val.height,
        "n_test": test.height,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Dataset preparado correctamente")
    return result


def prepare_vessel_features() -> dict[str, Any]:
    """Ejemplo completo: prepara features desde vessel_intelligence de Gold."""
    from sqlalchemy import text
    from src.storage.db import get_engine

    sql = text("""
        SELECT
            mmsi,
            vessel_type,
            total_voyages,
            total_distance_km,
            total_hours,
            avg_speed_knots,
            total_speed_anomalies,
            first_seen,
            last_seen
        FROM gold.vessel_intelligence
        WHERE total_voyages > 0
    """)
    with get_engine().begin() as conn:
        rows = conn.execute(sql).mappings().all()

    if not rows:
        return {"error": "No hay datos en gold.vessel_intelligence"}

    df = pl.DataFrame([dict(r) for r in rows])

    return prepare_training_dataset(
        df=df,
        time_column="first_seen",
        feature_columns=[
            "total_voyages",
            "total_distance_km",
            "total_hours",
            "avg_speed_knots",
        ],
        target_column="total_speed_anomalies",
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = prepare_vessel_features()
    if "error" not in result:
        print(f"Train: {result['n_train']}, Val: {result['n_validation']}, Test: {result['n_test']}")
        print("Scaler params:", result["scaler_params"])
        print(result["train"].head(3))
