from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from phase0.config import ConfigError, ProjectConfig
from phase0.constants import SECOND_EA_CAMPAIGN_CANDIDATES
from phase0.research_hypotheses import validate_research_hypothesis
from phase0.second_ea_hypotheses import validate_second_ea_hypothesis
from phase0.strategies.registry import RESEARCH_STRATEGY_CLASSES, STRATEGY_CLASSES, get_research_strategy
from phase0.synthetic import synthetic_context_for_expert


@dataclass(frozen=True)
class ResearchSmokeOutput:
    status: str
    report_path: Path
    manifest_path: Path
    expert: str
    signal_count: int
    phase0_result_run_allowed: bool


def run_research_candidate_smoke(
    config: ProjectConfig,
    expert: str,
    hypothesis_file: str,
) -> ResearchSmokeOutput:
    if expert in STRATEGY_CLASSES:
        raise ConfigError(
            f"{expert} is already active in the production Phase 0 registry. "
            "Research smoke expects a disabled candidate."
        )
    if expert not in RESEARCH_STRATEGY_CLASSES:
        raise ConfigError(f"{expert!r} is not in the research strategy registry.")

    validation = _validate_candidate_hypothesis(config, expert, hypothesis_file)
    strategy = get_research_strategy(expert)
    context = synthetic_context_for_expert(expert)
    signals = strategy.generate_signals(context)
    if not signals:
        raise ConfigError(f"Research smoke for {expert} generated no synthetic signals.")
    plan = strategy.build_trade_plan(signals[-1], context)
    checks = [
        {
            "name": "hypothesis_hash_locked",
            "status": validation.status,
            "message": validation.message,
        },
        {
            "name": "research_strategy_registered",
            "status": "PASS",
            "message": "Strategy is available only in the research registry.",
        },
        {
            "name": "active_registry_disabled",
            "status": "PASS",
            "message": "Strategy is not included in the active Phase 0 `all` registry.",
        },
        {
            "name": "synthetic_signal",
            "status": "PASS",
            "message": f"Generated {len(signals)} synthetic signal(s).",
        },
        {
            "name": "synthetic_trade_plan",
            "status": "PASS",
            "message": (
                f"Plan direction={plan.direction}, entry_type={plan.entry_type}, "
                f"risk_reward={plan.risk_reward}."
            ),
        },
    ]
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"

    report_path = config.root / "outputs" / "reports" / f"{expert}_research_smoke.md"
    manifest_path = config.root / "outputs" / "manifests" / f"{expert}_research_smoke_manifest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(status, expert, validation.sha256, checks, signals, plan),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "expert": expert,
        "hypothesis_file": str(validation.hypothesis_file.relative_to(config.root)),
        "hypothesis_sha256": validation.sha256,
        "signal_count": len(signals),
        "phase0_result_run_allowed": False,
        "report_path": str(report_path.relative_to(config.root)),
        "checks": checks,
        "latest_signal": {
            "timestamp_utc": signals[-1].timestamp_utc.isoformat(),
            "direction": signals[-1].direction,
            "reason_code": signals[-1].reason_code,
        },
        "latest_plan": {
            "direction": plan.direction,
            "entry_type": plan.entry_type,
            "entry_price": plan.entry_price,
            "stop_loss": plan.stop_loss,
            "take_profit": plan.take_profit,
            "risk_reward": plan.risk_reward,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return ResearchSmokeOutput(
        status=status,
        report_path=report_path,
        manifest_path=manifest_path,
        expert=expert,
        signal_count=len(signals),
        phase0_result_run_allowed=False,
    )


def _validate_candidate_hypothesis(config: ProjectConfig, expert: str, hypothesis_file: str):
    if expert not in SECOND_EA_CAMPAIGN_CANDIDATES:
        return validate_research_hypothesis(config, expert, hypothesis_file)

    relative_path = Path(hypothesis_file)
    if relative_path.is_absolute():
        raise ConfigError("Research hypothesis file must be relative to the Phase 0 root.")
    hypothesis_path = config.root / relative_path
    lock_path = hypothesis_path.with_suffix(".sha256.json")
    result = validate_second_ea_hypothesis(hypothesis_path, lock_path, raise_on_error=True)
    return ResearchHypothesisSmokeValidation(
        status=result.status,
        expert=expert,
        hypothesis_file=hypothesis_path,
        sha256=_locked_sha256(hypothesis_path, lock_path),
        message="Second-EA hypothesis is complete and hash-locked.",
    )


@dataclass(frozen=True)
class ResearchHypothesisSmokeValidation:
    status: str
    expert: str
    hypothesis_file: Path
    sha256: str
    message: str


def _locked_sha256(hypothesis_path: Path, lock_path: Path) -> str:
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    locked_hash = str(payload.get("sha256_hash") or payload.get("sha256") or "")
    if not locked_hash:
        raise ConfigError(f"Second-EA lock file does not include sha256_hash: {lock_path}")
    return locked_hash


def _render_report(
    status: str,
    expert: str,
    hypothesis_sha256: str,
    checks: list[dict[str, str]],
    signals: list,
    plan,
) -> str:
    latest_signal = signals[-1]
    return "\n".join(
        [
            "# Research Candidate Smoke Report",
            "",
            f"Status: {status}",
            f"Generated at UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
            f"Expert: `{expert}`",
            f"Hypothesis SHA256: `{hypothesis_sha256}`",
            "",
            "## Boundary",
            "",
            "This is a synthetic smoke check only. It does not authorize matrix, decile, multisymbol, or adversarial result runs.",
            "",
            "Phase 0 result run allowed: `false`",
            "",
            "## Checks",
            "",
            _markdown_table(
                [
                    {
                        "Check": check["name"],
                        "Status": check["status"],
                        "Message": check["message"],
                    }
                    for check in checks
                ],
                ["Check", "Status", "Message"],
            ),
            "",
            "## Latest Synthetic Signal",
            "",
            _markdown_table(
                [
                    {
                        "Timestamp": latest_signal.timestamp_utc.isoformat(),
                        "Direction": latest_signal.direction,
                        "Reason": latest_signal.reason_code,
                    }
                ],
                ["Timestamp", "Direction", "Reason"],
            ),
            "",
            "## Latest Synthetic Plan",
            "",
            _markdown_table(
                [
                    {
                        "Direction": plan.direction,
                        "Entry Type": plan.entry_type,
                        "Entry": "" if plan.entry_price is None else str(plan.entry_price),
                        "Stop": f"{plan.stop_loss:.5f}",
                        "Target": f"{plan.take_profit:.5f}",
                        "R": f"{plan.risk_reward:.2f}",
                    }
                ],
                ["Direction", "Entry Type", "Entry", "Stop", "Target", "R"],
            ),
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, str]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)
