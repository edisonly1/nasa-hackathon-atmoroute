from __future__ import annotations
from typing import Dict, List, Optional
import math
import random

# set fixed seed per call (from inputs) so wording is stable
def _seed_from(features: Dict[str, float], p: float) -> int:
    h = hash((round(p, 3),
              round(features.get("pr_mm", 0.0), 3),
              round(features.get("ws_mph", features.get("ws_ms", 0.0) * 2.23694), 3),
              round(features.get("rh_pct", features.get("rh", 0.0)), 1),
              round(features.get("tmaxC", 0.0), 1)))
    return h & 0xFFFFFFFF

def _band(v: float, cuts: List[float]) -> int:
    # returns 0..len(cuts) (bin index)
    for i, c in enumerate(cuts):
        if v < c:
            return i
    return len(cuts)

def _fmt_pct(x: float) -> str:
    return f"{x*100:.0f}%"

def _risk_word(p: float) -> str:
    b = _band(p, [0.35, 0.6, 0.85])
    return ["LOW", "MODERATE", "HIGH", "VERY HIGH"][b]

def _conf_phrase(p: float, conf: List[float]) -> str:
    if not conf or len(conf) != 2:
        return ""
    low, high = conf
    width = max(0.0, high - low)
    if width <= 0.1:  tag = "tight"
    elif width <= 0.2: tag = "reasonable"
    else:             tag = "wide"
    return f"(± ~{_fmt_pct(width/2)}) {tag} confidence"

def _driver_phrases(f: Dict[str, float]) -> List[str]:
    pr = float(f.get("pr_mm", 0.0))
    ws = float(f.get("ws_mph", f.get("ws_ms", 0.0) * 2.23694))
    rh = float(f.get("rh_pct", f.get("rh", 0.0)))
    tmaxC = float(f.get("tmaxC", 0.0))
    hiF = float(f.get("heatindex_F", 0.0))
    phrases = []

    # rain
    rb = _band(pr, [0.1, 1.0, 5.0])  # mm/day
    rain_words = ["little to no precip", "light precip", "showery setup", "wet/soaking"]
    phrases.append(f"{rain_words[rb]} (~{pr:.1f} mm)")

    # humidity
    hb = _band(rh, [45, 60, 75])
    hum_words = ["dry air", "moderate humidity", "humid", "very humid"]
    phrases.append(f"{hum_words[hb]} (RH ~{rh:.0f}%)")

    # wind
    wb = _band(ws, [8, 15, 22])
    wind_words = ["light winds", "breezy", "windy", "strong gusts"]
    phrases.append(f"{wind_words[wb]} (~{ws:.0f} mph)")

    # heat / instability proxy
    if hiF and hiF >= 95:
        phrases.append(f"elevated heat index (~{hiF:.0f}°F)")
    elif tmaxC >= 30:
        phrases.append(f"hot afternoon (~{tmaxC:.0f}°C)")

    return phrases

def _timing_hint(f: Dict[str, float]) -> str:
    # convection heuristic: warm + humid -> afternoon risk
    rh = float(f.get("rh_pct", f.get("rh", 0.0)))
    tmaxC = float(f.get("tmaxC", 0.0))
    if tmaxC >= 22 and rh >= 55:
        return "Greatest shower risk typically 14:00–18:00 local; morning (09:00–12:00) is usually the safer window."
    if rh < 45 and tmaxC < 18:
        return "Cool/drier setup; if showers occur, they tend to be brief and earlier."
    return "Risk fairly flat through the day; monitor for short-notice updates."

def _actions(f: Dict[str, float], p: float) -> List[str]:
    pr = float(f.get("pr_mm", 0.0))
    ws = float(f.get("ws_mph", f.get("ws_ms", 0.0) * 2.23694))
    rh = float(f.get("rh_pct", f.get("rh", 0.0)))
    out: List[str] = []

    # baseline action by risk
    if p >= 0.85:
        out.append("Delay start 60–90 min if schedule allows; prepare a wet-weather plan.")
    elif p >= 0.6:
        out.append("Keep Plan B ready; add rain covers and aisle mats.")
    else:
        out.append("Proceed with standard setup; keep a light rain plan on standby.")

    # rain-driven
    if pr >= 1.0:
        out.append("Protect electronics and signage; ensure drainage and slip-resistant flooring.")
    # wind-driven
    if ws >= 20:
        out.append("Ballast/secure canopies and stage elements; limit tall banners.")
    elif ws >= 12:
        out.append("Check tie-downs and cable management for breezy conditions.")

    # humidity / heat
    if rh >= 70:
        out.append("Have towels and cover cloths ready for damp surfaces.")
    return out

def llm_brief(features: Dict[str, float], p: float, conf: List[float], loc: List[Optional[float]]) -> str:
    """
    Offline, deterministic NLG that crafts an ops-style briefing.
    No external APIs or models required. Always returns text.
    """
    random.seed(_seed_from(features, p))

    risk_word = _risk_word(p)
    conf_txt  = _conf_phrase(p, conf)
    drivers   = _driver_phrases(features)
    timing    = _timing_hint(features)
    actions   = _actions(features, p)

    # small var in wording (so i can make it sound more impressive LOL)
    openers = [
        "EXEC SUMMARY", "SUMMARY", "OPERATIONAL SUMMARY"
    ]
    opener = random.choice(openers)

    lines = []
    loc_str = (
        f"({loc[0]:.4f}, {loc[1]:.4f})" if loc and None not in loc
        else "(location provided)"
    )

    lines.append(f"{opener}: {risk_word} risk of impactful weather — { _fmt_pct(p) } {conf_txt}".strip())
    lines.append("")
    lines.append(f"• Location: {loc_str}")
    lines.append("• Drivers: " + "; ".join(drivers))
    lines.append(f"• Timing: {timing}")
    lines.append("• Actions:")
    for a in actions:
        lines.append(f"  - {a}")
    lines.append("")
    lines.append("One-liner: Prep for weather impacts; favor earlier window and keep Plan B ready.")
    

    return "\n".join(lines)