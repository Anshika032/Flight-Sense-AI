import os
import time

from dotenv import load_dotenv
from supabase import create_client
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def _create_supabase_client():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


def fetch_live_telemetry():
    empty_columns = [
        "timestamp",
        "altitude",
        "airspeed",
        "pitch",
        "roll",
        "yaw",
        "engine_temp",
        "fuel_level",
        "vertical_speed",
    ]

    supabase = _create_supabase_client()

    if supabase is None:
        return pd.DataFrame(columns=empty_columns)

    try:
        response = (
            supabase.table("telemetry_frames").select("*").order("timestamp", desc=False).execute()
        )
    except Exception:
        return pd.DataFrame(columns=empty_columns)

    if not response.data:
        return pd.DataFrame(columns=empty_columns)

    return pd.DataFrame(response.data)


class FlightDashboard:
    def __init__(
        self,
        dataframe,
        anomalies=None,
        alerts=None,
        timeline=None,
        states=None,
        risk_scores=None,
        timelines=None
    ):
        self.data = dataframe
        self.anomalies = anomalies if anomalies else []
        self.alerts = self._coerce_records(alerts)
        self.timeline = self._coerce_records(
            timelines if timelines is not None else timeline
        )
        self.states = states
        self.risk_scores = risk_scores if risk_scores is not None else []

    def _coerce_records(self, records):
        if records is None:
            return []

        if isinstance(records, pd.DataFrame):
            return records.to_dict(orient="records")

        if isinstance(records, pd.Series):
            return records.tolist()

        return list(records)

    def _latest_record(self):
        if self.data is None or self.data.empty:
            return None

        return self.data.iloc[-1]

    def _latest_metric_value(self, column_name, fallback=None):
        if self.data is not None and column_name in self.data.columns:
            return self.data.iloc[-1][column_name]

        if fallback is not None:
            return fallback

        return None

    def _latest_state_value(self):
        if self.data is not None and "flight_state" in self.data.columns:
            return self.data.iloc[-1]["flight_state"]

        if isinstance(self.states, pd.Series) and not self.states.empty:
            return self.states.iloc[-1]

        if isinstance(self.states, list) and self.states:
            return self.states[-1]

        return None

    def _state_dataframe(self):
        if self.data is not None and "flight_state" in self.data.columns:
            return self.data[["timestamp", "flight_state"]].copy()

        if self.states is None:
            return pd.DataFrame(columns=["timestamp", "flight_state"])

        state_series = self.states
        if isinstance(state_series, list):
            state_series = pd.Series(state_series)

        if self.data is not None and "timestamp" in self.data.columns:
            timestamp_series = self.data["timestamp"].iloc[: len(state_series)]
        else:
            timestamp_series = pd.Series(range(len(state_series)))

        return pd.DataFrame(
            {
                "timestamp": timestamp_series.values,
                "flight_state": state_series.iloc[: len(timestamp_series)].values,
            }
        )

    def _format_numeric(self, value, suffix=""):
        if value is None or pd.isna(value):
            return "--"

        if isinstance(value, (int, float)):
            return f"{value:,.1f}{suffix}"

        return f"{value}{suffix}"

    def _build_incident_report(self):
        latest = self._latest_record()
        report_lines = ["Flight Telemetry Intelligence Platform", ""]
        report_lines.append(f"Telemetry frames: {len(self.data)}")
        report_lines.append(f"Anomalies detected: {len(self.anomalies)}")
        report_lines.append(f"Critical alerts: {len(self.alerts)}")
        report_lines.append(f"Incident timelines: {len(self.timeline)}")

        if latest is not None:
            report_lines.extend([
                "",
                "Latest telemetry snapshot:",
                f"- Timestamp: {latest.get('timestamp', '--')}",
                f"- Altitude: {self._format_numeric(latest.get('altitude'), ' ft')}",
                f"- Airspeed: {self._format_numeric(latest.get('airspeed'), ' kts')}",
                f"- Engine temp: {self._format_numeric(latest.get('engine_temp'), ' C')}",
                f"- Fuel level: {self._format_numeric(latest.get('fuel_level'), ' %')}",
                f"- Risk score: {self._format_numeric(latest.get('risk_score'))}",
            ])

        return "\n".join(report_lines)

    def show_metrics(self):
        st.sidebar.header("Flight Summary")

        st.sidebar.metric(
            "Telemetry Frames",
            len(self.data)
        )

        st.sidebar.metric(
            "Anomalies",
            len(self.anomalies)
        )

        st.sidebar.metric(
            "Critical Alerts",
            len(self.alerts)
        )

        latest_state = self._latest_state_value()
        if latest_state is not None:
            st.sidebar.metric("Current State", latest_state)

    def show_live_snapshot(self):
        latest = self._latest_record()

        if latest is None:
            st.info("No telemetry available.")
            return

        cols = st.columns(5)
        cols[0].metric("Altitude", self._format_numeric(latest.get("altitude"), " ft"))
        cols[1].metric("Airspeed", self._format_numeric(latest.get("airspeed"), " kts"))
        cols[2].metric("Engine Temp", self._format_numeric(latest.get("engine_temp"), " C"))
        cols[3].metric("Fuel Level", self._format_numeric(latest.get("fuel_level"), " %"))
        cols[4].metric("Risk Score", self._format_numeric(latest.get("risk_score")))

    def show_risk_gauge(self):
        latest_risk = self._latest_metric_value("risk_score")

        if latest_risk is None and self.risk_scores:
            latest_risk = self.risk_scores[-1]

        if latest_risk is None:
            return

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=float(latest_risk),
                number={"suffix": "/100"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#f97316"},
                    "steps": [
                        {"range": [0, 35], "color": "#14532d"},
                        {"range": [35, 70], "color": "#854d0e"},
                        {"range": [70, 100], "color": "#7f1d1d"},
                    ],
                },
                title={"text": "Risk Meter"},
            )
        )

        fig.update_layout(height=260, margin={"l": 10, "r": 10, "t": 45, "b": 10})
        st.plotly_chart(fig, use_container_width=True)

    def _has_columns(self, required_columns):
        return (
            self.data is not None and
            not self.data.empty and
            all(column in self.data.columns for column in required_columns)
        )

    def plot_altitude(self):
        if not self._has_columns(["timestamp", "altitude"]):
            st.info("Altitude chart will appear once telemetry is available.")
            return

        fig = px.line(
            self.data,
            x="timestamp",
            y="altitude",
            title="Altitude Timeline"
        )

        if self.anomalies:
            anomaly_data = self.data.iloc[self.anomalies]

            fig.add_scatter(
                x=anomaly_data["timestamp"],
                y=anomaly_data["altitude"],
                mode="markers",
                name="Anomalies"
            )

        st.plotly_chart(fig)

    def plot_engine_temp(self):
        if not self._has_columns(["timestamp", "engine_temp"]):
            st.info("Engine temperature chart will appear once telemetry is available.")
            return

        fig = px.line(
            self.data,
            x="timestamp",
            y="engine_temp",
            title="Engine Temperature"
        )

        st.plotly_chart(fig)

    def plot_risk_score(self):
        if not self._has_columns(["timestamp", "risk_score"]):
            st.info("Risk progression chart will appear once telemetry is available.")
            return

        fig = px.line(
            self.data,
            x="timestamp",
            y="risk_score",
            title="Risk Progression"
        )

        st.plotly_chart(fig)

    def show_flight_states(self):
        st.subheader("Flight State Timeline")

        state_df = self._state_dataframe()

        if state_df.empty:
            st.info("No flight state data available.")
            return

        st.dataframe(state_df)

    def show_alerts(self):
        st.subheader("Operational Alerts")

        if self.alerts:
            alert_df = pd.DataFrame(self.alerts)
            st.dataframe(alert_df)
        else:
            st.info("No active alerts.")

    def show_timeline(self):
        st.subheader("Incident Timeline")

        if self.timeline:
            timeline_df = pd.DataFrame(self.timeline)
            st.dataframe(timeline_df)
        else:
            st.info("No incident timelines available.")

    def show_frame_inspector(self):
        st.subheader("Frame Inspector")

        options = ["Latest telemetry"]
        options.extend(
            [
                f"Alert {idx + 1}: {alert.get('severity', 'UNKNOWN')}"
                for idx, alert in enumerate(self.alerts)
            ]
        )

        selected_option = st.selectbox(
            "Select a telemetry frame",
            options,
            index=0,
        )

        if selected_option == "Latest telemetry":
            latest = self._latest_record()
            if latest is not None:
                st.json(latest.to_dict())
            return

        alert_index = options.index(selected_option) - 1
        st.json(self.alerts[alert_index])

    def show_export_controls(self):
        report = self._build_incident_report()
        st.download_button(
            "Export Incident Report",
            data=report,
            file_name="flight_incident_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    def run(self):
        # Initialize environment and Streamlit UI at runtime (avoid running UI on import)
        load_dotenv()
        st.set_page_config(page_title="Flight Telemetry Dashboard")
        st.title("Flight Telemetry Dashboard V2")

        # Attach autorefresh helper if not present
        if not hasattr(st, "autorefresh"):
            def _autorefresh(interval=5000, key="telemetry_refresh"):
                refresh_state_key = f"{key}_last_run"
                now = time.time()
                last_run = st.session_state.get(refresh_state_key)

                if last_run is not None and (now - last_run) * 1000 >= interval:
                    st.session_state[refresh_state_key] = now
                    st.rerun()

                if last_run is None:
                    st.session_state[refresh_state_key] = now

            st.autorefresh = _autorefresh

        # Fetch live telemetry lazily
        df = fetch_live_telemetry()
        self.data = df

        st.autorefresh(interval=5000, key="telemetry_refresh")
        st.caption(
            "Real-time aerospace telemetry, anomaly intelligence, and predictive risk analytics"
        )

        self.show_metrics()

        if self.data is None or self.data.empty:
            st.warning("No live telemetry found in Supabase yet. The dashboard will refresh automatically.")

        main_col, side_col = st.columns([3, 1], gap="large")

        with main_col:
            self.show_live_snapshot()
            self.show_risk_gauge()
            self.plot_altitude()
            self.plot_engine_temp()
            self.plot_risk_score()
            self.show_flight_states()

        with side_col:
            self.show_alerts()
            self.show_frame_inspector()
            self.show_timeline()
            self.show_export_controls()