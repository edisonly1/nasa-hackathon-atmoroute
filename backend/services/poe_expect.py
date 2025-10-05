# backend/services/poe_expect.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
import os
import numpy as np
import pandas as pd

# Your existing POWER point fetcher should return a daily DataFrame indexed by ISO date ("YYYY-MM-DD"),
# with columns: tmaxC (°C), rh (%), ws_ms (m/s), pr_mm (mm/day).
from services.power import fetch_power_point
# If you already have a DOY pooling util, you can swap _pool_same_doy for it.

def _CtoF(c: float) -> float:
    return c * 9.0/5.0 + 32.0

def _heat_index_F(Tf: float, RH: float) -> float:
    # Rothfusz regression (NWS)
    if np.isnan(Tf) or np.isnan(RH):
        return np.nan
    if Tf < 80:  # °F
        return Tf
    c1=-42.379; c2=2.04901523; c3=10.14333127
    c4=-0.22475541; c5=-0.00683783; c6=-0.05481717
    c7=0.00122874; c8=0.00085282; c9=-0.00000199
    HI=(c1 + c2*Tf + c3*RH + c4*Tf*RH + c5*Tf*Tf + c6*RH*RH +
        c7*Tf*Tf*RH + c8*Tf*RH*RH + c9*Tf*Tf*RH*RH)
    if RH < 13 and 80 <= Tf <= 112:
        HI -= ((13 - RH)/4) * np.sqrt((17 - abs(Tf-95))/17)
    if RH > 85 and 80 <= Tf <= 87:
        HI += 0.02 * (RH - 85) * (87 - Tf)
    return float(HI)

def _poe_ge(series: pd.Series, thr: float) -> float:
    series = pd.to_numeric(series, errors="coerce").dropna()
    if series.empty: return np.nan
    return float((series >= thr).mean())

def _pool_same_doy(df_daily: pd.DataFrame, target_day: date, window_days: int = 14) -> pd.DataFrame:
    """Pool all historical days within ±window_days around the same DOY across all years."""
    if df_daily.empty:
        return df_daily
    # Expect df_daily.index as strings "YYYY-MM-DD"
    idx = pd.to_datetime(df_daily.index, errors="coerce").date
    pool = []
    tgt_doy = target_day.timetuple().tm_yday
    for i, d in enumerate(idx):
        doy = d.timetuple().tm_yday
        # handle wrap around new year by comparing minimal circular distance
        dist = min((doy - tgt_doy) % 366, (tgt_doy - doy) % 366)
        if dist <= window_days:
            pool.append(df_daily.iloc[i])
    if not pool:
        return pd.DataFrame(columns=df_daily.columns)
    return pd.DataFrame(pool)

@dataclass
class ExpectedEVS:
    total: float
    subs: dict  # keys: rain, wind, heat, humidity

def expected_evs_for_day(
    lat: float,
    lon: float,
    day: date,
    window_days: int = None,
    thresholds: dict | None = None,
    weights: dict | None = None
) -> ExpectedEVS:
    """
    POWER climatology → expected EVS for a calendar day.
    We compute PoE of 'bad' conditions and map to expected subscores = 100*(1 - PoE_bad),
    then combine with EVS weights.
    """
    # Defaults (judge-friendly)
    window_days = window_days or int(os.getenv("CLIMO_WINDOW_DAYS", "14"))
    thr = thresholds or {
        "rain_mm_day": 10.0,   # heavy rain day
        "wind_mph":    20.0,   # breezy/gusty
        "hi_F":        95.0,   # uncomfortably hot
        "rh_pct":      80.0,   # muggy
    }
    w = weights or {
        "rain": 0.35,
        "wind": 0.25,
        "heat": 0.25,
        "humidity": 0.15,
    }

    df = fetch_power_point(lat, lon)
    if df is None or df.empty:
        return ExpectedEVS(total=50.0, subs={"rain":50,"wind":50,"heat":50,"humidity":50})

    pool = _pool_same_doy(df, day, window_days=window_days)
    if pool.empty:
        return ExpectedEVS(total=50.0, subs={"rain":50,"wind":50,"heat":50,"humidity":50})

    # Compute PoE of 'bad' conditions
    poe_rain = _poe_ge(pool["pr_mm"].fillna(0.0), thr["rain_mm_day"])
    poe_wind = _poe_ge((pool["ws_ms"]*2.23694).fillna(0.0), thr["wind_mph"])

    # Heat index from Tmax + RH
    Tf = _CtoF(pool["tmaxC"].astype(float))
    RH = pool["rh"].astype(float)
    hi_vals = pd.Series([_heat_index_F(t, r) for t, r in zip(Tf, RH)], index=pool.index)
    poe_heat = _poe_ge(hi_vals, thr["hi_F"])
    poe_rh   = _poe_ge(RH, thr["rh_pct"])

    # Expected subscores
    subs = {
        "rain":     float(100 * (1 - poe_rain)) if not np.isnan(poe_rain) else 50.0,
        "wind":     float(100 * (1 - poe_wind)) if not np.isnan(poe_wind) else 50.0,
        "heat":     float(100 * (1 - poe_heat)) if not np.isnan(poe_heat) else 50.0,
        "humidity": float(100 * (1 - poe_rh))   if not np.isnan(poe_rh)   else 50.0,
    }
    # Weighted EVS total
    total = float(
        subs["rain"] * w["rain"] +
        subs["wind"] * w["wind"] +
        subs["heat"] * w["heat"] +
        subs["humidity"] * w["humidity"]
    )
    return ExpectedEVS(total=total, subs=subs)
