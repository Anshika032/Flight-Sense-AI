from parser import FlightDataParser


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

print(data.head())