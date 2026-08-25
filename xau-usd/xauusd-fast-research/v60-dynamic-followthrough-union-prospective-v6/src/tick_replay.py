from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = (
    ROOT.parent
    / "v60-mature-source-health-rank-veto-prospective-v2"
    / "src"
    / "tick_replay.py"
)


spec = importlib.util.spec_from_file_location("v60_dynamic_v6_base_tick_replay", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load base tick replay: {BASE_PATH}")
BASE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = BASE
spec.loader.exec_module(BASE)

iter_tick_files = BASE.iter_tick_files
replay_ticks = BASE.replay_ticks
trades_from_evidence = BASE.trades_from_evidence
