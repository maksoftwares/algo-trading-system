from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "RUNTIME_AUTHORIZATION_RECONCILIATION_2026_06_19.json"
DEFAULT_EVIDENCE_DATE = "2026_06_18"


@dataclass(frozen=True)
class RuntimeAccount:
    label: str
    login: str
    role: str
    profile_dir: Path


ACCOUNTS = (
    RuntimeAccount(
        label="A1",
        login="1025742",
        role="standard_experimental_demo",
        profile_dir=Path(
            "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/"
            "D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Profiles/Charts/Default"
        ),
    ),
    RuntimeAccount(
        label="A2",
        login="1033030",
        role="tier1_breakout_only",
        profile_dir=Path("C:/MT5PortableTier1BestEA/MQL5/Profiles/Charts/Default"),
    ),
    RuntimeAccount(
        label="A3",
        login="1033669",
        role="paused_repair_lane",
        profile_dir=Path("C:/MT5PortableRepairLane/MQL5/Profiles/Charts/Default"),
    ),
)


@dataclass(frozen=True)
class ChartRuntime:
    account_label: str
    account_login: str
    chart: str
    symbol: str
    expert: str
    magic: str
    candidate: str
    dry_run_only: str
    broker_action_allowed: str
    manage_action_allowed: str
    allow_demo_trading: str
    run_id: str
    order_comment: str
    classification: str
    reason: str


def generate_runtime_authorization_reconciliation(
    phase1_root: Path,
    output_json: Path | None = None,
    evidence_date: str = DEFAULT_EVIDENCE_DATE,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    rows = [_classify_chart(account, chart) for account in ACCOUNTS for chart in _chart_rows(account)]
    evidence = _load_daily_trade_evidence(phase1_root, evidence_date)
    prior_drift = _prior_drift_rows(evidence)
    current_bad = [row for row in rows if row.classification in {"UNAUTHORIZED", "PAUSED_BUT_TRADING"}]
    status = "PASS_CURRENT"
    if current_bad:
        status = "FAIL_CURRENT_RUNTIME_DRIFT"
    elif prior_drift:
        status = "PASS_CURRENT_PRIOR_DRIFT_REMEDIATED"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "purpose": "Standing runtime-vs-authorized reconciliation across A1/A2/A3 demo terminals.",
        "boundary": {
            "read_only": True,
            "orders_sent": False,
            "positions_closed": False,
            "profiles_modified": False,
            "canonical_phase2_changed": False,
            "live_real_capital": False,
        },
        "accounts": [asdict(account) | {"profile_dir": str(account.profile_dir)} for account in ACCOUNTS],
        "charts": [asdict(row) for row in rows],
        "summary": _summary(rows),
        "current_bad_rows": [asdict(row) for row in current_bad],
        "evidence_date": evidence_date,
        "trade_evidence_summary": evidence,
        "prior_drift_rows": prior_drift,
        "decision": _decision(status, current_bad, prior_drift),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_json.with_suffix(".md").write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _chart_rows(account: RuntimeAccount) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not account.profile_dir.exists():
        return rows
    for path in sorted(account.profile_dir.glob("chart*.chr")):
        text = _read_chart(path)
        if "<expert>" not in text:
            continue
        expert = _expert_name(text)
        if not expert:
            continue
        rows.append(
            {
                "account": account,
                "path": path,
                "symbol": _value(text, "symbol"),
                "expert": expert,
                "magic": _value(text, "InpMagicNumber"),
                "candidate": _value(text, "InpCandidate"),
                "dry_run_only": _value(text, "InpDryRunOnly"),
                "broker_action_allowed": _value(text, "InpBrokerActionAllowed"),
                "manage_action_allowed": _value(text, "InpManageActionAllowed"),
                "allow_demo_trading": _value(text, "InpAllowDemoTrading"),
                "run_id": _value(text, "InpRunId"),
                "order_comment": _value(text, "InpOrderComment"),
            }
        )
    return rows


def _classify_chart(account: RuntimeAccount, row: dict[str, Any]) -> ChartRuntime:
    action_requested = _broker_action_requested(row)
    magic = str(row["magic"])
    expert = str(row["expert"])
    classification = "AUTHORIZED"
    reason = "Matches expected demo role."

    if account.label == "A3":
        if action_requested:
            classification = "PAUSED_BUT_TRADING"
            reason = "A3 is paused; no A3 chart may have broker/manage action enabled."
        else:
            classification = "PAUSED"
            reason = "A3 chart is disarmed as expected."
    elif account.label == "A2":
        if expert == "Phase2ExperimentalDemoExecutor" and row["candidate"] == "breakout_retest" and row["symbol"] == "XAUUSD":
            classification = "AUTHORIZED" if action_requested else "AUTHORIZED_BUT_NOT_ARMED"
            reason = "A2 is the tier-1 breakout-only demo lane."
        elif _is_shadow_or_guardian(expert):
            classification = "AUTHORIZED_SHADOW"
            reason = "Non-entry support/observer lane."
        else:
            classification = "UNAUTHORIZED" if action_requested else "UNKNOWN_SAFE"
            reason = "A2 only authorizes tier-1 breakout plus support observers."
    elif account.label == "A1":
        if expert in {"Phase2ExperimentalDemoExecutor", "Phase2ExperimentalDemoRepairExecutor", "WR50_BreakoutWideStop_v0"}:
            classification = "AUTHORIZED" if action_requested else "AUTHORIZED_BUT_NOT_ARMED"
            reason = "A1 experimental demo entry lane; governed by A1 goal/session controls."
        elif _is_shadow_or_guardian(expert):
            classification = "AUTHORIZED_SHADOW"
            reason = "A1 support/guardian/observer lane."
        else:
            classification = "UNAUTHORIZED" if action_requested else "UNKNOWN_SAFE"
            reason = "Unknown A1 expert with broker action surface."

    if magic == "933500" and account.label == "A3" and not action_requested:
        reason = "SoftRetest 933500 was previously drifted into broker action; current chart is now paused."

    return ChartRuntime(
        account_label=account.label,
        account_login=account.login,
        chart=Path(row["path"]).name,
        symbol=str(row["symbol"]),
        expert=expert,
        magic=magic,
        candidate=str(row["candidate"]),
        dry_run_only=str(row["dry_run_only"]),
        broker_action_allowed=str(row["broker_action_allowed"]),
        manage_action_allowed=str(row["manage_action_allowed"]),
        allow_demo_trading=str(row["allow_demo_trading"]),
        run_id=str(row["run_id"]),
        order_comment=str(row["order_comment"]),
        classification=classification,
        reason=reason,
    )


def _broker_action_requested(row: dict[str, Any]) -> bool:
    dry = str(row.get("dry_run_only", "")).lower()
    broker = str(row.get("broker_action_allowed", "")).lower()
    manage = str(row.get("manage_action_allowed", "")).lower()
    allow_demo = str(row.get("allow_demo_trading", "")).lower()
    if broker == "true" and dry != "true":
        return True
    if allow_demo == "true" and dry != "true":
        return True
    if manage == "true" and dry != "true":
        return True
    return False


def _is_shadow_or_guardian(expert: str) -> bool:
    return "Shadow" in expert or "Observer" in expert or "Publisher" in expert or "Guardian" in expert


def _load_daily_trade_evidence(phase1_root: Path, evidence_date: str) -> dict[str, Any]:
    path = phase1_root / "outputs" / "reports" / f"XAUUSD_DAILY_ROWS_{evidence_date}.csv"
    if not path.exists():
        return {"path": str(path), "exists": False, "rows": []}
    groups: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(lambda: {"trades": 0, "pnl_aed_001": 0.0})
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row.get("account", ""), row.get("magic", ""), row.get("candidate", ""))
            groups[key]["trades"] += 1
            groups[key]["pnl_aed_001"] += _float(row.get("profit_aed_001"))
    rows = [
        {
            "account": account,
            "magic": magic,
            "candidate": candidate,
            "trades": values["trades"],
            "pnl_aed_001": round(values["pnl_aed_001"], 2),
        }
        for (account, magic, candidate), values in sorted(groups.items())
    ]
    return {"path": str(path), "exists": True, "rows": rows}


def _prior_drift_rows(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in evidence.get("rows", []):
        if str(row.get("account")) == "1033669" and str(row.get("magic", "")).startswith("933") and row.get("trades", 0):
            rows.append({**row, "classification": "PAUSED_BUT_TRADING_EVIDENCE"})
    return rows


def _summary(rows: list[ChartRuntime]) -> dict[str, Any]:
    by_class = defaultdict(int)
    by_account = defaultdict(int)
    for row in rows:
        by_class[row.classification] += 1
        by_account[row.account_label] += 1
    return {
        "chart_count": len(rows),
        "by_classification": dict(sorted(by_class.items())),
        "by_account": dict(sorted(by_account.items())),
    }


def _decision(status: str, current_bad: list[ChartRuntime], prior_drift: list[dict[str, Any]]) -> str:
    if current_bad:
        return "HALT_OR_REPAIR_CURRENT_RUNTIME_BEFORE_RESEARCH"
    if prior_drift:
        return "CURRENT_RUNTIME_SAFE; PRIOR_A3_DRIFT_REMEDIATED; KEEP_RECONCILIATION_STANDING"
    return "CURRENT_RUNTIME_AUTHORIZED"


def _render_markdown(payload: dict[str, Any]) -> str:
    rows = payload["charts"]
    evidence_rows = payload["trade_evidence_summary"].get("rows", [])
    lines = [
        "# Runtime Authorization Reconciliation - 2026-06-19",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["purpose"],
        "",
        "Boundary: read-only reconciliation report. It sends no orders, closes no positions, and changes no profile.",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        "## Current Runtime Charts",
        "",
        "| Account | Chart | Symbol | Expert | Magic | Candidate | Dry-run | Broker | Manage | Demo | Classification | Reason |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {account_label} | {chart} | {symbol} | `{expert}` | `{magic}` | `{candidate}` | `{dry}` | `{broker}` | `{manage}` | `{demo}` | `{classification}` | {reason} |".format(
                account_label=row["account_label"],
                chart=row["chart"],
                symbol=row["symbol"],
                expert=_esc(row["expert"]),
                magic=row["magic"],
                candidate=_esc(row["candidate"]),
                dry=row["dry_run_only"],
                broker=row["broker_action_allowed"],
                manage=row["manage_action_allowed"],
                demo=row["allow_demo_trading"],
                classification=row["classification"],
                reason=_esc(row["reason"]),
            )
        )
    lines.extend(
        [
            "",
            "## Prior Drift Evidence",
            "",
            f"Evidence date: `{payload['evidence_date']}`",
            "",
            "| Account | Magic | Candidate | Trades | PnL AED_001 | Classification |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    prior = payload["prior_drift_rows"]
    if prior:
        for row in prior:
            lines.append(
                f"| {row['account']} | {row['magic']} | `{_esc(row['candidate'])}` | {row['trades']} | {row['pnl_aed_001']} | `{row['classification']}` |"
            )
    else:
        lines.append("| n/a | n/a | n/a | 0 | 0.00 | `NO_PRIOR_DRIFT_IN_EVIDENCE_FILE` |")
    lines.extend(["", "## Trade Evidence Summary", "", "| Account | Magic | Candidate | Trades | PnL AED_001 |", "| --- | --- | --- | ---: | ---: |"])
    for row in evidence_rows:
        lines.append(
            f"| {row['account']} | {row['magic']} | `{_esc(row['candidate'])}` | {row['trades']} | {row['pnl_aed_001']} |"
        )
    return "\n".join(lines) + "\n"


def _read_chart(path: Path) -> str:
    payload = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeError:
            continue
    return payload.decode(errors="replace")


def _expert_name(text: str) -> str:
    in_expert = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<expert>":
            in_expert = True
            continue
        if stripped == "</expert>":
            in_expert = False
            continue
        if in_expert and raw.startswith("name="):
            return raw.split("=", 1)[1].strip()
    return ""


def _value(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}=(.*)$", text)
    return match.group(1).strip() if match else ""


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0


def _esc(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate runtime-vs-authorized reconciliation across demo accounts.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--evidence-date", default=DEFAULT_EVIDENCE_DATE)
    args = parser.parse_args(argv)
    payload = generate_runtime_authorization_reconciliation(args.phase1_root, args.output_json, args.evidence_date)
    output = args.output_json or args.phase1_root / DEFAULT_OUTPUT_JSON
    print(json.dumps({"status": payload["status"], "output": str(output)}, indent=2))
    return 0 if not str(payload["status"]).startswith("FAIL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
