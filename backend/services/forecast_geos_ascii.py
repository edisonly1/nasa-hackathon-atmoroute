# backend/services/forecast_geos_ascii.py
# Hourly GEOS-FP point extractor via OPeNDAP .ascii (no local netCDF)

from __future__ import annotations
import os, re, requests, numpy as np, pandas as pd
from datetime import datetime, timezone
from typing import List, Optional

# Try these endpoints in order; add a GES DISC granule URL if you have EDL creds.
FCAST_URLS = [
    # NCCS collection (no auth; may be down sometimes)
    "https://opendap.nccs.nasa.gov/dods/GEOS-5/fp/0.25_deg/assim/inst1_2d_asm_Nx",
    # Example GES DISC per-granule (requires Earthdata Login cookie; replace with a real granule if desired):
    # "https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/GEOS-FP/inst1_2d_asm_Nx/2025/20251004/GEOS.fp.inst1_2d_asm_Nx.20251004_0000.V01.nc4"
]

# If you want to hard-set a single URL, set BASE_URL; otherwise we probe FCAST_URLS.
BASE_URL: Optional[str] = None

UA = {"User-Agent": "ParadeForecast/1.0 (+github)"}
EDL_USER = os.getenv("EARTHDATA_USERNAME")
EDL_PASS = os.getenv("EARTHDATA_PASSWORD")

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(UA)
    # Only used if you add a gesdisc URL that needs auth
    if EDL_USER and EDL_PASS:
        s.auth = (EDL_USER, EDL_PASS)
    return s

def _nums(txt: str) -> np.ndarray:
    """Extract all numeric values from Hyrax .ascii response in order."""
    arr = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", txt)
    if not arr:
        return np.array([], dtype=float)
    return np.array([float(x) for x in arr], dtype=float)

def _pick_base_url(sess: requests.Session) -> Optional[str]:
    """Return first working OPeNDAP URL by probing '?time'."""
    for u in FCAST_URLS:
        try:
            r = sess.get(u + ".ascii?time", timeout=20)
            if r.status_code < 400 and ("time" in r.text or re.search(r"\btime\b", r.text)):
                return u
        except Exception:
            continue
    return None

def _parse_units(units: str) -> tuple[str, datetime]:
    m = re.search(r"(\w+)\s+since\s+(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})", units)
    if not m:
        return "hours", datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    scale = m.group(1).lower()
    origin = datetime.fromisoformat(m.group(2).replace(" ", "T")).replace(tzinfo=timezone.utc)
    return scale, origin

def _to_units(dt: datetime, scale: str, origin: datetime) -> float:
    dt = dt.astimezone(timezone.utc)
    sec = (dt - origin).total_seconds()
    if scale.startswith("hour"):   return sec / 3600.0
    if scale.startswith("minute"): return sec / 60.0
    if scale.startswith("second"): return sec
    if scale.startswith("day"):    return sec / 86400.0
    return sec / 3600.0

def hourly_point(lat: float, lon: float, start: datetime, end: datetime) -> pd.DataFrame:
    """
    Return hourly dataframe with columns:
      Tf (°F), RH (%), wind_mph, precip_mmhr
    Index is UTC datetime.
    """
    sess = _session()
    base = BASE_URL or _pick_base_url(sess)
    if not base:
        raise RuntimeError("No working GEOS-FP OPeNDAP endpoint reachable (NCCS/GES DISC).")

    lon360 = (lon + 360.0) % 360.0

    # --- coords & time units ---
    rt = sess.get(base + ".ascii?time", timeout=45); rt.raise_for_status()
    rl = sess.get(base + ".ascii?lat",  timeout=45); rl.raise_for_status()
    rL = sess.get(base + ".ascii?lon",  timeout=45); rL.raise_for_status()

    tvals_all = _nums(rt.text)
    lats = _nums(rl.text)
    lons = _nums(rL.text)

    m = re.search(r'time:units\s*=\s*"([^"]+)"', rt.text)
    tunits = m.group(1) if m else "hours since 2000-01-01 00:00:00"
    scale, origin = _parse_units(tunits)

    # --- time indices for the requested window ---
    a = _to_units(start, scale, origin)
    b = _to_units(end,   scale, origin)
    i0 = int(np.argmin(np.abs(tvals_all - a)))
    i1 = int(np.argmin(np.abs(tvals_all - b)))
    if i1 < i0:
        i0, i1 = i1, i0

    # pull exact time slice to ensure consistent length
    s_time = sess.get(f"{base}.ascii?time[{i0}:{i1}]", timeout=45); s_time.raise_for_status()
    tvals_slice = _nums(s_time.text)  # length N (may be 1 if server is odd)
    times: List[datetime] = []
    for v in tvals_slice:
        if scale.startswith("hour"):    dt = origin + pd.Timedelta(hours=float(v))
        elif scale.startswith("minute"): dt = origin + pd.Timedelta(minutes=float(v))
        elif scale.startswith("second"): dt = origin + pd.Timedelta(seconds=float(v))
        elif scale.startswith("day"):    dt = origin + pd.Timedelta(days=float(v))
        else:                             dt = origin + pd.Timedelta(hours=float(v))
        times.append(dt)

    # --- nearest spatial indices ---
    iy = int(np.argmin(np.abs(lats - lat)))
    ix = int(np.argmin(np.abs(lons - lon360)))

    def fetch_var(var: str) -> np.ndarray:
        r = sess.get(f"{base}.ascii?{var}[{i0}:{i1}][{iy}][{ix}]", timeout=45)
        r.raise_for_status()
        return np.atleast_1d(_nums(r.text)).astype(float)

    # --- variables ---
    Tk  = fetch_var("T2M")                # K
    U10 = fetch_var("U10M")
    V10 = fetch_var("V10M")
    try:
        RH = fetch_var("RH2M")            # %
    except Exception:
        QV = fetch_var("QV2M")            # kg/kg
        PS = fetch_var("PS")              # Pa
        Tc = Tk - 273.15
        e  = QV * PS / (0.622 + 0.378 * QV)
        es = 611.2 * np.exp((17.67*Tc)/(Tc+243.5))
        RH = 100.0 * np.clip(e/es, 0.0, 2.0)

    PRECrate = fetch_var("PRECTOT")       # kg m-2 s-1 == mm/s
    precip_mmhr = PRECrate * 3600.0

    # --- length alignment ---
    lengths = [len(Tk), len(U10), len(V10), len(RH), len(precip_mmhr), len(times)]
    n = int(min(lengths)) if all(l > 0 for l in lengths) else 0
    if n <= 1:
        # synthesize an hourly index from start with N from first var length (fallback)
        n = int(max(len(Tk), len(U10), len(V10), len(RH), len(precip_mmhr), 1))
        times = pd.date_range(start=start.replace(tzinfo=timezone.utc), periods=n, freq="H").to_pydatetime().tolist()

    Tk, U10, V10, RH, precip_mmhr, times = Tk[:n], U10[:n], V10[:n], RH[:n], precip_mmhr[:n], times[:n]

    # --- derived + dataframe ---
    wind_ms = np.hypot(U10, V10)
    wind_mph = wind_ms * 2.23694
    Tf = (Tk - 273.15) * 9/5 + 32

    df = pd.DataFrame(
        {"Tf": Tf, "RH": RH, "wind_mph": wind_mph, "precip_mmhr": precip_mmhr},
        index=pd.DatetimeIndex(times, name="time")
    )
    return df
