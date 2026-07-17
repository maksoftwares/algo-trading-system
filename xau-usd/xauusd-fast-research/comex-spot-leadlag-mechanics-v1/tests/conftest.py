from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "comex_spot_leadlag_campaign_tests", ROOT / "src" / "campaign.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError("Could not load COMEX-spot lead/lag campaign")
CAMPAIGN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAMPAIGN
SPEC.loader.exec_module(CAMPAIGN)
