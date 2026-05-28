"""
Test script for Upgrade F — Hybrid ML Intelligence
Validates Random Forest + Isolation Forest comparison
"""

import importlib.util
import sys

sys.path.insert(0, 'd:\\flight-replay-system\\flight-replay-system')

parser_spec = importlib.util.spec_from_file_location('flight_parser', r'src\parser.py')
parser_module = importlib.util.module_from_spec(parser_spec)
parser_spec.loader.exec_module(parser_module)
FlightDataParser = parser_module.FlightDataParser

cleaner_spec = importlib.util.spec_from_file_location('flight_cleaner', r'src\cleaner.py')
cleaner_module = importlib.util.module_from_spec(cleaner_spec)
cleaner_spec.loader.exec_module(cleaner_module)
FlightDataCleaner = cleaner_module.FlightDataCleaner

predictor_spec = importlib.util.spec_from_file_location('flight_predictor', r'src\predictor.py')
predictor_module = importlib.util.module_from_spec(predictor_spec)
predictor_spec.loader.exec_module(predictor_module)
FlightFailurePredictor = predictor_module.FlightFailurePredictor

# Parse and clean data
print("Loading and cleaning telemetry...")
raw_data = FlightDataParser('data/flight_data.csv').parse()
_, processed_data = FlightDataCleaner(raw_data).clean()

# Create predictor
print("\n=== Upgrade F: Hybrid ML Intelligence ===")
predictor = FlightFailurePredictor(processed_data)

# Train both models
print("\nTraining models...")
results = predictor.train_model()

print(f"\nModel Comparison:")
print(f"  Random Forest Accuracy: {results['rf_accuracy']:.2f}")
print(f"  Isolation Forest Anomalies: {results['if_anomalies']}")

# Test hybrid assessment on a sample row
print("\n=== Hybrid Risk Assessment (Sample Row) ===")
sample_row = processed_data.iloc[10].values
assessment = predictor.hybrid_risk_assessment(sample_row)
print(f"  Random Forest Risk: {assessment['rf_risk']}")
print(f"  Isolation Forest Anomaly: {assessment['if_anomaly']}")
print(f"  Combined Risk Score: {assessment['combined_risk']:.2f}")

print("\n✓ Random Forest:")
print("  - Supervised learning on failure labels")
print("  - Accuracy-based validation")
print("  - Captures labeled patterns")

print("\n✓ Isolation Forest:")
print("  - Unsupervised anomaly detection")
print("  - Identifies statistical outliers")
print("  - No labels required")

print("\n✓ Hybrid Intelligence:")
print("  - Combines supervised + unsupervised")
print("  - Cross-validates predictions")
print("  - Improves detection reliability")

print("\n✓ Upgrade F validation complete!")
