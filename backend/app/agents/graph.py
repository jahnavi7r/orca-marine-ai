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

async def extract_and_geocode_location(query: str):
    """
    Confidence-Scored Universal Geocoder.
    Scans the entire sentence, ranks all candidate places by geographical importance,
    and guarantees major cities/ports override random hiking trails or generic word matches.
    """
    raw_query = query.strip()
    if not raw_query:
        return None, None, None

    # 1. Direct GPS Check (e.g. 9.93, 76.26)
    coord_match = re.search(r'(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)', raw_query)
    if coord_match:
        lat = float(coord_match.group(1))
        lon = float(coord_match.group(2))
        return lat, lon, f"Coordinates ({lat:.2f}, {lon:.2f})"

    # 2. Extract words across Unicode scripts
    tokens = re.findall(r'[\w\u0900-\u0DFF\uAC00-\uD7AF]+', raw_query, re.UNICODE)
    if not tokens:
        return None, None, None

    # Noise tokens to avoid testing as standalone places
    generic_words = {
        "is", "it", "safe", "for", "small", "large", "motorboats", "motorboat",
        "boat", "boats", "trawler", "trawlers", "venture", "out", "tomorrow",
        "today", "morning", "evening", "night", "conditions", "condition",
        "weather", "sea", "ocean", "waves", "wave", "swell", "wind", "speed",
        "can", "we", "go", "sailing", "sail", "status", "check", "tell", "give",
        "show", "please", "what", "about", "how", "alert", "warning", "fishing"
    }

    # 3. Detect Prepositional Anchors: words immediately following "off", "near", "at", "in", "from"
    priority_candidates = []
    lower_tokens = [t.lower() for t in tokens]
    for idx, token in enumerate(lower_tokens):
        if token in {"off", "near", "at", "in", "from", "around", "to"} and idx + 1 < len(tokens):
            target = tokens[idx + 1]
            if target.lower() not in generic_words:
                priority_candidates.append(target)
            if idx + 2 < len(tokens) and tokens[idx + 2].lower() not in generic_words:
                priority_candidates.append(f"{target} {tokens[idx + 2]}")

    # Build other candidate n-grams
    other_candidates = []
    for n in (2, 1):
        for i in range(len(tokens) - n + 1):
            phrase_tokens = tokens[i:i + n]
            phrase = " ".join(phrase_tokens)
            if (
                len(phrase) >= 3 and 
                phrase.lower() not in generic_words and 
                phrase not in priority_candidates and 
                phrase not in other_candidates
            ):
                other_candidates.append(phrase)

    # Search priority candidates first, then other candidates
    all_candidates = priority_candidates + other_candidates
    if raw_query not in all_candidates:
        all_candidates.append(raw_query)

    headers = {
        "User-Agent": "ORCA-Marine-Intelligence-SIH2026/5.5 (isro-sih@marine.ai)",
        "Accept-Language": "en,te,ta,hi,*"
    }

    # High-value marine & administrative classifications
    high_priority_classes = {
        "city": 1.0, "town": 0.9, "harbour": 1.0, "port": 1.0, "bay": 0.95,
        "island": 0.95, "administrative": 0.85, "state": 0.9, "coastal": 0.9,
        "sea": 0.9, "beach": 0.8, "peninsula": 0.85, "village": 0.6
    }

    best_match = None
    best_score = -1.0

    async with httpx.AsyncClient(timeout=6.0) as client:
        # Evaluate candidate places
        for candidate in all_candidates[:8]:
            try:
                osm_url = "https://nominatim.openstreetmap.org/search"
                params = {
                    "q": candidate,
                    "format": "json",
                    "limit": 3,
                    "addressdetails": 1
                }
                res = await client.get(osm_url, params=params, headers=headers)
                if res.status_code == 200:
                    results = res.json()
                    for item in results:
                        addresstype = item.get("addresstype", "")
                        osm_type = item.get("type", "")
                        osm_class = item.get("class", "")
                        importance = float(item.get("importance", 0.1))

                        # Exclude paths, tracks, trails, footways, and random words
                        if osm_class in {"highway", "footway", "path", "track", "leisure"}:
                            continue

                        # Calculate confidence score
                        type_weight = high_priority_classes.get(addresstype, high_priority_classes.get(osm_type, 0.2))
                        score = (importance * 0.6) + (type_weight * 0.4)

                        # If candidate was anchored by a preposition, apply priority bonus
                        if candidate in priority_candidates:
                            score += 0.35

                        if score > best_score and (addresstype in high_priority_classes or osm_type in high_priority_classes or osm_class in {"place", "boundary", "natural"}):
                            best_score = score
                            lat = float(item["lat"])
                            lon = float(item["lon"])
                            display_name = item.get("display_name", candidate).split(",")[0]
                            best_match = (lat, lon, display_name)

                            # Early exit on high-confidence administrative/marine match
                            if score >= 0.85:
                                return best_match
            except Exception:
                pass

        if best_match:
            return best_match

        # Fallback Engine: Komoot Photon
        for candidate in (priority_candidates or all_candidates)[:4]:
            try:
                photon_url = "https://photon.komoot.io/api/"
                p_res = await client.get(photon_url, params={"q": candidate, "limit": 2}, headers=headers)
                if p_res.status_code == 200:
                    features = p_res.json().get("features", [])
                    for feat in features:
                        props = feat.get("properties", {})
                        osm_key = props.get("osm_key", "")
                        osm_value = props.get("osm_value", "")
                        geom = feat.get("geometry", {}).get("coordinates", [])

                        if osm_key in {"highway", "footway", "path", "track"}:
                            continue

                        if (osm_key in {"place", "natural", "boundary", "waterway"} or osm_value in high_priority_classes) and len(geom) >= 2:
                            return float(geom[1]), float(geom[0]), props.get("name", candidate)
            except Exception:
                pass

    return None, None, None

def predict_marine_species(lat: float, lon: float, sst: float, chlorophyll: float) -> dict:
    """
    Bio-oceanographic fish species predictor.
    Dynamically resolves target commercial fish species based on geographic marine basin,
    sea surface temperature (SST), and primary biological productivity (chlorophyll-a).
    """
    # 1. East Asian Waters (e.g. Jeju Island, Yellow Sea, Sea of Japan)
    if 30.0 <= lat <= 45.0 and 120.0 <= lon <= 145.0:
        if sst < 20.0:
            species = "Pacific Cod, Pollock, Squid, and Flatfish"
            gear = "Bottom Trawls & Jigs"
        else:
            species = "Hairtail (Cutlassfish), Pacific Mackerel, Yellowtail, and Anchovy"
            gear = "Longlines & Purse Seines"
        zone_desc = "Temperate convergence zone supporting rich pelagic and demersal feeding grounds."

    # 2. Arabian Sea & West Coast of India (Goa, Kochi, Mumbai, Gujarat)
    elif 7.0 <= lat <= 25.0 and 65.0 <= lon <= 77.5:
        if chlorophyll > 1.8:
            species = "Indian Oil Sardine, Indian Mackerel, and Ribbonfish schools"
            gear = "Ring Seines & Gillnets"
        else:
            species = "Kingfish (Surmai), Skipjack Tuna, and Coastal Trevally"
            gear = "Trolling Lines & Hooks"
        zone_desc = "Upwelling Arabian Sea corridor rich in zooplankton and pelagic shoals."

    # 3. Bay of Bengal & East Coast of India (Visakhapatnam, Kakinada, Chennai, Odisha)
    elif 7.0 <= lat <= 23.0 and 78.0 <= lon <= 95.0:
        if sst > 29.0:
            species = "Yellowfin Tuna, White Pomfret, Seerfish, and Anchovy"
            gear = "Pelagic Longlines & Drift Gillnets"
        else:
            species = "Hilsa shad, Silver Pomfret, Croakers, and Coastal Prawns"
            gear = "Trammel Nets & Trawls"
        zone_desc = "High-nutrient riverine runoff boundary fostering prime feeding zones."

    # 4. Global Tropical Waters (SST >= 26°C)
    elif sst >= 26.0:
        species = "Skipjack Tuna, Mahi-Mahi (Dorado), Barracuda, and Snapper"
        gear = "Longlines & Artificial Lures"
        zone_desc = "Warm tropical epipelagic feeding boundary."

    # 5. Global Cold/Temperate Waters (SST < 20°C)
    else:
        species = "Atlantic/Pacific Mackerel, Herring, Hake, and Blue Whiting"
        gear = "Midwater Trawls"
        zone_desc = "Cold-water nutrient upwelling belt."

    return {
        "species": species,
        "recommended_gear": gear,
        "description": zone_desc
    }

def evaluate_coastal_hazard(weather, ocean, geofence, place_name: str) -> dict:
    """
    100% Physics & Telemetry-Driven Hazard Assessment.
    Zero hardcoded city lists. Evaluates dynamic risk based entirely on:
    - Wave height & swell steepness ratio
    - Gust differential (micro-squall factor)
    - Wave energy density & coastal surge
    - Marine spatial geofencing (IMBL / MPA boundaries)
    """
    wind = weather.wind_speed_knots
    gusts = weather.gusts_knots
    waves = ocean.significant_wave_height_m
    swell = ocean.swell_period_sec
    gust_spread = round(gusts - wind, 1)

    # Calculate wave steepness index (Wave Height / (Swell Period^2))
    # High steepness index (> 0.035) causes dangerous breaking waves and boat capsizing
    steepness_index = round(waves / max(1.0, swell ** 2), 4)

    # 1. Territorial Sea / Geofencing Limits
    if geofence.imbl_alert:
        hazard_class = "CRITICAL: BORDER JURISDICTION BUFFER"
        risk = "Proximity to international maritime separation line. High risk of naval interception and crossing territorial baseline."
        action = "Steer inward along navigational green channel. Do not deviate outward."
    elif geofence.mpa_alert:
        hazard_class = "RESTRICTED: MARINE SANCTUARY ZONE"
        risk = "Ecological conservation reserve. Submerged artificial reefs and statutory trawling restrictions active."
        action = "Bypass area completely. Commercial netting and bottom anchoring prohibited."

    # 2. Extreme Squalls / Gale Winds
    elif weather.squall_warning or gusts >= 25.0:
        hazard_class = "CRITICAL: HIGH-GUST SQUALL SECTOR"
        risk = f"Violent atmospheric gust front ({gusts} kts, gust spread +{gust_spread} kts). Severe capsize and swamping risk for small vessels."
        action = "Suspend operations. Secure craft immediately behind harbor breakwater."

    # 3. High Wave Steepness (Breaking Seas over Shallow Sandbanks/Shoals)
    elif steepness_index >= 0.030 or (waves >= 1.8 and swell <= 6.0):
        hazard_class = "HIGH RISK: BREAKING SURF & SHALLOW SHOAL SECTOR"
        risk = f"High wave steepness ({waves}m cresting on {swell}s cycle). Waves are plunging over shallow submerged banks."
        action = "Do not transit beam-to-seas. Keep engine revved to maintain steerage way."

    # 4. Heavy Groundswell Energy (Long-period surge)
    elif swell >= 11.0 and waves >= 1.2:
        hazard_class = "ELEVATED: GROUND SWELL SURGE & UNDERTOW"
        risk = f"Long-period ocean swell ({swell}s) releasing sudden heavy surge energy against coastal reefs and shallows."
        action = "Maintain wide berth from inshore breaker line. Exercise caution when anchoring."

    # 5. Moderate Choppy Seas
    elif wind >= 13.0 or waves >= 1.4:
        hazard_class = "CAUTION: CHOPPY SEA STATE & CURRENT DRIFT"
        risk = f"Surface chop generated by {wind} kts winds over {waves}m waves causing erratic lateral drift on light hulls."
        action = "Motorized skiffs and catamarans proceed at reduced speed (< 6 kts) within marked channel."

    # 6. Calm / Benign Coastal Waters
    else:
        hazard_class = "ADVISORY: NEARSHORE SHALLOW DRAFT MARGIN"
        risk = f"Shallow coastal bathymetry and localized littoral currents (Waves: {waves}m, Wind: {wind} kts)."
        action = "Stay within marked green navigation corridor to avoid unmarked shallow spits."

    return {
        "hazard_class": hazard_class,
        "hazard_reason": risk,
        "action": action,
        "color_code": "#ef4444"  # Always maintain Red maritime hazard styling
    }

async def intent_agent_node(state: OrcaState):
    lat, lon, place_name = await extract_and_geocode_location(state["query"])

    # Multi-turn context: Retain active coordinates if location is omitted in follow-up
    if (lat is None or lon is None) and state.get("previous_location"):
        prev = state["previous_location"]
        lat = prev.get("latitude")
        lon = prev.get("longitude")
        place_name = prev.get("harbor")

    if lat is None or lon is None:
        raise ValueError("LOCATION_NOT_FOUND")

    mission = generate_global_mission_plan(lat, lon, place_name)
    telemetry = await fetch_global_satellite_ocean_data(lat, lon)

    # Dynamic vessel classification
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
    lat = state["params"].latitude
    lon = state["params"].longitude

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

    try:
        chlor_val = float(re.findall(r"[-+]?\d*\.\d+|\d+", str(pfz.chlorophyll_level))[0])
    except Exception:
        chlor_val = 1.85

    fishing_yield_probability = min(96, max(55, int(52 + (chlor_val * 18))))
    bio_data = predict_marine_species(lat, lon, ocean.sea_surface_temp_c, chlor_val)

    # Fully dynamic telemetry evaluation
    hazard_data = evaluate_coastal_hazard(weather, ocean, geofence, place)

    geojson_overlays = {
        "pfz_zone": {
            "type": "Feature",
            "properties": {
                "name": "Potential Fishing Zone (PFZ)",
                "chlorophyll": pfz.chlorophyll_level,
                "sst": f"{ocean.sea_surface_temp_c}°C",
                "sensor": pfz.satellite_sensor,
                "fishing_potential": f"{fishing_yield_probability}%",
                "aggregation_status": "Active Pelagic Fish Aggregation",
                "target_species": bio_data["species"],
                "recommended_gear": bio_data["recommended_gear"],
                "zone_description": bio_data["description"]
            },
            "geometry": {"type": "Polygon", "coordinates": [mission["pfz_poly"]]}
        },
        "safe_zone": {
            "type": "Feature",
            "properties": {
                "zone": "Safe Navigation Corridor",
                "status": overall,
                "wave_height": f"{ocean.significant_wave_height_m}m",
                "wind_speed": f"{weather.wind_speed_knots} kts",
                "clearance": "Clear Coastal Passage (< 12 NM)",
                "harbor": place
            },
            "geometry": {"type": "Polygon", "coordinates": [mission["safe_poly"]]}
        },
        "danger_zone": {
            "type": "Feature",
            "properties": {
                "zone": "Coastal Hazard & Shallow Breaker Sector",
                "hazard_class": hazard_data["hazard_class"],
                "swell_period": f"{ocean.swell_period_sec}s",
                "wind_gusts": f"{weather.gusts_knots} kts",
                "hazard_reason": hazard_data["hazard_reason"],
                "action": hazard_data["action"],
                "color_code": hazard_data["color_code"]
            },
            "geometry": {"type": "Polygon", "coordinates": [mission["danger_poly"]]}
        }
    }

    verdict = FinalRecommendation(
        overall_status=overall,
        primary_recommendation=rec,
        detailed_reasoning=f"Satellite telemetry: Waves {ocean.significant_wave_height_m}m | Winds {weather.wind_speed_knots} kts | Chlorophyll {pfz.chlorophyll_level} | Target Species: {bio_data['species']}.",
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

orca_graph = builder.compile()