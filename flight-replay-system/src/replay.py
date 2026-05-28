import time


class FlightReplayEngine:
    def __init__(self, dataframe):
        self.data = dataframe

    def replay_timeline(self, delay=1):
        """
        Replay telemetry row by row
        """

        print("Starting flight replay...\n")

        for index, row in self.data.iterrows():
            print(f"Time: {row['timestamp']}")
            print(f"Altitude: {row['altitude']}")
            print(f"Airspeed: {row['airspeed']}")
            print(f"Engine Temp: {row['engine_temp']}")
            print(f"Fuel Level: {row['fuel_level']}")
            print(f"Vertical Speed: {row['vertical_speed']}")
            print("-" * 40)

            time.sleep(delay)

        print("Replay complete.")