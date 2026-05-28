"""
FlightSense AI — State Engine
Phase-aware state classification matching simulator phases.
"""


class FlightStateEngine:
    def __init__(self, dataframe):
        self.data = dataframe.copy()

    def classify_state(self, row):
        # Priority 1: explicit phase column from simulator
        if "phase" in row and row["phase"] in (
            "PREFLIGHT","TAKEOFF","CLIMB","CRUISE","DESCENT","LANDING"
        ):
            # Override with EMERGENCY if sensors breach limits
            if row.get("engine_temp", 0) > 125:
                return "EMERGENCY"
            return row["phase"]

        # Fallback: derive from telemetry values
        vs   = row.get("vertical_speed", 0)
        spd  = row.get("airspeed", 0)
        temp = row.get("engine_temp", 0)
        alt  = row.get("altitude", 0)

        if temp > 125:                          return "EMERGENCY"
        if alt < 100 and spd < 50:              return "PREFLIGHT"
        if alt < 2000 and spd < 175:            return "TAKEOFF"
        if vs > 200:                            return "CLIMB"
        if vs < -200:                           return "DESCENT"
        if alt < 3500 and vs < 0:              return "LANDING"
        if abs(vs) <= 100 and spd > 300:        return "CRUISE"
        return "UNSTABLE"

    def assign_states(self):
        self.data["flight_state"] = self.data.apply(self.classify_state, axis=1)
        self.data["state"]        = self.data["flight_state"]
        print("[StateEngine] States assigned.")
        return self.data

    def classify_states(self):
        return self.assign_states()