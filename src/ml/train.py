"""Script principal de entrenamiento: extrae de Gold, entrena y registra en MinIO."""
from __future__ import annotations
import logging
import json
from datetime import datetime
from sqlalchemy import text
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.storage.db import get_engine
from src.ml.preprocessing import temporal_split
from src.ml.models import get_eta_model
from src.ml.registry import save_model_to_minio

logger = logging.getLogger("ml.train")
logging.basicConfig(level=logging.INFO)

def train_eta_model() -> None:
    """Pipeline completo de entrenamiento para ETA."""
    logger.info("Iniciando extracción de datos desde Gold...")
    
    # 1. Extraer datos
    with get_engine().begin() as conn:
        df = pd.read_sql(text("""
            SELECT start_ts, total_distance_km, avg_speed_knots, vessel_type, duration_seconds
            FROM gold.fact_vessel_voyage
            WHERE total_distance_km > 0
        """), conn)

    if len(df) < 10:
        logger.error("Muy pocos datos en Gold para entrenar (se necesitan al menos 10).")
        return

    # 2. Feature Engineering básico
    df['start_ts'] = pd.to_datetime(df['start_ts'])
    # Target: ETA (duración en horas)
    df['eta_hours'] = df['duration_seconds'] / 3600.0
    
    # Convertir variable categórica a numérica (One-Hot Encoding)
    df = pd.get_dummies(df, columns=['vessel_type'], drop_first=True)
    
    # 3. Split Temporal (Devuelve 3 dataframes: train, val, test)
    train_df, val_df, test_df = temporal_split(df, time_col='start_ts')
    
    # 4. Separar Features (X) y Target (y)
    # Eliminamos las columnas que no son features (tiempos crudos y el target)
    drop_cols = ['start_ts', 'duration_seconds', 'eta_hours']
    feature_cols = [c for c in train_df.columns if c not in drop_cols]
    
    X_train, y_train = train_df[feature_cols], train_df['eta_hours']
    X_val, y_val = val_df[feature_cols], val_df['eta_hours']
    
    logger.info(f"Features utilizadas ({len(feature_cols)}): {feature_cols}")

    # 5. Entrenamiento con Early Stopping
    logger.info("Entrenando modelo XGBoost...")
    model = get_eta_model()
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False
    )

    # 6. Evaluación en Validación (Corregido para versiones modernas de sklearn)
    preds_val = model.predict(X_val)
    mae = mean_absolute_error(y_val, preds_val)
    rmse = float(np.sqrt(mean_squared_error(y_val, preds_val)))
    
    logger.info(f"Métricas Val: MAE={mae:.2f} horas, RMSE={rmse:.2f} horas")

    # 7. Registro en MinIO
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_uri = save_model_to_minio(model, "eta_model", version)
    
    # 8. Guardar métricas locales
    metrics = {"mae": mae, "rmse": rmse, "version": version, "s3_uri": s3_uri}
    with open(f"/tmp/metrics_{version}.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Entrenamiento finalizado. Artefacto en {s3_uri}")

if __name__ == "__main__":
    train_eta_model()
