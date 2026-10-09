"""Helper de conexión y operaciones contra S3/MinIO."""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.client import BaseClient
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from src.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_s3_client() -> BaseClient:
    """Devuelve un cliente S3 cacheado, configurado para MinIO o AWS."""
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def upload_file(local_path: Path, bucket: str, s3_key: str) -> None:
    """Sube un archivo local a un bucket S3/MinIO."""
    client = get_s3_client()
    try:
        client.upload_file(str(local_path), bucket, s3_key)
        logger.info("Subido a s3://%s/%s", bucket, s3_key)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Error subiendo %s a s3://%s/%s: %s", local_path, bucket, s3_key, exc)
        raise
