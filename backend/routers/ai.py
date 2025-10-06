from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime
from pathlib import Path

from services.models.evs_model import EVSModel
from services.features import build_features
from services.power import fetch_power_point

router = APIRouter(prefix="/api/ai", tags=["AI"])

ROOT = Path(__file__).resolve().parents[1]
MODEL = EVSModel(
    model_path=str(ROOT / "models" / "evs_clf.joblib"),
    meta_path=str(ROOT / "models" / "evs_meta.joblib"),
)

class ScoreReq(BaseModel):
    feats: Dict[str, float] = Field(..., description="flat features dict")

@router.post("/score")
def ai_score(req: ScoreReq):
    try:
        out = MODEL.predict(req.feats)
        return {"p_ge_70": out.p, "conf": [out.p_low, out.p_high]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from datetime import datetime, timedelta

@router.get("/realtime")
def ai_realtime(lat: float, lon: float):
    try:
        end_dt = datetime.utcnow() - timedelta(hours=18)
        start_dt = end_dt - timedelta(days=6)   # 7 day window total
        start = start_dt.strftime("%Y%m%d")
        end = end_dt.strftime("%Y%m%d")

        df = fetch_power_point(lat, lon, start=start, end=end)

        # POWER uses -999 for missing stuff (so itll be inacc if missing bruh))
        import numpy as np
        df = df.replace(-999, np.nan).dropna(how="any")
        if df.empty:
            raise HTTPException(status_code=404, detail="No valid POWER rows in the last 7 days.")

        row = df.sort_index().iloc[-1].to_dict()
        feats = build_features(row, end_dt)
        out = MODEL.predict(feats)
        return {
            "location": [lat, lon],
            "features_used": feats,
            "p_ge_70": out.p,
            "conf": [out.p_low, out.p_high],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
