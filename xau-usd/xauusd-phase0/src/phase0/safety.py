from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from phase0.config import ConfigError, ProjectConfig


FORBIDDEN_LIVE_TRADING_TERMS = (
    "Order" + "Send",
    "C" + "Trade",
    "trade" + ".Buy",
    "trade" + ".Sell",
    "Position" + "Open",
    "Order" + "Send" + "Async",
)

SAFETY_SCAN_GLOBS = (
    "src/phase0/**/*.py",
    "scripts/*.py",
    "tests/*.py",
    "mt5/*.mq5",
    "mt5/*.md",
    "README.md",
    "data/README_DATA.md",
)


@dataclass(frozen=True)
class SafetyFinding:
    path: Path
    line_number: int
    pattern: str
    line: str


def audit_no_live_trading_calls(config: ProjectConfig) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    compiled = [re.compile(_term_pattern(term)) for term in FORBIDDEN_LIVE_TRADING_TERMS]
    for path in _scan_paths(config.root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern in compiled:
                if pattern.search(line):
                    findings.append(
                        SafetyFinding(
                            path=path,
                            line_number=line_number,
                            pattern=pattern.pattern,
                            line=line.strip(),
                        )
                    )
    return findings


def assert_no_live_trading_calls(config: ProjectConfig) -> None:
    findings = audit_no_live_trading_calls(config)
    if not findings:
        return
    details = "\n".join(
        f"{finding.path}:{finding.line_number}: {finding.pattern}: {finding.line}"
        for finding in findings
    )
    raise ConfigError(f"Live-trading safety audit failed:\n{details}")


def _scan_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for pattern in SAFETY_SCAN_GLOBS:
        paths.extend(path for path in root.glob(pattern) if path.is_file())
    return sorted(set(paths))


def _term_pattern(term: str) -> str:
    return r"\b" + re.escape(term) + r"\b"
