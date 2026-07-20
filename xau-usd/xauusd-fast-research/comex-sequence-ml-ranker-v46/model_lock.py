from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ranker import sha256_file


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "comex_sequence_ml_ranker_v46.json"
OUTPUTS = ROOT / "outputs"
MODEL = OUTPUTS / "COMEX_SEQUENCE_ML_V46_MODEL.joblib"
CALIBRATION_SCORES = OUTPUTS / "COMEX_SEQUENCE_ML_V46_CALIBRATION_SCORES.parquet"
LOCK = OUTPUTS / "COMEX_SEQUENCE_ML_V46_MODEL_LOCK.json"
TRACKED = [
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "config/comex_sequence_ml_ranker_v46.json",
    "train_and_lock.py",
    "model_lock.py",
    "run_internal_exam.py",
    "run_stage.py",
    "src/__init__.py",
    "src/ranker.py",
    "tests/test_ranker.py",
]


def payload_digest(payload: dict[str, Any]) -> str:
    clean = {key: value for key, value in payload.items() if key != "contract_sha256"}
    return hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verify_lock() -> dict[str, Any]:
    if not LOCK.is_file():
        raise FileNotFoundError("V46 model lock is missing.")
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    if payload.get("contract_sha256") != payload_digest(payload):
        raise RuntimeError("V46 lock payload digest is invalid.")
    observed_files = {name: sha256_file(ROOT / name) for name in TRACKED}
    if observed_files != payload.get("tracked_file_sha256"):
        raise RuntimeError("V46 tracked model contract changed after lock.")
    if sha256_file(MODEL) != payload.get("model_sha256"):
        raise RuntimeError("V46 serialized model changed after lock.")
    if sha256_file(CALIBRATION_SCORES) != payload.get("calibration_scores_sha256"):
        raise RuntimeError("V46 calibration scores changed after lock.")
    return payload
