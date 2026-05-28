"""
FlightSense AI — Feature Engineering
Delta, rolling, volatility, and load-proxy features.
"""
import pandas as pd


class FlightFeatureEngineer:
    def __init__(self, dataframe):
        self.data = dataframe.copy()

    def create_delta_features(self):
        for col in ["altitude","airspeed","engine_temp","fuel_level","vertical_speed"]:
            if col in self.data.columns:
                self.data[f"{col}_delta"] = self.data[col].diff()

    def create_rolling_features(self, window=5):
        for col in ["engine_temp","airspeed","altitude"]:
            if col in self.data.columns:
                self.data[f"{col}_roll_mean"] = self.data[col].rolling(window).mean()
                self.data[f"{col}_roll_std"]  = self.data[col].rolling(window).std()

    def create_stability_index(self):
        """Composite instability score per frame."""
        vs  = self.data.get("vertical_speed", pd.Series(0, index=self.data.index))
        spd = self.data.get("airspeed_delta", pd.Series(0, index=self.data.index)).abs()
        self.data["stability_index"] = (vs.abs() / 3000 + spd / 20).clip(0, 1)

    def create_fuel_efficiency(self):
        if "fuel_level_delta" in self.data.columns and "airspeed" in self.data.columns:
            burn = self.data["fuel_level_delta"].abs().replace(0, 1e-6)
            self.data["fuel_efficiency"] = self.data["airspeed"] / burn

    def engineer(self):
        self.create_delta_features()
        self.create_rolling_features()
        self.create_stability_index()
        self.create_fuel_efficiency()
        self.data.fillna(0, inplace=True)
        print("[FeatureEngineer] Pipeline complete.")
        return self.data

    def build_features(self):
        return self.engineer()