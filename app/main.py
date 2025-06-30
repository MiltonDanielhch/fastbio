from fastapi import FastAPI
from app.routers import devices, health, ws
from app.background.tasks import start_background_tasks
import logging
import asyncio

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZKTeco Microservice",
    description="Microservicio para gestión de dispositivos biométricos ZKTeco",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Registrar routers
app.include_router(devices.router)
app.include_router(health.router)
app.include_router(ws.router)

# Iniciar tareas en segundo plano
@app.on_event("startup")
async def startup_event():
    try:
        asyncio.create_task(start_background_tasks())
        logger.info("Tareas en segundo plano programadas")
    except Exception as e:
        logger.error(f"Error al iniciar tareas: {str(e)}")
        raise

# Detener tareas y liberar recursos
@app.on_event("shutdown")
async def shutdown_event():
    try:
        from app.services.zk_service import cleanup_devices
        await cleanup_devices()
        logger.info("Recursos liberados y tareas detenidas")
    except ImportError:
        logger.warning("La función cleanup_devices no está disponible")
    except Exception as e:
        logger.error(f"Error durante el apagado: {str(e)}")