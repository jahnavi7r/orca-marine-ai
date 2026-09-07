from app.models.schemas import (
    WeatherReport, OceanReport, GeofenceReport, 
    PFZReport, QueryExtraction, FinalRecommendation
)
from app.services.route_service import compute_safe_waypoints, generate_zone_polygons

def run_synthesis(
    params: QueryExtraction,
    weather: WeatherReport,
    ocean: OceanReport,
    geofence: GeofenceReport,
    pfz: PFZReport
) -> FinalRecommendation:
    risks = []
    
    # 1. Weather hazards
    if weather.status == "CRITICAL":
        risks.append(f"Gale wind conditions ({weather.wind_speed_knots} kts) with severe squall probability")
    elif weather.status == "CAUTION":
        risks.append(f"Elevated surface winds ({weather.wind_speed_knots} kts)")

    # 2. Ocean hazards
    if ocean.status == "CRITICAL":
        risks.append(f"High wave heights ({ocean.significant_wave_height_m}m) exceeding small vessel stability")
    elif ocean.status == "CAUTION":
        risks.append(f"Choppy sea state (wave height: {ocean.significant_wave_height_m}m)")

    # 3. Geofence & Boundary hazards (Slide 3 Path C)
    if geofence.imbl_alert:
        risks.append("CRITICAL: Route approaches International Maritime Boundary Line (IMBL)")
    if geofence.mpa_alert:
        risks.append("Route intersects legally protected Marine Sanctuary (No Fishing Allowed)")

    # 4. Synthesize Decision Matrix
    is_critical = "CRITICAL" in [weather.status, ocean.status, geofence.status]
    is_caution = "CAUTION" in [weather.status, ocean.status, geofence.status]

    if is_critical:
        overall = "CRITICAL"
        recommendation = f"NO-GO: Do not venture out from {params.harbor}. Hostile oceanic or boundary conditions."
        safe_zones = ["Remain berthed inside port limits."]
    elif is_caution:
        overall = "CAUTION"
        recommendation = f"CAUTION: Restricted conditions off {params.harbor}. Advised for large trawlers with VHF only."
        safe_zones = ["Remain within nearshore safety corridor (< 3 NM)."]
    else:
        overall = "SAFE"
        recommendation = f"GO: Conditions favorable. Navigation corridor clear toward {pfz.target_coordinates}."
        safe_zones = [f"Oceansat-3 Target PFZ ({pfz.chlorophyll_level})"]

    # Compute navigation waypoints (Slide 5)
    waypoints = compute_safe_waypoints(
        start_coords=[params.latitude, params.longitude],
        pfz_coords=pfz.target_coordinates,
        is_critical=is_critical
    )

    # Generate spatial GeoJSON meshes (Slide 2)
    overlays = generate_zone_polygons(
        lat=params.latitude,
        lon=params.longitude,
        is_safe=(overall == "SAFE")
    )

    reasoning = (
        f"Autonomous Synthesis: [Ocean: {ocean.status}] {ocean.evidence} | "
        f"[Weather: {weather.status}] {weather.evidence} | "
        f"[Boundary: {geofence.status}] {geofence.evidence} | "
        f"[Yield Potential: {'HIGH' if pfz.pfz_detected else 'LOW'}] {pfz.evidence}"
    )

    return FinalRecommendation(
        overall_status=overall,
        primary_recommendation=recommendation,
        detailed_reasoning=reasoning,
        risk_factors=risks,
        suggested_safe_zones=safe_zones,
        nav_waypoints=waypoints,
        geojson_overlays=overlays,
        evidence_breakdown={
            "weather_agent": weather.model_dump(),
            "ocean_agent": ocean.model_dump(),
            "geofence_agent": geofence.model_dump(),
            "pfz_agent": pfz.model_dump()
        }
    )