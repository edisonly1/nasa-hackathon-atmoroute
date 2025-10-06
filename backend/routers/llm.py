# atmoroute/backend/routers/llm.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

from services.power import fetch_power_point
from services.features import build_features
from services.models.evs_model import EVSModel
from services.llm import llm_brief

router = APIRouter(prefix="/api/llm", tags=["LLM"])

ROOT = Path(__file__).resolve().parents[1]
MODEL = EVSModel(
    model_path=str(ROOT / "models" / "evs_clf.joblib"),
    meta_path=str(ROOT / "models" / "evs_meta.joblib"),
)

class ScoreBody(BaseModel):
    feats: Dict[str, float] = Field(..., description="Flat features dict used by the EVS model.")

@router.get("/brief")
def llm_brief_realtime(lat: float = Query(...), lon: float = Query(...)):
    """
    Fetch NASA POWER for last ~7 days, pick most recent valid day,
    score with EVS model, then generate an LLM briefing.
    Works with or without OPENAI_API_KEY (fallback text if missing).
    """
    try:
        end_dt = datetime.utcnow() - timedelta(hours=18)  # avoid incomplete UTC day (cuz itll use 999 for missing stuff and mess it up)
        start_dt = end_dt - timedelta(days=6)
        start, end = start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")

        df = fetch_power_point(lat, lon, start=start, end=end)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No POWER data returned.")
        df = df.replace(-999, np.nan).dropna(how="any")
        if df.empty:
            raise HTTPException(status_code=404, detail="No valid POWER rows in the last 7 days.")

        row = df.sort_index().iloc[-1].to_dict()
        feats = build_features(row, end_dt)
        out = MODEL.predict(feats)
        brief_text = llm_brief(feats, out.p, [out.p_low, out.p_high], [lat, lon])

        return {
            "location": [lat, lon],
            "features_used": feats,
            "p_ge_70": out.p,
            "conf": [out.p_low, out.p_high],
            "brief": brief_text,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/brief")
def llm_brief_from_features(body: ScoreBody):
    """
    Provide features directly; we score with EVS and generate an LLM briefing.
    """
    try:
        out = MODEL.predict(body.feats)
        brief_text = llm_brief(body.feats, out.p, [out.p_low, out.p_high], [None, None])
        return {"p_ge_70": out.p, "conf": [out.p_low, out.p_high], "brief": brief_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))