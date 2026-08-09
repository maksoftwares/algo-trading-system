from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mql5" / "US500V41CausalSharedDemoEA.mq5"
PRE_OBSERVABILITY_SOURCE_SHA256 = (
    "91926cd40f33840096478471ab806b8f2b3e91e10775e721eaaf7613bcbb40b7"
)


def strategy_projection(source: str) -> str:
    """Remove the approved telemetry-only additions from the EA source."""
    omitted_lines = {
        'const string OPERATIONAL_HEALTH_LOG = "SHARED_1033030_US500_V41_HEALTH.csv";',
        "ulong g_health_sequence=0;",
        "ulong check_started=GetTickCount64();",
        "double check_ms=(double)(GetTickCount64()-check_started);",
        'OperationalHealth("ORDER_CHECK_FAILED",check_ms,-1.0,price,0.0,check.retcode);',
        "ulong send_started=GetTickCount64();",
        "double send_ms=(double)(GetTickCount64()-send_started);",
        'OperationalHealth("ORDER_EXECUTION",check_ms,send_ms,price,result.price,result.retcode);',
        "ulong close_send_started=GetTickCount64();",
        "double close_send_ms=(double)(GetTickCount64()-close_send_started);",
        'OperationalHealth("CLOSE_EXECUTION",-1.0,close_send_ms,request.price,result.price,result.retcode);',
        'OperationalHealth("INIT_HEALTH");',
        'OperationalHealth("HEARTBEAT_HEALTH");',
    }
    projected: list[str] = []
    inside_telemetry_function = False
    for line in source.splitlines(keepends=True):
        if line.startswith("// Best-effort operational telemetry only."):
            inside_telemetry_function = True
            continue
        if inside_telemetry_function:
            if line.startswith("bool TesterTrace("):
                inside_telemetry_function = False
                projected.append(line)
            continue
        if line.strip() not in omitted_lines:
            projected.append(line)
    return "".join(projected)


def test_removing_observability_recovers_exact_prior_frozen_strategy_source() -> None:
    source = EA.read_text(encoding="utf-8")
    projected = strategy_projection(source).encode("utf-8")

    assert hashlib.sha256(projected).hexdigest() == PRE_OBSERVABILITY_SOURCE_SHA256


def test_telemetry_is_best_effort_and_does_not_duplicate_broker_actions() -> None:
    source = EA.read_text(encoding="utf-8")
    telemetry = source.split("void OperationalHealth(", 1)[1].split("bool TesterTrace(", 1)[0]

    assert "g_integrity_failed" not in telemetry
    assert "return false" not in telemetry
    assert source.count("OrderCheck(request,check)") == 1
    # One unchanged entry send plus one unchanged timed-exit close send.
    assert source.count("OrderSend(request,result)") == 2
    assert "Sleep(" not in source
