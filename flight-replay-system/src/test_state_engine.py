from parser import FlightDataParser
from cleaner import FlightDataCleaner
from feature_engineering import FlightFeatureEngineer
from state_engine import FlightStateEngine


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

engineer = FlightFeatureEngineer(raw_data)
featured_data = engineer.engineer()

state_engine = FlightStateEngine(featured_data)
state_data = state_engine.assign_states()

print(
    state_data[
        ["timestamp", "vertical_speed", "engine_temp", "flight_state"]
    ]
)
