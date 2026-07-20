from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


def load_v58_audit(path: Path) -> Any:
    name = "xau_one_trade_per_day_v58_audit_for_v59"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load V58 audit module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def filter_broker_expressible_core(
    core: pd.DataFrame,
    router_trades: pd.DataFrame,
    settings: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    result = core.copy()
    for column in ("signal_time", "entry_time", "exit_time"):
        result[column] = pd.to_datetime(result[column], utc=True, errors="raise")
    r5_mask = result["specialist_id"].eq(settings["r5_specialist_id"])
    r5_core = result.loc[r5_mask].copy()
    source = router_trades.loc[
        router_trades["attempt_no"].eq(int(settings["r5_router_attempt"]))
    ].copy()
    if len(source) != int(settings["expected_r5_rows"]):
        raise ValueError(f"R5 router row count changed: {len(source)}")
    if source["candidate_id"].astype(str).duplicated().any():
        raise ValueError("R5 router candidate IDs are not unique")
    if len(r5_core) != int(settings["expected_r5_rows"]):
        raise ValueError(f"V58 R5 Core row count changed: {len(r5_core)}")
    joined = r5_core.merge(
        source[["candidate_id", "risk_weight"]],
        left_on="trade_id",
        right_on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    if joined["risk_weight"].isna().any():
        raise ValueError("A V58 R5 row has no router-weight match")
    full = np.isclose(
        joined["risk_weight"].to_numpy(dtype=float),
        float(settings["full_weight"]),
        rtol=0.0,
        atol=float(settings["weight_absolute_tolerance"]),
    )
    if int(full.sum()) != int(settings["expected_full_weight_rows"]):
        raise ValueError("R5 full-weight row count changed")
    if int((~full).sum()) != int(settings["expected_fractional_rows"]):
        raise ValueError("R5 fractional row count changed")
    keep_ids = set(joined.loc[full, "trade_id"].astype(str))
    rejected = joined.loc[~full].copy()
    rejected["decision_reason"] = "SUB_MINIMUM_FRACTIONAL_LOT_REJECTED"
    kept = result.loc[~r5_mask | result["trade_id"].astype(str).isin(keep_ids)].copy()
    kept["sleeve_id"] = "V59_BROKER_CORE"
    audit = {
        "r5_rows_before": int(len(joined)),
        "r5_full_weight_kept": int(full.sum()),
        "r5_fractional_rejected": int((~full).sum()),
        "minimum_fractional_weight": float(joined.loc[~full, "risk_weight"].min()),
        "maximum_fractional_weight": float(joined.loc[~full, "risk_weight"].max()),
        "fractional_rounding_used": False,
    }
    return (
        kept.sort_values(["entry_time", "trade_id"], kind="mergesort").reset_index(
            drop=True
        ),
        rejected.reset_index(drop=True),
        audit,
    )
