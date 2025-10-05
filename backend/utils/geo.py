# backend/utils/geo.py
from __future__ import annotations

from typing import Any, Tuple, List, Union
from pydantic import BaseModel
from shapely.geometry import shape, Point, Polygon, LineString
from shapely.geometry.base import BaseGeometry

from schemas.common import GeoJSON  # your existing type

class BadGeometry(ValueError):
    """Raised when geometry is invalid; catch in routers and return 400."""
    pass

_VALID_GEO_TYPES = {
    "Point", "Polygon", "LineString",
    "MultiPoint", "MultiPolygon", "MultiLineString"
}

def _ensure_geojson_geometry(obj: Any) -> dict:
    """
    Accept a Pydantic model or dict and return a valid GeoJSON geometry dict.
    Raise BadGeometry with a helpful message if invalid.
    """
    if isinstance(obj, BaseModel):
        obj = obj.model_dump()

    if isinstance(obj, str):
        raise BadGeometry(
            "geometry_geojson must be a GeoJSON geometry object (dict), not a string. "
            "If you want 'city', geocode it to a Point first, e.g. "
            "{'type':'Point','coordinates':[lon, lat]}."
        )

    if not isinstance(obj, dict):
        raise BadGeometry("geometry_geojson must be a dict like GeoJSON geometry.")

    t = obj.get("type")
    if t not in _VALID_GEO_TYPES:
        raise BadGeometry(
            f"Unknown or unsupported GeoJSON geometry type: {t!r}. "
            f"Expected one of {sorted(_VALID_GEO_TYPES)}."
        )

    if t == "Point":
        coords = obj.get("coordinates")
        if (
            not isinstance(coords, (list, tuple)) or
            len(coords) != 2 or
            not all(isinstance(x, (int, float)) for x in coords)
        ):
            raise BadGeometry("Point.coordinates must be [lon, lat].")

    return obj

def _to_shapely(geojson_like: Union[dict, BaseModel, Any]) -> BaseGeometry:
    gj = _ensure_geojson_geometry(geojson_like)
    return shape(gj)

def centroid_lonlat(geo: GeoJSON) -> Tuple[float, float]:
    g = _to_shapely(geo)
    c = g.centroid
    return (float(c.x), float(c.y))

def bbox_lonlat(geo: GeoJSON) -> Tuple[float, float, float, float]:
    g = _to_shapely(geo)
    minx, miny, maxx, maxy = g.bounds
    return (float(minx), float(miny), float(maxx), float(maxy))

def grid_centroids_for_area(geo: GeoJSON, nx: int = 4, ny: int = 3) -> List[tuple[float, float]]:
    """Light nx×ny grid of centroids within polygon bbox (hackathon-fast)."""
    poly = _to_shapely(geo)
    if not isinstance(poly, Polygon):
        try:
            poly = Polygon(poly.exterior.coords)  # may fail for MultiPolygon
        except Exception:
            cx, cy = centroid_lonlat(geo)
            return [(cx, cy)]

    minx, miny, maxx, maxy = poly.bounds
    xs = [minx + (i + 0.5) * (maxx - minx) / nx for i in range(nx)]
    ys = [miny + (j + 0.5) * (maxy - miny) / ny for j in range(ny)]
    out: List[tuple[float, float]] = []
    for y in ys:
        for x in xs:
            p = Point(x, y)
            if poly.contains(p):
                out.append((float(x), float(y)))
    if not out:  # fallback: centroid only
        c = poly.centroid
        out = [(float(c.x), float(c.y))]
    return out

def sample_points_along_route(geo: GeoJSON, n: int = 10) -> List[tuple[float, float]]:
    line = _to_shapely(geo)
    if not isinstance(line, LineString):
        try:
            line = LineString(line)
        except Exception:
            c = line.centroid
            return [(float(c.x), float(c.y))]

    dist = line.length
    if dist == 0:
        c = line.centroid
        return [(float(c.x), float(c.y))]
    steps = [dist * i / max(1, (n - 1)) for i in range(n)]
    coords = [line.interpolate(d) for d in steps]
    return [(float(p.x), float(p.y)) for p in coords]
