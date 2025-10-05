from typing import List, Tuple
from schemas.common import GeoJSON

from utils.geo import grid_centroids_for_area, sample_points_along_route

def sample_points(geometry_type: str, geom: GeoJSON) -> List[Tuple[float, float]]:
    if geometry_type == "area":
        return grid_centroids_for_area(geom, nx=4, ny=3)
    if geometry_type == "route":
        return sample_points_along_route(geom, n=12)
    # Fallback (pin/city)
    from utils.geo import centroid_lonlat
    return [centroid_lonlat(geom)]
