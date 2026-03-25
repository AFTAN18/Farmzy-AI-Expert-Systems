from __future__ import annotations

from typing import Any, Awaitable, Callable

from database import safe_insert, safe_select

BroadcastFn = Callable[[str, dict[str, Any]], Awaitable[None]]


class AlertEngine:
    """Creates and broadcasts alerts while preventing duplicate unresolved entries."""

    def __init__(self) -> None:
        self._broadcaster: BroadcastFn | None = None

    def set_broadcaster(self, fn: BroadcastFn) -> None:
        self._broadcaster = fn

    async def _already_open(self, farm_id: str, field_id: str | None, alert_type: str) -> bool:
        filters = [
            ("eq", "farm_id", farm_id),
            ("eq", "alert_type", alert_type),
            ("eq", "is_resolved", False),
        ]
        if field_id:
            filters.append(("eq", "field_id", field_id))

        rows = await safe_select("alerts", columns="id", filters=filters, limit=1)
        return len(rows) > 0

    async def evaluate_and_store(
        self,
        *,
        farm_id: str,
        field_id: str | None,
        expert_alerts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Insert new alerts if unresolved duplicates do not exist."""
        created: list[dict[str, Any]] = []

        for alert in expert_alerts:
            alert_type = str(alert.get("alert_type", "GENERIC_ALERT"))
            if await self._already_open(farm_id, field_id, alert_type):
                continue

            payload = {
                "farm_id": farm_id,
                "field_id": field_id,
                "alert_type": alert_type,
                "severity": alert.get("severity", "warning"),
                "message": alert.get("message", "Automated FARMZY alert."),
                "is_resolved": False,
            }

            inserted = await safe_insert("alerts", payload)
            if inserted:
                created_alert = inserted[0]
                created.append(created_alert)
                if self._broadcaster is not None:
                    await self._broadcaster(
                        farm_id,
                        {
                            "event": "new_alert",
                            "data": created_alert,
                        },
                    )

        return created


alert_engine = AlertEngine()
