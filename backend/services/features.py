from __future__ import annotations
import math
from datetime import datetime
from typing import Dict

def _doy_feats(dt: datetime) -> Dict[str, float]:
    doy = dt.timetuple().tm_yday
    return {
        "doy_sin": math.sin(2*math.pi*doy/366),
        "doy_cos": math.cos(2*math.pi*doy/366),
    }

def build_features(row: Dict, when: datetime) -> Dict[str, float]:
    """
    row: dict like {"tmaxC":..,"tminC":..,"tavgC":..,"rh":..,"ws_ms":..,"pr_mm":..}
    when: datetime (UTC is fine)
    """
    tmaxC = float(row.get("tmaxC") or 0.0)
    tminC = float(row.get("tminC") or 0.0)
    tavgC = float(row.get("tavgC") or 0.0)
    rh    = float(row.get("rh") or 0.0)          # %
    ws_ms = float(row.get("ws_ms") or 0.0)       # m/s
    pr_mm = float(row.get("pr_mm") or 0.0)       # mm/day

    ws_mph = ws_ms * 2.23694
    tmaxF  = tmaxC * 9/5 + 32
    HI     = tmaxF + 0.2 * (rh/100.0) * (tmaxF - 80.0)  # simple proxy

    feats = {
        "tmaxC": tmaxC,
        "tminC": tminC,
        "tavgC": tavgC,
        "rh_pct": rh,
        "ws_mph": ws_mph,
        "pr_mm": pr_mm,
        "tmaxF": tmaxF,
        "heatindex_F": HI,
    }
    feats.update(_doy_feats(when))
    return feats