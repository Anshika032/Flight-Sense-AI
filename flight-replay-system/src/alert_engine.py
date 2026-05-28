"""
FlightSense AI — Alert Engine
MIL-STD-1553 inspired tiered alerting: ADVISORY / CAUTION / WARNING / EMERGENCY
"""
from datetime import datetime, timezone


# Each rule: (field, operator, threshold, severity, code, message)
_RULES = [
    ("engine_temp",    ">", 125, "EMERGENCY", "ENG-001", "ENGINE TEMP REDLINE — IMMEDIATE ACTION"),
    ("engine_temp",    ">", 115, "WARNING",   "ENG-002", "Engine temp high — monitor EGT"),
    ("engine_temp",    ">", 105, "CAUTION",   "ENG-003", "Engine temp elevated"),
    ("fuel_level",     "<",   8, "EMERGENCY", "FUEL-001","FUEL CRITICAL — Divert immediately"),
    ("fuel_level",     "<",  20, "WARNING",   "FUEL-002","Fuel low — begin divert planning"),
    ("fuel_level",     "<",  35, "CAUTION",   "FUEL-003","Fuel below normal reserves"),
    ("airspeed",       ">", 340, "WARNING",   "SPD-001", "VMO exceeded — reduce speed"),
    ("airspeed",       "<",  80, "WARNING",   "SPD-002", "Airspeed low — stall proximity"),
    ("vertical_speed", ">", 3500,"WARNING",   "VS-001",  "Excessive climb rate"),
    ("vertical_speed", "<",-3000,"WARNING",   "VS-002",  "Excessive descent rate — GPWS"),
    ("altitude",       ">",41000,"CAUTION",   "ALT-001", "Above certified ceiling"),
]


class FlightAlertEngine:
    def __init__(self, dataframe):
        self.data = dataframe

    def generate_alerts(self):
        alerts = []
        for _, row in self.data.iterrows():
            for field, op, threshold, severity, code, msg in _RULES:
                val = row.get(field)
                if val is None:
                    continue
                triggered = (op == ">" and val > threshold) or (op == "<" and val < threshold)
                if triggered:
                    alerts.append({
                        "timestamp": row.get("timestamp"),
                        "severity":  severity,
                        "code":      code,
                        "field":     field,
                        "value":     round(float(val), 2),
                        "threshold": threshold,
                        "message":   msg,
                        "phase":     row.get("phase", "UNKNOWN"),
                        "utc":       datetime.now(timezone.utc).isoformat(),
                    })
        print(f"[AlertEngine] {len(alerts)} alerts generated")
        return alerts