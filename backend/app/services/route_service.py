from typing import List, Dict, Any
from app.models.schemas import Waypoint

def compute_safe_waypoints(start_coords: List[float], pfz_coords: List[float], is_critical: bool) -> List[Waypoint]:
    """
    Computes intermediate navigation waypoints avoiding restricted coastal corridors.
    Matches Slide 5: Waypoint 1 -> Waypoint 2 -> Safe Zone / Destination.
    """
    lat1, lon1 = start_coords
    lat2, lon2 = pfz_coords

    if is_critical:
        return [
            Waypoint(
                sequence=1,
                name="Harbor Berth",
                coordinates=[lat1, lon1],
                nav_instruction="Hold position inside designated harbor basin. Unfavorable open-sea state."
            )
        ]

    # Midpoint offset to route vessels away from heavy nearshore breakers
    mid_lat = round((lat1 + lat2) / 2 + 0.02, 4)
    mid_lon = round((lon1 + lon2) / 2 + 0.03, 4)

    return [
        Waypoint(
            sequence=1,
            name="Departure Berth",
            coordinates=[lat1, lon1],
            nav_instruction=f"Depart harbor channel heading eastward."
        ),
        Waypoint(
            sequence=2,
            name="Safe Coastal Transit Corriodor",
            coordinates=[mid_lat, mid_lon],
            nav_instruction="Bypass shallow eco-sanctuary and offshore shoals."
        ),
        Waypoint(
            sequence=3,
            name="Target PFZ Operational Sector",
            coordinates=[lat2, lon2],
            nav_instruction="Arrive at satellite-derived chlorophyll feeding ground."
        )
    ]

def generate_zone_polygons(lat: float, lon: float, is_safe: bool) -> Dict[str, Any]:
    """
    Builds the Green (GO) and Red (NO-GO) spatial polygons seen on Slide 2 and 5.
    """
    return {
        "safe_zone": {
            "type": "Feature",
            "properties": {"zone": "Recommended Corridor", "status": "GO" if is_safe else "RESTRICTED"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - 0.05, lat - 0.05],
                    [lon + 0.15, lat - 0.05],
                    [lon + 0.15, lat + 0.12],
                    [lon - 0.05, lat + 0.12],
                    [lon - 0.05, lat - 0.05]
                ]]
            }
        },
        "danger_zone": {
            "type": "Feature",
            "properties": {"zone": "Severe Wave/High Squall Vector", "status": "NO-GO"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon + 0.18, lat + 0.08],
                    [lon + 0.35, lat + 0.08],
                    [lon + 0.35, lat + 0.25],
                    [lon + 0.18, lat + 0.25],
                    [lon + 0.18, lat + 0.08]
                ]]
            }
        }
    }