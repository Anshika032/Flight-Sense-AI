from parser import FlightDataParser
from cleaner import FlightDataCleaner
from feature_engineering import FlightFeatureEngineer


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

engineer = FlightFeatureEngineer(raw_data)

featured_data = engineer.engineer()

print(featured_data.head())
print(featured_data.columns)
