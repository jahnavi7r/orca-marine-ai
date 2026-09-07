from app.models.schemas import GISReport
from app.services.gis_service import evaluate_geofencing_and_pfz

def run_gis_agent(lat: float, lon: float) -> GISReport:
    data = evaluate_geofencing_and_pfz(lat, lon)
    
    if data["in_mpa"] or data["near_imbl"]:
        status = "CRITICAL"
    else:
        status = "SAFE"
        
    evidence = (
        f"MPA Geofence: {'VIOLATION' if data['in_mpa'] else 'CLEAR'}. "
        f"IMBL Proximity: {'WARNING' if data['near_imbl'] else 'CLEAR'}. "
        f"Target PFZ detected: {data['pfz_coords']}. [Source: {data['source']}]"
    )
    
    return GISReport(
        in_marine_protected_area=data["in_mpa"],
        near_international_boundary=data["near_imbl"],
        pfz_available_nearby=data["pfz_available"],
        pfz_coordinates=data["pfz_coords"],
        status=status,
        evidence=evidence
    )