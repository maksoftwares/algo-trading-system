from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mt5_network_baseline_parses_authorization_pings_without_private_fields(tmp_path: Path):
    module = _load_module()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "20260528.log").write_text(
        "\n".join(
            [
                "DJ\t0\t00:34:16.081\tNetwork\t'121409': authorized on Capital.ComMena-Live through Access Point 2 (ping: 311.01 ms, build 5800)",
                "ND\t0\t00:34:16.081\tNetwork\t'121409': previous successful authorization performed from 110.226.120.64 on 2026.05.27 10:41:57",
                "NE\t0\t00:34:23.426\tNetwork\t'121409': authorized on Capital.ComMena-Live through Access Point 1 (ping: 172.80 ms, build 5800)",
            ]
        ),
        encoding="utf-16",
    )
    report_path = tmp_path / "baseline.md"

    output = module.generate_phase2_mt5_network_baseline(logs_dir, report_path)
    report = report_path.read_text(encoding="utf-8")

    assert output.status == "PASS"
    assert output.sample_count == 2
    assert output.best_ping_ms == 172.80
    assert output.latest_ping_ms == 172.80
    assert "Capital.ComMena-Live" in report
    assert "| 1 |" in report
    assert "121409" not in report
    assert "110.226.120.64" not in report


def test_mt5_network_baseline_pending_without_logs(tmp_path: Path):
    module = _load_module()
    report_path = tmp_path / "baseline.md"

    output = module.generate_phase2_mt5_network_baseline(tmp_path / "missing", report_path)

    assert output.status == "PENDING"
    assert output.sample_count == 0
    assert "Overall status: PENDING" in report_path.read_text(encoding="utf-8")


def test_mt5_network_baseline_script_is_evidence_only():
    script = (ROOT / "scripts" / "generate_phase2_mt5_network_baseline.py").read_text(encoding="utf-8")

    assert "OrderSend" not in script
    assert "CTrade" not in script
    assert "trade.Buy" not in script
    assert "trade.Sell" not in script


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_mt5_network_baseline.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_mt5_network_baseline", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_mt5_network_baseline"] = module
    spec.loader.exec_module(module)
    return module
