from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_config(
    repo_root: Path, v57_config_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    overlay = json.loads(v57_config_path.read_text(encoding="utf-8"))
    base_path = repo_root / str(overlay["base_config_path"])
    base = json.loads(base_path.read_text(encoding="utf-8"))
    resolved = dict(base)
    resolved["schema_version"] = overlay["schema_version"]
    resolved["overlay_sleeve"] = overlay["overlay_sleeve"]
    resolved["account"] = {**base["account"], **overlay["account_overrides"]}
    resolved["outputs"] = overlay["outputs"]
    resolved["research_controls"] = overlay["research_controls"]
    return resolved, overlay
