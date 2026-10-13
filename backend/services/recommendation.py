import math
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "ai_ml" / "models" / "crop_recommendation_model.pkl"
FEATURES = ("N", "P", "K", "temperature", "humidity", "ph", "rainfall")


class CropDataError(RuntimeError):
    pass


def recommend_crop(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("Crop inputs must be a JSON object.")

    query: dict[str, float] = {}
    for feature in FEATURES:
        value = payload.get(feature)
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{feature} must be a number.") from error
        if not math.isfinite(number):
            raise ValueError(f"{feature} must be a finite number.")
        query[feature] = number

    model = _load_model(MODEL_PATH)
    input_data = pd.DataFrame([query], columns=FEATURES)
    try:
        recommendation = str(model.predict(input_data)[0])
        probabilities = model.predict_proba(input_data)[0]
        classes = model.classes_
    except (AttributeError, IndexError, TypeError, ValueError) as error:
        raise CropDataError(f"The trained crop model could not process the supplied features: {error}") from error

    try:
        if len(classes) != len(probabilities) or not len(classes):
            raise ValueError("prediction classes and probabilities do not match")
        ranked = sorted(
            ((str(label), float(probability)) for label, probability in zip(classes, probabilities)),
            key=lambda item: (-item[1], item[0]),
        )
    except (TypeError, ValueError) as error:
        raise CropDataError(f"The trained crop model returned invalid probabilities: {error}") from error

    scores = dict(ranked)
    if (
        recommendation not in scores
        or any(not math.isfinite(score) or score < 0 or score > 1 for score in scores.values())
    ):
        raise CropDataError("The trained crop model returned an invalid prediction.")

    return {
        "recommendation": recommendation,
        "confidence": round(scores[recommendation], 3),
        "alternatives": [label for label, _ in ranked if label != recommendation][:3],
        "method": "Trained crop recommendation classifier included with this project",
        "disclaimer": "Dataset-based suggestion only. Check local season, soil-test results, water, market, and an agriculture officer before planting.",
    }


@lru_cache(maxsize=1)
def _load_model(path: Path) -> Any:
    if not path.is_file():
        raise CropDataError(f"Trained crop model not found: {path}")
    try:
        return joblib.load(path)
    except (AttributeError, ImportError, EOFError, OSError, pickle.UnpicklingError, TypeError, ValueError) as error:
        raise CropDataError(f"Unable to load trained crop model from {path}: {error}") from error
