from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
OVERLAY = ROOT / "config" / "overlay.json"
OUTPUTS = ROOT / "outputs"


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
    if any(overlay["authorization"].values()):
        raise ValueError("V8 research overlay must remain disarmed")
    for name in ("parent_config", "dynamic_runner"):
        item = overlay[name]
        actual = sha256(resolve(item["path"]))
        if actual != item["sha256"]:
            raise ValueError(f"Overlay input identity changed: {name}: {actual}")
    expanded = json.loads(resolve(overlay["parent_config"]["path"]).read_text())
    expanded["schema_version"] = "v60_dynamic_health_margin_union_v8"
    expanded["v2_policy_overrides"] = overlay["v2_policy_overrides"]
    expanded["evidence_status"] = "RETROSPECTIVE_POSTHOC_FORWARD_CONFIRMATION_REQUIRED"
    runner_path = resolve(overlay["dynamic_runner"]["path"])
    spec = importlib.util.spec_from_file_location("v60_dynamic_v8_runner", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load dynamic runner: {runner_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["v60_dynamic_v8_runner"] = module
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="v60-dynamic-v8-config-") as temporary:
        expanded_path = Path(temporary) / "experiment.json"
        expanded_path.write_text(json.dumps(expanded), encoding="utf-8")
        module.CONFIG = expanded_path
        module.OUTPUTS = OUTPUTS
        return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
