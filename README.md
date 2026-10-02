# Location Assessment Tool

## Problem

Evaluating prospective real estate or business locations requires analyzing multiple geographic and environmental factors, such as terrain elevation and local climate conditions. Manually looking up addresses across disparate public government databases and meteorological APIs is slow, inconsistent, and error-prone.

## Solution

The **Location Assessment Tool** is a full-stack prototype that automates location evaluation:
1. Accepts a US street address and an optional label.
2. Geocodes the address into precise geographic coordinates (latitude and longitude).
3. Fetches real-time environmental data: elevation (via USGS) and current temperature (via Open-Meteo).
4. Computes an objective suitability score (up to 100 points) based on defined scoring bands.
5. Persists the assessment and score breakdown to an SQLite database.
6. Presents an interactive dashboard with clear status indicators (`Complete`, `Partial Data`, or `Failed`).

---

## Tech Stack

- **Frontend:** React (built with Vite, Vanilla CSS, Axios)
- **Backend:** FastAPI (Python, SQLAlchemy, Pydantic V2, HTTPX)
- **Database:** SQLite
- **External APIs:**
  - **US Census Bureau Geocoder API:** Converts US street addresses to latitude/longitude coordinates.
  - **USGS Elevation Point Query Service (EPQS):** Retrieves surface elevation in feet.
  - **Open-Meteo Forecast API:** Retrieves current ambient temperature in Celsius.

---

## Architecture

The request workflow follows a structured pipeline:

```text
Frontend (React UI)
  │  1. Submit Address & Label
  ▼
FastAPI Backend (POST /assessments)
  │  2. Query Address
  ▼
US Census Geocoder
  │  3. Return Coordinates (Lat, Lon)
  ▼
External Data Sources (in parallel / sequence)
  ├── USGS EPQS (Elevation in feet)
  └── Open-Meteo (Temperature in °C)
  │  4. Raw Metrics
  ▼
Scoring Module (backend/scoring.py)
  │  5. Compute Scores (Max 100 pts)
  ▼
SQLite Database (locations.db)
  │  6. Persist Assessment Record
  ▼
Frontend (React UI)
     7. Display Factor Breakdown, Scores & Badges
```

---

## Setup

Follow these exact steps to run the application from a fresh clone.

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**

---

### 1. Backend Setup

Open a terminal at the project root:

```bash
# 1. Navigate to the project root (if not already there)
cd location-assessment-app

# 2. Create and activate a Python virtual environment
# Windows:
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux:
# python3 -m venv venv
# source venv/bin/activate

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Start the FastAPI backend server
uvicorn backend.main:app --reload --port 8000
```

The backend API will be live at:
- **API Root:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

### 2. Frontend Setup

Open a second terminal window:

```bash
# 1. Navigate to the frontend directory
cd location-assessment-app/frontend

# 2. Install npm dependencies
npm install

# 3. Start the React development server
npm run dev
```

The frontend application will be available at [http://localhost:5173](http://localhost:5173).

---

## Scoring Rules

The system scores a location on a scale of **0 to 100 total points**, divided across two categories:

### 1. Elevation Score (Max 40 points)
Calculated from elevation in feet above sea level:
- **0 to 500 ft:** 40 points
- **501 to 1,500 ft:** 30 points
- **1,501 to 3,000 ft:** 20 points
- **3,001 to 5,000 ft:** 10 points
- **Above 5,000 ft:** 0 points

### 2. Temperature Score (Max 60 points)
Calculated from current ambient temperature in degrees Celsius (°C):
- **15°C to 25°C:** 60 points *(Ideal range)*
- **10°C to 14°C** or **26°C to 30°C:** 45 points
- **5°C to 9°C** or **31°C to 35°C:** 25 points
- **Below 5°C** or **Above 35°C:** 10 points

---

## Missing Data Handling

External APIs can intermittently fail, time out, or encounter points outside their geographical coverage. 

**Core Rule: Unavailable data is NEVER converted to zero.**

- If an external metric cannot be fetched, its raw value and factor score are recorded as `None` (`null`).
- The total score is computed strictly from the sum of available factors (e.g., if only temperature is available, the score is out of 60 possible points, rather than penalizing the assessment with a 0 for elevation).
- The record status reflects the data fidelity:
  - `complete`: All external data sources succeeded.
  - `partial`: One or more secondary data sources were unavailable; assessment is preserved and scored on available data.
  - `failed`: Geocoding failed or no data could be retrieved.
- The UI explicitly renders `Unavailable` for missing metrics, displaying a warning banner and never showing `0 ft` or `0°C`.

---

## API Timeouts

Every outbound call to external services (Census Geocoder, USGS Elevation, Open-Meteo) uses an explicit **10-second timeout** via `httpx.AsyncClient(timeout=10.0)`.

If an external service does not respond within 10 seconds:
- `httpx.TimeoutException` is caught gracefully.
- The failure is logged with context.
- The application continues processing remaining services without hanging or returning a 500 Internal Server Error.

---

## Tests

The project includes an automated test suite covering API routes, database persistence, scoring logic, live integration, and timeout handling.

To run the test suite:

```bash
# From the project root with the virtual environment activated:
python -m pytest backend/tests -v
```

---

## Design Decisions

1. **Explicit `None` vs. Sentinel Values for Missing Data**
   - *Decision:* Represent missing/unavailable metrics as `None` in Python and `null` in JSON/SQL.
   - *Alternative Considered:* Defaulting missing values to `0` or `-1`.
   - *Why this choice was made:* Elevation at sea level is genuinely `0 ft`, and temperature can genuinely be `0°C`. Defaulting errors to `0` corrupts scoring and misleads users.

2. **FastAPI with Async HTTP Client (`httpx`)**
   - *Decision:* Use FastAPI with asynchronous `httpx` clients for external API queries.
   - *Alternative Considered:* Synchronous Flask with `requests`.
   - *Why this choice was made:* Outbound calls to government and weather APIs involve I/O wait. Async execution prevents blocking the web server worker threads during network latency.

3. **Lightweight SQLite with SQLAlchemy**
   - *Decision:* Use file-backed SQLite with SQLAlchemy ORM.
   - *Alternative Considered:* PostgreSQL or in-memory dictionary storage.
   - *Why this choice was made:* Zero-setup requirement for local testing and evaluators, while retaining ACID persistence across server restarts.

4. **Modular Service Layer**
   - *Decision:* Decouple geocoding, elevation, weather, and scoring into independent service modules (`backend/services/`).
   - *Alternative Considered:* Placing all external API calls directly inside the route handler in `main.py`.
   - *Why this choice was made:* Simplifies unit testing, mocking, maintenance, and swapping data providers in the future.

---

## Limitations

- **Geographic Coverage:** The US Census Geocoder and USGS EPQS APIs only support United States locations and territories. International addresses will fail geocoding.
- **Single-Address Input:** The current prototype evaluates one address at a time; batch CSV/bulk upload is not implemented.
- **Current vs. Historical Weather:** Scoring uses real-time snapshot temperature, which varies by time of day and season, rather than annual climate averages.
- **Rate Limits & External Latency:** Government endpoints (US Census, USGS) can occasionally experience high latency or downtime during peak hours.

---

## What I Would Improve With More Time

- **Geocoding Fallback Providers:** Integrate OpenStreetMap (Nominatim) or Mapbox as fallback geocoders for international support and increased reliability.
- **Historical Climate Data:** Incorporate 30-year average temperatures and seasonal extremes rather than instantaneous single-moment weather.
- **Interactive Map:** Integrate Leaflet / MapLibre to display a map pin with elevation contour overlays.
- **Caching Layer:** Add Redis or in-memory TTL caching for geocoded coordinates and elevation lookups to minimize duplicate external API requests.
- **Batch Processing:** Add support for uploading a CSV list of addresses for batch assessment.

---

## AI Assistance

- AI assistants were used for boilerplate scaffolding, test generation, and development assistance.
- All generated code was thoroughly reviewed, debugged, manually verified, and tested against real endpoints prior to submission.

---

## Approximate Time Spent

**Time Spent:** `[ INSERT YOUR TIME HERE, e.g., 3.5 hours ]`
