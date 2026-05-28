"""
FlightSense AI — Anomaly Detector
Hybrid: rule-based (raw values) + ML Isolation Forest (pattern-based).
"""
import pandas as pd
from sklearn.ensemble import IsolationForest


# Rule thresholds operate on RAW (un-normalized) telemetry
_RULES = [
    ("engine_temp",    ">", 120),
    ("engine_temp",    "<",  40),
    ("fuel_level",     "<",  10),
    ("vertical_speed", ">", 3200),
    ("vertical_speed", "<",-3000),
    ("airspeed",       ">", 340),
    ("airspeed",       "<",  60),
]


class FlightAnomalyDetector:
    def __init__(self, dataframe):
        self.data  = dataframe.copy()
        self.model = IsolationForest(contamination=0.08, random_state=42, n_jobs=-1)

    def rule_based_detection(self):
        anomalies = set()
        for field, op, threshold in _RULES:
            if field not in self.data.columns:
                continue
            if op == ">":
                mask = self.data[field] > threshold
            else:
                mask = self.data[field] < threshold
            anomalies.update(self.data[mask].index.tolist())
        result = sorted(anomalies)
        print(f"[AnomalyDetector] Rule-based: {len(result)} anomalies")
        return result

    def ml_based_detection(self):
        numeric = self.data.select_dtypes(include="number")
        preds   = self.model.fit_predict(numeric)
        result  = [i for i, p in enumerate(preds) if p == -1]
        print(f"[AnomalyDetector] ML-based: {len(result)} anomalies")
        return result

    def combined_detection(self):
        """Union of rule-based indices and ML indices."""
        rule_set = set(self.rule_based_detection())
        ml_set   = set(self.ml_based_detection())
        combined = sorted(rule_set | ml_set)
        print(f"[AnomalyDetector] Combined: {len(combined)} anomalies")
        return combined