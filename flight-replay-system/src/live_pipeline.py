"""
FlightSense AI — Live Pipeline (OpenSky Real Data)
Pulls live aircraft over India → ML pipeline → Supabase
"""
import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from feature_engineering import FlightFeatureEngineer
from state_engine import FlightStateEngine
from risk_engine import FlightRiskEngine
from alert_engine import FlightAlertEngine
from supabase_client import SupabaseTelemetryClient

# ── OpenSky bbox: India ───────────────────────────────────────────────────────
LAMIN, LOMIN, LAMAX, LOMAX = 8.0, 68.0, 37.0, 97.0
OPENSKY_URL = (
    f"https://opensky-network.org/api/states/all"
    f"?lamin={LAMIN}&lomin={LOMIN}&lamax={LAMAX}&lomax={LOMAX}"
)
POLL_SEC = 10   # OpenSky free tier: max 1 req/10s

# State vector indices (OpenSky docs)
# [icao, callsign, origin, _, timestamp, lat, lon, baro_alt,
#  on_ground, velocity, heading, vert_rate, _, geo_alt, squawk, spi, pos_src]
I_ICAO, I_CALL, I_TS = 0, 1, 4
I_LAT, I_LON       = 5, 6
I_BARO, I_GEO      = 7, 13
I_GND, I_SPD       = 8, 9
I_HDG, I_VRATE     = 10, 11


def fetch_aircraft() -> list:
    user = os.getenv("OPENSKY_USER", "")
    pwd  = os.getenv("OPENSKY_PASS", "")
    auth = (user, pwd) if user else None
    try:
        r = requests.get(OPENSKY_URL, auth=auth, timeout=15)
        if r.status_code == 200:
            states = r.json().get("states") or []
            # filter: airborne only, has velocity + altitude
            return [s for s in states
                    if s[I_GND] is False
                    and s[I_SPD] is not None
                    and s[I_BARO] is not None]
        print(f"[OpenSky] HTTP {r.status_code}")
    except Exception as e:
        print(f"[OpenSky] fetch error: {e}")
    return []


def derive_phase(alt_ft: float, vrate: float) -> str:
    if alt_ft < 500:   return "TAKEOFF" if vrate > 100 else "LANDING"
    if vrate >  300:   return "CLIMB"
    if vrate < -300:   return "DESCENT"
    if alt_ft > 20000: return "CRUISE"
    return "CLIMB"


def state_to_frame(s: list, ts: int) -> dict:
    alt_m    = s[I_BARO] or 0.0
    alt_ft   = alt_m * 3.281
    spd_ms   = s[I_SPD] or 0.0
    spd_kt   = spd_ms * 1.944
    vrate    = (s[I_VRATE] or 0.0) * 196.85   # m/s → fpm
    heading  = s[I_HDG] or 0.0

    # Estimate engine temp from altitude & speed (plausible physics proxy)
    engine_temp = 75 + (spd_kt / 500) * 40 + (alt_ft / 40000) * 15
    engine_temp = round(min(max(engine_temp, 70), 130), 1)

    # Fuel proxy: decreases with time-in-flight (use altitude as proxy)
    fuel = round(max(10.0, 100 - (alt_ft / 40000) * 60), 1)

    phase = derive_phase(alt_ft, vrate)

    return {
        "timestamp":      ts,
        "icao24":         s[I_ICAO] or "UNKNOWN",
        "callsign":       (s[I_CALL] or "").strip() or "UNKNOWN",
        "altitude":       round(alt_ft, 1),
        "airspeed":       round(spd_kt, 1),
        "vertical_speed": round(vrate, 1),
        "engine_temp":    engine_temp,
        "fuel_level":     fuel,
        "pitch":          0.0,
        "roll":           0.0,
        "yaw":            round(heading, 1),
        "phase":          phase,
    }


def run_live_pipeline():
    db       = SupabaseTelemetryClient()
    frame_n  = 0
    print("FlightSense AI — OpenSky Live Pipeline ONLINE")
    print(f"Tracking real aircraft over India (bbox {LAMIN}N-{LAMAX}N, {LOMIN}E-{LOMAX}E)")
    print("=" * 60)

    while True:
        aircraft = fetch_aircraft()
        if not aircraft:
            print("[Pipeline] No aircraft returned, retrying...")
            time.sleep(POLL_SEC)
            continue

        ts = int(time.time())
        print(f"\n[Tick] {len(aircraft)} airborne aircraft found")

        for s in aircraft[:1]:   # process only 1 per tick to keep a single-aircraft timeseries
            frame_n += 1
            raw = state_to_frame(s, ts)

            try:
                df = pd.DataFrame([raw])
                df = FlightFeatureEngineer(df).engineer()
                df = FlightStateEngine(df).assign_states()
                df = FlightRiskEngine(df).calculate_risk_score()
                alerts = FlightAlertEngine(df).generate_alerts()

                payload = {
                    "timestamp":      raw["timestamp"],
                    "callsign":       raw["callsign"],
                    "phase":          raw["phase"],
                    "altitude":       raw["altitude"],
                    "airspeed":       raw["airspeed"],
                    "pitch":          raw["pitch"],
                    "roll":           raw["roll"],
                    "yaw":            raw["yaw"],
                    "engine_temp":    raw["engine_temp"],
                    "fuel_level":     raw["fuel_level"],
                    "vertical_speed": raw["vertical_speed"],
                    "risk_score":     float(df.iloc[-1]["risk_score"]),
                    "flight_state":   str(df.iloc[-1]["flight_state"]),
                }
                db.insert_telemetry(payload)

                print(
                    f"[{frame_n:04d}] {raw['callsign']:8s} {raw['phase']:8s} | "
                    f"ALT={raw['altitude']:7.0f}ft SPD={raw['airspeed']:5.1f}kt "
                    f"TMP={raw['engine_temp']:5.1f}°C FUEL={raw['fuel_level']:4.1f}% "
                    f"RISK={payload['risk_score']:4.1f} ALERTS={len(alerts)}"
                )
            except Exception as e:
                print(f"[{raw['callsign']}] pipeline error: {e}")

        time.sleep(POLL_SEC)


if __name__ == "__main__":
    run_live_pipeline()