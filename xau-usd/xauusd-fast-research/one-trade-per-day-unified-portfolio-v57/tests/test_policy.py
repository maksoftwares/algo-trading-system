import hashlib
from pathlib import Path

from policy import resolve_config


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_v57_uses_unified_hard_governor_contract() -> None:
    path = ROOT / "config" / "one_trade_per_day_unified_portfolio_v57.json"
    resolved, overlay = resolve_config(REPO_ROOT, path)
    base_path = REPO_ROOT / overlay["base_config_path"]
    assert (
        hashlib.sha256(base_path.read_bytes()).hexdigest()
        == overlay["base_config_sha256"]
    )
    assert resolved["account"]["drawdown_suspend_usd"] == 225.0
    assert resolved["account"]["drawdown_resume_usd"] == 180.0
    assert resolved["account"]["maximum_combined_closed_drawdown_usd"] == 300.0
    assert resolved["gates"]["minimum_combined_trades_per_weekday"] == 1.0
    assert resolved["overlay_sleeve"]["mechanism"] == "BREAK"
    assert resolved["overlay_sleeve"]["action_id"] == "SWING_2R_36H"
