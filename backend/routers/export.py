# backend/routers/export.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from .event import EVENT_CACHE
from utils.export import csv_lines_from_event

router = APIRouter(tags=["export"])

@router.get("/event/{event_id}/export")
def export_event(event_id: str, format: str = "csv"):
    result = EVENT_CACHE.get(event_id)
    if not result:
        raise HTTPException(status_code=404, detail="event_id not found")
    if format == "json":
        return JSONResponse(content=result)
    if format == "csv":
        return StreamingResponse(
            csv_lines_from_event(result),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{event_id}.csv"'},
        )
    raise HTTPException(status_code=400, detail="format must be 'csv' or 'json'")
