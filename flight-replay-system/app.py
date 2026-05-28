from src.parser import FlightDataParser
from src.cleaner import FlightDataCleaner
from src.feature_engineering import FlightFeatureEngineer
from src.state_engine import FlightStateEngine
from src.risk_engine import FlightRiskEngine
from src.anomaly import FlightAnomalyDetector
from src.alert_engine import FlightAlertEngine
from src.timeline_engine import FlightTimelineEngine
from src.dashboard import FlightDashboard
from src.report_generator import FlightReportGenerator


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

engineer = FlightFeatureEngineer(raw_data)
featured_data = engineer.engineer()

state_engine = FlightStateEngine(featured_data)
state_data = state_engine.assign_states()

risk_engine = FlightRiskEngine(state_data)
risk_data = risk_engine.calculate_risk_score()

# Drop non-numeric columns for anomaly detection
numeric_data = risk_data.select_dtypes(include=['number'])
detector = FlightAnomalyDetector(numeric_data)
anomalies = detector.ml_based_detection()

alert_engine = FlightAlertEngine(raw_data)
alerts = alert_engine.generate_alerts()

timeline_engine = FlightTimelineEngine(raw_data, anomaly_indices=anomalies)
timelines = timeline_engine.build_incident_timeline(window=2)

report_generator = FlightReportGenerator(
    risk_data,
    anomalies
)
report_generator.save_report()

dashboard = FlightDashboard(
    risk_data,
    anomalies,
    alerts,
    timelines
)

dashboard.run()