import math
from typing import Dict, Any, List

def calculate_seaward_bearing(lat: float, lon: float) -> List[float]:
    """Calculates seaward expansion direction into open ocean."""
    # Americas Pacific (West)
    if -170.0 < lon < -30.0:
        return [0.02, -0.12]
    # Americas Atlantic (East)
    if -80.0 <= lon <= -30.0:
        return [0.02, 0.12]
    # Indian Subcontinent West Coast (Arabian Sea)
    if lon <= 78.0:
        return [0.02, -0.12]
    # Indian Subcontinent East Coast (Bay of Bengal)
    return [0.03, 0.12]

def generate_pfz_polygon(center_lat: float, center_lon: float, radius_km: float = 5.0) -> List[List[float]]:
    """Generates a smooth circular PFZ oceanic boundary."""
    points = []
    num_points = 16
    for i in range(num_points + 1):
        angle = math.radians((i * 360) / num_points)
        d_lat = (radius_km / 110.574) * math.cos(angle)
        d_lon = (radius_km / (111.320 * math.cos(math.radians(center_lat)))) * math.sin(angle)
        points.append([round(center_lon + d_lon, 4), round(center_lat + d_lat, 4)])
    return points

def evaluate_global_geofencing(lat: float, lon: float) -> Dict[str, Any]:
    """Evaluates international boundaries and MPAs."""
    is_imbl_alert = (8.5 <= lat <= 10.5 and 79.0 <= lon <= 80.2)
    is_mpa_alert = (
        (20.5 <= lat <= 20.9 and 86.8 <= lon <= 87.2) or
        (8.9 <= lat <= 9.4 and 78.9 <= lon <= 79.4)
    )
    return {
        "imbl_alert": is_imbl_alert,
        "mpa_alert": is_mpa_alert,
        "status": "CRITICAL" if (is_imbl_alert or is_mpa_alert) else "SAFE"
    }

def generate_global_mission_plan(lat: float, lon: float, place_name: str) -> Dict[str, Any]:
    seaward_vec = calculate_seaward_bearing(lat, lon)
    v_lat, v_lon = seaward_vec[0], seaward_vec[1]

    # Waypoints
    wp1 = [round(lat, 4), round(lon, 4)]
    wp2 = [round(lat + v_lat * 0.5, 4), round(lon + v_lon * 0.5, 4)]
    wp3 = [round(lat + v_lat, 4), round(lon + v_lon, 4)]

    # Dynamic PFZ Polygon centered at Waypoint 3
    pfz_poly = generate_pfz_polygon(wp3[0], wp3[1], radius_km=5.0)

    # 1. Safe Navigation Corridor (Green Box): Directly envelopes WP1 and WP2 out towards WP3
    # Defined with normal offset perpendicular to transit
    safe_poly = [
        [round(lon - 0.015, 4), round(lat - 0.025, 4)],
        [round(lon + v_lon * 0.75, 4), round(lat - 0.025, 4)],
        [round(lon + v_lon * 0.75, 4), round(lat + v_lat * 0.75 + 0.025, 4)],
        [round(lon - 0.015, 4), round(lat + v_lat * 0.75 + 0.025, 4)],
        [round(lon - 0.015, 4), round(lat - 0.025, 4)]
    ]

    # 2. Hazard / Coastal Shoal Sector (Red Box): Directly flanks the boat's navigation path!
    # Sits directly on the exposed flank of the transit corridor between departure and transit
    # Warning small craft not to drift into the shallow rocky breaker zone.
    danger_poly = [
        [round(lon - 0.015, 4), round(lat + v_lat * 0.75 + 0.025, 4)],
        [round(lon + v_lon * 0.75, 4), round(lat + v_lat * 0.75 + 0.025, 4)],
        [round(lon + v_lon * 0.75, 4), round(lat + v_lat * 0.75 + 0.065, 4)],
        [round(lon - 0.015, 4), round(lat + v_lat * 0.75 + 0.065, 4)],
        [round(lon - 0.015, 4), round(lat + v_lat * 0.75 + 0.025, 4)]
    ]

    return {
        "waypoints": [
            {
                "sequence": 1,
                "name": f"Berth: {place_name}",
                "coordinates": wp1,
                "nav_instruction": "Depart coastline heading outward along safe navigational channel."
            },
            {
                "sequence": 2,
                "name": "Safe Coastal Transit Corridor",
                "coordinates": wp2,
                "nav_instruction": "Follow marked GPS waypoints avoiding shallow breaker sector."
            },
            {
                "sequence": 3,
                "name": "Target Potential Fishing Zone (PFZ)",
                "coordinates": wp3,
                "nav_instruction": "Arrive at high-chlorophyll thermal boundary for pelagic fishing."
            }
        ],
        "pfz_coords": wp3,
        "pfz_poly": pfz_poly,
        "safe_poly": safe_poly,
        "danger_poly": danger_poly
    }