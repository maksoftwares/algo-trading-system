from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def generate_forward_week_evidence_templates(repo_root: Path, report_date: date | None = None) -> list[Path]:
    repo_root = repo_root.resolve()
    report_date = report_date or date.today()
    stamp = report_date.strftime("%Y_%m_%d")
    reports_dir = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    quarantine = _read_json(reports_dir / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.json")
    target_charts = quarantine.get("after_target_charts", quarantine.get("target_charts", []))
    protected_charts = quarantine.get("after_protected_charts", quarantine.get("protected_charts", []))

    outputs = {
        f"XAUUSD_ROUND_FAMILY_FORWARD_WEEK_IMPACT_{stamp}.md": _round_family_impact(stamp, target_charts),
        f"XAUUSD_PROTECTED_BREAKOUT_CORE_FORWARD_WEEK_{stamp}.md": _protected_breakout(stamp, protected_charts),
        f"XAUUSD_NON_ROUND_AFTERNOON_RESIDUAL_{stamp}.md": _non_round_residual(stamp),
        f"XAUUSD_ROUND_QUARANTINE_ROLLBACK_READINESS_{stamp}.md": _rollback_readiness(stamp, quarantine),
        f"A1_DIRECT_HISTORY_RECONCILIATION_{stamp}.md": _account_reconciliation("A1", "1025742", stamp),
        f"A2_DIRECT_HISTORY_RECONCILIATION_{stamp}.md": _account_reconciliation("A2", "1033030", stamp),
        f"A3_DIRECT_HISTORY_RECONCILIATION_{stamp}.md": _account_reconciliation("A3", "1033669", stamp),
    }
    written: list[Path] = []
    for name, text in outputs.items():
        path = reports_dir / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _round_family_impact(stamp: str, target_charts: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| `{item.get('chart', '')}` | `{item.get('candidate', '')}` | "
        f"`{item.get('dry_run', '')}` | `{item.get('broker_action_allowed', '')}` | "
        f"`0 expected` | `PENDING_FORWARD_WEEK` |"
        for item in target_charts
    )
    if not rows:
        rows = "| `PENDING_EXPORT` | `PENDING_EXPORT` | `PENDING_EXPORT` | `PENDING_EXPORT` | `0 expected` | `PENDING_FORWARD_WEEK` |"
    return f"""# XAUUSD Round-Family Forward-Week Impact Report - {stamp}

Status: `PENDING_FORWARD_WEEK`

Evidence/reporting only. No runtime change is authorized by this template.

## Quarantine State

| Chart | Candidate | Dry Run | Broker Action | Expected new broker rows | Status |
| --- | --- | ---: | ---: | ---: | --- |
{rows}

## Target Order-Log Delta

| Candidate | Rows before | Rows after | New broker-action rows | Status |
| --- | ---: | ---: | ---: | --- |
| `symbol_normalized_round_retest_v0` | `PENDING` | `PENDING` | `0 expected` | `PENDING_FORWARD_WEEK` |
| `round_number_retest_v0` | `PENDING` | `PENDING` | `0 expected` | `PENDING_FORWARD_WEEK` |

## Forward-Week Decision

Keep quarantine active: `PENDING_FORWARD_WEEK`

Rollback required: `PENDING_FORWARD_WEEK`

Further runtime change authorized: `false`
"""


def _protected_breakout(stamp: str, protected_charts: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| `{item.get('chart', '')}` | `{item.get('candidate', '')}` | `PENDING` | `PENDING` | "
        f"`PENDING` | `PENDING` | `PENDING_INPUT_DRIFT_CHECK` |"
        for item in protected_charts
    )
    if not rows:
        rows = "| `PENDING_EXPORT` | `breakout_retest / swing_breakout_retest_v0` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_INPUT_DRIFT_CHECK` |"
    return f"""# XAUUSD Protected Breakout-Core Forward-Week Report - {stamp}

Status: `PENDING_FORWARD_WEEK`

This report is for `breakout_retest` and `swing_breakout_retest_v0` only.

| Chart | Candidate | Rows | Win Rate | PnL AED | PF | Input Drift |
| --- | --- | ---: | ---: | ---: | ---: | --- |
{rows}

Required conclusion after the week:

- Did breakout-core keep trading normally?
- Did any input drift occur after round-family quarantine?
- Did protected evening/night behavior remain intact?
"""


def _non_round_residual(stamp: str) -> str:
    return f"""# XAUUSD Non-Round Afternoon Residual Report - {stamp}

Status: `PENDING_FORWARD_WEEK`

Purpose: measure whether the afternoon loss problem remains after the round-family broker-action quarantine.

| Slice | Rows | Win Rate | PnL AED | PF | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Non-round XAUUSD afternoon residual | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_FORWARD_WEEK` |

Do not use this report to authorize a broad afternoon ban unless fresh non-round evidence remains bad after the quarantine.
"""


def _rollback_readiness(stamp: str, quarantine: dict[str, Any]) -> str:
    backup = quarantine.get("terminal", {}).get("profile_backup_dir", "PENDING_BACKUP_PATH")
    return f"""# XAUUSD Round-Quarantine Rollback Readiness - {stamp}

Status: `PENDING_FORWARD_WEEK`

Backup path: `{backup}`

| Check | Expected | Status |
| --- | --- | --- |
| Backup path recorded | true | `PENDING_PATH_CHECK` |
| chart09/chart11 stay quarantined | true | `PENDING_FORWARD_WEEK` |
| chart03/chart06 stay unchanged | true | `PENDING_FORWARD_WEEK` |
| A2 untouched by round quarantine | true | `PENDING_DIRECT_HISTORY` |
| A3 untouched by round quarantine | true | `PENDING_DIRECT_HISTORY` |

Rollback is not recommended unless a documented trigger occurs.
"""


def _account_reconciliation(account_label: str, login: str, stamp: str) -> str:
    return f"""# {account_label} Direct History Reconciliation - {stamp}

Status: `PENDING_DIRECT_MT5_REFRESH`

Account: `{login}`

This template is intentionally not filled from stale CSV rows. Refresh direct MT5 history before completing it.

| Item | Value |
| --- | --- |
| Server | `PENDING_DIRECT_MT5_REFRESH` |
| Balance | `PENDING_DIRECT_MT5_REFRESH` |
| Equity | `PENDING_DIRECT_MT5_REFRESH` |
| Open positions | `PENDING_DIRECT_MT5_REFRESH` |
| New orders since round quarantine | `PENDING_DIRECT_MT5_REFRESH` |
| Unexpected runtime change | `PENDING_DIRECT_MT5_REFRESH` |

Conclusion: `PENDING_DIRECT_MT5_REFRESH`
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate pending forward-week XAUUSD evidence reports.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--date", default=None, help="Report date in YYYY-MM-DD format.")
    args = parser.parse_args(argv)
    report_date = date.fromisoformat(args.date) if args.date else None
    for path in generate_forward_week_evidence_templates(args.repo_root, report_date):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
