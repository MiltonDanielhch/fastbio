from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class AttendanceRecord(BaseModel):
    user_id: str
    timestamp: datetime
    status: int
    punch: int

class User(BaseModel):
    uid: int
    user_id: str
    name: str
    privilege: str
    password: str
    group_id: str

class DeviceInfo(BaseModel):
    firmware_version: str
    device_name: str
    serial_number: str
    mac_address: str
    platform: str
    device_time: str

# Añade este nuevo modelo
class UserTemplate(BaseModel):
    user_id: str
    finger_index: int
    template_data: bytes