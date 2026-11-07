"""Módulo para el registro (Model Registry) de artefactos en MinIO."""
from __future__ import annotations
import logging
from pathlib import Path
import joblib
from src.storage.s3_lake import get_s3_client
from src.config import settings

logger = logging.getLogger("ml.registry")

def save_model_to_minio(model: object, model_name: str, version: str) -> str:
    """Serializa un modelo a .joblib y lo sube a MinIO S3."""
    local_path = Path(f"/tmp/{model_name}_{version}.joblib")
    joblib.dump(model, local_path)
    
    client = get_s3_client()
    s3_key = f"models/{model_name}/{version}.joblib"
    bucket = "ml-models"
    
    # Asegurar que el bucket existe
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:
        client.create_bucket(Bucket=bucket)
        logger.info(f"Bucket {bucket} creado.")
        
    logger.info(f"Subiendo modelo a s3://{bucket}/{s3_key}...")
    client.upload_file(str(local_path), bucket, s3_key)
    
    local_path.unlink()
    logger.info("Modelo registrado exitosamente.")
    return f"s3://{bucket}/{s3_key}"
