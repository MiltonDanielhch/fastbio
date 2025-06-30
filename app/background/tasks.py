import asyncio
import time
import logging
from app.services.zk_service import DeviceConnection
from app.config import settings

logger = logging.getLogger(__name__)
device_status = {}
lock = asyncio.Lock()

async def check_device(ip: str):
    async with lock:
        try:
            device = DeviceConnection(ip)
            info = await asyncio.to_thread(device.get_device_info)
            
            device_status[ip] = {
                "status": "online",
                "info": info,
                "timestamp": time.time()
            }
        except Exception as e:
            device_status[ip] = {
                "status": "offline",
                "error": str(e),
                "timestamp": time.time()
            }

async def monitor_devices():
    while True:
        tasks = []
        for ip in settings.KNOWN_DEVICES:
            if ip:
                tasks.append(asyncio.create_task(check_device(ip)))
        await asyncio.gather(*tasks)
        await asyncio.sleep(settings.DEVICE_CHECK_INTERVAL)

async def start_background_tasks():
    asyncio.create_task(monitor_devices())