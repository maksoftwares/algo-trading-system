from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"

A1_TERMINAL_DATA = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
A2_TERMINAL_DATA = Path("C:/MT5PortableTier1BestEA")
A3_TERMINAL_DATA = Path("C:/MT5PortableRepairLane")

A1_PROFILE = A1_TERMINAL_DATA / "MQL5" / "Profiles" / "Charts" / "Default"
A2_PROFILE = A2_TERMINAL_DATA / "MQL5" / "Profiles" / "Charts" / "Default"
A3_PROFILE = A3_TERMINAL_DATA / "MQL5" / "Profiles" / "Charts" / "Default"

EXECUTOR_EA = "Phase2ExperimentalDemoExecutor"
REPAIR_EA = "Phase2ExperimentalDemoRepairExecutor"
GUARDIAN_EA = "Account1DailyProfitFloorGuardian"
WR50_EA = "WR50_BreakoutWideStop_v0"

INVENTORY_CSV = REPORTS_DIR / "RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv"
OUTPUT_JSON = REPORTS_DIR / "A1_A2_920101_MAINTENANCE_SUPPLEMENTAL_VERIFICATION_2026_06_21.json"


@dataclass(frozen=True)
class ChartRow:
    lane: str
    chart: str
    path: str
    symbol: str
    expert: str
    broker_action_state: str
    derived_magic: str
    sha256: str
    inputs: dict[str, str]


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_inventory_csv(payload["inventory_rows"])
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_JSON.with_suffix(".md").write_text(render_markdown(payload), encoding="utf-8")
    print(f"{payload['status']} -> {OUTPUT_JSON}")
    print(f"inventory -> {INVENTORY_CSV}")
    return 0 if payload["status"].startswith("PASS") else 1


def build_payload() -> dict[str, Any]:
    inventory = inventory_all()
    checks = build_checks(inventory)
    status = (
        "PASS_WITH_ORDER_LOG_PENDING"
        if all(row["status"] in {"PASS", "PENDING"} for row in checks)
        and not any(row["status"] == "FAIL" for row in checks)
        else "FAIL"
    )
    startup_evidence = startup_log_evidence()
    source_mapping = derived_magic_source_mapping()
    order_log_evidence = order_log_evidence_rows()
    return {
        "status": status,
        "created_at_utc": now_utc(),
        "purpose": "Supplement Claude's runtime-state review after the A1/A2 920101 maintenance by refreshing the stale chart inventory and surfacing startup identity proof.",
        "boundaries": [
            "Read-only verification.",
            "No MT5 terminal, chart, preset, order, or position state is modified by this script.",
            "A3 remains paused and is not changed.",
        ],
        "inventory_csv": str(INVENTORY_CSV),
        "inventory_rows": [row_to_dict(row) for row in inventory],
        "checks": checks,
        "derived_magic_source_mapping": source_mapping,
        "startup_log_evidence": startup_evidence,
        "order_log_evidence": order_log_evidence,
        "claude_review_focus": [
            "Confirm the refreshed inventory supersedes the stale pre-fix RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv.",
            "Confirm A1 chart03 is the restored XAU breakout_retest executor with broker action enabled.",
            "Confirm A1 chart01/chart02/chart18/chart19/chart20 and chart21 are disarmed.",
            "Confirm A2 chart02 is the aligned XAU breakout_retest executor with broker action enabled.",
            "Confirm A1/A2 guardians are active with +100 AED daily floor and -100 AED daily loss stop.",
            "Confirm 920101 is derived from source formula plus startup mutex proof, while order-log proof is pending until the first post-maintenance order.",
        ],
    }


def inventory_all() -> list[ChartRow]:
    rows: list[ChartRow] = []
    for lane, profile in (("A1", A1_PROFILE), ("A2", A2_PROFILE), ("A3", A3_PROFILE)):
        if not profile.exists():
            continue
        rows.extend(inventory(lane, profile))
    return rows


def inventory(lane: str, profile: Path) -> list[ChartRow]:
    rows: list[ChartRow] = []
    for path in sorted(profile.glob("chart*.chr")):
        text = read_text_any(path)
        inputs = parse_inputs(text)
        expert = parse_expert(text)
        symbol = parse_value(text, "symbol")
        rows.append(
            ChartRow(
                lane=lane,
                chart=path.name,
                path=str(path),
                symbol=symbol,
                expert=expert,
                broker_action_state=broker_action_state(expert, inputs),
                derived_magic=derived_magic(expert, inputs, symbol),
                sha256=sha256_file(path),
                inputs=inputs,
            )
        )
    return rows


def broker_action_state(expert: str, inputs: dict[str, str]) -> str:
    if expert in {EXECUTOR_EA, REPAIR_EA}:
        if inputs.get("InpDryRunOnly") == "false" and inputs.get("InpBrokerActionAllowed") == "true":
            return "BROKER_ACTION_ENABLED"
        if inputs.get("InpDryRunOnly") == "true" and inputs.get("InpBrokerActionAllowed") == "false":
            return "DISARMED_DRY_RUN"
        return "MIXED_OR_UNKNOWN"
    if expert == WR50_EA:
        return "BROKER_ACTION_ENABLED" if inputs.get("InpAllowDemoTrading") == "true" else "DISARMED_DEMO_TRADING_FALSE"
    if expert == GUARDIAN_EA:
        if inputs.get("InpDryRunOnly") == "false" and inputs.get("InpCloseActionAllowed") == "true":
            return "GUARDIAN_CLOSE_ACTION_ENABLED"
        return "GUARDIAN_DRY_OR_UNKNOWN"
    if expert == "NO_EA":
        return "NO_EA"
    return "OBSERVER_OR_OTHER"


def derived_magic(expert: str, inputs: dict[str, str], chart_symbol: str) -> str:
    if expert != EXECUTOR_EA:
        return inputs.get("InpMagicNumber", "")
    candidate = inputs.get("InpCandidate", "")
    symbol = chart_symbol or inputs.get("InpTargetSymbol", "")
    candidate_offset = {
        "breakout_retest": 10,
        "swing_breakout_retest_v0": 20,
        "symbol_normalized_round_retest_v0": 30,
        "round_number_retest_v0": 40,
        "session_extreme_retest_v0": 50,
    }.get(candidate, 90)
    symbol_offset = {
        "XAUUSD": 1,
        "EURUSD": 2,
        "USDJPY": 3,
        "GBPUSD": 4,
        "BTCUSD": 5,
    }.get(symbol, 9)
    return str(920000 + candidate_offset * 10 + symbol_offset)


def row_to_dict(row: ChartRow) -> dict[str, str]:
    inputs = row.inputs
    return {
        "lane": row.lane,
        "chart": row.chart,
        "symbol": row.symbol,
        "expert": row.expert,
        "broker_action_state": row.broker_action_state,
        "derived_magic": row.derived_magic,
        "InpRunId": inputs.get("InpRunId", ""),
        "InpCandidate": inputs.get("InpCandidate", ""),
        "InpTargetSymbol": inputs.get("InpTargetSymbol", ""),
        "InpAllowedAccountLoginsCsv": inputs.get("InpAllowedAccountLoginsCsv", ""),
        "InpDryRunOnly": inputs.get("InpDryRunOnly", ""),
        "InpBrokerActionAllowed": inputs.get("InpBrokerActionAllowed", ""),
        "InpAllowDemoTrading": inputs.get("InpAllowDemoTrading", ""),
        "InpFixedLot": inputs.get("InpFixedLot", ""),
        "InpMaxOpenPositionsPerInstance": inputs.get("InpMaxOpenPositionsPerInstance", ""),
        "InpMaxEstimatedCostR": inputs.get("InpMaxEstimatedCostR", ""),
        "InpMaxMeasuredSpreadPoints": inputs.get("InpMaxMeasuredSpreadPoints", ""),
        "InpTradeSessionGateEnabled": inputs.get("InpTradeSessionGateEnabled", ""),
        "InpTradeSessionStartHour": inputs.get("InpTradeSessionStartHour", ""),
        "InpTradeSessionEndHour": inputs.get("InpTradeSessionEndHour", ""),
        "InpCloseActionAllowed": inputs.get("InpCloseActionAllowed", ""),
        "InpDailyFloorAed": inputs.get("InpDailyFloorAed", ""),
        "InpDailyLossStopEnabled": inputs.get("InpDailyLossStopEnabled", ""),
        "InpDailyLossStopAed": inputs.get("InpDailyLossStopAed", ""),
        "InpEntryHaltFileName": inputs.get("InpEntryHaltFileName", ""),
        "sha256": row.sha256,
        "path": row.path,
    }


def write_inventory_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "lane",
        "chart",
        "symbol",
        "expert",
        "broker_action_state",
        "derived_magic",
        "InpRunId",
        "InpCandidate",
        "InpTargetSymbol",
        "InpAllowedAccountLoginsCsv",
        "InpDryRunOnly",
        "InpBrokerActionAllowed",
        "InpAllowDemoTrading",
        "InpFixedLot",
        "InpMaxOpenPositionsPerInstance",
        "InpMaxEstimatedCostR",
        "InpMaxMeasuredSpreadPoints",
        "InpTradeSessionGateEnabled",
        "InpTradeSessionStartHour",
        "InpTradeSessionEndHour",
        "InpCloseActionAllowed",
        "InpDailyFloorAed",
        "InpDailyLossStopEnabled",
        "InpDailyLossStopAed",
        "InpEntryHaltFileName",
        "sha256",
        "path",
    ]
    with INVENTORY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_checks(rows: list[ChartRow]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    def pending(name: str, detail: str) -> None:
        checks.append({"name": name, "status": "PENDING", "detail": detail})

    a1_chart03 = [row for row in rows if row.lane == "A1" and row.chart == "chart03.chr"]
    a2_chart02 = [row for row in rows if row.lane == "A2" and row.chart == "chart02.chr"]
    a1_disabled = [row for row in rows if row.lane == "A1" and row.chart in {"chart01.chr", "chart02.chr", "chart18.chr", "chart19.chr", "chart20.chr"}]
    a1_wr50 = [row for row in rows if row.lane == "A1" and row.chart == "chart21.chr"]
    a1_guardian = [row for row in rows if row.lane == "A1" and row.chart == "chart26.chr"]
    a2_guardian = [row for row in rows if row.lane == "A2" and row.chart == "chart03.chr"]

    check("a1_chart03_920101_active", len(a1_chart03) == 1 and executor_ok(a1_chart03[0], "1025742", "experimental_demo_kill_switch.txt"), summarize_rows(a1_chart03))
    check("a2_chart02_920101_active", len(a2_chart02) == 1 and executor_ok(a2_chart02[0], "1033030", "tier1_bestea_kill_switch.txt"), summarize_rows(a2_chart02))
    check("a1_non_spec_lanes_disarmed", len(a1_disabled) == 5 and all(row_is_disarmed_or_absent(row) for row in a1_disabled), summarize_rows(a1_disabled))
    check("a1_wr50_disarmed", len(a1_wr50) == 1 and row_is_disarmed_or_absent(a1_wr50[0]), summarize_rows(a1_wr50))
    check("a1_guardian_active", len(a1_guardian) == 1 and guardian_ok(a1_guardian[0], "1025742", "experimental_demo_kill_switch.txt"), summarize_rows(a1_guardian))
    check("a2_guardian_active", len(a2_guardian) == 1 and guardian_ok(a2_guardian[0], "1033030", "tier1_bestea_kill_switch.txt"), summarize_rows(a2_guardian))

    a3_broker_action = [
        row for row in rows
        if row.lane == "A3"
        and row.expert != "NO_EA"
        and row.broker_action_state in {"BROKER_ACTION_ENABLED", "GUARDIAN_CLOSE_ACTION_ENABLED"}
    ]
    check("a3_no_broker_action_enabled", not a3_broker_action, summarize_rows(a3_broker_action) or "A3 has no broker-action enabled rows in inspected profile.")

    startup = startup_log_evidence()
    check("a1_startup_mentions_920101", startup["A1_920101"]["contains_920101"], startup["A1_920101"]["path"])
    check("a2_startup_mentions_920101", startup["A2_920101"]["contains_920101"], startup["A2_920101"]["path"])
    check("a1_guardian_startup_active", startup["A1_guardian"]["contains_active_guardian"], startup["A1_guardian"]["path"])
    check("a2_guardian_startup_active", startup["A2_guardian"]["contains_active_guardian"], startup["A2_guardian"]["path"])

    orders = order_log_evidence_rows()
    if not orders["A1_920101"]["has_post_maintenance_order_rows"]:
        pending("a1_first_order_log_proof", "No post-maintenance A1 920101 order row yet; expected until market/session signal fires.")
    if not orders["A2_920101"]["has_post_maintenance_order_rows"]:
        pending("a2_first_order_log_proof", "No post-maintenance A2 920101 order row yet; expected until market/session signal fires.")
    return checks


def executor_ok(row: ChartRow, account: str, kill_switch: str) -> bool:
    inputs = row.inputs
    return (
        row.symbol == "XAUUSD"
        and row.expert == EXECUTOR_EA
        and row.derived_magic == "920101"
        and row.broker_action_state == "BROKER_ACTION_ENABLED"
        and inputs.get("InpCandidate") == "breakout_retest"
        and inputs.get("InpTargetSymbol") == "XAUUSD"
        and inputs.get("InpAllowedAccountLoginsCsv") == account
        and inputs.get("InpFixedLot") == "0.01"
        and inputs.get("InpMaxOpenPositionsPerInstance") == "1"
        and inputs.get("InpMaxEstimatedCostR") == "0.30"
        and inputs.get("InpMaxMeasuredSpreadPoints") == "75.0"
        and inputs.get("InpTradeSessionGateEnabled") == "true"
        and inputs.get("InpTradeSessionStartHour") == "12"
        and inputs.get("InpTradeSessionEndHour") == "15"
        and inputs.get("InpKillSwitchFileName") == kill_switch
    )


def guardian_ok(row: ChartRow, account: str, halt_file: str) -> bool:
    inputs = row.inputs
    return (
        row.expert == GUARDIAN_EA
        and row.broker_action_state == "GUARDIAN_CLOSE_ACTION_ENABLED"
        and inputs.get("InpAllowedAccountLogin") == account
        and inputs.get("InpDailyFloorAed") == "100.0"
        and inputs.get("InpDailyLossStopEnabled") == "true"
        and inputs.get("InpDailyLossStopAed") == "-100.0"
        and inputs.get("InpEntryHaltFileName") == halt_file
    )


def row_is_disarmed_or_absent(row: ChartRow) -> bool:
    return row.broker_action_state in {"DISARMED_DRY_RUN", "DISARMED_DEMO_TRADING_FALSE", "NO_EA"}


def summarize_rows(rows: list[ChartRow]) -> str:
    return "; ".join(
        f"{row.lane} {row.chart} {row.symbol} {row.expert} {row.broker_action_state} magic={row.derived_magic}"
        for row in rows
    )


def startup_log_evidence() -> dict[str, dict[str, Any]]:
    paths = {
        "A1_920101": A1_TERMINAL_DATA / "MQL5" / "Files" / "a1_920101_evening_startup_log.csv",
        "A2_920101": A2_TERMINAL_DATA / "MQL5" / "Files" / "a2_920101_evening_startup_log.csv",
        "A1_guardian": A1_TERMINAL_DATA / "MQL5" / "Files" / "A1_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv",
        "A2_guardian": A2_TERMINAL_DATA / "MQL5" / "Files" / "A2_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv",
    }
    evidence: dict[str, dict[str, Any]] = {}
    for key, path in paths.items():
        tail = read_tail(path, 6)
        joined = "\n".join(tail)
        evidence[key] = {
            "path": str(path),
            "exists": path.exists(),
            "tail": tail,
            "contains_920101": "920101" in joined,
            "contains_active_guardian": guardian_startup_file_is_active(path),
        }
    return evidence


def guardian_startup_file_is_active(path: Path) -> bool:
    if not path.exists():
        return False
    lines = [line for line in read_text_any(path).splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    header = lines[0].split(",")
    row = lines[-1].split(",")
    if len(row) != len(header):
        return False
    values = dict(zip(header, row))
    return (
        values.get("dry_run") == "false"
        and values.get("close_action_allowed") == "true"
        and values.get("daily_floor_aed") in {"100.0", "100.00"}
        and values.get("daily_loss_stop_enabled") == "true"
        and values.get("daily_loss_stop_aed") in {"-100.0", "-100.00"}
        and values.get("startup_status", "").startswith("ATTACHED_")
    )


def order_log_evidence_rows() -> dict[str, dict[str, Any]]:
    paths = {
        "A1_920101": A1_TERMINAL_DATA / "MQL5" / "Files" / "a1_920101_evening_order_log.csv",
        "A2_920101": A2_TERMINAL_DATA / "MQL5" / "Files" / "a2_920101_evening_order_log.csv",
    }
    evidence: dict[str, dict[str, Any]] = {}
    for key, path in paths.items():
        tail = read_tail(path, 8)
        non_header_rows = [line for line in tail if line and not line.startswith("timestamp_broker")]
        evidence[key] = {
            "path": str(path),
            "exists": path.exists(),
            "tail": tail,
            "has_post_maintenance_order_rows": any("920101" in line for line in non_header_rows),
        }
    return evidence


def derived_magic_source_mapping() -> dict[str, Any]:
    source = PHASE1_ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"
    text = read_text_any(source)
    return {
        "source": str(source),
        "formula": "920000 + CandidateMagicOffset(InpCandidate) * 10 + SymbolMagicOffset(_Symbol)",
        "breakout_retest_candidate_offset": 10,
        "xauusd_symbol_offset": 1,
        "derived_magic": 920000 + 10 * 10 + 1,
        "source_contains_formula": "return 920000 + CandidateMagicOffset(InpCandidate) * 10 + SymbolMagicOffset(_Symbol);" in text,
        "source_contains_breakout_offset": 'if(candidate == "breakout_retest")' in text and "return 10;" in text,
        "source_contains_xauusd_offset": 'if(symbol_name == "XAUUSD")' in text and "return 1;" in text,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    checks = "\n".join(
        f"| {row['name']} | `{row['status']}` | {escape_md(row['detail'])} |"
        for row in payload["checks"]
    )
    key_rows = [
        row for row in payload["inventory_rows"]
        if (row["lane"], row["chart"]) in {
            ("A1", "chart01.chr"),
            ("A1", "chart02.chr"),
            ("A1", "chart03.chr"),
            ("A1", "chart18.chr"),
            ("A1", "chart19.chr"),
            ("A1", "chart20.chr"),
            ("A1", "chart21.chr"),
            ("A1", "chart26.chr"),
            ("A2", "chart02.chr"),
            ("A2", "chart03.chr"),
        }
    ]
    inventory_table = "\n".join(
        "| {lane} | {chart} | {symbol} | `{expert}` | `{state}` | `{magic}` | `{dry}` | `{broker}` | `{demo}` | `{start}->{end}` | `{account}` |".format(
            lane=row["lane"],
            chart=row["chart"],
            symbol=row["symbol"],
            expert=row["expert"],
            state=row["broker_action_state"],
            magic=row["derived_magic"],
            dry=row["InpDryRunOnly"],
            broker=row["InpBrokerActionAllowed"],
            demo=row["InpAllowDemoTrading"],
            start=row["InpTradeSessionStartHour"],
            end=row["InpTradeSessionEndHour"],
            account=row["InpAllowedAccountLoginsCsv"],
        )
        for row in key_rows
    )
    startup_sections = []
    for key, item in payload["startup_log_evidence"].items():
        startup_sections.append(f"### {key}\n\nPath: `{item['path']}`\n\n```text\n{chr(10).join(item['tail'])}\n```")
    source = payload["derived_magic_source_mapping"]
    order_sections = []
    for key, item in payload["order_log_evidence"].items():
        order_sections.append(f"### {key}\n\nPath: `{item['path']}`\n\nStatus: `{'ORDER_ROW_FOUND' if item['has_post_maintenance_order_rows'] else 'PENDING_FIRST_ORDER'}`\n\n```text\n{chr(10).join(item['tail'])}\n```")
    return f"""# A1/A2 920101 Maintenance Supplemental Verification - 2026-06-21

Status: `{payload['status']}`

Created UTC: `{payload['created_at_utc']}`

This is a read-only verification report. It refreshes the stale runtime chart inventory and surfaces startup identity proof after the A1/A2 920101 maintenance. It does not change MT5 runtime state.

## Checks

| Check | Status | Detail |
|---|---|---|
{checks}

## Key Runtime Inventory

Full refreshed inventory CSV: `{payload['inventory_csv']}`

| Lane | Chart | Symbol | Expert | State | Derived magic | Dry-run | Broker action | Demo trading | Session | Account |
|---|---|---|---|---|---:|---|---|---|---|---|
{inventory_table}

## Derived Magic Proof

`920101` is not a static chart input. It is derived at runtime by `Phase2ExperimentalDemoExecutor.mq5`:

```text
{source['formula']}
breakout_retest offset = {source['breakout_retest_candidate_offset']}
XAUUSD offset = {source['xauusd_symbol_offset']}
920000 + 10 * 10 + 1 = {source['derived_magic']}
```

Source: `{source['source']}`

- Source formula present: `{source['source_contains_formula']}`
- Breakout offset present: `{source['source_contains_breakout_offset']}`
- XAUUSD offset present: `{source['source_contains_xauusd_offset']}`

## Startup Evidence

{chr(10).join(startup_sections)}

## Order Log Evidence

No post-maintenance order is required yet because the market/session/signal may not have fired after the relaunch. The first Monday order should add order-log proof with magic `920101`.

{chr(10).join(order_sections)}

## Claude Review Focus

{chr(10).join(f'- {item}' for item in payload['claude_review_focus'])}
"""


def parse_expert(text: str) -> str:
    in_expert = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<expert>":
            in_expert = True
            continue
        if stripped == "</expert>":
            in_expert = False
            continue
        if in_expert and stripped.startswith("name="):
            return stripped.split("=", 1)[1]
    return "NO_EA"


def parse_inputs(text: str) -> dict[str, str]:
    inputs: dict[str, str] = {}
    in_inputs = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<inputs>":
            in_inputs = True
            continue
        if stripped == "</inputs>":
            in_inputs = False
            continue
        if in_inputs and "=" in stripped:
            key, value = stripped.split("=", 1)
            inputs[key] = value
    return inputs


def parse_value(text: str, key: str) -> str:
    prefix = f"{key}="
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith(prefix):
            return stripped.split("=", 1)[1]
    return ""


def read_text_any(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
        except FileNotFoundError:
            return ""
    return path.read_text(errors="replace") if path.exists() else ""


def read_tail(path: Path, limit: int) -> list[str]:
    if not path.exists():
        return []
    lines = read_text_any(path).splitlines()
    return lines[-limit:]


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
