from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "ml_artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
DATASET_PATH = ROOT / "crop_recommendation.csv"


def dump_model_variants(obj: Any, artifact_path: Path) -> None:
    """Save model using both .joblib and .pkl filenames."""
    joblib.dump(obj, artifact_path)
    if artifact_path.suffix == ".joblib":
        joblib.dump(obj, artifact_path.with_suffix(".pkl"))


def expert_rules(n: float, p: float, k: float, t: float, h: float, ph: float, sm: float) -> tuple[float, str, list[str]]:
    fired: list[str] = []
    water = 0.0

    if sm < 20 and t > 32:
        water = 50.0
        fired.append("RULE_001")
    elif 20 <= sm <= 40 and h < 50:
        water = 30.0
        fired.append("RULE_002")
    elif sm > 60 and h > 65:
        water = 0.0
        fired.append("RULE_003")

    if t > 35 and sm < 50:
        water += 15.0
        fired.append("RULE_004")

    if n < 40 or p < 30 or k < 35:
        fired.append("RULE_005")

    if ph < 5.5 or ph > 7.5:
        fired.append("RULE_006")

    decision = "ON" if water > 0 else "OFF"
    return max(0.0, water), decision, fired


def synthetic_irrigation_dataset(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = rng.uniform(0, 140, rows)
    p = rng.uniform(0, 145, rows)
    k = rng.uniform(0, 205, rows)
    t = rng.uniform(18, 45, rows)
    h = rng.uniform(14, 100, rows)
    ph = rng.uniform(3.5, 9, rows)
    sm = rng.uniform(0, 100, rows)
    gas = rng.uniform(250, 550, rows)

    water = []
    decision = []
    for i in range(rows):
        liters, dec, _ = expert_rules(n[i], p[i], k[i], t[i], h[i], ph[i], sm[i])
        liters += float(rng.normal(0, max(1.0, liters * 0.1)))
        liters = max(0.0, liters)
        water.append(liters)
        decision.append(dec)

    return pd.DataFrame(
        {
            "nitrogen": n,
            "phosphorus": p,
            "potassium": k,
            "temperature": t,
            "humidity": h,
            "ph": ph,
            "gas": gas,
            "soil_moisture": sm,
            "water_requirement_liters": water,
            "irrigation_decision": decision,
        }
    )


def load_crop_dataset() -> pd.DataFrame:
    if DATASET_PATH.exists():
        return pd.read_csv(DATASET_PATH)

    labels = [
        "rice", "maize", "jute", "cotton", "coconut", "papaya", "orange", "apple", "muskmelon", "watermelon",
        "grapes", "mango", "banana", "pomegranate", "lentil", "blackgram", "mungbean", "mothbeans", "pigeonpeas", "kidneybeans",
        "chickpea", "coffee",
    ]
    rng = np.random.default_rng(12)
    rows = []
    for idx, label in enumerate(labels):
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
                    "label": label,
                }
            )
    return pd.DataFrame(rows)


def train_linear_regression(df: pd.DataFrame) -> dict[str, Any]:
    features = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "soil_moisture"]
    X = df[features]
    y = df["water_requirement_liters"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())])
    pipeline.fit(X_train, y_train)

    pred = pipeline.predict(X_test)
    r2 = r2_score(y_test, pred)
    mae = mean_absolute_error(y_test, pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    cv = cross_val_score(pipeline, X, y, cv=5, scoring="r2")

    dump_model_variants(pipeline, ARTIFACTS / "lr_irrigation_v1.joblib")

    plt.figure(figsize=(6, 4))
    plt.scatter(y_test, pred, s=12, alpha=0.6)
    plt.title("LR Predicted vs Actual")
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "lr_actual_vs_pred.png", dpi=150)
    plt.close()

    return {
        "Model": "LinearRegression",
        "Version": "v1",
        "Metric": "R2",
        "Score": round(float(r2), 4),
        "Extra": {"MAE": round(float(mae), 4), "RMSE": round(float(rmse), 4), "CV_R2": round(float(np.mean(cv)), 4)},
    }


def train_naive_bayes(df: pd.DataFrame) -> dict[str, Any]:
    features = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    X = df[features]
    y = df["label"]

    encoder = LabelEncoder()
    y_enc = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = GaussianNB()
    model.fit(X_train_s, y_train)

    pred = model.predict(X_test_s)
    acc = accuracy_score(y_test, pred)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(Pipeline([("scaler", StandardScaler()), ("model", GaussianNB())]), X, y_enc, cv=cv, scoring="accuracy")

    cm = confusion_matrix(y_test, pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, cmap="Greens")
    plt.title("Naive Bayes Confusion Matrix")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "nb_confusion_matrix.png", dpi=150)
    plt.close()

    dump_model_variants(Pipeline([("scaler", scaler), ("model", model)]), ARTIFACTS / "nb_crop_v1.joblib")
    dump_model_variants(encoder, ARTIFACTS / "label_encoder.joblib")

    print(classification_report(y_test, pred, zero_division=0))

    sample = X_test.iloc[0:1]
    sample_probs = model.predict_proba(scaler.transform(sample))[0]
    top3_idx = np.argsort(sample_probs)[::-1][:3]
    top3 = [(encoder.classes_[i], float(sample_probs[i])) for i in top3_idx]
    print("Sample top-3:", top3)

    return {
        "Model": "GaussianNB",
        "Version": "v1",
        "Metric": "Accuracy",
        "Score": round(float(acc), 4),
        "Extra": {"CV_ACC": round(float(np.mean(cv_scores)), 4)},
    }


def train_kmeans(df: pd.DataFrame) -> dict[str, Any]:
    X = df[["nitrogen", "phosphorus", "potassium", "ph", "soil_moisture"]].to_numpy(dtype=float)

    inertias = []
    silhouettes = {}
    best_k = 2
    best_score = -1.0
    best_model = None

    for k in range(2, 11):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X)
        inertias.append((k, model.inertia_))
        if k <= 8:
            score = silhouette_score(X, labels)
            silhouettes[k] = score
            if score > best_score:
                best_score = score
                best_k = k
                best_model = model

    assert best_model is not None

    plt.figure(figsize=(6, 4))
    plt.plot([k for k, _ in inertias], [v for _, v in inertias], marker="o")
    plt.title("Elbow Method")
    plt.xlabel("k")
    plt.ylabel("Inertia")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "kmeans_elbow.png", dpi=150)
    plt.close()

    pca2 = PCA(n_components=2, random_state=42)
    X_2d = pca2.fit_transform(X)
    labels = best_model.predict(X)

    plt.figure(figsize=(6, 4))
    plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap="viridis", s=12)
    plt.title("KMeans Clusters (PCA 2D)")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "kmeans_pca_scatter.png", dpi=150)
    plt.close()

    dump_model_variants(best_model, ARTIFACTS / "kmeans_zones_v1.joblib")

    return {
        "Model": "KMeans",
        "Version": "v1",
        "Metric": "Silhouette",
        "Score": round(float(best_score), 4),
        "Extra": {"k": best_k, "inertia": round(float(best_model.inertia_), 4)},
    }


def train_pca(df: pd.DataFrame) -> dict[str, Any]:
    X = df[["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "gas", "soil_moisture"]].to_numpy(dtype=float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    pca_full = PCA(n_components=8, random_state=42)
    pca_full.fit(Xs)

    plt.figure(figsize=(7, 4))
    exp = pca_full.explained_variance_ratio_
    plt.bar(range(1, 9), exp, alpha=0.75, label="Explained")
    plt.plot(range(1, 9), np.cumsum(exp), marker="o", color="black", label="Cumulative")
    plt.title("PCA Explained Variance")
    plt.xlabel("Components")
    plt.ylabel("Variance Ratio")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "pca_variance.png", dpi=150)
    plt.close()

    pca3 = PCA(n_components=3, random_state=42)
    pca3.fit(Xs)

    dump_model_variants(pca3, ARTIFACTS / "pca_sensor_v1.joblib")
    dump_model_variants(scaler, ARTIFACTS / "pca_scaler_v1.joblib")

    return {
        "Model": "PCA",
        "Version": "v1",
        "Metric": "Variance@3PC",
        "Score": round(float(np.sum(pca3.explained_variance_ratio_)), 4),
    }


def expert_simulation(samples: pd.DataFrame, n_rows: int = 10) -> None:
    print("\nExpert system simulation (10 samples)")
    sample_rows = samples.head(n_rows)
    for i, row in sample_rows.iterrows():
        liters, decision, fired = expert_rules(
            row["nitrogen"], row["phosphorus"], row["potassium"], row["temperature"], row["humidity"], row["ph"], row["soil_moisture"]
        )
        trace = {
            "sample": int(i),
            "decision": decision,
            "water_liters": round(float(liters), 2),
            "rules_fired": fired,
        }
        print(trace)


def main() -> None:
    irrigation_df = synthetic_irrigation_dataset(5000)
    crop_df = load_crop_dataset()

    summary = [
        train_linear_regression(irrigation_df),
        train_naive_bayes(crop_df),
        train_kmeans(irrigation_df),
        train_pca(irrigation_df),
    ]

    expert_simulation(irrigation_df, 10)

    table = pd.DataFrame(summary)
    print("\nSummary")
    print(table[["Model", "Version", "Metric", "Score"]].to_string(index=False))

    print("\nArtifacts saved to:", ARTIFACTS)
    print("Copy all .joblib files into backend ml/artifacts directory.")


if __name__ == "__main__":
    main()
