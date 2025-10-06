# AtmoRoute — NASA Space Apps Challenge 2025

**What we built**
AtmoRoute is a real-time weather-risk engine for outdoor events and route planning. Draw a corridor on the map and pick a date; we turn open **NASA POWER/DataRods** into:

* Probability-of-Exceedance (PoE) for impactful weather (default: ≥ 1 mm/day rain, plus wind & humidity/heat)
* One **Event Viability Score (EVS)** for the route (0–100)
* Uncertainty bands on every probability
* A plain-English ops brief with timing, drivers, and recommended actions

Runs on CPU laptops, uses only open data, and is explainable by design.
**Live demo:** [https://nasa-hackathon-atmoroute.vercel.app/](https://nasa-hackathon-atmoroute.vercel.app/)

---

## The challenge

[https://www.spaceappschallenge.org/2025/challenges/will-it-rain-on-my-parade/]

---

## How it works

For each point along your route and chosen date, we query **historical daily NASA POWER** values at the **exact latitude/longitude** for the **same day-of-year within ± window_days** (captures local seasonality). We build features from precipitation, wind, relative humidity, and temperatures, add smooth seasonality (sine/cosine of day-of-year), and short-term memory via recent-day lags and rolling statistics. A **LightGBM** model with **physics-guided monotone constraints** (risk never decreases as precip/wind/RH increase) predicts PoE. We **calibrate** probabilities with isotonic regression and attach **split-conformal** uncertainty bands. Segments are sampled along the polyline using **haversine (great-circle) spacing** and aggregated with driver weights into **EVS**. The UI colors segments by risk and generates an Ops Brief.

---

## Repository structure

```
atmoroute/
├─ backend/                 # FastAPI app (PoE, EVS, what-if, explain, trend)
│  ├─ api.py                # REST endpoints
│  ├─ model/                # trained artifacts (evs_clf.joblib, evs_meta.joblib)
│  └─ training/             # train_evs_calibrated.py, POWER fetch & prep
├─ frontend/                # Next.js (React + TypeScript), Tailwind, Leaflet
└─ scripts/                 # helper scripts (figs, evaluation)
```

---

## Install & run

**Backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn atmoroute.backend.api:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
# open http://localhost:3000
```

**(Optional) Train a model**

```bash
cd backend/training
python train_evs_calibrated.py --tau_mm 1.0 --window_days 21
# writes evs_clf.joblib and evs_meta.joblib (features, calibration, conformal q)
```

---

## What the app returns

* **Per-segment PoE** with an **uncertainty band**
* **EVS (0–100)** for the whole corridor
* **Ops Brief**: likely timing, main drivers, and recommended actions
* **What-if**: nudge inputs (e.g., +2 mm rain, +5 mph wind) to see risk deltas

---

## Why it matters

* **Decisions need probabilities**: we show how likely, how uncertain, and what to do (e.g., delay 60–90 minutes or choose an earlier window).
* **Trustworthy AI**: physics-guided constraints, leakage-safe validation, calibration, and conformal bands yield probabilities you can defend.
* **Accessible**: open NASA data, small footprint, CPU-only deployment.

---

## Tech stack

* **Backend**: Python, FastAPI, Uvicorn
* **ML**: LightGBM, scikit-learn (calibration/metrics), NumPy, pandas, joblib
* **Frontend**: TypeScript, React/Next.js, Tailwind CSS, Leaflet, HTML/JS
* **Hosting**: Vercel (frontend). Backend can run locally or on any VM

---

## NASA data & docs (verified links)

* POWER Portal — [https://power.larc.nasa.gov/](https://power.larc.nasa.gov/)
* POWER Services/API Docs — [https://power.larc.nasa.gov/docs/services/api/](https://power.larc.nasa.gov/docs/services/api/)
* POWER Temporal Daily API — [https://power.larc.nasa.gov/docs/services/api/temporal/daily/](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
* POWER Data Access Viewer (DAV) — [https://power.larc.nasa.gov/data-access-viewer/](https://power.larc.nasa.gov/data-access-viewer/)
* DAV Quick Start — [https://power.larc.nasa.gov/data-access-viewer/quick-start/](https://power.larc.nasa.gov/data-access-viewer/quick-start/)

*(We use POWER’s open daily climatology at the requested lat/lon and DOY ± window_days to compute PoE.)*

---

## Other tools & data (verified links)

* LightGBM — [https://lightgbm.readthedocs.io/](https://lightgbm.readthedocs.io/)
* scikit-learn — [https://scikit-learn.org/stable/](https://scikit-learn.org/stable/)
* NumPy — [https://numpy.org/](https://numpy.org/)
* pandas — [https://pandas.pydata.org/](https://pandas.pydata.org/)
* FastAPI — [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
* Uvicorn — [https://www.uvicorn.org/](https://www.uvicorn.org/)
* React — [https://react.dev/](https://react.dev/)
* Next.js — [https://nextjs.org/](https://nextjs.org/)
* Leaflet — [https://leafletjs.com/](https://leafletjs.com/)
* Tailwind CSS — [https://tailwindcss.com/](https://tailwindcss.com/)
* Vercel — [https://vercel.com/](https://vercel.com/)
* OpenStreetMap Attribution — [https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright)
* Haversine formula (route sampling reference) — [https://en.wikipedia.org/wiki/Haversine_formula](https://en.wikipedia.org/wiki/Haversine_formula)

---

## AI use (disclosure)

We used an AI assistant **only for bug fixing and small refactors** (handling POWER sentinel −999 values, cross-platform paths, numeric clipping, and minor performance tweaks). All suggestions were reviewed and tested before commit. The Ops Brief is **deterministic** by default; teams may optionally enable a local/API LLM to generate a richer, AI-labeled narrative.

---

## Notes for judges

* **Validation**: GroupKFold by ~0.25° “site” buckets to prevent spatial leakage; optional rolling time splits for future-only tests.
* **Calibration + uncertainty**: post-hoc isotonic calibration and split-conformal bands on every probability.
* **Geometry**: we use **haversine (great-circle) spacing** to sample route segments prior to EVS aggregation — analogous in spirit to the “shoelace-theorem” style of being explicit about the geometry step, but for polylines instead of polygon area.

---

##US

[https://www.spaceappschallenge.org/2025/find-a-team/snakes/]
[https://www.spaceappschallenge.org/2025/challenges/will-it-rain-on-my-parade/]
