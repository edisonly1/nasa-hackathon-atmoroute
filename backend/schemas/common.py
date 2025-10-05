from typing import Any, Dict, Literal, Optional, Union, List
from pydantic import BaseModel, Field, field_validator

# What the API accepts in requests
GeometryType = Literal["pin", "city", "area", "route"]

class Thresholds(BaseModel):
    """Thresholds used by PoE"""
    precip_mmhr: float = 1.0
    wind_mph: float = 25.0
    heatindex_F: float = 95.0
    rh_pct: float = 80.0

class UnitsMeta(BaseModel):
    units: Dict[str, str]
    sources: list[str] = Field(default_factory=list)
    notes: Optional[str] = None

# Minimal GeoJSON geometry with helpful validation + examples for Swagger
class GeoJSON(BaseModel):
    """Loose GeoJSON geometry (Point | Polygon | LineString). Coordinates are [lon, lat] in WGS84."""
    type: Literal["Point", "Polygon", "LineString"] = Field(
        description="GeoJSON geometry type."
    )
    coordinates: Any = Field(
        description="Coordinates array. Point: [lon,lat]. "
                    "Polygon: [[ [lon,lat],... ]]. LineString: [ [lon,lat], ... ]."
    )

    @field_validator("coordinates")
    @classmethod
    def _non_string_coords(cls, v):
        if isinstance(v, str):
            # Prevent "string" placeholder from Swagger
            raise ValueError("coordinates must be an array, not a string. "
                             "Example Point: [ -84.334, 34.023 ]")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"type": "Point", "coordinates": [-84.334, 34.023]},
                {"type": "Polygon", "coordinates": [[
                    [-84.34, 34.02],
                    [-84.33, 34.02],
                    [-84.33, 34.03],
                    [-84.34, 34.03],
                    [-84.34, 34.02]
                ]]},
                {"type": "LineString", "coordinates": [
                    [-84.34, 34.02], [-84.33, 34.025], [-84.32, 34.03]
                ]}
            ]
        }
    }
