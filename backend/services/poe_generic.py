# backend/services/poe_generic.py
# Generic per parameter PoE engine: DOY±window pooling + PoE/Hist/CDF/PoE-curve.

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import datetime
from math import sqrt
from typing import List, Tuple, Dict, Any

def _CtoF(c): return c*9/5+32
def _to_mph(ms): return ms*2.23694

def _heat_index_F(Tf, RH):
    if pd.isna(Tf) or pd.isna(RH): return np.nan
    if Tf < 80: return Tf
    c1=-42.379; c2=2.04901523; c3=10.14333127
    c4=-0.22475541; c5=-0.00683783; c6=-0.05481717
    c7=0.00122874; c8=0.00085282; c9=-0.00000199
    HI=(c1+c2*Tf+c3*RH+c4*Tf*RH+c5*Tf*Tf+c6*RH*RH+c7*Tf*Tf*RH+c8*Tf*RH*RH+c9*Tf*Tf*RH*RH)
    if RH<13 and 80<=Tf<=112: HI -= ((13-RH)/4)*sqrt((17-abs(Tf-95))/17)
    if RH>85 and 80<=Tf<=87:  HI += 0.02*(RH-85)*(87-Tf)
    return HI

# Registry: how to compute each variable from the merged daily dataframe
# df columns assumed: tmaxC,tminC,tavgC,rh,ws_ms,pr_mm
def series_for(var: str, df: pd.DataFrame) -> pd.Series:
    if var == "precip_mm_day": return df["pr_mm"].fillna(0.0)
    if var == "precip_mm_hr":  return (df["pr_mm"].fillna(0.0) / 24.0)
    if var == "wind_mph":      return _to_mph(df["ws_ms"])
    if var == "gust_mph":      return _to_mph(df["ws_ms"]) * 1.6
    if var == "rh_pct":        return df["rh"].clip(0,100)
    if var == "tmaxF":         return _CtoF(df["tmaxC"])
    if var == "tminF":         return _CtoF(df["tminC"])
    if var == "heatindex_F":
        tmaxF = _CtoF(df["tmaxC"]); rh = df["rh"].clip(0,100)
        return pd.Series([_heat_index_F(T, R) for T, R in zip(tmaxF, rh)], index=df.index)
    raise KeyError(f"Unsupported var: {var}")

UNITS = {
  "precip_mm_day":"mm/day","precip_mm_hr":"mm/hr","wind_mph":"mph","gust_mph":"mph",
  "rh_pct":"%","tmaxF":"°F","tminF":"°F","heatindex_F":"°F"
}

def _pool_same_doy(series: pd.Series, center: datetime, window_days: int) -> np.ndarray:
    doy = int(center.strftime("%j")); half = window_days//2
    vals=[]
    for y in range(series.index.year.min(), series.index.year.max()+1):
        base = pd.Timestamp(y,1,1) + pd.Timedelta(days=doy-1)
        for d in range(-half, half+1):
            t = base + pd.Timedelta(days=d)
            if t in series.index:
                vals.append(series.loc[t])
    a = np.asarray(vals, dtype=float)
    return a[~np.isnan(a)]

def _hist(a: np.ndarray, bins):
    if a.size == 0:
        b = bins if isinstance(bins, list) else []
        k = (len(b)-1) if isinstance(b, list) else 0
        return {"bins": b, "pdf": [0]*max(0,k)}
    if not isinstance(bins, list):
        bins = np.histogram_bin_edges(a, bins=bins).tolist()
    h, edges = np.histogram(a, bins=bins, density=False)
    s = h.sum(); pdf = (h/s).tolist() if s else [0]*len(h)
    return {"bins": edges.tolist(), "pdf": pdf}

def _cdf(a: np.ndarray):
    if a.size == 0: return {"x": [], "F": []}
    x = np.sort(a); n = x.size
    F = np.arange(1, n+1) / n
    return {"x": x.tolist(), "F": F.tolist()}

def _poe_value(a: np.ndarray, thr: float, op: str):
    if a.size == 0: return 0.0
    if op == "ge": return float(np.mean(a >= thr))
    if op == "le": return float(np.mean(a <= thr))
    raise ValueError("op must be 'ge' or 'le'")

def _poe_curve(a: np.ndarray, op: str, n=40):
    if a.size == 0: return {"thresholds": [], "poe": []}
    q = np.linspace(0.02, 0.98, n)
    thr = np.quantile(a, q)
    poe = [ _poe_value(a, t, op) for t in thr ]
    return {"thresholds": thr.tolist(), "poe": poe}

def compute_generic_poe(df: pd.DataFrame, center: datetime, window_days: int, metrics: list):
    results = {}
    for m in metrics:
        var, thr, op = m["var"], float(m["threshold"]), m.get("op","ge")
        a = _pool_same_doy(series_for(var, df), center, window_days)
        # default bins by var family
        default_bins = {
            "precip_mm_day":[0,1,5,10,15,25,50],
            "precip_mm_hr":[0,0.2,0.5,1,2,5,10],
            "wind_mph":[0,5,10,15,20,25,35,50],
            "gust_mph":[0,10,15,20,25,30,35,45,60],
            "rh_pct":[20,30,40,50,60,70,80,90,100],
            "tmaxF":[60,70,80,85,90,95,100,105],
            "tminF":[-10,0,10,20,32,40,50,60],
            "heatindex_F":[70,80,85,90,95,100,105]
        }.get(var, 10)  # auto if unknown
        hist = _hist(a, default_bins)
        results[var] = {
            "poe": _poe_value(a, thr, op),
            "hist": hist,
            "cdf": _cdf(a),
            "poe_curve": _poe_curve(a, op),
            "units": UNITS.get(var, "")
        }
    samples = len(_pool_same_doy(series_for(metrics[0]["var"], df), center, window_days)) if metrics else 0
    return results, samples
