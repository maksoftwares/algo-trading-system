from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest


PHASE = Path(__file__).resolve().parents[1]
SCRIPTS = PHASE / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


B = _load("build_a1_xau_r6_native_spread_provenance_probe")
R = _load("run_a1_xau_r6_native_spread_provenance_probe")
A = _load("analyze_a1_xau_r6_native_spread_provenance_probe")


def _tsv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def test_deterministic_source_generation_and_committed_source() -> None:
    first, second = B.render_probe(), B.render_probe()
    assert first == second == B.SOURCE.read_text(encoding="utf-8")
    assert B.verify_source(B.SOURCE)["zero_action"] is True
    assert all(token in first for token in ("CopyRates(", "CopySpread(", "iSpread(", "CopyTicksRange("))


def test_source_has_no_broker_action_or_runtime_attach_surface() -> None:
    source = B.SOURCE.read_text(encoding="utf-8")
    B.assert_source_safety(source)
    assert all(token not in source for token in B.FORBIDDEN)
    assert "OnTick() {}" in source
    assert "PositionsTotal()==0" in source and "OrdersTotal()==0" in source


def test_source_preserves_raw_signed_values_without_normalization() -> None:
    source = B.SOURCE.read_text(encoding="utf-8")
    assert "(int)rates[i].spread" in source
    assert "raw=ticks[i].ask-ticks[i].bid" in source
    lowered = source.lower()
    assert all(token not in lowered for token in ("mathabs", "mathmax", "clamp", "forward-fill", "replacement"))


def test_clean_root_empty_history_cache_preflight(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "clean"
    root.mkdir(); (root / R.MARKER).write_bytes(R.MARKER_BYTES)
    (root / "terminal64.exe").write_bytes(b"x"); (root / "MetaEditor64.exe").write_bytes(b"x")
    monkeypatch.setattr(R, "CLEAN_ROOT", root)
    R.validate_clean_root(root, before_first_invocation=True)
    for relative in (Path("Bases"), Path("history"), Path("Tester/cache"), Path("Tester/Agent-1"), Path("MQL5/Files")):
        target = root / relative; target.mkdir(parents=True, exist_ok=True)
        with pytest.raises(RuntimeError, match="history/cache"):
            R.validate_clean_root(root, before_first_invocation=True)
        target.rmdir()


def test_wrong_root_marker_or_terminal_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "clean"; root.mkdir(); monkeypatch.setattr(R, "CLEAN_ROOT", root)
    with pytest.raises(RuntimeError, match="marker"):
        R.validate_clean_root(root, before_first_invocation=True)
    (root / R.MARKER).write_text("wrong\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="marker"):
        R.validate_clean_root(root, before_first_invocation=True)
    (root / R.MARKER).write_bytes(R.MARKER_BYTES)
    with pytest.raises(RuntimeError, match="binaries"):
        R.validate_clean_root(root, before_first_invocation=True)


def test_frozen_environment_and_exact_three_run_budget() -> None:
    assert R.RUN_IDS == ("warmup", "probe1", "probe2")
    assert len(R.RUN_IDS) == 3
    for run_id in R.RUN_IDS:
        text = R.render_ini(run_id)
        assert "Symbol=XAUUSD" in text and "Period=M5" in text and "Model=4" in text
        assert "FromDate=2015.06.01" in text and "ToDate=2026.07.01" in text
        assert "Deposit=10000" in text and "Currency=USD" in text and "Leverage=50" in text
        assert "UseRemote=0" in text and "UseCloud=0" in text and f"InpRunId={run_id}" in text
    with pytest.raises(ValueError):
        R.render_ini("probe3")


def test_source_lock_binds_every_g1a_implementation_file() -> None:
    payload = R.verify_lock()
    assert payload["reviewed_diagnostic_commit"] == R.REVIEWED_COMMIT
    assert payload["reviewed_diagnostic_tree"] == R.REVIEWED_TREE
    assert payload["invocation_budget"]["strategy_tester_order"] == list(R.RUN_IDS)


def test_wrong_metaeditor_version_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "root"; root.mkdir()
    editor = root / "MetaEditor64.exe"; editor.write_bytes(b"x")
    def fake(command, cwd, timeout):
        source = root / "MQL5" / "Experts" / B.PROBE_NAME
        source.with_suffix(".ex5").write_bytes(b"ex5")
        (root / "compile.log").write_text("0 errors, 0 warnings", encoding="utf-8")
        return type("Done", (), {"returncode": 1, "stdout": b"", "stderr": b""})()
    with pytest.raises(RuntimeError, match="version mismatch"):
        R.compile_once(root, editor, runner=fake, version_reader=lambda path: "wrong")


def test_compile_requires_ex5_and_zero_error_log(tmp_path: Path) -> None:
    root = tmp_path / "root"; root.mkdir(); editor = root / "MetaEditor64.exe"; editor.write_bytes(b"x")
    done = type("Done", (), {"returncode": 1, "stdout": b"", "stderr": b""})()
    with pytest.raises(RuntimeError, match="compilation failed"):
        R.compile_once(root, editor, runner=lambda *args: done, version_reader=lambda path: R.EXPECTED_VERSION)


@pytest.mark.parametrize(("reproduced", "ticks_ok", "interfaces_ok", "expected"), [
    (False, True, True, "PRIOR_ROOT_CACHE_SPECIFIC_SUPPORTED"),
    (True, True, True, "BAR_SERIES_METADATA_LAYER_INVALID_SUPPORTED"),
    (True, False, True, "RAW_TICK_HISTORY_LAYER_INVALID_SUPPORTED"),
    (False, True, False, "UPSTREAM_ORIGIN_UNRESOLVED"),
])
def test_classification_precedence(reproduced: bool, ticks_ok: bool, interfaces_ok: bool, expected: str) -> None:
    flags, classification = A.classify(reproduced=reproduced, all_ticks_nonnegative=ticks_ok, interfaces_consistent=interfaces_ok)
    assert classification == expected and flags[-1] == expected


def test_interface_consistency_and_divergence() -> None:
    base = {"timeframe": "H1", "open_time_broker": "2025-06-18T03:00:00", "copyrates_spread": "-7", "copyspread_spread": "-7", "ispread_spread": "-7"}
    rows, consistent = A.interface_analysis([base])
    assert consistent and rows[0]["copyrates_spread"] == -7
    divergent = {**base, "ispread_spread": "8"}
    rows, consistent = A.interface_analysis([divergent])
    assert not consistent and rows[0]["interfaces_equal"] == "false"


def test_raw_tick_negative_detection_and_positive_spreads(tmp_path: Path) -> None:
    run = tmp_path / "run"
    columns = ["schema_version", "broker_day", "time_msc", "time", "bid", "ask", "last", "volume", "volume_real", "flags", "raw_ask_minus_bid", "raw_spread_points", "negative_spread_boolean", "quote_sides_positive", "copyticks_return", "copyticks_error"]
    for index, name in enumerate(A.TICK_FILES):
        negative = index == 0
        row = {"schema_version": "v1", "broker_day": "d", "time_msc": "1", "time": "t", "bid": "10", "ask": "9" if negative else "11", "last": "0", "volume": "1", "volume_real": "1", "flags": "1", "raw_ask_minus_bid": "-1" if negative else "1", "raw_spread_points": "-1" if negative else "1", "negative_spread_boolean": str(negative).lower(), "quote_sides_positive": "true", "copyticks_return": "1", "copyticks_error": "0"}
        _tsv(run / name, columns, [row])
    summaries, negatives, all_ok = A.tick_analysis(run)
    assert not all_ok and len(negatives) == 1 and summaries[0]["negative_ask_bid_rows"] == 1


def test_missing_zero_quote_sides_preserved_and_counted(tmp_path: Path) -> None:
    run = tmp_path / "run"
    columns = ["schema_version", "broker_day", "time_msc", "time", "bid", "ask", "last", "volume", "volume_real", "flags", "raw_ask_minus_bid", "raw_spread_points", "negative_spread_boolean", "quote_sides_positive", "copyticks_return", "copyticks_error"]
    row = {"schema_version": "v1", "broker_day": "d", "time_msc": "1", "time": "t", "bid": "0", "ask": "10", "last": "0", "volume": "1", "volume_real": "1", "flags": "1", "raw_ask_minus_bid": "", "raw_spread_points": "", "negative_spread_boolean": "", "quote_sides_positive": "false", "copyticks_return": "1", "copyticks_error": "0"}
    for name in A.TICK_FILES: _tsv(run / name, columns, [row])
    summaries, negatives, all_ok = A.tick_analysis(run)
    assert all_ok and not negatives and all(item["row_count"] == item["missing_or_zero_quote_sides"] == 1 for item in summaries)


def test_tick_flag_value_mismatch_fails(tmp_path: Path) -> None:
    run = tmp_path / "run"
    columns = ["schema_version", "broker_day", "time_msc", "time", "bid", "ask", "last", "volume", "volume_real", "flags", "raw_ask_minus_bid", "raw_spread_points", "negative_spread_boolean", "quote_sides_positive", "copyticks_return", "copyticks_error"]
    row = {"schema_version": "v1", "broker_day": "d", "time_msc": "1", "time": "t", "bid": "10", "ask": "11", "last": "0", "volume": "1", "volume_real": "1", "flags": "1", "raw_ask_minus_bid": "1", "raw_spread_points": "1", "negative_spread_boolean": "true", "quote_sides_positive": "true", "copyticks_return": "1", "copyticks_error": "0"}
    for name in A.TICK_FILES: _tsv(run / name, columns, [row])
    with pytest.raises(ValueError, match="flag/value"):
        A.tick_analysis(run)


def test_prior_negative_reproduced_and_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior = tmp_path / "prior.csv"
    prior.write_text("run,timeframe,timestamp,raw_signed_spread\nrun1,H1,2025-06-18T03:00:00,-7\nrun2,H1,2025-06-18T03:00:00,-7\n", encoding="utf-8")
    monkeypatch.setattr(A, "PRIOR_NEGATIVE", prior)
    rows = [{"timeframe": "H1", "timestamp": "2025-06-18T03:00:00", "copyrates_spread": -7}]
    comparison, reproduced = A.prior_comparison(rows)
    assert reproduced and comparison[0]["exact_value_reproduced"] == "true"
    rows[0]["copyrates_spread"] = 5
    comparison, reproduced = A.prior_comparison(rows)
    assert not reproduced and comparison[0]["clean_negative"] == "false"


def test_missing_reviewed_bar_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior = tmp_path / "prior.csv"
    prior.write_text("run,timeframe,timestamp,raw_signed_spread\nrun1,H1,2025-06-18T03:00:00,-7\n", encoding="utf-8")
    monkeypatch.setattr(A, "PRIOR_NEGATIVE", prior)
    with pytest.raises(ValueError, match="missing"):
        A.prior_comparison([])


def test_manifest_nonrecursive_tamper_detection(tmp_path: Path) -> None:
    root = tmp_path / "packet"; root.mkdir(); (root / "a.txt").write_text("a", encoding="utf-8")
    A.write_json(root / "manifest.json", {"artifacts": A.inventory(root)})
    (root / "manifest.sha256").write_text(A.sha256_file(root / "manifest.json") + "\n", encoding="ascii")
    A.verify_manifest(root)
    (root / "a.txt").write_text("b", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact mismatch"):
        A.verify_manifest(root)


def test_static_no_result_research_or_canonical_status_surface() -> None:
    sources = "\n".join((SCRIPTS / name).read_text(encoding="utf-8") for name in (
        "build_a1_xau_r6_native_spread_provenance_probe.py",
        "run_a1_xau_r6_native_spread_provenance_probe.py",
        "analyze_a1_xau_r6_native_spread_provenance_probe.py",
    ))
    lowered = sources.lower()
    assert all(token not in lowered for token in ("net_profit", "profit_factor", "mfe", "mae"))
    assert "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS" not in sources
    assert "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL" not in sources
    assert '"status": "NP1_G1_DIAGNOSTIC_COMPLETE"' in sources
