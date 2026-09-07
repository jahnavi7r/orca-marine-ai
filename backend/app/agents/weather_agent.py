from app.models.schemas import WeatherReport
from app.services.weather_service import fetch_marine_weather

async def run_weather_agent(lat: float, lon: float) -> WeatherReport:
    data = await fetch_marine_weather(lat, lon)
    wind_speed = data["wind_speed"]
    gusts = data["wind_gusts"]
    
    squall = gusts > 30.0 or wind_speed > 25.0
    
    if squall or wind_speed >= 28.0:
        status = "CRITICAL"
    elif wind_speed >= 18.0:
        status = "CAUTION"
    else:
        status = "SAFE"
        
    evidence = (
        f"Wind: {wind_speed} kts, Gusts: {gusts} kts. "
        f"Squall alert: {'ACTIVE' if squall else 'CLEAR'}. [Source: {data['source']}]"
    )
    
    return WeatherReport(
        wind_speed_knots=wind_speed,
        gusts_knots=gusts,
        squall_warning=squall,
        status=status,
        evidence=evidence
    )