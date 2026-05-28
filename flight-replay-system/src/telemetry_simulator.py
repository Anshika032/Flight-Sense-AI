"""
FlightSense AI — Telemetry Simulator
Realistic 6-phase flight model: PREFLIGHT → TAKEOFF → CLIMB → CRUISE → DESCENT → LANDING
"""
import random
import time

TOTAL_FUEL = 100.0
PHASE_SEQUENCE = ["PREFLIGHT", "TAKEOFF", "CLIMB", "CRUISE", "DESCENT", "LANDING"]


class FlightTelemetrySimulator:
    def __init__(self):
        self.timestamp   = 0
        self.phase_index = 0
        self.phase       = PHASE_SEQUENCE[0]
        self._phase_tick = 0
        self.state = {
            "altitude": 0.0, "airspeed": 0.0,
            "pitch": 0.0, "roll": 0.0, "yaw": 90.0,
            "engine_temp": 68.0, "fuel_level": TOTAL_FUEL,
            "vertical_speed": 0.0,
        }

    def _n(self, s=1.0): return random.gauss(0, s)
    def _c(self, v, lo, hi): return max(lo, min(hi, v))

    def _step_preflight(self):
        s = self.state
        s["engine_temp"] = self._c(s["engine_temp"] + 1.2 + self._n(0.3), 68, 85)
        s["fuel_level"]  = self._c(s["fuel_level"] - 0.01, 0, TOTAL_FUEL)
        if self._phase_tick >= 8: self._next_phase()

    def _step_takeoff(self):
        s = self.state
        s["airspeed"]    = self._c(s["airspeed"] + 6 + self._n(0.8), 0, 175)
        s["engine_temp"] = self._c(s["engine_temp"] + 2.5 + self._n(0.5), 68, 128)
        s["pitch"]       = self._c(s["pitch"] + 0.6 + self._n(0.2), 0, 15)
        s["fuel_level"]  = self._c(s["fuel_level"] - 0.12, 0, TOTAL_FUEL)
        s["vertical_speed"] = 0.0
        if s["airspeed"] >= 160:
            s["vertical_speed"] = 400
            s["altitude"] += 200
            self._next_phase()

    def _step_climb(self):
        s = self.state
        target = 35000
        ratio  = s["altitude"] / target
        vs     = self._c(2800 * (1 - ratio * 0.6) + self._n(40), 400, 2800)
        s["vertical_speed"] = vs
        s["altitude"]    = self._c(s["altitude"] + vs / 60, 0, target + 300)
        s["airspeed"]    = self._c(s["airspeed"] + self._n(1.2) + 0.4, 160, 310)
        s["pitch"]       = self._c(10 - ratio * 8 + self._n(0.4), 0, 12)
        s["engine_temp"] = self._c(s["engine_temp"] + self._n(1.0) - 0.3, 85, 108)
        s["fuel_level"]  = self._c(s["fuel_level"] - 0.09, 0, TOTAL_FUEL)
        if s["altitude"] >= target - 200: self._next_phase()

    def _step_cruise(self):
        s = self.state
        s["vertical_speed"] = self._n(20)
        s["altitude"]    = self._c(35000 + s["vertical_speed"] / 60 * 5, 34700, 35300)
        s["airspeed"]    = self._c(480 + self._n(3), 460, 500)
        s["pitch"]       = self._c(self._n(0.3), -2, 2)
        s["roll"]        = self._c(self._n(0.2), -3, 3)
        s["engine_temp"] = self._c(s["engine_temp"] + self._n(0.4) - 0.05, 88, 112)
        s["fuel_level"]  = self._c(s["fuel_level"] - 0.06, 0, TOTAL_FUEL)
        if s["fuel_level"] <= 45.0: self._next_phase()

    def _step_descent(self):
        s = self.state
        vs = self._c(-1800 + self._n(60), -2500, -400)
        s["vertical_speed"] = vs
        s["altitude"]    = self._c(s["altitude"] + vs / 60, 0, 35000)
        s["airspeed"]    = self._c(s["airspeed"] - self._n(1) - 0.2, 180, 480)
        s["pitch"]       = self._c(-4 + self._n(0.5), -8, 0)
        s["engine_temp"] = self._c(s["engine_temp"] - 0.4 + self._n(0.3), 72, 108)
        s["fuel_level"]  = self._c(s["fuel_level"] - 0.03, 0, TOTAL_FUEL)
        if s["altitude"] <= 3000: self._next_phase()

    def _step_landing(self):
        s = self.state
        vs = self._c(s["altitude"] * -0.06, -600, -30) if s["altitude"] > 10 else 0
        s["vertical_speed"] = vs
        s["altitude"]    = self._c(s["altitude"] + vs / 60, 0, 3000)
        s["airspeed"]    = self._c(s["airspeed"] - 4 + self._n(0.5), 0, 200)
        s["pitch"]       = self._c(-2 + self._n(0.3), -5, 2)
        s["engine_temp"] = self._c(s["engine_temp"] - 1.0 + self._n(0.2), 65, 98)
        s["fuel_level"]  = self._c(s["fuel_level"] - 0.02, 0, TOTAL_FUEL)
        if s["altitude"] <= 0 and s["airspeed"] <= 0:
            self._reset_flight()

    _PHASE_FN = {
        "PREFLIGHT": _step_preflight, "TAKEOFF": _step_takeoff,
        "CLIMB": _step_climb,         "CRUISE":  _step_cruise,
        "DESCENT": _step_descent,     "LANDING": _step_landing,
    }

    def _next_phase(self):
        self.phase_index = (self.phase_index + 1) % len(PHASE_SEQUENCE)
        self.phase = PHASE_SEQUENCE[self.phase_index]
        self._phase_tick = 0

    def _reset_flight(self):
        self.phase_index = 0
        self.phase = PHASE_SEQUENCE[0]
        self._phase_tick = 0
        s = self.state
        s["altitude"] = s["airspeed"] = s["vertical_speed"] = 0.0
        s["pitch"] = s["roll"] = 0.0
        s["engine_temp"] = 68.0
        s["fuel_level"]  = TOTAL_FUEL

    def generate_next_frame(self):
        self.timestamp   += 1
        self._phase_tick += 1
        self._PHASE_FN[self.phase](self)
        self.state["yaw"] = (self.state["yaw"] + self._n(0.1)) % 360
        return {"timestamp": self.timestamp, "phase": self.phase,
                **{k: round(v, 2) for k, v in self.state.items()}}

    def inject_anomaly(self, kind="engine_overheat"):
        s = self.state
        if   kind == "engine_overheat": s["engine_temp"] += 28
        elif kind == "fuel_leak":       s["fuel_level"]   = max(0, s["fuel_level"] - 15)
        elif kind == "turbulence":
            s["vertical_speed"] += random.choice([-1, 1]) * random.randint(800, 1400)
            s["roll"]           += random.uniform(-12, 12)
        elif kind == "sensor_fail":     s["airspeed"] = -1

    def run_stream(self, frames=60):
        for i in range(frames):
            if i == 15: self.inject_anomaly("turbulence")
            if i == 30: self.inject_anomaly("engine_overheat")
            print(self.generate_next_frame())
            time.sleep(1)


if __name__ == "__main__":
    FlightTelemetrySimulator().run_stream()