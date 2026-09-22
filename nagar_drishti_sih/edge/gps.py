from __future__ import annotations
import re
import serial


def _nmea_to_decimal(value: str, direction: str) -> float:
    deg_len = 2 if direction in ("N", "S") else 3
    deg = float(value[:deg_len])
    minutes = float(value[deg_len:])
    decimal = deg + minutes / 60.0
    return -decimal if direction in ("S", "W") else decimal


class GPSReader:
    def __init__(self, port: str | None = None, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        if port:
            self.serial = serial.Serial(port, baudrate=baudrate, timeout=1)

    def read(self) -> dict | None:
        if not self.serial:
            return None
        for _ in range(10):
            line = self.serial.readline().decode("ascii", errors="ignore").strip()
            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                parts = line.split(",")
                if len(parts) > 6 and parts[2] == "A":
                    return {
                        "latitude": _nmea_to_decimal(parts[3], parts[4]),
                        "longitude": _nmea_to_decimal(parts[5], parts[6]),
                    }
        return None
