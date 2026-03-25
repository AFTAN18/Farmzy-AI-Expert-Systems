from __future__ import annotations

import json

from services.ml_pipeline import model_manager


async def predict_example() -> dict:
    await model_manager.initialize()
    reading = {
        "nitrogen": 72,
        "phosphorus": 45,
        "potassium": 80,
        "temperature": 33,
        "humidity": 48,
        "ph": 6.4,
        "gas_ppm": 360,
        "soil_moisture": 28,
    }

    return {
        "irrigation": model_manager.predict_irrigation(reading),
        "crops": model_manager.recommend_crop(reading),
        "zone": model_manager.cluster_reading(reading),
    }


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(predict_example())
    print(json.dumps(result, indent=2))
