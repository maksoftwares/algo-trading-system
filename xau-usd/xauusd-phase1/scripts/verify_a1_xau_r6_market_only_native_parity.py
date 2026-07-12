"""Deterministic verifier/finalizer for the locked NP1 native evidence packet."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

import build_a1_xau_r6_market_only_native_parity_oracle as B


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = ROOT / "docs" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_SOURCE_CONTRACT_V1.json"
OUTPUT_SCHEMA = ROOT / "docs" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_OUTPUT_SCHEMA_V1.json"
LOCK_MANIFEST = ROOT / "outputs" / "manifests" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_LOCK_MANIFEST_V1.json"
STATE_CODES = {"UNKNOWN": 0, "SHOCK": 1, "UPTREND": 2, "DOWNTREND": 3, "COMPRESSION": 4, "CHOP": 5}
NATIVE_TO_CANONICAL = {name.lower(): name for name in STATE_CODES}


@dataclass
class Buckets:
    invalid: list[str] = field(default_factory=list)
    source: list[str] = field(default_factory=list)
    zero_action: list[str] = field(default_factory=list)
    parity: list[str] = field(default_factory=list)

    def all(self) -> list[str]:
        return [*self.invalid, *self.source, *self.zero_action, *self.parity]


@dataclass(frozen=True)
class VerificationResult:
    status: str
    errors: tuple[str, ...]
    metrics: dict[str, Any]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source, schema, manifest = read_json(SOURCE_CONTRACT), read_json(OUTPUT_SCHEMA), read_json(LOCK_MANIFEST)
    for relative, item in manifest["artifacts"].items():
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size != item["size_bytes"] or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"NP1 lock manifest mismatch: {relative}")
    authority = source["python_router_authority"]
    path = ROOT / authority["path"].removeprefix("xau-usd/xauusd-phase1/")
    if not path.is_file() or sha256_file(path) != authority["sha256"]:
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    return source, schema, manifest


def load_python_router(source_contract: dict[str, Any]) -> Any:
    authority = source_contract["python_router_authority"]
    path = ROOT / authority["path"].removeprefix("xau-usd/xauusd-phase1/")
    if sha256_file(path) != authority["sha256"]:
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    name = "a1_xau_r6_pinned_python_router"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    required = [authority["function"], *authority["numerical_and_data_dependencies"]]
    if any(not hasattr(module, item) for item in required):
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    return module


def read_tsv(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if list(reader.fieldnames or ()) != list(expected_columns):
            raise ValueError(f"TSV header mismatch: {path}")
        return list(reader)


def write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def verify_source_equivalence(path: Path, generated_source: Path) -> list[str]:
    errors: list[str] = []
    payload = read_json(path)
    source = B.assert_pinned_source().decode("utf-8")
    generated = generated_source.read_text(encoding="utf-8")
    rows = payload.get("blocks", [])
    if len(rows) != len(B.BLOCK_NAMES):
        errors.append("source-equivalence block count mismatch")
    for row in rows:
        source_raw = source.encode()[row["source_start_byte_offset"] : row["source_end_byte_offset"]]
        generated_raw = generated.encode()[row["generated_start_byte_offset"] : row["generated_end_byte_offset"]]
        if source_raw != generated_raw:
            errors.append(f"source block differs: {row.get('signature')}")
        if hashlib.sha256(source_raw).hexdigest() != row.get("source_raw_sha256"):
            errors.append(f"source block hash mismatch: {row.get('signature')}")
        if hashlib.sha256(generated_raw).hexdigest() != row.get("generated_raw_sha256"):
            errors.append(f"generated block hash mismatch: {row.get('signature')}")
        if row.get("exact_equal") is not True:
            errors.append(f"source-equivalence flag false: {row.get('signature')}")
    try:
        B.assert_source_safety(generated)
    except RuntimeError as exc:
        errors.append(str(exc))
    return errors


def verify_assertions(path: Path, schema: dict[str, Any], run_id: str) -> list[str]:
    contract = schema["native_assertions"]
    rows = read_tsv(path, contract["columns"])
    by_id: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_id.setdefault(row["assertion_id"], []).append(row)
    errors = [
        f"required assertion did not pass: {assertion_id}"
        for assertion_id in contract["required_assertion_ids"]
        if not by_id.get(assertion_id)
        or any(row["passed"].lower() != "true" for row in by_id[assertion_id])
    ]
    expected_inputs = {
        "InpRunId": run_id,
        "InpRouterRowsFileName": f"np1_{run_id}_native_router_rows.tsv",
        "InpH1BarsFileName": f"np1_{run_id}_native_h1_bars.tsv",
        "InpH4BarsFileName": f"np1_{run_id}_native_h4_bars.tsv",
        "InpD1BarsFileName": f"np1_{run_id}_native_d1_bars.tsv",
        "InpContractFileName": f"np1_{run_id}_native_contract.tsv",
        "InpOrderCalcProfitFileName": f"np1_{run_id}_native_ordercalcprofit.tsv",
        "InpAssertionsFileName": f"np1_{run_id}_native_assertions.tsv",
        "InpOrderZeroFileName": f"np1_{run_id}_order.zero",
        "InpDealZeroFileName": f"np1_{run_id}_deal.zero",
    }
    expected_environment = {
        "environment_mql_tester": "true", "environment_symbol": "XAUUSD",
        "environment_period": "PERIOD_M5", "environment_account_login": "1025742",
        "environment_server": "Capital.ComMena-Demo",
        "environment_company": "Capital Com Mena Securities Trading L.L.C",
        "environment_currency": "USD", "environment_leverage": "50",
        "environment_terminal_build": "5833",
    }
    expected_rows = {f"effective_input_{key}": value for key, value in expected_inputs.items()}
    fixed_constants = {
        "InpTargetSymbol": "XAUUSD", "InpAtrPeriod": "14", "InpRegimeFastEmaPeriod": "20",
        "InpRegimeSlowEmaPeriod": "50", "InpRegimeSlopeLagBars": "5",
        "InpRegimePersistenceD1Bars": "2", "InpRegimeRequireH4Confirm": "true",
        "InpRegimeShockH1RangeAtrMultiple": "3", "InpRegimeShockD1AtrLookback": "60",
        "InpRegimeShockD1AtrPercentileMin": "95", "InpRegimeCompressionBoxDays": "5",
        "InpRegimeCompressionD1AtrPercentileMax": "30", "InpRegimeCompressionRangeMedianMax": "1",
    }
    expected_rows.update({f"fixed_constant_{key}": value for key, value in fixed_constants.items()})
    expected_rows.update(expected_environment)
    for key, expected in expected_rows.items():
        matches = by_id.get(key, [])
        if len(matches) != 1 or matches[0]["passed"].lower() != "true" or matches[0]["observed"] != expected or matches[0]["expected"] != expected:
            errors.append(f"native effective input/environment assertion mismatch: {key}")
    return errors


def _decode_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def parse_native_report(path: Path) -> dict[str, Any]:
    text = _decode_text(path)
    plain = html.unescape(re.sub(r"<[^>]+>", "\n", text))

    def field(label: str) -> str:
        patterns = (
            rf"{re.escape(label)}\s*:?</td>\s*<td[^>]*>\s*([^<\r\n]+)",
            rf"(?:^|\n)\s*{re.escape(label)}\s*[:=]\s*([^\r\n]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return html.unescape(match.group(1)).strip()
        match = re.search(rf"(?:^|\n)\s*{re.escape(label)}\s*:?\s*\n+\s*([^\n]+)", plain, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        raise ValueError(f"native report missing {label}")

    def integer(label: str) -> int:
        match = re.search(r"[0-9][0-9,]*", field(label))
        if not match:
            raise ValueError(f"native report invalid {label}")
        return int(match.group(0).replace(",", ""))

    return {
        "expert": field("Expert"), "symbol": field("Symbol"), "period": field("Period"),
        "model": field("Model"), "initial_deposit": field("Initial Deposit"),
        "leverage": field("Leverage"), "bars": integer("Bars in test"),
        "ticks": integer("Ticks modelled"), "total_trades": integer("Total Trades"),
        "total_deals": integer("Total Deals"), "text": plain,
    }


def verify_native_report(path: Path, run_id: str, buckets: Buckets) -> dict[str, Any]:
    report = parse_native_report(path)
    exact = {
        "expert": "A1XauR6MarketOnlyNativeParityOracle", "symbol": "XAUUSD",
        "model": "Every tick based on real ticks", "leverage": "1:50",
    }
    for key, expected in exact.items():
        if report[key] != expected:
            buckets.invalid.append(f"{run_id}: native report {key} mismatch: {report[key]!r}")
    if re.fullmatch(r"M5\s+\(2015\.06\.01\s+-\s+2026\.06\.30\)", report["period"]) is None:
        buckets.invalid.append(f"{run_id}: native report period mismatch: {report['period']!r}")
    deposit_match = re.search(r"([0-9][0-9,.\s]*)\s*(USD)?", report["initial_deposit"], re.IGNORECASE)
    if not deposit_match or float(re.sub(r"[\s,]", "", deposit_match.group(1))) != 10000.0:
        buckets.invalid.append(f"{run_id}: native report initial deposit mismatch")
    if report["bars"] <= 0 or report["ticks"] <= 0:
        buckets.invalid.append(f"{run_id}: native report bar/tick counts must be positive")
    expected_inputs = {
        "InpRunId": run_id,
        "InpRouterRowsFileName": f"np1_{run_id}_native_router_rows.tsv",
        "InpH1BarsFileName": f"np1_{run_id}_native_h1_bars.tsv",
        "InpH4BarsFileName": f"np1_{run_id}_native_h4_bars.tsv",
        "InpD1BarsFileName": f"np1_{run_id}_native_d1_bars.tsv",
        "InpContractFileName": f"np1_{run_id}_native_contract.tsv",
        "InpOrderCalcProfitFileName": f"np1_{run_id}_native_ordercalcprofit.tsv",
        "InpAssertionsFileName": f"np1_{run_id}_native_assertions.tsv",
        "InpOrderZeroFileName": f"np1_{run_id}_order.zero",
        "InpDealZeroFileName": f"np1_{run_id}_deal.zero",
    }
    compact = re.sub(r"\s+", "", report["text"])
    for key, value in expected_inputs.items():
        if f"{key}={value}" not in compact:
            buckets.invalid.append(f"{run_id}: native report effective input missing/mismatch: {key}")
    if report["total_trades"] != 0 or report["total_deals"] != 0:
        buckets.zero_action.append(
            f"{run_id}: native report trades={report['total_trades']} deals={report['total_deals']}"
        )
    return report


def verify_compile_packet(compiled: Path, buckets: Buckets) -> None:
    source = compiled / B.ORACLE_NAME
    ex5 = compiled / Path(B.ORACLE_NAME).with_suffix(".ex5").name
    log = compiled / "compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log"
    equivalence = compiled / "source_equivalence.json"
    for path in (source, ex5, log, equivalence):
        if not path.is_file() or path.stat().st_size == 0:
            buckets.invalid.append(f"compiled artifact missing or empty: {path.name}")
    if buckets.invalid:
        return
    try:
        B.verify_generated_source(source)
        buckets.source.extend(verify_source_equivalence(equivalence, source))
    except (RuntimeError, ValueError, KeyError) as exc:
        buckets.source.append(str(exc))
    text = log.read_text(encoding="utf-8-sig", errors="replace")
    for required in ("MetaEditor executable version: 5.0.0.5833", "0 errors", "0 warnings"):
        if required not in text:
            buckets.invalid.append(f"compile log missing proof: {required}")


def _dt(value: str) -> datetime:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", value) is None:
        raise ValueError(f"timestamp is not locked ISO broker format: {value!r}")
    return datetime.fromisoformat(value)


def expected_weekend_gap(timeframe: str, first: datetime, second: datetime) -> bool:
    if first.weekday() != 4 or second.weekday() != 0:
        return False
    delta = int((second - first).total_seconds())
    if timeframe == "H1":
        return first.hour in {19, 20} and second.hour in {0, 1} and delta <= 54 * 3600
    if timeframe == "H4":
        return first.hour in {16, 20} and second.hour == 0 and delta <= 56 * 3600
    if timeframe == "D1":
        return first.hour == second.hour == 0 and delta == 3 * 86400
    return False


def load_bar_rows(
    path: Path, schema: dict[str, Any], router: Any, *, timeframe: str,
    test_start: datetime, test_end: datetime,
) -> tuple[list[dict[str, str]], list[Any]]:
    rows = read_tsv(path, schema["bar_exports"]["columns"])
    if not rows:
        raise ValueError(f"bar export is empty: {path.name}")
    if any(row["schema_version"] != "a1_xau_r6_native_bar_v1" or row["timeframe"] != timeframe for row in rows):
        raise ValueError(f"bar schema/timeframe mismatch: {path.name}")
    times = [_dt(row["open_time_broker"]) for row in rows]
    if times != sorted(set(times)):
        raise ValueError(f"bar timestamps not unique/increasing: {path.name}")
    step = {"H1": timedelta(hours=1), "H4": timedelta(hours=4), "D1": timedelta(days=1)}[timeframe]
    if not (test_start <= times[0] < test_start + step):
        raise ValueError(f"bar warm-up start mismatch: {path.name}: {times[0].isoformat()}")
    if not (test_end - step <= times[-1] < test_end):
        raise ValueError(f"bar exclusive-end coverage mismatch: {path.name}: {times[-1].isoformat()}")
    seconds = int(step.total_seconds())
    for first, second in zip(times, times[1:]):
        delta = int((second - first).total_seconds())
        if delta <= 0 or delta % seconds:
            raise ValueError(f"bar interval mismatch: {path.name}: {first.isoformat()}->{second.isoformat()}")
        allowed_session_gap = (
            (timeframe == "H1" and delta <= 2 * seconds)
            or (timeframe == "H4" and delta <= 2 * seconds)
        )
        if delta > seconds and not allowed_session_gap and not expected_weekend_gap(timeframe, first, second):
            raise ValueError(f"unexpected market-history gap: {path.name}: {first.isoformat()}->{second.isoformat()}")
    for row in rows:
        if any(int(row[name]) < 0 for name in ("tick_volume", "spread", "real_volume")):
            raise ValueError(f"negative bar volume/spread field: {path.name}")
    bars = [router.Bar(times[i], float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])) for i, row in enumerate(rows)]
    router.validate_bars(bars)
    return rows, bars


def prefix_sha(rows: Sequence[dict[str, str]], columns: Sequence[str], decision: datetime) -> tuple[str, str]:
    causal = [
        row for row, next_row in zip(rows, rows[1:])
        if _dt(next_row["open_time_broker"]) <= decision
    ]
    if not causal:
        raise ValueError("causal prefix is empty")
    data = ("\n".join("\t".join(row[column] for column in columns) for row in causal) + "\n").encode()
    return causal[-1]["open_time_broker"], hashlib.sha256(data).hexdigest()


def _close(native: float, python: float, rule: dict[str, float]) -> tuple[bool, float]:
    if not math.isfinite(native) or not math.isfinite(python):
        return False, math.inf
    difference = abs(native - python)
    limit = max(rule["absolute_tolerance"], rule["relative_tolerance"] * max(abs(native), abs(python)))
    return difference <= limit, difference


def python_metrics(router: Any, h1: Sequence[Any], h4: Sequence[Any], d1: Sequence[Any], decision: datetime) -> tuple[str, dict[str, float]]:
    state = router.classify_router(h1=h1, h4=h4, d1=d1, decision=decision)
    if state == "UNKNOWN":
        return state, {}
    h1_i, h4_i, d1_i = (router._last_completed_index(bars, decision) for bars in (h1, h4, d1))
    h1_atr, d1_atr = router.wilder_atr(h1), router.wilder_atr(d1)
    h4_fast, h4_slow = router.ema([bar.close for bar in h4[: h4_i + 1]], 20), router.ema([bar.close for bar in h4[: h4_i + 1]], 50)
    d1_fast, d1_slow = router.ema([bar.close for bar in d1[: d1_i + 1]], 20), router.ema([bar.close for bar in d1[: d1_i + 1]], 50)
    d1_60 = [value for value in d1_atr[d1_i - 59 : d1_i + 1] if value is not None]
    d1_252 = [value for value in d1_atr[d1_i - 251 : d1_i + 1] if value is not None]
    five = d1[d1_i - 4 : d1_i + 1]
    box_high, box_low = max(bar.high for bar in five), min(bar.low for bar in five)
    width = box_high - box_low
    median_range = router.median([bar.high - bar.low for bar in d1[d1_i - 19 : d1_i + 1]])
    return state, {
        "h1_atr14_shift1": h1_atr[h1_i],
        "h1_shock_ratio": (h1[h1_i].high - h1[h1_i].low) / h1_atr[h1_i],
        "h4_ema20_shift1": h4_fast[h4_i], "h4_ema50_shift1": h4_slow[h4_i],
        "h4_ema20_shift6": h4_fast[h4_i - 5], "h4_ema50_shift6": h4_slow[h4_i - 5],
        "d1_ema20_shift1": d1_fast[d1_i], "d1_ema50_shift1": d1_slow[d1_i],
        "d1_ema20_shift2": d1_fast[d1_i - 1], "d1_ema50_shift2": d1_slow[d1_i - 1],
        "d1_ema20_shift6": d1_fast[d1_i - 5], "d1_ema50_shift6": d1_slow[d1_i - 5],
        "d1_ema20_shift7": d1_fast[d1_i - 6], "d1_ema50_shift7": d1_slow[d1_i - 6],
        "d1_atr14_shift1": d1_atr[d1_i],
        "d1_atr_percentile_60_shift1": router.percentile_rank(d1_60, d1_atr[d1_i]),
        "d1_atr_percentile_252_shift1": router.percentile_rank(d1_252, d1_atr[d1_i]),
        "d1_box_high_5": box_high, "d1_box_low_5": box_low, "d1_box_width_5": width,
        "d1_box_average_5": width / 5.0, "d1_median_range_20": median_range,
        "d1_compression_box_to_median_ratio": (width / 5.0) / median_range,
    }


NUMERIC_RULE = {
    "h1_atr14_shift1": "atr", "h1_shock_ratio": "atr",
    "h4_ema20_shift1": "ema", "h4_ema50_shift1": "ema", "h4_ema20_shift6": "ema", "h4_ema50_shift6": "ema",
    "d1_ema20_shift1": "ema", "d1_ema50_shift1": "ema", "d1_ema20_shift2": "ema", "d1_ema50_shift2": "ema",
    "d1_ema20_shift6": "ema", "d1_ema50_shift6": "ema", "d1_ema20_shift7": "ema", "d1_ema50_shift7": "ema",
    "d1_atr14_shift1": "atr", "d1_atr_percentile_60_shift1": "percentile", "d1_atr_percentile_252_shift1": "percentile",
    "d1_box_high_5": "compression_metrics", "d1_box_low_5": "compression_metrics", "d1_box_width_5": "compression_metrics",
    "d1_box_average_5": "compression_metrics", "d1_median_range_20": "compression_metrics",
    "d1_compression_box_to_median_ratio": "compression_metrics",
}
RAW_NUMERIC_FIELDS = (
    "h1_shift1_high", "h1_shift1_low", "h1_shift1_range", "h4_close_shift1",
    "d1_close_shift1", "d1_close_shift2",
)


def verify_router_run(run_id: str, run_dir: Path, source: dict[str, Any], schema: dict[str, Any], buckets: Buckets, source_equivalence_sha256: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    router = load_python_router(source)
    try:
        environment = source["tester_environment"]
        test_start = _dt(environment["test_from_inclusive_broker_time"])
        test_end = _dt(environment["test_to_exclusive_broker_time"])
        h1_rows, h1 = load_bar_rows(run_dir / "native_h1_bars.tsv", schema, router, timeframe="H1", test_start=test_start, test_end=test_end)
        h4_rows, h4 = load_bar_rows(run_dir / "native_h4_bars.tsv", schema, router, timeframe="H4", test_start=test_start, test_end=test_end)
        d1_rows, d1 = load_bar_rows(run_dir / "native_d1_bars.tsv", schema, router, timeframe="D1", test_start=test_start, test_end=test_end)
        native = read_tsv(run_dir / "native_router_rows.tsv", schema["native_router_rows"]["columns"])
    except (FileNotFoundError, ValueError, KeyError) as exc:
        buckets.invalid.append(f"{run_id}: {exc}")
        return [], [], {}
    start = _dt(schema["native_router_rows"]["evidence_interval_from_inclusive"])
    end = _dt(schema["native_router_rows"]["evidence_interval_to_exclusive"])
    expected = [row["open_time_broker"] for row in h4_rows if start <= _dt(row["open_time_broker"]) < end]
    native_structure_valid = True
    invalid_native_rows: set[int] = set()
    for row_index, row in enumerate(native):
        try:
            if row["run_id"] != run_id or row["symbol"] != "XAUUSD":
                raise ValueError("Router row identity mismatch")
            if row["schema_version"] != "a1_xau_r6_native_router_row_v1":
                raise ValueError("Router row schema_version mismatch")
            if row["data_available"] not in {"true", "false"}:
                raise ValueError("Router row data_available is not true/false")
            if row["state_name"] not in NATIVE_TO_CANONICAL:
                raise ValueError("Router row state_name is not locked")
            native_code = int(row["state_code"])
            if native_code not in STATE_CODES.values() or native_code != STATE_CODES[NATIVE_TO_CANONICAL[row["state_name"]]]:
                raise ValueError("Router row state_code/name mismatch")
            if int(row["native_error_code"]) != 0:
                raise ValueError("Router row native_error_code is nonzero")
            if any(int(row[name]) < 0 for name in ("h1_bar_count", "h4_bar_count", "d1_bar_count")):
                raise ValueError("Router row bar count is negative")
            for name in ("timestamp_broker", "h1_shift1_time", "h4_shift1_time", "d1_shift1_time"):
                _dt(row[name])
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            native_structure_valid = False
            invalid_native_rows.add(row_index)
            buckets.invalid.append(f"{run_id}: malformed native Router row: {exc}")
        if row["router_source_commit"] != B.SOURCE_COMMIT or row["router_source_blob"] != B.SOURCE_BLOB:
            buckets.source.append(f"{run_id}: Router row source lineage mismatch")
        if row["source_equivalence_sha256"] != source_equivalence_sha256:
            buckets.source.append(f"{run_id}: Router row source-equivalence hash mismatch")
    actual = [row["timestamp_broker"] for row in native]
    if native_structure_valid and actual != expected:
        buckets.parity.append(f"{run_id}: H4 decision-row coverage mismatch expected={len(expected)} actual={len(actual)}")
    acceptance = schema["parity"]["acceptance"]
    parity_rows: list[dict[str, Any]] = []
    prefix_rows: list[dict[str, Any]] = []
    states = Counter()
    max_diff = {name: 0.0 for name in ("ema", "atr", "percentile", "compression_metrics")}
    first_mismatch = ""
    first_mismatch_timestamp = ""
    first_mismatch_field = ""
    state_match_count = 0
    availability_match_count = 0
    mismatch_count_by_native_state: Counter[str] = Counter()
    for row_index, row in enumerate(native):
        if row_index in invalid_native_rows:
            continue
        try:
            decision = _dt(row["timestamp_broker"])
            expected_counts = {
                "h1_bar_count": sum(bar.time <= decision for bar in h1),
                "h4_bar_count": sum(bar.time <= decision for bar in h4),
                "d1_bar_count": sum(bar.time <= decision for bar in d1),
            }
            if any(int(row[name]) != expected_value for name, expected_value in expected_counts.items()):
                buckets.invalid.append(f"{run_id}: native Router bar-count reconciliation mismatch at {row['timestamp_broker']}")
                continue
            python_state, metrics = python_metrics(router, h1, h4, d1, decision)
            canonical_native = NATIVE_TO_CANONICAL.get(row["state_name"], "INVALID")
            native_code = int(row["state_code"])
            state_match = canonical_native == python_state and native_code == STATE_CODES[python_state]
            available_match = (row["data_available"].lower() == "true") == (python_state != "UNKNOWN")
            state_match_count += int(state_match)
            availability_match_count += int(available_match)
            states[canonical_native] += 1
            mismatch_fields: list[str] = []
            if not state_match:
                mismatch_fields.append("state")
            if not available_match:
                mismatch_fields.append("data_available")
            per_row_diff = {name: 0.0 for name in max_diff}
            for field_name, python_value in metrics.items():
                if not row[field_name]:
                    mismatch_fields.append(field_name)
                    continue
                rule_name = NUMERIC_RULE[field_name]
                matched, difference = _close(float(row[field_name]), float(python_value), acceptance[rule_name])
                per_row_diff[rule_name] = max(per_row_diff[rule_name], difference)
                max_diff[rule_name] = max(max_diff[rule_name], difference)
                if not matched:
                    mismatch_fields.append(field_name)
            if python_state == "UNKNOWN" and any(row[name] for name in (*NUMERIC_RULE, *RAW_NUMERIC_FIELDS)):
                mismatch_fields.append("unavailable_numeric_not_empty")
            h1_last, h1_hash = prefix_sha(h1_rows, schema["bar_exports"]["columns"], decision)
            h4_last, h4_hash = prefix_sha(h4_rows, schema["bar_exports"]["columns"], decision)
            d1_last, d1_hash = prefix_sha(d1_rows, schema["bar_exports"]["columns"], decision)
            if row["h1_shift1_time"] != h1_last or row["h4_shift1_time"] != h4_last or row["d1_shift1_time"] != d1_last:
                mismatch_fields.append("causal_prefix_last_completed_time")
            h1_i, h4_i, d1_i = (router._last_completed_index(bars, decision) for bars in (h1, h4, d1))
            raw_values = {
                "h1_shift1_high": h1[h1_i].high,
                "h1_shift1_low": h1[h1_i].low,
                "h1_shift1_range": h1[h1_i].high - h1[h1_i].low,
                "h4_close_shift1": h4[h4_i].close,
                "d1_close_shift1": d1[d1_i].close,
                "d1_close_shift2": d1[d1_i - 1].close,
            }
            if python_state != "UNKNOWN":
                for field_name, expected_value in raw_values.items():
                    if not row[field_name] or not _close(float(row[field_name]), expected_value, acceptance["compression_metrics"])[0]:
                        mismatch_fields.append(field_name)
            if mismatch_fields:
                buckets.parity.append(f"{run_id}: parity mismatch {row['timestamp_broker']}: {','.join(mismatch_fields)}")
                first_mismatch = first_mismatch or f"{row['timestamp_broker']}:{mismatch_fields[0]}"
                first_mismatch_timestamp = first_mismatch_timestamp or row["timestamp_broker"]
                first_mismatch_field = first_mismatch_field or mismatch_fields[0]
                mismatch_count_by_native_state[canonical_native] += 1
            parity_rows.append({
                "run_id": run_id, "timestamp_broker": row["timestamp_broker"], "symbol": row["symbol"],
                "native_data_available": row["data_available"], "python_data_available": str(python_state != "UNKNOWN").lower(),
                "native_state_code": native_code, "python_state_code": STATE_CODES[python_state],
                "native_state_name": canonical_native, "python_state_name": python_state,
                "state_exact_match": str(state_match).lower(), "data_available_exact_match": str(available_match).lower(),
                "ema_max_absolute_difference": per_row_diff["ema"], "atr_max_absolute_difference": per_row_diff["atr"],
                "percentile_max_absolute_difference": per_row_diff["percentile"],
                "compression_metric_max_absolute_difference": per_row_diff["compression_metrics"],
                "first_mismatch_field": mismatch_fields[0] if mismatch_fields else "",
            })
            prefix_rows.append({
                "run_id": run_id, "timestamp_broker": row["timestamp_broker"], "symbol": row["symbol"],
                "h1_last_completed_time": h1_last, "h1_prefix_sha256": h1_hash,
                "h4_last_completed_time": h4_last, "h4_prefix_sha256": h4_hash,
                "d1_last_completed_time": d1_last, "d1_prefix_sha256": d1_hash,
            })
        except (ValueError, KeyError, IndexError, ZeroDivisionError, TypeError, OverflowError) as exc:
            buckets.invalid.append(f"{run_id}: Router evidence row malformed: {exc}")
    total = len(native)
    summary = {
        "run_id": run_id, "native_decision_rows": total, "expected_h4_decisions": len(expected),
        "state_counts": dict(sorted(states.items())), "first_mismatch": first_mismatch,
        "state_exact_match_rate": state_match_count / total if total else 0.0,
        "data_availability_exact_match_rate": availability_match_count / total if total else 0.0,
        "first_mismatch_timestamp": first_mismatch_timestamp, "first_mismatch_field": first_mismatch_field,
        "mismatch_count_by_native_state": dict(sorted(mismatch_count_by_native_state.items())),
        "ema_max_absolute_difference": max_diff["ema"], "atr_max_absolute_difference": max_diff["atr"],
        "percentile_max_absolute_difference": max_diff["percentile"],
        "compression_metric_max_absolute_difference": max_diff["compression_metrics"],
    }
    return parity_rows, prefix_rows, summary


def verify_ordercalcprofit(run_id: str, run_dir: Path, schema: dict[str, Any], buckets: Buckets) -> list[dict[str, Any]]:
    contract = schema["native_ordercalcprofit"]
    try:
        probes = read_tsv(run_dir / contract["file"], contract["columns"])
        contract_rows = read_tsv(run_dir / "native_contract.tsv", schema["contract_snapshot"]["columns"])
    except (FileNotFoundError, ValueError) as exc:
        buckets.invalid.append(f"{run_id}: {exc}")
        return []
    if len(contract_rows) != 1 or any(value == "" for value in contract_rows[0].values()):
        buckets.invalid.append(f"{run_id}: contract snapshot incomplete")
        return []
    c = contract_rows[0]
    expected_contract = {
        "server": "Capital.ComMena-Demo", "company": "Capital Com Mena Securities Trading L.L.C",
        "account_login": "1025742", "account_currency": "USD", "account_leverage": "50", "symbol": "XAUUSD",
    }
    for key, expected in expected_contract.items():
        if c.get(key) != expected:
            buckets.invalid.append(f"{run_id}: contract environment mismatch {key}={c.get(key)!r}")
    try:
        _dt(c["timestamp_broker"])
        positive_contract = ("point", "volume_min", "volume_step", "volume_max", "contract_size", "tick_size", "tick_value", "tick_value_profit", "tick_value_loss")
        if any(not math.isfinite(float(c[name])) or float(c[name]) <= 0 for name in positive_contract):
            buckets.invalid.append(f"{run_id}: contract positive finite numeric invariant failed")
        if float(c["volume_min"]) > float(c["volume_max"]):
            buckets.invalid.append(f"{run_id}: contract volume bounds invalid")
        for name in ("digits", "stops_level", "freeze_level", "margin_mode", "trade_calc_mode", "trade_mode"):
            if int(c[name]) < 0:
                buckets.invalid.append(f"{run_id}: contract nonnegative integer invariant failed: {name}")
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        buckets.invalid.append(f"{run_id}: malformed native contract: {exc}")
        return []
    ids = [row["probe_id"] for row in probes]
    if ids != contract["required_probe_ids"] or len(probes) != 12:
        buckets.invalid.append(f"{run_id}: OrderCalcProfit probe identity/order mismatch")
    rows: list[dict[str, Any]] = []
    rule = schema["parity"]["acceptance"]["ordercalcprofit_absolute_loss"]
    tick_size, tick_value_loss = float(c["tick_size"]), float(c["tick_value_loss"])
    exits = [2002.49, 2002.50, 2002.51, 2024.99, 2025.00, 2025.01, 1997.51, 1997.50, 1997.49, 1975.01, 1975.00, 1974.99]
    expected_by_id = {
        probe_id: ("SELL" if probe_id.startswith("SELL") else "BUY", exit_price)
        for probe_id, exit_price in zip(contract["required_probe_ids"], exits)
    }
    for probe in probes:
        try:
            expected_order, expected_exit = expected_by_id[probe["probe_id"]]
            volume, entry, exit_price = float(probe["volume"]), float(probe["entry_price"]), float(probe["exit_price"])
            native_profit, native_loss = float(probe["profit_account_currency"]), float(probe["absolute_loss"])
            exact_ok = (
                probe["order_type"] == expected_order and probe["symbol"] == "XAUUSD"
                and volume == float(c["volume_min"]) and entry == 2000.0 and exit_price == expected_exit
                and probe["success"].lower() == "true" and probe["last_error"] == "0"
                and probe["evidence_class"] == contract["evidence_class"]
                and math.isfinite(native_profit) and math.isfinite(native_loss)
                and native_profit < 0.0 and native_loss == abs(native_profit)
            )
            if not exact_ok:
                buckets.invalid.append(f"{run_id}: exact native OrderCalcProfit probe contract failed {probe['probe_id']}")
                continue
            python_loss = abs(exit_price - entry) / tick_size * tick_value_loss * volume
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            buckets.invalid.append(f"{run_id}: malformed native OrderCalcProfit probe: {exc}")
            continue
        matched, difference = _close(native_loss, python_loss, {
            "absolute_tolerance": rule["absolute_tolerance_account_currency"], "relative_tolerance": rule["relative_tolerance"]
        })
        if not matched:
            buckets.parity.append(f"{run_id}: OrderCalcProfit parity mismatch {probe['probe_id']}")
        rows.append({
            "run_id": run_id, "probe_id": probe["probe_id"], "native_absolute_loss": native_loss,
            "python_absolute_loss": python_loss, "absolute_difference": difference, "match": str(matched).lower(),
        })
    return rows


def normalized_tsv_bytes(path: Path, *, blank_columns: set[str], normalize_run_tokens: bool = False) -> bytes:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = list(reader.fieldnames or ())
        rows = list(reader)
    for row in rows:
        for column in blank_columns:
            if column in row:
                row[column] = "<NORMALIZED>"
        if normalize_run_tokens:
            for column, value in row.items():
                row[column] = value.replace("np1_run1_", "np1_<RUN>_").replace("np1_run2_", "np1_<RUN>_")
                if row[column] in {"run1", "run2"}:
                    row[column] = "<RUN>"
    lines = ["\t".join(columns), *("\t".join(row[column] for column in columns) for row in rows)]
    return ("\n".join(lines) + "\n").encode()


def verify_two_run_determinism(evidence_dir: Path, buckets: Buckets) -> None:
    rules = {
        "native_router_rows.tsv": ({"run_id"}, False), "native_h1_bars.tsv": (set(), False),
        "native_h4_bars.tsv": (set(), False), "native_d1_bars.tsv": (set(), False),
        "native_contract.tsv": ({"timestamp_broker"}, False), "native_ordercalcprofit.tsv": (set(), False),
        "native_assertions.tsv": (set(), True),
    }
    for filename, (blank, normalize_run_tokens) in rules.items():
        try:
            first = normalized_tsv_bytes(evidence_dir / "runs" / "run1" / filename, blank_columns=blank, normalize_run_tokens=normalize_run_tokens)
            second = normalized_tsv_bytes(evidence_dir / "runs" / "run2" / filename, blank_columns=blank, normalize_run_tokens=normalize_run_tokens)
            if first != second:
                buckets.parity.append(f"two-run normalized mismatch: {filename}")
        except (FileNotFoundError, ValueError) as exc:
            buckets.invalid.append(f"two-run determinism input invalid: {exc}")


def verify_ini(path: Path, run_id: str, buckets: Buckets) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        buckets.invalid.append(f"{run_id}: tester.ini missing")
        return
    try:
        import run_a1_xau_r6_market_only_native_parity_exact as runner
        actual = runner.parse_ini_exact(text)
        expected = runner.parse_ini_exact(
            runner.render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}")
        )
        if actual != expected:
            buckets.invalid.append(f"{run_id}: tester.ini exact unique key/value contract mismatch")
    except (RuntimeError, ValueError) as exc:
        buckets.invalid.append(f"{run_id}: tester.ini malformed: {exc}")


def status_for(buckets: Buckets) -> str:
    if buckets.invalid:
        return "R6_NP1_EVIDENCE_INVALID"
    if buckets.source:
        return "R6_NP1_SOURCE_EQUIVALENCE_FAIL"
    if buckets.zero_action:
        return "R6_NP1_ZERO_ACTION_CONTRACT_FAIL"
    if buckets.parity:
        return "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"
    return "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS"


def attested_artifact_hashes(evidence_dir: Path) -> dict[str, str]:
    return {
        path.relative_to(evidence_dir).as_posix(): sha256_file(path)
        for path in sorted(evidence_dir.rglob("*")) if path.is_file()
        and path.name not in {"test_validation.md", "manifest.json", "manifest.sha256"}
    }


def validate_attestation(evidence_dir: Path, attestation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version", "git_head", "git_tree", "git_status_porcelain", "os", "architecture",
        "python_version", "python_executable", "dependency_versions", "mt5_terminal_build", "metaeditor_version",
        "same_ex5_sha256_run1_run2", "commands", "artifact_sha256", "environment", "review_authority",
    }
    if set(attestation) != required:
        return ["exact-commit attestation field set mismatch"]
    if attestation["schema_version"] != "a1_xau_np1_exact_commit_attestation_v1":
        errors.append("exact-commit attestation schema mismatch")
    for name in ("git_head", "git_tree"):
        if re.fullmatch(r"[0-9a-f]{40}", str(attestation[name])) is None:
            errors.append(f"exact-commit attestation invalid {name}")
    if attestation["git_status_porcelain"] != "":
        errors.append("exact-commit attestation worktree was not clean")
    if attestation["mt5_terminal_build"] != 5833 or attestation["metaeditor_version"] != "5.0.0.5833":
        errors.append("exact-commit attestation build mismatch")
    authority = attestation["review_authority"]
    if not isinstance(authority, dict) or set(authority) != {
        "controlling_review_artifact", "controlling_review_sha256", "reviewed_generator_commit", "reviewed_generator_tree",
        "authorization_status", "review_verdict",
    }:
        errors.append("exact review authority attestation schema mismatch")
    else:
        if re.fullmatch(r"A1_XAU_NP1B4_[A-Z0-9_]+\.md", authority["controlling_review_artifact"]) is None:
            errors.append("controlling NP1-B4 review artifact mismatch")
        if re.fullmatch(r"[0-9a-f]{64}", authority["controlling_review_sha256"]) is None:
            errors.append("controlling NP1-B4 review SHA256 mismatch")
        if authority["authorization_status"] != "AUTHORIZED" or authority["review_verdict"] != "PASS":
            errors.append("controlling NP1-B4 review does not explicitly authorize NP1-C with PASS")
        if attestation["git_head"] != authority["reviewed_generator_commit"] or attestation["git_tree"] != authority["reviewed_generator_tree"]:
            errors.append("attested HEAD/tree do not equal exact reviewed generator commit/tree")
        try:
            completed = subprocess.run(
                ["git", "rev-parse", f"{authority['reviewed_generator_commit']}^{{tree}}"], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            resolved_tree = completed.stdout.decode("ascii", errors="strict").strip()
            if completed.returncode != 0 or resolved_tree != authority["reviewed_generator_tree"]:
                errors.append("reviewed generator commit/tree is not the exact repository object")
        except (OSError, UnicodeError):
            errors.append("reviewed generator commit/tree could not be resolved")
    dependencies = attestation["dependency_versions"]
    if not isinstance(dependencies, dict) or set(dependencies) != {"python_implementation", "pytest", "third_party_runtime_dependencies"}:
        errors.append("dependency-version attestation mismatch")
    elif not dependencies["python_implementation"] or not dependencies["pytest"] or dependencies["third_party_runtime_dependencies"] != {}:
        errors.append("dependency-version attestation incomplete")
    commands = attestation["commands"]
    command_fields = {"command", "exit_code", "stdout_base64", "stderr_base64", "stdout_sha256", "stderr_sha256"}
    if not isinstance(commands, list) or len(commands) != 5:
        errors.append("exact-commit attestation requires compile, two tester, finalizer, and verifier commands")
    else:
        for index, row in enumerate(commands):
            if not isinstance(row, dict) or set(row) != command_fields:
                errors.append(f"exact-commit command attestation schema mismatch at {index}")
                continue
            if not isinstance(row["command"], list) or not row["command"] or not isinstance(row["exit_code"], int):
                errors.append(f"exact-commit command attestation value mismatch at {index}")
            try:
                stdout = base64.b64decode(row["stdout_base64"], validate=True)
                stderr = base64.b64decode(row["stderr_base64"], validate=True)
            except (ValueError, TypeError):
                errors.append(f"exact-commit command stream encoding mismatch at {index}")
                continue
            if hashlib.sha256(stdout).hexdigest() != row["stdout_sha256"] or hashlib.sha256(stderr).hexdigest() != row["stderr_sha256"]:
                errors.append(f"exact-commit command stream content/hash mismatch at {index}")
        if all(isinstance(row, dict) and isinstance(row.get("command"), list) for row in commands):
            command_values = [row["command"] for row in commands]
            lowered = [[str(part).replace("\\", "/").lower() for part in command] for command in command_values]
            compile_ok = (
                Path(str(command_values[0][0])).name.lower() == "metaeditor64.exe"
                and any(part.startswith("/compile:") for part in lowered[0])
                and any(part.startswith("/log:") for part in lowered[0])
                and commands[0]["exit_code"] in {0, 1}
            )
            if not compile_ok:
                errors.append("attested command 1 is not the exact MetaEditor compile contract")
            for index, run_id in ((1, "run1"), (2, "run2")):
                tester_ok = (
                    Path(str(command_values[index][0])).name.lower() == "terminal64.exe"
                    and "/portable" in lowered[index]
                    and any(part.startswith("/config:") and part.endswith(f"np1_{run_id}.ini") for part in lowered[index])
                    and commands[index]["exit_code"] == 0
                )
                if not tester_ok:
                    errors.append(f"attested command {index + 1} is not the exact Strategy Tester {run_id} contract")
            finalizer = lowered[3]
            finalizer_ok = (
                len(finalizer) == 7 and Path(str(command_values[3][0])).resolve() == Path(attestation["python_executable"]).resolve()
                and Path(str(command_values[3][1])).resolve() == Path(__file__).resolve()
                and Path(str(command_values[3][2])).is_absolute()
                and finalizer[3] == "--finalize" and finalizer[4] == "--attestation-json" and finalizer[6] == "--quiet"
                and commands[3]["exit_code"] == 0
            )
            verifier = lowered[4]
            verifier_ok = (
                len(verifier) == 4 and Path(str(command_values[4][0])).resolve() == Path(attestation["python_executable"]).resolve()
                and Path(str(command_values[4][1])).resolve() == Path(__file__).resolve()
                and Path(str(command_values[4][2])).resolve() == Path(str(command_values[3][2])).resolve()
                and verifier[3] == "--quiet" and commands[4]["exit_code"] == 0
            )
            if not finalizer_ok:
                errors.append("attested command 4 is not the exact quiet finalizer contract")
            if not verifier_ok:
                errors.append("attested command 5 is not the exact quiet read-only verifier contract")
            for index in (3, 4):
                if commands[index]["stdout_base64"] != "" or commands[index]["stderr_base64"] != "":
                    errors.append(f"attested command {index + 1} finalizer/verifier streams must be empty")
    if attestation["artifact_sha256"] != attested_artifact_hashes(evidence_dir):
        errors.append("exact-commit attestation artifact hash set mismatch")
    ex5 = evidence_dir / "compiled" / Path(B.ORACLE_NAME).with_suffix(".ex5").name
    if ex5.is_file() and attestation["same_ex5_sha256_run1_run2"] != sha256_file(ex5):
        errors.append("exact-commit attestation EX5 hash mismatch")
    environment = attestation["environment"]
    expected_environment = {
        "account_login": 1025742, "server": "Capital.ComMena-Demo", "currency": "USD",
        "leverage": "1:50", "symbol": "XAUUSD",
    }
    if not isinstance(environment, dict) or any(environment.get(key) != value for key, value in expected_environment.items()):
        errors.append("exact-commit attestation environment mismatch")
    for key in ("os", "architecture", "python_version", "python_executable"):
        if not isinstance(attestation[key], str) or not attestation[key]:
            errors.append(f"exact-commit attestation missing dependency/environment value: {key}")
    return errors


def _render_validation(status: str, errors: Sequence[str], attestation: dict[str, Any]) -> str:
    payload = json.dumps(attestation, indent=2, sort_keys=True)
    return (
        f"# NP1 Validation\n\nTerminal status: `{status}`\n\nError count: `{len(errors)}`\n\n"
        "## Exact commit, environment, commands, and artifacts\n\n```json\n" + payload + "\n```\n"
    )


def parse_validation_attestation(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"## Exact commit, environment, commands, and artifacts\s+```json\s+(\{.*\})\s+```", text, re.DOTALL)
    if not match:
        raise ValueError("test_validation.md attestation block missing")
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        raise ValueError("test_validation.md attestation is not an object")
    return value


def _write_reports(
    evidence_dir: Path, status: str, buckets: Buckets, metrics: dict[str, Any], attestation: dict[str, Any]
) -> None:
    payload = {
        "schema_version": "a1_xau_r6_market_only_native_parity_exact_v1", "status": status,
        "boundary": {"census_generated": False, "pnl_calculated": False, "broker_action": False},
        "errors": {"invalid": buckets.invalid, "source": buckets.source, "zero_action": buckets.zero_action, "parity": buckets.parity},
        "metrics": metrics,
    }
    json_path = evidence_dir / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# A1 XAU R6 Market-Only Native-Parity Exact Evidence", "", f"Status: `{status}`", "",
        "No R6 census, P/L, exit, target, MFE, MAE, demo/live, or broker action was produced.", "", "## Errors", "",
    ]
    errors = buckets.all()
    lines.extend([f"- {error}" for error in errors] if errors else ["- None"])
    (evidence_dir / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    (evidence_dir / "test_validation.md").write_text(
        _render_validation(status, errors, attestation), encoding="utf-8", newline="\n"
    )


def generate_manifest(evidence_dir: Path, schema: dict[str, Any]) -> None:
    excluded = {"manifest.json", "manifest.sha256"}
    expected = set(schema["exact_tree"]) - excluded
    actual = {path.relative_to(evidence_dir).as_posix() for path in evidence_dir.rglob("*") if path.is_file()} - excluded
    if actual != expected:
        raise ValueError(f"cannot generate manifest for incomplete/unexpected tree: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    rows = [
        {"relative_path": relative, "size_bytes": (evidence_dir / relative).stat().st_size, "sha256": sha256_file(evidence_dir / relative)}
        for relative in sorted(expected)
    ]
    manifest = evidence_dir / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "a1_xau_r6_evidence_manifest_v1", "artifacts": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (evidence_dir / "manifest.sha256").write_text(sha256_file(manifest) + "\n", encoding="ascii", newline="\n")


def verify_nonrecursive_manifest(evidence_dir: Path, schema: dict[str, Any]) -> list[str]:
    manifest, sidecar = evidence_dir / "manifest.json", evidence_dir / "manifest.sha256"
    if not manifest.is_file() or not sidecar.is_file():
        return ["manifest pair missing"]
    payload = read_json(manifest)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return ["manifest artifacts must be a list"]
    errors: list[str] = []
    listed = {row.get("relative_path") for row in artifacts if isinstance(row, dict)}
    if {"manifest.json", "manifest.sha256"} & listed:
        errors.append("manifest pair must be excluded from manifest artifact rows")
    expected = set(schema["exact_tree"]) - {"manifest.json", "manifest.sha256"}
    if listed != expected:
        errors.append("manifest artifact path set mismatch")
    for row in artifacts:
        if not isinstance(row, dict) or set(row) != {"relative_path", "size_bytes", "sha256"}:
            errors.append("manifest artifact row schema mismatch")
            continue
        path = evidence_dir / row["relative_path"]
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or sha256_file(path) != row["sha256"]:
            errors.append(f"manifest artifact mismatch: {row['relative_path']}")
    if sidecar.read_text(encoding="ascii") != sha256_file(manifest) + "\n":
        errors.append("manifest.sha256 mismatch")
    return errors


def finalize_evidence_directory(
    evidence_dir: Path, *, attestation: dict[str, Any] | None = None
) -> VerificationResult:
    source, schema, _ = load_contracts()
    buckets = Buckets()
    metrics: dict[str, Any] = {}
    if attestation is None:
        try:
            attestation = parse_validation_attestation(evidence_dir / "test_validation.md")
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            attestation = {}
            buckets.invalid.append(f"exact-commit attestation missing/malformed: {exc}")
    if attestation:
        buckets.invalid.extend(validate_attestation(evidence_dir, attestation))
    verify_compile_packet(evidence_dir / "compiled", buckets)
    equivalence_path = evidence_dir / "compiled" / "source_equivalence.json"
    source_equivalence_sha256 = sha256_file(equivalence_path) if equivalence_path.is_file() else ""
    parity_rows: list[dict[str, Any]] = []
    prefix_rows: list[dict[str, Any]] = []
    ordercalc_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for run_id in ("run1", "run2"):
        run_dir = evidence_dir / "runs" / run_id
        verify_ini(run_dir / "tester.ini", run_id, buckets)
        try:
            assertion_errors = verify_assertions(run_dir / "native_assertions.tsv", schema, run_id)
            for error in assertion_errors:
                if any(name in error for name in ("report_zero_trades", "report_zero_deals", "order_zero_bytes", "deal_zero_bytes", "open_positions_zero", "pending_orders_zero")):
                    buckets.zero_action.append(f"{run_id}: {error}")
                else:
                    buckets.invalid.append(f"{run_id}: {error}")
            report = verify_native_report(run_dir / "native_report.htm", run_id, buckets)
            metrics.setdefault("native_reports", {})[run_id] = {
                "bars": report["bars"], "ticks": report["ticks"],
                "total_trades": report["total_trades"], "total_deals": report["total_deals"],
            }
            for sentinel in ("order.zero", "deal.zero"):
                if not (run_dir / sentinel).is_file() or (run_dir / sentinel).stat().st_size != 0:
                    buckets.zero_action.append(f"{run_id}: {sentinel} is missing or nonempty")
        except (FileNotFoundError, ValueError) as exc:
            buckets.invalid.append(f"{run_id}: {exc}")
        rows, prefixes, summary = verify_router_run(run_id, run_dir, source, schema, buckets, source_equivalence_sha256)
        parity_rows.extend(rows); prefix_rows.extend(prefixes); summaries.append(summary)
        ordercalc_rows.extend(verify_ordercalcprofit(run_id, run_dir, schema, buckets))
    verify_two_run_determinism(evidence_dir, buckets)
    reports = metrics.get("native_reports", {})
    if set(reports) == {"run1", "run2"} and (
        reports["run1"].get("bars"), reports["run1"].get("ticks")
    ) != (
        reports["run2"].get("bars"), reports["run2"].get("ticks")
    ):
        buckets.invalid.append("two-run native report bar/tick count mismatch")
    parity_dir = evidence_dir / "parity"
    router_columns = ["run_id", *schema["parity"]["router_parity_columns"]]
    prefix_columns = ["run_id", *schema["parity"]["native_prefix_chain_hashes_columns"]]
    order_columns = ["run_id", *schema["parity"]["ordercalcprofit_parity_columns"]]
    write_csv(parity_dir / "router_python_native_parity.csv", router_columns, parity_rows)
    write_csv(parity_dir / "native_prefix_chain_hashes.csv", prefix_columns, prefix_rows)
    write_csv(parity_dir / "ordercalcprofit_python_native_parity.csv", order_columns, ordercalc_rows)
    write_csv(parity_dir / "router_state_summary.csv", [
        "run_id", "native_decision_rows", "expected_h4_decisions", "state_counts",
        "state_exact_match_rate", "data_availability_exact_match_rate", "first_mismatch_timestamp",
        "first_mismatch_field", "mismatch_count_by_native_state", "ema_max_absolute_difference",
        "atr_max_absolute_difference", "percentile_max_absolute_difference", "compression_metric_max_absolute_difference",
    ], [
        {
            **row, "state_counts": json.dumps(row.get("state_counts", {}), sort_keys=True),
            "mismatch_count_by_native_state": json.dumps(row.get("mismatch_count_by_native_state", {}), sort_keys=True),
        } for row in summaries
    ])
    metrics["runs"] = summaries
    status = status_for(buckets)
    _write_reports(evidence_dir, status, buckets, metrics, attestation)
    try:
        generate_manifest(evidence_dir, schema)
    except ValueError as exc:
        buckets.invalid.append(str(exc))
        status = status_for(buckets)
        _write_reports(evidence_dir, status, buckets, metrics, attestation)
        try:
            generate_manifest(evidence_dir, schema)
        except ValueError:
            pass
    return VerificationResult(status, tuple(buckets.all()), metrics)


def verify_evidence_directory(evidence_dir: Path) -> VerificationResult:
    def snapshot() -> dict[str, tuple[int, str]]:
        return {
            path.relative_to(evidence_dir).as_posix(): (path.stat().st_size, sha256_file(path))
            for path in sorted(evidence_dir.rglob("*")) if path.is_file()
        }

    before = snapshot()
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    verified_result: VerificationResult | None = None
    try:
        _, schema, _ = load_contracts()
        errors.extend(verify_nonrecursive_manifest(evidence_dir, schema))
        attestation = parse_validation_attestation(evidence_dir / "test_validation.md")
        errors.extend(validate_attestation(evidence_dir, attestation))
        with tempfile.TemporaryDirectory(prefix="a1-xau-np1-read-only-verify-") as temporary:
            recomputed_dir = Path(temporary) / "evidence"
            shutil.copytree(evidence_dir, recomputed_dir)
            result = finalize_evidence_directory(recomputed_dir, attestation=attestation)
            metrics = result.metrics
            derived = {
                "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.md",
                "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json",
                "test_validation.md", "manifest.json", "manifest.sha256",
                "parity/router_python_native_parity.csv", "parity/router_state_summary.csv",
                "parity/native_prefix_chain_hashes.csv", "parity/ordercalcprofit_python_native_parity.csv",
            }
            for relative in sorted(derived):
                original, expected = evidence_dir / relative, recomputed_dir / relative
                if not original.is_file() or not expected.is_file() or original.read_bytes() != expected.read_bytes():
                    errors.append(f"read-only derived artifact mismatch: {relative}")
            if not errors:
                verified_result = result
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, json.JSONDecodeError) as exc:
        errors.append(f"malformed evidence: {exc}")
    finally:
        after = snapshot()
        if after != before:
            errors.append("read-only verifier mutated the evidence directory")
    if verified_result is not None and not errors:
        return verified_result
    return VerificationResult("R6_NP1_EVIDENCE_INVALID", tuple(errors), metrics)


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--attestation-json", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    if args.finalize:
        if args.attestation_json is None:
            parser.error("--finalize requires --attestation-json")
        result = finalize_evidence_directory(args.evidence_dir.resolve(), attestation=read_json(args.attestation_json))
    else:
        if args.attestation_json is not None:
            parser.error("--attestation-json is only valid with --finalize")
        result = verify_evidence_directory(args.evidence_dir.resolve())
    if not args.quiet:
        print(json.dumps({"status": result.status, "errors": result.errors, "metrics": result.metrics}, indent=2))
    return 0 if result.status in {
        "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS",
        "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL",
    } else 1


if __name__ == "__main__":
    raise SystemExit(_main())
