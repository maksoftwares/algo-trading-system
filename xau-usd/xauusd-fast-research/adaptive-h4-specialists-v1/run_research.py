from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from adaptive import FAMILIES, generate_candidates, score_stage  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "adaptive_h4_shared_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
ENGINE = load_module(
    "adaptive_h4_execution_engine",
    RESEARCH_ROOT / "ml-candidate-rankers-v1" / "src" / "engine.py",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_candidate_ids(candidates: pd.DataFrame) -> pd.DataFrame:
    result = candidates.copy()
    payload = (
        result["family_id"].astype(str)
        + "|"
        + result["signal_time"].astype(str)
        + "|"
        + result["direction"].astype(str)
    )
    result.insert(
        0,
        "candidate_id",
        payload.map(lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()),
    )
    if result["candidate_id"].duplicated().any():
        raise ValueError("Duplicate deterministic candidate IDs")
    return result


def robust_label_candidates(
    candidates: pd.DataFrame, m5: pd.DataFrame, execution: dict[str, Any]
) -> pd.DataFrame:
    if candidates.empty:
        empty = candidates.copy()
        empty["entry_time"] = pd.Series(dtype="datetime64[ns, UTC]")
        empty["exit_time"] = pd.Series(dtype="datetime64[ns, UTC]")
        empty["stress_net_r"] = pd.Series(dtype=float)
        empty["current_account_feasible"] = pd.Series(dtype=bool)
        return empty
    arrays = ENGINE._execution_arrays(m5)
    rows: list[dict[str, Any]] = []
    for candidate in candidates.itertuples(index=False):
        outcome = ENGINE._label_candidate(arrays, candidate, execution)
        if outcome is not None:
            rows.append({**candidate._asdict(), **outcome})
    if not rows:
        return robust_label_candidates(candidates.iloc[0:0], m5, execution)
    return pd.DataFrame(rows).sort_values(
        ["signal_time", "family_id"], kind="mergesort"
    ).reset_index(drop=True)


def source_days(m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        m5.loc[
            (m5["bar_start_utc"] >= start) & (m5["bar_start_utc"] < end),
            "bar_start_utc",
        ].dt.date.nunique()
    )


def unopened(family: str, stage: str) -> dict[str, Any]:
    return {
        "family_id": family,
        "stage": stage,
        "decision_eligible": False,
        "raw_gate_pass": False,
        "promoted": False,
        "status": "NOT_OPENED_PRIOR_STAGE_FAIL",
        "trades": None,
        "source_days": None,
        "trades_per_source_day": None,
        "stress_net_r": None,
        "stress_pf": None,
        "average_stress_r": None,
        "positive_active_month_share": None,
        "closed_drawdown_r": None,
        "top_winners_removed_stress_net_r": None,
        "current_account_feasible_share": None,
    }


def evaluate_family(
    family: str,
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[list[pd.DataFrame], list[pd.DataFrame], list[dict[str, Any]], list[dict[str, Any]], bool]:
    labels: list[pd.DataFrame] = []
    selected_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    opened = pd.DataFrame()
    eligible = True
    for stage in ("validation", "internal_test", "exam"):
        start, end = map(pd.Timestamp, config["windows"][stage])
        if not eligible:
            metric_rows.append(unopened(family, stage))
            diagnostic_rows.append(
                {
                    "family_id": family,
                    "stage": stage,
                    "status": "NOT_OPENED_PRIOR_STAGE_FAIL",
                }
            )
            continue
        stage_candidates = candidates.loc[candidates["signal_time"] < end]
        new_candidates = stage_candidates.loc[
            ~stage_candidates["candidate_id"].isin(
                opened["candidate_id"] if not opened.empty else []
            )
        ]
        new_labels = robust_label_candidates(new_candidates, m5, config["execution"])
        if not new_labels.empty:
            labels.append(new_labels)
            opened = pd.concat([opened, new_labels], ignore_index=True)
        selected, diagnostics = score_stage(opened, start, end, config)
        if not selected.empty:
            selected = selected.copy()
            selected["stage"] = stage
            selected_frames.append(selected)
        gate = config["gates"][stage]
        values = ENGINE.metrics(
            selected,
            source_days(m5, start, end),
            int(gate["top_winners_removed"]),
        )
        raw_pass, checks = ENGINE.evaluate_gate(values, gate)
        metric_rows.append(
            {
                "family_id": family,
                "stage": stage,
                "decision_eligible": True,
                "raw_gate_pass": raw_pass,
                "promoted": raw_pass,
                "status": "PASS" if raw_pass else "FAIL",
                **values,
            }
        )
        diagnostic_rows.extend(
            {"family_id": family, "stage": stage, **item} for item in diagnostics
        )
        diagnostic_rows.append(
            {
                "family_id": family,
                "stage": stage,
                "status": "STAGE_GATE",
                "gate_pass": raw_pass,
                "gate_checks": json.dumps(checks, sort_keys=True),
            }
        )
        eligible = bool(raw_pass)
    return labels, selected_frames, metric_rows, diagnostic_rows, eligible


def verify_lock(config: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    lock = json.loads(path.read_text(encoding="utf-8"))
    for relative, expected in lock["files"].items():
        if sha256_file((ROOT / relative).resolve()) != expected:
            raise ValueError(f"Contract changed after lock: {relative}")
    return lock


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def render(payload: dict[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD Adaptive H4 Specialists V1 Result",
        "",
        f"Decision: **{payload['decision']}**",
        "",
        "| Family | Stage | Status | Trades | Trades/day | Stress PF | Avg R | Drawdown R | Top five removed R |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in stages.to_dict("records"):

        def show(key: str, digits: int = 3) -> str:
            value = row.get(key)
            return "SEALED" if value is None or pd.isna(value) else f"{value:.{digits}f}"

        lines.append(
            f"| `{row['family_id']}` | {row['stage']} | {row['status']} | "
            f"{show('trades', 0)} | {show('trades_per_source_day')} | "
            f"{show('stress_pf')} | {show('average_stress_r')} | "
            f"{show('closed_drawdown_r')} | "
            f"{show('top_winners_removed_stress_net_r')} |"
        )
    lines.extend(
        [
            "",
            "Each six-month block was scored by a model trained only on earlier exited trades.",
            "Later-stage outcomes were not opened after a prior-stage failure.",
            "No result grants Python, EA, demo, live, or broker authority.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "adaptive_h4_specialists_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    lock = verify_lock(config)
    bundle = DATA.load_bundle(config)
    m5, h4 = bundle.bars["M5"], bundle.bars["H4"]
    candidates = add_candidate_ids(generate_candidates(h4, config))
    label_frames: list[pd.DataFrame] = []
    selected_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    survivors: list[str] = []
    for family in FAMILIES:
        labels, selected, metrics, diagnostics, survived = evaluate_family(
            family,
            candidates.loc[candidates["family_id"].eq(family)],
            m5,
            config,
        )
        label_frames.extend(labels)
        selected_frames.extend(selected)
        metric_rows.extend(metrics)
        diagnostic_rows.extend(diagnostics)
        if survived:
            survivors.append(family)

    opened = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame()
    selected = (
        pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame()
    )
    stages = pd.DataFrame(metric_rows)
    diagnostics = pd.DataFrame(diagnostic_rows)
    decision = (
        "PROMOTE_ADAPTIVE_H4_SURVIVORS_REQUIRES_FORWARD_SHADOW"
        if survivors
        else "REJECT_ADAPTIVE_H4_SPECIALISTS_V1"
    )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "survivors": survivors,
        "contract_hash": lock["combined_sha256"],
        "mechanical_candidate_rows": int(len(candidates)),
        "opened_label_rows": int(len(opened)),
        "selected_trade_rows": int(len(selected)),
        "data_evidence": bundle.evidence,
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output / config["outputs"]["candidate_ledger"], index=False)
    opened.to_csv(output / config["outputs"]["opened_label_ledger"], index=False)
    selected.to_csv(output / config["outputs"]["selected_trade_ledger"], index=False)
    stages.to_csv(output / config["outputs"]["stage_metrics"], index=False)
    diagnostics.to_csv(output / config["outputs"]["model_diagnostics"], index=False)
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(
        render(payload, stages), encoding="utf-8"
    )
    write_json(
        output / config["outputs"]["manifest"],
        {
            "contract_hash": lock["combined_sha256"],
            "config_sha256": sha256_file(config_path),
            "adaptive_sha256": sha256_file(ROOT / "src" / "adaptive.py"),
            "runner_sha256": sha256_file(Path(__file__)),
            "candidate_rows": int(len(candidates)),
            "opened_label_rows": int(len(opened)),
            "selected_trade_rows": int(len(selected)),
        },
    )
    print(
        json.dumps(
            {
                "decision": decision,
                "survivors": survivors,
                "candidates": len(candidates),
                "opened_labels": len(opened),
                "selected": len(selected),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
