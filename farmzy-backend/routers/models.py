from fastapi import APIRouter

from scheduler import scheduler_service
from services.ml_pipeline import model_manager

router = APIRouter(tags=["models"])


@router.post("/api/models/retrain")
async def retrain_models() -> dict:
    return await scheduler_service.retrain_models(force=True)


@router.get("/api/models/status")
async def model_status() -> dict:
    return await model_manager.status()
