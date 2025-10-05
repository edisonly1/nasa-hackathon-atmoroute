# backend/routers/meta.py
import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List

class MetaResponse(BaseModel):
    name: str
    version: str
    datasets: List[str]
    units: Dict[str, str]
    cadence: str
    sources: List[str]
    notes: str

router = APIRouter(prefix="/api", tags=["meta"])

NAME = "Will it Rain on My Parade?"
VERSION = "0.9.0"

UNITS = {
    "precip_mm_day": "mm/day",
    "precip_mm_hr": "mm/hr",
    "wind_mph": "mph",
    "gust_mph": "mph",
    "tmaxF": "°F",
    "tminF": "°F",
    "rh_pct": "%",
    "heatindex_F": "°F",
}

@router.get("/meta", response_model=MetaResponse)
def get_meta():
    datasets = [
        "NASA POWER (daily point): T2M_MAX, T2M_MIN, T2M, RH2M, WS10M",
    ]
    sources = [
        "POWER API (JSON/CSV); no Earthdata login required",
        "GES DISC Data Rods (JSON/CSV)",
    ]
    notes = (
        "Point-based PoE uses climatology of same day-of-year ± window across 1981–present. "
        "Event Corridor (≤7 days) uses daily POWER/Data Rods at route/area samples; EVS computed from precip/wind/HI/RH. "
        "No netCDF/xarray at runtime."
    )
    cadence = "Daily (POWER/Data Rods); PoE is climatology; Corridor uses per-day bins"
    return MetaResponse(
        name=NAME,
        version=VERSION,
        datasets=datasets,
        units=UNITS,
        cadence=cadence,
        sources=sources,
        notes=notes,
    )
