from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str

# ---------- Health ----------
class HealthStatus(BaseModel):
    status: str
    database: str
    version: str
    timestamp: datetime

# ---------- Ports ----------
class PortBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    port_id: str
    port_name: str
    country_code: str
    latitude: float
    longitude: float

class PortCongestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    port_id: str
    hour: datetime
    unique_vessels: int
    avg_speed_knots: Optional[float]
    congestion_score: float
    congestion_level: str

# ---------- Vessels ----------
class VesselProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    mmsi: str
    vessel_name: Optional[str]
    vessel_type: Optional[str]
    total_voyages: int
    total_distance_km: float
    avg_speed_knots: Optional[float]
    first_seen: datetime
    last_seen: datetime

class Voyage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    track_id: str
    mmsi: str
    start_ts: datetime
    end_ts: datetime
    total_distance_km: float
    duration_seconds: float
    num_positions: int

# ---------- Routes ----------
class RouteIntelligence(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    origin_port_id: str
    destination_port_id: str
    frequency: int
    avg_distance_km: Optional[float]
    avg_duration_hours: Optional[float]
    unique_vessels: int

# ---------- Anomalies ----------
class Anomaly(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    anomaly_id: str
    vessel_id: str
    timestamp: datetime
    anomaly_type: str
    severity: str
    score: float
    baseline: float
    observed_value: float
