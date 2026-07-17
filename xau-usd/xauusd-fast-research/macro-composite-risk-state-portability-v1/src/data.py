from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SHARED_DATA_PATH = ROOT / "independent-specialists-v1" / "src" / "data.py"


def _load_shared_data() -> Any:
    name = "xau_macro_composite_shared_data"
    spec = importlib.util.spec_from_file_location(name, SHARED_DATA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared data module from {SHARED_DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SHARED_DATA = _load_shared_data()


@dataclass(frozen=True)
class ResearchInputs:
    gold: Any
    macro_state: pd.DataFrame
    evidence: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fred_series(
    path: Path,
    value_column: str,
    lag_calendar_days: int,
) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"observation_date", value_column}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing columns {missing}")
    result = pd.DataFrame(
        {
            "observation_date": pd.to_datetime(
                frame["observation_date"], utc=True, errors="coerce"
            ),
            "value": pd.to_numeric(frame[value_column], errors="coerce"),
        }
    ).dropna()
    result = result.sort_values("observation_date", kind="mergesort").reset_index(drop=True)
    result["available_at"] = result["observation_date"] + pd.Timedelta(
        days=int(lag_calendar_days)
    )
    if result["available_at"].duplicated().any():
        raise ValueError(f"Duplicate availability timestamps in {path}")
    return result


def _change_frame(source: pd.DataFrame, periods: int, output: str) -> pd.DataFrame:
    result = source[["available_at", "value"]].copy()
    result[output] = result["value"] - result["value"].shift(periods)
    return result[["available_at", output]].dropna().reset_index(drop=True)


def _merge_feature(
    timeline: pd.DataFrame,
    feature: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    return pd.merge_asof(
        timeline.sort_values("available_at"),
        feature[["available_at", column]].sort_values("available_at"),
        on="available_at",
        direction="backward",
        allow_exact_matches=True,
    )


def build_macro_state(series: dict[str, pd.DataFrame]) -> pd.DataFrame:
    features = {
        "real_yield_change_20d": _change_frame(series["real_yield_10y"], 20, "real_yield_change_20d"),
        "dollar_change_20d": _change_frame(series["dollar_index_broad"], 20, "dollar_change_20d"),
        "breakeven_5y_change_20d": _change_frame(series["breakeven_5y"], 20, "breakeven_5y_change_20d"),
        "dgs2_change_20d": _change_frame(series["dgs2"], 20, "dgs2_change_20d"),
        "treasury_10y2y_change_20d": _change_frame(series["treasury_10y2y"], 20, "treasury_10y2y_change_20d"),
        "baa10y_change_20d": _change_frame(series["baa10y"], 20, "baa10y_change_20d"),
        "vix_change_20d": _change_frame(series["vix_close"], 20, "vix_change_20d"),
        "gvz_change_20d": _change_frame(series["gvz_close"], 20, "gvz_change_20d"),
        "nfci_change_4obs": _change_frame(series["nfci"], 4, "nfci_change_4obs"),
    }
    availability = pd.concat(
        [frame["available_at"] for frame in features.values()], ignore_index=True
    ).drop_duplicates().sort_values()
    state = pd.DataFrame({"available_at": availability})
    for column, feature in features.items():
        state = _merge_feature(state, feature, column)
    state = state.dropna().reset_index(drop=True)
    state["macro_bull_votes"] = (
        (state["real_yield_change_20d"] <= -0.15).astype(int)
        + (state["dollar_change_20d"] <= -1.00).astype(int)
        + (state["breakeven_5y_change_20d"] >= 0.10).astype(int)
        + (
            (state["dgs2_change_20d"] <= -0.15)
            & (state["treasury_10y2y_change_20d"] >= 0.03)
        ).astype(int)
        + (state["baa10y_change_20d"] >= 0.10).astype(int)
        + (
            (state["vix_change_20d"] >= 3.00)
            | (state["gvz_change_20d"] >= 3.00)
        ).astype(int)
        + (state["nfci_change_4obs"] >= 0.10).astype(int)
    )
    state["macro_bear_votes"] = (
        (state["real_yield_change_20d"] >= 0.15).astype(int)
        + (state["dollar_change_20d"] >= 1.00).astype(int)
        + (state["breakeven_5y_change_20d"] <= -0.10).astype(int)
        + (
            (state["dgs2_change_20d"] >= 0.15)
            & (state["treasury_10y2y_change_20d"] <= -0.03)
        ).astype(int)
        + (state["baa10y_change_20d"] <= -0.10).astype(int)
        + (
            (state["vix_change_20d"] <= -3.00)
            | (state["gvz_change_20d"] <= -3.00)
        ).astype(int)
        + (state["nfci_change_4obs"] <= -0.10).astype(int)
    )
    state["macro_composite_score"] = (
        state["macro_bull_votes"] - state["macro_bear_votes"]
    )
    return state


def load_macro_state(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = REPOSITORY_ROOT / config["fred_source_root"]
    series: dict[str, pd.DataFrame] = {}
    evidence: dict[str, Any] = {}
    for name, specification in config["fred_sources"].items():
        path = root / specification["path"]
        actual_sha = sha256_file(path)
        if actual_sha != specification["sha256"]:
            raise ValueError(f"FRED source hash mismatch for {name}: {actual_sha}")
        frame = load_fred_series(
            path,
            specification["column"],
            int(specification["lag_calendar_days"]),
        )
        series[name] = frame
        evidence[name] = {
            "path": str(path),
            "sha256": actual_sha,
            "rows": int(len(frame)),
            "first_observation": frame["observation_date"].min().isoformat(),
            "last_observation": frame["observation_date"].max().isoformat(),
            "last_available_at": frame["available_at"].max().isoformat(),
            "lag_calendar_days": int(specification["lag_calendar_days"]),
        }
    state = build_macro_state(series)
    evidence["macro_state"] = {
        "rows": int(len(state)),
        "first_available_at": state["available_at"].min().isoformat(),
        "last_available_at": state["available_at"].max().isoformat(),
    }
    return state, evidence


def load_inputs(config: dict[str, Any]) -> ResearchInputs:
    gold = SHARED_DATA.load_bundle(config)
    macro_state, macro_evidence = load_macro_state(config)
    return ResearchInputs(
        gold=gold,
        macro_state=macro_state,
        evidence={"gold": gold.evidence, "fred": macro_evidence},
    )
