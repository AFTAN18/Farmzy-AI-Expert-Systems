from fastapi import APIRouter

from database import safe_select

router = APIRouter(tags=["zones"])


@router.get("/api/farms/{farm_id}/zones")
async def farm_zones(farm_id: str) -> dict:
    rows = await safe_select(
        "field_zones",
        columns="*",
        filters=[("eq", "farm_id", farm_id)],
        order_by=("run_at", True),
        limit=1,
    )
    latest = rows[0] if rows else None

    field_rows = await safe_select(
        "fields",
        columns="id,name,zone_label,zone_cluster_id",
        filters=[("eq", "farm_id", farm_id)],
    )

    return {
        "farm_id": farm_id,
        "latest": latest,
        "fields": field_rows,
    }
