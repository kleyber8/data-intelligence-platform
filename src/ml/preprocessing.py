"""Módulo de preprocesamiento y selección de variables con rigor estadístico."""
from __future__ import annotations
import logging
from typing import Any
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.feature_selection import f_classif
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("ml.preprocessing")

def temporal_split(df: pd.DataFrame, time_col: str, train_ratio: float = 0.7, val_ratio: float = 0.15) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Realiza un split ESTRICTAMENTE temporal para evitar Data Leakage."""
    df = df.sort_values(by=time_col).reset_index(drop=True)
    n = len(df)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    
    train = df.iloc[:n_train].copy()
    val = df.iloc[n_train:n_train+n_val].copy()
    test = df.iloc[n_train+n_val:].copy()
    
    logger.info(f"Split Temporal completado: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    return train, val, test

def apply_pca(X_train: pd.DataFrame, X_val: pd.DataFrame, X_test: pd.DataFrame, n_components: float = 0.95) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, PCA]:
    """Aplica PCA para eliminar multicolinealidad, ajustando SOLO con el train."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    pca = PCA(n_components=n_components)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_val_pca = pca.transform(X_val_scaled)
    X_test_pca = pca.transform(X_test_scaled)
    
    cols = [f"PC_{i}" for i in range(X_train_pca.shape[1])]
    logger.info(f"PCA retuvo {n_components*100}% de la varianza con {len(cols)} componentes.")
    
    return (pd.DataFrame(X_train_pca, columns=cols), 
            pd.DataFrame(X_val_pca, columns=cols), 
            pd.DataFrame(X_test_pca, columns=cols), pca)

def select_features_anova(X_train: pd.DataFrame, y_train: pd.Series, p_threshold: float = 0.05) -> list[str]:
    """Selecciona características usando ANOVA F-test, descartando p-values > 0.05."""
    f_scores, p_values = f_classif(X_train, y_train)
    selected = X_train.columns[p_values < p_threshold].tolist()
    logger.info(f"ANOVA seleccionó {len(selected)} de {len(X_train.columns)} features (p < {p_threshold})")
    return selected
