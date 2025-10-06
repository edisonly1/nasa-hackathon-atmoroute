from __future__ import annotations
import joblib, numpy as np
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class EVSModelOut:
    p: float
    p_low: float
    p_high: float

class EVSModel:
    def __init__(self, model_path: str, meta_path: str, band=0.1):
        self.clf = joblib.load(model_path)
        meta = joblib.load(meta_path)
        self.feat_names: List[str] = meta["feat_names"]
        self.band = band

    def predict(self, feats: Dict[str, float]) -> EVSModelOut:
        x = np.array([[feats[k] for k in self.feat_names]], dtype=float)
        p = float(self.clf.predict_proba(x)[0, 1])
        return EVSModelOut(
            p=p,
            p_low=max(0.0, p - self.band),
            p_high=min(1.0, p + self.band),
        )