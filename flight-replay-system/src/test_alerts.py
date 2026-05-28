from parser import FlightDataParser
from cleaner import FlightDataCleaner
from alert_engine import FlightAlertEngine


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

alert_engine = FlightAlertEngine(raw_data)

alerts = alert_engine.generate_alerts()

for alert in alerts:
    print(alert)