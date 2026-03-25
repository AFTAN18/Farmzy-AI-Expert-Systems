from __future__ import annotations

import numpy as np


class FuzzyIrrigationController:
    """Mamdani fuzzy controller for irrigation volume estimation."""

    def __init__(self) -> None:
        self.moisture_sets = {
            "DRY": (0, 0, 20, 40),
            "MODERATE": (20, 40, 60, 80),
            "WET": (60, 80, 100, 100),
        }
        self.temperature_sets = {
            "COOL": (0, 0, 20, 28),
            "WARM": (20, 28, 35, 45),
            "HOT": (32, 38, 50, 50),
        }
        self.humidity_sets = {
            "LOW": (0, 0, 30, 55),
            "MEDIUM": (30, 55, 75, 90),
            "HIGH": (60, 75, 100, 100),
        }
        self.output_singletons = {
            "NONE": 0.0,
            "LIGHT": 10.0,
            "MODERATE": 25.0,
            "HEAVY": 40.0,
            "CRITICAL": 55.0,
        }

    @staticmethod
    def _trapmf(x: np.ndarray | float, a: float, b: float, c: float, d: float) -> np.ndarray:
        values = np.asarray(x, dtype=float)
        result = np.zeros_like(values)

        rising = (a < values) & (values < b)
        result[rising] = (values[rising] - a) / max(b - a, 1e-9)

        plateau = (b <= values) & (values <= c)
        result[plateau] = 1.0

        falling = (c < values) & (values < d)
        result[falling] = (d - values[falling]) / max(d - c, 1e-9)

        return np.clip(result, 0.0, 1.0)

    @staticmethod
    def _singleton_membership(domain: np.ndarray, center: float, width: float = 8.0) -> np.ndarray:
        left = center - width / 2
        right = center + width / 2
        return FuzzyIrrigationController._trapmf(domain, left, center, center, right)

    def _fuzzify(self, soil_moisture: float, temperature: float, humidity: float) -> dict[str, dict[str, float]]:
        return {
            "soil_moisture": {
                name: float(self._trapmf(soil_moisture, *params))
                for name, params in self.moisture_sets.items()
            },
            "temperature": {
                name: float(self._trapmf(temperature, *params))
                for name, params in self.temperature_sets.items()
            },
            "humidity": {
                name: float(self._trapmf(humidity, *params))
                for name, params in self.humidity_sets.items()
            },
        }

    def infer(self, soil_moisture: float, temperature: float, humidity: float) -> tuple[float, dict[str, float]]:
        """Run Mamdani inference and return (liters, output_memberships)."""
        fuzz = self._fuzzify(soil_moisture, temperature, humidity)

        activation: dict[str, float] = {label: 0.0 for label in self.output_singletons}

        activation["CRITICAL"] = max(
            activation["CRITICAL"],
            min(fuzz["soil_moisture"]["DRY"], fuzz["temperature"]["HOT"]),
        )
        activation["HEAVY"] = max(
            activation["HEAVY"],
            min(fuzz["soil_moisture"]["DRY"], fuzz["temperature"]["WARM"]),
        )
        activation["MODERATE"] = max(
            activation["MODERATE"],
            min(fuzz["soil_moisture"]["MODERATE"], fuzz["temperature"]["HOT"]),
        )
        activation["NONE"] = max(activation["NONE"], fuzz["soil_moisture"]["WET"])
        activation["LIGHT"] = max(
            activation["LIGHT"],
            min(fuzz["humidity"]["HIGH"], fuzz["soil_moisture"]["MODERATE"]),
        )

        domain = np.linspace(0, 60, 601)
        aggregated = np.zeros_like(domain)
        for label, alpha in activation.items():
            if alpha <= 0:
                continue
            center = self.output_singletons[label]
            out_mf = self._singleton_membership(domain, center)
            aggregated = np.maximum(aggregated, np.minimum(alpha, out_mf))

        if float(np.sum(aggregated)) == 0:
            return 0.0, activation

        centroid = float(np.sum(domain * aggregated) / np.sum(aggregated))
        return round(centroid, 2), activation


fuzzy_controller = FuzzyIrrigationController()
