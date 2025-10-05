# backend/schemas/meta.py
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel

class MetaResponse(BaseModel):
    name: str
    version: str
    datasets: List[str]
    units: Dict[str, str]
    cadence: str
    sources: List[str]
    notes: Optional[str] = None
