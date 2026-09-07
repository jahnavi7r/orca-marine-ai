from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class QueryExtraction(BaseModel):
    harbor: str = Field(description="Departure harbor or coastal zone")
    target_time: str = Field(description="Time window for departure")
    vessel_type: str = Field(default="small_motorboat")
    latitude: float
    longitude: float

class WeatherReport(BaseModel):
    wind_speed_knots: float
    gusts_knots: float
    squall_warning: bool
    status: Literal["SAFE", "CAUTION", "CRITICAL"]
    evidence: str

class OceanReport(BaseModel):
    significant_wave_height_m: float
    swell_period_sec: float
    sea_surface_temp_c: float
    status: Literal["SAFE", "CAUTION", "CRITICAL"]
    evidence: str

class GeofenceReport(BaseModel):
    is_breached: bool
    imbl_alert: bool
    mpa_alert: bool
    nearest_restricted_zone: str
    status: Literal["SAFE", "CAUTION", "CRITICAL"]
    evidence: str

class PFZReport(BaseModel):
    pfz_detected: bool
    target_coordinates: List[float]  # [lat, lon]
    chlorophyll_level: str
    satellite_sensor: str
    evidence: str

class Waypoint(BaseModel):
    sequence: int
    name: str
    coordinates: List[float]  # [lat, lon]
    nav_instruction: str

class FinalRecommendation(BaseModel):
    overall_status: Literal["SAFE", "CAUTION", "CRITICAL"]
    primary_recommendation: str
    detailed_reasoning: str
    risk_factors: List[str]
    suggested_safe_zones: List[str]
    nav_waypoints: List[Waypoint]
    geojson_overlays: Dict[str, Any]
    evidence_breakdown: Dict[str, Any]