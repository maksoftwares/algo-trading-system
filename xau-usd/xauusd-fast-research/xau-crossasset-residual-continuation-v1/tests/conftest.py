from __future__ import annotations

import sys
from pathlib import Path

import pytest

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE / "src"))

from xau_continuation.research import configure_reviewed_engine  # noqa: E402


@pytest.fixture(scope="session")
def lane() -> Path:
    return LANE


@pytest.fixture(scope="session")
def reviewed(lane: Path):
    return configure_reviewed_engine(lane)
