from fastapi import APIRouter
from app.background.tasks import device_status
from typing import Dict, Any
import time

router = APIRouter(tags=["health"])

@router.get("/health", response_model=Dict[str, Any])
def health_check():
    if not device_status:
        return {
            "service_status": "running",
            "devices": {
                "message": "Aún no se han verificado dispositivos"
            }
        }
    
    total_devices = len(device_status)
    online_devices = sum(1 for status in device_status.values() if status["status"] == "online")
    offline_devices = total_devices - online_devices
    
    current_time = time.time()
    device_details = {}
    for ip, status in device_status.items():
        last_update = status.get("timestamp", current_time)
        device_details[ip] = {
            "status": status["status"],
            "last_update_seconds": round(current_time - last_update, 1)
        }
    
    return {
        "service_status": "running",
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": offline_devices,
            "details": device_details
        }
    }