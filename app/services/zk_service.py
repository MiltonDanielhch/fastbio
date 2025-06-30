# app/services/zk_service.py
from zk import ZK, const
from zk.exception import ZKError
import asyncio
from app.config import settings
from app.utils.concurrent import executor
from fastapi import HTTPException
from app.models.schemas import AttendanceRecord, User, DeviceInfo
from datetime import datetime
import logging
from typing import List, Callable, Dict, Any, Optional
import socket
import time

logger = logging.getLogger(__name__)

# Manejo de conexiones activas para limpieza
active_connections = []

class DeviceConnection:
    def __init__(self, ip: str, password: Optional[str] = None):
        """Inicializa la conexión con el dispositivo"""
        self.ip = ip
        self.password = password or settings.DEVICE_PASSWORD
        self.zk = ZK(
            self.ip,
            port=settings.DEVICE_PORT,
            timeout=settings.DEVICE_TIMEOUT,
            password=self.password,
            ommit_ping=True,
            verbose=settings.DEBUG
        )
        self.conn = None
        logger.debug(f"DeviceConnection creado para {self.ip}")
        active_connections.append(self)

    def connect(self, retries: int = 3) -> None:
        """Establece conexión con el dispositivo con reintentos"""
        for attempt in range(retries):
            try:
                if not self.conn:
                    logger.info(f"Conectando a dispositivo {self.ip} (intento {attempt+1}/{retries})")
                    self.conn = self.zk.connect()
                    logger.info(f"Conexión exitosa a {self.ip}")
                return
            
            except (ZKError, socket.error, socket.timeout) as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Error de conexión, reintentando en {wait_time} segundos...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error de conexión en {self.ip}: {str(e)}")
                    raise ConnectionError(f"Error de conexión: {str(e)}")
            
            except Exception as e:
                logger.exception(f"Error inesperado en conexión: {str(e)}")
                raise

    def disconnect(self) -> None:
        """Cierra la conexión y limpia recursos"""
        if self.conn:
            try:
                logger.debug(f"Desconectando de {self.ip}")
                self.conn.disconnect()
            except Exception as e:
                logger.warning(f"Error desconectando {self.ip}: {str(e)}")
            finally:
                self.conn = None
        
        if self in active_connections:
            active_connections.remove(self)

    def disable_device(self) -> None:
        """Deshabilita el dispositivo para operaciones seguras"""
        if self.conn:
            logger.debug(f"Deshabilitando dispositivo {self.ip}")
            self.conn.disable_device()

    def enable_device(self) -> None:
        """Habilita el dispositivo nuevamente"""
        if self.conn:
            logger.debug(f"Habilitando dispositivo {self.ip}")
            self.conn.enable_device()

    def get_users(self) -> List[User]:
        """Obtiene todos los usuarios del dispositivo"""
        try:
            self.connect()
            users = self.conn.get_users()
            return [
                User(
                    uid=user.uid,
                    user_id=user.user_id,
                    name=user.name,
                    privilege="Admin" if user.privilege == const.USER_ADMIN else "User",
                    password=user.password,
                    group_id=user.group_id
                )
                for user in users
            ]
        except Exception as e:
            logger.error(f"Error obteniendo usuarios en {self.ip}: {str(e)}")
            raise
        finally:
            self.disconnect()

    def get_attendance(self) -> List[AttendanceRecord]:
        """Obtiene registros de asistencia"""
        try:
            self.connect()
            attendance = self.conn.get_attendance()
            return [
                AttendanceRecord(
                    user_id=record.user_id,
                    timestamp=record.timestamp,
                    status=record.status,
                    punch=record.punch
                )
                for record in attendance
            ]
        except Exception as e:
            logger.error(f"Error obteniendo asistencia en {self.ip}: {str(e)}")
            raise
        finally:
            self.disconnect()

    def get_device_info(self) -> DeviceInfo:
        """Obtiene información detallada del dispositivo"""
        try:
            self.connect()
            return DeviceInfo(
                firmware_version=self.conn.get_firmware_version(),
                device_name=self.conn.get_device_name(),
                serial_number=self.conn.get_serialnumber(),
                mac_address=self.conn.get_mac(),
                platform=self.conn.get_platform(),
                device_time=str(self.conn.get_time())
            )
        except Exception as e:
            logger.error(f"Error obteniendo info de {self.ip}: {str(e)}")
            raise
        finally:
            self.disconnect()

    def test_voice(self, index: int = 0) -> None:
        """Reproduce un mensaje de voz (0: 'Thank You')"""
        try:
            self.connect()
            self.conn.test_voice(index=index)
        except Exception as e:
            logger.error(f"Error en prueba de voz: {str(e)}")
            raise
        finally:
            self.disconnect()

    def live_capture(self, callback: Callable[[Dict[str, Any]], None], timeout: int = 30) -> None:
        """Captura eventos en tiempo real con manejo de timeout"""
        try:
            self.connect()
            start_time = datetime.now()
            logger.info(f"Iniciando captura en vivo en {self.ip} (timeout: {timeout}s)")
            
            for attendance in self.conn.live_capture():
                if (datetime.now() - start_time).total_seconds() > timeout:
                    logger.info(f"Timeout alcanzado en {self.ip}")
                    break
                    
                if attendance:
                    event_data = {
                        "user_id": attendance.user_id,
                        "timestamp": attendance.timestamp,
                        "status": attendance.status,
                        "punch": attendance.punch,
                        "device_ip": self.ip
                    }
                    try:
                        callback(event_data)
                    except Exception as e:
                        logger.error(f"Error en callback: {str(e)}")
        except Exception as e:
            logger.error(f"Error en captura en vivo en {self.ip}: {str(e)}")
            raise RuntimeError(f"Error en captura en vivo: {str(e)}")
        finally:
            self.disconnect()

    def save_user_templates(self, user_templates: List[tuple]) -> None:
        """Guarda múltiples plantillas a alta velocidad"""
        try:
            self.connect()
            self.conn.save_user_template(user_templates)
        finally:
            self.disconnect()

async def with_device(ip: str, operation: Callable, password: Optional[str] = None):
    """Contexto seguro para operaciones con el dispositivo"""
    device = DeviceConnection(ip, password)
    loop = asyncio.get_event_loop()
    try:
        # Conectar y deshabilitar
        await loop.run_in_executor(executor, device.connect)
        await loop.run_in_executor(executor, device.disable_device)
        
        # Ejecutar operación
        result = await loop.run_in_executor(executor, operation, device)
        return result
    except ZKError as e:
        logger.exception(f"Error específico ZK en dispositivo {ip}")
        raise HTTPException(status_code=503, detail=f"Error ZK: {str(e)}")
    except Exception as e:
        logger.exception(f"Error en operación con dispositivo {ip}")
        raise HTTPException(status_code=503, detail=f"Error en dispositivo: {str(e)}")
    finally:
        # Habilitar y desconectar
        if device.conn:
            await loop.run_in_executor(executor, device.enable_device)
            await loop.run_in_executor(executor, device.disconnect)

async def get_attendance(ip: str, password: Optional[str] = None) -> List[AttendanceRecord]:
    """Obtiene registros de asistencia de forma asíncrona"""
    def operation(device):
        return device.get_attendance()
    return await with_device(ip, operation, password)

async def get_users(ip: str, password: Optional[str] = None) -> List[User]:
    """Obtiene usuarios de forma asíncrona"""
    def operation(device):
        return device.get_users()
    return await with_device(ip, operation, password)

async def get_device_info(ip: str, password: Optional[str] = None) -> DeviceInfo:
    """Obtiene información del dispositivo de forma asíncrona"""
    def operation(device):
        return device.get_device_info()
    return await with_device(ip, operation, password)

async def test_voice(ip: str, password: Optional[str] = None):
    """Prueba de voz asíncrona"""
    def operation(device):
        device.test_voice()
    return await with_device(ip, operation, password)

async def realtime_events(ip: str, callback: Callable, password: Optional[str] = None, timeout: int = 30):
    """Maneja eventos en tiempo real usando live_capture()"""
    loop = asyncio.get_event_loop()
    
    # Definir callback seguro
    def safe_callback(event):
        asyncio.run_coroutine_threadsafe(callback(event), loop)
    
    def operation(device):
        device.live_capture(safe_callback, timeout)
    
    return await with_device(ip, operation, password)

async def upload_templates(ip: str, user_templates: List[tuple], password: Optional[str] = None):
    """Sube plantillas de huellas a alta velocidad"""
    def operation(device):
        device.save_user_templates(user_templates)
    return await with_device(ip, operation, password)

async def cleanup_devices():
    """Cierra todas las conexiones activas"""
    for device in active_connections[:]:
        try:
            device.disconnect()
            logger.info(f"Conexión cerrada: {device.ip}")
        except Exception as e:
            logger.error(f"Error cerrando conexión {device.ip}: {str(e)}")
    active_connections.clear()
    logger.info("Todas las conexiones de dispositivos cerradas")