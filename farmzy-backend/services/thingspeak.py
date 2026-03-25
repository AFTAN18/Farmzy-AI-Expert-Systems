from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from database import safe_insert, safe_select


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def fetch_latest_readings(channel_id: str, api_key: str, num_results: int = 10) -> list[dict[str, Any]]:
    """Fetch and map latest ThingSpeak feed entries."""
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    params = {"api_key": api_key, "results": num_results}

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    feeds = payload.get("feeds", [])
    mapped: list[dict[str, Any]] = []
    for feed in feeds:
        entry_id = feed.get("entry_id")
        created_at = feed.get("created_at")
        if entry_id is None or created_at is None:
            continue

        mapped.append(
            {
                "thingspeak_entry_id": int(entry_id),
                "recorded_at": datetime.fromisoformat(str(created_at).replace("Z", "+00:00")).isoformat(),
                "nitrogen": _to_float(feed.get("field1")),
                "phosphorus": _to_float(feed.get("field2")),
                "potassium": _to_float(feed.get("field3")),
                "temperature": _to_float(feed.get("field4")),
                "humidity": _to_float(feed.get("field5")),
                "ph": _to_float(feed.get("field6")),
                "gas_ppm": _to_float(feed.get("field7")),
                "soil_moisture": _to_float(feed.get("field8")),
            }
        )

    return mapped


async def ingest_latest_readings_for_field(
    farm_id: str,
    field_id: str,
    channel_id: str,
    api_key: str,
    num_results: int = 10,
) -> list[dict[str, Any]]:
    """Fetch ThingSpeak feeds, dedupe by entry_id, and upsert new rows."""
    feeds = await fetch_latest_readings(channel_id, api_key, num_results=num_results)
    if not feeds:
        return []

    entry_ids = [item["thingspeak_entry_id"] for item in feeds]
    existing = await safe_select(
        "sensor_readings",
        columns="thingspeak_entry_id",
        filters=[("eq", "farm_id", farm_id), ("in", "thingspeak_entry_id", entry_ids)],
    )
    existing_ids = {int(row["thingspeak_entry_id"]) for row in existing if row.get("thingspeak_entry_id") is not None}

    new_rows = []
    for item in feeds:
        if item["thingspeak_entry_id"] in existing_ids:
            continue
        new_rows.append({
            "farm_id": farm_id,
            "field_id": field_id,
            **item,
        })

    if not new_rows:
        return []

    inserted = await safe_insert(
        "sensor_readings",
        new_rows,
        upsert=True,
        on_conflict="farm_id,thingspeak_entry_id",
    )
    return inserted
