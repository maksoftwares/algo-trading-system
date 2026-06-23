from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("config") / "ml" / "a3_ml_label_promotion.json"
SCHEMA_VERSION = "a3_ml_label_promotion_v1"
DEFAULT_ALLOWED_LABEL_STATUSES = (
    "TP",
    "SL",
    "TIMEOUT_POSITIVE",
    "TIMEOUT_NEGATIVE",
    "TIMEOUT_FLAT",
)
KNOWN_TRAINABLE_LABEL_STATUSES = set(DEFAULT_ALLOWED_LABEL_STATUSES)


@dataclass(frozen=True)
class LabelPromotionScope:
    schema_version: str
    label_promotion_authorized: bool
    review_reference: str
    allowed_label_statuses: tuple[str, ...]
    minimum_mature_labels: int
    minimum_minority_labels: int
    require_slippage_adequate: bool

    @property
    def scope_name(self) -> str:
        if not self.label_promotion_authorized:
            return "label_promotion_locked"
        return "reviewer_approved_label_promotion"

    def promotion_active(self, slippage_status: str) -> bool:
        if not self.label_promotion_authorized:
            return False
        return not self.require_slippage_adequate or slippage_status == "ADEQUATE"


def load_label_promotion_scope(root: Path, config_path: Path | None = None) -> LabelPromotionScope:
    root = root.resolve()
    path = (config_path or root / DEFAULT_CONFIG).resolve()
    if not path.exists():
        return _default_scope()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported label promotion schema: {path}")
    authorized = bool(payload.get("label_promotion_authorized", False))
    review_reference = str(payload.get("review_reference", "")).strip()
    allowed = _allowed_statuses(payload.get("allowed_label_statuses", DEFAULT_ALLOWED_LABEL_STATUSES))
    minimum_mature_labels = _positive_int(payload.get("minimum_mature_labels", 300), "minimum_mature_labels", path)
    minimum_minority_labels = _positive_int(payload.get("minimum_minority_labels", 90), "minimum_minority_labels", path)
    require_slippage_adequate = bool(payload.get("require_slippage_adequate", True))
    if authorized:
        _validate_authorized_scope(path, review_reference, allowed)
    return LabelPromotionScope(
        schema_version=SCHEMA_VERSION,
        label_promotion_authorized=authorized,
        review_reference=review_reference,
        allowed_label_statuses=allowed if authorized else DEFAULT_ALLOWED_LABEL_STATUSES,
        minimum_mature_labels=minimum_mature_labels,
        minimum_minority_labels=minimum_minority_labels,
        require_slippage_adequate=require_slippage_adequate,
    )


def _default_scope() -> LabelPromotionScope:
    return LabelPromotionScope(
        schema_version=SCHEMA_VERSION,
        label_promotion_authorized=False,
        review_reference="",
        allowed_label_statuses=DEFAULT_ALLOWED_LABEL_STATUSES,
        minimum_mature_labels=300,
        minimum_minority_labels=90,
        require_slippage_adequate=True,
    )


def _allowed_statuses(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list | tuple):
        raise ValueError("allowed_label_statuses must be a list")
    statuses = []
    seen: set[str] = set()
    for value in values:
        status = str(value or "").strip().upper()
        if not status:
            raise ValueError("allowed_label_statuses contains an empty status")
        if status not in KNOWN_TRAINABLE_LABEL_STATUSES:
            raise ValueError(f"unknown trainable label status: {status}")
        if status not in seen:
            statuses.append(status)
            seen.add(status)
    return tuple(statuses)


def _positive_int(value: Any, key: str, path: Path) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer in {path}") from exc
    if parsed <= 0:
        raise ValueError(f"{key} must be positive in {path}")
    return parsed


def _validate_authorized_scope(path: Path, review_reference: str, allowed: tuple[str, ...]) -> None:
    if not review_reference:
        raise ValueError(f"label promotion requires review_reference: {path}")
    if not allowed:
        raise ValueError(f"label promotion requires at least one allowed_label_status: {path}")
