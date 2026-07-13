from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_a1_xau_r5_pre_downtrend_opportunity.py"
spec = importlib.util.spec_from_file_location("r5_opportunity", SCRIPT)
assert spec and spec.loader
R = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = R
spec.loader.exec_module(R)


def write(path: Path, header: str, rows: list[str]) -> None:
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def test_analysis_keeps_rule_independent_and_applies_fixed_risk_filters(tmp_path: Path) -> None:
    deals, oracle, orders = tmp_path / "deals.tsv", tmp_path / "oracle.tsv", tmp_path / "orders.tsv"
    write(
        deals,
        "timestamp_broker\tposition_id\tentry_code",
        [
            "2022.07.01 00:00:00\t1\t0",
            "2022.07.01 02:00:00\t1\t1",
            "2022.07.01 01:00:00\t2\t0",
            "2022.07.01 03:00:00\t2\t1",
        ],
    )
    write(
        oracle,
        "timestamp_broker\treason",
        [
            "2022.07.01 00:30:00\tuptrend",
            "2022.07.01 01:30:00\tchop",
            "2022.07.01 02:30:00\tshock",
            "2022.07.01 04:00:00\tdowntrend",
        ],
    )
    write(
        orders,
        "timestamp_broker\treason\tspread_points\testimated_cost_r\tstop_points",
        [
            "2022.07.01 01:30:00\tregime_router_block_short_r2_downtrend_only_state_chop\t5\t0.04\t900",
            "2022.07.01 02:30:00\tregime_router_block_short_r2_downtrend_only_state_uptrend\t5\t0.06\t900",
            "2022.07.01 02:45:00\tregime_router_block_short_r2_downtrend_only_state_uptrend\t5\t0.04\t1001",
        ],
    )

    payload, overlap = R.analyze(deals, oracle, orders)
    assert payload["boundary"]["h4_outcomes_used_in_rule"] is False
    assert payload["h4"]["common_window_positions"] == 2
    assert payload["h4"]["common_window_merged_exposure_episodes"] == 1
    assert payload["router_availability_while_h4_exposed"]["exposed_rows"] == 3
    assert payload["q55_opportunities"]["raw_uptrend_chop_rows"] == 3
    assert payload["q55_opportunities"]["risk_eligible_rows"] == 1
    assert payload["q55_opportunities"]["h4_positions_touched"] == 2
    assert len(overlap) == 1
