"""
FlightSense AI — Report Generator
Structured incident report with anomaly breakdown and risk summary.
"""
import os
from datetime import datetime, timezone


class FlightReportGenerator:
    def __init__(self, dataframe, anomalies):
        self.data      = dataframe
        self.anomalies = anomalies

    def generate_summary(self):
        latest = self.data.iloc[-1] if not self.data.empty else {}
        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "total_frames":        len(self.data),
            "total_anomalies":     len(self.anomalies),
            "anomaly_indices":     self.anomalies,
            "max_engine_temp":     round(self.data["engine_temp"].max(), 2) if "engine_temp" in self.data else "N/A",
            "min_fuel_level":      round(self.data["fuel_level"].min(), 2)  if "fuel_level"  in self.data else "N/A",
            "max_risk_score":      round(self.data["risk_score"].max(), 2)  if "risk_score"  in self.data else "N/A",
            "avg_risk_score":      round(self.data["risk_score"].mean(), 2) if "risk_score"  in self.data else "N/A",
            "phases_observed":     self.data["phase"].unique().tolist()      if "phase"       in self.data else [],
        }

    def save_report(self, file_path="reports/flight_report.txt"):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        summary = self.generate_summary()
        lines   = ["FlightSense AI — Incident Analysis Report", "=" * 50]
        for k, v in summary.items():
            lines.append(f"{k}: {v}")

        # Anomaly detail block
        if self.anomalies and "engine_temp" in self.data.columns:
            lines += ["", "── Anomaly Frames ──"]
            for idx in self.anomalies[:20]:   # cap at 20
                try:
                    row = self.data.iloc[idx]
                    lines.append(
                        f"  Frame {idx}: ALT={row.get('altitude','?'):.0f}ft "
                        f"TMP={row.get('engine_temp','?'):.1f}°C "
                        f"SPD={row.get('airspeed','?'):.1f}kt "
                        f"RISK={row.get('risk_score','?')}"
                    )
                except Exception:
                    continue

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[ReportGenerator] Saved -> {file_path}")