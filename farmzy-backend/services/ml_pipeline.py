from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.base import BaseEstimator

from config import get_settings
from database import safe_select

settings = get_settings()


@dataclass
class ModelState:
    model: BaseEstimator | None = None
    version: str | None = None
    artifact_path: str | None = None
    metric_name: str | None = None
    metric_value: float | None = None


@dataclass
class ModelManager:
    """Loads and serves FARMZY ML models with lightweight registry sync."""

    models: dict[str, ModelState] = field(default_factory=lambda: {
        "linear_regression": ModelState(),
        "naive_bayes": ModelState(),
        "kmeans": ModelState(),
        "pca": ModelState(),
    })
    label_encoder: Any | None = None

    async def initialize(self) -> None:
        self._load_local_defaults()
        await self.refresh_if_newer()

    def _artifacts_dir(self) -> Path:
        return Path(settings.model_artifacts_dir)

    def _load_model_file(self, filename: str) -> Any | None:
        path = self._artifacts_dir() / filename
        if path.exists():
            return joblib.load(path)
        if path.suffix == ".joblib":
            pkl_path = path.with_suffix(".pkl")
            if pkl_path.exists():
                return joblib.load(pkl_path)
        return None

    def _load_local_defaults(self) -> None:
        default_map = {
            "linear_regression": "lr_irrigation_v1.joblib",
            "naive_bayes": "nb_crop_v1.joblib",
            "kmeans": "kmeans_zones_v1.joblib",
            "pca": "pca_sensor_v1.joblib",
        }

        for model_type, filename in default_map.items():
            model = self._load_model_file(filename)
            if model is None:
                continue
            self.models[model_type].model = model
            self.models[model_type].version = "v1"
            self.models[model_type].artifact_path = str(self._artifacts_dir() / filename)

        label_encoder = self._load_model_file("label_encoder.joblib")
        if label_encoder is not None:
            self.label_encoder = label_encoder

    async def refresh_if_newer(self) -> None:
        for model_type in self.models:
            rows = await safe_select(
                "model_registry",
                columns="model_type,version,accuracy_metric,metric_name,artifact_path,trained_at",
                filters=[("eq", "model_type", model_type), ("eq", "is_active", True)],
                order_by=("trained_at", True),
                limit=1,
            )
            if not rows:
                continue
            latest = rows[0]
            state = self.models[model_type]
            if latest.get("version") == state.version:
                continue

            artifact = latest.get("artifact_path")
            if artifact:
                artifact_path = Path(artifact)
                if not artifact_path.is_absolute():
                    artifact_path = Path(os.getcwd()) / artifact
                if artifact_path.exists():
                    state.model = joblib.load(artifact_path)
                    state.version = latest.get("version")
                    state.artifact_path = str(artifact_path)
                    state.metric_name = latest.get("metric_name")
                    state.metric_value = latest.get("accuracy_metric")

    def predict_irrigation(self, reading: dict[str, Any]) -> dict[str, Any]:
        model = self.models["linear_regression"].model
        features = np.array(
            [[
                float(reading.get("soil_moisture") or 0),
                float(reading.get("temperature") or 0),
                float(reading.get("humidity") or 0),
                float(reading.get("nitrogen") or 0),
                float(reading.get("phosphorus") or 0),
                float(reading.get("potassium") or 0),
                float(reading.get("ph") or 7),
            ]],
            dtype=float,
        )

        if model is None:
            fallback = max(0.0, (35.0 - float(reading.get("soil_moisture") or 0)) * 1.2)
            return {
                "water_requirement_liters": round(fallback, 2),
                "model_version": "fallback",
            }

        prediction = float(model.predict(features)[0])
        return {
            "water_requirement_liters": round(max(0.0, prediction), 2),
            "model_version": self.models["linear_regression"].version or "unknown",
        }

    def recommend_crop(self, reading: dict[str, Any]) -> dict[str, Any]:
        model = self.models["naive_bayes"].model
        features = np.array(
            [[
                float(reading.get("nitrogen") or 0),
                float(reading.get("phosphorus") or 0),
                float(reading.get("potassium") or 0),
                float(reading.get("temperature") or 0),
                float(reading.get("humidity") or 0),
                float(reading.get("ph") or 7),
                float(reading.get("gas_ppm") or 100),
            ]],
            dtype=float,
        )

        if model is None:
            fallback = [("Rice", 0.55), ("Maize", 0.3), ("Wheat", 0.15)]
            return {
                "top_3": fallback,
                "confidence": fallback[0][1],
                "probabilities": {k: v for k, v in fallback},
                "model_version": "fallback",
            }

        probs = model.predict_proba(features)[0]
        classes = (
            list(self.label_encoder.classes_)
            if self.label_encoder is not None
            else [str(x) for x in getattr(model, "classes_", [])]
        )

        ranked_idx = np.argsort(probs)[::-1][:3]
        top_3 = [(classes[i], float(probs[i])) for i in ranked_idx]
        return {
            "top_3": [(label, round(score, 4)) for label, score in top_3],
            "confidence": round(float(top_3[0][1]), 4),
            "probabilities": {classes[i]: round(float(probs[i]), 6) for i in range(len(classes))},
            "model_version": self.models["naive_bayes"].version or "unknown",
        }

    def cluster_reading(self, reading: dict[str, Any]) -> dict[str, Any]:
        model = self.models["kmeans"].model
        vector = np.array(
            [[
                float(reading.get("nitrogen") or 0),
                float(reading.get("phosphorus") or 0),
                float(reading.get("potassium") or 0),
                float(reading.get("ph") or 7),
                float(reading.get("soil_moisture") or 0),
            ]],
            dtype=float,
        )

        if model is None:
            return {
                "cluster_id": 0,
                "zone_label": "Zone A (Fallback)",
                "model_version": "fallback",
            }

        cluster_id = int(model.predict(vector)[0])
        zone_map = {
            0: "Zone A (Optimal)",
            1: "Zone B (Nitrogen Deficient)",
            2: "Zone C (Water Stressed)",
            3: "Zone D (pH Imbalanced)",
        }
        return {
            "cluster_id": cluster_id,
            "zone_label": zone_map.get(cluster_id, f"Zone {cluster_id + 1}"),
            "model_version": self.models["kmeans"].version or "unknown",
        }

    async def status(self) -> dict[str, Any]:
        await self.refresh_if_newer()
        output: dict[str, Any] = {}
        for model_type, state in self.models.items():
            output[model_type] = {
                "version": state.version,
                "artifact_path": state.artifact_path,
                "metric_name": state.metric_name,
                "metric_value": state.metric_value,
                "loaded": state.model is not None,
            }
        return output


model_manager = ModelManager()
