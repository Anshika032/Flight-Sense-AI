from parser import FlightDataParser
from cleaner import FlightDataCleaner


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

print(raw_data.head())
print(processed_data.head())