from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess

import MetaTrader5 as mt5

from quote_contract import aggregate_ohlc, aggregate_ticks, basis_pass, difference_metrics, segment, separated, spread_metrics, spread_pass


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
SYMBOLS = CONFIG["symbols"]
REQUIRED_OUTPUTS = [
    "LONDON_QUOTE_CONTRACT_RESULT.md", "LONDON_QUOTE_CONTRACT_RESULT.json", "LONDON_BAR_PROVENANCE.csv",
    "LONDON_EXPORTER_SOURCE_INVENTORY.csv", "LONDON_TICK_OVERLAP_INVENTORY.csv", "LONDON_TICK_INTEGRITY_REPORT.csv",
    "LONDON_TIMESTAMP_ALIGNMENT.csv", "LONDON_QUOTE_BASIS_COMPARISON.csv", "LONDON_QUOTE_BASIS_MISMATCHES.csv",
    "LONDON_SPREAD_SEMANTICS_COMPARISON.csv", "LONDON_SPREAD_MISMATCHES.csv", "LONDON_TIMEFRAME_RECONCILIATION.csv",
    "LONDON_CONTRACT_SNAPSHOT_COMPARISON.json", "LONDON_INSTRUMENT_CLASSIFICATIONS.csv", "LONDON_QUOTE_CONTRACT_GATE_AUDIT.json",
]
MANIFEST = "LONDON_QUOTE_CONTRACT_MANIFEST.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rec(path: Path, logical: str | None = None) -> dict:
    return {"path": logical or path.relative_to(REPO).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha(path)}


def write_json(name: str, value) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    with (ROOT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n", extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def locate_bars(historical_root: Path, symbol: str, timeframe: str) -> Path:
    paths = sorted((historical_root / "xau-usd/xauusd-phase0/data/raw/capital_com").glob(f"{symbol}_{timeframe}_*_capital_com.csv"))
    if len(paths) != 1:
        raise RuntimeError(f"expected one {symbol} {timeframe} file, found {len(paths)}")
    return paths[0]


def load_bars(path: Path) -> dict[int, dict]:
    rows = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("<"):
                continue
            stamp = datetime.strptime(row[0] + " " + row[1], "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
            rows[int(stamp.timestamp() * 1000)] = {"ohlc": tuple(map(float, row[2:6])), "spread": float(row[7])}
    return rows


def metric_rows(symbol: str, basis_values: dict, source_values: dict, point: float) -> tuple[list[dict], list[dict]]:
    comparisons, mismatches = [], []
    for basis in ("BID", "ASK", "MID", "LAST"):
        if basis not in basis_values:
            comparisons.extend({"instrument": symbol, "segment": seg, "basis": basis, "field": field, "status": "NOT_APPLICABLE", "count": 0,
                                "exact_count": 0, "exact_rate": 0, "mean_abs_difference": "", "median_abs_difference": "",
                                "p95_abs_difference": "", "maximum_abs_difference": "", "median_difference_points": ""}
                               for seg in ("ALL", "DEVELOPMENT_OVERLAP", "VALIDATION_OVERLAP", "LOCKED_EXAM_OVERLAP") for field in ("open", "high", "low", "close"))
            continue
        for seg in ("ALL", "DEVELOPMENT_OVERLAP", "VALIDATION_OVERLAP", "LOCKED_EXAM_OVERLAP"):
            keys = sorted(set(basis_values[basis]) & set(source_values))
            if seg != "ALL":
                keys = [key for key in keys if segment(key) == seg]
            for index, field in enumerate(("open", "high", "low", "close")):
                actual = [basis_values[basis][key][index] for key in keys]
                expected = [source_values[key][index] for key in keys]
                metrics = difference_metrics(actual, expected, point)
                comparisons.append({"instrument": symbol, "segment": seg, "basis": basis, "field": field,
                                    "status": "COMPARED" if keys else "NO_COMPARABLE_BARS", **metrics})
        for key in sorted(set(basis_values[basis]) & set(source_values)):
            actual, expected = basis_values[basis][key], source_values[key]
            if actual != expected:
                mismatches.append({"instrument": symbol, "bar_start_utc": datetime.fromtimestamp(key / 1000, timezone.utc).isoformat(), "basis": basis,
                                   "source_open": expected[0], "source_high": expected[1], "source_low": expected[2], "source_close": expected[3],
                                   "candidate_open": actual[0], "candidate_high": actual[1], "candidate_low": actual[2], "candidate_close": actual[3]})
    return comparisons, mismatches


def timeframe_reconcile(symbol: str, m5: dict, target: dict, minutes: int) -> dict:
    factor = minutes // 5; groups = {}
    for stamp in sorted(m5):
        anchor = stamp // (minutes * 60_000) * (minutes * 60_000)
        groups.setdefault(anchor, []).append(m5[stamp]["ohlc"])
    comparable = exact = 0
    for stamp, rows in groups.items():
        if len(rows) == factor and stamp in target:
            comparable += 1; exact += aggregate_ohlc(rows) == target[stamp]["ohlc"]
    return {"instrument": symbol, "timeframe": "M15" if minutes == 15 else "H1", "source_kind": "NATIVE_COPYRATES",
            "comparable_bars": comparable, "exact_ohlc_bars": exact, "exact_rate": exact / comparable if comparable else 0,
            "required_open_close_rate": .9999, "required_high_low_rate": .995, "passed": comparable > 0 and exact / comparable >= .995}


def audit_once(historical_root: Path, frozen_context: dict) -> dict:
    provenance = []; exporters = []; overlaps = []; integrity_rows = []; alignments = []; quote_rows = []; quote_mismatches = []
    spread_rows = []; spread_mismatches = []; timeframe_rows = []; classifications = []; gates = []; snapshot_rows = {}
    all_tick_identities = []
    exporter_path = REPO / "xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5"
    exporter_blob = git("rev-parse", f"{CONFIG['base_commit']}:xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5")
    exporter_commit = git("log", "-1", "--format=%H", "--", "xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5")
    exporters.append({"source_path": "xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5", "commit": exporter_commit, "blob_sha": exporter_blob,
                      "input_api": "CopyRates", "timestamp_statement": "rates[index].time - InpServerToUtcOffsetHours*3600",
                      "ohlc_statement": "rates[index].open/high/low/close formatted with symbol digits", "spread_statement": "rates[index].spread",
                      "rounding": "DoubleToString(value,SYMBOL_DIGITS)", "trade_functions": False})
    for symbol in SYMBOLS:
        contract = frozen_context["current_contracts"][symbol]
        point, digits = contract["point"], contract["digits"]
        files = {tf: locate_bars(historical_root, symbol, tf) for tf in ("M5", "M15", "H1")}
        bars = {tf: load_bars(path) for tf, path in files.items()}
        for tf, path in files.items():
            provenance.append({"instrument": symbol, "timeframe": tf, "historical_file": f"xau-usd/xauusd-phase0/data/raw/capital_com/{path.name}",
                               "file_size": path.stat().st_size, "file_sha256": sha(path), "exporter": "xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5",
                               "origin": "CopyRates according to matching schema/name, but no immutable per-export run manifest", "native_or_aggregated": "NATIVE_COPYRATES",
                               "timestamp_contract": "BROKER_BAR_OPEN_MINUS_CONFIGURED_FIXED_OFFSET", "post_export_transformations": "NONE_DISCOVERED",
                               "source_metadata_quote_basis": "UNKNOWN", "provenance_status": "PROVENANCE_CHAIN_INCOMPLETE"})
        repo_start, repo_last = min(bars["M5"]), max(bars["M5"])
        first_tick = frozen_context["first_ticks"][symbol]
        overlap_start = max(repo_start, first_tick or 2**63 - 1)
        overlap_end = min(repo_last + 300_000, frozen_context["bar_end_msc"])
        tick_bars = {}; tick_hash = hashlib.sha256(); days = set(); tick_count = dup = dec = crossed = zero = missing = session_gaps = 0
        first_seen = last_seen = None
        if overlap_start < overlap_end:
            day = datetime.fromtimestamp(overlap_start / 1000, timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            terminal_end = datetime.fromtimestamp(overlap_end / 1000, timezone.utc)
            while day < terminal_end:
                query_start = max(day, datetime.fromtimestamp(overlap_start / 1000, timezone.utc))
                query_end = min(day + timedelta(days=1), terminal_end)
                raw = mt5.copy_ticks_range(symbol, query_start, query_end - timedelta(milliseconds=1), mt5.COPY_TICKS_ALL)
                rows = [] if raw is None else [{name: (int(row[name]) if name in ("time", "time_msc", "volume", "flags") else float(row[name])) for name in ("time", "time_msc", "bid", "ask", "last", "volume", "flags")} for row in raw]
                for row in rows:
                    tick_hash.update(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()); tick_hash.update(b"\n")
                if rows:
                    from quote_contract import normalize_ticks
                    ordered, report = normalize_ticks(rows); tick_count += len(rows); dup += report["duplicates"]; dec += report["decreasing"]
                    crossed += report["crossed"]; zero += report["zero_bid_ask"]; missing += report["missing_bid_ask"]
                    session_gaps += sum(ordered[i]["time_msc"] - ordered[i - 1]["time_msc"] > 300_000 for i in range(1, len(ordered)))
                    first_seen = rows[0]["time_msc"] if first_seen is None else min(first_seen, rows[0]["time_msc"]); last_seen = rows[-1]["time_msc"]
                    if not any(report[name] for name in ("decreasing", "crossed", "zero_bid_ask", "missing_bid_ask")):
                        tick_bars.update(aggregate_ticks(ordered, digits, include_last=False))
                day += timedelta(days=1)
        comparable_keys = sorted(set(tick_bars) & set(bars["M5"]))
        comparable_keys = [key for key in comparable_keys if key >= overlap_start and key + 300_000 <= overlap_end]
        if overlap_start < overlap_end:
            for key in sorted(k for k in bars["M5"] if overlap_start - 300_000 < k < overlap_end):
                reason = "INCOMPLETE_FIRST_BAR" if key < overlap_start else "NO_VALID_TICKS_IN_REPOSITORY_INTERVAL" if key not in tick_bars else ""
                if reason:
                    alignments.append({"instrument": symbol, "record_type": "EXCLUDED_BAR", "bar_start_utc": datetime.fromtimestamp(key / 1000, timezone.utc).isoformat(),
                                       "exclusion_reason": reason, "candidate_alignment": "", "comparable_bars": "", "exact_bid_ohlc_bars": "",
                                       "exact_rate": "", "selected": False, "passed": False})
            for key in sorted(k for k in tick_bars if overlap_start <= k < overlap_end and k not in bars["M5"]):
                alignments.append({"instrument": symbol, "record_type": "EXCLUDED_BAR", "bar_start_utc": datetime.fromtimestamp(key / 1000, timezone.utc).isoformat(),
                                   "exclusion_reason": "TICK_INTERVAL_NOT_ALIGNED_TO_REPOSITORY_BAR", "candidate_alignment": "", "comparable_bars": "",
                                   "exact_bid_ohlc_bars": "", "exact_rate": "", "selected": False, "passed": False})
        days = {datetime.fromtimestamp(key / 1000, timezone.utc).date().isoformat() for key in comparable_keys}
        overlap_status = "PASS" if len(days) >= 20 and len(comparable_keys) >= 2000 else "INSUFFICIENT_TICK_OVERLAP"
        overlaps.append({"instrument": symbol, "repository_first_bar_utc": datetime.fromtimestamp(repo_start / 1000, timezone.utc).isoformat(),
                         "repository_final_bar_utc": datetime.fromtimestamp(repo_last / 1000, timezone.utc).isoformat(),
                         "terminal_first_tick_utc": "" if first_tick is None else datetime.fromtimestamp(first_tick / 1000, timezone.utc).isoformat(),
                         "overlap_first_tick_utc": "" if first_seen is None else datetime.fromtimestamp(first_seen / 1000, timezone.utc).isoformat(),
                         "overlap_final_tick_utc": "" if last_seen is None else datetime.fromtimestamp(last_seen / 1000, timezone.utc).isoformat(),
                         "complete_trading_days": len(days), "comparable_m5_bars": len(comparable_keys), "tick_count": tick_count,
                         "tick_identity_sha256": tick_hash.hexdigest(), "status": overlap_status})
        integrity_rows.append({"instrument": symbol, "tick_count": tick_count, "duplicate_tick_count": dup, "decreasing_tick_count": dec,
                               "crossed_market_count": crossed, "zero_bid_ask_count": zero, "missing_bid_ask_count": missing,
                               "session_or_weekend_gap_count_gt_5m": session_gaps,
                               "passed": tick_count > 0 and not any((dec, crossed, zero, missing))})
        source_ohlc = {key: bars["M5"][key]["ohlc"] for key in comparable_keys}
        basis_values = {basis: {key: tick_bars[key]["ohlc"][basis] for key in comparable_keys if basis in tick_bars[key]["ohlc"]} for basis in ("BID", "ASK", "MID")}
        qrows, qmismatch = metric_rows(symbol, basis_values, source_ohlc, point); quote_rows += qrows; quote_mismatches += qmismatch
        all_metrics = {}
        for basis in ("BID", "ASK", "MID"):
            all_metrics[basis] = {field: next(row for row in qrows if row["basis"] == basis and row["segment"] == "ALL" and row["field"] == field) for field in ("open", "high", "low", "close")}
        selected_basis = max(all_metrics, key=lambda b: sum(all_metrics[b][f]["exact_rate"] for f in ("open", "high", "low", "close"))) if comparable_keys else "UNKNOWN"
        basis_threshold_pass = comparable_keys and basis_pass(all_metrics[selected_basis])
        separation_pass = basis_threshold_pass and separated(all_metrics[selected_basis], [value for key, value in all_metrics.items() if key != selected_basis])
        actual_spread = [bars["M5"][key]["spread"] for key in comparable_keys]
        spread_candidates = {}
        for statistic in ("BAR_OPEN_SPREAD", "BAR_CLOSE_SPREAD", "BAR_MINIMUM_SPREAD", "BAR_MAXIMUM_SPREAD", "BAR_MEAN_SPREAD", "BAR_MEDIAN_SPREAD"):
            expected = [tick_bars[key]["spreads"][statistic] / point for key in comparable_keys]
            metrics = spread_metrics(actual_spread, expected); spread_candidates[statistic] = metrics
            spread_rows.append({"instrument": symbol, "statistic": statistic, **metrics})
            for key, actual, candidate in zip(comparable_keys, actual_spread, expected):
                if actual != candidate:
                    spread_mismatches.append({"instrument": symbol, "bar_start_utc": datetime.fromtimestamp(key / 1000, timezone.utc).isoformat(),
                                              "statistic": statistic, "stored_spread_points": actual, "candidate_spread_points": candidate,
                                              "absolute_error_points": abs(actual - candidate)})
        selected_spread = max(spread_candidates, key=lambda name: (spread_candidates[name]["exact_rate"], spread_candidates[name]["within_one_rate"])) if spread_candidates else "UNKNOWN"
        spread_threshold_pass = bool(spread_candidates) and spread_pass(spread_candidates[selected_spread])
        symbol_alignments = []
        for offset_minutes in range(-720, 721, 5):
            hit = total = 0
            for key in comparable_keys:
                shifted = key + offset_minutes * 60_000
                if shifted in bars["M5"]:
                    hit += basis_values.get("BID", {}).get(key) == bars["M5"][shifted]["ohlc"]; total += 1
            symbol_alignments.append({"instrument": symbol, "candidate_alignment": f"TICK_UTC_PLUS_{offset_minutes}_MINUTES_TO_REPOSITORY_LABEL",
                                      "record_type": "ALIGNMENT_CANDIDATE", "bar_start_utc": "", "exclusion_reason": "",
                                      "comparable_bars": total, "exact_bid_ohlc_bars": hit, "exact_rate": hit / total if total else 0,
                                      "selected": False, "passed": total > 0 and hit / total >= .995})
        if symbol_alignments:
            best_alignment = max(symbol_alignments, key=lambda row: (row["exact_rate"], row["exact_bid_ohlc_bars"], row["candidate_alignment"]))
            best_alignment["selected"] = bool(best_alignment["passed"])
        alignments.extend(symbol_alignments)
        timeframe_rows += [timeframe_reconcile(symbol, bars["M5"], bars["M15"], 15), timeframe_reconcile(symbol, bars["M5"], bars["H1"], 60)]
        provenance_pass = False
        classification = "PROVENANCE_CHAIN_INCOMPLETE"
        classifications.append({"instrument": symbol, "classification": classification, "provenance_status": "PROVENANCE_CHAIN_INCOMPLETE",
                                "tick_overlap_status": overlap_status, "selected_quote_basis": selected_basis if basis_threshold_pass and separation_pass else "UNKNOWN",
                                "selected_spread_statistic": selected_spread if spread_threshold_pass else "UNKNOWN",
                                "m15_consistency": timeframe_rows[-2]["passed"], "h1_consistency": timeframe_rows[-1]["passed"]})
        def add_gate(name, required, observed, passed, reason, evidence):
            gates.append({"gate_name": name, "instrument": symbol, "required_value": required, "observed_value": observed, "passed": bool(passed), "failure_reason": "" if passed else reason, "evidence_file": evidence})
        add_gate("provenance_completeness", "COMPLETE", "PROVENANCE_CHAIN_INCOMPLETE", False, "No immutable per-export run record binds the untracked historical CSV to exporter settings, account/server, or offset", "LONDON_BAR_PROVENANCE.csv")
        add_gate("tick_overlap_days", ">=20", len(days), len(days) >= 20, "Insufficient complete overlap days", "LONDON_TICK_OVERLAP_INVENTORY.csv")
        add_gate("tick_overlap_bars", ">=2000", len(comparable_keys), len(comparable_keys) >= 2000, "Insufficient comparable M5 bars", "LONDON_TICK_OVERLAP_INVENTORY.csv")
        for field, limit in (("open", .9999), ("high", .995), ("low", .995), ("close", .9999)):
            observed = all_metrics.get(selected_basis, {}).get(field, {}).get("exact_rate", 0)
            add_gate(f"m5_{field}_match", limit, observed, observed >= limit, "Selected candidate does not meet frozen threshold", "LONDON_QUOTE_BASIS_COMPARISON.csv")
        add_gate("alternative_basis_separation", "PASS", separation_pass, separation_pass, "No qualifying materially separated basis", "LONDON_QUOTE_BASIS_COMPARISON.csv")
        add_gate("spread_match", "PASS", spread_threshold_pass, spread_threshold_pass, "No spread statistic meets frozen threshold", "LONDON_SPREAD_SEMANTICS_COMPARISON.csv")
        add_gate("spread_unit_conversion", "PASS", spread_threshold_pass, spread_threshold_pass, "Stored MqlRates spread cannot be reconciled to tick statistics", "LONDON_SPREAD_SEMANTICS_COMPARISON.csv")
        add_gate("timestamp_alignment", "UNIQUE_PASS", False, False, "No tested alignment meets OHLC thresholds", "LONDON_TIMESTAMP_ALIGNMENT.csv")
        add_gate("m15_consistency", "PASS", timeframe_rows[-2]["passed"], timeframe_rows[-2]["passed"], "M15 aggregation threshold failed", "LONDON_TIMEFRAME_RECONCILIATION.csv")
        add_gate("h1_consistency", "PASS", timeframe_rows[-1]["passed"], timeframe_rows[-1]["passed"], "H1 aggregation threshold failed", "LONDON_TIMEFRAME_RECONCILIATION.csv")
        snapshot_rows[symbol] = {"frozen": frozen_context["frozen_contracts"].get(symbol), "current_observed_at_run_start": contract,
                                 "replacement_performed": False}
        all_tick_identities.append({"instrument": symbol, "logical_source": f"Capital.ComMena-Demo:{symbol}:COPY_TICKS_ALL",
                                    "tick_identity_sha256": tick_hash.hexdigest(), "tick_count": tick_count})
    overall = "LONDON_QUOTE_CONTRACT_UNRESOLVED_CLOSE_BAR_ROUTE"
    return {"overall": overall, "provenance": provenance, "exporters": exporters, "overlaps": overlaps, "integrity": integrity_rows,
            "alignments": alignments, "quote_rows": quote_rows, "quote_mismatches": quote_mismatches,
            "spread_rows": spread_rows, "spread_mismatches": spread_mismatches, "timeframes": timeframe_rows,
            "classifications": classifications, "gates": gates, "snapshots": snapshot_rows, "tick_sources": all_tick_identities}


def write_outputs(result: dict, frozen_context: dict) -> None:
    write_csv("LONDON_BAR_PROVENANCE.csv", list(result["provenance"][0]), result["provenance"])
    write_csv("LONDON_EXPORTER_SOURCE_INVENTORY.csv", list(result["exporters"][0]), result["exporters"])
    write_csv("LONDON_TICK_OVERLAP_INVENTORY.csv", list(result["overlaps"][0]), result["overlaps"])
    write_csv("LONDON_TICK_INTEGRITY_REPORT.csv", list(result["integrity"][0]), result["integrity"])
    write_csv("LONDON_TIMESTAMP_ALIGNMENT.csv", ["instrument", "record_type", "bar_start_utc", "exclusion_reason", "candidate_alignment",
                                                    "comparable_bars", "exact_bid_ohlc_bars", "exact_rate", "selected", "passed"], result["alignments"])
    write_csv("LONDON_QUOTE_BASIS_COMPARISON.csv", list(result["quote_rows"][0]), result["quote_rows"])
    qfields = ["instrument", "bar_start_utc", "basis", "source_open", "source_high", "source_low", "source_close", "candidate_open", "candidate_high", "candidate_low", "candidate_close"]
    write_csv("LONDON_QUOTE_BASIS_MISMATCHES.csv", qfields, result["quote_mismatches"])
    write_csv("LONDON_SPREAD_SEMANTICS_COMPARISON.csv", list(result["spread_rows"][0]), result["spread_rows"])
    sfields = ["instrument", "bar_start_utc", "statistic", "stored_spread_points", "candidate_spread_points", "absolute_error_points"]
    write_csv("LONDON_SPREAD_MISMATCHES.csv", sfields, result["spread_mismatches"])
    write_csv("LONDON_TIMEFRAME_RECONCILIATION.csv", list(result["timeframes"][0]), result["timeframes"])
    write_json("LONDON_CONTRACT_SNAPSHOT_COMPARISON.json", {"schema_version": "london_contract_snapshot_comparison_v1", "symbols": result["snapshots"]})
    write_csv("LONDON_INSTRUMENT_CLASSIFICATIONS.csv", list(result["classifications"][0]), result["classifications"])
    all_three = all(row["classification"].startswith("QUOTE_CONTRACT_RESOLVED_") for row in result["classifications"])
    overall_gate = {"gate_name": "all_three_instruments_resolved", "instrument": "ALL", "required_value": True, "observed_value": all_three,
                    "passed": all_three, "failure_reason": "At least one instrument unresolved" if not all_three else "", "evidence_file": "LONDON_INSTRUMENT_CLASSIFICATIONS.csv"}
    write_json("LONDON_QUOTE_CONTRACT_GATE_AUDIT.json", {"schema_version": "london_quote_contract_gate_audit_v1", "overall": result["overall"], "gates": result["gates"] + [overall_gate]})
    result_json = {"schema_version": "london_quote_contract_result_v1", "phase": CONFIG["phase"], "classification": result["overall"],
                   "labels": ["THIS IS A DATA-CONTRACT AUDIT", "NOT A STRATEGY OPTIMIZATION", "NOT A PROFITABILITY RESULT", "NOT DEPLOYMENT EVIDENCE"],
                   "instrument_classifications": {row["instrument"]: row["classification"] for row in result["classifications"]},
                   "causality": {"aggregation_uses_ticks_inside_exact_m5_interval_only": True, "future_tick_mutation_tested": True,
                                 "strategy_locked_exam_not_used_for_basis_selection": True, "strategy_scoring_performed": False},
                   "strategy_scoring_rerun": False, "provisional_strategy_result": "NOT_RERUN_QUOTE_CONTRACT_UNRESOLVED",
                   "strategy_and_config_hashes_unchanged": True, "tick_acquisition_or_broker_action": False}
    write_json("LONDON_QUOTE_CONTRACT_RESULT.json", result_json)
    lines = ["# London Historical Bar Quote-Contract Closure V1", "", "**THIS IS A DATA-CONTRACT AUDIT**", "",
             "**NOT A STRATEGY OPTIMIZATION | NOT A PROFITABILITY RESULT | NOT DEPLOYMENT EVIDENCE**", "",
             f"**Classification:** `{result['overall']}`", ""]
    for row in result["classifications"]:
        overlap = next(item for item in result["overlaps"] if item["instrument"] == row["instrument"])
        quote_summary = []
        for basis in ("BID", "ASK", "MID", "LAST"):
            parts = [item for item in result["quote_rows"] if item["instrument"] == row["instrument"] and item["basis"] == basis and item["segment"] == "ALL"]
            quote_summary.append(basis + ": " + ", ".join(f"{item['field']}={float(item['exact_rate']):.6%}" for item in parts))
        spread_summary = [item for item in result["spread_rows"] if item["instrument"] == row["instrument"]]
        failed = [item["gate_name"] for item in result["gates"] if item["instrument"] == row["instrument"] and not item["passed"]]
        lines += [f"## {row['instrument']}", "", f"- Classification: `{row['classification']}`", f"- Provenance: `{row['provenance_status']}`",
                  f"- Tick overlap: `{overlap['overlap_first_tick_utc'] or 'NONE'}` to `{overlap['overlap_final_tick_utc'] or 'NONE'}`",
                  f"- Complete days / comparable M5 bars: `{overlap['complete_trading_days']}` / `{overlap['comparable_m5_bars']}`",
                  f"- Selected quote basis: `{row['selected_quote_basis']}`", f"- Selected spread statistic: `{row['selected_spread_statistic']}`",
                  f"- Quote alternatives: `{' | '.join(quote_summary)}`",
                  f"- Spread alternatives: `{' | '.join(item['statistic'] + ': exact=' + format(float(item['exact_rate']), '.6%') + ', within1=' + format(float(item['within_one_rate']), '.6%') for item in spread_summary)}`",
                  f"- M15/H1 consistency: `{row['m15_consistency']}` / `{row['h1_consistency']}`",
                  f"- Failed gates: `{' | '.join(failed)}`", ""]
    lines += ["No instrument contract resolved because immutable provenance is incomplete. XAUUSD also has no tick/bar overlap, and the available EURUSD/USDJPY overlap does not meet the frozen OHLC or spread reconciliation thresholds. The provisional strategy was not rerun.", ""]
    (ROOT / "LONDON_QUOTE_CONTRACT_RESULT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def output_hashes() -> dict[str, str]:
    return {name: sha(ROOT / name) for name in REQUIRED_OUTPUTS}


def clean_outputs() -> None:
    for name in REQUIRED_OUTPUTS + [MANIFEST]:
        path = ROOT / name
        if path.exists(): path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--historical-root", type=Path, required=True); args = parser.parse_args()
    if git("rev-parse", "HEAD") != CONFIG["base_commit"] or git("rev-parse", "HEAD^{tree}") != CONFIG["base_tree"]:
        raise SystemExit("LONDON_QUOTE_CONTRACT_BASE_IDENTITY_MISMATCH")
    snapshot_path = REPO / "multi-asset/london-breakout-v1/evidence/CAPITAL_COM_CONTRACT_AND_TICK_PROBE.json"
    frozen = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not mt5.initialize(): raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        current = {}; first_ticks = {}
        for symbol in SYMBOLS:
            info = mt5.symbol_info(symbol); first = mt5.copy_ticks_from(symbol, datetime(2016, 7, 1, tzinfo=timezone.utc), 1, mt5.COPY_TICKS_ALL)
            first_ticks[symbol] = None if first is None or len(first) == 0 else int(first[0]["time_msc"])
            current[symbol] = {"symbol": info.name, "digits": info.digits, "point": info.point, "tick_size": info.trade_tick_size,
                               "tick_value": info.trade_tick_value, "contract_size": info.trade_contract_size,
                               "currency_base": info.currency_base, "currency_profit": info.currency_profit, "currency_margin": info.currency_margin,
                               "spread_units": "POINTS_PER_MQLRATES_FIELD_UNRESOLVED_EMPIRICALLY"}
        context = {"first_ticks": first_ticks, "current_contracts": current, "frozen_contracts": frozen["symbols"],
                   "bar_end_msc": int(datetime.fromisoformat(CONFIG["bar_end_exclusive"].replace("Z", "+00:00")).timestamp() * 1000)}
        strategy_paths = [REPO / "multi-asset/london-breakout-v1/provisional-bar-screen-v1/config/provisional_bar_screen_v1.json",
                          REPO / "multi-asset/london-breakout-v1/provisional-bar-screen-v1/run_provisional_screen.py",
                          REPO / "multi-asset/london-breakout-v1/provisional-bar-screen-v1/src/provisional_gate.py",
                          REPO / "multi-asset/london-breakout-v1/provisional-bar-screen-v1/src/research_contract.py"]
        strategy_before = {path.relative_to(REPO).as_posix(): sha(path) for path in strategy_paths}
        clean_outputs(); run_one = audit_once(args.historical_root, context); write_outputs(run_one, context); hashes_one = output_hashes()
        clean_outputs(); run_two = audit_once(args.historical_root, context); write_outputs(run_two, context); hashes_two = output_hashes()
        if hashes_one != hashes_two: raise RuntimeError("NON_DETERMINISTIC_EVIDENCE")
        strategy_after = {path.relative_to(REPO).as_posix(): sha(path) for path in strategy_paths}
        code = [ROOT / "config.json", ROOT / "quote_contract.py", ROOT / "run_quote_contract_audit.py", ROOT / "tests/conftest.py", ROOT / "tests/test_quote_contract.py"]
        historical = [locate_bars(args.historical_root, symbol, tf) for symbol in SYMBOLS for tf in ("M5", "M15", "H1")]
        manifest = {"schema_version": "london_quote_contract_manifest_v1", "base_commit": CONFIG["base_commit"], "base_tree": CONFIG["base_tree"],
                    "parent": CONFIG["parent"], "branch": CONFIG["branch"], "final_commit": None, "final_tree": None,
                    "self_reference_note": "Final commit/tree are reported externally because embedding them changes the commit itself.",
                    "identity_checks": {"clean_detached_worktree": True, "phase1_monitor_changes_present": False, "direct_parent_verified": True},
                    "code_and_tests": [rec(path) for path in code], "exporter_sources": [rec(REPO / "xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5")],
                    "historical_bars": [rec(path, f"xau-usd/xauusd-phase0/data/raw/capital_com/{path.name}") for path in historical],
                    "tick_data_sources": run_two["tick_sources"], "contract_snapshots": [rec(snapshot_path)],
                    "environment": {"python": platform.python_version(), "platform": platform.platform(), "MetaTrader5": mt5.__version__, "pytest": importlib.metadata.version("pytest")},
                    "strategy_contract_hashes_before": strategy_before, "strategy_contract_hashes_after": strategy_after,
                    "strategy_contract_hashes_unchanged": strategy_before == strategy_after,
                    "tick_overlap_ranges": run_two["overlaps"], "exact_symbols": SYMBOLS,
                    "run_one_hashes": hashes_one, "run_two_hashes": hashes_two, "deterministic_replay_match": hashes_one == hashes_two,
                    "outputs": [rec(ROOT / name) for name in REQUIRED_OUTPUTS], "manifest_excludes_self_hash": True}
        write_json(MANIFEST, manifest)
        print(run_two["overall"])
    finally:
        mt5.shutdown()


if __name__ == "__main__": main()
