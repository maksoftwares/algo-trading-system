from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.shared_audit import (
    post_route_limit_checks,
    route_v98_candidates,
    shared_window_metrics,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "causal_event_nearmiss_ranker_v98.json"
PREFIX = "CAUSAL_EVENT_NEARMISS_RANKER_V98"
RESULT_PATH = OUTPUT / f"{PREFIX}_SHARED_AUDIT.json"
MARKER_PATH = OUTPUT / f"{PREFIX}_SHARED_OUTCOMES_OPENED.json"
WINDOWS_PATH = OUTPUT / f"{PREFIX}_SHARED_WINDOWS.csv"
ACCEPTED_PATH = OUTPUT / f"{PREFIX}_SHARED_ACCEPTED_TRADES.parquet"
DECISIONS_PATH = OUTPUT / f"{PREFIX}_SHARED_ROUTING_DECISIONS.parquet"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0.0 else None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    output = frame.copy()
    if "checks" in output:
        output["checks_json"] = output.pop("checks").map(
            lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
        )
    output.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _write_parquet(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_parquet(temporary, index=False, compression="zstd")
    os.replace(temporary, path)


def _load_final_candidates(
    run: Any, contract_hash: str
) -> tuple[pd.DataFrame, list[str]]:
    final = run._verify_advancement("final", contract_hash)
    policy_ids = [str(value) for value in final["selected_policy_ids"]]
    if not policy_ids:
        raise RuntimeError(
            "V98 shared audit is sealed because Final selected no policy"
        )
    frames = []
    for stage in run.STAGES:
        run._verify_advancement(stage, contract_hash)
        path = run._trades_path(stage)
        if not path.is_file():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path, dtype={"policy_id": str})
        if frame.empty:
            continue
        selected = frame.loc[frame["policy_id"].astype(str).isin(policy_ids)].copy()
        if not selected.empty:
            frames.append(selected.assign(source_stage=stage))
    if not frames:
        raise RuntimeError("Final V98 policies have no staged trade ledger")
    candidates = pd.concat(frames, ignore_index=True)
    if set(candidates["policy_id"].astype(str)) != set(policy_ids):
        raise ValueError("A Final V98 policy is missing from the staged trade ledgers")
    return candidates, policy_ids


def main() -> int:
    if MARKER_PATH.exists() or RESULT_PATH.exists():
        raise RuntimeError("V98 shared audit has already been opened")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    run = _load_module(
        "causal_event_nearmiss_ranker_v98_shared_run", ROOT / "run_research.py"
    )
    lock, lock_module = run._verify_contract(config)
    contract_hash = str(lock["contract_sha256"])
    candidates, policy_ids = _load_final_candidates(run, contract_hash)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _write_json(
        MARKER_PATH,
        {
            "schema_version": "xauusd_causal_event_nearmiss_ranker_v98_shared_stage_open",
            "opened_utc": datetime.now(UTC).isoformat(),
            "contract_sha256": contract_hash,
            "research_model_fitting_authorized": True,
            "deployment_model_training_authorized": False,
            "execution_authorized": False,
        },
    )
    paths = lock_module.contract_paths(config)
    shared = config["shared_account"]
    v59_config = json.loads(paths["shared/v59_config"].read_text(encoding="utf-8"))
    v60_config = json.loads(paths["shared/v60_config"].read_text(encoding="utf-8"))
    v60_result = json.loads(paths["shared/v60_result"].read_text(encoding="utf-8"))
    if not bool(v60_result["passed"]):
        raise ValueError("Frozen V60 baseline did not pass")
    account = v59_config["account"]
    if int(account["maximum_addon_open_positions"]) != int(
        shared["maximum_addon_open_positions"]
    ):
        raise ValueError("V98 add-on position limit differs from frozen V59")
    if float(account["maximum_addon_concurrent_initial_risk_usd"]) != float(
        shared["maximum_addon_concurrent_initial_risk_usd"]
    ):
        raise ValueError("V98 add-on risk limit differs from frozen V59")
    for key in ("drawdown_suspend_usd", "drawdown_resume_usd"):
        if float(account[key]) != float(shared[key]):
            raise ValueError(f"V98 {key} differs from frozen V59")
    floating = v60_config["floating_equity"]
    if float(floating["capital_buffer_multiplier"]) != float(
        shared["capital_buffer_multiplier"]
    ):
        raise ValueError("V98 capital buffer differs from frozen V60")
    if float(floating["maximum_allowed_drawdown_usd"]) != float(
        shared["maximum_buffered_floating_drawdown_usd"]
    ):
        raise ValueError("V98 floating drawdown cap differs from frozen V60")

    baseline = pd.read_parquet(paths["shared/v60_price_ledger"])
    accepted, decisions = route_v98_candidates(baseline, candidates, shared)
    windows = shared_window_metrics(
        baseline,
        accepted,
        v60_config["windows"],
        config["gates"],
        shared,
    )
    combined_ledger = pd.concat([baseline, accepted], ignore_index=True, sort=False)
    v60_audit = _load_module(
        "causal_event_nearmiss_ranker_v98_v60_audit",
        paths["shared/v60_audit_module"],
    )
    bars, market_audit = v60_audit.load_m5_bars(v60_config["market_data"])
    frozen_market_audit = v60_result["market_data_audit"]
    for key in (
        "bars",
        "first_bar_utc",
        "last_bar_utc",
        "legacy_bid_manifest_sha256",
        "legacy_ask_manifest_sha256",
    ):
        if market_audit[key] != frozen_market_audit[key]:
            raise ValueError(f"V60 market-data audit changed: {key}")
    curve = v60_audit.floating_curve(
        bars,
        combined_ledger,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(v60_config["floating_equity"]["bar_minutes"]),
    )
    drawdown = v60_audit.envelope_drawdown(curve)
    buffered_drawdown = float(drawdown["maximum_drawdown_usd"]) * float(
        shared["capital_buffer_multiplier"]
    )
    limit_checks = post_route_limit_checks(curve, shared)
    checks = {
        "all_required_windows_pass": bool(windows["passed"].all()),
        "buffered_floating_drawdown": buffered_drawdown
        <= float(shared["maximum_buffered_floating_drawdown_usd"]),
        **limit_checks,
    }
    passed = bool(all(checks.values()))
    result = {
        "schema_version": "xauusd_causal_event_nearmiss_ranker_v98_shared_audit",
        "created_utc": datetime.now(UTC).isoformat(),
        "contract_sha256": contract_hash,
        "final_policy_ids": policy_ids,
        "candidate_v98_trades": int(len(candidates)),
        "accepted_v98_trades": int(len(accepted)),
        "routing_reason_counts": decisions["reason"].value_counts().to_dict(),
        "windows": windows.to_dict(orient="records"),
        "floating_drawdown": drawdown,
        "buffered_floating_drawdown_usd": buffered_drawdown,
        "market_data_audit": market_audit,
        "maximum_open_addons": int(curve["open_addons"].max()),
        "maximum_addon_initial_risk_usd": float(curve["addon_initial_risk_usd"].max()),
        "checks": checks,
        "passed": passed,
        "decision": "V98_SHARED_V59_V60_PASS" if passed else "V98_SHARED_V59_V60_FAIL",
        "v59_v60_modified": False,
        "research_model_fitting_authorized": True,
        "deployment_model_training_authorized": False,
        "execution_authorized": False,
    }
    _write_csv(WINDOWS_PATH, windows)
    _write_parquet(ACCEPTED_PATH, accepted)
    _write_parquet(DECISIONS_PATH, decisions)
    _write_json(RESULT_PATH, result)
    run._update_artifact_manifest(contract_hash)
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True, allow_nan=False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
