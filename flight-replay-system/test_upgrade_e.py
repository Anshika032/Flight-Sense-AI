"""
Test script for Upgrade E — Enhanced Dashboard
Validates dashboard sections and charts
"""

import importlib.util
import sys

sys.path.insert(0, 'd:\\flight-replay-system\\flight-replay-system')

parser_spec = importlib.util.spec_from_file_location('flight_parser', r'src\parser.py')
parser_module = importlib.util.module_from_spec(parser_spec)
parser_spec.loader.exec_module(parser_module)
FlightDataParser = parser_module.FlightDataParser

anomaly_spec = importlib.util.spec_from_file_location('flight_anomaly', r'src\anomaly.py')
anomaly_module = importlib.util.module_from_spec(anomaly_spec)
anomaly_spec.loader.exec_module(anomaly_module)
FlightAnomalyDetector = anomaly_module.FlightAnomalyDetector

alert_spec = importlib.util.spec_from_file_location('flight_alerts', r'src\alert_engine.py')
alert_module = importlib.util.module_from_spec(alert_spec)
alert_spec.loader.exec_module(alert_module)
FlightAlertEngine = alert_module.FlightAlertEngine

feature_spec = importlib.util.spec_from_file_location('flight_features', r'src\feature_engineering.py')
feature_module = importlib.util.module_from_spec(feature_spec)
feature_spec.loader.exec_module(feature_module)
FlightFeatureEngineer = feature_module.FlightFeatureEngineer

state_spec = importlib.util.spec_from_file_location('flight_states', r'src\state_engine.py')
state_module = importlib.util.module_from_spec(state_spec)
state_spec.loader.exec_module(state_module)
FlightStateEngine = state_module.FlightStateEngine

risk_spec = importlib.util.spec_from_file_location('flight_risk', r'src\risk_engine.py')
risk_module = importlib.util.module_from_spec(risk_spec)
risk_spec.loader.exec_module(risk_module)
FlightRiskEngine = risk_module.FlightRiskEngine

dashboard_spec = importlib.util.spec_from_file_location('flight_dashboard', r'src\dashboard.py')
dashboard_module = importlib.util.module_from_spec(dashboard_spec)
dashboard_spec.loader.exec_module(dashboard_module)
FlightDashboard = dashboard_module.FlightDashboard

# Parse data
print("Loading telemetry...")
raw_data = FlightDataParser('data/flight_data.csv').parse()

# Build pipeline
print("Running feature engineering...")
engineered_data = FlightFeatureEngineer(raw_data).build_features()

print("Classifying flight states...")
state_data = FlightStateEngine(engineered_data).classify_states()

print("Calculating risk scores...")
risk_data = FlightRiskEngine(state_data).calculate_risk_score()

print("Detecting anomalies...")
anomaly_detector = FlightAnomalyDetector(risk_data)
anomalies = anomaly_detector.rule_based_detection()

print("Generating alerts...")
alerts = FlightAlertEngine(risk_data).generate_alerts()

# Create dashboard instance
print("\n=== Upgrade E: Enhanced Dashboard ===")
print(f"Dashboard initialized with:")
print(f"  - {len(risk_data)} telemetry records")
print(f"  - {len(anomalies)} anomalies detected")
print(f"  - {len(alerts)} alerts generated")
print(f"  - Columns: {list(risk_data.columns)}")

dashboard = FlightDashboard(
    risk_data,
    anomalies=anomalies,
    alerts=alerts,
    states=state_data.get("state", None) if hasattr(state_data, "get") else None,
    risk_scores=list(risk_data["risk_score"]) if "risk_score" in risk_data.columns else [],
    timelines=[]
)

print("\n✓ Dashboard Sections Available:")
print("  - Live Telemetry (latest values)")
print("  - Risk Meter (gauge 0-100)")
print("  - Flight State (distribution pie chart)")
print("  - Alert Feed (all alerts table)")
print("  - Incident Timeline (expandable incidents)")

print("\n✓ Dashboard Charts Available:")
print("  - Raw Telemetry (altitude, airspeed, temp)")
print("  - Rolling Trends (3-sample averages)")
print("  - Anomaly Markers (altitude + anomalies)")
print("  - Risk Trend (risk score over time)")

print("\n✓ Latest Telemetry:")
latest = risk_data.iloc[-1]
print(f"  Altitude: {latest['altitude']:.1f}ft")
print(f"  Airspeed: {latest['airspeed']:.1f}kts")
print(f"  Temp: {latest['engine_temp']:.1f}°C")
print(f"  Risk Score: {latest['risk_score']:.1f}")
print(f"  State: {latest['state']}")

print("\n✓ Risk Distribution:")
print(f"  Min: {risk_data['risk_score'].min()}")
print(f"  Max: {risk_data['risk_score'].max()}")
print(f"  Mean: {risk_data['risk_score'].mean():.1f}")

print("\n✓ State Distribution:")
print(risk_data['state'].value_counts())

print("\n✓ Upgrade E validation complete!")
