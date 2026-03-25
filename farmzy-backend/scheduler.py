from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import numpy as np
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import get_settings
from database import safe_insert, safe_select, safe_update
from routers.websocket import connection_manager
from services.alert_engine import alert_engine
from services.expert_system import expert_engine
from services.ml_pipeline import model_manager
from services.thingspeak import ingest_latest_readings_for_field

settings = get_settings()


class SchedulerService:
    """Background scheduler for ThingSpeak polling, retraining, and clustering."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._started = False
        alert_engine.set_broadcaster(connection_manager.broadcast)

    async def start(self) -> None:
        if self._started:
            return

        self.scheduler.add_job(self.poll_thingspeak, "interval", seconds=settings.poll_interval_seconds, id="poll_thingspeak")
        self.scheduler.add_job(self.retrain_models, "interval", hours=24, id="retrain_models")
        self.scheduler.add_job(self.cluster_fields, "interval", hours=12, id="cluster_fields")
        self.scheduler.start()
        self._started = True

    async def stop(self) -> None:
        if self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False

    async def poll_thingspeak(self) -> None:
        farms = await safe_select("farms", columns="id,thingspeak_channel_id,thingspeak_read_api_key")

        for farm in farms:
            farm_id = farm["id"]
            channel_id = farm.get("thingspeak_channel_id") or settings.thingspeak_channel_id
            api_key = farm.get("thingspeak_read_api_key") or settings.thingspeak_read_api_key
            if not channel_id or not api_key:
                continue

            fields = await safe_select("fields", columns="id,name", filters=[("eq", "farm_id", farm_id)], limit=1)
            if not fields:
                continue
            field_id = fields[0]["id"]

            try:
                inserted = await ingest_latest_readings_for_field(
                    farm_id=farm_id,
                    field_id=field_id,
                    channel_id=str(channel_id),
                    api_key=str(api_key),
                    num_results=10,
                )
            except Exception:
                continue

            for row in inserted:
                reading = {
                    "nitrogen": row.get("nitrogen"),
                    "phosphorus": row.get("phosphorus"),
                    "potassium": row.get("potassium"),
                    "temperature": row.get("temperature"),
                    "humidity": row.get("humidity"),
                    "ph": row.get("ph"),
                    "gas_ppm": row.get("gas_ppm"),
                    "soil_moisture": row.get("soil_moisture"),
                }

                expert_result = await expert_engine.evaluate(
                    reading,
                    field_id=field_id,
                    sensor_reading_id=row["id"],
                )

                ml_irrigation = model_manager.predict_irrigation(reading)
                target_liters = max(
                    float(expert_result["water_liters"]),
                    float(ml_irrigation["water_requirement_liters"]),
                )

                prediction_row = expert_result.get("prediction_row") or {}
                prediction_id = prediction_row.get("id")
                if prediction_id:
                    await safe_update(
                        "irrigation_predictions",
                        {
                            "water_requirement_liters": round(target_liters, 2),
                            "model_version": f"{prediction_row.get('model_version', 'hybrid_rule_fuzzy_v1')}|{ml_irrigation['model_version']}",
                        },
                        filters=[("eq", "id", prediction_id)],
                    )

                crop = model_manager.recommend_crop(reading)
                crop_rows = await safe_insert(
                    "crop_recommendations",
                    {
                        "field_id": field_id,
                        "sensor_reading_id": row["id"],
                        "top_crop_1": crop["top_3"][0][0] if crop["top_3"] else None,
                        "top_crop_2": crop["top_3"][1][0] if len(crop["top_3"]) > 1 else None,
                        "top_crop_3": crop["top_3"][2][0] if len(crop["top_3"]) > 2 else None,
                        "probabilities": crop["probabilities"],
                        "naive_bayes_confidence": crop["confidence"],
                        "model_version": crop["model_version"],
                        "reasoning_summary": "Recommended using GaussianNB over current NPK and climate profile.",
                    },
                )

                cluster = model_manager.cluster_reading(reading)
                await safe_update(
                    "fields",
                    {
                        "zone_label": cluster["zone_label"],
                        "zone_cluster_id": cluster["cluster_id"],
                    },
                    filters=[("eq", "id", field_id)],
                )

                alerts_created = await alert_engine.evaluate_and_store(
                    farm_id=farm_id,
                    field_id=field_id,
                    expert_alerts=expert_result.get("alerts", []),
                )

                await connection_manager.broadcast(
                    farm_id,
                    {
                        "event": "new_reading",
                        "data": {
                            "reading": row,
                            "prediction": {
                                **(prediction_row or {}),
                                "water_requirement_liters": round(target_liters, 2),
                                "irrigation_decision": expert_result["decision"],
                                "confidence_score": expert_result["confidence"],
                                "rules_fired": expert_result["rules_fired"],
                            },
                            "alerts": alerts_created,
                            "crop": crop_rows[0] if crop_rows else None,
                        },
                    },
                )

    async def retrain_models(self, force: bool = False) -> dict[str, Any]:
        rows = await safe_select("sensor_readings", columns="id", limit=settings.retrain_min_rows + 1)
        if not force and len(rows) < settings.retrain_min_rows:
            return {"status": "skipped", "reason": "insufficient_new_rows"}

        from ml.train import retrain_all_models

        metrics = await asyncio.to_thread(retrain_all_models)

        timestamp = datetime.utcnow().isoformat()
        inserts = []
        for item in metrics:
            inserts.append(
                {
                    "model_type": item["model_type"],
                    "version": item["version"],
                    "accuracy_metric": item["score"],
                    "metric_name": item["metric_name"],
                    "trained_at": timestamp,
                    "training_rows": item.get("training_rows", 0),
                    "artifact_path": item["artifact_path"],
                    "is_active": True,
                    "notes": "Automated retraining job",
                }
            )

        if inserts:
            await safe_insert("model_registry", inserts)

        await model_manager.initialize()
        return {"status": "ok", "models": metrics}

    async def cluster_fields(self) -> dict[str, Any]:
        farms = await safe_select("farms", columns="id")
        kmeans_model = model_manager.models["kmeans"].model
        pca_model = model_manager.models["pca"].model

        for farm in farms:
            farm_id = farm["id"]
            latest_rows = await safe_select("v_latest_readings", columns="*", filters=[("eq", "farm_id", farm_id)])
            if not latest_rows:
                continue

            cluster_labels: dict[str, int] = {}
            vectors: list[list[float]] = []
            for reading in latest_rows:
                cluster = model_manager.cluster_reading(reading)
                field_id = reading["field_id"]
                cluster_labels[field_id] = int(cluster["cluster_id"])
                vectors.append([
                    float(reading.get("nitrogen") or 0),
                    float(reading.get("phosphorus") or 0),
                    float(reading.get("potassium") or 0),
                    float(reading.get("ph") or 7),
                    float(reading.get("soil_moisture") or 0),
                ])

                await safe_update(
                    "fields",
                    {
                        "zone_cluster_id": cluster["cluster_id"],
                        "zone_label": cluster["zone_label"],
                    },
                    filters=[("eq", "id", field_id)],
                )

            centers = kmeans_model.cluster_centers_.tolist() if hasattr(kmeans_model, "cluster_centers_") else []
            explained = pca_model.explained_variance_ratio_.tolist() if hasattr(pca_model, "explained_variance_ratio_") else []
            components = pca_model.components_.tolist() if hasattr(pca_model, "components_") else []
            inertia = float(getattr(kmeans_model, "inertia_", 0.0)) if kmeans_model is not None else 0.0

            await safe_insert(
                "field_zones",
                {
                    "farm_id": farm_id,
                    "run_at": datetime.utcnow().isoformat(),
                    "num_clusters": len(set(cluster_labels.values())),
                    "cluster_centers": centers,
                    "cluster_labels": cluster_labels,
                    "pca_explained_variance": explained,
                    "pca_components": components,
                    "inertia": inertia,
                    "model_version": model_manager.models["kmeans"].version,
                },
            )

        return {"status": "ok"}


scheduler_service = SchedulerService()
