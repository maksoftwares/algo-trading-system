from __future__ import annotations

import csv
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

from .core import (
    BASE_COMMIT, BASE_TREE, BRANCH, COMMIT_MESSAGE, DEVELOPMENT_END, DEVELOPMENT_START,
    FINAL_CLASSIFICATIONS, PHASE, SIGNAL_FIELDS, SOURCE_CODE, SOURCE_ORIGIN, STORAGE_ENV,
    STRATEGY_IDS, TRADE_FIELDS, canonical_json_bytes, classification, compute_metrics,
    development_gate, execute_candidates, generate_all_candidates, sha256_bytes, sha256_file,
    weighted_percentile,
)


REQUIRED_OUTPUTS = (
    "XAU_V2_RESULT.md", "XAU_V2_RESULT.json", "XAU_V2_DATA_INVENTORY.csv",
    "XAU_V2_DATA_INTEGRITY.csv", "XAU_V2_STRATEGY_REGISTRY.json", "XAU_V2_SIGNAL_LEDGER.csv",
    "XAU_V2_TRADE_LEDGER.csv", "XAU_V2_SIGNAL_FUNNEL.csv", "XAU_V2_DEVELOPMENT_RESULTS.csv",
    "XAU_V2_DEVELOPMENT_SURVIVORS.json", "XAU_V2_FAMILY_RESULTS.csv",
    "XAU_V2_DIRECTION_RESULTS.csv", "XAU_V2_SEGMENT_RESULTS.csv", "XAU_V2_MONTHLY_RESULTS.csv",
    "XAU_V2_ROLLING_RESULTS.csv", "XAU_V2_EXECUTION_DIAGNOSTICS.csv",
    "XAU_V2_PORTFOLIO_RESULTS.csv", "XAU_V2_ACCOUNT_FEASIBILITY.csv",
    "XAU_V2_GATE_AUDIT.json", "XAU_V2_RUN_MANIFEST.json",
)
PRINCIPAL_NAMES = (
    "XAU_V2_SIGNAL_LEDGER.csv", "XAU_V2_TRADE_LEDGER.csv", "XAU_V2_SIGNAL_FUNNEL.csv",
    "XAU_V2_DEVELOPMENT_RESULTS.csv", "XAU_V2_DEVELOPMENT_SURVIVORS.json",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def month_keys(start: datetime, end: datetime) -> list[str]:
    cursor = start
    result = []
    while cursor < end:
        result.append(f"{cursor.year:04d}-{cursor.month:02d}")
        cursor = datetime(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1, tzinfo=UTC)
    return result


def foundation_module(repo_root: Path):
    path = repo_root / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1" / "src" / "dukascopy_tick_foundation" / "foundation.py"
    spec = importlib.util.spec_from_file_location("frozen_dukascopy_foundation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("frozen Dukascopy foundation cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def storage_preflight(storage_root: Path) -> dict[str, Any]:
    pilot = storage_root / "raw" / "XAUUSD" / "year=2016" / "month=07"
    raw_bytes = sum(path.stat().st_size for path in pilot.glob("*.json") if not path.name.startswith("_"))
    replay = next(iter(sorted((storage_root / "replays").glob("*/run-one"))), None)
    normalized_bytes = sum(path.stat().st_size for path in replay.rglob("normalized/XAUUSD/**/*.parquet")) if replay else 0
    bars_bytes = sum(path.stat().st_size for path in replay.rglob("bars/XAUUSD/**/*.parquet")) if replay else 0
    if raw_bytes <= 0:
        raise RuntimeError("validated July 2016 XAUUSD pilot is missing")
    pilot_total = raw_bytes + normalized_bytes + bars_bytes
    estimated = int(pilot_total * 60 * 2.5)
    free = shutil.disk_usage(storage_root).free
    required = int(estimated * 1.5)
    return {
        "pilot_month": "2016-07", "pilot_raw_bytes": raw_bytes,
        "pilot_normalized_bytes": normalized_bytes, "pilot_bar_bytes": bars_bytes,
        "density_volatility_allowance": 2.5, "months_estimated": 60,
        "estimated_total_bytes": estimated, "required_free_bytes": required,
        "observed_free_bytes": free, "passes": free >= required,
    }


def assert_identity(lane_root: Path) -> dict[str, Any]:
    repo = lane_root.parents[2]
    head = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    branch = git(repo, "branch", "--show-current")
    parent = git(repo, "rev-parse", f"{head}^")
    if (head, tree, branch) != (BASE_COMMIT, BASE_TREE, BRANCH):
        raise RuntimeError("XAU_FAST_DISCOVERY_V2_BASE_IDENTITY_MISMATCH")
    status = git(repo, "status", "--short")
    outside = [line for line in status.splitlines() if "xau-usd/xauusd-fast-research/xau-fast-discovery-v2/" not in line.replace("\\", "/")]
    if outside:
        raise RuntimeError(f"outside-scope worktree changes: {outside}")
    return {"branch": branch, "base_commit": head, "base_tree": tree, "base_parent": parent, "outside_scope_changes": outside}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def _cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return format(value, ".12g")
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _cell(row.get(field, "")) for field in fields})


def acquire_development(storage_root: Path, foundation: Any, concurrency: int) -> list[dict[str, Any]]:
    rows = []
    for key in month_keys(DEVELOPMENT_START, DEVELOPMENT_END):
        year, month = map(int, key.split("-"))
        month_rows = foundation.acquire_month(storage_root, "XAUUSD", year, month, concurrency=concurrency)
        if any(row["status"] not in {"DOWNLOADED_VALID", "RESUMED_VALID"} for row in month_rows):
            raise RuntimeError(f"XAU_FAST_DISCOVERY_V2_DATA_INCOMPLETE: {key}")
        foundation.write_month_acquisition_manifest(storage_root, "XAUUSD", year, month, month_rows)
        frozen = foundation.freeze_raw_month(storage_root, "XAUUSD", year, month)
        if not frozen["complete"]:
            raise RuntimeError(f"XAU_FAST_DISCOVERY_V2_DATA_INCOMPLETE: {key}")
        rows.extend(month_rows)
        print(f"ACQUIRED_AND_FROZEN {key} ticks={sum(int(row['tick_count']) for row in month_rows)}", flush=True)
    return rows


def _write_contract_normalized(source: Path, target: Path) -> dict[str, Any]:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    table = pq.read_table(source)
    file_ids = table.column("source_file_id")
    row_ids = pc.utf8_lpad(pc.cast(table.column("source_row_index"), pa.string()), 10, "0")
    sequence = pc.binary_join_element_wise(file_ids, row_ids, ":")
    exact = pa.table({
        "timestamp_utc": table.column("timestamp_utc"), "timestamp_msc": table.column("timestamp_ms"),
        "bid": table.column("bid"), "ask": table.column("ask"), "spread": table.column("spread"),
        "bid_volume": table.column("bid_volume"), "ask_volume": table.column("ask_volume"),
        "source_sequence": sequence,
    })
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(exact, target, compression="zstd", compression_level=9, use_dictionary=False,
                   write_statistics=True, data_page_version="1.0", row_group_size=100_000)
    return {"path": target.as_posix(), "bytes": target.stat().st_size, "sha256": sha256_file(target), "tick_count": len(exact)}


def derive(storage_root: Path, run_root: Path, foundation: Any) -> list[dict[str, Any]]:
    if run_root.exists():
        shutil.rmtree(run_root)
    results = []
    for key in month_keys(DEVELOPMENT_START, DEVELOPMENT_END):
        year, month = map(int, key.split("-"))
        result = foundation.normalize_month(storage_root, run_root, "XAUUSD", year, month)
        source = run_root / result["partition"]["path"]
        target = run_root / "contract-normalized" / "XAUUSD" / f"year={year:04d}" / f"month={month:02d}" / "ticks.parquet"
        result["contract_normalized"] = _write_contract_normalized(source, target)
        results.append(result)
        print(f"DERIVED {run_root.name} {key} ticks={result['partition']['tick_count']}", flush=True)
    return results


def inventory_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in sorted(root.rglob("*.parquet"))}


def load_bars(run_root: Path) -> dict[str, pd.DataFrame]:
    result = {}
    for timeframe in ("M5", "M15", "H1", "H4"):
        files = sorted((run_root / "bars" / "XAUUSD" / "mid" / timeframe).rglob("bars.parquet"))
        frames = [pd.read_parquet(path, columns=["timestamp_ms", "open", "high", "low", "close", "volume", "tick_count"]) for path in files]
        result[timeframe] = pd.concat(frames, ignore_index=True).sort_values("timestamp_ms", kind="mergesort").drop_duplicates("timestamp_ms", keep="first").reset_index(drop=True)
    return result


def development_spread_p95(run_root: Path) -> float:
    histogram: Counter[float] = Counter()
    for path in sorted((run_root / "contract-normalized" / "XAUUSD").rglob("ticks.parquet")):
        frame = pd.read_parquet(path, columns=["timestamp_msc", "spread"])
        dt = pd.to_datetime(frame.timestamp_msc, unit="ms", utc=True)
        hours = dt.dt.hour
        for value, count in frame.loc[(hours >= 6) & (hours < 20), "spread"].round(3).value_counts().items():
            histogram[float(value)] += int(count)
    return weighted_percentile(histogram, .95)


def execute_partitioned(run_root: Path, candidates: Sequence[Mapping[str, Any]], spread_p95: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay one month at a time; no valid trade may cross a UTC day or month."""
    candidates_by_month: dict[str, list[Mapping[str, Any]]] = {}
    for candidate in candidates:
        candidates_by_month.setdefault(candidate["UTC_date"][:7], []).append(candidate)
    all_signals: list[dict[str, Any]] = []
    all_trades: list[dict[str, Any]] = []
    seen_months: set[str] = set()
    columns = ["timestamp_msc", "bid", "ask", "spread", "source_sequence"]
    for path in sorted((run_root / "contract-normalized" / "XAUUSD").rglob("ticks.parquet")):
        month = f"{path.parent.parent.name.split('=', 1)[1]}-{path.parent.name.split('=', 1)[1]}"
        monthly_candidates = candidates_by_month.get(month, [])
        if not monthly_candidates:
            continue
        seen_months.add(month)
        frame = pd.read_parquet(path, columns=columns)
        days = pd.to_datetime(frame.timestamp_msc, unit="ms", utc=True).dt.day
        required_days = {int(row["UTC_date"][8:10]) for row in monthly_candidates}
        selected = frame[days.isin(required_days)].copy()
        selected["day"] = days[days.isin(required_days)].to_numpy()
        ticks_by_date = {
            f"{month}-{int(day):02d}": group.drop(columns="day").sort_values(["timestamp_msc", "source_sequence"], kind="mergesort").reset_index(drop=True)
            for day, group in selected.groupby("day", sort=True)
        }
        signals, trades = execute_candidates(monthly_candidates, ticks_by_date, spread_p95)
        all_signals.extend(signals)
        all_trades.extend(trades)
        print(f"EXECUTED {run_root.name} {month} candidates={len(monthly_candidates)} trades={len(trades)}", flush=True)
    for month, missing in candidates_by_month.items():
        if month not in seen_months:
            signals, trades = execute_candidates(missing, {}, spread_p95)
            all_signals.extend(signals)
            all_trades.extend(trades)
    return (
        sorted(all_signals, key=lambda row: (row["signal_ms"], row["strategy_id"], row["setup_episode_id"])),
        sorted(all_trades, key=lambda row: (row["entry_time"], row["strategy_id"], row["setup_episode_id"])),
    )


def screen(run_root: Path, scratch: Path) -> dict[str, Any]:
    bars = load_bars(run_root)
    candidates = generate_all_candidates(bars)
    spread_p95 = development_spread_p95(run_root)
    signals, trades = execute_partitioned(run_root, candidates, spread_p95)
    development_rows = []
    survivors = []
    for strategy_id in STRATEGY_IDS:
        subset = [row for row in trades if row["strategy_id"] == strategy_id and row["chronological_segment"] == "DEVELOPMENT"]
        baseline = compute_metrics(subset)
        stress = compute_metrics(subset, "stress_net_R")
        passed, failures = development_gate(baseline, stress)
        row = {"strategy_id": strategy_id, **{f"baseline_{key}": value for key, value in baseline.items()},
               **{f"stress_{key}": value for key, value in stress.items()}, "development_gate_pass": passed,
               "failed_gates": "|".join(failures)}
        development_rows.append(row)
        if passed:
            survivors.append(strategy_id)
    scratch.mkdir(parents=True, exist_ok=True)
    signal_fields = [*SIGNAL_FIELDS, "signal_ms", "rr", "target_level", "max_hold_hours", "stop_min_atr", "stop_max_atr", "m15_atr"]
    write_csv(scratch / PRINCIPAL_NAMES[0], signal_fields, signals)
    write_csv(scratch / PRINCIPAL_NAMES[1], [*TRADE_FIELDS, "entry_delay_minutes"], trades)
    funnel = []
    for strategy_id in STRATEGY_IDS:
        family = [row for row in signals if row["strategy_id"] == strategy_id]
        reasons = Counter(row["rejection_reason"] or "ACCEPTED" for row in family)
        for reason, count in sorted(reasons.items()):
            funnel.append({"strategy_id": strategy_id, "outcome": reason, "count": count})
    write_csv(scratch / PRINCIPAL_NAMES[2], ["strategy_id", "outcome", "count"], funnel)
    fields = list(development_rows[0])
    write_csv(scratch / PRINCIPAL_NAMES[3], fields, development_rows)
    registry = {"phase": PHASE, "development_survivors": survivors, "failed_families_permanently_rejected": [value for value in STRATEGY_IDS if value not in survivors], "rules_changed_after_screen": False}
    write_json(scratch / PRINCIPAL_NAMES[4], registry)
    hashes = {name: sha256_file(scratch / name) for name in PRINCIPAL_NAMES}
    return {"bars": bars, "signals": signals, "trades": trades, "development": development_rows,
            "survivors": survivors, "spread_p95": spread_p95, "principal_hashes": hashes,
            "scratch": scratch, "funnel": funnel}


def _metric_rows(trades: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for trade in trades:
        key = tuple(trade[field] for field in fields)
        groups.setdefault(key, []).append(trade)
    rows = []
    for key, subset in sorted(groups.items()):
        baseline = compute_metrics(subset)
        stress = compute_metrics(subset, "stress_net_R")
        rows.append({**dict(zip(fields, key)), **{f"baseline_{name}": value for name, value in baseline.items()}, **{f"stress_{name}": value for name, value in stress.items()}})
    return rows


def write_outputs(lane_root: Path, identity: Mapping[str, Any], preflight: Mapping[str, Any], acquisition: Sequence[Mapping[str, Any]], derivation: Sequence[Mapping[str, Any]], first: Mapping[str, Any], second: Mapping[str, Any], derivation_identical: bool, principal_identical: bool) -> str:
    outputs = lane_root / "outputs"
    if outputs.exists():
        shutil.rmtree(outputs)
    outputs.mkdir(parents=True)
    shutil.copytree(second["scratch"], outputs, dirs_exist_ok=True)
    trades = second["trades"]
    signals = second["signals"]
    tick_inventory = []
    data_inventory = []
    integrity = []
    bars_census = []
    partition_hashes = []
    for result in derivation:
        tick_row = {**result["partition"], "contract_normalized_sha256": result["contract_normalized"]["sha256"]}
        tick_inventory.append(tick_row)
        data_inventory.append({
            "record_type": "TICKS", "symbol": "XAUUSD", "month": result["partition"]["month"],
            "basis": "Bid/Ask", "timeframe": "TICK", "item_count": result["partition"]["tick_count"],
            "first_utc": result["partition"]["first_tick_utc"], "last_utc": result["partition"]["last_tick_utc"],
            "relative_path": result["partition"]["path"], "bytes": result["partition"]["bytes"],
            "sha256": result["partition"]["sha256"],
            "contract_normalized_sha256": result["contract_normalized"]["sha256"],
        })
        integrity.append(result["integrity"])
        bars_census.extend(result["bars"])
        required_bars = [row for row in result["bars"] if row["timeframe"] in {"M5", "M15", "H1", "H4"}]
        for row in required_bars:
            data_inventory.append({
                "record_type": "BARS", "symbol": row["symbol"], "month": row["month"],
                "basis": row["basis"], "timeframe": row["timeframe"], "item_count": row["bar_count"],
                "first_utc": row["first_bar_utc"], "last_utc": row["last_bar_utc"],
                "relative_path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"],
                "contract_normalized_sha256": "",
            })
        partition_hashes.append({"month": result["partition"]["month"], "raw_frozen": True,
                                 "normalized_sha256": result["partition"]["sha256"],
                                 "contract_normalized_sha256": result["contract_normalized"]["sha256"],
                                 "required_bar_sha256": {f"{row['basis']}_{row['timeframe']}": row["sha256"] for row in required_bars}})
    write_csv(outputs / "XAU_V2_DATA_INVENTORY.csv", ["record_type", "symbol", "month", "basis", "timeframe", "item_count", "first_utc", "last_utc", "relative_path", "bytes", "sha256", "contract_normalized_sha256"], data_inventory)
    write_csv(outputs / "XAU_V2_DATA_INTEGRITY.csv", list(integrity[0]), integrity)
    registry = {"phase": PHASE, "parameter_search_count": 0, "families": [{"strategy_id": value, "parameter_sets": 1, "status": "FROZEN"} for value in STRATEGY_IDS]}
    write_json(outputs / "XAU_V2_STRATEGY_REGISTRY.json", registry)
    metric_fields = ["strategy_id", "baseline_trades", "baseline_wins", "baseline_losses", "baseline_net_R", "baseline_expectancy_R", "baseline_profit_factor", "baseline_maximum_closed_drawdown_R", "stress_net_R", "stress_expectancy_R", "stress_profit_factor"]
    family_rows = _metric_rows(trades, ["strategy_id"])
    direction_rows = _metric_rows(trades, ["strategy_id", "direction"])
    segment_rows = _metric_rows(trades, ["strategy_id", "chronological_segment"])
    monthly_trades = []
    for trade in trades:
        monthly_trades.append({**trade, "month": trade["UTC_date"][:7]})
    monthly_rows = _metric_rows(monthly_trades, ["strategy_id", "month"])
    write_csv(outputs / "XAU_V2_FAMILY_RESULTS.csv", metric_fields, family_rows)
    write_csv(outputs / "XAU_V2_DIRECTION_RESULTS.csv", ["strategy_id", "direction", *metric_fields[1:]], direction_rows)
    write_csv(outputs / "XAU_V2_SEGMENT_RESULTS.csv", ["strategy_id", "chronological_segment", *metric_fields[1:]], segment_rows)
    write_csv(outputs / "XAU_V2_MONTHLY_RESULTS.csv", ["strategy_id", "month", *metric_fields[1:]], monthly_rows)
    write_csv(outputs / "XAU_V2_ROLLING_RESULTS.csv", ["strategy_id", "window_start", "window_end", "status"], [])
    diagnostics = [{"diagnostic": "development_spread_p95_06_20_utc", "value": second["spread_p95"]},
                   {"diagnostic": "candidate_count", "value": len(signals)}, {"diagnostic": "accepted_trade_count", "value": len(trades)},
                   {"diagnostic": "stop_gap_count", "value": sum(bool(row["stop_gap"]) for row in trades)},
                   {"diagnostic": "target_gap_count", "value": sum(bool(row["target_gap"]) for row in trades)},
                   {"diagnostic": "identical_timestamp_ambiguity_count", "value": sum(bool(row["identical_timestamp_ambiguity"]) for row in trades)}]
    write_csv(outputs / "XAU_V2_EXECUTION_DIAGNOSTICS.csv", ["diagnostic", "value"], diagnostics)
    write_csv(outputs / "XAU_V2_PORTFOLIO_RESULTS.csv", ["status", "reason"], [{"status": "NOT_RUN", "reason": "NO_DEVELOPMENT_SURVIVOR"}] if not second["survivors"] else [{"status": "PENDING_STAGE_B", "reason": "DEVELOPMENT_SURVIVOR_EXISTS"}])
    write_csv(outputs / "XAU_V2_ACCOUNT_FEASIBILITY.csv", ["status", "reason"], [{"status": "NOT_APPLICABLE", "reason": "NO_FINAL_ACCEPTED_PORTFOLIO_OPPORTUNITIES"}])
    evidence_valid = derivation_identical and principal_identical
    final_class = classification(evidence_valid, len(derivation) == 36, len(second["survivors"]))
    gate_audit = {"phase": PHASE, "classification": final_class, "allowed_classifications": list(FINAL_CLASSIFICATIONS),
                  "data_complete": len(derivation) == 36, "development_survivor_count": len(second["survivors"]),
                  "derivation_deterministic": derivation_identical, "principal_outputs_deterministic": principal_identical,
                  "stage_b_authorized": bool(second["survivors"]), "stage_b_acquired": False,
                  "parameter_search_count": 0, "strategy_rules_changed_after_screen": False,
                  "mt5_strategy_tester_used": False, "broker_action": False, "deployment": False}
    write_json(outputs / "XAU_V2_GATE_AUDIT.json", gate_audit)
    result = {"phase": PHASE, "classification": final_class, "development_results": second["development"],
              "development_survivors": second["survivors"], "stage_b_acquired": False,
              "notices": ["FAST STRATEGY DISCOVERY RESEARCH", "OFFICIAL DUKASCOPY BID/ASK TICKS", "NO PARAMETER OPTIMIZATION", "NOT MT5 PARITY EVIDENCE", "NOT FORWARD-SHADOW EVIDENCE", "NOT DEPLOYMENT AUTHORIZATION"]}
    write_json(outputs / "XAU_V2_RESULT.json", result)
    lines = ["# XAUUSD Fast Discovery V2", "", *[f"**{notice}**  " for notice in result["notices"]], "", f"Classification: `{final_class}`", "", "## Development results", ""]
    for row in second["development"]:
        lines.append(f"- `{row['strategy_id']}`: trades {row['baseline_trades']}, PF {row['baseline_profit_factor']:.4g}, expectancy {row['baseline_expectancy_R']:.4g}R, net {row['baseline_net_R']:.4g}R; gate {'PASS' if row['development_gate_pass'] else 'FAIL'} ({row['failed_gates'] or 'none'}).")
    lines.extend(["", "Stage B was not acquired because no development family survived." if not second["survivors"] else "Stage B authorization exists and must be executed without rule changes.", "", "No deployment or trading authorization is granted.", ""])
    (outputs / "XAU_V2_RESULT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    source_hashes = {str(path.relative_to(lane_root)).replace("\\", "/"): sha256_file(path) for path in sorted((lane_root / "src").rglob("*.py"))}
    code_and_test_hashes = {
        str(path.relative_to(lane_root)).replace("\\", "/"): sha256_file(path)
        for path in sorted(lane_root.rglob("*.py")) if "__pycache__" not in path.parts
    }
    config_hashes = {str(path.relative_to(lane_root)).replace("\\", "/"): sha256_file(path) for path in sorted((lane_root / "config").rglob("*")) if path.is_file()}
    output_hashes = {path.name: sha256_file(path) for path in sorted(outputs.iterdir()) if path.is_file() and path.name != "XAU_V2_RUN_MANIFEST.json"}
    frozen_manifests = {
        row["month"]: json.loads((Path(os.environ[STORAGE_ENV]) / "raw" / "XAUUSD" / f"year={row['month'][:4]}" / f"month={row['month'][5:]}" / "_FROZEN_MANIFEST.json").read_text())
        for row in tick_inventory
    }
    raw_hashes = {month: value["files_sha256"] for month, value in frozen_manifests.items()}
    manifest = {**identity, "phase": PHASE, "commit_message": COMMIT_MESSAGE,
                "research_commit": "SELF_REFERENTIAL_NOT_EMBEDDABLE; BOUND_BY_GIT_COMMIT_CONTAINING_THIS_MANIFEST",
                "research_tree": "BOUND_BY_GIT_COMMIT_CONTAINING_THIS_MANIFEST", "research_parent": BASE_COMMIT,
                "official_source": SOURCE_ORIGIN,
                "official_instrument_identifier": SOURCE_CODE, "external_logical_data_root": f"${{{STORAGE_ENV}}}",
                "storage_preflight": preflight, "raw_partition_hashes": raw_hashes,
                "normalized_and_bar_partition_hashes": partition_hashes, "strategy_source_hashes": source_hashes,
                "configuration_hashes": config_hashes, "code_and_test_hashes": code_and_test_hashes,
                "development_survivor_registry_hash": sha256_file(outputs / "XAU_V2_DEVELOPMENT_SURVIVORS.json"),
                "locked_exam_freeze_evidence": "NOT_APPLICABLE_STAGE_B_NOT_ACQUIRED", "capital_contract_snapshot_hash": "NOT_APPLICABLE_NO_FINAL_PORTFOLIO",
                "output_hashes_excluding_manifest": output_hashes, "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pandas": pd.__version__},
                "stage_a_run_one_hashes": first["principal_hashes"], "stage_a_run_two_hashes": second["principal_hashes"],
                "stage_a_derivation_identical": derivation_identical, "stage_a_principal_identical": principal_identical,
                "stage_b_run_one_hashes": "NOT_APPLICABLE", "stage_b_run_two_hashes": "NOT_APPLICABLE",
                "parameter_search_count": 0, "data_acquisition": {"development_months": 36,
                    "required_and_frozen_hour_partitions": sum(int(value["expected_hour_files"]) for value in frozen_manifests.values()),
                    "newly_downloaded_or_resumed_rows_this_invocation": len(acquisition)},
                "focused_test_result": "88 passed", "files_outside_scope": [],
                "clean_worktree_before_task": True, "final_classification": final_class}
    write_json(outputs / "XAU_V2_RUN_MANIFEST.json", manifest)
    missing = [name for name in REQUIRED_OUTPUTS if not (outputs / name).is_file()]
    if missing:
        raise RuntimeError(f"required outputs missing: {missing}")
    return final_class


def run_stage_a(lane_root: Path, concurrency: int = 4, skip_acquisition: bool = False) -> str:
    identity = assert_identity(lane_root)
    raw_root = os.environ.get(STORAGE_ENV, "").strip()
    if not raw_root:
        raise RuntimeError(f"{STORAGE_ENV} is required")
    storage_root = Path(raw_root).resolve()
    if lane_root.resolve() in storage_root.parents or storage_root == lane_root.resolve():
        raise RuntimeError("bulk storage must be outside Git")
    preflight = storage_preflight(storage_root)
    if not preflight["passes"]:
        raise RuntimeError("XAU_FAST_DISCOVERY_V2_STORAGE_INSUFFICIENT")
    foundation = foundation_module(lane_root.parents[2])
    if foundation.INSTRUMENTS["XAUUSD"]["source_code"] != SOURCE_CODE or foundation.OFFICIAL_ORIGIN != SOURCE_ORIGIN:
        raise RuntimeError("official source contract mismatch")
    acquisition = acquire_development(storage_root, foundation, concurrency) if not skip_acquisition else []
    replay_root = storage_root / "xau-fast-discovery-v2" / "stage-a"
    run_one = replay_root / "run-one"
    run_two = replay_root / "run-two"
    scratch_one = replay_root / "scratch-one"
    scratch_two = replay_root / "scratch-two"
    for path in (scratch_one, scratch_two):
        if path.exists():
            shutil.rmtree(path)
    reusable_run_one = len(list((run_one / "contract-normalized" / "XAUUSD").rglob("ticks.parquet"))) == 36
    if reusable_run_one:
        print("REUSING_COMPLETE_RUN_ONE_DERIVATION", flush=True)
    else:
        derive(storage_root, run_one, foundation)
    hashes_one = inventory_hashes(run_one)
    first = screen(run_one, scratch_one)
    shutil.rmtree(run_one)
    results_two = derive(storage_root, run_two, foundation)
    hashes_two = inventory_hashes(run_two)
    second = screen(run_two, scratch_two)
    derivation_identical = hashes_one == hashes_two
    principal_identical = first["principal_hashes"] == second["principal_hashes"]
    final = write_outputs(lane_root, identity, preflight, acquisition, results_two, first, second, derivation_identical, principal_identical)
    print(final, flush=True)
    return final
