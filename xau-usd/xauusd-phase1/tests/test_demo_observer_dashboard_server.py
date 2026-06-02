from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_safe_static_path_serves_only_repo_files(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    dashboard = repo / "demo-observer-dashboard.html"
    dashboard.write_text("<html></html>", encoding="utf-8")

    assert module._safe_static_path(repo, "/demo-observer-dashboard.html") == dashboard.resolve()
    assert module._safe_static_path(repo, "/missing.html") is None
    assert module._safe_static_path(repo, "/../secret.txt") is None


def test_live_refresh_url_constant_is_exposed():
    module = _load_module()
    assert module.DEFAULT_LIVE_REFRESH_URL == "http://127.0.0.1:8777/demo-observer-dashboard.html"
    assert module.DEFAULT_PORT == 8777


def _load_module():
    script_dir = ROOT / "scripts"
    sys.path.insert(0, str(script_dir))
    try:
        path = script_dir / "serve_demo_observer_dashboard.py"
        spec = importlib.util.spec_from_file_location("serve_demo_observer_dashboard", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["serve_demo_observer_dashboard"] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(str(script_dir))
        except ValueError:
            pass
