from pathlib import Path
from typing import Any

import joblib

from app.ml.data import data_signature

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


def load_artifact(name: str) -> Any | None:
    path = ARTIFACT_DIR / name
    if not path.exists():
        return None
    artifact = joblib.load(path)
    if artifact.get("signature") != data_signature():
        return None
    return artifact.get("payload")


def save_artifact(name: str, payload: Any) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"signature": data_signature(), "payload": payload}, ARTIFACT_DIR / name)
