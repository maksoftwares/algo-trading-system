from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ACTIVE_MARKET_ACCEPTANCE_DOC = Path("docs") / "PHASE1_ACTIVE_MARKET_SOAK_ACCEPTANCE.md"
ACTIVE_MARKET_ACCEPTANCE_TOKEN = "PHASE1_ACTIVE_MARKET_56H_ACCEPTED"
DEFAULT_ACCEPTED_ACTIVE_MARKET_HOURS = 56.0


@dataclass(frozen=True)
class ActiveMarketAcceptance:
    path: Path
    accepted_hours: float
    token: str


def read_active_market_acceptance(source_root: Path) -> ActiveMarketAcceptance | None:
    path = source_root.resolve() / ACTIVE_MARKET_ACCEPTANCE_DOC
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if ACTIVE_MARKET_ACCEPTANCE_TOKEN not in text:
        return None
    if "Overall status: PASS" not in text:
        return None
    return ActiveMarketAcceptance(
        path=path,
        accepted_hours=_accepted_hours(text),
        token=ACTIVE_MARKET_ACCEPTANCE_TOKEN,
    )


def _accepted_hours(text: str) -> float:
    match = re.search(r"Accepted Phase 1 threshold\s*\|\s*([0-9]+(?:\.[0-9]+)?)", text)
    if match:
        return float(match.group(1))
    match = re.search(r"Accepted active-market hours:\s*([0-9]+(?:\.[0-9]+)?)", text)
    if match:
        return float(match.group(1))
    return DEFAULT_ACCEPTED_ACTIVE_MARKET_HOURS
