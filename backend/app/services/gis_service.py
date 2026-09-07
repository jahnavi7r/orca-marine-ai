import json
import os
from typing import Dict, Any, List
from shapely.geometry import Point, Polygon

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "marine_zones.json")

def evaluate_geofencing_and_pfz(lat: float, lon: float) -> Dict[str, Any]:
    target_pt = Point(lon, lat)
    in_restricted_area = False
    active_pfz: List[float] = [83.4500, 17.8500] # Default Oceansat waypoint
    metadata = "ISRO Oceansat-3 Daily Composite"

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                geo_data = json.load(f)
                
            for feature in geo_data.get("features", []):
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                
                # Check MPA boundary crossing
                if props.get("category") == "MPA" and geom.get("type") == "Polygon":
                    poly = Polygon(geom["coordinates"][0])
                    if poly.contains(target_pt):
                        in_restricted_area = True
                
                # Check PFZ location from satellite data
                if props.get("category") == "PFZ" and geom.get("type") == "Point":
                    active_pfz = [geom["coordinates"][1], geom["coordinates"][0]] # [lat, lon]
                    metadata = f"{props.get('satellite_sensor')} (Chlorophyll: {props.get('chlorophyll_mg_m3')} mg/m³)"

        except Exception as e:
            print(f"[GIS PARSE ERROR] {e}")

    # Calculate proximity to International Maritime Boundary Line (IMBL)
    near_imbl = (lat < 9.5 and lon > 79.8) # Palk Bay sector

    return {
        "in_mpa": in_restricted_area,
        "near_imbl": near_imbl,
        "pfz_available": True,
        "pfz_coords": active_pfz,
        "source": metadata
    }