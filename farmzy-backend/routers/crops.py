from fastapi import APIRouter

from database import safe_select

router = APIRouter(tags=["crops"])


@router.get("/api/farms/{farm_id}/crops")
async def farm_crops(farm_id: str, limit: int = 100) -> dict:
    field_rows = await safe_select("fields", columns="id", filters=[("eq", "farm_id", farm_id)])
    field_ids = {row["id"] for row in field_rows}

    rows = await safe_select(
        "crop_recommendations",
        columns="*",
        order_by=("recommended_at", True),
        limit=limit,
    )
    filtered = [row for row in rows if row.get("field_id") in field_ids]
    return {"farm_id": farm_id, "items": filtered}
