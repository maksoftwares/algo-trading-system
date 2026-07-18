from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from campaign import simulate_variant  # noqa: E402
from foundation import ROUTER, SCORE, load_foundation  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _self_hash(payload: dict[str, Any]) -> str:
    work = dict(payload)
    work.pop("contract_sha256", None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _verify_record(record: dict[str, Any], base: Path, label: str) -> None:
    path = (base / str(record["path"])).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} path escaped its root: {path}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != int(record["bytes"]):
        raise ValueError(f"{label} size mismatch: {record['path']}")
    if sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} hash mismatch: {record['path']}")


def verify_lock(config: dict[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening outcomes")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if _self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for item in lock["package_files"] + lock["dependency_files"]:
        _verify_record(item, REPO, "repository")
    storage = Path(
        os.environ.get(
            str(config["source"]["storage_environment_variable"]),
            str(config["source"]["default_storage_root"]),
        )
    ).resolve()
    for item in lock["external_files"]:
        _verify_record(item, storage, "external")
    manifest_path = output / config["outputs"]["manifest"]
    if sha256_file(manifest_path) != str(lock["manifest_sha256"]):
        raise ValueError("Manifest changed after contract lock")
    if len(pd.read_csv(manifest_path)) != int(lock["attempt_count"]):
        raise ValueError("Manifest count changed after contract lock")
    return lock


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if math.isnan(number):
            return None
        if math.isinf(number):
            return "Infinity" if number > 0 else "-Infinity"
        return number
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_json_value(payload), indent=2, sort_keys=True, ensure_ascii=True)
        + "\n",
        encoding="utf-8",
    )


def _render(result: dict[str, Any], shortlist: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD Macro-Regime Routing V1 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        f"Attempts completed: **{result['attempts_completed']}**",
        f"Economic passes: **{result['economic_pass_rows']}**",
        f"FDR-supported finalists: **{result['statistical_finalist_rows']}**",
        "",
        "| Owner | Attempts | Economic passes | Best min-era PF | Best whole PF | Max trades |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in result["owner_summary"]:
        lines.append(
            f"| {item['regime_owner']} | {item['attempts']} | "
            f"{item['economic_passes']} | {item['best_minimum_era_stress_pf']:.3f} | "
            f"{item['best_whole_stress_pf']:.3f} | {item['maximum_trades']} |"
        )
    lines.extend(["", "## Shortlist", ""])
    if shortlist.empty:
        lines.append("No definition passed every registered economic gate.")
    else:
        lines.extend(
            [
                "| Attempt | Owner | Mechanic | Geometry | Trades | PF | Min-era PF | q |",
                "|---:|---|---|---|---:|---:|---:|---:|",
            ]
        )
        for row in shortlist.itertuples(index=False):
            lines.append(
                f"| {int(row.attempt_no)} | {row.regime_owner} | {row.mechanic} | "
                f"{row.geometry_id} | {int(row.whole_trades)} | "
                f"{float(row.whole_stress_pf):.3f} | "
                f"{float(row.minimum_era_stress_pf):.3f} | "
                f"{float(row.daily_fdr_qvalue):.6f} |"
            )
    lines.extend(
        [
            "",
            "Historical periods remain discovery evidence. Exact raw-tick replay and prospective shadow evidence are required before promotion.",
            "Shock remains abstain. No result authorizes training or execution.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "macro_regime_routing_v1.json").read_text(encoding="utf-8")
    )
    lock = verify_lock(config)
    output = ROOT / config["outputs"]["directory"]
    result_path = output / config["outputs"]["result_json"]
    if result_path.exists():
        raise FileExistsError(
            "V1 outcomes already exist; same-version reruns are forbidden"
        )
    manifest = pd.read_csv(output / config["outputs"]["manifest"])
    foundation = load_foundation(config)
    outcomes: dict[tuple[int, int, str], dict[str, Any] | None] = {}
    metric_rows: list[dict[str, Any]] = []
    economic_trades: list[pd.DataFrame] = []
    for number, row in enumerate(manifest.itertuples(index=False), 1):
        trades = simulate_variant(
            foundation.decisions,
            foundation.arrays,
            row,
            config,
            outcomes,
            ROUTER.simulate_fixed_trade,
        )
        metrics = SCORE.score_variant(trades, foundation.decisions, config)
        metric_rows.append({**row._asdict(), **metrics})
        if bool(metrics["economic_pass"]):
            economic_trades.append(
                trades.assign(
                    attempt_no=int(row.attempt_no), variant_id=str(row.variant_id)
                )
            )
        if number % 50 == 0:
            print(
                f"scored={number}/1000 economic={sum(bool(item['economic_pass']) for item in metric_rows)} "
                f"cached_outcomes={len(outcomes)}",
                flush=True,
            )
    metrics = pd.DataFrame(metric_rows).sort_values("attempt_no", kind="mergesort")
    if len(metrics) != int(config["selection"]["total_attempts"]):
        raise ValueError("Scored attempt count differs from contract")
    metrics["daily_fdr_qvalue"] = SCORE.bh_adjust(metrics["daily_pvalue"])
    metrics["statistical_pass"] = metrics["daily_fdr_qvalue"].le(
        float(config["selection"]["false_discovery_rate"])
    )
    economic = (
        metrics.loc[metrics["economic_pass"]]
        .copy()
        .sort_values(
            [
                "daily_fdr_qvalue",
                "minimum_era_stress_pf",
                "whole_stress_pf",
                "whole_trades",
                "attempt_no",
            ],
            ascending=[True, False, False, False, True],
            kind="mergesort",
        )
    )
    maximum = int(config["selection"]["maximum_finalists_per_mechanic"])
    shortlist = economic.groupby(["regime_owner", "mechanic"], sort=True).head(maximum)
    statistical = shortlist.loc[shortlist["statistical_pass"]]
    if not statistical.empty:
        decision = "MACRO_REGIME_ROUTING_FDR_FINALISTS_FOUND"
    elif not shortlist.empty:
        decision = "MACRO_REGIME_ROUTING_ECONOMIC_ONLY_FINALISTS_FOUND"
    else:
        decision = "NO_MACRO_REGIME_ROUTING_V1_ECONOMIC_FINALIST"
    if economic_trades:
        selected = pd.concat(economic_trades, ignore_index=True)
        selected = selected.loc[
            selected["attempt_no"].isin(shortlist["attempt_no"])
        ].sort_values(["attempt_no", "entry_time"], kind="mergesort")
    else:
        selected = pd.DataFrame(
            columns=[
                "attempt_no",
                "variant_id",
                "regime_owner",
                "mechanic",
                "signal_time",
                "entry_time",
                "exit_time",
                "stress_net_r",
            ]
        )
    owner_summary = []
    for owner, group in metrics.groupby("regime_owner", sort=True):
        owner_summary.append(
            {
                "regime_owner": owner,
                "attempts": int(len(group)),
                "economic_passes": int(group["economic_pass"].sum()),
                "fdr_economic_passes": int(
                    (group["economic_pass"] & group["statistical_pass"]).sum()
                ),
                "best_minimum_era_stress_pf": float(
                    group["minimum_era_stress_pf"].max()
                ),
                "best_whole_stress_pf": float(group["whole_stress_pf"].max()),
                "maximum_trades": int(group["whole_trades"].max()),
            }
        )
    result = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "attempt_first": int(metrics["attempt_no"].min()),
        "attempt_last": int(metrics["attempt_no"].max()),
        "attempts_completed": int(len(metrics)),
        "cumulative_campaign_attempts": int(metrics["attempt_no"].max()),
        "economic_pass_rows": int(metrics["economic_pass"].sum()),
        "economic_shortlist_rows": int(len(shortlist)),
        "statistical_finalist_rows": int(len(statistical)),
        "owner_summary": owner_summary,
        "data_evidence": foundation.evidence,
        "execution_evidence": {
            "native_dukas_bid_ask": True,
            "broker_spread_substitution": False,
            "cached_unique_outcomes": int(len(outcomes)),
            "same_bar_priority": config["execution"]["same_bar_priority"],
        },
        "authorization": {
            "historical_periods_are_discovery_only": True,
            "exact_raw_tick_confirmation_required": True,
            "prospective_shadow_required": True,
            "shock_is_abstain": True,
            "training_authorized": False,
            "execution_authorized": False,
            "research_only": True,
        },
    }
    metrics_path = output / config["outputs"]["metrics"]
    shortlist_path = output / config["outputs"]["shortlist"]
    selected_path = output / config["outputs"]["selected_trades"]
    markdown_path = output / config["outputs"]["result_markdown"]
    metrics.to_csv(metrics_path, index=False, lineterminator="\n")
    shortlist.to_csv(shortlist_path, index=False, lineterminator="\n")
    selected.to_csv(selected_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    markdown_path.write_text(_render(result, shortlist), encoding="utf-8")
    names = [
        config["outputs"]["contract_lock"],
        config["outputs"]["manifest"],
        config["outputs"]["metrics"],
        config["outputs"]["shortlist"],
        config["outputs"]["selected_trades"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    artifact = {
        "schema_version": "xauusd_macro_regime_routing_v1_artifacts",
        "files": {
            name: {
                "bytes": int((output / name).stat().st_size),
                "sha256": sha256_file(output / name),
            }
            for name in names
        },
    }
    write_json(output / config["outputs"]["artifact_manifest"], artifact)
    print(json.dumps(_json_value(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
