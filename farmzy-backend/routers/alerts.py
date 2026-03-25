from datetime import datetime

from fastapi import APIRouter, HTTPException

from database import safe_select, safe_update

router = APIRouter(tags=["alerts"])


@router.get("/api/farms/{farm_id}/alerts")
async def farm_alerts(farm_id: str, include_resolved: bool = False) -> dict:
    filters = [("eq", "farm_id", farm_id)]
    if not include_resolved:
        filters.append(("eq", "is_resolved", False))

    rows = await safe_select(
        "alerts",
        columns="*",
        filters=filters,
        order_by=("triggered_at", True),
        limit=500,
    )
    return {"farm_id": farm_id, "items": rows}


@router.post("/api/farms/{farm_id}/alerts/{alert_id}/resolve")
async def resolve_alert(farm_id: str, alert_id: str) -> dict:
    rows = await safe_update(
        "alerts",
        {
            "is_resolved": True,
            "resolved_at": datetime.utcnow().isoformat(),
        },
        filters=[("eq", "id", alert_id), ("eq", "farm_id", farm_id)],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "resolved", "alert": rows[0]}
