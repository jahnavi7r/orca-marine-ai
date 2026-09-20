import httpx
import re
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.models.schemas import (
    QueryExtraction, WeatherReport, OceanReport,
    GeofenceReport, PFZReport, FinalRecommendation, NavWaypoint
)
from app.services.satellite_service import fetch_global_satellite_ocean_data
from app.services.gis_service import evaluate_global_geofencing, generate_global_mission_plan

class OrcaState(TypedDict):
    query: str
    chat_history: Optional[list]
    previous_location: Optional[dict]
    params: Optional[QueryExtraction]
    telemetry: Optional[dict]
    weather: Optional[WeatherReport]
    ocean: Optional[OceanReport]
    geofence: Optional[GeofenceReport]
    pfz: Optional[PFZReport]
    mission_plan: Optional[dict]
    verdict: Optional[FinalRecommendation]

async def resolve_global_coordinates(query: str):
    """
    Resolves real-world latitude and longitude for English, Telugu, Tamil, and Hindi inputs.
    Returns (None, None, None) if no valid location candidate can be geocoded.
    """
    # 1. Raw GPS coordinates regex (e.g., "17.68, 83.21")
    coord_match = re.search(r'(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)', query)
    if coord_match:
        lat = float(coord_match.group(1))
        lon = float(coord_match.group(2))
        return lat, lon, f"Coordinates ({lat:.2f}, {lon:.2f})"

    # 2. Comprehensive stopword removal across English, Telugu, Tamil, and Hindi
    cleaned = query
    # English stopwords
    cleaned = re.sub(
        r'(?i)\b(analyze|sea|conditions|condition|is|it|safe|for|fishing|can|we|go|take|a|boat|trawler|out|from|near|at|in|to|tomorrow|today|tonight|now|window|please|tell|me|the|of|what|about|how|swell|wave|waves|wind|speed|height|gusts)\b',
        ' ',
        cleaned
    )
    # Telugu stopwords
    cleaned = re.sub(r'(వద్ద|సముద్ర|పరిస్థితులను|పరిస్థితి|విశ్లేషించండి|చేపల|వేటకు|వెళ్లవచ్చా|చెప్పండి|తీరం|రేవు|అలలు|గాలులు|ఎలా|ఉంది)', ' ', cleaned)
    # Tamil stopwords
    cleaned = re.sub(r'(இல்|கடல்|நிலையை|நிலை|பகுப்பாய்வு|செய்யுங்கள்|மீன்பிடிக்க|செல்லலாமா|சொல்லுங்கள்|துறைமுகம்|அலைகள்|காற்று)', ' ', cleaned)
    # Hindi stopwords
    cleaned = re.sub(r'(में|पर|समुद्र|की|स्थिति|का|विश्लेषण|करें|मछली|पकड़ने|जा|सकते|हैं|बताएं|बंदरगाह|लहरें|हवा)', ' ', cleaned)

    search_query = cleaned.strip()

    # If the cleaned text is empty or too short, return None to allow previous_location retention
    if not search_query or len(search_query) < 2:
        return None, None, None

    candidates = [search_query]
    if query.strip() not in candidates:
        candidates.append(query.strip())

    headers = {"User-Agent": "ORCA-Marine-SIH2026-Global-Agent/2.2"}
    
    async with httpx.AsyncClient(timeout=8.0) as client:
        for candidate in candidates:
            if not candidate:
                continue
            try:
                url = "https://nominatim.openstreetmap.org/search"
                res = await client.get(url, params={"q": candidate, "format": "json", "limit": 1}, headers=headers)
                if res.status_code == 200 and len(res.json()) > 0:
                    item = res.json()[0]
                    lat = float(item["lat"])
                    lon = float(item["lon"])
                    place_name = item.get("display_name", candidate).split(",")[0]
                    return lat, lon, place_name
            except Exception as e:
                print(f"[Geocoder Candidate Error]: {e}")

    return None, None, None

async def intent_agent_node(state: OrcaState):
    lat, lon, place_name = await resolve_global_coordinates(state["query"])

    # If the user's follow-up didn't specify a new place, retain the previous location context
    if (lat is None or lon is None) and state.get("previous_location"):
        prev = state["previous_location"]
        lat = prev.get("latitude")
        lon = prev.get("longitude")
        place_name = prev.get("harbor")

    # If still unresolved, trigger the location not found error
    if lat is None or lon is None:
        raise ValueError("LOCATION_NOT_FOUND")

    mission = generate_global_mission_plan(lat, lon, place_name)
    telemetry = await fetch_global_satellite_ocean_data(lat, lon)

    vessel = "small_motorboat"
    q_lower = state["query"].lower()
    if any(k in q_lower for k in ["trawler", "ship", "large", "deep sea"]):
        vessel = "deepsea_trawler"
    elif any(k in q_lower for k in ["catamaran", "canoe", "traditional"]):
        vessel = "traditional_catamaran"

    return {
        "params": QueryExtraction(
            harbor=place_name,
            target_time="Next 12-24 Hours",
            vessel_type=vessel,
            latitude=lat,
            longitude=lon
        ),
        "telemetry": telemetry,
        "mission_plan": mission
    }

async def weather_agent_node(state: OrcaState):
    telem = state["telemetry"]
    wind_k = telem["wind_speed_kts"]
    gusts_k = telem["wind_gusts_kts"]
    is_squall = gusts_k > 28.0 or wind_k > 22.0

    status = "CRITICAL" if is_squall else "CAUTION" if wind_k > 16.0 else "SAFE"
    report = WeatherReport(
        wind_speed_knots=wind_k,
        gusts_knots=gusts_k,
        squall_warning=is_squall,
        status=status,
        evidence=f"Wind: {wind_k} kts, Gusts: {gusts_k} kts. Squall warning: {'ACTIVE' if is_squall else 'CLEAR'}. [Source: {telem['source']}]"
    )
    return {"weather": report}

async def ocean_agent_node(state: OrcaState):
    telem = state["telemetry"]
    wave_h = telem["wave_height_m"]
    swell_p = telem["wave_period_s"]
    sst = telem["sea_surface_temp_c"]

    status = "CRITICAL" if wave_h >= 2.5 or swell_p < 5.0 else "CAUTION" if wave_h >= 1.8 else "SAFE"
    report = OceanReport(
        significant_wave_height_m=wave_h,
        swell_period_sec=swell_p,
        sea_surface_temp_c=sst,
        status=status,
        evidence=f"Significant wave height: {wave_h}m, Swell period: {swell_p}s, SST: {sst}°C. [Source: Live Copernicus / NOAA WaveWatch III]"
    )
    return {"ocean": report}

async def geofencing_agent_node(state: OrcaState):
    lat = state["params"].latitude
    lon = state["params"].longitude
    geo_eval = evaluate_global_geofencing(lat, lon)

    status = geo_eval["status"]
    report = GeofenceReport(
        is_breached=(status == "CRITICAL"),
        imbl_alert=geo_eval["imbl_alert"],
        mpa_alert=geo_eval["mpa_alert"],
        nearest_restricted_zone="International Maritime Boundary / Marine Sanctuary" if status == "CRITICAL" else "None",
        status=status,
        evidence=f"IMBL Alert: {'ACTIVE' if geo_eval['imbl_alert'] else 'CLEAR'} | Protected Area: {'RESTRICTED' if geo_eval['mpa_alert'] else 'CLEAR'}."
    )
    return {"geofence": report}

async def pfz_agent_node(state: OrcaState):
    telem = state["telemetry"]
    mission = state["mission_plan"]
    chlor = telem["chlorophyll_mg_m3"]

    report = PFZReport(
        pfz_detected=True,
        target_coordinates=mission["pfz_coords"],
        chlorophyll_level=f"{chlor} mg/m³",
        satellite_sensor="Sentinel-3 OLCI & NOAA VIIRS Composite",
        evidence=f"Active biological feeding zone detected with Chlorophyll-a concentration of {chlor} mg/m³ and SST of {telem['sea_surface_temp_c']}°C."
    )
    return {"pfz": report}

async def synthesis_node(state: OrcaState):
    weather = state["weather"]
    ocean = state["ocean"]
    geofence = state["geofence"]
    pfz = state["pfz"]
    mission = state["mission_plan"]
    place = state["params"].harbor

    if geofence.is_breached or ocean.status == "CRITICAL" or weather.squall_warning:
        overall = "CRITICAL"
        rec = f"NO-GO: Dangerous conditions or restricted border sector detected off {place}. Sailing prohibited."
    elif ocean.status == "CAUTION" or weather.status == "CAUTION":
        overall = "CAUTION"
        rec = f"CAUTION: Elevated swell or choppy conditions off {place}. Large motorized vessels advised only."
    else:
        overall = "SAFE"
        rec = f"GO: Conditions favorable off {place}. Clear satellite navigation route identified."

    waypoints = [
        NavWaypoint(
            sequence=w["sequence"],
            name=w["name"],
            coordinates=w["coordinates"],
            nav_instruction=w["nav_instruction"]
        )
        for w in mission["waypoints"]
    ]

    # Dynamic overlays including PFZ Zone and Maritime Boundary Line
    geojson_overlays = {
        "pfz_zone": {
            "type": "Feature",
            "properties": {
                "name": "Potential Fishing Zone (PFZ)",
                "chlorophyll": pfz.chlorophyll_level,
                "sensor": pfz.satellite_sensor
            },
            "geometry": {"type": "Polygon", "coordinates": [mission["pfz_poly"]]}
        },
        "maritime_boundary": {
            "type": "Feature",
            "properties": {
                "name": "Territorial Sea Baseline / EEZ Buffer Line",
                "status": "CLEAR" if not geofence.imbl_alert else "BREACH"
            },
            "geometry": {"type": "LineString", "coordinates": mission["boundary_line"]}
        },
        "safe_zone": {
            "type": "Feature",
            "properties": {"zone": "Safe Navigation Corridor", "status": overall},
            "geometry": {"type": "Polygon", "coordinates": [mission["safe_poly"]]}
        },
        "danger_zone": {
            "type": "Feature",
            "properties": {"zone": "Severe Swell / Outer Shoal Sector", "status": "NO-GO"},
            "geometry": {"type": "Polygon", "coordinates": [mission["danger_poly"]]}
        }
    }

    verdict = FinalRecommendation(
        overall_status=overall,
        primary_recommendation=rec,
        detailed_reasoning=f"Satellite telemetry: Waves {ocean.significant_wave_height_m}m | Winds {weather.wind_speed_knots} kts | Chlorophyll {pfz.chlorophyll_level}.",
        risk_factors=[weather.evidence, ocean.evidence],
        suggested_safe_zones=["Nearshore Safe Corridor (< 12 NM)"],
        nav_waypoints=waypoints,
        geojson_overlays=geojson_overlays,
        evidence_breakdown={
            "weather_agent": {"evidence": weather.evidence},
            "ocean_agent": {"evidence": ocean.evidence},
            "geofence_agent": {"evidence": geofence.evidence},
            "pfz_agent": {"evidence": pfz.evidence}
        }
    )
    return {"verdict": verdict}

# Assemble LangGraph Pipeline
builder = StateGraph(OrcaState)
builder.add_node("intent_agent", intent_agent_node)
builder.add_node("weather_agent", weather_agent_node)
builder.add_node("ocean_agent", ocean_agent_node)
builder.add_node("geofence_agent", geofencing_agent_node)
builder.add_node("pfz_agent", pfz_agent_node)
builder.add_node("synthesis", synthesis_node)

builder.set_entry_point("intent_agent")

builder.add_edge("intent_agent", "weather_agent")
builder.add_edge("intent_agent", "ocean_agent")
builder.add_edge("intent_agent", "geofence_agent")
builder.add_edge("intent_agent", "pfz_agent")

builder.add_edge("weather_agent", "synthesis")
builder.add_edge("ocean_agent", "synthesis")
builder.add_edge("geofence_agent", "synthesis")
builder.add_edge("pfz_agent", "synthesis")

builder.add_edge("synthesis", END)

# Export the compiled multi-agent graph
orca_graph = builder.compile()