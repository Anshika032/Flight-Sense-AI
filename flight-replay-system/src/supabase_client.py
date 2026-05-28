import os
import time
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from supabase import create_client, Client


class SupabaseTelemetryClient:
    def __init__(self):
        load_dotenv(
            dotenv_path=Path(__file__).resolve().parent.parent / ".env",
            override=True
        )

        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )

        parsed_url = urlparse(self.url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError(
                "SUPABASE_URL must be a valid https URL"
            )

        self.client: Client = create_client(
            self.url,
            self.key
        )

    def insert_telemetry(self, telemetry_data, retries=3):
        for attempt in range(retries):
            try:
                response = (
                    self.client
                    .table("telemetry_frames")
                    .insert(telemetry_data)
                    .execute()
                )
                return response

            except Exception as e:
                print(f"Supabase insert failed (attempt {attempt+1}): {e}")
                time.sleep(2)

        return None
