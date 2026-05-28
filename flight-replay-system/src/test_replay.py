from parser import FlightDataParser
from cleaner import FlightDataCleaner
from replay import FlightReplayEngine


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

replay_engine = FlightReplayEngine(raw_data)
replay_engine.replay_timeline(delay=0.5)