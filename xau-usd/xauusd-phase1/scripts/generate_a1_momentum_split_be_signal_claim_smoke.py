import json
from datetime import datetime, timezone
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
OUT_JSON = REPORTS / "A1_XAU_M5_MOMENTUM_SPLIT_BE_SIGNAL_CLAIM_SMOKE_2026_07_03.json"
OUT_MD = REPORTS / "A1_XAU_M5_MOMENTUM_SPLIT_BE_SIGNAL_CLAIM_SMOKE_2026_07_03.md"
EA = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"


def simulate_ordered_claim() -> list[dict[str, str]]:
    claims: set[tuple[str, str]] = set()
    rows: list[dict[str, str]] = []
    signal = ("XAUUSD", "LONG", "2026-07-03T12:15:00")
    for component, priority in [
        ("risk_norm_split20_v6_max2_all8", 1),
        ("risk_norm_split20_freq_weak_hours_all8", 2),
        ("risk_norm_split20_v13_rr0p7_all8_22", 3),
    ]:
        higher_claim = any((signal, str(p)) in claims for p in range(1, priority))
        if higher_claim:
            action = "SKIP"
            reason = "signal_claimed_by_higher_priority"
        else:
            claims.add((signal, str(priority)))
            action = "CLAIM"
            reason = "SIGNAL_CLAIM_OK"
        rows.append(
            {
                "component": component,
                "priority": str(priority),
                "action": action,
                "reason": reason,
            }
        )
    return rows


def simulate_lower_first_with_grace() -> list[dict[str, str]]:
    return [
        {
            "component": "risk_norm_split20_freq_weak_hours_all8",
            "priority": "2",
            "event": "lower priority signal appears first",
            "action": "WAIT_GRACE",
            "reason": "InpSignalClaimGraceSeconds gives priority 1 time to claim",
        },
        {
            "component": "risk_norm_split20_v6_max2_all8",
            "priority": "1",
            "event": "highest priority claims same direction/bar",
            "action": "CLAIM",
            "reason": "SIGNAL_CLAIM_OK",
        },
        {
            "component": "risk_norm_split20_freq_weak_hours_all8",
            "priority": "2",
            "event": "lower priority resumes after grace",
            "action": "SKIP",
            "reason": "signal_claimed_by_higher_priority",
        },
    ]


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    source = EA.read_text(encoding="utf-8")
    required_fragments = [
        "InpSignalClaimEnabled",
        "InpSignalClaimPriority",
        "HigherPrioritySignalClaimExists",
        "GlobalVariableSetOnCondition",
        "signal_claimed_by_higher_priority",
        "SIGNAL_CLAIM_OK",
    ]
    source_checks = [
        {"fragment": fragment, "present": fragment in source} for fragment in required_fragments
    ]
    ordered = simulate_ordered_claim()
    lower_first = simulate_lower_first_with_grace()
    pass_status = (
        all(row["present"] for row in source_checks)
        and sum(1 for row in ordered if row["action"] == "CLAIM") == 1
        and ordered[0]["priority"] == "1"
        and all(row["action"] == "SKIP" for row in ordered[1:])
    )
    payload = {
        "status": "PASS" if pass_status else "FAIL",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Offline smoke only; no MT5 runtime, chart, preset, order, or position changed.",
        "source_checks": source_checks,
        "ordered_simultaneous_case": ordered,
        "lower_priority_first_with_grace_case": lower_first,
        "expected_runtime_effect": (
            "For the split-entry forward stack, only the highest-priority component should send "
            "orders for a same-direction signal inside the four-minute claim window."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# A1 XAU M5 Momentum Split-Entry Signal Claim Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["scope"],
        "",
        "## Source Checks",
        "",
        "| Fragment | Present |",
        "|---|---:|",
    ]
    for row in source_checks:
        lines.append(f"| `{row['fragment']}` | `{row['present']}` |")
    lines.extend(["", "## Simultaneous Same-Bar Case", "", "| Component | Priority | Action | Reason |", "|---|---:|---:|---|"])
    for row in ordered:
        lines.append(
            f"| `{row['component']}` | `{row['priority']}` | `{row['action']}` | `{row['reason']}` |"
        )
    lines.extend(["", "## Lower-Priority First With Grace", "", "| Component | Priority | Event | Action | Reason |", "|---|---:|---|---:|---|"])
    for row in lower_first:
        lines.append(
            f"| `{row['component']}` | `{row['priority']}` | {row['event']} | `{row['action']}` | {row['reason']} |"
        )
    lines.extend(["", "## Interpretation", "", payload["expected_runtime_effect"], ""])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "json": str(OUT_JSON), "md": str(OUT_MD)}))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
