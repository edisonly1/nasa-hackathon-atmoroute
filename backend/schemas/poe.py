# backend/schemas/poe.py
from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field

# Supported variables for the generic PoE endpoint.
VarName = Literal[
    "precip_mm_day",   # daily precip (mm/day)
    "precip_mm_hr",    # derived: mm/hr ~ day/24
    "wind_mph",        # mean 10 m wind (mph)
    "gust_mph",        # derived proxy: 1.6 * wind_mph
    "rh_pct",          # relative humidity (%)
    "tmaxF",           # daily max temperature (°F)
    "tminF",           # daily min temperature (°F)
    "heatindex_F",     # derived from tmaxF + rh_pct
]

OpName = Literal["ge", "le"]

class Metric(BaseModel):
    """A single PoE query: P(var op threshold)."""
    var: VarName = Field(examples=["precip_mm_day"])
    threshold: float = Field(examples=[12.7])
    op: OpName = Field("ge", description="'ge' (>=) or 'le' (<=)")

class PoEReq(BaseModel):
    """
    Probability-of-Exceedance request (point-based, climatology).
    - `date`: ISO timestamp or 'YYYY-MM-DD' (used for same DOY ± window pooling)
    - `window_days`: total window length in days (e.g., 14 => ±7)
    - `metrics`: list of per-parameter exceedance tests
    """
    lat: float = Field(examples=[34.05])
    lon: float = Field(examples=[-118.25])
    date: str = Field("2025-07-04", examples=["2025-07-04", "2025-07-04T12:00:00Z"])
    window_days: int = Field(14, ge=1, le=60)
    metrics: List[Metric] = Field(
        default_factory=list,
        examples=[[
            {"var": "precip_mm_day", "threshold": 12.7, "op": "ge"},
            {"var": "wind_mph", "threshold": 25, "op": "ge"},
            {"var": "rh_pct", "threshold": 80, "op": "ge"},
            {"var": "heatindex_F", "threshold": 95, "op": "ge"}
        ]]
    )
