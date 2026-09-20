from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QueryExtraction(BaseModel):
    harbor: str
    target_time: str
    vessel_type: str
    latitude: float
    longitude: float

class WeatherReport(BaseModel):
    wind_speed_knots: float
    gusts_knots: float
    squall_warning: bool
    status: str
    evidence: str

class OceanReport(BaseModel):
    significant_wave_height_m: float
    swell_period_sec: float
    sea_surface_temp_c: float
    status: str
    evidence: str

class GeofenceReport(BaseModel):
    is_breached: bool
    imbl_alert: bool
    mpa_alert: bool
    nearest_restricted_zone: str
    status: str
    evidence: str

class PFZReport(BaseModel):
    pfz_detected: bool
    target_coordinates: List[float]
    chlorophyll_level: str
    satellite_sensor: str
    evidence: str

class NavWaypoint(BaseModel):
    sequence: int
    name: str
    coordinates: List[float]
    nav_instruction: str

class FinalRecommendation(BaseModel):
    overall_status: str
    primary_recommendation: str
    detailed_reasoning: str
    risk_factors: List[str]
    suggested_safe_zones: List[str]
    nav_waypoints: List[NavWaypoint] = Field(default_factory=list)
    geojson_overlays: Optional[Dict[str, Any]] = None
    evidence_breakdown: Optional[Dict[str, Any]] = None