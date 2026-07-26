from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(dict(value)), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def resolve_inputs(repo_root: Path, config: Mapping[str, Any]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for name, spec in config["inputs"].items():
        path = repo_root / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != str(spec["sha256"]):
            raise ValueError(f"Expanded V4 input hash mismatch for {name}: {actual}")
        result[name] = path
    return result


def assert_correction_only(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    *,
    keys: Sequence[str],
    allowed_changed_columns: Sequence[str],
    name: str,
) -> dict[str, int]:
    if set(current.columns) != set(previous.columns):
        raise ValueError(f"{name} columns changed")
    current = current.sort_values(list(keys), kind="mergesort").reset_index(drop=True)
    previous = previous.sort_values(list(keys), kind="mergesort").reset_index(drop=True)
    if current[list(keys)].to_dict("records") != previous[list(keys)].to_dict(
        "records"
    ):
        raise ValueError(f"{name} identities changed")
    allowed = set(allowed_changed_columns)
    unchanged = [column for column in current.columns if column not in allowed]
    try:
        pd.testing.assert_frame_equal(
            current[unchanged],
            previous[unchanged],
            check_dtype=False,
            check_exact=True,
        )
    except AssertionError as error:
        raise ValueError(f"{name} changed outside the correction") from error
    changed = {
        column: int((~current[column].eq(previous[column])).sum())
        for column in allowed_changed_columns
    }
    if any(value == 0 for value in changed.values()):
        raise ValueError(f"{name} did not change every corrected feature")
    return changed


def assert_exact_frame(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    *,
    keys: Sequence[str],
    name: str,
) -> None:
    current = current.sort_values(list(keys), kind="mergesort").reset_index(drop=True)
    previous = previous.sort_values(list(keys), kind="mergesort").reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(
            current, previous, check_dtype=False, check_exact=True
        )
    except AssertionError as error:
        raise ValueError(f"{name} changed") from error
