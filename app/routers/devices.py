from typing import List
from fastapi import APIRouter, HTTPException, WebSocket, Depends
from app.services import zk_service
from app.dependencies import validate_api_key
from app.models.schemas import AttendanceRecord, User, DeviceInfo
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(validate_api_key)],
    prefix="/devices",
    tags=["devices"]
)

@router.get("/{ip}/attendance", response_model=List[AttendanceRecord])
async def get_device_attendance(ip: str):
    try:
        attendance = await zk_service.get_attendance(ip)
        return attendance
    except Exception as e:
        logger.error(f"Error obteniendo asistencia de {ip}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Error al obtener asistencia: {str(e)}")

@router.get("/{ip}/users", response_model=List[User])
async def get_device_users(ip: str):
    try:
        users = await zk_service.get_users(ip)
        return users
    except Exception as e:
        logger.error(f"Error obteniendo usuarios de {ip}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Error al obtener usuarios: {str(e)}")

@router.get("/{ip}/info", response_model=DeviceInfo)
async def get_device_info(ip: str):
    try:
        device_info = await zk_service.get_device_info(ip)
        return device_info
    except Exception as e:
        logger.error(f"Error obteniendo info de {ip}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Error al obtener info del dispositivo: {str(e)}")

@router.post("/{ip}/test-voice")
async def test_device_voice(ip: str):
    try:
        await zk_service.test_voice(ip)
        return {"message": "Prueba de voz ejecutada"}
    except Exception as e:
        logger.error(f"Error en prueba de voz en {ip}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Error en prueba de voz: {str(e)}")

@router.websocket("/{ip}/realtime")
async def websocket_realtime(websocket: WebSocket, ip: str):
    await websocket.accept()
    try:
        async def send_event(event):
            await websocket.send_json({
                "user_id": event["user_id"],
                "timestamp": event["timestamp"].isoformat(),
                "status": event["status"],
                "punch": event["punch"],
                "device_ip": event["device_ip"]
            })
        
        # Usar timeout configurable (ej: 300 segundos = 5 minutos)
        await zk_service.realtime_events(ip, send_event, timeout=300)
    except Exception as e:
        logger.error(f"Error en WebSocket realtime {ip}: {str(e)}")
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

# @router.post("/{ip}/upload-templates")
# async def upload_templates(ip: str, templates: List[UserTemplate]):
#     try:
#         user_templates = [(user, templates) for user, templates in templates]
#         await asyncio.to_thread(zk_service.save_user_templates, ip, user_templates)
#         return {"message": "Plantillas subidas exitosamente"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))