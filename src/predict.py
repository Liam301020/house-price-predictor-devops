# src/predict.py
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any

_model = None

def load_model(path: str | None = None):
    """
    Load the trained pipeline from rf_pipeline.pkl.
    Tries the project root first, then the current working directory.
    """
    global _model
    if _model is not None:
        return _model

    if path is None:
        repo_root = Path(__file__).resolve().parents[1]
        candidates = [
            repo_root / "rf_pipeline.pkl",   # project root
            Path.cwd() / "rf_pipeline.pkl",  # current working directory
        ]
        for p in candidates:
            if p.exists():
                path = str(p)
                break
        else:
            raise FileNotFoundError(
                "rf_pipeline.pkl not found in project root or current working directory"
            )

    _model = joblib.load(path)
    return _model

def _expected_feature_names(model) -> list[str] | None:
    """Best-effort: read the feature names the model/preprocessor was fitted with."""
    if hasattr(model, "feature_names_in_"):
        return list(model.feature_names_in_)
    if hasattr(model, "named_steps"):
        for key in ("preprocessor", "pre"):
            pre = model.named_steps.get(key)
            if pre is not None and hasattr(pre, "feature_names_in_"):
                return list(pre.feature_names_in_)
    return None

def _align_payload(payload: Dict[str, Any], model) -> pd.DataFrame:
    """
    Return a single-row DataFrame whose columns match what the model expects.
    - Derive fields we can (e.g., *_sqm from base inputs).
    - Fill missing, non-derivable fields with safe defaults (0 / False).
    """
    cols = _expected_feature_names(model)
    if not cols:
        return pd.DataFrame([payload])

    row: Dict[str, Any] = {}
    for c in cols:
        if c in payload:
            row[c] = payload[c]
            continue

        # Derivable fields
        if c == "land_size_sqm" and "land_size" in payload:
            row[c] = payload["land_size"]
        elif c == "building_size_sqm" and "building_size" in payload:
            row[c] = payload["building_size"]
        elif c == "schools_nearby":
            row[c] = payload.get("schools_nearby", 0)
        elif c == "above_suburb_median":
            row[c] = 0  
        elif c in ("price_per_land_sqm", "price_per_building_sqm"):
            row[c] = 0.0  
        else:
            # Generic safe fallback for any other missing feature
            row[c] = 0

    return pd.DataFrame([row], columns=cols)

def predict_price(payload: Dict[str, Any]) -> float:
    model = load_model()
    X = _align_payload(payload, model)
    y = model.predict(X)
    return float(y[0])