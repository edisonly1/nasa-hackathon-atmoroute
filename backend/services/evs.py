def subscores_from_raw(rain_mmhr: float, wind_mph: float, heatindex_F: float, rh_pct: float) -> dict:
    # Simple monotone piecewise maps (MVP defaults)
    def map_rain(x):
        if x <= 0.2: return 100
        if x <= 2.0: return 40
        if x <= 5.0: return 20
        return 0
    def map_wind(x):
        if x <= 10: return 100
        if x <= 20: return 60
        if x <= 25: return 30
        return 10
    def map_heat(x):
        if x <= 85: return 100
        if x <= 95: return 70
        if x <= 100: return 40
        return 15
    def map_rh(x):
        if x <= 60: return 100 if x >= 40 else 80
        if x <= 80: return 70
        return 40

    return {
        "rain": map_rain(rain_mmhr),
        "wind": map_wind(wind_mph),
        "heat": map_heat(heatindex_F),
        "humidity": map_rh(rh_pct),
    }

def evs_from_subscores(sub: dict, weights=None) -> float:
    w = weights or {"rain": 0.45, "wind": 0.25, "heat": 0.20, "humidity": 0.10}
    total = sum(sub[k] * w[k] for k in w.keys())
    return max(0.0, min(100.0, total))
