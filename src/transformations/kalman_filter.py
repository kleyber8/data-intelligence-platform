"""
Filtro de Kalman lineal para suavizado de trayectorias AIS.

Modelo dinámico:
    Estado x = [lat, lon, v_lat, v_lon]^T
    Transición F = [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]]
    Medición H = [[1, 0, 0, 0], [0, 1, 0, 0]]

    Predicción:
        x_k|k-1 = F @ x_k-1|k-1
        P_k|k-1 = F @ P_k-1|k-1 @ F^T + Q

    Corrección:
        S = H @ P_k|k-1 @ H^T + R
        K = P_k|k-1 @ H^T @ inv(S)
        x_k|k = x_k|k-1 + K @ (z_k - H @ x_k|k-1)
        P_k|k = (I - K @ H) @ P_k|k-1

El filtro opera en un espacio proyectado (lat/lon tratadas como Cartesianas
locales) porque los desplazamientos son pequeños y la latitud de cada track
es aproximadamente constante.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import polars as pl

logger = logging.getLogger("transformations.kalman_filter")

# Parámetros del filtro
DEFAULT_PROCESS_NOISE = 1e-6      # Q: confianza en el modelo físico
DEFAULT_MEASUREMENT_NOISE = 1e-4  # R: ruido del GPS AIS (aprox 10 metros en grados)
DEFAULT_INITIAL_UNCERTAINTY = 1.0 # P0: incertidumbre inicial alta


class KalmanFilter2D:
    """
    Filtro de Kalman 2D para trayectorias GPS.

    El estado es [lat, lon, v_lat, v_lon]. Cada paso temporal aplica
    la predicción física y luego corrige con la medición del GPS.
    """

    def __init__(
        self,
        process_noise: float = DEFAULT_PROCESS_NOISE,
        measurement_noise: float = DEFAULT_MEASUREMENT_NOISE,
        initial_uncertainty: float = DEFAULT_INITIAL_UNCERTAINTY,
    ) -> None:
        # Matriz de transición (se actualiza con dt en cada paso)
        self.F = np.eye(4, dtype=np.float64)
        # Matriz de medición: solo medimos lat y lon
        self.H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ], dtype=np.float64)
        # Ruido del proceso
        self.Q_base = np.eye(4, dtype=np.float64) * process_noise
        # Ruido de la medición
        self.R = np.eye(2, dtype=np.float64) * measurement_noise
        # Incertidumbre inicial
        self.P = np.eye(4, dtype=np.float64) * initial_uncertainty
        # Estado actual (se inicializa con la primera medición)
        self.x: np.ndarray | None = None
        self.initialized = False

    def _update_transition(self, dt: float) -> None:
        """Actualiza la matriz F con el dt dado."""
        self.F = np.array([
            [1.0, 0.0, dt,  0.0],
            [0.0, 1.0, 0.0, dt ],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float64)
        # Escalar Q por dt (más incertidumbre cuando más tiempo pasa)
        self.Q = self.Q_base * max(dt, 1e-6)

    def initialize(self, lat: float, lon: float, v_lat: float = 0.0, v_lon: float = 0.0) -> None:
        """Inicializa el estado con la primera medición."""
        self.x = np.array([lat, lon, v_lat, v_lon], dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64) * DEFAULT_INITIAL_UNCERTAINTY
        self.initialized = True

    def predict(self, dt: float) -> np.ndarray:
        """Paso de predicción."""
        self._update_transition(dt)
        assert self.x is not None
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, lat: float, lon: float) -> np.ndarray:
        """Paso de corrección con medición GPS."""
        assert self.x is not None
        z = np.array([lat, lon], dtype=np.float64)
        y = z - self.H @ self.x                      # innovación
        S = self.H @ self.P @ self.H.T + self.R      # covarianza de innovación
        K = self.P @ self.H.T @ np.linalg.inv(S)     # ganancia de Kalman
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P
        return self.x

    def step(self, lat: float | None, lon: float | None, dt: float) -> np.ndarray:
        """
        Ejecuta un paso completo: predict + update (si hay medición).
        Si no hay medición, solo predict.
        """
        if not self.initialized:
            if lat is None or lon is None:
                raise ValueError("Primera medición no puede ser nula")
            self.initialize(lat, lon)

        self.predict(dt)

        if lat is not None and lon is not None:
            self.update(lat, lon)

        assert self.x is not None
        return self.x


def _process_track(track_df: pl.DataFrame) -> pl.DataFrame:
    """Aplica Kalman a un track individual."""
    if track_df.height < 2:
        return track_df

    ts = track_df["position_ts"].to_numpy()
    lats = track_df["latitude"].to_numpy()
    lons = track_df["longitude"].to_numpy()

    kf = KalmanFilter2D()
    filtered_lats: list[float] = []
    filtered_lons: list[float] = []
    uncertainties: list[float] = []

    prev_ts = None
    for i in range(len(ts)):
        if prev_ts is None:
            dt = 0.0
        else:
            dt = float((ts[i] - prev_ts) / np.timedelta64(1, "s"))

        state = kf.step(float(lats[i]), float(lons[i]), dt)
        filtered_lats.append(float(state[0]))
        filtered_lons.append(float(state[1]))
        # Traza de la covarianza como medida de incertidumbre
        uncertainties.append(float(np.trace(kf.P)))

        prev_ts = ts[i]

    return track_df.with_columns([
        pl.Series("kalman_latitude", filtered_lats, dtype=pl.Float64),
        pl.Series("kalman_longitude", filtered_lons, dtype=pl.Float64),
        pl.Series("kalman_uncertainty", uncertainties, dtype=pl.Float64),
    ])


def smooth_tracks(df: pl.DataFrame) -> pl.DataFrame:
    """Aplica el filtro de Kalman a todas las trayectorias."""
    required = {"track_id", "latitude", "longitude", "position_ts"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Columnas faltantes: {missing}")

    tracks = df.partition_by("track_id", as_dict=False)
    logger.info("Suavizando %d tracks con Kalman", len(tracks))

    results = []
    for track_df in tracks:
        track_df = track_df.sort("position_ts")
        results.append(_process_track(track_df))

    if not results:
        return pl.DataFrame()

    return pl.concat(results)


def smooth_from_silver(limit_tracks: int | None = None) -> pl.DataFrame:
    """Lee Silver y aplica el filtro de Kalman a los tracks."""
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
        return pl.DataFrame()

    df = pl.DataFrame([dict(r) for r in rows])

    if limit_tracks is not None:
        track_ids = df["track_id"].unique().sort().head(limit_tracks)
        df = df.filter(pl.col("track_id").is_in(track_ids))

    return smooth_tracks(df)


def summary(smoothed: pl.DataFrame) -> dict[str, Any]:
    """Compara las posiciones originales con las suavizadas."""
    if smoothed.height == 0:
        return {"rows": 0}

    # Error cuadrático medio entre posición original y suavizada
    lat_diff = (smoothed["latitude"] - smoothed["kalman_latitude"]).to_numpy()
    lon_diff = (smoothed["longitude"] - smoothed["kalman_longitude"]).to_numpy()
    rmse_lat = float(np.sqrt(np.mean(lat_diff ** 2)))
    rmse_lon = float(np.sqrt(np.mean(lon_diff ** 2)))

    return {
        "rows": smoothed.height,
        "tracks": smoothed["track_id"].n_unique(),
        "rmse_lat_degrees": rmse_lat,
        "rmse_lon_degrees": rmse_lon,
        "rmse_lat_meters_approx": rmse_lat * 111_000,
        "rmse_lon_meters_approx": rmse_lon * 111_000,
        "avg_uncertainty": float(smoothed["kalman_uncertainty"].mean() or 0.0),
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = smooth_from_silver()
    print(summary(result))
    if result.height > 0:
        print(result.select([
            "track_id", "position_ts", "latitude", "kalman_latitude",
            "longitude", "kalman_longitude", "kalman_uncertainty",
        ]).head(10))
