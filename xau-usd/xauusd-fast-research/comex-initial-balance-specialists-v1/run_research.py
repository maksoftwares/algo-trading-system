from __future__ import annotations

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

from specialists import FAMILIES, generate_candidates  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_module(
    "comex_initial_balance_base_runner",
    RESEARCH_ROOT / "comex-auction-profile-specialists-v1" / "run_research.py",
)
BASE_LABEL_CANDIDATES = BASE.label_candidates


def robust_label_candidates(
    candidates: pd.DataFrame, m5: pd.DataFrame, execution: dict[str, Any]
) -> pd.DataFrame:
    if candidates.empty:
        return BASE_LABEL_CANDIDATES(candidates, m5, execution)
    arrays = BASE.ENGINE._execution_arrays(m5)
    rows: list[dict[str, Any]] = []
    for candidate in candidates.itertuples(index=False):
        outcome = BASE.ENGINE._label_candidate(arrays, candidate, execution)
        if outcome is not None:
            rows.append({**candidate._asdict(), **outcome})
    if not rows:
        return BASE_LABEL_CANDIDATES(candidates.iloc[0:0], m5, execution)
    return pd.DataFrame(rows).sort_values(
        ["signal_time", "family_id"], kind="mergesort"
    ).reset_index(drop=True)


def verify_lock(config: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    lock = json.loads(path.read_text(encoding="utf-8"))
    for relative, expected in lock["files"].items():
        actual = BASE.sha256_file((ROOT / relative).resolve())
        if actual != expected:
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
        "# XAUUSD COMEX Initial-Balance Specialists V1 Result",
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
            f"{show('trades', 0)} | {show('trades_per_source_day')} | {show('stress_pf')} | "
            f"{show('average_stress_r')} | {show('closed_drawdown_r')} | "
            f"{show('top_winners_removed_stress_net_r')} |"
        )
    lines.extend(
        [
            "",
            "The exam was opened only for unchanged families passing fit and development.",
            "No result grants Python, EA, demo, live, or broker authority.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "comex_initial_balance_specialists_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    lock = verify_lock(config)
    gold = BASE.DATA.load_bundle(config)
    auction, auction_evidence = BASE.load_cache(config)
    m5 = gold.bars["M5"]
    candidates = BASE.add_candidate_ids(generate_candidates(m5, auction, config))
    BASE.label_candidates = robust_label_candidates

    label_frames: list[pd.DataFrame] = []
    selected_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {}
    survivors: list[str] = []
    for family in FAMILIES:
        labels, selected, rows, family_audit, survived = BASE.evaluate_family(
            family,
            candidates.loc[candidates["family_id"].eq(family)],
            m5,
            config,
        )
        label_frames.extend(labels)
        selected_frames.extend(selected)
        metric_rows.extend(rows)
        audit[family] = family_audit
        if survived:
            survivors.append(family)

    labels = pd.concat(label_frames, ignore_index=True) if label_frames else pd.DataFrame()
    selected = pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame()
    stages = pd.DataFrame(metric_rows)
    decision = "PROMOTE_INITIAL_BALANCE_SURVIVORS" if survivors else "REJECT_COMEX_INITIAL_BALANCE_V1"
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
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
    candidates.to_csv(output / config["outputs"]["candidate_ledger"], index=False)
    labels.to_csv(output / "COMEX_INITIAL_BALANCE_OPENED_LABELS.csv", index=False)
    selected.to_csv(output / config["outputs"]["selected_trade_ledger"], index=False)
    stages.to_csv(output / config["outputs"]["stage_metrics"], index=False)
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(
        render(payload, stages), encoding="utf-8"
    )
    write_json(
        output / config["outputs"]["manifest"],
        {
            "contract_hash": lock["combined_sha256"],
            "config_sha256": BASE.sha256_file(config_path),
            "specialists_sha256": BASE.sha256_file(ROOT / "src" / "specialists.py"),
            "runner_sha256": BASE.sha256_file(Path(__file__)),
            "comex_cache_sha256": auction_evidence["cache_sha256"],
            "candidate_rows": int(len(candidates)),
            "opened_label_rows": int(len(labels)),
            "selected_rows": int(len(selected)),
        },
    )
    print(json.dumps({"decision": decision, "survivors": survivors, "candidates": len(candidates), "selected": len(selected)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
