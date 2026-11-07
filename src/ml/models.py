"""Fábrica de modelos de Machine Learning con hiperparámetros configurados."""
from __future__ import annotations
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN

def get_eta_model() -> xgb.XGBRegressor:
    """Modelo de regresión para predecir ETA, con regularización L1/L2 y Early Stopping."""
    return xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,   # L1 Regularization
        reg_lambda=1.0,  # L2 Regularization
        random_state=42,
        early_stopping_rounds=10,
        objective="reg:squarederror"
    )

def get_isolation_forest_model() -> IsolationForest:
    """Modelo no supervisado para detección de anomalías en alta dimensionalidad."""
    return IsolationForest(
        n_estimators=100,
        contamination=0.05, # Asumimos que el 5% de los datos son anomalías
        random_state=42
    )

def get_dbscan_model(eps: float = 0.1, min_samples: int = 5) -> DBSCAN:
    """Modelo de clustering espacial para detectar desvíos de ruta en coordenadas."""
    return DBSCAN(eps=eps, min_samples=min_samples)
