from fastapi import APIRouter

from database import safe_select

router = APIRouter(tags=["predictions"])


@router.get("/api/farms/{farm_id}/predictions")
async def farm_predictions(farm_id: str, limit: int = 100) -> dict:
    rows = await safe_select(
        "irrigation_predictions",
        columns="id,field_id,sensor_reading_id,predicted_at,water_requirement_liters,irrigation_decision,confidence_score,model_version,expert_rule_fired,fuzzy_membership_score,reasoning_trace",
        order_by=("predicted_at", True),
        limit=limit,
    )
    if farm_id:
        field_rows = await safe_select("fields", columns="id", filters=[("eq", "farm_id", farm_id)])
        field_ids = {row["id"] for row in field_rows}
        rows = [item for item in rows if item.get("field_id") in field_ids]
    return {"farm_id": farm_id, "items": rows}


@router.get("/api/expert-system/explain/{reading_id}")
async def explain_prediction(reading_id: str) -> dict:
    rows = await safe_select(
        "irrigation_predictions",
        columns="*",
        filters=[("eq", "sensor_reading_id", reading_id)],
        order_by=("predicted_at", True),
        limit=1,
    )
    return {"reading_id": reading_id, "explanation": rows[0] if rows else None}
