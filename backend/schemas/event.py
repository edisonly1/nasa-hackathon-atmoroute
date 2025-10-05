from typing import Dict, List
from pydantic import BaseModel, Field
from .common import GeoJSON, UnitsMeta
from typing import Literal, Optional

class EventRequest(BaseModel):
    """
    Event scoring over an area (Polygon) or route (LineString).
    start_ts: ISO UTC time (e.g., 2025-07-15T18:00:00Z).
    duration_min: total minutes; step_min: bin size minutes.
    thresholds.evs_min: coverage threshold (default 70).
    """
    geometry_type: str = Field(examples=["area", "route"])
    geometry_geojson: GeoJSON = Field(
        ...,
        description="Polygon for 'area', LineString for 'route'.",
        examples=[{
            "type":"Polygon",
            "coordinates":[[
                [-84.34,34.02],[-84.33,34.02],[-84.33,34.03],[-84.34,34.03],[-84.34,34.02]
            ]]
        }]
    )
    start_ts: str = Field("2025-07-15T18:00:00Z", examples=["2025-07-15T18:00:00Z"])
    duration_min: int = Field(120, ge=1)
    step_min: int = Field(30, ge=1)
    thresholds: Dict[str, float] = Field(default_factory=lambda: {"evs_min": 70.0})

    mode: Optional[Literal["forecast","reanalysis","climo"]] = "forecast"
    hourly: Optional[bool] = True

class EVSComponent(BaseModel):
    t: int
    total: float
    rain: float
    wind: float
    heat: float
    humidity: float

class CellOut(BaseModel):
    cell_id: int
    lon: float
    lat: float
    evs: List[EVSComponent]

class Aggregate(BaseModel):
    t: int
    coverage_ge_70: float
    mean: float
    min: float

class EventResponse(BaseModel):
    event_id: str
    times: List[str]
    cells: List[CellOut]
    aggregates: List[Aggregate]
    meta: UnitsMeta
