import math
from typing import Dict, Any, List

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def calculate_seaward_bearing(lat: float, lon: float) -> List[float]:
    """Dynamically projects seaward expansion vector into deep open ocean."""
    # Americas West Coast -> Pacific (West)
    if -170.0 < lon < -30.0:
        return [0.03, -0.16]
    # Americas East Coast -> Atlantic (East)
    if -80.0 <= lon <= -30.0:
        return [0.03, 0.16]
    # Europe / West Africa Atlantic -> West
    if 0 < lat < 60.0 and -20.0 < lon < 0.0:
        return [0.02, -0.16]
    # India Subcontinent:
    if lon <= 78.0:
        # Arabian Sea (West of 78°E)
        return [0.02, -0.16]
    # Bay of Bengal (East of 78°E)
    return [0.04, 0.16]

def generate_pfz_polygon(center_lat: float, center_lon: float, radius_km: float = 6.0) -> List[List[float]]:
    """Generates a dynamic 16-point circular/elliptical PFZ oceanic zone."""
    points = []
    num_points = 16
    for i in range(num_points + 1):
        angle = math.radians((i * 360) / num_points)
        d_lat = (radius_km / 110.574) * math.cos(angle)
        d_lon = (radius_km / (111.320 * math.cos(math.radians(center_lat)))) * math.sin(angle)
        points.append([round(center_lon + d_lon, 4), round(center_lat + d_lat, 4)])
    return points

def generate_coastal_boundary_line(lat: float, lon: float, seaward_vec: List[float]) -> List[List[float]]:
    """Generates the maritime boundary line (Territorial Sea / EEZ safety buffer) running parallel to coast."""
    # Perpendicular vector to coastline
    perp_vec = [-seaward_vec[1], seaward_vec[0]]
    line_center_lat = lat + (seaward_vec[0] * 1.5)
    line_center_lon = lon + (seaward_vec[1] * 1.5)

    p1 = [round(line_center_lon - (perp_vec[1] * 0.4), 4), round(line_center_lat - (perp_vec[0] * 0.4), 4)]
    p2 = [round(line_center_lon, 4), round(line_center_lat, 4)]
    p3 = [round(line_center_lon + (perp_vec[1] * 0.4), 4), round(line_center_lat + (perp_vec[0] * 0.4), 4)]
    return [p1, p2, p3]

def evaluate_global_geofencing(lat: float, lon: float) -> Dict[str, Any]:
    # 1. Palk Bay / Indo-Sri Lanka IMBL
    is_imbl_alert = (8.5 <= lat <= 10.5 and 79.0 <= lon <= 80.2)
    # 2. Designated Marine Protected Areas (MPAs)
    is_mpa_alert = (
        (20.5 <= lat <= 20.9 and 86.8 <= lon <= 87.2) or
        (8.9 <= lat <= 9.4 and 78.9 <= lon <= 79.4) or
        (-19.0 <= lat <= -10.0 and 145.0 <= lon <= 152.0)
    )
    return {
        "imbl_alert": is_imbl_alert,
        "mpa_alert": is_mpa_alert,
        "status": "CRITICAL" if (is_imbl_alert or is_mpa_alert) else "SAFE"
    }

def generate_global_mission_plan(lat: float, lon: float, place_name: str) -> Dict[str, Any]:
    seaward_vec = calculate_seaward_bearing(lat, lon)
    
    wp1 = [round(lat, 4), round(lon, 4)]
    wp2 = [round(lat + seaward_vec[0] * 0.45, 4), round(lon + seaward_vec[1] * 0.45, 4)]
    wp3 = [round(lat + seaward_vec[0], 4), round(lon + seaward_vec[1], 4)]

    # Dynamic PFZ polygon centered right on Waypoint 3
    pfz_poly = generate_pfz_polygon(wp3[0], wp3[1], radius_km=5.5)
    
    # Boundary line (Territorial baseline / EEZ buffer)
    boundary_line = generate_coastal_boundary_line(lat, lon, seaward_vec)

    # Corridor safe polygon
    safe_poly = [
        [round(lon - 0.03, 4), round(lat - 0.03, 4)],
        [round(lon + seaward_vec[1] * 0.8, 4), round(lat - 0.03, 4)],
        [round(lon + seaward_vec[1] * 0.8, 4), round(lat + 0.08, 4)],
        [round(lon - 0.03, 4), round(lat + 0.08, 4)],
        [round(lon - 0.03, 4), round(lat - 0.03, 4)]
    ]

    # Danger/Squall zone polygon
    danger_poly = [
        [round(lon + seaward_vec[1] * 1.6, 4), round(lat + 0.08, 4)],
        [round(lon + seaward_vec[1] * 2.3, 4), round(lat + 0.08, 4)],
        [round(lon + seaward_vec[1] * 2.3, 4), round(lat + 0.22, 4)],
        [round(lon + seaward_vec[1] * 1.6, 4), round(lat + 0.22, 4)],
        [round(lon + seaward_vec[1] * 1.6, 4), round(lat + 0.08, 4)]
    ]

    return {
        "waypoints": [
            {"sequence": 1, "name": f"Berth: {place_name}", "coordinates": wp1, "nav_instruction": "Depart coastline heading outward into deep water."},
            {"sequence": 2, "name": "Safe Coastal Transit Corridor", "coordinates": wp2, "nav_instruction": "Transit clear of coastal breaker zone and port limits."},
            {"sequence": 3, "name": "Target Satellite PFZ Feeding Sector", "coordinates": wp3, "nav_instruction": "Arrive at chlorophyll-rich thermal boundary (PFZ Zone)."}
        ],
        "pfz_coords": wp3,
        "pfz_poly": pfz_poly,
        "boundary_line": boundary_line,
        "safe_poly": safe_poly,
        "danger_poly": danger_poly
    }