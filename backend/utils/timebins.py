# backend/utils/timebins.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dateutil import parser

def enumerate_bins(start_iso: str, duration_min: int, step_min: int) -> list[datetime]:
    """
    Create a list of datetimes starting at start_iso with step_min spacing
    and total span of duration_min (exclusive of the end).
    """
    if step_min <= 0 or duration_min <= 0:
        return []
    start = parser.isoparse(start_iso)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    steps = duration_min // step_min
    return [start + timedelta(minutes=step_min * i) for i in range(steps)]
