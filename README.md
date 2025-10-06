# NASA space app challenge 2025 Team Snakes

## The Challenge
If you’re planning an outdoor event—like a vacation, a hike on a trail, or fishing on a lake—it would be good to know the chances of adverse weather for the time and location you are considering. There are many types of Earth observation data that can provide information on weather conditions for a particular location and day of the year. Your challenge is to construct an app with a personalized interface that enables users to conduct a customized query to tell them the likelihood of “very hot,” “very cold,” “very windy,” “very wet,” or “very uncomfortable” conditions for the location and time they specify.

## Structure
 -- frontend/
- Next.js (React + TypeScript) web application
- Interactive map (Leaflet / Mapbox GL JS)
- Sidebar parameter controls (date, duration, thresholds)
- CSV download for route specific data
-- backend/
- FastAPI service in Python
- /api/poe: Computes Probability of Exceedance using NASA POWER data
- /api/event: Generates corridor analysis for event routes
- /api/export: Provides CSV data export
- Built in caching and histogram computation

## Features
Features
- Probability of Exceedance (PoE) — Statistical probability that precipitation, temperature, humidity, or wind will exceed chosen limits.
- Uses multi year NASA reanalysis data to estimate long-term seasonal probabilities for far-future events.
- Event Corridor Analysis — Evaluates routes to show risk along a parade or travel path.
- Histogram Visualization — Displays historical distributions for each weather variable.
- Data Export — One click CSV download for PoE and histogram data.
- Responsive UI — Built with React, TypeScript, and Tailwind CSS.

## Data sources
NASA POWER (Prediction of Worldwide Energy Resources)
https://power.larc.nasa.gov/
MERRA-2 Reanalysis Data — Temperature, wind, precipitation, humidity
https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/
NLDAS Data Rods
https://disc.gsfc.nasa.gov/information/tools?title=Data%20Rods

## Links
Web App 
[https://nasa-hackathon-atmoroute.vercel.app](https://nasa-hackathon-atmoroute.vercel.app/)

Team Link
[https://www.spaceappschallenge.org/2025/challenges/will-it-rain-on-my-parade/](https://www.spaceappschallenge.org/2025/find-a-team/snakes/?tab=details)
