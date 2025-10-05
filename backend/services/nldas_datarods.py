# backend/services/nldas_datarods.py
from __future__ import annotations
import io, os, requests, pandas as pd
from datetime import datetime, timezone

UA = {"User-Agent": "ParadeForecast/1.0 (+github)"}

NLDAS_BASE = os.getenv("NLDAS_BASE", "").strip()  # e.g. https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi
EDL_TOKEN  = os.getenv("EDL_TOKEN", "").strip()

class NLDASConfigError(RuntimeError): pass

def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _read_csv(text: str, time_cols=("DateTime","time","Time","datetime")) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text))
    tcol = next((c for c in time_cols if c in df.columns), df.columns[0])
    vcol = next((c for c in df.columns if c != tcol), df.columns[-1])
    df[tcol] = pd.to_datetime(df[tcol], utc=True, errors="coerce")
    df = df.dropna(subset=[tcol]).set_index(tcol).sort_index()
    return df.rename(columns={vcol: "value"})

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(UA)
    if EDL_TOKEN:
        s.headers["Authorization"] = f"Bearer {EDL_TOKEN}"
    return s

# Map our needs → NLDAS FORA hourly “Data Rods” variable ids
VMAP = {
    "t2m": "NLDAS:NLDAS_FORA0125_H.002:AirT_t2m",   # K
    "u10": "NLDAS:NLDAS_FORA0125_H.002:Wind_E",     # m/s
    "v10": "NLDAS:NLDAS_FORA0125_H.002:Wind_N",     # m/s
    "rh":  "NLDAS:NLDAS_FORA0125_H.002:RH_2m",      # %
    "pr":  "NLDAS:NLDAS_FORA0125_H.002:TotalPrecip" # mm/hr
}

# inside backend/services/nldas_datarods.py

def _series(var_id: str, lat: float, lon: float, start: datetime, end: datetime) -> pd.DataFrame:
    if not NLDAS_BASE:
        raise NLDASConfigError(
            "NLDAS_BASE not configured. Example: https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"
        )
    params = {
        "variable": var_id,
        "startDate": _iso(start),
        "endDate": _iso(end),
        "location": f"GEOM:POINT({lon:.5f},{lat:.5f})",  # <-- key change
        "type": "csv"
    }
    s = _session()
    r = s.get(NLDAS_BASE, params=params, timeout=60)
    r.raise_for_status()
    try:
        return _read_csv(r.text)
    except Exception:
        df = pd.read_table(io.StringIO(r.text), delim_whitespace=True, names=["DateTime","value"], comment="#")
        df["DateTime"] = pd.to_datetime(df["DateTime"], utc=True, errors="coerce")
        df = df.dropna(subset=["DateTime"]).set_index("DateTime").sort_index()
        return df
