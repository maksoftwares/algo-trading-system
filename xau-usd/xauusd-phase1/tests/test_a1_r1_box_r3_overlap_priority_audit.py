from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import analyze_a1_r1_box_r3_overlap_priority_audit as audit  # noqa: E402


def _row(
    source_id: str,
    entry_time: datetime,
    *,
    pnl: float,
    source_row: int,
    direction: str = "LONG",
) -> dict[str, object]:
    exit_time = entry_time + timedelta(hours=1)
    return {
        "component": source_id,
        "source_id": source_id,
        "source_priority": 80 if source_id == audit.BOX_SOURCE else 85,
        "entry_time": entry_time,
        "entry_date": entry_time.date(),
        "exit_time": exit_time,
        "exit_date": exit_time.date(),
        "direction": direction,
        "pnl_usd": pnl,
        "tickets": 1,
        "lots": 0.01,
        "source_row": source_row,
    }


def _dropped_r3(
    entry_time: datetime,
    duplicate_time: datetime,
    *,
    pnl: float,
    source_row: int,
    direction: str = "LONG",
) -> dict[str, object]:
    row = _row(audit.R3_SOURCE, entry_time, pnl=pnl, source_row=source_row, direction=direction)
    row.update(
        {
            "drop_reason": "same_direction_overlap_5m",
            "duplicate_of_source_id": audit.BOX_SOURCE,
            "duplicate_of_entry_time": duplicate_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return row


class R1BoxR3OverlapPriorityAuditTests(unittest.TestCase):
    def test_pair_overlap_rows_is_one_to_one_inclusive_five_minutes_and_outcome_blind(self) -> None:
        box_time = datetime(2025, 1, 2, 8, 0)
        box = _row(audit.BOX_SOURCE, box_time, pnl=-999.0, source_row=2)
        r3 = _dropped_r3(box_time + timedelta(minutes=5), box_time, pnl=999.0, source_row=3)

        pairs = audit.pair_overlap_rows([box], [r3])

        self.assertEqual(pairs, [(box, r3)])
        box["pnl_usd"] = 5000.0
        r3["pnl_usd"] = -5000.0
        self.assertEqual(audit.pair_overlap_rows([box], [r3]), [(box, r3)])

    def test_pair_overlap_rows_fails_closed_on_ambiguous_baseline_match(self) -> None:
        entry_time = datetime(2025, 1, 2, 8, 0)
        baseline = [
            _row(audit.BOX_SOURCE, entry_time, pnl=10.0, source_row=2),
            _row(audit.BOX_SOURCE, entry_time, pnl=20.0, source_row=3),
        ]
        dropped = [_dropped_r3(entry_time, entry_time, pnl=30.0, source_row=4)]

        with self.assertRaisesRegex(ValueError, "exactly one baseline box match"):
            audit.pair_overlap_rows(baseline, dropped)

    def test_replacement_rows_swaps_only_mapped_box_and_preserves_nonoverlap(self) -> None:
        overlap_time = datetime(2025, 1, 2, 8, 0)
        other_time = datetime(2025, 1, 3, 8, 0)
        overlap_box = _row(audit.BOX_SOURCE, overlap_time, pnl=10.0, source_row=2)
        other_box = _row(audit.BOX_SOURCE, other_time, pnl=20.0, source_row=3)
        other_source = _row("r1_h1_pullback_long_v1", other_time + timedelta(hours=2), pnl=30.0, source_row=4)
        overlap_r3 = _dropped_r3(overlap_time, overlap_time, pnl=40.0, source_row=5)
        nonoverlap_r3 = _row(audit.R3_SOURCE, other_time + timedelta(days=1), pnl=50.0, source_row=6)

        result = audit.replacement_rows(
            [overlap_box, other_box, other_source],
            [overlap_r3, nonoverlap_r3],
            [(overlap_box, overlap_r3)],
        )
        identities = {audit.row_identity(row) for row in result}

        self.assertNotIn(audit.row_identity(overlap_box), identities)
        self.assertIn(audit.row_identity(other_box), identities)
        self.assertIn(audit.row_identity(other_source), identities)
        self.assertIn(audit.row_identity(overlap_r3), identities)
        self.assertIn(audit.row_identity(nonoverlap_r3), identities)
        self.assertEqual(len(result), 4)

    def test_dd_kill_rule_takes_precedence_over_otherwise_passing_gates(self) -> None:
        gates = {"quality": True, "dd": False}
        kills = {"replacement_dd_gt_115pct_baseline": True}

        status, decision, _interpretation = audit.decide(gates, kills)

        self.assertEqual(status, "R1_BOX_R3_OVERLAP_PRIORITY_KILL_PORTFOLIO_USE")
        self.assertEqual(decision, "KILLED_FOR_PORTFOLIO_USE_KEEP_STANDALONE_SHADOW_ONLY")

    def test_committed_exact_ledgers_recompose_to_frozen_audit_result(self) -> None:
        payload, artifacts = audit.build_audit()
        metrics = payload["metrics"]

        self.assertTrue(all(payload["integrity_checks"].values()))
        self.assertEqual(metrics["overlap_count"], 110)
        self.assertEqual(metrics["r3_dropped_count"], 110)
        self.assertEqual(metrics["baseline_trade_kept_count"], 110)
        self.assertEqual(metrics["nonoverlap_r3_count"], 29)
        self.assertAlmostEqual(metrics["r3_overlap_net"], 6618.92, places=2)
        self.assertAlmostEqual(metrics["baseline_overlap_net"], 4236.90, places=2)
        self.assertAlmostEqual(metrics["r3_replaces_baseline_delta_net"], 2382.02, places=2)
        self.assertAlmostEqual(metrics["nonoverlap_r3_net"], 3523.80, places=2)
        self.assertAlmostEqual(metrics["replacement_combined_net"], 15545.87, places=2)
        self.assertAlmostEqual(metrics["replacement_stress_net"], 15333.77, places=2)
        self.assertAlmostEqual(metrics["replacement_wr"], 53.18, places=2)
        self.assertAlmostEqual(metrics["replacement_wl"], 3.0911, places=4)
        self.assertAlmostEqual(metrics["replacement_pf"], 3.5113, places=4)
        self.assertAlmostEqual(metrics["replacement_max_closed_dd"], 1217.13, places=2)
        self.assertAlmostEqual(metrics["r3_replaces_baseline_delta_dd"], 140.57, places=2)
        self.assertAlmostEqual(metrics["replacement_vs_r1_r2_baseline_delta_dd"], 327.44, places=2)
        self.assertAlmostEqual(metrics["replacement_dd_minus_cap"], 193.99, places=2)
        self.assertAlmostEqual(metrics["replacement_recent3_net"], 764.92, places=2)
        self.assertAlmostEqual(metrics["top10_removed_net"], 12055.93, places=2)
        self.assertAlmostEqual(metrics["top3_days_removed_net"], 12566.55, places=2)
        self.assertAlmostEqual(metrics["best_month_share_pct"], 21.71, places=2)
        self.assertEqual(metrics["positive_months"], 27)
        self.assertEqual(len(artifacts["pairs"]), 110)
        self.assertEqual(len(artifacts["replacement"]), 707)
        self.assertEqual(payload["failed_gates"], ["replacement_dd_lte_115pct_baseline"])
        self.assertEqual(payload["triggered_kill_rules"], ["replacement_dd_gt_115pct_baseline"])
        self.assertEqual(payload["decision"], "KILLED_FOR_PORTFOLIO_USE_KEEP_STANDALONE_SHADOW_ONLY")
        dd_window = payload["dd_window_attribution"]
        self.assertEqual(dd_window["peak_exit_time"], "2025-04-02 23:46:32")
        self.assertEqual(dd_window["trough_exit_time"], "2025-08-11 11:31:42")
        self.assertEqual(dd_window["replaced_box_trades_closing_in_window"], 5)
        self.assertEqual(dd_window["replacement_r3_trades_closing_in_window"], 5)
        self.assertAlmostEqual(dd_window["replaced_box_net_in_window"], -305.37, places=2)
        self.assertAlmostEqual(dd_window["replacement_r3_net_in_window"], -445.94, places=2)
        self.assertAlmostEqual(dd_window["r3_minus_box_net_in_window"], -140.57, places=2)

    def test_order_send_fail_reconciliation_and_no_mt5_execution_path(self) -> None:
        payload, _artifacts = audit.build_audit()
        reconciliation = payload["ORDER_SEND_FAIL_RECONCILIATION"]
        script_text = (SCRIPTS / "analyze_a1_r1_box_r3_overlap_priority_audit.py").read_text(encoding="utf-8")

        self.assertEqual(reconciliation["order_send_ok_count"], 139)
        self.assertEqual(reconciliation["order_send_fail_count"], 2)
        self.assertTrue(reconciliation["count_reconciles"])
        self.assertTrue(reconciliation["all_failures_have_would_signal"])
        self.assertTrue(reconciliation["all_failures_unexecuted"])
        self.assertEqual({item["retcode"] for item in reconciliation["failures"]}, {10018})
        self.assertEqual({item["retcode_description"] for item in reconciliation["failures"]}, {"market closed"})
        self.assertTrue(all(not item["same_timestamp_retry_observed"] for item in reconciliation["failures"]))
        self.assertTrue(all(not item["hypothetical_pnl_imputed"] for item in reconciliation["failures"]))
        self.assertNotIn("run_variants(", script_text)
        self.assertIn("no new MT5 run", payload["evidence_boundary"])

    def test_render_narratives_follow_pass_no_pass_and_kill_status(self) -> None:
        base, _artifacts = audit.build_audit()

        kill_report = audit.render(base)
        self.assertIn("portfolio use is killed by the triggered hard rule", kill_report)
        self.assertIn("exceeds the hard cap", kill_report)

        passed = deepcopy(base)
        passed["status"] = "R1_BOX_R3_OVERLAP_PRIORITY_PASS"
        passed["decision"] = "REPLACEMENT_SUPPORTED_PENDING_ONE_EXACT_MT5_TEST"
        passed["interpretation"] = "Synthetic pass rendering check."
        passed["metrics"]["replacement_dd_minus_cap"] = -25.0
        passed["replacement_combined"]["max_closed_dd"] = 998.14
        passed["gate_checks"] = {name: True for name in passed["gate_checks"]}
        passed["failed_gates"] = []
        passed["kill_checks"] = {name: False for name in passed["kill_checks"]}
        passed["triggered_kill_rules"] = []
        pass_report = audit.render(passed)
        self.assertIn("Proceed only to the one conditional exact-MT5 source-priority test", pass_report)
        self.assertIn("headroom to the hard cap", pass_report)
        self.assertNotIn("portfolio use is killed", pass_report)

        no_pass = deepcopy(base)
        no_pass["status"] = "R1_BOX_R3_OVERLAP_PRIORITY_NO_PASS"
        no_pass["decision"] = "KEEP_STANDALONE_SHADOW_ONLY"
        no_pass["interpretation"] = "Synthetic no-pass rendering check."
        no_pass["kill_checks"] = {name: False for name in no_pass["kill_checks"]}
        no_pass["triggered_kill_rules"] = []
        no_pass_report = audit.render(no_pass)
        self.assertIn("audit did not clear every pass gate", no_pass_report)
        self.assertNotIn("portfolio use is killed", no_pass_report)


if __name__ == "__main__":
    unittest.main()
