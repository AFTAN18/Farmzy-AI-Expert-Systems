import asyncio
from typing import Any

from supabase import Client, create_client

from config import get_settings

settings = get_settings()


def _create_supabase_client() -> Client | None:
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_service_key)


supabase: Client | None = _create_supabase_client()


async def run_query(query_builder: Any) -> Any:
    """Execute a Supabase query in a worker thread."""
    return await asyncio.to_thread(query_builder.execute)


async def safe_select(
    table: str,
    columns: str = "*",
    *,
    filters: list[tuple[str, str, Any]] | None = None,
    order_by: tuple[str, bool] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict[str, Any]]:
    """Read rows from a table, returning an empty list when DB is unavailable."""
    if supabase is None:
        return []

    query = supabase.table(table).select(columns)

    if filters:
        for op, key, value in filters:
            if op == "eq":
                query = query.eq(key, value)
            elif op == "neq":
                query = query.neq(key, value)
            elif op == "gt":
                query = query.gt(key, value)
            elif op == "gte":
                query = query.gte(key, value)
            elif op == "lt":
                query = query.lt(key, value)
            elif op == "lte":
                query = query.lte(key, value)
            elif op == "in":
                query = query.in_(key, value)

    if order_by:
        query = query.order(order_by[0], desc=order_by[1])
    if limit:
        query = query.limit(limit)
    if offset is not None:
        query = query.range(offset, offset + (limit or 100) - 1)

    response = await run_query(query)
    return response.data or []


async def safe_insert(
    table: str,
    payload: dict[str, Any] | list[dict[str, Any]],
    *,
    upsert: bool = False,
    on_conflict: str | None = None,
) -> list[dict[str, Any]]:
    """Insert rows and return inserted data or an empty list when DB is unavailable."""
    if supabase is None:
        return []

    query = supabase.table(table).upsert(payload, on_conflict=on_conflict) if upsert else supabase.table(table).insert(payload)
    response = await run_query(query)
    return response.data or []


async def safe_update(
    table: str,
    payload: dict[str, Any],
    *,
    filters: list[tuple[str, str, Any]],
) -> list[dict[str, Any]]:
    """Update rows and return changed data."""
    if supabase is None:
        return []

    query = supabase.table(table).update(payload)
    for op, key, value in filters:
        if op == "eq":
            query = query.eq(key, value)
        elif op == "is":
            query = query.is_(key, value)

    response = await run_query(query)
    return response.data or []
