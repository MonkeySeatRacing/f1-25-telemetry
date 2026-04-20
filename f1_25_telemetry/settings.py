"""
Configuration loader for F1 25 telemetry.

Settings are read from environment variables, with .env file support via python-dotenv.
Copy .env.example to .env and fill in your values — never commit .env to version control.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class TelemetrySettings:
    host: str = field(default_factory=lambda: os.getenv("TELEMETRY_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("TELEMETRY_PORT", "20777")))


@dataclass
class InfluxDBSettings:
    url: str = field(default_factory=lambda: os.getenv("INFLUXDB_URL", ""))
    token: str = field(default_factory=lambda: os.getenv("INFLUXDB_TOKEN", ""))
    org: str = field(default_factory=lambda: os.getenv("INFLUXDB_ORG", ""))
    bucket: str = field(default_factory=lambda: os.getenv("INFLUXDB_BUCKET", "f1-telemetry"))
    batch_size: int = field(default_factory=lambda: int(os.getenv("INFLUXDB_BATCH_SIZE", "500")))

    def validate(self) -> None:
        missing = [
            name for name, val in [
                ("INFLUXDB_URL", self.url),
                ("INFLUXDB_TOKEN", self.token),
                ("INFLUXDB_ORG", self.org),
            ]
            if not val
        ]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Copy .env.example to .env and fill in the values."
            )


def load_settings() -> tuple[TelemetrySettings, InfluxDBSettings]:
    telemetry = TelemetrySettings()
    influxdb = InfluxDBSettings()
    influxdb.validate()
    return telemetry, influxdb
