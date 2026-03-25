from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "ml" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _dump_model_variants(obj: Any, artifact: Path) -> None:
    """Persist model in both joblib and pickle-compatible filename variants."""
    joblib.dump(obj, artifact)
    if artifact.suffix == ".joblib":
        joblib.dump(obj, artifact.with_suffix(".pkl"))


def _expert_rule_water(n: float, p: float, k: float, temp: float, humidity: float, ph: float, moisture: float) -> float:
    water = 0.0
    if moisture < 20 and temp > 32:
        water = 50.0
    elif 20 <= moisture <= 40 and humidity < 50:
        water = 30.0
    elif moisture > 60 and humidity > 65:
        water = 0.0

    if temp > 35 and moisture < 50:
        water += 15.0

    if humidity > 85 and moisture > 70:
        water = 0.0

    return max(0.0, water)


def generate_irrigation_dataset(n_rows: int = 5000, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    nitrogen = rng.uniform(0, 140, n_rows)
    phosphorus = rng.uniform(0, 145, n_rows)
    potassium = rng.uniform(0, 205, n_rows)
    temperature = rng.uniform(18, 45, n_rows)
    humidity = rng.uniform(14, 100, n_rows)
    ph = rng.uniform(3.5, 9.0, n_rows)
    gas = rng.uniform(250, 550, n_rows)
    soil_moisture = rng.uniform(0, 100, n_rows)

    water = []
    decision = []
    for n, p, k, t, h, pv, sm in zip(nitrogen, phosphorus, potassium, temperature, humidity, ph, soil_moisture):
        liters = _expert_rule_water(n, p, k, t, h, pv, sm)
        noise = float(rng.normal(0, max(1.0, liters * 0.1)))
        liters = max(0.0, liters + noise)
        water.append(liters)
        decision.append("ON" if liters > 0 else "OFF")

    return pd.DataFrame(
        {
            "nitrogen": nitrogen,
            "phosphorus": phosphorus,
            "potassium": potassium,
            "temperature": temperature,
            "humidity": humidity,
            "ph": ph,
            "gas_ppm": gas,
            "soil_moisture": soil_moisture,
            "water_requirement_liters": water,
            "irrigation_decision": decision,
        }
    )


def _make_crop_synthetic() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    crops = [
        "rice", "maize", "jute", "cotton", "coconut", "papaya", "orange", "apple", "muskmelon", "watermelon",
        "grapes", "mango", "banana", "pomegranate", "lentil", "blackgram", "mungbean", "mothbeans", "pigeonpeas", "kidneybeans",
        "chickpea", "coffee",
    ]

    rows = []
    for idx, crop in enumerate(crops):
        center = {
            "N": 20 + (idx * 5 % 110),
            "P": 15 + (idx * 7 % 120),
            "K": 25 + (idx * 9 % 160),
            "temperature": 18 + (idx * 1.1 % 18),
            "humidity": 45 + (idx * 2.3 % 45),
            "ph": 5.2 + (idx * 0.11 % 2.0),
            "rainfall": 60 + (idx * 11 % 180),
        }
        for _ in range(100):
            rows.append(
                {
                    "N": float(np.clip(rng.normal(center["N"], 3.0), 0, 140)),
                    "P": float(np.clip(rng.normal(center["P"], 3.0), 5, 145)),
                    "K": float(np.clip(rng.normal(center["K"], 4.0), 5, 205)),
                    "temperature": float(np.clip(rng.normal(center["temperature"], 1.2), 10, 43)),
                    "humidity": float(np.clip(rng.normal(center["humidity"], 3.0), 20, 100)),
                    "ph": float(np.clip(rng.normal(center["ph"], 0.12), 3.8, 8.5)),
                    "rainfall": float(np.clip(rng.normal(center["rainfall"], 8.0), 20, 300)),
                    "label": crop,
                }
            )
    return pd.DataFrame(rows)


def load_crop_dataset() -> pd.DataFrame:
    csv_path = DATA_DIR / "crop_recommendation.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if "label" in df.columns and not df["label"].empty and int(df["label"].value_counts().min()) >= 2:
            return df
    return _make_crop_synthetic()


def train_linear_regression(df: pd.DataFrame) -> dict[str, Any]:
    feature_cols = ["soil_moisture", "temperature", "humidity", "nitrogen", "phosphorus", "potassium", "ph"]
    target_col = "water_requirement_liters"

    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    r2 = float(r2_score(y_test, y_pred))
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring="r2")

    artifact = ARTIFACTS_DIR / "lr_irrigation_v1.joblib"
    _dump_model_variants(pipeline, artifact)

    return {
        "model_type": "linear_regression",
        "version": "v1",
        "metric_name": "R2",
        "score": round(r2, 4),
        "artifact_path": str(artifact),
        "training_rows": int(len(df)),
        "details": {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "cv_r2_mean": round(float(np.mean(cv_scores)), 4),
            "cv_r2_std": round(float(np.std(cv_scores)), 4),
        },
    }


def train_naive_bayes(df: pd.DataFrame) -> dict[str, Any]:
    feature_cols = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    X = df[feature_cols]
    y = df["label"]

    encoder = LabelEncoder()
    y_enc = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_enc,
        test_size=0.2,
        random_state=42,
        stratify=y_enc,
    )

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", GaussianNB()),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X, y_enc, cv=cv, scoring="accuracy")

    model_artifact = ARTIFACTS_DIR / "nb_crop_v1.joblib"
    label_artifact = ARTIFACTS_DIR / "label_encoder.joblib"
    _dump_model_variants(pipeline, model_artifact)
    _dump_model_variants(encoder, label_artifact)

    return {
        "model_type": "naive_bayes",
        "version": "v1",
        "metric_name": "accuracy",
        "score": round(accuracy, 4),
        "artifact_path": str(model_artifact),
        "training_rows": int(len(df)),
        "details": {
            "cv_acc_mean": round(float(np.mean(cv_scores)), 4),
            "cv_acc_std": round(float(np.std(cv_scores)), 4),
        },
    }


def train_kmeans(df: pd.DataFrame) -> dict[str, Any]:
    feature_cols = ["nitrogen", "phosphorus", "potassium", "ph", "soil_moisture"]
    X = df[feature_cols].to_numpy(dtype=float)

    best_k = 2
    best_score = -1.0
    best_model: KMeans | None = None

    for k in range(2, 9):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X)
        score = silhouette_score(X, labels)
        if score > best_score:
            best_score = float(score)
            best_k = k
            best_model = model

    assert best_model is not None
    artifact = ARTIFACTS_DIR / "kmeans_zones_v1.joblib"
    _dump_model_variants(best_model, artifact)

    return {
        "model_type": "kmeans",
        "version": "v1",
        "metric_name": "silhouette",
        "score": round(best_score, 4),
        "artifact_path": str(artifact),
        "training_rows": int(len(df)),
        "details": {
            "k": best_k,
            "inertia": round(float(best_model.inertia_), 4),
        },
    }


def train_pca(df: pd.DataFrame) -> dict[str, Any]:
    feature_cols = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "gas_ppm", "soil_moisture"]
    X = df[feature_cols].to_numpy(dtype=float)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=3, random_state=42)
    pca.fit(X_scaled)

    artifact = ARTIFACTS_DIR / "pca_sensor_v1.joblib"
    scaler_artifact = ARTIFACTS_DIR / "pca_scaler_v1.joblib"
    _dump_model_variants(pca, artifact)
    _dump_model_variants(scaler, scaler_artifact)

    explained = float(np.sum(pca.explained_variance_ratio_))

    return {
        "model_type": "pca",
        "version": "v1",
        "metric_name": "variance@3pc",
        "score": round(explained, 4),
        "artifact_path": str(artifact),
        "training_rows": int(len(df)),
    }


def retrain_all_models() -> list[dict[str, Any]]:
    irrigation_df = generate_irrigation_dataset()
    crop_df = load_crop_dataset()

    metrics = [
        train_linear_regression(irrigation_df),
        train_naive_bayes(crop_df),
        train_kmeans(irrigation_df),
        train_pca(irrigation_df),
    ]

    summary = pd.DataFrame(
        {
            "Model": [m["model_type"] for m in metrics],
            "Version": [m["version"] for m in metrics],
            "Metric": [m["metric_name"] for m in metrics],
            "Score": [m["score"] for m in metrics],
        }
    )
    print(summary.to_string(index=False))

    return metrics


if __name__ == "__main__":
    retrain_all_models()
