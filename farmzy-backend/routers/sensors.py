from fastapi import APIRouter, Query

from database import safe_select

router = APIRouter(prefix="/api/farms", tags=["sensors"])


@router.get("/{farm_id}/dashboard")
async def farm_dashboard(farm_id: str) -> dict:
    rows = await safe_select(
        "v_field_dashboard",
        columns="*",
        filters=[("eq", "farm_id", farm_id)],
        order_by=("recorded_at", True),
    )
    return {"farm_id": farm_id, "rows": rows}


@router.get("/{farm_id}/readings")
async def farm_readings(
    farm_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    page: int = Query(default=1, ge=1),
) -> dict:
    offset = (page - 1) * limit
    rows = await safe_select(
        "sensor_readings",
        columns="*",
        filters=[("eq", "farm_id", farm_id)],
        order_by=("recorded_at", True),
        limit=limit,
        offset=offset,
    )
    return {
        "farm_id": farm_id,
        "page": page,
        "limit": limit,
        "count": len(rows),
        "items": rows,
    }
