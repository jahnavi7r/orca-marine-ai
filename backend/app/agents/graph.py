from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.models.schemas import (
    QueryExtraction, WeatherReport, OceanReport,
    GeofenceReport, PFZReport, FinalRecommendation
)
from app.agents.weather_agent import run_weather_agent
from app.agents.ocean_agent import run_ocean_agent
from app.services.gis_service import evaluate_geofencing_and_pfz
from app.agents.synthesis_agent import run_synthesis

HARBOR_REGISTRY = {
    "visakhapatnam": (17.6868, 83.2185),
    "vizag": (17.6868, 83.2185),
    "chennai": (13.0827, 80.2707),
    "kochi": (9.9312, 76.2673),
    "cochin": (9.9312, 76.2673),
    "mumbai": (18.9438, 72.8354),
    "paradip": (20.3167, 86.6114),
    "mangaluru": (12.9141, 74.8560),
    "kakinada": (16.9891, 82.2475),
    "tuticorin": (8.7642, 78.1348),
    "thoothukudi": (8.7642, 78.1348)
}

class OrcaState(TypedDict):
    query: str
    params: Optional[QueryExtraction]
    weather: Optional[WeatherReport]
    ocean: Optional[OceanReport]
    geofence: Optional[GeofenceReport]
    pfz: Optional[PFZReport]
    verdict: Optional[FinalRecommendation]

# 1. Intent Analysis Agent (Slide 3 Path A)
async def intent_agent_node(state: OrcaState):
    query_lower = state["query"].lower()
    detected_lat = 17.6868
    detected_lon = 83.2185
    harbor_name = "Visakhapatnam Harbor"

    for port, coords in HARBOR_REGISTRY.items():
        if port in query_lower:
            harbor_name = f"{port.capitalize()} Coastal Sector"
            detected_lat, detected_lon = coords
            break

    vessel = "small_motorboat"
    if any(k in query_lower for k in ["trawler", "ship", "large"]):
        vessel = "deepsea_trawler"
    elif any(k in query_lower for k in ["catamaran", "canoe", "traditional"]):
        vessel = "traditional_catamaran"

    return {
        "params": QueryExtraction(
            harbor=harbor_name,
            target_time="Next 12 Hours",
            vessel_type=vessel,
            latitude=detected_lat,
            longitude=detected_lon
        )
    }

# 2. Weather Intelligence Agent (Slide 3 Path C)
async def weather_agent_node(state: OrcaState):
    lat = state["params"].latitude
    lon = state["params"].longitude
    report = await run_weather_agent(lat, lon)
    return {"weather": report}

# 3. Ocean Analytics Agent (Slide 3 Path B)
async def ocean_agent_node(state: OrcaState):
    lat = state["params"].latitude
    lon = state["params"].longitude
    report = await run_ocean_agent(lat, lon)
    return {"ocean": report}

# 4. Geofencing & Boundary Agent (Slide 3 Path C)
async def geofencing_agent_node(state: OrcaState):
    lat = state["params"].latitude
    lon = state["params"].longitude
    gis_data = evaluate_geofencing_and_pfz(lat, lon)

    status = "CRITICAL" if (gis_data["in_mpa"] or gis_data["near_imbl"]) else "SAFE"
    report = GeofenceReport(
        is_breached=gis_data["in_mpa"] or gis_data["near_imbl"],
        imbl_alert=gis_data["near_imbl"],
        mpa_alert=gis_data["in_mpa"],
        nearest_restricted_zone="Rushikonda Eco-Reserve / Palk Strait Border" if status == "CRITICAL" else "None",
        status=status,
        evidence=f"IMBL Alert: {'ACTIVE' if gis_data['near_imbl'] else 'CLEAR'} | MPA Restricted Zone: {'BREACH' if gis_data['in_mpa'] else 'CLEAR'}."
    )
    return {"geofence": report}

# 5. PFZ & Ocean Color Discovery Agent (Slide 3 Path A)
async def pfz_agent_node(state: OrcaState):
    lat = state["params"].latitude
    lon = state["params"].longitude
    gis_data = evaluate_geofencing_and_pfz(lat, lon)

    report = PFZReport(
        pfz_detected=True,
        target_coordinates=gis_data["pfz_coords"],
        chlorophyll_level="High (1.45 mg/m³)",
        satellite_sensor="Oceansat-3 OCM-3 & INSAT SST",
        evidence=f"Active feeding front identified via {gis_data['source']}."
    )
    return {"pfz": report}

# 6. Multi-Agent Synthesis Node (Slide 3 Synthesized Recommendation)
async def synthesis_node(state: OrcaState):
    verdict = run_synthesis(
        params=state["params"],
        weather=state["weather"],
        ocean=state["ocean"],
        geofence=state["geofence"],
        pfz=state["pfz"]
    )
    return {"verdict": verdict}

# Assemble StateGraph
builder = StateGraph(OrcaState)

builder.add_node("intent_agent", intent_agent_node)
builder.add_node("weather_agent", weather_agent_node)
builder.add_node("ocean_agent", ocean_agent_node)
builder.add_node("geofence_agent", geofencing_agent_node)
builder.add_node("pfz_agent", pfz_agent_node)
builder.add_node("synthesis", synthesis_node)

builder.set_entry_point("intent_agent")

# Parallel fan-out
builder.add_edge("intent_agent", "weather_agent")
builder.add_edge("intent_agent", "ocean_agent")
builder.add_edge("intent_agent", "geofence_agent")
builder.add_edge("intent_agent", "pfz_agent")

# Collect into synthesis
builder.add_edge("weather_agent", "synthesis")
builder.add_edge("ocean_agent", "synthesis")
builder.add_edge("geofence_agent", "synthesis")
builder.add_edge("pfz_agent", "synthesis")

builder.add_edge("synthesis", END)

orca_graph = builder.compile()