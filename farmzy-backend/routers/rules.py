from fastapi import APIRouter, HTTPException

from database import safe_insert, safe_select, safe_update
from schemas.prediction import RulePayload
from services.expert_system import expert_engine

router = APIRouter(tags=["rules"])


@router.get("/api/expert-system/rules")
async def list_rules() -> dict:
    rules = await expert_engine.list_rules()
    return {"items": rules}


@router.post("/api/expert-system/rules")
async def create_rule(payload: RulePayload) -> dict:
    rows = await safe_insert(
        "expert_system_rules",
        payload.model_dump(),
        upsert=True,
        on_conflict="rule_id",
    )
    if not rows:
        raise HTTPException(status_code=400, detail="Rule could not be created")
    return {"item": rows[0]}


@router.put("/api/expert-system/rules/{rule_id}")
async def update_rule(rule_id: str, payload: RulePayload) -> dict:
    existing = await safe_select(
        "expert_system_rules",
        columns="id",
        filters=[("eq", "rule_id", rule_id)],
        limit=1,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")

    rows = await safe_update(
        "expert_system_rules",
        payload.model_dump(),
        filters=[("eq", "rule_id", rule_id)],
    )
    return {"item": rows[0] if rows else None}
