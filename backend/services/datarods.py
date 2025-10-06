# backend/services/datarods.py
# Daily precipitation series at a point.
# Uses NASA Data Rods if configured; otherwise falls back to POWER 'pr_mm'.

from __future__ import annotations

import os
import pandas as pd
from datetime import datetime
from typing import Optional
from services.power import fetch_power_point

# If wire a Data Rods endpoint, set DATARODS_MODE=datarods and implement _fetch_datarods_json.
DATARODS_MODE = os.getenv("DATARODS_MODE", "power").lower()

def _as_daily_df(dates, values, col="pr_mm") -> pd.DataFrame:
    df = pd.DataFrame({"date": pd.to_datetime(dates), col: values})
    return df.set_index("date").sort_index()

def datarods_precip_series(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    session=None,
) -> pd.DataFrame:
    """
    Return a DataFrame with a daily 'pr_mm' column between [start_date, end_date] inclusive.
    Currently defaults to POWER precipitation; switch DATARODS_MODE=datarods when you wire the API.
    """
    # POWER fallback
    dfp = fetch_power_point(lat, lon, start=start_date.replace("-", ""), end=end_date.replace("-", ""))
    if dfp.empty:
        return _as_daily_df([], [], "pr_mm")
    # Clip to requested window
    sub = dfp.loc[(dfp.index >= start_date) & (dfp.index <= end_date)]
    return sub[["pr_mm"]].copy()