from parser import FlightDataParser
from cleaner import FlightDataCleaner
from predictor import FlightFailurePredictor


parser = FlightDataParser("data/flight_data.csv")
data = parser.parse()

cleaner = FlightDataCleaner(data)
raw_data, processed_data = cleaner.clean()

predictor = FlightFailurePredictor(processed_data)

predictor.train_model()