from fastapi import APIRouter, HTTPException, Query

from database import safe_select, safe_update
from scheduler import scheduler_service
from schemas.sensor import SyncNowRequest, ThingSpeakConfigUpdate

router = APIRouter(prefix="/api/farms", tags=["sensors"])


@router.get("")
async def list_farms() -> dict:
    rows = await safe_select(
        "farms",
        columns="id,name,location,thingspeak_channel_id,thingspeak_read_api_key,created_at",
        order_by=("created_at", True),
    )
    items = [
        {
            "id": row.get("id"),
            "name": row.get("name"),
            "location": row.get("location"),
            "thingspeak_channel_id": row.get("thingspeak_channel_id"),
            "has_api_key": bool(row.get("thingspeak_read_api_key")),
        }
        for row in rows
    ]
    return {"items": items}


@router.get("/{farm_id}/thingspeak-config")
async def get_farm_thingspeak_config(farm_id: str) -> dict:
    rows = await safe_select(
        "farms",
        columns="id,name,thingspeak_channel_id,thingspeak_read_api_key",
        filters=[("eq", "id", farm_id)],
        limit=1,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Farm not found")

    row = rows[0]
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "thingspeak_channel_id": row.get("thingspeak_channel_id"),
        "thingspeak_read_api_key": row.get("thingspeak_read_api_key"),
        "has_api_key": bool(row.get("thingspeak_read_api_key")),
    }


@router.put("/{farm_id}/thingspeak-config")
async def update_farm_thingspeak_config(farm_id: str, payload: ThingSpeakConfigUpdate) -> dict:
    channel_id = (payload.thingspeak_channel_id or "").strip() or None
    read_api_key = (payload.thingspeak_read_api_key or "").strip() or None

    rows = await safe_update(
        "farms",
        {
            "thingspeak_channel_id": channel_id,
            "thingspeak_read_api_key": read_api_key,
        },
        filters=[("eq", "id", farm_id)],
    )
    updated = rows[0] if rows else None
    if updated is None:
        existing = await safe_select(
            "farms",
            columns="id,thingspeak_channel_id,thingspeak_read_api_key",
            filters=[("eq", "id", farm_id)],
            limit=1,
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Farm not found")
        updated = existing[0]

    return {
        "status": "updated",
        "item": {
            "id": updated.get("id"),
            "thingspeak_channel_id": updated.get("thingspeak_channel_id"),
            "has_api_key": bool(updated.get("thingspeak_read_api_key")),
        },
    }


@router.post("/{farm_id}/sync-now")
async def sync_now(farm_id: str, payload: SyncNowRequest | None = None) -> dict:
    result = await scheduler_service.sync_farm_now(
        farm_id=farm_id,
        num_results=(payload.num_results if payload else 10),
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result)
    return result


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
