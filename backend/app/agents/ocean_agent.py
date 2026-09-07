from app.models.schemas import OceanReport
from app.services.weather_service import fetch_marine_weather

async def run_ocean_agent(lat: float, lon: float) -> OceanReport:
    data = await fetch_marine_weather(lat, lon)
    wave_height = data["wave_height"]
    period = data["wave_period"]
    
    if wave_height >= 2.5:
        status = "CRITICAL"
    elif wave_height >= 1.6:
        status = "CAUTION"
    else:
        status = "SAFE"
        
    evidence = (
        f"Significant wave height: {wave_height}m, Swell period: {period}s. "
        f"[Source: {data['source']}]"
    )
    
    return OceanReport(
        significant_wave_height_m=wave_height,
        swell_period_sec=period,
        sea_surface_temp_c=28.5,
        status=status,
        evidence=evidence
    )