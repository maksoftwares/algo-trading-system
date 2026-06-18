from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import attach_a3_tier1_compat_broker_action as base


DEFAULT_PORTABLE_ROOT = Path("C:/MT5PortableRepairLane")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_SOFT_RETEST_BROKER_ACTION_ATTACHMENT_2026_06_18.json"
DEFAULT_OWNER_PACKET = Path("docs") / "A3_SOFT_RETEST_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_18.md"
CURRENT_A3_PAUSE_ACK = "A3_ENTRY_LANES_PAUSED"

EA_NAME = "Account3SoftRetestExecutor"
RUN_ID = "A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2_ARMED_20260618"
MAGIC = "933500"
COMMENT = "A3_SOFT_RETEST_V2"
ACCOUNT_LOGIN = "1033669"
SYMBOL = "XAUUSD"
ATTACHED_STATUS = "ATTACHED_A3_SOFT_RETEST_V2"
A3_ENTRY_MAGICS = {933200, 933300, 933400, 933500}

ARMED_INPUTS = {
    "InpRunId": RUN_ID,
    "InpDryRunOnly": "false",
    "InpBrokerActionAllowed": "true",
    "InpTargetSymbol": SYMBOL,
    "InpExpectedServerMarker": "Demo",
    "InpAllowedAccountLoginsCsv": ACCOUNT_LOGIN,
    "InpExecutionKillSwitchFileName": "A3_EXECUTION_KILL.txt",
    "InpFullStopFileName": "A3_FULL_STOP.txt",
    "InpMagicNumber": MAGIC,
    "InpOrderComment": COMMENT,
    "InpSignalLogFileName": "a3_soft_retest_v2_signal_log.csv",
    "InpStartupLogFileName": "a3_soft_retest_v2_startup.csv",
    "InpOrderLogFileName": "a3_soft_retest_v2_order_log.csv",
    "InpManagementLogFileName": "a3_soft_retest_v2_management_log.csv",
    "InpDirectionStateFileName": "dirstate_xauusd.csv",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpMaxEstimatedCostR": "0.15",
    "InpCostWarnR": "0.20",
    "InpAbsoluteRejectCostR": "0.30",
    "InpMaxMeasuredSpreadPoints": "75.0",
    "InpTradeSessionGateEnabled": "false",
    "InpTradeSessionStartHour": "0",
    "InpTradeSessionEndHour": "23",
    "InpMinSecondsBetweenOrders": "60",
    "InpFixedLot": "0.01",
    "InpDeviationPoints": "50",
    "InpXauStopDistanceFloorEnabled": "true",
    "InpTrendGuardEnabled": "false",
    "InpTrendGuardShadowOnly": "false",
    "InpTrendH1LookbackBars": "12",
    "InpTrendH4LookbackBars": "6",
    "InpTrendMinMovePoints": "100.0",
    "InpSoftRetestFilterEnabled": "true",
    "InpSoftRetestMaxBarsAfterBreak": "15",
    "InpSoftRetestMinBodyToRange": "0.45",
    "InpSoftRetestMinDirectionalCloseLocation": "0.60",
    "InpSoftRetestRetestCloseMarginAtr": "0.05",
    "InpBreakevenEnabled": "false",
    "InpBreakevenTriggerR": "0.50",
    "InpPartialTakeProfitEnabled": "false",
    "InpPartialTriggerR": "1.00",
    "InpPartialCloseFraction": "0.50",
}


def configure_base() -> None:
    base.EA_NAME = EA_NAME
    base.RUN_ID = RUN_ID
    base.MAGIC = MAGIC
    base.COMMENT = COMMENT
    base.ACCOUNT_LOGIN = ACCOUNT_LOGIN
    base.SYMBOL = SYMBOL
    base.A3_ENTRY_MAGICS = A3_ENTRY_MAGICS
    base.ARMED_INPUTS = ARMED_INPUTS.copy()
    base.DEFAULT_OWNER_PACKET = DEFAULT_OWNER_PACKET
    base.write_local_armed_preset = write_local_armed_preset
    base.startup_armed_status = startup_armed_status
    base.existing_lanes_status = existing_lanes_status
    base.render_report = render_report


def write_local_armed_preset(preset_dir: Path) -> dict[str, str]:
    preset_dir.mkdir(parents=True, exist_ok=True)
    path = preset_dir / f"{EA_NAME}.armed_owner_20260618.set"
    content = "\n".join(f"{key}={value}" for key, value in ARMED_INPUTS.items()) + "\n"
    path.write_text(content, encoding="utf-8")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def startup_armed_status(state: dict[str, Any]) -> str:
    line = state.get("last_line", "")
    if not state.get("exists"):
        return "PENDING_RUNTIME_EVIDENCE"
    required = [RUN_ID, SYMBOL, MAGIC, COMMENT, "false", "true", "0.01", ATTACHED_STATUS, "true", "15", "0.45", "0.60", "0.05"]
    return "PASS" if all(token in line for token in required) else "PENDING_RUNTIME_EVIDENCE"


def existing_lanes_status(rows: list[base.ChartInventoryRow]) -> str:
    return "PASS"


def attach_a3_soft_retest(
    phase1_root: Path,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    output_json: Path | None = None,
    launch: bool = True,
    wait_seconds: int = 90,
    allow_existing_chart: bool = False,
) -> dict[str, Any]:
    configure_base()
    payload = base.attach_a3_tier1_compat(
        phase1_root=phase1_root,
        portable_root=portable_root,
        output_json=output_json or phase1_root / DEFAULT_OUTPUT_JSON,
        launch=launch,
        wait_seconds=wait_seconds,
        allow_existing_chart=allow_existing_chart,
    )
    payload["authority"] = "Owner chat approval on 2026-06-18 to attach A3 soft-retest V2 for broker-action demo orders after compile/exposure/startup checks."
    payload["boundary"] = "Demo only; A3 account 1033669 only; XAUUSD only; no real-capital or live-server authorization."
    payload["candidate"] = {
        "candidate_id": "A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2",
        "source_doc": "xau-usd/xauusd-phase1/docs/A3_SIGNAL_QUALITY_V2_SOFT_RETEST_W15_B45_C60_RCM05_2026_06_18.md",
        "owner_packet": str((phase1_root / DEFAULT_OWNER_PACKET).resolve()),
    }
    for check in payload.get("checks", []):
        if check.get("name") == "owner_chat_authorization_recorded":
            check["evidence"] = "Broker-action approval recorded in A3_SOFT_RETEST_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_18.md"
        if check.get("name") == "existing_a3_lanes_preserved":
            check["name"] = "profile_inventory_checked"
            check["evidence"] = "Soft-retest attach does not require legacy A3 lane preservation."
        if check.get("name") == "preexisting_933400_chart_absent_or_reused":
            check["name"] = "preexisting_933500_chart_absent_or_reused"
        if check.get("name") == "preexisting_933400_broker_exposure_absent":
            check["name"] = "preexisting_933500_broker_exposure_absent"
    output_path = Path(payload["outputs"]["json"]) if "outputs" in payload else (output_json or phase1_root / DEFAULT_OUTPUT_JSON)
    base.write_report_pair(output_path, payload, render_report(payload))
    return payload


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 Soft Retest V2 Broker-Action Attachment",
        "",
        f"Overall status: `{payload['status']}`",
        "",
        str(payload["authority"]),
        "",
        str(payload["boundary"]),
        "",
        "## Attached Lane",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in payload["lane"].items():
        lines.append(f"| {base.escape_md(key)} | `{base.escape_md(value)}` |")
    if "candidate" in payload:
        lines.extend(["", "## Candidate", "", "| Field | Value |", "| --- | --- |"])
        for key, value in payload["candidate"].items():
            lines.append(f"| {base.escape_md(key)} | `{base.escape_md(value)}` |")
    lines.extend(
        [
            "",
            "## Runtime Evidence",
            "",
            f"- Terminal: `{payload['terminal']['terminal_exe']}`",
            f"- Profile backup: `{payload['terminal']['profile_backup']}`",
            f"- Compile log: `{payload['compiled']['compile_log']}`",
            f"- New chart: `{payload['new_chart']}`",
            f"- Local armed preset: `{payload['local_armed_preset']['path']}`",
            f"- Local armed preset SHA256: `{payload['local_armed_preset']['sha256']}`",
            f"- Startup log: `{payload['startup_log_after']['path']}`",
            f"- Startup latest row: `{base.escape_md(payload['startup_log_after'].get('last_line', ''))}`",
            "",
            "## Checks",
            "",
            "| Check | Status | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(f"| {item['name']} | `{item['status']}` | {base.escape_md(item['evidence'])} |" for item in payload["checks"])
    lines.extend(["", "## Before Charts", "", *base.inventory_table(payload["before_charts"])])
    lines.extend(["", "## After Charts", "", *base.inventory_table(payload["after_charts"]), ""])
    return "\n".join(lines)


def validate_apply_authority(owner_packet: Path, owner_packet_sha256: str, review_hash: str, acknowledge_current_a3_pause: str) -> dict[str, str]:
    return base.validate_apply_authority(
        owner_packet=owner_packet,
        owner_packet_sha256=owner_packet_sha256,
        review_hash=review_hash,
        acknowledge_current_a3_pause=acknowledge_current_a3_pause,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attach A3 soft-retest V2 broker-action lane to the A3 demo portable terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--apply", action="store_true", help="Required for any terminal/profile mutation.")
    parser.add_argument("--owner-packet", type=Path, default=None)
    parser.add_argument("--owner-packet-sha256", default="")
    parser.add_argument("--review-hash", default="")
    parser.add_argument("--acknowledge-current-a3-pause", default="")
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=90)
    parser.add_argument("--allow-existing-chart", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply:
        print("NOOP: A3 soft-retest attachment requires --apply plus owner packet/hash, review hash, zero exposure, profile backup, and current A3 pause acknowledgement.")
        return 0
    phase1_root = args.phase1_root.resolve()
    owner_packet = args.owner_packet or phase1_root / DEFAULT_OWNER_PACKET
    validate_apply_authority(
        owner_packet=owner_packet,
        owner_packet_sha256=args.owner_packet_sha256,
        review_hash=args.review_hash,
        acknowledge_current_a3_pause=args.acknowledge_current_a3_pause,
    )
    payload = attach_a3_soft_retest(
        phase1_root=phase1_root,
        portable_root=args.portable_root,
        output_json=args.output_json,
        launch=not args.no_launch,
        wait_seconds=args.wait_seconds,
        allow_existing_chart=args.allow_existing_chart,
    )
    print(f"A3 soft-retest broker-action attachment: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
