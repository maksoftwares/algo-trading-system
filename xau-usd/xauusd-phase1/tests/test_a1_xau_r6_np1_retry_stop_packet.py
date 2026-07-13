from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest


PHASE = Path(__file__).resolve().parents[1]
SCRIPT = PHASE / "scripts" / "analyze_a1_xau_r6_np1_retry_stop_packet.py"
sys.path.insert(0, str(PHASE / "scripts"))
SPEC = importlib.util.spec_from_file_location("a1_xau_r6_np1f1", SCRIPT)
assert SPEC and SPEC.loader
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
PACKET = PHASE / "outputs" / "reports" / "A1_XAU_R6_NP1_RETRY_STOP_DIAGNOSTIC_20260712"


def _auth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "authorization.md"
    path.write_text("test authorization artifact\n", encoding="utf-8")
    monkeypatch.setattr(A, "AUTHORIZATION_SHA256", A.sha256_file(path))
    return path


def _empty_gaps() -> dict[str, set[tuple[str, str]]]:
    return {name: set() for name in A.TIMEFRAME_SECONDS}


def _empty_indexes() -> dict[str, dict[datetime, dict[str, str]]]:
    return {name: {} for name in A.TIMEFRAME_SECONDS}


def _row(timeframe: str, timestamp: str, spread: str) -> dict[str, str]:
    return {
        "schema_version": "v1", "timeframe": timeframe, "open_time_broker": timestamp,
        "open": "1", "high": "2", "low": "0", "close": "1.5",
        "tick_volume": "10", "spread": spread, "real_volume": "20",
    }


def test_production_packet_exact_anchors_and_expected_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    auth = _auth(tmp_path, monkeypatch)
    result = A.analyze(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)
    assert result["status"] == "NP1_F1_DIAGNOSTIC_COMPLETE"
    assert result["negative_spread_counts"] == {"H1": 31, "H4": 12, "D1": 4}
    assert result["flags"] == [
        "OFFICIAL_HISTORY_STABLE_AFTER_WARMUP", "PRIOR_GAP_CLOSED_BY_CONTIGUOUS_NATIVE_BARS",
        "CURRENT_GAP_SET_IS_SUBSET_OF_REVIEWED_SUPERSET", "NEGATIVE_MQLRATES_SPREAD_CONFIRMED",
        "NEGATIVE_SPREAD_IDENTICAL_ACROSS_OFFICIAL_RUNS", "SPREAD_EXPORT_PATH_HAS_NO_TRANSFORMATION",
        "SPREAD_UPSTREAM_ORIGIN_UNRESOLVED", "CANONICAL_NP1C_RESULT_NOT_AUTHORIZED", "MT5_RERUN_NOT_AUTHORIZED",
    ]


@pytest.mark.parametrize(("commit", "tree"), [("0" * 40, A.REVIEWED_TREE), (A.REVIEWED_COMMIT, "0" * 40)])
def test_wrong_reviewed_commit_or_tree_fails(commit: str, tree: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    auth = _auth(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="commit/tree"):
        A.verify_anchors(PACKET, auth, commit, tree)


@pytest.mark.parametrize("target", ["authorization", "contract", "manifest"])
def test_wrong_authorization_contract_or_manifest_hash_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, target: str) -> None:
    auth = _auth(tmp_path, monkeypatch)
    original = A.sha256_file

    def wrong(path: Path) -> str:
        if (target == "authorization" and path == auth) or (target == "contract" and path == A.CONTRACT_PATH) or (target == "manifest" and path == A.RETRY_MANIFEST_PATH):
            return "0" * 64
        return original(path)

    monkeypatch.setattr(A, "sha256_file", wrong)
    with pytest.raises(ValueError, match="authorization|contract|manifest"):
        A.verify_anchors(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)


@pytest.mark.parametrize("mutation", ["missing", "extra", "canonical_result", "parity", "manifest_pair"])
def test_partial_tree_is_exact_and_unfinalized(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str) -> None:
    auth = _auth(tmp_path, monkeypatch)
    original = A._actual_files

    def altered(root: Path) -> set[str]:
        files = original(root)
        if root.name != "canonical_partial":
            return files
        if mutation == "missing":
            files.remove(next(iter(files)))
        elif mutation == "extra":
            files.add("extra.bin")
        elif mutation == "canonical_result":
            files.add("result.json")
        elif mutation == "parity":
            files.add("parity/final.json")
        else:
            files.add("manifest.json")
        return files

    monkeypatch.setattr(A, "_actual_files", altered)
    with pytest.raises(ValueError, match="file tree/count"):
        A.verify_anchors(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)


def test_report_bar_hash_row_count_zero_action_and_source_equivalence_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    auth = _auth(tmp_path, monkeypatch)
    original_report = A.parse_report
    monkeypatch.setattr(A, "parse_report", lambda path: {**original_report(path), "ticks": 1})
    with pytest.raises(ValueError, match="report anchor"):
        A.verify_anchors(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)
    monkeypatch.undo()
    auth = _auth(tmp_path, monkeypatch)
    original_hash = A.sha256_file
    monkeypatch.setattr(A, "sha256_file", lambda path: "0" * 64 if path.name == "native_h1_bars.tsv" else original_hash(path))
    with pytest.raises(ValueError, match="H1 anchor"):
        A.verify_anchors(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)
    monkeypatch.undo()
    auth = _auth(tmp_path, monkeypatch)
    original_bars = A.read_bars
    monkeypatch.setattr(A, "read_bars", lambda path, timeframe: (original_bars(path, timeframe)[0][:-1], original_bars(path, timeframe)[1]) if timeframe == "H1" else original_bars(path, timeframe))
    with pytest.raises(ValueError, match="H1 anchor"):
        A.verify_anchors(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)
    monkeypatch.undo()
    auth = _auth(tmp_path, monkeypatch)
    monkeypatch.setattr(A, "verify_source_lineage", lambda partial: (_ for _ in ()).throw(ValueError("source-equivalence failure")))
    with pytest.raises(ValueError, match="source-equivalence"):
        A.verify_anchors(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)


def test_nonzero_order_or_deal_fails(tmp_path: Path) -> None:
    partial = tmp_path / "partial"
    for run in ("run1", "run2"):
        path = partial / "runs" / run
        path.mkdir(parents=True)
        (path / "order.zero").write_bytes(b"")
        (path / "deal.zero").write_bytes(b"")
    A.verify_zero_action_files(partial)
    (partial / "runs" / "run2" / "deal.zero").write_text("1", encoding="ascii")
    with pytest.raises(ValueError, match="zero-action"):
        A.verify_zero_action_files(partial)


def test_complete_gap_closure_and_failure_modes() -> None:
    prior, current = _empty_gaps(), _empty_gaps()
    gap = ("2025-07-03T00:00:00", "2025-07-03T03:00:00")
    prior["H1"].add(gap)
    one, two = _empty_indexes(), _empty_indexes()
    for hour in (1, 2):
        stamp = datetime.fromisoformat(f"2025-07-03T0{hour}:00:00")
        one["H1"][stamp] = two["H1"][stamp] = _row("H1", stamp.isoformat(), "3")
    assert A.prove_gap_closures(prior, current, one, two)[0]["closure_status"] == "CLOSED_BY_CONTIGUOUS_NATIVE_BARS"
    del two["H1"][datetime.fromisoformat("2025-07-03T02:00:00")]
    with pytest.raises(ValueError, match="constructive contiguous-fill"):
        A.prove_gap_closures(prior, current, one, two)
    two["H1"] = dict(one["H1"])
    two["H1"][datetime.fromisoformat("2025-07-03T01:00:00")] = _row("H1", "2025-07-03T01:00:00", "4")
    with pytest.raises(ValueError, match="constructive contiguous-fill"):
        A.prove_gap_closures(prior, current, one, two)


@pytest.mark.parametrize("gap", [
    ("2025-07-03T00:00:00", "2025-07-03T02:00:00"),
    ("2026-01-01T00:00:00", "2026-01-01T03:00:00"),
])
def test_smaller_replacement_or_new_gap_fails(gap: tuple[str, str]) -> None:
    prior, current = _empty_gaps(), _empty_gaps()
    prior["H1"].add(("2025-07-03T00:00:00", "2025-07-03T03:00:00"))
    current["H1"].add(gap)
    with pytest.raises(ValueError, match="new/unlisted"):
        A.prove_gap_closures(prior, current, _empty_indexes(), _empty_indexes())


def test_negative_extraction_preserves_signed_value_and_positive_rows() -> None:
    rows = {("run1", "H1"): [_row("H1", "2025-01-01T00:00:00", "-7"), _row("H1", "2025-01-01T01:00:00", "5")]}
    negative = A.extract_negative_spreads(rows)
    assert len(negative) == 1
    assert negative[0]["raw_signed_spread"] == -7
    assert negative[0]["unsigned_32_diagnostic"] == 4294967289
    assert rows[("run1", "H1")][0]["spread"] == "-7"
    assert rows[("run1", "H1")][1]["spread"] == "5"


def test_cross_timeframe_alignment() -> None:
    negative = A.extract_negative_spreads({("run1", "H1"): [_row("H1", "2025-01-01T02:00:00", "-7")]})
    indexes = {}
    for timeframe, stamp in (("H1", "2025-01-01T02:00:00"), ("H4", "2025-01-01T00:00:00"), ("D1", "2025-01-01T00:00:00")):
        when = datetime.fromisoformat(stamp)
        indexes[("run1", timeframe)] = {when: _row(timeframe, stamp, "-7")}
    aligned = A.cross_timeframe_alignment(negative, indexes)[0]
    assert aligned["matching_h1"] == "2025-01-01T02:00:00"
    assert aligned["matching_h4"] == aligned["matching_d1"] == "2025-01-01T00:00:00"


def test_identity_cast_lineage_and_wrapper_drift_rejection(tmp_path: Path) -> None:
    lineage = A.verify_source_lineage(PACKET / "raw" / "canonical_partial")
    assert lineage["spread_type"] == "MqlRates.spread:int"
    assert lineage["transformation"] == "int_identity_cast_only"
    copied = tmp_path / "partial"
    shutil.copytree(PACKET / "raw" / "canonical_partial" / "compiled", copied / "compiled")
    mq5 = copied / "compiled" / A.B.ORACLE_NAME
    mq5.write_text(mq5.read_text(encoding="utf-8").replace("(int)rates[i].spread", "MathAbs((int)rates[i].spread)"), encoding="utf-8")
    with pytest.raises(ValueError, match="reviewed deterministic builder"):
        A.verify_source_lineage(copied)


def test_raw_no_mutation_deterministic_outputs_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    auth = _auth(tmp_path, monkeypatch)
    before = {p.relative_to(PACKET / "raw").as_posix(): A.sha256_file(p) for p in (PACKET / "raw").rglob("*") if p.is_file()}
    A.verify_manifest(PACKET)
    after = {p.relative_to(PACKET / "raw").as_posix(): A.sha256_file(p) for p in (PACKET / "raw").rglob("*") if p.is_file()}
    assert before == after
    first = json.loads((PACKET / "result.json").read_text(encoding="utf-8"))
    second = A.analyze(PACKET, auth, A.REVIEWED_COMMIT, A.REVIEWED_TREE)
    second.pop("_tables")
    second.pop("_raw_inventory")
    first["authorization_sha256"] = A.AUTHORIZATION_SHA256
    assert first == second
    copy = tmp_path / "manifest-copy"
    shutil.copytree(PACKET, copy)
    (copy / "analysis" / "stop_classification.json").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact mismatch"):
        A.verify_manifest(copy)


def test_static_boundary_no_runtime_profitability_or_canonical_parity_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert all(token not in source for token in ("subprocess", "MetaTrader5", "terminal64", "OrderSend"))
    assert all(token not in source.lower() for token in ("net_profit", "profit_factor", "mfe", "mae", "census"))
    assert "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS" not in source
    assert "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL" not in source
