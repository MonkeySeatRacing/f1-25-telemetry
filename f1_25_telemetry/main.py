"""
Entry point for the F1 25 telemetry listener.
Reads UDP packets and writes them to InfluxDB (or prints JSON if no InfluxDB config).
"""

import json
import sys

from f1_25_telemetry.listener import TelemetryListener


def _get_listener(host: str, port: int) -> TelemetryListener:
    try:
        print(f'Starting F1 25 telemetry listener on {host}:{port}')
        return TelemetryListener(host=host, port=port)
    except OSError as exc:
        print(f'Unable to setup connection: {exc.args[1]}')
        sys.exit(127)


def main():
    try:
        from f1_25_telemetry.settings import load_settings
        from f1_25_telemetry.influxdb import InfluxDBWriter

        telemetry_cfg, influxdb_cfg = load_settings()
        listener = _get_listener(telemetry_cfg.host, telemetry_cfg.port)

        print(f'Writing to InfluxDB: {influxdb_cfg.url} / bucket={influxdb_cfg.bucket}')
        with InfluxDBWriter(
            url=influxdb_cfg.url,
            token=influxdb_cfg.token,
            org=influxdb_cfg.org,
            bucket=influxdb_cfg.bucket,
            batch_size=influxdb_cfg.batch_size,
        ) as writer:
            try:
                while True:
                    packet = listener.get()
                    written = writer.write(packet)
                    if written:
                        print(f'  wrote {written} points ({type(packet).__name__})')
            except KeyboardInterrupt:
                print('\nStop the car, stop the car Checo.')

    except (EnvironmentError, ImportError) as exc:
        # Fall back to JSON stdout if InfluxDB isn't configured or installed
        print(f'[warn] {exc}')
        print('[info] Falling back to JSON stdout mode\n')
        listener = _get_listener('0.0.0.0', 20777)
        try:
            while True:
                packet = listener.get()
                print(json.dumps(packet.to_dict(), indent=2, sort_keys=True))
        except KeyboardInterrupt:
            print('\nStop the car, stop the car Checo.')


if __name__ == '__main__':
    main()
