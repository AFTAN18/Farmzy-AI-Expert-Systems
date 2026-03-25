from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from database import safe_insert, safe_select
from services.fuzzy_logic import fuzzy_controller


ConditionFn = Callable[[dict[str, Any]], bool]
ActionFn = Callable[[dict[str, Any], dict[str, Any]], None]


@dataclass
class EngineRule:
    rule_id: str
    rule_name: str
    priority: int
    specificity: int
    condition: ConditionFn
    action: ActionFn


class ExpertSystemEngine:
    """Forward-chaining production rule engine for irrigation decisions."""

    def __init__(self) -> None:
        self._fallback_rules = self._build_fallback_rules()

    def _build_fallback_rules(self) -> list[EngineRule]:
        def r1_cond(r: dict[str, Any]) -> bool:
            return (r.get("soil_moisture") or 0) < 20 and (r.get("temperature") or 0) > 32

        def r1_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            state["decision"] = "ON"
            state["water_liters"] = max(state["water_liters"], 50.0)
            state["priority_tag"] = "CRITICAL"

        def r2_cond(r: dict[str, Any]) -> bool:
            soil = r.get("soil_moisture") or 0
            return 20 <= soil <= 40 and (r.get("humidity") or 0) < 50

        def r2_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            state["decision"] = "ON"
            state["water_liters"] = max(state["water_liters"], 30.0)
            state["priority_tag"] = "HIGH"

        def r3_cond(r: dict[str, Any]) -> bool:
            return (r.get("soil_moisture") or 0) > 60 and (r.get("humidity") or 0) > 65

        def r3_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            if not state["rules_fired"]:
                state["decision"] = "OFF"
                state["water_liters"] = 0.0
                state["priority_tag"] = "LOW"

        def r4_cond(r: dict[str, Any]) -> bool:
            return (r.get("temperature") or 0) > 35 and (r.get("soil_moisture") or 0) < 50

        def r4_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            state["decision"] = "ON"
            state["water_liters"] += 15.0

        def r5_cond(r: dict[str, Any]) -> bool:
            return (r.get("nitrogen") or 999) < 40 or (r.get("phosphorus") or 999) < 30 or (r.get("potassium") or 999) < 35

        def r5_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            state["alerts"].append(
                {
                    "alert_type": "LOW_NPK",
                    "severity": "warning",
                    "message": "NPK levels indicate soil amendment is needed.",
                }
            )

        def r6_cond(r: dict[str, Any]) -> bool:
            ph_val = r.get("ph") or 7.0
            return ph_val < 5.5 or ph_val > 7.5

        def r6_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            state["alerts"].append(
                {
                    "alert_type": "PH_ANOMALY",
                    "severity": "warning",
                    "message": "pH is outside the optimal crop range.",
                }
            )

        def r7_cond(r: dict[str, Any]) -> bool:
            return (r.get("gas_ppm") or 0) > 400

        def r7_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            state["alerts"].append(
                {
                    "alert_type": "AIR_QUALITY_WARNING",
                    "severity": "warning",
                    "message": "Air quality is degraded for this field.",
                }
            )

        def r8_cond(r: dict[str, Any]) -> bool:
            return (r.get("humidity") or 0) > 85 and (r.get("soil_moisture") or 0) > 70

        def r8_action(state: dict[str, Any], _: dict[str, Any]) -> None:
            state["decision"] = "OFF"
            state["water_liters"] = 0.0
            state["priority_tag"] = "HIGH"

        return [
            EngineRule("RULE_001", "CRITICAL DRY EMERGENCY", 100, 2, r1_cond, r1_action),
            EngineRule("RULE_008", "RAIN INFERENCE", 90, 2, r8_cond, r8_action),
            EngineRule("RULE_002", "MODERATE DRY", 80, 2, r2_cond, r2_action),
            EngineRule("RULE_004", "HIGH TEMPERATURE COMPENSATION", 70, 2, r4_cond, r4_action),
            EngineRule("RULE_005", "NPK DEFICIENCY ALERT", 60, 1, r5_cond, r5_action),
            EngineRule("RULE_006", "PH STRESS", 55, 1, r6_cond, r6_action),
            EngineRule("RULE_007", "AIR QUALITY RISK", 50, 1, r7_cond, r7_action),
            EngineRule("RULE_003", "OPTIMAL CONDITIONS", 40, 2, r3_cond, r3_action),
        ]

    async def _active_rule_overrides(self) -> dict[str, bool]:
        db_rules = await safe_select(
            "expert_system_rules",
            columns="rule_id,is_active",
        )
        return {row["rule_id"]: bool(row.get("is_active", True)) for row in db_rules if row.get("rule_id")}

    @staticmethod
    def _compute_confidence(rules_fired: list[str], fuzzy_liters: float, decision: str) -> float:
        score = 0.42 + 0.08 * len(rules_fired)
        if decision == "ON" and fuzzy_liters > 0:
            score += 0.1
        if decision == "OFF" and fuzzy_liters < 12:
            score += 0.08
        return round(max(0.05, min(score, 0.99)), 3)

    async def evaluate(
        self,
        reading: dict[str, Any],
        *,
        field_id: str,
        sensor_reading_id: str,
        model_version: str = "hybrid_rule_fuzzy_v1",
    ) -> dict[str, Any]:
        """Evaluate a sensor reading and persist irrigation prediction."""
        active_overrides = await self._active_rule_overrides()

        rules = [
            rule
            for rule in self._fallback_rules
            if active_overrides.get(rule.rule_id, True)
        ]
        rules.sort(key=lambda r: (r.priority, r.specificity), reverse=True)

        state: dict[str, Any] = {
            "decision": "OFF",
            "water_liters": 0.0,
            "priority_tag": "LOW",
            "rules_fired": [],
            "alerts": [],
        }

        evaluations: list[dict[str, Any]] = []

        for rule in rules:
            matched = rule.condition(reading)
            snapshot_before = {
                "decision": state["decision"],
                "water_liters": round(float(state["water_liters"]), 2),
                "alerts": len(state["alerts"]),
            }

            if matched:
                rule.action(state, reading)
                state["rules_fired"].append(rule.rule_id)

            evaluations.append(
                {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "matched": matched,
                    "priority": rule.priority,
                    "specificity": rule.specificity,
                    "state_before": snapshot_before,
                    "state_after": {
                        "decision": state["decision"],
                        "water_liters": round(float(state["water_liters"]), 2),
                        "alerts": len(state["alerts"]),
                    },
                }
            )

        fuzzy_liters, fuzzy_activation = fuzzy_controller.infer(
            soil_moisture=float(reading.get("soil_moisture") or 0.0),
            temperature=float(reading.get("temperature") or 0.0),
            humidity=float(reading.get("humidity") or 0.0),
        )

        if state["decision"] == "ON":
            state["water_liters"] = max(float(state["water_liters"]), float(fuzzy_liters))
        elif not state["rules_fired"]:
            state["decision"] = "ON" if fuzzy_liters >= 20 else "OFF"
            state["water_liters"] = float(fuzzy_liters) if state["decision"] == "ON" else 0.0

        if state["decision"] == "OFF":
            state["water_liters"] = 0.0

        max_membership = max(fuzzy_activation.values()) if fuzzy_activation else 0.0
        confidence = self._compute_confidence(state["rules_fired"], fuzzy_liters, state["decision"])

        reasoning_trace = {
            "input": reading,
            "conflict_resolution": "priority_ordering_then_specificity",
            "evaluations": evaluations,
            "fuzzy": {
                "activation": fuzzy_activation,
                "defuzzified_liters": fuzzy_liters,
                "max_membership": round(float(max_membership), 3),
            },
            "final_state": {
                "decision": state["decision"],
                "water_liters": round(float(state["water_liters"]), 2),
                "rules_fired": state["rules_fired"],
                "alerts": state["alerts"],
            },
        }

        prediction_rows = await safe_insert(
            "irrigation_predictions",
            {
                "field_id": field_id,
                "sensor_reading_id": sensor_reading_id,
                "water_requirement_liters": round(float(state["water_liters"]), 2),
                "irrigation_decision": state["decision"],
                "confidence_score": confidence,
                "model_version": model_version,
                "expert_rule_fired": ",".join(state["rules_fired"]) if state["rules_fired"] else None,
                "fuzzy_membership_score": round(float(max_membership), 3),
                "reasoning_trace": reasoning_trace,
            },
        )

        return {
            "decision": state["decision"],
            "water_liters": round(float(state["water_liters"]), 2),
            "rules_fired": state["rules_fired"],
            "reasoning_trace": reasoning_trace,
            "confidence": confidence,
            "alerts": state["alerts"],
            "prediction_row": prediction_rows[0] if prediction_rows else None,
            "fuzzy_membership_score": round(float(max_membership), 3),
        }

    async def list_rules(self) -> list[dict[str, Any]]:
        """Return database rules with fallback defaults if DB is empty."""
        db_rows = await safe_select("expert_system_rules", columns="*")
        if db_rows:
            return db_rows
        return [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "condition_description": "Built-in fallback rule",
                "action_description": "Built-in fallback action",
                "priority": r.priority,
                "is_active": True,
            }
            for r in sorted(self._fallback_rules, key=lambda item: item.priority, reverse=True)
        ]


expert_engine = ExpertSystemEngine()
