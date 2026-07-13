from __future__ import annotations

import dataclasses
import functools
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

import pytest


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
SCRIPTS = PHASE1_ROOT / "scripts"
SCRIPT = SCRIPTS / "build_a1_xau_router_entry_hold_schedule.py"
BASELINE_RELATIVE = Path(
    "xau-usd/xauusd-phase1/outputs/reports/"
    "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_"
    "current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)


def _load_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("a1_router_entry_hold_schedule", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


S = _load_module()


def _exact_inputs() -> tuple[Path, Path, Path] | None:
    baseline_candidates = [
        REPO_ROOT / BASELINE_RELATIVE,
        REPO_ROOT.parent / "algo-trading-system" / BASELINE_RELATIVE,
    ]
    baseline = next(
        (
            path
            for path in baseline_candidates
            if path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == S.BASELINE_EXPECTED_SHA256
        ),
        None,
    )
    config_root = Path("C:/MT5A1M5MomentumBacktest/Config")
    if baseline is None or not config_root.is_dir():
        return None
    raw_root = baseline.parents[2]
    return baseline, raw_root, config_root


@functools.lru_cache(maxsize=1)
def _exact_package():
    inputs = _exact_inputs()
    if inputs is None:
        pytest.skip("byte-exact ignored raw evidence is staged by Commit 3")
    baseline, raw_root, config_root = inputs
    return S.build_schedule_package(
        baseline_csv=baseline,
        raw_root=raw_root,
        config_root=config_root,
    )


def test_exact_schedule_joins_all_678_entries_without_outcome_fields():
    result = _exact_package()
    assert len(result.schedule_rows) == 678
    assert len({row["trade_id"] for row in result.schedule_rows}) == 678
    assert tuple(result.schedule_rows[0]) == S.SCHEDULE_FIELDNAMES
    assert set(S.SCHEDULE_FIELDNAMES).isdisjoint(S.FORBIDDEN_SCHEDULE_FIELDS)
    assert S.SEALED_OUTCOME_FIELDNAMES == ("trade_id", "native_final_pnl_usd")
    assert result.manifest["join_checks"]["all_native_entries_joined"] is True
    assert result.manifest["join_checks"]["all_orders_joined_to_would_signal"] is True
    assert result.manifest["outcome_seal"]["schedule_built_and_locked_before_outcome_read"] is True
    assert result.manifest["native_reconciliation"]["fee_evidence_complete_for_all_rows"] is False
    assert len(result.manifest["frozen_artifacts"]) == 28
    source_components = {
        "h4_d1_long_best_box2_atr80": "R1",
        "r1_h1_pullback_long_v1": "R1",
        "r2_continuation_short_v1": "R2",
        "r2_pullback_rejection_short_v1": "R2",
    }
    assert all(
        row["component"] == source_components[row["source_id"]]
        for row in result.schedule_rows
    )
    assert all(
        re.fullmatch(r"\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}", row["signal_time_broker"])
        for row in result.schedule_rows
    )
    entry_times = [row["entry_time_broker"] for row in result.schedule_rows]
    assert entry_times == sorted(entry_times)
    assert len(entry_times) == len(set(entry_times))
    assert all(row["signal_time_broker"] <= row["entry_time_broker"] for row in result.schedule_rows)


def test_replacing_every_native_pnl_leaves_schedule_bytes_unchanged():
    result = _exact_package()
    replaced_rows = tuple({**row, "native_pnl_usd": "987654.32"} for row in result.reconciliation.rows)
    replaced_reconciliation = dataclasses.replace(result.reconciliation, rows=replaced_rows)
    schedule_rows, _summary = S.build_outcome_free_schedule(
        replaced_reconciliation,
        result.source_artifacts,
    )
    schedule_bytes = S._csv_bytes(S.SCHEDULE_FIELDNAMES, schedule_rows)
    assert schedule_bytes == result.schedule_bytes
    assert hashlib.sha256(schedule_bytes).hexdigest() == result.schedule_sha256


def test_byte_exact_copy_refuses_existing_mutated_evidence(tmp_path: Path):
    source = tmp_path / "source.bin"
    destination = tmp_path / "evidence" / "copy.bin"
    source.write_bytes(b"frozen evidence\r\n")
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    copied = S._copy_immutable(source, destination, expected_sha256=expected)
    assert copied["sha256"] == expected
    assert destination.read_bytes() == source.read_bytes()

    destination.write_bytes(b"mutated")
    with pytest.raises(S.ScheduleEvidenceError, match="different bytes") as captured:
        S._copy_immutable(source, destination, expected_sha256=expected)
    assert captured.value.status == "ROUTER_PATH_INVALID_EVIDENCE"


def test_lf_normalized_baseline_is_not_accepted_as_frozen_evidence():
    local_baseline = REPO_ROOT / BASELINE_RELATIVE
    if not local_baseline.is_file():
        pytest.skip("local normalized checkout is unavailable")
    actual = hashlib.sha256(local_baseline.read_bytes()).hexdigest()
    if actual == S.BASELINE_EXPECTED_SHA256:
        pytest.skip("this checkout retained the byte-exact CRLF artifact")
    with pytest.raises(S.ScheduleEvidenceError, match="SHA256 mismatch"):
        S._verify_hash(
            local_baseline,
            S.BASELINE_EXPECTED_SHA256,
            source_id="__baseline__",
            artifact_type="baseline",
        )
