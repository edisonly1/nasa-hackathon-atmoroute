# backend/utils/export.py
from typing import Iterable

def csv_lines_from_event(result: dict) -> Iterable[str]:
    """CSV export for the last Event Corridor run."""
    meta = result.get("meta", {})
    yield "# Will it Rain on My Parade? — Event Corridor Export\n"
    yield f"# Units: {meta.get('units')}\n"
    yield f"# Sources: {meta.get('sources')}\n"
    yield f"# Notes: {meta.get('notes')}\n"
    yield "time,cell_id,lon,lat,evs_total,rain_sub,wind_sub,heat_sub,humidity_sub\n"

    times = result["times"]
    for cell in result["cells"]:
        cid = cell["cell_id"]; lon = cell["lon"]; lat = cell["lat"]
        for comp in cell["evs"]:
            ti = comp["t"]
            row = [
                times[ti], str(cid), f"{lon:.6f}", f"{lat:.6f}",
                f"{comp['total']:.2f}",
                f"{comp['rain']:.1f}", f"{comp['wind']:.1f}",
                f"{comp['heat']:.1f}", f"{comp['humidity']:.1f}",
            ]
            yield ",".join(row) + "\n"
