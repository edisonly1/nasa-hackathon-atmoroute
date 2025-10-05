# backend/routers/poe.py
# Point-based Probability of Exceedance (PoE) for user-selected parameters.
# NetCDF-free: NASA POWER + Data Rods (JSON/CSV).

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List

from schemas.poe import PoEReq, Metric  
from services.power import fetch_power_point
from services.datarods import datarods_precip_series
from services.poe_generic import compute_generic_poe

router = APIRouter(tags=["poe"])

@router.post("/poe")
def poe(req: PoEReq):
    if not req.metrics:
        raise HTTPException(status_code=400, detail="metrics[] cannot be empty")

    # 1) Fetch multi-decadal daily series at the point (1981→present)
    df_met = fetch_power_point(req.lat, req.lon, start="19810101")
    if df_met.empty:
        raise HTTPException(status_code=502, detail="POWER returned no data for this point")

    # 2) Precip from Data Rods (if it fails, we’ll rely on POWER 'pr_mm' if present)
    try:
        df_pr = datarods_precip_series(
            req.lat, req.lon, start_date="1981-01-01",
            end_date=datetime.utcnow().strftime("%Y-%m-%d")
        )
        df = df_met.join(df_pr, how="left")  # adds/overrides 'pr_mm'
    except Exception:
        # Graceful fallback: continue with POWER-only columns
        df = df_met

    # 3) Compute PoE per metric from same-DOY±window distribution
    center = datetime.fromisoformat(req.date.replace("Z", "+00:00"))
    results, samples = compute_generic_poe(
        df=df,
        center=center,
        window_days=req.window_days,
        metrics=[m.model_dump() for m in req.metrics],
    )

    return {
        "results": results,
        "meta": {
            "mode": "climatology",
            "window_days": req.window_days,
            "samples": samples,
            "sources": [
                "NASA POWER daily point (T2M_MAX,T2M_MIN,T2M,RH2M,WS10M)",
                "Data Rods Hydrology (daily precip at point)"
            ],
            "provenance": {
                "lat": req.lat, "lon": req.lon,
                "date": req.date
            }
        }
    }
