from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RESEARCH_ROOT = REPO_ROOT / "xau-usd" / "xauusd-fast-research"
PHASE1_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase1"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _target_guard(config: Mapping[str, Any]) -> Callable[[Any, Any], None]:
    expected = config["account"]

    def guard(account: Any, terminal: Any) -> None:
        if account is None or terminal is None:
            raise RuntimeError("MT5 account or terminal information is unavailable")
        if int(account.login) != int(expected["expected_login"]):
            raise RuntimeError(f"Wrong feed account: {account.login}")
        if str(account.server) != str(expected["expected_server"]):
            raise RuntimeError(f"Wrong feed server: {account.server}")
        if int(account.trade_mode) != 0:
            raise RuntimeError("Feed terminal is not logged into a demo account")
        if not bool(terminal.connected):
            raise RuntimeError("Feed terminal is disconnected")

    return guard


def _transport(config: Mapping[str, Any], name: str) -> Path:
    path = Path(config["runtime"]["directory"]) / "feeds" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _patch_frozen_source(
    module: Any,
    source_overrides: Mapping[str, Any],
) -> None:
    original = module.load_frozen

    def load_frozen(*args: Any, **kwargs: Any) -> Any:
        frozen = original(*args, **kwargs)
        frozen.package_config["source"].update(deepcopy(dict(source_overrides)))
        return frozen

    module.load_frozen = load_frozen


def run_r1_box(config: Mapping[str, Any]) -> dict[str, Any]:
    module = _load_module(
        "v60_v2_r1_box_runner",
        PHASE1_ROOT / "scripts" / "run_xau_specialist_shadow.py",
    )
    module.assert_demo_read_only = _target_guard(config)
    module.HISTORY_DAYS = 200
    return module.run_cycle(
        Path(config["account"]["terminal_exe"]), _transport(config, "r1_box")
    )


def run_r2_r3(config: Mapping[str, Any]) -> dict[str, Any]:
    package = RESEARCH_ROOT / "capital-core-same-period-shadow-v28"
    module = _load_module("v60_v2_r2_r3_runner", package / "run_shadow.py")
    module.assert_demo_read_only = _target_guard(config)
    _patch_frozen_source(
        module,
        {
            "terminal_exe": str(Path(config["account"]["terminal_exe"])),
            "runtime_directory": str(_transport(config, "r2_r3")),
            "account_login": int(config["account"]["expected_login"]),
            "account_server": str(config["account"]["expected_server"]),
            "history_days": 200,
        },
    )
    return module.run_cycle(REPO_ROOT, package)


def run_r1_pullback(config: Mapping[str, Any]) -> dict[str, Any]:
    package = RESEARCH_ROOT / "capital-r1-pullback-forward-v29"
    module = _load_module("v60_v2_r1_pullback_runner", package / "run_shadow.py")
    module.assert_demo_read_only = _target_guard(config)
    original = module.load_config

    def load_config() -> dict[str, Any]:
        value = deepcopy(original())
        value["source"].update(
            {
                "forward_terminal_exe": str(
                    Path(config["account"]["terminal_exe"])
                ),
                "forward_account_login": int(config["account"]["expected_login"]),
                "account_server": str(config["account"]["expected_server"]),
                "runtime_directory": str(_transport(config, "r1_pullback")),
            }
        )
        return value

    module.load_config = load_config
    return module.run_cycle()


def run_r4(config: Mapping[str, Any]) -> dict[str, Any]:
    package = RESEARCH_ROOT / "capital-r4-chop-forward-v34"
    module = _load_module("v60_v2_r4_runner", package / "run_shadow.py")
    module.assert_demo_read_only = _target_guard(config)
    files = Path(config["feeds"]["terminal_files_directory"])
    _patch_frozen_source(
        module,
        {
            "terminal_exe": str(Path(config["account"]["terminal_exe"])),
            "runtime_directory": str(_transport(config, "r4")),
            "tick_directory": str(files),
            "tick_filename_glob": str(config["feeds"]["tick_filename_glob"]),
            "account_login": int(config["account"]["expected_login"]),
            "account_server": str(config["account"]["expected_server"]),
            "history_days": 200,
        },
    )
    return module.run_cycle(REPO_ROOT, package)


def run_core_outcomes(config: Mapping[str, Any]) -> dict[str, Any]:
    package = RESEARCH_ROOT / "capital-core-causal-outcome-resolver-v40"
    previous_resolver = sys.modules.pop("resolver", None)
    try:
        module = _load_module(
            "v60_v2_core_outcome_runner", package / "run_resolver.py"
        )
        original = module.load_config

        def load_config(_path: Path | None = None) -> dict[str, Any]:
            path = (
                package
                / "config"
                / "capital_core_causal_outcome_resolver_v40.json"
            )
            value = deepcopy(original(path))
            value["source"].update(
                {
                    "tick_directory": str(
                        config["feeds"]["terminal_files_directory"]
                    ),
                    "tick_filename_glob": str(
                        config["feeds"]["tick_filename_glob"]
                    ),
                    "account_login": int(config["account"]["expected_login"]),
                    "account_server": str(config["account"]["expected_server"]),
                }
            )
            transports = {
                "v28": "r2_r3",
                "v29": "r1_pullback",
                "v34": "r4",
            }
            for stream, transport in transports.items():
                value["frozen_identity"][stream]["runtime_directory"] = str(
                    _transport(config, transport)
                )
            value["outputs"]["runtime_directory"] = str(
                _transport(config, "core_outcomes")
            )
            return value

        module.load_config = load_config
        return module.run_cycle(REPO_ROOT, package)
    finally:
        sys.modules.pop("resolver", None)
        if previous_resolver is not None:
            sys.modules["resolver"] = previous_resolver


def run_r5_components(config: Mapping[str, Any]) -> dict[str, Any]:
    package = RESEARCH_ROOT / "capital-r5-transition-forward-v35"
    module = _load_module("v60_v2_r5_components_runner", package / "run_shadow.py")
    module.assert_demo_read_only = _target_guard(config)
    _patch_frozen_source(
        module,
        {
            "terminal_exe": str(Path(config["account"]["terminal_exe"])),
            "runtime_directory": str(_transport(config, "r5_components")),
            "account_login": int(config["account"]["expected_login"]),
            "account_server": str(config["account"]["expected_server"]),
            "history_days": 200,
        },
    )
    return module.run_cycle(REPO_ROOT, package)


def run_r5_resolver(config: Mapping[str, Any]) -> dict[str, Any]:
    package = RESEARCH_ROOT / "capital-r5-causal-outcome-resolver-v38"
    module = _load_module("v60_v2_r5_resolver_runner", package / "run_resolver.py")
    original = module.load_config

    def load_config(_path: Path | None = None) -> dict[str, Any]:
        path = package / "config" / "capital_r5_causal_outcome_resolver_v38.json"
        value = deepcopy(original(path))
        value["source"].update(
            {
                "candidate_runtime_directory": str(
                    _transport(config, "r5_components")
                ),
                "tick_directory": str(config["feeds"]["terminal_files_directory"]),
                "tick_filename_glob": str(config["feeds"]["tick_filename_glob"]),
                "account_login": int(config["account"]["expected_login"]),
                "account_server": str(config["account"]["expected_server"]),
            }
        )
        value["outputs"]["runtime_directory"] = str(
            _transport(config, "r5_outcomes")
        )
        return value

    module.load_config = load_config
    return module.run_cycle(REPO_ROOT, package)


def run_r5_router(config: Mapping[str, Any]) -> dict[str, Any]:
    package = RESEARCH_ROOT / "capital-r5-causal-router-v39"
    module = _load_module("v60_v2_r5_router_runner", package / "run_router.py")
    original = module.load_config
    original_frozen = module.load_frozen

    def load_config(_path: Path | None = None) -> dict[str, Any]:
        path = package / "config" / "capital_r5_causal_router_v39.json"
        value = deepcopy(original(path))
        value["source"].update(
            {
                "v35_candidate_runtime_directory": str(
                    _transport(config, "r5_components")
                ),
                "v38_runtime_directory": str(_transport(config, "r5_outcomes")),
            }
        )
        value["outputs"]["runtime_directory"] = str(_transport(config, "r5_router"))
        return value

    module.load_config = load_config

    def load_frozen(value: dict[str, Any], repo_root: Path) -> Any:
        frozen = original_frozen(value, repo_root)
        frozen.v38_config["source"].update(
            {
                "account_login": int(config["account"]["expected_login"]),
                "account_server": str(config["account"]["expected_server"]),
            }
        )
        return frozen

    module.load_frozen = load_frozen
    return module.run_cycle(REPO_ROOT, package)


def run_core_feeds(config: Mapping[str, Any], *, include_slow: bool = True) -> dict[str, Any]:
    from addons import run_addon_feeds

    runners: list[tuple[str, Callable[[Mapping[str, Any]], dict[str, Any]]]] = [
        ("R1_BOX", run_r1_box),
        ("R1_PULLBACK", run_r1_pullback),
        ("R2_R3", run_r2_r3),
        ("R4", run_r4),
        ("CORE_OUTCOMES", run_core_outcomes),
        ("ADDONS", lambda value: run_addon_feeds(value, include_v25=include_slow)),
    ]
    if include_slow:
        runners.extend(
            [
                ("R5_COMPONENTS", run_r5_components),
                ("R5_RESOLVER", run_r5_resolver),
                ("R5_ROUTER", run_r5_router),
            ]
        )
    results: dict[str, Any] = {}
    checked_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    for name, runner in runners:
        try:
            results[name] = {"ok": True, "checked_at_utc": checked_at, "status": runner(config)}
        except Exception as exc:
            results[name] = {
                "ok": False,
                "checked_at_utc": checked_at,
                "error": f"{type(exc).__name__}: {exc}",
            }
    return {
        "schema_version": "xauusd_v60_canonical_feed_status_v2",
        "updated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "account_login": int(config["account"]["expected_login"]),
        "ml_used": False,
        "feeds": results,
        "all_requested_feeds_ok": all(item["ok"] for item in results.values()),
    }
