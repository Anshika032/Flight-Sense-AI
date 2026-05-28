"""
FlightSense AI — Data Cleaner
Null removal, dedup, physical bounds enforcement, min-max normalization.
"""
import pandas as pd

# Physical hard limits per parameter
_BOUNDS = {
    "altitude":       (0,    55000),
    "airspeed":       (0,    600),
    "engine_temp":    (40,   130),
    "fuel_level":     (0,    100),
    "vertical_speed": (-4000,4000),
    "pitch":          (-90,  90),
    "roll":           (-180, 180),
}


class FlightDataCleaner:
    def __init__(self, dataframe):
        self.raw_data       = dataframe.copy()
        self.processed_data = dataframe.copy()

    def remove_nulls(self):
        before = len(self.processed_data)
        self.processed_data.dropna(inplace=True)
        print(f"[Cleaner] Removed {before - len(self.processed_data)} null rows")

    def remove_duplicates(self):
        before = len(self.processed_data)
        self.processed_data.drop_duplicates(inplace=True)
        print(f"[Cleaner] Removed {before - len(self.processed_data)} duplicate rows")

    def enforce_physical_bounds(self):
        """Clip values to physically possible ranges."""
        for col, (lo, hi) in _BOUNDS.items():
            if col in self.processed_data.columns:
                self.processed_data[col] = self.processed_data[col].clip(lo, hi)
        print("[Cleaner] Physical bounds enforced")

    def normalize_columns(self):
        numeric = self.processed_data.select_dtypes(include="number").columns
        for col in numeric:
            lo, hi = self.processed_data[col].min(), self.processed_data[col].max()
            if hi != lo:
                self.processed_data[col] = (self.processed_data[col] - lo) / (hi - lo)
        print("[Cleaner] Normalization complete")

    def clean(self):
        self.remove_nulls()
        self.remove_duplicates()
        self.enforce_physical_bounds()
        self.normalize_columns()
        return self.raw_data, self.processed_data