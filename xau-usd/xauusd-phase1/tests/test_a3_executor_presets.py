from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "mt5" / "Presets"


def _values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw or raw.strip().startswith("#"):
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def test_a3_safe_presets_are_committed_non_executing():
    guarded = _values(PRESETS / "Account3RoundRetestGuardedExecutor.safe_xauusd.set")
    structured = _values(PRESETS / "Account3RoundRetestStructuredExecutor.safe_xauusd.set")

    assert guarded["InpDryRunOnly"] == "true"
    assert guarded["InpBrokerActionAllowed"] == "false"
    assert guarded["InpAllowedAccountLoginsCsv"] == "1033669"
    assert guarded["InpMagicNumber"] == "933000"
    assert guarded["InpFixedLot"] == "0.01"
    assert guarded["InpMaxOpenPositionsPerMagic"] == "1"

    assert structured["InpDryRunOnly"] == "true"
    assert structured["InpBrokerActionAllowed"] == "false"
    assert structured["InpAllowedAccountLoginsCsv"] == "1033669"
    assert structured["InpMagicNumber"] == "933100"
    assert structured["InpFixedLot"] == "0.01"
    assert structured["InpMaxOpenPositionsPerMagic"] == "1"


def test_no_committed_a3_execution_enabled_preset():
    offenders = []
    for path in PRESETS.glob("Account3RoundRetest*Executor*.set"):
        text = path.read_text(encoding="utf-8")
        if "InpBrokerActionAllowed=true" in text:
            offenders.append(path.name)

    assert offenders == []
