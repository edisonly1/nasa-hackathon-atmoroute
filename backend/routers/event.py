# backend/routers/event.py
from __future__ import annotations

import os
from typing import Dict, List
from uuid import uuid4
from datetime import datetime, timedelta, timezone, date as Date

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from schemas.event import EventRequest, EventResponse, CellOut, EVSComponent, Aggregate
from schemas.common import UnitsMeta
from utils.timebins import enumerate_bins
from services.sampling import sample_points
from services.poe_expect import expected_evs_for_day

router = APIRouter(tags=["event"])
EVENT_CACHE: Dict[str, dict] = {}

def _unique_dates(times: List[datetime]) -> List[Date]:
    # Sort and dedupe to one entry per calendar day (UTC)
    dates = sorted({t.astimezone(timezone.utc).date() for t in times})
    return list(dates)

@router.post("/event", response_model=EventResponse)
def event(req: EventRequest):
    if req.geometry_type not in {"area", "route"}:
        raise HTTPException(status_code=400, detail="geometry_type must be 'area' or 'route'")

    # Build time bins from request
    try:
        times_dt = enumerate_bins(req.start_ts, req.duration_min, req.step_min)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid time parameters: {e}")
    if not times_dt:
        raise HTTPException(status_code=400, detail="No time bins. Check duration_min/step_min.")

    # POWER is daily; coerce to daily unique dates
    dates = _unique_dates(times_dt)
    times_iso = [datetime(d.year, d.month, d.day, tzinfo=timezone.utc).isoformat() for d in dates]
    coerced = any(req.step_min < 1440 for _ in [0])  # True if user asked for sub-daily
    window_days = int(os.getenv("CLIMO_WINDOW_DAYS", "14"))

    # Sample points along route or within area
    try:
        pts = sample_points(req.geometry_type, req.geometry_geojson)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid geometry: {e}")
    if not pts:
        raise HTTPException(status_code=400, detail="No sample points found for geometry.")

    # Compute EVS list per cell and date using POWER climatology (same engine as PoE)
    cells: List[CellOut] = []
    for cid, (lon, lat) in enumerate(pts):
        evs_list: List[EVSComponent] = []
        for ti, d in enumerate(dates):
            res = expected_evs_for_day(lat, lon, d, window_days=window_days)
            evs_list.append(EVSComponent(
                t=ti,
                total=res.total,
                rain=res.subs["rain"],
                wind=res.subs["wind"],
                heat=res.subs["heat"],
                humidity=res.subs["humidity"],
            ))
        cells.append(CellOut(cell_id=cid, lon=lon, lat=lat, evs=evs_list))

    # Aggregates per daily bin
    evs_min = (req.thresholds or {}).get("evs_min", 70)
    aggregates: List[Aggregate] = []
    means_for_best = []
    for ti in range(len(dates)):
        vals = [c.evs[ti].total for c in cells if ti < len(c.evs)]
        if not vals:
            aggregates.append(Aggregate(t=ti, coverage_ge_70=0.0, mean=0.0, min=0.0))
            means_for_best.append(0.0)
            continue
        n = len(vals)
        coverage = sum(1 for v in vals if v >= evs_min) / n
        mean = sum(vals) / n
        minv = min(vals)
        aggregates.append(Aggregate(t=ti, coverage_ge_70=coverage, mean=mean, min=minv))
        means_for_best.append(mean)
    best_idx = int(np.argmax(means_for_best)) if means_for_best else 0

    # Provenance / notes
    units_map = {
        "evs": "0–100",
        "rain_mm_day": "mm/day",
        "wind_mph": "mph",
        "heatindex_F": "°F",
        "rh_pct": "%"
    }
    sources = ["NASA POWER daily point climatology (1981–present)"]
    notes = (
        "Event Corridor computed from climatological probabilities around the same day-of-year. "
        "We convert the probability of 'bad' conditions into expected subscores, then combine to EVS. "
        f"Window ±{window_days} days. "
        + ("Step coerced to daily for POWER-based corridor. " if coerced else "")
        + f"Best date: index {best_idx} at {times_iso[best_idx]}."
    )

    event_id = uuid4().hex[:8]
    resp = EventResponse(
        event_id=event_id,
        times=times_iso,
        cells=cells,
        aggregates=aggregates,
        meta=UnitsMeta(
            units=units_map,
            sources=sources,
            notes=notes,
            extra={
                "mode": "event_corridor",  # label for UI
                "best_time_idx": best_idx,
                "best_time_iso": times_iso[best_idx],
                "climo_window_days": window_days,
                "coerced_to_daily": coerced,
            },
        ),
    )
    # Cache for /export
    from routers.export import EVENT_CACHE as EXPORT_CACHE  # if you keep /export grabbing this dict
    try:
        EXPORT_CACHE[event_id] = resp.model_dump()
    except Exception:
        pass
    return resp
