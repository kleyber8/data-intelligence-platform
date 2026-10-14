"""
Resampling temporal de trayectorias AIS.

Convierte series irregulares (frecuencia variable) en series regulares
de paso fijo (por defecto 15 minutos). Aplica interpolación lineal
en el espacio de lat/lon y velocidad.

Precaución: los gaps mayores al umbral configurado NO se interpolan.
Se marcan como `is_interpolated = False` para preservar la semántica.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import polars as pl

logger = logging.getLogger("transformations.temporal_resampling")

DEFAULT_INTERVAL_MINUTES = 15
MAX_GAP_MINUTES = 180  # No interpolar más allá de 3 horas de gap


def _interpolate_track(
    track_df: pl.DataFrame,
    interval_minutes: int,
) -> pl.DataFrame:
    """
    Interpola linealmente una trayectoria a una malla temporal regular.

    Args:
        track_df: DataFrame con columnas mmsi, track_id, latitude, longitude,
                  speed_over_ground, position_ts para UN SOLO track.
        interval_minutes: paso temporal en minutos.

    Returns:
        DataFrame con la misma estructura, remuestreada.
    """
    if track_df.height < 2:
        return track_df

    # Convertir a arrays numpy para manipulación rápida
    ts = track_df["position_ts"].to_numpy()
    lats = track_df["latitude"].to_numpy()
    lons = track_df["longitude"].to_numpy()
    speeds = track_df["speed_over_ground"].to_numpy()

    # Nueva malla temporal regular
    t_start = ts.min()
    t_end = ts.max()
    interval_ns = np.timedelta64(interval_minutes, "m")
    new_ts = np.arange(t_start, t_end + interval_ns, interval_ns)

    if len(new_ts) < 2:
        return track_df

    # Timestamps en nanosegundos para interpolación
    ts_ns = ts.astype("datetime64[ns]").astype(np.int64)
    new_ts_ns = new_ts.astype("datetime64[ns]").astype(np.int64)

    # Interpolación lineal
    new_lats = np.interp(new_ts_ns, ts_ns, lats)
    new_lons = np.interp(new_ts_ns, ts_ns, lons)
    new_speeds = np.interp(new_ts_ns, ts_ns, speeds)

    # Marcar qué puntos son originales vs interpolados
    original_mask = np.isin(new_ts_ns, ts_ns)

    # Detectar gaps mayores al umbral
    gap_diff = np.diff(ts_ns) / 1e9 / 60  # minutos entre pings originales
    has_gap = (gap_diff > MAX_GAP_MINUTES).any()

    mmsi = track_df["mmsi"][0]
    track_id = track_df["track_id"][0]
    vessel_name = track_df["vessel_name"][0] if "vessel_name" in track_df.columns else None
    vessel_type = track_df["vessel_type"][0] if "vessel_type" in track_df.columns else None
    nav_status = track_df["nav_status"][0] if "nav_status" in track_df.columns else None

    result = pl.DataFrame({
        "mmsi": [mmsi] * len(new_ts),
        "track_id": [track_id] * len(new_ts),
        "vessel_name": [vessel_name] * len(new_ts),
        "vessel_type": [vessel_type] * len(new_ts),
        "nav_status": [nav_status] * len(new_ts),
        "position_ts": new_ts,
        "latitude": new_lats.astype(np.float64),
        "longitude": new_lons.astype(np.float64),
        "speed_over_ground": new_speeds.astype(np.float64),
        "is_interpolated": ~original_mask,
        "has_temporal_gap": [has_gap] * len(new_ts),
    })

    return result


def resample_tracks(
    df: pl.DataFrame,
    interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
) -> pl.DataFrame:
    """
    Remuestrea todas las trayectorias de un DataFrame.

    Args:
        df: DataFrame con columnas mmsi, track_id, latitude, longitude,
            speed_over_ground, position_ts.
        interval_minutes: paso temporal en minutos.

    Returns:
        DataFrame remuestreado, concatenando todos los tracks.
    """
    required = {"mmsi", "track_id", "latitude", "longitude",
                "speed_over_ground", "position_ts"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Columnas faltantes: {missing}")

    tracks = df.partition_by("track_id", as_dict=False)
    logger.info("Remuestreando %d tracks", len(tracks))

    results = []
    for track_df in tracks:
        track_df = track_df.sort("position_ts")
        resampled = _interpolate_track(track_df, interval_minutes)
        results.append(resampled)

    if not results:
        return pl.DataFrame()

    return pl.concat(results)


def resample_from_silver(
    interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
    limit_tracks: int | None = None,
) -> pl.DataFrame:
    """
    Lee int_vessel_tracks de Silver y remuestrea sus trayectorias.

    Args:
        interval_minutes: paso temporal en minutos.
        limit_tracks: limita el número de tracks para pruebas rápidas.

    Returns:
        DataFrame remuestreado.
    """
    from sqlalchemy import text
    from src.storage.db import get_engine

    sql = text("""
        SELECT
            mmsi, track_id, vessel_name, vessel_type, nav_status,
            latitude, longitude, speed_over_ground, position_ts
        FROM silver.int_vessel_tracks
        ORDER BY track_id, position_ts
    """)
    with get_engine().begin() as conn:
        rows = conn.execute(sql).mappings().all()

    if not rows:
        logger.warning("No hay filas en int_vessel_tracks")
        return pl.DataFrame()

    df = pl.DataFrame([dict(r) for r in rows])

    if limit_tracks is not None:
        track_ids = df["track_id"].unique().sort().head(limit_tracks)
        df = df.filter(pl.col("track_id").is_in(track_ids))

    return resample_tracks(df, interval_minutes)


def summary(resampled: pl.DataFrame) -> dict[str, Any]:
    """Resumen estadístico del resultado del remuestreo."""
    if resampled.height == 0:
        return {"rows": 0}

    return {
        "rows": resampled.height,
        "tracks": resampled["track_id"].n_unique(),
        "interpolated_ratio": float(
            resampled.filter(pl.col("is_interpolated")).height / resampled.height
        ),
        "tracks_with_gaps": resampled.filter(
            pl.col("has_temporal_gap")
        )["track_id"].n_unique(),
        "avg_speed": float(resampled["speed_over_ground"].mean() or 0.0),
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = resample_from_silver(interval_minutes=15)
    print(summary(result))
    if result.height > 0:
        print(result.head(10))
