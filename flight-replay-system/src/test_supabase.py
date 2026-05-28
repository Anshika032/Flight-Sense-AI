from supabase_client import SupabaseTelemetryClient


sample_data = {
    "timestamp": 1,
    "altitude": 35000,
    "airspeed": 480,
    "pitch": 2.1,
    "roll": 0.4,
    "yaw": 0.8,
    "engine_temp": 620,
    "fuel_level": 78,
    "vertical_speed": 1200
}


if __name__ == "__main__":
    client = SupabaseTelemetryClient()

    result = client.insert_telemetry(sample_data)

    print("Insert successful")
    print(result)
