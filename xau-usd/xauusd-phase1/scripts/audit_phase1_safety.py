from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MQL_FORBIDDEN_TERMS = (
    "Order" + "Send",
    "Order" + "Send" + "Async",
    "C" + "Trade",
    "trade" + ".Buy",
    "trade" + ".Sell",
    "Position" + "Open",
    "TRADE_ACTION_" + "DEAL",
    "TRADE_ACTION_" + "SLTP",
    "Position" + "Modify",
    "Position" + "Close",
    "Order" + "Delete",
)
PY_FORBIDDEN_TERMS = (
    "mt5." + "order_send",
    "order_" + "send(",
)
FORBIDDEN_TERMS = MQL_FORBIDDEN_TERMS + PY_FORBIDDEN_TERMS
SCAN_SUFFIXES = {".mq5", ".mqh", ".py"}
SOURCE_PARTS = ("mt5", "scripts")
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".venv", "outputs", "docs"}

ALLOWED_EXPERIMENTAL_DEMO_EXECUTION_FILES = {
    "Account3ProfitLockExitManager.mq5",
    "Account3RoundRetestGuardedExecutor.mq5",
    "Account3RoundRetestStructuredExecutor.mq5",
    "A3BreakoutExecutorBase.mqh",
    "Phase2ExperimentalDemoExecutor.mq5",
    "Phase2ExperimentalDemoRepairExecutor.mq5",
    "Phase2WeaknessBreakoutRetestExecutor.mq5",
    "W1D1MomentumContinuationExperimental.mq5",
    "W1D1MomentumM5ContinuationExperimental.mq5",
}


@dataclass(frozen=True)
class SafetyFinding:
    path: Path
    line_number: int
    term: str
    line: str


@dataclass(frozen=True)
class BrokerActionPolicy:
    allowed_terms: tuple[str, ...]
    required_tokens: tuple[str, ...]
    forbidden_tokens: tuple[str, ...] = ()


EXPERIMENTAL_POLICIES: dict[str, BrokerActionPolicy] = {
    "mt5/Experts/Phase2ExperimentalDemoExecutor.mq5": BrokerActionPolicy(
        allowed_terms=("Order" + "Send", "TRADE_ACTION_" + "DEAL"),
        required_tokens=(
            "input bool InpBrokerActionAllowed = false;",
            "InpDryRunOnly || !InpBrokerActionAllowed",
            "input string InpExpectedServerMarker = \"Demo\";",
            "InpAllowedAccountLoginsCsv",
            "AccountLoginWhitelisted()",
            "InpExperimentalAuthorizationToken",
            "ExperimentalAuthorizationTokenValid()",
            "InpCostSuspensionAcknowledgementToken",
            "CostSuspensionAcknowledgementTokenValid()",
            "InpKillSwitchFileName",
            "KillSwitchActive()",
            "ContainsText(server, \"live\")",
            "ContainsText(server, \"real\")",
            "InpMaxEstimatedCostR = 0.00",
            "InpMaxMeasuredSpreadPoints = 0.0",
        ),
    ),
    "mt5/Experts/Phase2ExperimentalDemoRepairExecutor.mq5": BrokerActionPolicy(
        allowed_terms=("Order" + "Send", "TRADE_ACTION_" + "DEAL"),
        required_tokens=(
            "input bool InpBrokerActionAllowed = false;",
            "InpDryRunOnly || !InpBrokerActionAllowed",
            "input string InpExpectedServerMarker = \"Demo\";",
            "InpAllowedAccountLoginsCsv",
            "AccountLoginWhitelisted()",
            "InpExperimentalAuthorizationToken",
            "ExperimentalAuthorizationTokenValid()",
            "InpCostSuspensionAcknowledgementToken",
            "CostSuspensionAcknowledgementTokenValid()",
            "InpKillSwitchFileName",
            "KillSwitchActive()",
            "ContainsText(server, \"live\")",
            "ContainsText(server, \"real\")",
            "InpMaxEstimatedCostR = 0.00",
            "InpMaxMeasuredSpreadPoints = 0.0",
        ),
    ),
    "mt5/Experts/Phase2WeaknessBreakoutRetestExecutor.mq5": BrokerActionPolicy(
        allowed_terms=("Order" + "Send", "TRADE_ACTION_" + "DEAL"),
        required_tokens=(
            "input bool InpDryRunOnly = true;",
            "input bool InpBrokerActionAllowed = false;",
            "input string InpExpectedServerMarker = \"Demo\";",
            "InpAllowedAccountLoginsCsv",
            "AccountLoginWhitelisted()",
            "InpExperimentalAuthorizationToken",
            "ExperimentalAuthorizationTokenValid()",
            "InpCostSuspensionAcknowledgementToken",
            "CostSuspensionAcknowledgementTokenValid()",
            "InpKillSwitchFileName",
            "KillSwitchActive()",
            "ContainsText(server, \"live\")",
            "ContainsText(server, \"real\")",
            "InpMaxEstimatedCostR = 0.30",
            "InpMaxMeasuredSpreadPoints = 75.0",
        ),
    ),
    "mt5/Include/A3BreakoutExecutorBase.mqh": BrokerActionPolicy(
        allowed_terms=("Order" + "Send", "TRADE_ACTION_" + "DEAL", "TRADE_ACTION_" + "SLTP"),
        required_tokens=(
            "input bool InpDryRunOnly = true;",
            "input bool InpBrokerActionAllowed = false;",
            "input string InpTargetSymbol = \"XAUUSD\";",
            "input string InpExpectedServerMarker = \"Demo\";",
            "input string InpAllowedAccountLoginsCsv = \"1033669\";",
            "input string InpExecutionKillSwitchFileName = \"A3_EXECUTION_KILL.txt\";",
            "input string InpFullStopFileName = \"A3_FULL_STOP.txt\";",
            "input int InpMagicNumber = A3_BREAKOUT_DEFAULT_MAGIC;",
            "InpMagicNumber != A3_BREAKOUT_EXPECTED_MAGIC",
            "AccountLoginWhitelisted()",
            "ScopeLocksPass",
            "FullStopActive()",
            "ExecutionKillSwitchActive()",
            "ContainsText(server, \"live\")",
            "ContainsText(server, \"real\")",
            "PositionGetInteger(POSITION_MAGIC) != InpMagicNumber",
            "OrderGetInteger(ORDER_MAGIC) == InpMagicNumber",
        ),
    ),
    "mt5/Experts/Account3ProfitLockExitManager.mq5": BrokerActionPolicy(
        allowed_terms=("Order" + "Send", "TRADE_ACTION_" + "SLTP"),
        required_tokens=(
            "input bool InpDryRunOnly = true;",
            "input bool InpManageActionAllowed = false;",
            "input string InpTargetSymbol = \"XAUUSD\";",
            "input string InpExpectedServerMarker = \"Demo\";",
            "input string InpAllowedAccountLoginsCsv = \"1033669\";",
            "input string InpExecutionKillSwitchFileName = \"A3_EXECUTION_KILL.txt\";",
            "input string InpFullStopFileName = \"A3_FULL_STOP.txt\";",
            "input string InpManagedMagicsCsv = \"933200,933400\";",
            "if(magic == 933300)",
            "return false;",
            "FullStopActive()",
            "ExecutionKillSwitchActive()",
            "AccountLoginWhitelisted()",
            "ScopeLocksPass",
            "InpDryRunOnly || !InpManageActionAllowed",
        ),
        forbidden_tokens=("TRADE_ACTION_" + "DEAL",),
    ),
    "mt5/Experts/Account3RoundRetestGuardedExecutor.mq5": BrokerActionPolicy(
        allowed_terms=("Order" + "Send", "TRADE_ACTION_" + "DEAL"),
        required_tokens=(
            "input bool InpDryRunOnly = true;",
            "input bool InpBrokerActionAllowed = false;",
            "input string InpTargetSymbol = \"XAUUSD\";",
            "input string InpExpectedServerMarker = \"Demo\";",
            "input string InpAllowedAccountLoginsCsv = \"1033669\";",
            "input string InpExecutionKillSwitchFileName = \"A3_EXECUTION_KILL.txt\";",
            "input string InpFullStopFileName = \"A3_FULL_STOP.txt\";",
            "input int InpMagicNumber = 933000;",
            "InpMagicNumber < 933000 || InpMagicNumber > 933099",
            "ClaimMutexBeforeOrder",
            "GlobalVariableSetOnCondition",
            "AccountLoginWhitelisted()",
            "FullStopActive()",
            "ExecutionKillSwitchActive()",
            "ContainsText(server, \"live\")",
            "ContainsText(server, \"real\")",
            "InpDryRunOnly || !InpBrokerActionAllowed",
        ),
    ),
    "mt5/Experts/Account3RoundRetestStructuredExecutor.mq5": BrokerActionPolicy(
        allowed_terms=("Order" + "Send", "TRADE_ACTION_" + "DEAL"),
        required_tokens=(
            "input bool InpDryRunOnly = true;",
            "input bool InpBrokerActionAllowed = false;",
            "input string InpTargetSymbol = \"XAUUSD\";",
            "input string InpExpectedServerMarker = \"Demo\";",
            "input string InpAllowedAccountLoginsCsv = \"1033669\";",
            "input string InpExecutionKillSwitchFileName = \"A3_EXECUTION_KILL.txt\";",
            "input string InpFullStopFileName = \"A3_FULL_STOP.txt\";",
            "input int InpMagicNumber = 933100;",
            "InpMagicNumber < 933100 || InpMagicNumber > 933199",
            "ClaimMutexBeforeOrder",
            "GlobalVariableSetOnCondition",
            "AccountLoginWhitelisted()",
            "FullStopActive()",
            "ExecutionKillSwitchActive()",
            "ContainsText(server, \"live\")",
            "ContainsText(server, \"real\")",
            "InpDryRunOnly || !InpBrokerActionAllowed",
        ),
    ),
    "mt5/Experts/W1D1MomentumContinuationExperimental.mq5": BrokerActionPolicy(
        allowed_terms=("C" + "Trade", "trade" + ".Buy", "trade" + ".Sell"),
        required_tokens=(
            "input bool   InpAllowDemoTrading     = false;",
            "input bool   InpAllowNonDemoAccounts = false;",
            "input long   InpAllowedAccountLogin  = 0;",
            "input string InpKillSwitchFileName",
            "ACCOUNT_TRADE_MODE_DEMO",
            "InpAllowDemoTrading ? \"ENABLED\" : \"DISABLED",
            "if(!InpAllowDemoTrading)",
            "KillSwitchPresent()",
            "InpMaxSpreadPoints",
            "InpFixedLots            = 0.01",
        ),
    ),
    "mt5/Experts/W1D1MomentumM5ContinuationExperimental.mq5": BrokerActionPolicy(
        allowed_terms=("C" + "Trade", "trade" + ".Buy", "trade" + ".Sell"),
        required_tokens=(
            "input bool   InpAllowDemoTrading      = false;",
            "input bool   InpAllowNonDemoAccounts  = false;",
            "input long   InpAllowedAccountLogin   = 0;",
            "input string InpKillSwitchFileName",
            "ACCOUNT_TRADE_MODE_DEMO",
            "InpAllowDemoTrading ? \"ENABLED\" : \"DISABLED",
            "if(!InpAllowDemoTrading)",
            "KillSwitchPresent()",
            "InpMaxSpreadPoints",
            "InpFixedLots             = 0.01",
        ),
    ),
}


def audit_canonical_phase1_sources(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for path in _scan_paths(root):
        relative = _relative_posix(root, path)
        if relative in EXPERIMENTAL_POLICIES:
            continue
        findings.extend(_broker_action_findings(path, _terms_for_path(path)))
    return findings


def audit_experimental_demo_sources(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for path in _scan_paths(root):
        relative = _relative_posix(root, path)
        policy = EXPERIMENTAL_POLICIES.get(relative)
        if policy is None:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(_policy_broker_action_findings(path, text, policy))
        findings.extend(_missing_required_token_findings(path, text, policy.required_tokens))
        findings.extend(_forbidden_token_findings(path, text, policy.forbidden_tokens))
    return findings


def audit_phase1_tree(root: Path) -> list[SafetyFinding]:
    return [
        *audit_canonical_phase1_sources(root),
        *audit_experimental_demo_sources(root),
    ]


def _policy_broker_action_findings(path: Path, text: str, policy: BrokerActionPolicy) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    allowed = set(policy.allowed_terms)
    for line_number, line in enumerate(text.splitlines(), start=1):
        for term in _terms_for_path(path):
            if term in line and term not in allowed:
                findings.append(SafetyFinding(path, line_number, term, line.strip()))
    return findings


def _broker_action_findings(path: Path, terms: tuple[str, ...]) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for term in terms:
            if term in line:
                findings.append(SafetyFinding(path, line_number, term, line.strip()))
    return findings


def _missing_required_token_findings(path: Path, text: str, tokens: tuple[str, ...]) -> list[SafetyFinding]:
    return [
        SafetyFinding(path, 0, "required_guard_missing", token)
        for token in tokens
        if token not in text
    ]


def _forbidden_token_findings(path: Path, text: str, tokens: tuple[str, ...]) -> list[SafetyFinding]:
    return [
        SafetyFinding(path, 0, "forbidden_guard_present", token)
        for token in tokens
        if token in text
    ]


def _terms_for_path(path: Path) -> tuple[str, ...]:
    if path.suffix == ".py":
        return PY_FORBIDDEN_TERMS
    return MQL_FORBIDDEN_TERMS


def _scan_paths(root: Path) -> list[Path]:
    roots = [root / part for part in SOURCE_PARTS if (root / part).exists()]
    if not roots:
        roots = [root]
    return sorted(
        path
        for scan_root in roots
        for path in scan_root.rglob("*")
        if path.is_file()
        and path.suffix in SCAN_SUFFIXES
        and not any(part in IGNORED_PARTS for part in path.parts)
    )


def _relative_posix(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = audit_phase1_tree(root)
    if findings:
        for finding in findings:
            rel = finding.path.relative_to(root) if finding.path.is_relative_to(root) else finding.path
            location = str(rel) if finding.line_number == 0 else f"{rel}:{finding.line_number}"
            print(f"{location}: {finding.term}: {finding.line}")
        return 1
    print("Phase 1 safety audit OK: canonical sources are broker-action-free and experimental sources match their policies.")
    if ALLOWED_EXPERIMENTAL_DEMO_EXECUTION_FILES:
        allowed = ", ".join(sorted(ALLOWED_EXPERIMENTAL_DEMO_EXECUTION_FILES))
        print(f"Policy-governed experimental broker-action files: {allowed}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
