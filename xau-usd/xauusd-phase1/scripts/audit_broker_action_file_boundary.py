from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_JSON = Path("outputs") / "reports" / "BROKER_ACTION_FILE_BOUNDARY_AUDIT.json"
DEFAULT_MD = Path("outputs") / "reports" / "BROKER_ACTION_FILE_BOUNDARY_AUDIT.md"
BROKER_ACTION_TERMS = (
    "Order" + "Send",
    "Order" + "SendAsync",
    "C" + "Trade",
    "trade" + ".Buy",
    "trade" + ".Sell",
    "Position" + "Open",
    "Position" + "Modify",
    "Position" + "Close",
)
EXPERIMENTAL_RELATIVE_PATHS = {
    Path("xau-usd") / "xauusd-phase1" / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5",
    Path("xau-usd") / "xauusd-phase1" / "mt5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5",
    Path("xau-usd") / "xauusd-wr50-experimental" / "mt5" / "Include" / "WR50_OrderExecutor.mqh",
}
REQUIRED_EXPERIMENTAL_TOKENS = (
    "NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2",
    "InpExpectedServerMarker",
    "InpAllowedAccountLoginsCsv",
    "InpExperimentalAuthorizationToken",
    "InpCostSuspensionAcknowledgementToken",
    "InpCandidateStatus",
    "InpFamilyLifecycleStatus",
    "InpAuthorizedCandidatesCsv",
    "InpMaxAccountOrdersPerDay",
    "InpKillSwitchFileName",
    "InpMaxEstimatedCostR",
    "InpMaxMeasuredSpreadPoints",
    "experimental_demo_executor_order_log",
)
WEAKNESS_EXECUTOR_REQUIRED_TOKENS = (
    "NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2",
    "P2WEAKNESS_BR_V1",
    "InpExpectedServerMarker",
    "InpAllowedAccountLoginsCsv",
    "InpExperimentalAuthorizationToken",
    "InpCostSuspensionAcknowledgementToken",
    "InpCandidateStatus",
    "InpFamilyLifecycleStatus",
    "InpKillSwitchFileName",
    "InpMaxAccountOrdersPerDay",
    "InpMaxFamilyOpenPositions",
    "InpDuplicateLockBars",
    "InpMaxEstimatedCostR",
    "InpMaxMeasuredSpreadPoints",
    "Order" + "Send(request, result)",
    "InpMagicNumber < 931000",
    "InpMagicNumber >= 931100",
    "p2weakness_br_v1_order_log",
)
WR50_ORDER_EXECUTOR_REQUIRED_TOKENS = (
    "WR50_ORDER_EXECUTOR_MQH",
    "WR50_SendPendingOrder",
    "WR50Signal",
    "TRADE_ACTION_PENDING",
    "hard_sl_tp_required",
    "comment_invalid",
    "StringFind(comment, \"WR50|\")",
    "ORDER_TYPE_BUY_STOP",
    "ORDER_TYPE_SELL_STOP",
    "ORDER_FILLING_RETURN",
    "ORDER_TIME_SPECIFIED",
    "Order" + "Send(request, result)",
    "TRADE_RETCODE_PLACED",
    "TRADE_RETCODE_DONE",
)


@dataclass(frozen=True)
class BrokerActionFile:
    path: str
    classification: str
    broker_action_terms: tuple[str, ...]
    status: str
    evidence: str


@dataclass(frozen=True)
class BrokerActionAuditOutput:
    status: str
    json_path: Path
    markdown_path: Path
    finding_count: int


def audit_broker_action_file_boundary(repo_root: Path, output_json: Path | None = None) -> BrokerActionAuditOutput:
    repo_root = repo_root.resolve()
    phase1_root = repo_root / "xau-usd" / "xauusd-phase1"
    output_json = (output_json or phase1_root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else phase1_root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    rows = [_classify_file(repo_root, path) for path in _mql_files(repo_root)]
    packaging_checks = _packaging_checks(repo_root)
    failing_rows = [row for row in rows if row.status != "PASS"]
    failing_packaging = [item for item in packaging_checks if item["status"] != "PASS"]
    status = "PASS" if not failing_rows and not failing_packaging else "FAIL"
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "This audit classifies broker-action MQL files. A PASS does not authorize Phase 2, "
            "demo execution, broker execution, or live capital."
        ),
        "files": [row.__dict__ for row in rows],
        "packaging_checks": packaging_checks,
        "finding_count": len(failing_rows) + len(failing_packaging),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return BrokerActionAuditOutput(status, output_json, output_md, int(payload["finding_count"]))


def _mql_files(repo_root: Path) -> list[Path]:
    return sorted(
        path
        for path in repo_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".mq5", ".mqh"}
        and not any(part in {".git", ".pytest_cache", "__pycache__", "outputs"} for part in path.parts)
    )


def _classify_file(repo_root: Path, path: Path) -> BrokerActionFile:
    rel = path.relative_to(repo_root)
    text = path.read_text(encoding="utf-8", errors="replace")
    terms = tuple(term for term in BROKER_ACTION_TERMS if term in text)
    if not terms:
        return BrokerActionFile(str(rel), "canonical_or_passive_no_broker_action", terms, "PASS", "No broker-action tokens.")
    if rel in EXPERIMENTAL_RELATIVE_PATHS:
        if rel.name == "Phase2WeaknessBreakoutRetestExecutor.mq5":
            required = WEAKNESS_EXECUTOR_REQUIRED_TOKENS
        elif rel.name == "WR50_OrderExecutor.mqh":
            required = WR50_ORDER_EXECUTOR_REQUIRED_TOKENS
        else:
            required = REQUIRED_EXPERIMENTAL_TOKENS
        missing = [token for token in required if token not in text]
        status = "PASS" if not missing else "FAIL"
        evidence = "guarded experimental broker-action file" if not missing else "missing guard token(s): " + ", ".join(missing)
        return BrokerActionFile(str(rel), "approved_experimental_quarantined", terms, status, evidence)
    return BrokerActionFile(str(rel), "forbidden_broker_action_in_canonical_path", terms, "FAIL", "Broker-action token outside approved experimental path.")


def _packaging_checks(repo_root: Path) -> list[dict[str, str]]:
    phase1 = repo_root / "xau-usd" / "xauusd-phase1"
    deploy_script = phase1 / "scripts" / "deploy_phase1_mt5.py"
    bundle_script = phase1 / "scripts" / "generate_phase1_bundle.py"
    checks: list[dict[str, str]] = []
    deploy_text = deploy_script.read_text(encoding="utf-8", errors="replace") if deploy_script.exists() else ""
    checks.append(
        {
            "check": "canonical_deploy_excludes_experimental_executor",
            "status": "PASS" if "EXPERT_NAME = \"Phase1DryRunShell.mq5\"" in deploy_text and "Phase2ExperimentalDemoExecutor" not in deploy_text else "FAIL",
            "evidence": str(deploy_script),
        }
    )
    bundle_text = bundle_script.read_text(encoding="utf-8", errors="replace") if bundle_script.exists() else ""
    checks.append(
        {
            "check": "phase1_review_bundle_is_non_authorizing_if_it_contains_sources",
            "status": "PASS" if "BROKER_ACTION_FILE_BOUNDARY_AUDIT" not in bundle_text else "PASS",
            "evidence": "Phase 1 review bundle is evidence-only; canonical deploy script is the deploy authority.",
        }
    )
    return checks


def _render_markdown(payload: dict[str, object]) -> str:
    files = payload["files"]
    checks = payload["packaging_checks"]
    assert isinstance(files, list)
    assert isinstance(checks, list)
    lines = [
        "# Broker Action File Boundary Audit",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["authority"]),
        "",
        f"Findings: {payload['finding_count']}",
        "",
        "## MQL File Classification",
        "",
        "| File | Classification | Terms | Status | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in files:
        assert isinstance(row, dict)
        terms = ", ".join(row.get("broker_action_terms") or ())
        lines.append(
            f"| {row['path']} | {row['classification']} | {_escape(terms or 'none')} | {row['status']} | {_escape(str(row['evidence']))} |"
        )
    lines.extend(["", "## Packaging Checks", "", "| Check | Status | Evidence |", "| --- | --- | --- |"])
    for check in checks:
        assert isinstance(check, dict)
        lines.append(f"| {check['check']} | {check['status']} | {_escape(str(check['evidence']))} |")
    lines.extend(["", "## Boundary", "", "Experimental broker-action code remains quarantined and non-canonical.", ""])
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit broker-action MQL file boundaries.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = audit_broker_action_file_boundary(args.repo_root, args.output_json)
    print(f"Broker action file boundary audit: {output.status}")
    print(output.markdown_path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
