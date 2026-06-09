from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_set(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(";") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_widestop_committed_presets_are_non_executing() -> None:
    presets = [
        ROOT / "mt5" / "Presets" / "WR50_WST12_SAFE_REVIEW_ONLY.set",
        ROOT / "mt5" / "Presets" / "WR50_WST15_SAFE_REVIEW_ONLY.set",
    ]
    for preset in presets:
        values = _read_set(preset)
        assert values["InpExperimentalDemoOnly"] == "true"
        assert values["InpAllowDemoTrading"] == "false"
        assert values["InpOwnerAuthorizationToken"] == ""
        assert values["InpRequiredOwnerAuthorizationToken"] == ""
        assert values["InpFixedLot"] == "0.01"
        assert values["InpMaxCostR"] == "0.15"


def test_widestop_presets_have_distinct_magics_and_targets() -> None:
    wst12 = _read_set(ROOT / "mt5" / "Presets" / "WR50_WST12_SAFE_REVIEW_ONLY.set")
    wst15 = _read_set(ROOT / "mt5" / "Presets" / "WR50_WST15_SAFE_REVIEW_ONLY.set")

    assert wst12["InpMagicNumber"] == "930300"
    assert wst12["InpTargetR"] == "1.20"
    assert wst12["InpEaShortCode"] == "WST12"

    assert wst15["InpMagicNumber"] == "930400"
    assert wst15["InpTargetR"] == "1.50"
    assert wst15["InpEaShortCode"] == "WST15"
