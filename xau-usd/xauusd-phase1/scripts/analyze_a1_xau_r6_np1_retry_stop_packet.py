"""Deterministic, read-only NP1-F1 retry-stop packet diagnostic."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Sequence

import build_a1_xau_r6_market_only_native_parity_oracle as B


ROOT = Path(__file__).resolve().parents[1]
REVIEWED_COMMIT = "40e2b0963f1c52e3f5468291ba4e11ad23ec0567"
REVIEWED_TREE = "7a6568ce038378e192545b0b61f28501eace5d4b"
AUTHORIZATION_SHA256 = "88ea4593ee3fe30018971c0816a811cf9a60d9044a62e9c9d2dc8f274d4050e5"
CONTRACT_SHA256 = "8834161b97f14dc3c1a5d88e4dd0d4cf2632140d6bfcf10676467d4f25e36c2e"
RETRY_MANIFEST_SHA256 = "b58a8324e74159240fd8d9e8e71b0ae26a1b5e084e4f8484b74fe793e832c6ee"
CONTRACT_PATH = ROOT / "docs" / "A1_XAU_R6_CAPITALCOM_SESSION_AND_HISTORY_STABILITY_CONTRACT_V1.json"
RETRY_MANIFEST_PATH = ROOT / "outputs" / "manifests" / "A1_XAU_R6_NP1_RETRY_LOCK_MANIFEST_V1.json"
PRIOR_GAPS_PATH = ROOT / "outputs" / "reports" / "A1_XAU_R6_NP1C_STOP_DIAGNOSTIC_20260712" / "analysis" / "market_gap_inventory.csv"
EXPECTED_REPORT = {"period": "M5 (2015.06.01 - 2026.07.01)", "bars": 779961, "ticks": 391745965, "total_trades": 0, "total_deals": 0}
EXPECTED_BAR_FILES = {
    "H1": ("9f79b8e4c844c4d1c64833f90d6d69b8a2ee30a296fafca031c5c01c68d73bff", 65332),
    "H4": ("0f977b7dcb6ed49af135270954d0395c153ba7db9230feece11a17e7b5607f2c", 17673),
    "D1": ("88cc8a3ae2b2f04d809a70942c480632c8648b9b9eeeaa126ba9e5fd1b7f6288", 3439),
}
TIMEFRAME_SECONDS = {"H1": 3600, "H4": 14400, "D1": 86400}
BAR_COLUMNS = ("schema_version", "timeframe", "open_time_broker", "open", "high", "low", "close", "tick_volume", "spread", "real_volume")
PARTIAL_FILES = {
    "compiled/A1XauR6MarketOnlyNativeParityOracle.mq5", "compiled/A1XauR6MarketOnlyNativeParityOracle.ex5",
    "compiled/compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log", "compiled/source_equivalence.json",
    *(f"runs/{run}/{name}" for run in ("run1", "run2") for name in (
        "tester.ini", "native_report.htm", "native_router_rows.tsv", "native_h1_bars.tsv", "native_h4_bars.tsv",
        "native_d1_bars.tsv", "native_contract.tsv", "native_ordercalcprofit.tsv", "native_assertions.tsv", "order.zero", "deal.zero",
    )),
}
WARMUP_FILES = {
    "tester.ini", "native_report.htm", "native_router_rows.tsv", "native_h1_bars.tsv", "native_h4_bars.tsv",
    "native_d1_bars.tsv", "native_contract.tsv", "native_ordercalcprofit.tsv", "native_assertions.tsv", "order.zero", "deal.zero",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _actual_files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _inventory(root: Path) -> list[dict[str, Any]]:
    return [
        {"relative_path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix())
    ]


class _Mt5CellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[str] = []
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "td":
            self.depth, self.parts = 1, []
        elif self.depth:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self.depth:
            return
        self.depth -= 1
        if tag.lower() == "td" and self.depth == 0:
            self.cells.append(" ".join("".join(self.parts).split()))

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.parts.append(data)


def _decode(path: Path) -> str:
    raw = path.read_bytes()
    return raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.decode("utf-8-sig")


def parse_report(path: Path) -> dict[str, Any]:
    parser = _Mt5CellParser()
    parser.feed(_decode(path))
    fields: dict[str, list[str]] = {}
    for index, cell in enumerate(parser.cells[:-1]):
        if cell.endswith(":"):
            fields.setdefault(cell[:-1], []).append(parser.cells[index + 1])

    def one(label: str) -> str:
        values = fields.get(label, [])
        if len(values) != 1:
            raise ValueError(f"native report requires one {label}")
        return values[0]

    def integer(label: str) -> int:
        match = re.search(r"[0-9][0-9,\s]*", one(label))
        if match is None:
            raise ValueError(f"invalid report {label}")
        return int(re.sub(r"[\s,]", "", match.group(0)))

    return {"period": one("Period"), "bars": integer("Bars"), "ticks": integer("Ticks"), "total_trades": integer("Total Trades"), "total_deals": integer("Total Deals")}


def read_bars(path: Path, timeframe: str) -> tuple[list[dict[str, str]], dict[datetime, dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != BAR_COLUMNS:
            raise ValueError(f"bar header mismatch: {path}")
        rows = list(reader)
    indexed: dict[datetime, dict[str, str]] = {}
    prior: datetime | None = None
    for row in rows:
        current = datetime.fromisoformat(row["open_time_broker"])
        if row["timeframe"] != timeframe or current in indexed or (prior is not None and current <= prior):
            raise ValueError(f"bar order/timeframe/duplicate mismatch: {path}")
        indexed[current] = row
        prior = current
    return rows, indexed


def gap_set(rows: list[dict[str, str]], timeframe: str) -> set[tuple[str, str]]:
    step = TIMEFRAME_SECONDS[timeframe]
    result = set()
    for first, second in zip(rows, rows[1:]):
        a, b = datetime.fromisoformat(first["open_time_broker"]), datetime.fromisoformat(second["open_time_broker"])
        if int((b - a).total_seconds()) > step:
            result.add((a.isoformat(), b.isoformat()))
    return result


def prior_gaps() -> dict[str, set[tuple[str, str]]]:
    result = {name: set() for name in TIMEFRAME_SECONDS}
    with PRIOR_GAPS_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["present_in_run1"] == row["present_in_run2"] == "true":
                result[row["timeframe"]].add((row["prior_bar_time"], row["next_bar_time"]))
    return result


def prove_gap_closures(
    prior: dict[str, set[tuple[str, str]]],
    current: dict[str, set[tuple[str, str]]],
    run1_indexes: dict[str, dict[datetime, dict[str, str]]],
    run2_indexes: dict[str, dict[datetime, dict[str, str]]],
) -> list[dict[str, Any]]:
    new_gaps = {timeframe: current[timeframe] - prior[timeframe] for timeframe in TIMEFRAME_SECONDS}
    if any(new_gaps.values()):
        raise ValueError(f"new/unlisted current gap: {new_gaps}")
    closed_rows: list[dict[str, Any]] = []
    for timeframe in TIMEFRAME_SECONDS:
        step = timedelta(seconds=TIMEFRAME_SECONDS[timeframe])
        for first_text, second_text in sorted(prior[timeframe] - current[timeframe]):
            first, second = datetime.fromisoformat(first_text), datetime.fromisoformat(second_text)
            expected: list[datetime] = []
            cursor = first + step
            while cursor < second:
                expected.append(cursor)
                cursor += step
            present1 = [value for value in expected if value in run1_indexes[timeframe]]
            present2 = [value for value in expected if value in run2_indexes[timeframe]]
            identical = all(run1_indexes[timeframe].get(value) == run2_indexes[timeframe].get(value) for value in expected)
            if len(present1) != len(expected) or len(present2) != len(expected) or not identical:
                raise ValueError(f"removed gap lacks constructive contiguous-fill proof: {timeframe}:{first_text}->{second_text}")
            closed_rows.append({
                "timeframe": timeframe, "prior_endpoint": first_text, "next_endpoint": second_text,
                "expected_native_steps": len(expected), "present_native_steps_run1": len(present1),
                "present_native_steps_run2": len(present2), "all_steps_present_run1": "true",
                "all_steps_present_run2": "true", "run1_run2_values_identical": "true", "closure_status": "CLOSED_BY_CONTIGUOUS_NATIVE_BARS",
            })
    return closed_rows


def extract_negative_spreads(
    rows_by_run_timeframe: dict[tuple[str, str], list[dict[str, str]]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for (run, timeframe), rows in rows_by_run_timeframe.items():
        for row in rows:
            spread = int(row["spread"])
            if spread < 0:
                result.append({
                    "run": run, "timeframe": timeframe, "timestamp": row["open_time_broker"],
                    "raw_signed_spread": spread, "unsigned_32_diagnostic": spread & 0xFFFFFFFF,
                    **{name: row[name] for name in ("open", "high", "low", "close", "tick_volume", "real_volume")},
                })
    return result


def cross_timeframe_alignment(
    negative_rows: list[dict[str, Any]],
    indexes: dict[tuple[str, str], dict[datetime, dict[str, str]]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in negative_rows:
        timestamp = datetime.fromisoformat(item["timestamp"])
        matches: dict[str, str] = {}
        for timeframe, seconds in TIMEFRAME_SECONDS.items():
            affected = [
                bar_time.isoformat() for bar_time, row in indexes[(item["run"], timeframe)].items()
                if int(row["spread"]) < 0 and bar_time <= timestamp < bar_time + timedelta(seconds=seconds)
            ]
            matches[timeframe] = ";".join(affected)
        result.append({"run": item["run"], "source_timeframe": item["timeframe"], "timestamp": item["timestamp"], "matching_h1": matches["H1"], "matching_h4": matches["H4"], "matching_d1": matches["D1"]})
    return result


def verify_source_lineage(partial: Path) -> dict[str, Any]:
    copied = partial / "compiled" / B.ORACLE_NAME
    generated, generated_equivalence = B.render_oracle()
    copied_text = copied.read_text(encoding="utf-8")
    if copied_text != generated:
        raise ValueError("copied MQ5 differs from reviewed deterministic builder output")
    B.assert_source_safety(copied_text)
    sidecar_path = partial / "compiled" / "source_equivalence.json"
    sidecar = read_json(sidecar_path)
    if sidecar != generated_equivalence or any(row.get("exact_equal") is not True for row in sidecar.get("blocks", [])):
        raise ValueError("source-equivalence sidecar mismatch")
    required_lines = {
        "rates_declaration": "MqlRates rates[];",
        "copyrates_call": "const int copied=CopyRates(InpTargetSymbol,timeframe,from,until,rates);",
        "filewrite_expression": '(int)rates[i].spread',
    }
    line_map: dict[str, dict[str, Any]] = {}
    lines = copied_text.splitlines()
    for name, token in required_lines.items():
        matches = [index + 1 for index, line in enumerate(lines) if token in line]
        if len(matches) != 1:
            raise ValueError(f"spread lineage token mismatch: {name}")
        line_map[name] = {"line": matches[0], "token": token}
    if re.search(r"(?:abs|max|min)\s*\([^\n]*rates\[i\]\.spread", copied_text, re.IGNORECASE):
        raise ValueError("spread export contains prohibited transformation")
    return {
        "reviewed_builder_source_sha256": sha256_file(Path(B.__file__)),
        "reviewed_mq5_sha256": hashlib.sha256(generated.encode()).hexdigest(),
        "copied_mq5_sha256": sha256_file(copied),
        "source_equivalence_sha256": sha256_file(sidecar_path),
        "source_commit": sidecar.get("source_commit"), "source_blob": sidecar.get("source_blob"),
        "lineage": line_map, "spread_type": "MqlRates.spread:int", "transformation": "int_identity_cast_only",
    }


def verify_zero_action_files(partial: Path) -> None:
    for run in ("run1", "run2"):
        if (partial / "runs" / run / "order.zero").stat().st_size or (partial / "runs" / run / "deal.zero").stat().st_size:
            raise ValueError("official zero-action file mismatch")


def verify_anchors(
    diagnostic_root: Path, authorization_artifact: Path, reviewed_commit: str, reviewed_tree: str,
) -> tuple[Path, Path, dict[str, Any]]:
    if reviewed_commit != REVIEWED_COMMIT or reviewed_tree != REVIEWED_TREE:
        raise ValueError("reviewed generator commit/tree mismatch")
    if not authorization_artifact.is_file() or sha256_file(authorization_artifact) != AUTHORIZATION_SHA256:
        raise ValueError("retry authorization artifact hash mismatch")
    if sha256_file(CONTRACT_PATH) != CONTRACT_SHA256 or sha256_file(RETRY_MANIFEST_PATH) != RETRY_MANIFEST_SHA256:
        raise ValueError("session contract or retry manifest hash mismatch")
    partial, warmup = diagnostic_root / "raw" / "canonical_partial", diagnostic_root / "raw" / "warmup_capture"
    if _actual_files(partial) != PARTIAL_FILES or _actual_files(warmup) != WARMUP_FILES:
        raise ValueError("source packet exact file tree/count mismatch")
    if any((partial / path).exists() for path in ("manifest.json", "manifest.sha256", "test_validation.md", "parity")):
        raise ValueError("partial packet contains forbidden canonical finalization artifact")
    reports = {run: parse_report(partial / "runs" / run / "native_report.htm") for run in ("run1", "run2")}
    if any(report != EXPECTED_REPORT for report in reports.values()) or reports["run1"] != reports["run2"]:
        raise ValueError("official native report anchor mismatch")
    verify_zero_action_files(partial)
    for timeframe, (expected_hash, expected_rows) in EXPECTED_BAR_FILES.items():
        first = partial / "runs" / "run1" / f"native_{timeframe.lower()}_bars.tsv"
        second = partial / "runs" / "run2" / f"native_{timeframe.lower()}_bars.tsv"
        rows1, _ = read_bars(first, timeframe)
        rows2, _ = read_bars(second, timeframe)
        if sha256_file(first) != expected_hash or sha256_file(second) != expected_hash or len(rows1) != expected_rows or len(rows2) != expected_rows or first.read_bytes() != second.read_bytes():
            raise ValueError(f"official {timeframe} anchor/stability mismatch")
    lineage = verify_source_lineage(partial)
    return partial, warmup, {"reports": reports, "source_lineage": lineage}


def analyze(
    diagnostic_root: Path, authorization_artifact: Path, reviewed_commit: str, reviewed_tree: str,
) -> dict[str, Any]:
    partial, warmup, anchors = verify_anchors(diagnostic_root, authorization_artifact, reviewed_commit, reviewed_tree)
    prior = prior_gaps()
    current_rows: dict[str, list[dict[str, str]]] = {}
    current_index: dict[str, dict[datetime, dict[str, str]]] = {}
    current: dict[str, set[tuple[str, str]]] = {}
    for timeframe in TIMEFRAME_SECONDS:
        rows, indexed = read_bars(partial / "runs" / "run1" / f"native_{timeframe.lower()}_bars.tsv", timeframe)
        current_rows[timeframe], current_index[timeframe], current[timeframe] = rows, indexed, gap_set(rows, timeframe)
    run2_index = {timeframe: read_bars(partial / "runs" / "run2" / f"native_{timeframe.lower()}_bars.tsv", timeframe)[1] for timeframe in TIMEFRAME_SECONDS}
    new_gaps = {timeframe: current[timeframe] - prior[timeframe] for timeframe in TIMEFRAME_SECONDS}
    closed_rows = prove_gap_closures(prior, current, current_index, run2_index)
    rows_by_run_tf = {(run, timeframe): read_bars(partial / "runs" / run / f"native_{timeframe.lower()}_bars.tsv", timeframe)[0] for run in ("run1", "run2") for timeframe in TIMEFRAME_SECONDS}
    negative_rows = extract_negative_spreads(rows_by_run_tf)
    if not negative_rows:
        raise ValueError("expected native negative spread rows are absent")
    by_run_tf = {(run, timeframe): read_bars(partial / "runs" / run / f"native_{timeframe.lower()}_bars.tsv", timeframe)[1] for run in ("run1", "run2") for timeframe in TIMEFRAME_SECONDS}
    cross_rows = cross_timeframe_alignment(negative_rows, by_run_tf)
    official_identical = all(
        (partial / "runs" / "run1" / f"native_{timeframe.lower()}_bars.tsv").read_bytes()
        == (partial / "runs" / "run2" / f"native_{timeframe.lower()}_bars.tsv").read_bytes()
        for timeframe in TIMEFRAME_SECONDS
    )
    negative_signature = Counter((item["timeframe"], item["timestamp"], item["raw_signed_spread"]) for item in negative_rows if item["run"] == "run1")
    negative_identical = negative_signature == Counter((item["timeframe"], item["timestamp"], item["raw_signed_spread"]) for item in negative_rows if item["run"] == "run2")
    flags = []
    if official_identical:
        flags.append("OFFICIAL_HISTORY_STABLE_AFTER_WARMUP")
    if closed_rows:
        flags.append("PRIOR_GAP_CLOSED_BY_CONTIGUOUS_NATIVE_BARS")
    if all(current[name] <= prior[name] for name in TIMEFRAME_SECONDS):
        flags.append("CURRENT_GAP_SET_IS_SUBSET_OF_REVIEWED_SUPERSET")
    if negative_rows:
        flags.append("NEGATIVE_MQLRATES_SPREAD_CONFIRMED")
    if negative_identical:
        flags.append("NEGATIVE_SPREAD_IDENTICAL_ACROSS_OFFICIAL_RUNS")
    if anchors["source_lineage"]["transformation"] == "int_identity_cast_only":
        flags.append("SPREAD_EXPORT_PATH_HAS_NO_TRANSFORMATION")
    flags.extend(("SPREAD_UPSTREAM_ORIGIN_UNRESOLVED", "CANONICAL_NP1C_RESULT_NOT_AUTHORIZED", "MT5_RERUN_NOT_AUTHORIZED"))
    return {
        "status": "NP1_F1_DIAGNOSTIC_COMPLETE", "reviewed_generator_commit": reviewed_commit,
        "reviewed_generator_tree": reviewed_tree, "authorization_sha256": AUTHORIZATION_SHA256,
        "contract_sha256": CONTRACT_SHA256, "retry_manifest_sha256": RETRY_MANIFEST_SHA256,
        "flags": flags, "reports": anchors["reports"], "source_lineage": anchors["source_lineage"],
        "official_history_fingerprints": {timeframe: {"sha256": EXPECTED_BAR_FILES[timeframe][0], "row_count": EXPECTED_BAR_FILES[timeframe][1]} for timeframe in TIMEFRAME_SECONDS},
        "gap_counts": {timeframe: {"prior": len(prior[timeframe]), "current": len(current[timeframe]), "closed": len(prior[timeframe] - current[timeframe]), "new": len(new_gaps[timeframe])} for timeframe in TIMEFRAME_SECONDS},
        "negative_spread_counts": dict(Counter(item["timeframe"] for item in negative_rows if item["run"] == "run1")),
        "_tables": {"closed": closed_rows, "negative": negative_rows, "cross": cross_rows, "current": current},
        "_raw_inventory": {"canonical_partial": _inventory(partial), "warmup_capture": _inventory(warmup)},
    }


def _outer_manifest(root: Path) -> dict[str, Any]:
    artifacts = [item for item in _inventory(root) if item["relative_path"] not in {"manifest.json", "manifest.sha256"}]
    return {"schema_version": "a1_xau_r6_np1_retry_stop_diagnostic_manifest_v1", "artifacts": artifacts}


def verify_manifest(root: Path) -> None:
    manifest = read_json(root / "manifest.json")
    sidecar = (root / "manifest.sha256").read_text(encoding="ascii").strip()
    if sidecar != sha256_file(root / "manifest.json"):
        raise ValueError("outer manifest sidecar mismatch")
    listed = {item["relative_path"] for item in manifest.get("artifacts", [])}
    actual = _actual_files(root) - {"manifest.json", "manifest.sha256"}
    if listed != actual:
        raise ValueError("outer manifest tree mismatch")
    for item in manifest["artifacts"]:
        path = root / item["relative_path"]
        if path.stat().st_size != item["size_bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"outer manifest artifact mismatch: {item['relative_path']}")


def build_diagnostic(diagnostic_root: Path, authorization_artifact: Path, reviewed_commit: str, reviewed_tree: str) -> dict[str, Any]:
    before = {item["relative_path"]: item["sha256"] for item in _inventory(diagnostic_root / "raw")}
    result = analyze(diagnostic_root, authorization_artifact, reviewed_commit, reviewed_tree)
    tables, raw_inventory = result.pop("_tables"), result.pop("_raw_inventory")
    analysis = diagnostic_root / "analysis"
    write_json(analysis / "source_packet_inventory.json", raw_inventory)
    write_json(analysis / "native_report_comparison.json", result["reports"])
    write_json(analysis / "official_history_fingerprints.json", result["official_history_fingerprints"])
    write_json(analysis / "prior_vs_current_gap_set.json", {"counts": result["gap_counts"], "policy": "CURRENT_GAP_SET_SUBSET_WITH_CONSTRUCTIVE_CLOSURE"})
    write_csv(analysis / "closed_whitelisted_gaps.csv", ("timeframe", "prior_endpoint", "next_endpoint", "expected_native_steps", "present_native_steps_run1", "present_native_steps_run2", "all_steps_present_run1", "all_steps_present_run2", "run1_run2_values_identical", "closure_status"), tables["closed"])
    current_rows = ({"timeframe": timeframe, "prior_bar_time": first, "next_bar_time": second} for timeframe in TIMEFRAME_SECONDS for first, second in sorted(tables["current"][timeframe]))
    write_csv(analysis / "current_gap_inventory.csv", ("timeframe", "prior_bar_time", "next_bar_time"), current_rows)
    negative_columns = ("run", "timeframe", "timestamp", "raw_signed_spread", "unsigned_32_diagnostic", "open", "high", "low", "close", "tick_volume", "real_volume")
    write_csv(analysis / "negative_spread_rows.csv", negative_columns, tables["negative"])
    write_csv(analysis / "negative_spread_cross_timeframe.csv", ("run", "source_timeframe", "timestamp", "matching_h1", "matching_h4", "matching_d1"), tables["cross"])
    write_json(analysis / "spread_export_lineage.json", result["source_lineage"])
    unsigned = sorted({(item["raw_signed_spread"], item["unsigned_32_diagnostic"]) for item in tables["negative"]})
    write_csv(analysis / "spread_signed_unsigned_diagnostic.csv", ("raw_signed_spread", "unsigned_32_diagnostic", "interpretation"), ({"raw_signed_spread": signed, "unsigned_32_diagnostic": unsigned_value, "interpretation": "DIAGNOSTIC_ONLY_RAW_VALUE_UNCHANGED"} for signed, unsigned_value in unsigned))
    write_json(analysis / "stop_classification.json", {"status": result["status"], "flags": result["flags"], "canonical_np1c_result_authorized": False, "mt5_rerun_authorized": False})
    write_json(diagnostic_root / "result.json", result)
    (diagnostic_root / "README.md").write_text(
        "# A1 XAU NP1 Guarded-Retry Stop Diagnostic\n\n"
        "This packet preserves the unfinalized retry and warm-up captures byte-for-byte. It is diagnostic-only.\n\n"
        f"- Status: `{result['status']}`\n- Flags: `{', '.join(result['flags'])}`\n"
        "- Canonical NP1-C result: `NOT AUTHORIZED`\n- MT5 rerun: `NOT AUTHORIZED / NOT PERFORMED`\n",
        encoding="utf-8", newline="\n",
    )
    after = {item["relative_path"]: item["sha256"] for item in _inventory(diagnostic_root / "raw")}
    if before != after:
        raise RuntimeError("raw packet mutated during analysis")
    write_json(diagnostic_root / "manifest.json", _outer_manifest(diagnostic_root))
    (diagnostic_root / "manifest.sha256").write_text(sha256_file(diagnostic_root / "manifest.json") + "\n", encoding="ascii", newline="\n")
    verify_manifest(diagnostic_root)
    return result


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostic_root", type=Path)
    parser.add_argument("--authorization-artifact", type=Path, required=True)
    parser.add_argument("--reviewed-generator-commit", required=True)
    parser.add_argument("--reviewed-generator-tree", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_manifest(args.diagnostic_root)
        analyze(args.diagnostic_root, args.authorization_artifact, args.reviewed_generator_commit, args.reviewed_generator_tree)
        return 0
    try:
        result = build_diagnostic(args.diagnostic_root, args.authorization_artifact, args.reviewed_generator_commit, args.reviewed_generator_tree)
    except (FileNotFoundError, KeyError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "NP1_F1_SOURCE_PACKET_INVALID", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"status": result["status"], "flags": result["flags"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
