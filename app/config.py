import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

COMPATIBLE_DEVICES = {
    "ZEM500": {"firmware": "Ver 6.21"},
    "ZEM510_TFT": {"firmware": "Ver 6.60"},
    "ZEM600_TFT": {"firmware": "Ver 6.60"},
    "ZEM800_TFT": {"firmware": "Ver 6.60"},
    # ... añadir más según documentación
}

class DeviceInfo:
    def __init__(self, platform: str, firmware_version: str):
        self.platform = platform
        self.firmware_version = firmware_version

def check_compatibility(device_info: DeviceInfo):
    platform = device_info.platform
    firmware = device_info.firmware_version
    
    if platform not in COMPATIBLE_DEVICES:
        return False
    
    expected_firmware = COMPATIBLE_DEVICES[platform]["firmware"]
    return expected_firmware in firmware

class Settings:
    API_KEY = os.getenv("API_KEY", "default-secret-key")
    DEVICE_TIMEOUT = int(os.getenv("DEVICE_TIMEOUT", "5"))
    DEVICE_PORT = int(os.getenv("DEVICE_PORT", "4370"))
    DEVICE_PASSWORD = os.getenv("DEVICE_PASSWORD", "0")
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
    DEVICE_CHECK_INTERVAL = int(os.getenv("DEVICE_CHECK_INTERVAL", "60"))
    RECONNECT_ATTEMPTS = int(os.getenv("RECONNECT_ATTEMPTS", "3"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    def __init__(self):
        devices = os.getenv("KNOWN_DEVICES", "")
        self.KNOWN_DEVICES = [ip.strip() for ip in devices.split(",") if ip.strip()]

settings = Settings()