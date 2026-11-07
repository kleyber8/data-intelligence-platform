"""Módulo de análisis causal para distinguir correlación de causalidad."""
from __future__ import annotations
import logging
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests

logger = logging.getLogger("ml.causal_analysis")

def test_granger_causality(df: pd.DataFrame, cause_col: str, effect_col: str, max_lag: int = 6) -> dict:
    """
    Realiza el test de Causalidad de Granger.
    Determina si la serie 'cause_col' es útil para predecir 'effect_col'.
    """
    logger.info(f"Ejecutando Test de Granger: {cause_col} -> {effect_col}")
    
    # Granger requiere que las series sean estacionarias. 
    # Un enfoque simplificado es aplicar diferencia de primer orden.
    data = df[[effect_col, cause_col]].diff().dropna()
    
    try:
        results = grangercausalitytests(data, maxlag=max_lag, verbose=False)
        # Extraemos el p-value del test de F para el lag 1
        p_value = results[1][0]['ssr_ftest'][1]
        is_causal = p_value < 0.05
        
        logger.info(f"Resultado Granger: p-value={p_value:.4f} (Causal={is_causal})")
        return {"cause": cause_col, "effect": effect_col, "p_value": p_value, "is_causal": is_causal}
    except Exception as e:
        logger.error(f"Error en Granger: {e}")
        return {"cause": cause_col, "effect": effect_col, "error": str(e)}
