from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import alerts, crops, models, predictions, rules, sensors, websocket, zones
from scheduler import scheduler_service
from services.ml_pipeline import model_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await model_manager.initialize()
    await scheduler_service.start()
    try:
        yield
    finally:
        await scheduler_service.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensors.router)
app.include_router(predictions.router)
app.include_router(crops.router)
app.include_router(zones.router)
app.include_router(alerts.router)
app.include_router(models.router)
app.include_router(rules.router)
app.include_router(websocket.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
