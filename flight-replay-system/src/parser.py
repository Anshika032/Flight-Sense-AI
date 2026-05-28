import pandas as pd


REQUIRED_COLUMNS = [
    "timestamp",
    "altitude",
    "airspeed",
    "pitch",
    "roll",
    "yaw",
    "engine_temp",
    "fuel_level",
    "vertical_speed"
]


class FlightDataParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None

    def load_csv(self):
        """
        Load telemetry CSV into DataFrame
        """
        try:
            self.data = pd.read_csv(self.file_path)
            print("Flight telemetry loaded successfully.")
            return self.data
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None

    def validate_columns(self):
        """
        Validate required telemetry fields
        """
        missing_columns = [
            col for col in REQUIRED_COLUMNS
            if col not in self.data.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing columns: {missing_columns}"
            )

        print("Telemetry structure validated.")
        return True

    def parse(self):
        """
        Main parser pipeline
        """
        self.load_csv()
        self.validate_columns()
        return self.data