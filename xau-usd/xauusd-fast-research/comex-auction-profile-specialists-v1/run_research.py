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
REPO_ROOT = RESEARCH_ROOT.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auction import FAMILIES, generate_candidates, load_cache, sha256_file  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "comex_auction_shared_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
ENGINE = load_module(
    "comex_auction_execution_engine",
    RESEARCH_ROOT / "ml-candidate-rankers-v1" / "src" / "engine.py",
)


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


def verify_contract_lock(config: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    lock = json.loads(path.read_text(encoding="utf-8"))
    for relative, expected in lock["files"].items():
        actual = sha256_file(ROOT / relative)
        if actual != expected:
            raise ValueError(f"Contract file changed after lock: {relative} ({actual} != {expected})")
    combined = hashlib.sha256(
        "\n".join(
            f"{name}:{digest}" for name, digest in sorted(lock["files"].items())
        ).encode("ascii")
    ).hexdigest()
    if combined != lock["combined_sha256"]:
        raise ValueError("Combined contract hash is invalid")
    return lock


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
        raise ValueError("Mechanical candidates contain duplicate deterministic IDs")
    return result


def select_family_trades(trades: pd.DataFrame, execution: dict[str, Any]) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    scored = trades.copy()
    scored["model_score"] = 0.0
    selected = ENGINE._select_trades(scored, float("-inf"), execution)
    return selected.drop(columns=["model_score"], errors="ignore")


def label_candidates(candidates: pd.DataFrame, m5: pd.DataFrame, execution: dict[str, Any]) -> pd.DataFrame:
    if not candidates.empty:
        return ENGINE.label_candidates(candidates, m5, execution)
    empty = candidates.copy()
    empty["entry_time"] = pd.Series(dtype="datetime64[ns, UTC]")
    empty["exit_time"] = pd.Series(dtype="datetime64[ns, UTC]")
    empty["stress_net_r"] = pd.Series(dtype=float)
    empty["current_account_feasible"] = pd.Series(dtype=bool)
    return empty


def unopened_stage(family: str, stage: str) -> dict[str, Any]:
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
    family_candidates: pd.DataFrame,
    m5: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[list[pd.DataFrame], list[dict[str, Any]], dict[str, Any], bool]:
    windows = config["windows"]
    execution = config["execution"]
    pre_exam_end = pd.Timestamp(windows["development"][1])
    pre_exam_candidates = family_candidates.loc[
        family_candidates["signal_time"] < pre_exam_end
    ]
    pre_exam_labels = label_candidates(pre_exam_candidates, m5, execution)
    label_frames = [pre_exam_labels] if not pre_exam_labels.empty else []
    selected_frames: list[pd.DataFrame] = []
    rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {}
    eligible = True
    for stage in ("fit", "development"):
        start, end = map(pd.Timestamp, windows[stage])
        stage_rows = pre_exam_labels.loc[
            (pre_exam_labels["entry_time"] >= start) & (pre_exam_labels["entry_time"] < end)
        ]
        selected = select_family_trades(stage_rows, execution)
        if not selected.empty:
            selected = selected.copy()
            selected["stage"] = stage
            selected_frames.append(selected)
        metrics = ENGINE.metrics(
            selected,
            ENGINE._source_days(m5, start, end),
            int(config["gates"][stage]["top_winners_removed"]),
        )
        raw_pass, checks = ENGINE.evaluate_gate(metrics, config["gates"][stage])
        promoted = bool(eligible and raw_pass)
        status = "PASS" if promoted else "FAIL" if eligible else "INELIGIBLE"
        rows.append(
            {
                "family_id": family,
                "stage": stage,
                "decision_eligible": eligible,
                "raw_gate_pass": raw_pass,
                "promoted": promoted,
                "status": status,
                **metrics,
            }
        )
        audit[stage] = {
            "decision_eligible": eligible,
            "raw_gate_pass": raw_pass,
            "promoted": promoted,
            "status": status,
            "checks": checks,
            "metrics": metrics,
        }
        eligible = promoted

    if not eligible:
        row = unopened_stage(family, "exam")
        rows.append(row)
        audit["exam"] = row
        return label_frames, selected_frames, rows, audit, False

    exam_start, exam_end = map(pd.Timestamp, windows["exam"])
    exam_candidates = family_candidates.loc[
        (family_candidates["signal_time"] >= exam_start)
        & (family_candidates["signal_time"] < exam_end)
    ]
    exam_labels = label_candidates(exam_candidates, m5, execution)
    if not exam_labels.empty:
        label_frames.append(exam_labels)
    selected = select_family_trades(exam_labels, execution)
    if not selected.empty:
        selected = selected.copy()
        selected["stage"] = "exam"
        selected_frames.append(selected)
    metrics = ENGINE.metrics(
        selected,
        ENGINE._source_days(m5, exam_start, exam_end),
        int(config["gates"]["exam"]["top_winners_removed"]),
    )
    raw_pass, checks = ENGINE.evaluate_gate(metrics, config["gates"]["exam"])
    row = {
        "family_id": family,
        "stage": "exam",
        "decision_eligible": True,
        "raw_gate_pass": raw_pass,
        "promoted": raw_pass,
        "status": "PASS" if raw_pass else "FAIL",
        **metrics,
    }
    rows.append(row)
    audit["exam"] = {**row, "checks": checks}
    return label_frames, selected_frames, rows, audit, bool(raw_pass)


def render_report(payload: dict[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD COMEX Auction-Profile Specialists V1 Result",
        "",
        f"Decision: **{payload['decision']}**",
        "",
        "Research only. No Python prediction, EA, demo, live, or broker authority is granted.",
        "",
        "| Family | Stage | Status | Trades | Trades/day | Stress PF | Avg R | Drawdown R | Top five removed R |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in stages.to_dict("records"):
        def value(name: str, digits: int = 3) -> str:
            item = row.get(name)
            return "SEALED" if item is None or pd.isna(item) else f"{item:.{digits}f}"

        lines.append(
            f"| `{row['family_id']}` | {row['stage']} | {row['status']} | "
            f"{value('trades', 0)} | {value('trades_per_source_day')} | "
            f"{value('stress_pf')} | {value('average_stress_r')} | "
            f"{value('closed_drawdown_r')} | {value('top_winners_removed_stress_net_r')} |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "comex_auction_profile_specialists_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    lock = verify_contract_lock(config)
    gold = DATA.load_bundle(config)
    auction, auction_evidence = load_cache(config)
    m5 = gold.bars["M5"]
    candidates = add_candidate_ids(generate_candidates(m5, auction, config))

    all_labels: list[pd.DataFrame] = []
    all_selected: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {}
    survivors: list[str] = []
    for family in FAMILIES:
        labels, selected, rows, family_audit, survived = evaluate_family(
            family,
            candidates.loc[candidates["family_id"].eq(family)],
            m5,
            config,
        )
        all_labels.extend(labels)
        all_selected.extend(selected)
        metric_rows.extend(rows)
        audit[family] = family_audit
        if survived:
            survivors.append(family)

    labels = pd.concat(all_labels, ignore_index=True) if all_labels else pd.DataFrame()
    selected = pd.concat(all_selected, ignore_index=True) if all_selected else pd.DataFrame()
    stages = pd.DataFrame(metric_rows)
    decision = "PROMOTE_AUCTION_PROFILE_SURVIVORS" if survivors else "REJECT_COMEX_AUCTION_PROFILE_V1"
    interpretation = (
        "At least one unchanged auction-profile family passed fit, development, and the sealed exam. "
        "It remains research-only pending independent implementation and prospective evidence."
        if survivors
        else "No unchanged auction-profile family cleared the chronological firewall. "
        "The V1 mechanisms are closed and must not be threshold-tuned against these outcomes."
    )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "interpretation": interpretation,
        "survivors": survivors,
        "contract_hash": lock["combined_sha256"],
        "mechanical_candidate_rows": int(len(candidates)),
        "opened_label_rows": int(len(labels)),
        "selected_trade_rows": int(len(selected)),
        "gate_audit": audit,
        "data_evidence": {"gold": gold.evidence, "comex_auction": auction_evidence},
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output / config["outputs"]["candidate_ledger"], index=False, lineterminator="\n")
    labels.to_csv(output / "COMEX_AUCTION_PROFILE_OPENED_LABELS.csv", index=False, lineterminator="\n")
    selected.to_csv(output / config["outputs"]["selected_trade_ledger"], index=False, lineterminator="\n")
    stages.to_csv(output / config["outputs"]["stage_metrics"], index=False, lineterminator="\n")
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(
        render_report(payload, stages), encoding="utf-8"
    )
    manifest = {
        "contract_hash": lock["combined_sha256"],
        "config_sha256": sha256_file(config_path),
        "auction_source_sha256": sha256_file(ROOT / "src" / "auction.py"),
        "runner_sha256": sha256_file(Path(__file__)),
        "execution_engine_sha256": sha256_file(
            RESEARCH_ROOT / "ml-candidate-rankers-v1" / "src" / "engine.py"
        ),
        "gold_feature_sha256": gold.evidence["feature_sha256"],
        "comex_cache_sha256": auction_evidence["cache_sha256"],
        "mechanical_candidate_rows": int(len(candidates)),
        "opened_label_rows": int(len(labels)),
        "selected_trade_rows": int(len(selected)),
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(
        json.dumps(
            {
                "decision": decision,
                "survivors": survivors,
                "candidates": len(candidates),
                "opened_labels": len(labels),
                "selected": len(selected),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
