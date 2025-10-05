# backend/services/power.py
# NetCDF-free NASA POWER daily point fetch → pandas DataFrame

from __future__ import annotations

import requests
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Variables we need for generic PoE; POWER returns JSON so no netCDF/xarray required.
PARAMS = {
    "tmax": "T2M_MAX",   # °C
    "tmin": "T2M_MIN",   # °C
    "tavg": "T2M",       # °C
    "rh":   "RH2M",      # %
    "ws":   "WS10M",     # m/s (10 m wind)
    "pr":   "PRECTOTCORR"  # mm/day (corrected precip)
}

class PowerError(RuntimeError):
    pass

def _validate_latlon(lat: float, lon: float) -> None:
    if not (-90.0 <= float(lat) <= 90.0) or not (-180.0 <= float(lon) <= 180.0):
        raise ValueError(f"lat/lon out of range: {lat}, {lon}")

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "WillItRainOnMyParade/1.0"})
    return s

def _fetch_json(
    lat: float,
    lon: float,
    start_yyyymmdd: str,
    end_yyyymmdd: str,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    s = session or _session()
    q = {
        "parameters": ",".join(PARAMS.values()),
        "community": "RE",          # stable default
        "latitude": lat,
        "longitude": lon,
        "start": start_yyyymmdd,
        "end": end_yyyymmdd,
        "format": "JSON",
    }
    r = s.get(POWER_URL, params=q, timeout=45)
    if r.status_code >= 400:
        raise PowerError(f"POWER {r.status_code}: {r.text[:200]}")
    return r.json()

def fetch_power_point(
    lat: float,
    lon: float,
    start: str = "19810101",
    end: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """
    Return a daily time series for a point (lat, lon) from NASA POWER.

    Index: pandas.DatetimeIndex (daily)
    Columns:
      - tmaxC (°C), tminC (°C), tavgC (°C)
      - rh (%), ws_ms (m/s), pr_mm (mm/day)
    """
    _validate_latlon(lat, lon)
    if end is None:
        end = datetime.utcnow().strftime("%Y%m%d")

    js = _fetch_json(lat, lon, start, end, session=session)
    params = js.get("properties", {}).get("parameter", {})

    # Collect all available dates across requested parameters
    all_dates = set()
    for p in PARAMS.values():
        if p in params:
            all_dates.update(params[p].keys())
    dates = sorted(all_dates)

    rows = []
    for d in dates:
        rows.append(
            {
                "date": d,
                "tmaxC": params.get(PARAMS["tmax"], {}).get(d),
                "tminC": params.get(PARAMS["tmin"], {}).get(d),
                "tavgC": params.get(PARAMS["tavg"], {}).get(d),
                "rh": params.get(PARAMS["rh"], {}).get(d),
                "ws_ms": params.get(PARAMS["ws"], {}).get(d),
                "pr_mm": params.get(PARAMS["pr"], {}).get(d),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        # Return a correctly-shaped empty frame
        return pd.DataFrame(
            columns=["tmaxC", "tminC", "tavgC", "rh", "ws_ms", "pr_mm"],
            index=pd.DatetimeIndex([], name="date"),
        )

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    # Ensure numeric dtype
    for c in ["tmaxC", "tminC", "tavgC", "rh", "ws_ms", "pr_mm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df
