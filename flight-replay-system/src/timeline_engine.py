class FlightTimelineEngine:
    def __init__(self, dataframe, anomaly_indices=None):
        self.data = dataframe.copy()
        self.anomaly_indices = anomaly_indices if anomaly_indices else []

    def build_incident_timeline(self, window=3):
        """
        Reconstruct incident sequences around anomalies.
        Shows T-window to T0 progression.
        """
        timelines = []

        for anomaly_idx in self.anomaly_indices:
            start = max(0, anomaly_idx - window)
            end = anomaly_idx + 1

            incident_window = self.data.iloc[start:end].copy()
            incident_window["event_type"] = "normal"

            for i, row_idx in enumerate(incident_window.index):
                steps_from_anomaly = anomaly_idx - row_idx
                if steps_from_anomaly == 0:
                    incident_window.loc[row_idx, "event_type"] = "ANOMALY"
                else:
                    incident_window.loc[
                        row_idx,
                        "event_type"
                    ] = f"T-{steps_from_anomaly}"

            timeline_record = {
                "anomaly_index": anomaly_idx,
                "anomaly_timestamp": self.data.iloc[anomaly_idx]["timestamp"],
                "sequence": incident_window.to_dict(orient="records")
            }

            timelines.append(timeline_record)

        print(f"Reconstructed {len(timelines)} incident timelines.")
        return timelines

    def summarize_timeline(self, timeline):
        """
        Create readable incident narrative.
        """
        anomaly_ts = timeline["anomaly_timestamp"]
        sequence = timeline["sequence"]

        summary = f"\n--- Incident at T={anomaly_ts} ---\n"

        for record in sequence:
            event = record["event_type"]
            ts = record["timestamp"]
            temp = record["engine_temp"]
            speed = record["airspeed"]
            vspeed = record["vertical_speed"]

            summary += (
                f"{event:12} | "
                f"Temp: {temp:6.1f}°C | "
                f"Speed: {speed:6.1f}kts | "
                f"VSpeed: {vspeed:6.1f}ft/min\n"
            )

        return summary
