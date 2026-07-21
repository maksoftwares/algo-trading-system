from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_PATH = Path(__file__).with_name("ml_campaign.py")
_SPEC = importlib.util.spec_from_file_location("causal_hourly_action_router_v97_impl", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _IMPL
_SPEC.loader.exec_module(_IMPL)

for _name in _IMPL.__all__:
    globals()[_name] = getattr(_IMPL, _name)

__all__ = list(_IMPL.__all__)
