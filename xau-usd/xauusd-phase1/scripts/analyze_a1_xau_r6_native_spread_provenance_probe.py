"""Analyze and cryptographically close NP1-G1 clean-root provenance evidence."""

from __future__ import annotations

import csv
import argparse
import hashlib
import html
import json
import math
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
PRIOR_RESULT = ROOT / "outputs" / "reports" / "A1_XAU_R6_NP1_RETRY_STOP_DIAGNOSTIC_20260712"
PRIOR_NEGATIVE = PRIOR_RESULT / "analysis" / "negative_spread_rows.csv"
PRIOR_FINGERPRINTS = PRIOR_RESULT / "analysis" / "official_history_fingerprints.json"
TIMEFRAMES = ("H1", "H4", "D1")
TICK_FILES = ("ticks_20250618.tsv", "ticks_20250929.tsv", "ticks_20251117.tsv", "ticks_20260414.tsv")
OFFICIAL_FILES = ("native_report.htm", "h1_bars.tsv", "h4_bars.tsv", "d1_bars.tsv", "bar_spread_interfaces.tsv", *TICK_FILES, "assertions.tsv", "order.zero", "deal.zero")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class Cells(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[str] = []
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "td": self.depth, self.parts = 1, []
        elif self.depth: self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self.depth: return
        self.depth -= 1
        if tag.lower() == "td" and self.depth == 0: self.cells.append(" ".join("".join(self.parts).split()))

    def handle_data(self, data: str) -> None:
        if self.depth: self.parts.append(data)


def parse_report(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.decode("utf-8-sig")
    parser = Cells(); parser.feed(text)
    fields = {cell[:-1]: parser.cells[i + 1] for i, cell in enumerate(parser.cells[:-1]) if cell.endswith(":")}
    def integer(name: str) -> int:
        found = re.search(r"[0-9][0-9,\s]*", fields[name])
        if not found: raise ValueError(f"invalid report field {name}")
        return int(re.sub(r"[,\s]", "", found.group()))
    return {"period": fields["Period"], "bars": integer("Bars"), "ticks": integer("Ticks"), "trades": integer("Total Trades"), "deals": integer("Total Deals")}


def assert_official_stability(output: Path) -> dict[str, Any]:
    first, second = output / "runs" / "probe1", output / "runs" / "probe2"
    reports = {"probe1": parse_report(first / "native_report.htm"), "probe2": parse_report(second / "native_report.htm")}
    if reports["probe1"] != reports["probe2"] or reports["probe1"]["trades"] or reports["probe1"]["deals"]:
        raise ValueError("official report drift or nonzero action")
    for name in OFFICIAL_FILES[1:]:
        if not (first / name).is_file() or not (second / name).is_file() or (first / name).read_bytes() != (second / name).read_bytes():
            raise ValueError(f"official probe byte drift: {name}")
    for run in (first, second):
        if (run / "order.zero").stat().st_size or (run / "deal.zero").stat().st_size:
            raise ValueError("nonzero action sentinel")
        assertions = read_tsv(run / "assertions.tsv")
        if not assertions or any(row.get("passed") != "true" for row in assertions):
            raise ValueError("official zero-action/environment assertion failure")
    warmup = output / "runs" / "warmup"
    if set(p.name for p in warmup.iterdir() if p.is_file()) != {"tester.ini", "native_report.htm", "assertions.tsv", "order.zero", "deal.zero"}:
        raise ValueError("warm-up exact file tree mismatch")
    if (warmup / "order.zero").stat().st_size or (warmup / "deal.zero").stat().st_size:
        raise ValueError("warm-up nonzero action sentinel")
    return reports


def interface_analysis(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], bool]:
    if not rows: raise ValueError("missing bar-interface rows")
    output, consistent = [], True
    for row in rows:
        raw = int(row["copyrates_spread"])
        copy = int(row["copyspread_spread"])
        isp = int(row["ispread_spread"])
        agree = raw == copy == isp
        consistent &= agree
        output.append({"timeframe": row["timeframe"], "timestamp": row["open_time_broker"], "copyrates_spread": raw, "copyspread_spread": copy, "ispread_spread": isp, "interfaces_equal": str(agree).lower()})
    return output, consistent


def tick_analysis(run: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    summaries, negatives = [], []
    all_nonnegative = True
    for name in TICK_FILES:
        rows = read_tsv(run / name)
        if not rows: raise ValueError(f"missing/empty raw tick window: {name}")
        positive, missing, negative = 0, 0, 0
        for row in rows:
            for field in ("bid", "ask", "last", "volume_real"):
                if row[field] and not math.isfinite(float(row[field])): raise ValueError("nonfinite raw tick field")
            if row["quote_sides_positive"] == "true":
                positive += 1
                raw = float(row["raw_ask_minus_bid"])
                flag = row["negative_spread_boolean"] == "true"
                if flag != (raw < 0): raise ValueError("raw tick negative flag/value mismatch")
                if flag:
                    negative += 1; all_nonnegative = False
                    negatives.append({"tick_file": name, **row})
            else:
                missing += 1
        summaries.append({"tick_file": name, "row_count": len(rows), "positive_quote_sides": positive, "missing_or_zero_quote_sides": missing, "negative_ask_bid_rows": negative, "sha256": sha256_file(run / name)})
    return summaries, negatives, all_nonnegative


def prior_comparison(interface_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    current = {(row["timeframe"], row["timestamp"]): row for row in interface_rows}
    prior_rows = [row for row in csv.DictReader(PRIOR_NEGATIVE.open(encoding="utf-8")) if row["run"] == "run1"]
    output, reproduced = [], False
    for prior in prior_rows:
        key = (prior["timeframe"], prior["timestamp"])
        clean = current.get(key)
        if clean is None: raise ValueError(f"reviewed negative row missing from clean interface capture: {key}")
        prior_value, clean_value = int(prior["raw_signed_spread"]), int(clean["copyrates_spread"])
        same = prior_value == clean_value
        reproduced |= clean_value < 0
        output.append({"timeframe": key[0], "timestamp": key[1], "prior_raw_signed_spread": prior_value, "clean_copyrates_spread": clean_value, "exact_value_reproduced": str(same).lower(), "clean_negative": str(clean_value < 0).lower()})
    return output, reproduced


def classify(*, reproduced: bool, all_ticks_nonnegative: bool, interfaces_consistent: bool) -> tuple[list[str], str]:
    flags = ["CLEAN_ROOT_NEGATIVE_BAR_SPREAD_REPRODUCED" if reproduced else "CLEAN_ROOT_NEGATIVE_BAR_SPREAD_NOT_REPRODUCED"]
    flags.append("RAW_TICK_ASK_BID_ALL_NONNEGATIVE" if all_ticks_nonnegative else "RAW_TICK_NEGATIVE_ASK_BID_PRESENT")
    flags.append("BAR_SPREAD_INTERFACES_CONSISTENT" if interfaces_consistent else "BAR_SPREAD_INTERFACES_DIVERGENT")
    if not all_ticks_nonnegative:
        classification = "RAW_TICK_HISTORY_LAYER_INVALID_SUPPORTED"
    elif reproduced:
        classification = "BAR_SERIES_METADATA_LAYER_INVALID_SUPPORTED"
    elif interfaces_consistent:
        classification = "PRIOR_ROOT_CACHE_SPECIFIC_SUPPORTED"
    else:
        classification = "UPSTREAM_ORIGIN_UNRESOLVED"
    flags.append(classification)
    return flags, classification


def inventory(root: Path) -> list[dict[str, Any]]:
    return [{"relative_path": p.relative_to(root).as_posix(), "sha256": sha256_file(p), "size_bytes": p.stat().st_size} for p in sorted(root.rglob("*")) if p.is_file() and p.name not in {"manifest.json", "manifest.sha256"}]


def verify_manifest(root: Path) -> None:
    payload = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (root / "manifest.sha256").read_text(encoding="ascii").strip() != sha256_file(root / "manifest.json"):
        raise ValueError("manifest sidecar mismatch")
    listed = {row["relative_path"] for row in payload["artifacts"]}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} - {"manifest.json", "manifest.sha256"}
    if listed != actual: raise ValueError("manifest tree mismatch")
    for row in payload["artifacts"]:
        p = root / row["relative_path"]
        if p.stat().st_size != row["size_bytes"] or sha256_file(p) != row["sha256"]: raise ValueError(f"manifest artifact mismatch: {p}")


def build_packet(output: Path) -> dict[str, Any]:
    before = {p.relative_to(output).as_posix(): sha256_file(p) for p in output.rglob("*") if p.is_file()}
    reports = assert_official_stability(output)
    run = output / "runs" / "probe1"
    interface_rows, interfaces_consistent = interface_analysis(read_tsv(run / "bar_spread_interfaces.tsv"))
    tick_summaries, tick_negatives, ticks_nonnegative = tick_analysis(run)
    prior_rows, reproduced = prior_comparison(interface_rows)
    flags, classification = classify(reproduced=reproduced, all_ticks_nonnegative=ticks_nonnegative, interfaces_consistent=interfaces_consistent)
    prior_fp = json.loads(PRIOR_FINGERPRINTS.read_text(encoding="utf-8"))
    clean_fp = {tf: {"sha256": sha256_file(run / f"{tf.lower()}_bars.tsv"), "row_count": len(read_tsv(run / f"{tf.lower()}_bars.tsv")), "prior": prior_fp[tf]} for tf in TIMEFRAMES}
    analysis = output / "analysis"
    write_json(analysis / "prior_vs_clean_bar_fingerprints.json", clean_fp)
    write_csv(analysis / "reviewed_negative_bar_comparison.csv", ("timeframe", "timestamp", "prior_raw_signed_spread", "clean_copyrates_spread", "exact_value_reproduced", "clean_negative"), prior_rows)
    write_csv(analysis / "bar_interface_comparison.csv", ("timeframe", "timestamp", "copyrates_spread", "copyspread_spread", "ispread_spread", "interfaces_equal"), interface_rows)
    write_csv(analysis / "raw_tick_spread_summary.csv", ("tick_file", "row_count", "positive_quote_sides", "missing_or_zero_quote_sides", "negative_ask_bid_rows", "sha256"), tick_summaries)
    negative_columns = tuple(tick_negatives[0]) if tick_negatives else ("tick_file", "schema_version", "broker_day", "time_msc", "time", "bid", "ask", "last", "volume", "volume_real", "flags", "raw_ask_minus_bid", "raw_spread_points", "negative_spread_boolean", "quote_sides_positive", "copyticks_return", "copyticks_error")
    write_csv(analysis / "raw_tick_negative_rows.csv", negative_columns, tick_negatives)
    write_json(analysis / "provenance_classification.json", {"classification": classification, "flags": flags})
    result = {"status": "NP1_G1_DIAGNOSTIC_COMPLETE", "classification": classification, "flags": flags, "reports": reports, "clean_history_fingerprints": clean_fp, "tick_window_summaries": tick_summaries, "canonical_np1c_authorized": False, "census_authorized": False, "broker_action_authorized": False}
    write_json(output / "result.json", result)
    (output / "README.md").write_text(f"# NP1-G1 Clean-Root Native Spread Provenance Probe\n\nStatus: `{result['status']}`\n\nClassification: `{classification}`\n\nDiagnostic only. Canonical NP1-C, census, profitability, deployment, and broker action remain unauthorized.\n", encoding="utf-8", newline="\n")
    (output / "test_validation.md").write_text("# Validation\n\nGenerated only after the locked G1-A focused and full Phase 1 suites passed.\n", encoding="utf-8", newline="\n")
    after_existing = {p.relative_to(output).as_posix(): sha256_file(p) for p in output.rglob("*") if p.is_file() and p.relative_to(output).as_posix() in before}
    if after_existing != before: raise RuntimeError("raw/compiled campaign evidence mutated during analysis")
    write_json(output / "manifest.json", {"schema_version": "a1_xau_r6_np1_g1_evidence_manifest_v1", "artifacts": inventory(output)})
    (output / "manifest.sha256").write_text(sha256_file(output / "manifest.json") + "\n", encoding="ascii", newline="\n")
    verify_manifest(output)
    return result


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_manifest(args.output)
        assert_official_stability(args.output)
        return 0
    result = build_packet(args.output)
    print(json.dumps({"status": result["status"], "flags": result["flags"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
