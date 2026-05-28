"""
FlightSense AI — Risk Engine
Weighted multi-factor risk scoring (0-100 scale).
Factors: engine_temp, fuel_level, vertical_instability, airspeed_deviation, g_load_proxy
"""


class FlightRiskEngine:
    def __init__(self, dataframe):
        self.data = dataframe.copy()
        # Weights must sum to 1.0
        self.weights = {
            "temp":          0.30,
            "fuel":          0.20,
            "vertical":      0.20,
            "speed_dev":     0.15,
            "temp_rate":     0.15,
        }

    def _score_temp(self, temp):
        # 68°C baseline, 128°C redline
        return min(max((temp - 68) / 60.0, 0), 1.0)

    def _score_fuel(self, fuel):
        # Inverted: lower fuel = higher risk
        return min(max((35 - fuel) / 35.0, 0), 1.0)

    def _score_vertical(self, vs):
        # Anything over 2500 fpm is concerning
        return min(abs(vs) / 2500.0, 1.0)

    def _score_speed_dev(self, spd):
        # Cruise ~480kt; deviation from safe envelope 80-340kt
        if spd < 80:   return min((80 - spd) / 80.0, 1.0)
        if spd > 340:  return min((spd - 340) / 100.0, 1.0)
        return 0.0

    def _score_temp_rate(self, delta):
        # Rapid temp rise is dangerous
        return min(abs(delta) / 8.0, 1.0)

    def calculate_risk_score(self):
        risk_scores = []
        prev_temp   = None

        for _, row in self.data.iterrows():
            temp  = row.get("engine_temp", 68)
            fuel  = row.get("fuel_level", 100)
            vs    = row.get("vertical_speed", 0)
            spd   = row.get("airspeed", 250)
            delta = (temp - prev_temp) if prev_temp is not None else 0
            prev_temp = temp

            raw = (
                self.weights["temp"]      * self._score_temp(temp)      +
                self.weights["fuel"]      * self._score_fuel(fuel)      +
                self.weights["vertical"]  * self._score_vertical(vs)    +
                self.weights["speed_dev"] * self._score_speed_dev(spd)  +
                self.weights["temp_rate"] * self._score_temp_rate(delta)
            )
            risk_scores.append(round(min(raw * 100, 100), 2))

        self.data["risk_score"] = risk_scores
        print("[RiskEngine] Scoring complete.")
        return self.data