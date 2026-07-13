from __future__ import annotations

import csv
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
SCRIPT = PHASE1_ROOT / "scripts" / "build_a1_xau_native_position_reconciliation.py"
BASELINE_RELATIVE = Path(
    "xau-usd/xauusd-phase1/outputs/reports/"
    "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_"
    "current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("a1_native_position_reconciliation", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


N = _load_module()


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]], *, delimiter: str = ","):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=delimiter, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _source_pair(
    root: Path,
    name: str,
    *,
    run_id: str,
    direction: str,
    entry_volume: str = "0.01",
    exit_volume: str = "0.01",
) -> Path:
    trades = root / f"{name}_trades.csv"
    deals = root / f"{name}_deals.csv"
    entry_type, exit_type = ("0", "1") if direction == "LONG" else ("1", "0")
    _write_csv(
        trades,
        [
            "entry_time",
            "direction",
            "entry_deal",
            "volume",
            "entry_price",
            "entry_comment",
            "exit_time",
            "exit_deal",
            "exit_price",
            "profit_aed",
            "exit_comment",
        ],
        [
            {
                "entry_time": "2026.01.02 01:00:00",
                "direction": direction,
                "entry_deal": "2",
                "volume": entry_volume,
                "entry_price": "2000.00",
                "entry_comment": "entry",
                "exit_time": "2026.01.02 02:00:00",
                "exit_deal": "3",
                "exit_price": "2001.00",
                "profit_aed": "1.00",
                "exit_comment": "tp",
            }
        ],
    )
    deal_fields = [
        "timestamp_broker",
        "run_id",
        "account",
        "symbol",
        "magic",
        "deal_ticket",
        "position_id",
        "entry_code",
        "type_code",
        "reason_code",
        "direction",
        "volume",
        "price",
        "profit",
        "commission",
        "swap",
        "order_ticket",
        "comment",
    ]
    common = {
        "run_id": run_id,
        "account": "1025742",
        "symbol": "XAUUSD",
        "magic": "932200",
        "position_id": "2",
        "direction": direction,
        "commission": "0.00",
        "swap": "0.00",
    }
    _write_csv(
        deals,
        deal_fields,
        [
            {
                **common,
                "timestamp_broker": "2026.01.02 01:00:00",
                "deal_ticket": "2",
                "entry_code": "0",
                "type_code": entry_type,
                "reason_code": "3",
                "volume": entry_volume,
                "price": "2000.00",
                "profit": "0.00",
                "order_ticket": "2",
                "comment": "entry",
            },
            {
                **common,
                "timestamp_broker": "2026.01.02 02:00:00",
                "deal_ticket": "3",
                "entry_code": "1",
                "type_code": exit_type,
                "reason_code": "5",
                "volume": exit_volume,
                "price": "2001.00",
                "profit": "1.00",
                "order_ticket": "3",
                "comment": "tp",
            },
        ],
        delimiter="\t",
    )
    return trades


def _write_baseline(path: Path, sources: list[tuple[str, str, Path]]):
    rows = []
    for source_id, direction, source_csv in sources:
        rows.append(
            {
                "component": source_id,
                "source_id": source_id,
                "direction": direction,
                "entry_time": "2026-01-02 01:00:00",
                "exit_time": "2026-01-02 02:00:00",
                "pnl_usd": "1.00",
                "source_csv": str(source_csv),
                "source_row": "2",
            }
        )
    _write_csv(path, list(rows[0]), rows)


def _frozen_baseline() -> Path | None:
    candidates = [REPO_ROOT / BASELINE_RELATIVE, REPO_ROOT.parent / "algo-trading-system" / BASELINE_RELATIVE]
    for candidate in candidates:
        if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == N.FROZEN_BASELINE_SHA256:
            return candidate
    return None


def test_frozen_678_native_positions_reproduce_preregistered_fifo_defect_counts():
    baseline = _frozen_baseline()
    if baseline is None:
        pytest.skip("byte-exact ignored raw evidence is staged by Commit 3")
    result = N.build_native_position_reconciliation(baseline)
    assert result.summary["all_valid"] is True
    assert result.summary["trade_count"] == 678
    assert result.summary["unique_native_entry_count"] == 678
    assert result.summary["unique_native_position_count"] == 678
    assert result.summary["unique_trade_id_count"] == 678
    assert result.summary["legacy_exit_deal_mismatch_count"] == 388
    assert result.summary["legacy_pnl_mismatch_count"] == 387
    assert result.summary["aggregate_native_pnl_usd"] == "9640.05"
    assert all(result.summary["checks"].values())
    assert result.summary["fifo_fallback_used"] is False
    assert result.summary["fee_evidence_complete_for_all_rows"] is False


def test_native_namespace_prevents_ticket_restart_collision(tmp_path: Path):
    first = _source_pair(tmp_path, "first", run_id="RUN_A", direction="LONG")
    second = _source_pair(tmp_path, "second", run_id="RUN_B", direction="LONG")
    baseline = tmp_path / "baseline.csv"
    _write_baseline(baseline, [("source_a", "LONG", first), ("source_b", "LONG", second)])

    result = N.build_native_position_reconciliation(baseline, enforce_frozen_controls=False)
    assert len(result.rows) == 2
    assert len({row["trade_id"] for row in result.rows}) == 2
    assert {row["native_entry_deal"] for row in result.rows} == {"2"}
    assert result.summary["checks"]["unique_entry_to_position"] is True
    assert result.summary["checks"]["unique_trade_ids"] is True


def test_partial_exit_fails_closed_without_fifo_fallback(tmp_path: Path):
    trades = _source_pair(
        tmp_path,
        "partial",
        run_id="RUN_PARTIAL",
        direction="SHORT",
        entry_volume="0.02",
        exit_volume="0.01",
    )
    baseline = tmp_path / "baseline.csv"
    _write_baseline(baseline, [("source_partial", "SHORT", trades)])

    with pytest.raises(N.NativePositionReconciliationError, match="full positive entry volume") as captured:
        N.build_native_position_reconciliation(baseline, enforce_frozen_controls=False)
    assert captured.value.status == "ROUTER_PATH_INVALID_EVIDENCE"


def test_identity_join_schema_excludes_exit_outcome_and_router_fields():
    assert set(N.IDENTITY_JOIN_FIELDS).isdisjoint(N.PROHIBITED_IDENTITY_JOIN_FIELDS)
    assert N.IDENTITY_JOIN_FIELDS == (
        "source_csv",
        "source_row",
        "entry_deal",
        "run_id",
        "account",
        "symbol",
        "magic",
        "position_id",
    )
