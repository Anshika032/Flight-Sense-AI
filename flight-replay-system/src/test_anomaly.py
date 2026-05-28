from parser import FlightDataParser
from cleaner import FlightDataCleaner
from anomaly import FlightAnomalyDetector


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

detector = FlightAnomalyDetector(processed_data)

rule_anomalies = detector.rule_based_detection()
ml_anomalies = detector.ml_based_detection()

print("Rule anomalies:", rule_anomalies)
print("ML anomalies:", ml_anomalies)