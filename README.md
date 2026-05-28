# FlightSense AI ✈️

> Real-time flight monitoring platform tracking live aircraft over India using OpenSky ADS-B data, ML anomaly detection (Isolation Forest), and a React dashboard backed by Supabase.

---

## What it does
- Tracks **200+ live aircraft** over India via OpenSky Network ADS-B
- Supports **CSV-based historical flight replay** for offline analysis
- Runs each flight through an **ML anomaly detection pipeline** (Isolation Forest)
- Calculates **risk scores** using physics-based scoring functions
- Streams live data to **Supabase** every 10 seconds
- Displays on a **React HUD dashboard** with real-time charts

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Data Processing | Pandas |
| ML / Anomaly Detection | Scikit-learn (Isolation Forest) |
| Live Flight Data | OpenSky Network ADS-B REST API |
| Offline Data | CSV telemetry (altitude, airspeed, engine temp, fuel) |
| Database | Supabase (PostgreSQL) |
| Backend DB Client | Supabase Python SDK |
| HTTP Client | Requests |
| Environment Config | python-dotenv |
| Frontend Framework | React + TypeScript |
| Frontend Build Tool | Vite |
| Charts | Recharts |
| Animations | Framer Motion |
| Styling | Tailwind CSS |
| Version Control | Git / GitHub |

---

## Features
- Real ICAO callsigns (IndiGo, Air India, Air Arabia, SpiceJet)
- CSV parser + cleaner with physical bounds enforcement
- MIL-STD-1553 style tiered alerts (ADVISORY → CAUTION → WARNING → EMERGENCY)
- 6 flight phases: PREFLIGHT → TAKEOFF → CLIMB → CRUISE → DESCENT → LANDING
- Isolation Forest + rule-based combined anomaly detection
- Incident timeline reconstruction around anomalies
- Live risk bar, engine temp, fuel burn, vertical speed charts
- Phase-colored HUD badge per flight

---

## Two Modes

### Live Mode (OpenSky)
Pulls real ADS-B transponder data from 200+ aircraft flying over India right now.
```
python src/live_pipeline.py
```

### Offline Mode (CSV)
Replay historical flight data from a CSV file through the full ML pipeline.
```
python app.py
```
CSV format required:
```
timestamp,altitude,airspeed,pitch,roll,yaw,engine_temp,fuel_level,vertical_speed
```

---

## Setup
```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/flightsense-ai.git
cd flightsense-ai/flight-replay-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add credentials
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_KEY, OPENSKY_USER, OPENSKY_PASS

# 4. Run live pipeline
python src/live_pipeline.py

# 5. Run frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

## Environment Variables
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENSKY_USER=your_opensky_email
OPENSKY_PASS=your_opensky_password
```

---

## Note on Callsigns
Some aircraft suppress ADS-B identification (military, private jets) — these show as UNKNOWN. This is real-world ATC behavior, not a bug.

---

Built with Python + React. Data from OpenSky Network.
