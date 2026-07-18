from __future__ import annotations

import configparser
import hashlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "mt5_five_specialist_replay_v1.json"
SCHEDULE_COLUMNS = [
    "signal_id",
    "specialist_id",
    "server_entry_time",
    "direction",
    "risk_distance",
    "target_r",
    "hold_minutes",
    "source_entry_time_utc",
    "source_entry_price",
    "source_stop",
    "source_target",
    "source_stress_r",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def source_path(config: dict[str, Any], key: str) -> Path:
    return REPO / str(config["sources"][key])


def load_source_frames(
    config: dict[str, Any],
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    return {
        "r23": (
            pd.read_parquet(source_path(config, "r23_trades")),
            pd.read_parquet(source_path(config, "r23_candidates")),
        ),
        "r4": (
            pd.read_parquet(source_path(config, "r4_trades")),
            pd.read_parquet(source_path(config, "r4_candidates")),
        ),
        "r5": (
            pd.read_parquet(source_path(config, "r5_trades")),
            pd.read_parquet(source_path(config, "r5_candidates")),
        ),
    }


def build_schedule(
    definition: dict[str, Any],
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame]],
    config: dict[str, Any],
) -> pd.DataFrame:
    trades, candidates = frames[str(definition["source"])]
    selected = trades.copy()
    filter_column = definition.get("source_filter_column")
    if filter_column:
        selected = selected.loc[
            selected[str(filter_column)].eq(definition["source_filter_value"])
        ]
    if "attempt_no" in definition:
        selected = selected.loc[
            selected["attempt_no"].eq(int(definition["attempt_no"]))
        ]

    start = pd.Timestamp(config["window"]["start_utc"])
    end = pd.Timestamp(config["window"]["end_exclusive_utc"])
    selected = selected.loc[
        selected["scheduled_entry_time"].ge(start)
        & selected["scheduled_entry_time"].lt(end)
    ].copy()
    candidate_geometry = candidates[["candidate_id", "hold_hours"]].copy()
    candidate_geometry["target_r"] = (
        candidates["target_r"].astype(float) if "target_r" in candidates else 0.0
    )
    selected = selected.merge(
        candidate_geometry,
        on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    if selected[["hold_hours"]].isna().any().any():
        raise ValueError(f"missing horizon for {definition['specialist_id']}")

    if str(definition["source"]) == "r23":
        selected["target_r"] = 0.0
    timezone = ZoneInfo(str(config["mt5"]["server_timezone"]))
    server_times = selected["scheduled_entry_time"].dt.tz_convert(timezone)
    source_target = (
        selected["target"]
        if "target" in selected
        else pd.Series(0.0, index=selected.index)
    )
    schedule = pd.DataFrame(
        {
            "signal_id": selected["candidate_id"].astype(str),
            "specialist_id": str(definition["specialist_id"]),
            "server_entry_time": server_times.dt.strftime("%Y.%m.%d %H:%M:%S"),
            "direction": selected["direction"].astype(str),
            "risk_distance": selected["risk_price"].astype(float),
            "target_r": selected["target_r"].fillna(0.0).astype(float),
            "hold_minutes": selected["hold_hours"].astype(float) * 60.0,
            "source_entry_time_utc": selected["entry_time"].dt.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "source_entry_price": selected["entry_price"].astype(float),
            "source_stop": selected["stop"].astype(float),
            "source_target": source_target.fillna(0.0).astype(float),
            "source_stress_r": selected["stress_net_r"].astype(float),
        }
    )
    schedule = schedule.sort_values(["server_entry_time", "signal_id"]).reset_index(
        drop=True
    )
    expected = int(definition["expected_schedule_rows"])
    if len(schedule) != expected:
        raise ValueError(
            f"{definition['specialist_id']} schedule rows={len(schedule)}, expected={expected}"
        )
    return schedule[SCHEDULE_COLUMNS]


def build_combined_schedule(
    schedules: dict[str, pd.DataFrame], definition: dict[str, Any]
) -> pd.DataFrame:
    nonempty = [frame.copy() for frame in schedules.values() if not frame.empty]
    if not nonempty:
        return pd.DataFrame(columns=SCHEDULE_COLUMNS)
    combined = pd.concat(nonempty, ignore_index=True)
    source_ids = combined["specialist_id"].astype(str)
    combined["signal_id"] = source_ids + "__" + combined["signal_id"].astype(str)
    combined["specialist_id"] = str(definition["specialist_id"])
    combined = combined.sort_values(["server_entry_time", "signal_id"]).reset_index(
        drop=True
    )
    expected = int(definition["expected_schedule_rows"])
    if len(combined) != expected:
        raise ValueError(f"combined schedule rows={len(combined)}, expected={expected}")
    return combined[SCHEDULE_COLUMNS]


def write_ini(path: Path, parser: configparser.ConfigParser) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        parser.write(handle, space_around_delimiters=False)


def native_r1_config(
    definition: dict[str, Any], config: dict[str, Any]
) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    template = Path(str(definition["template"]))
    if not parser.read(template, encoding="utf-8"):
        raise FileNotFoundError(template)
    tester = parser["Tester"]
    tester["Model"] = str(config["mt5"]["model"])
    tester["FromDate"] = str(config["window"]["tester_from_date"])
    tester["ToDate"] = str(config["window"]["tester_to_date"])
    tester["Visual"] = str(config["mt5"]["visual"])
    tester["Report"] = f"Reports\\{definition['report']}"
    tester["ReplaceReport"] = "1"
    tester["ShutdownTerminal"] = str(config["mt5"]["shutdown_terminal"])
    inputs = parser["TesterInputs"]
    inputs["InpRunId"] = str(definition["run_id"])
    slug = str(definition["component_id"]).lower()
    for key, suffix in (
        ("InpStartupLogFileName", "startup"),
        ("InpSignalLogFileName", "signals"),
        ("InpOrderLogFileName", "orders"),
        ("InpManagementLogFileName", "management"),
        ("InpDealLogFileName", "deals"),
    ):
        inputs[key] = f"five_specialist_3m_{slug}_{suffix}.csv"
    return parser


def replay_config(
    definition: dict[str, Any], schedule_name: str, config: dict[str, Any]
) -> configparser.ConfigParser:
    mt5 = config["mt5"]
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser["Common"] = {
        "Login": str(mt5["login"]),
        "Server": str(mt5["server"]),
        "KeepPrivate": "1",
        "NewsEnable": "0",
    }
    specialist_id = str(definition["specialist_id"])
    report_name = f"FIVE_SPECIALIST_MT5_3M_{specialist_id}"
    parser["Tester"] = {
        "Expert": "FiveSpecialistSignalReplay.ex5",
        "Symbol": str(mt5["symbol"]),
        "Period": str(mt5["period"]),
        "Optimization": "0",
        "Model": str(mt5["model"]),
        "Dates": "2",
        "FromDate": str(config["window"]["tester_from_date"]),
        "ToDate": str(config["window"]["tester_to_date"]),
        "ForwardMode": "0",
        "Deposit": f"{float(mt5['deposit']):.2f}",
        "Currency": str(mt5["currency"]),
        "ProfitInPips": "0",
        "Leverage": str(mt5["leverage"]),
        "ExecutionMode": "0",
        "OptimizationCriterion": "0",
        "Visual": str(mt5["visual"]),
        "Report": f"Reports\\{report_name}",
        "ReplaceReport": "1",
        "ShutdownTerminal": str(mt5["shutdown_terminal"]),
        "UseLocal": "1",
        "UseRemote": "0",
        "UseCloud": "0",
    }
    parser["TesterInputs"] = {
        "InpScheduleFile": schedule_name,
        "InpSpecialistId": specialist_id,
        "InpExpectedLogin": str(mt5["login"]),
        "InpExpectedServerMarker": "Demo",
        "InpMagicNumber": str(definition["magic"]),
        "InpFixedLots": f"{float(mt5['fixed_lots']):.2f}",
        "InpDeviationPoints": "100",
        "InpMaxEntryDelaySeconds": "600",
        "InpEventLogFile": f"five_specialist_3m_{specialist_id.lower()}_events.csv",
    }
    return parser


def main() -> int:
    config = load_config()
    frames = load_source_frames(config)
    outputs = ROOT / "outputs"
    schedules_dir = outputs / "schedules"
    configs_dir = outputs / "tester_configs"
    schedules_dir.mkdir(parents=True, exist_ok=True)
    configs_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, dict[str, Any]] = {}
    schedule_frames: dict[str, pd.DataFrame] = {}
    for definition in config["replay_specialists"]:
        schedule = build_schedule(definition, frames, config)
        specialist_id = str(definition["specialist_id"])
        schedule_frames[specialist_id] = schedule
        schedule_name = f"FIVE_SPECIALIST_MT5_3M_{specialist_id}_SCHEDULE.csv"
        schedule_path = schedules_dir / schedule_name
        schedule.to_csv(schedule_path, index=False, lineterminator="\n")
        ini_path = configs_dir / f"FIVE_SPECIALIST_MT5_3M_{specialist_id}.ini"
        write_ini(ini_path, replay_config(definition, schedule_name, config))
        artifacts[specialist_id] = {
            "mode": "MT5_REAL_TICK_EXECUTION_SCHEDULE_REPLAY",
            "schedule": str(schedule_path.relative_to(ROOT)),
            "schedule_rows": int(len(schedule)),
            "schedule_sha256": sha256_file(schedule_path),
            "tester_config": str(ini_path.relative_to(ROOT)),
            "tester_config_sha256": sha256_file(ini_path),
            "reference_net_usd": float(definition["reference_net_usd"]),
        }

    combined_definition = config["combined_replay"]
    combined_schedule = build_combined_schedule(schedule_frames, combined_definition)
    combined_id = str(combined_definition["specialist_id"])
    combined_schedule_name = f"FIVE_SPECIALIST_MT5_3M_{combined_id}_SCHEDULE.csv"
    combined_schedule_path = schedules_dir / combined_schedule_name
    combined_schedule.to_csv(combined_schedule_path, index=False, lineterminator="\n")
    combined_ini_path = configs_dir / f"FIVE_SPECIALIST_MT5_3M_{combined_id}.ini"
    write_ini(
        combined_ini_path,
        replay_config(combined_definition, combined_schedule_name, config),
    )
    combined_artifact = {
        "mode": "MT5_REAL_TICK_COMBINED_EXECUTION_SCHEDULE_REPLAY",
        "schedule": str(combined_schedule_path.relative_to(ROOT)),
        "schedule_rows": int(len(combined_schedule)),
        "schedule_sha256": sha256_file(combined_schedule_path),
        "tester_config": str(combined_ini_path.relative_to(ROOT)),
        "tester_config_sha256": sha256_file(combined_ini_path),
    }

    native_configs: list[dict[str, Any]] = []
    for definition in config["native_r1"]:
        ini_path = (
            configs_dir / f"FIVE_SPECIALIST_MT5_3M_{definition['component_id']}.ini"
        )
        write_ini(ini_path, native_r1_config(definition, config))
        native_configs.append(
            {
                "component_id": definition["component_id"],
                "mode": "NATIVE_MT5_SIGNAL_GENERATION_REAL_TICKS",
                "tester_config": str(ini_path.relative_to(ROOT)),
                "tester_config_sha256": sha256_file(ini_path),
                "template": definition["template"],
                "template_sha256": sha256_file(Path(definition["template"])),
            }
        )

    source_hashes = {
        key: {
            "path": str(config["sources"][key]),
            "sha256": sha256_file(source_path(config, key)),
        }
        for key in config["sources"]
    }
    manifest = {
        "schema_version": config["schema_version"],
        "window": config["window"],
        "mt5": config["mt5"],
        "replay_ea_source": {
            "path": "mt5/FiveSpecialistSignalReplay.mq5",
            "sha256": sha256_file(ROOT / "mt5" / "FiveSpecialistSignalReplay.mq5"),
        },
        "native_r1_components": native_configs,
        "replay_specialists": artifacts,
        "combined_replay": combined_artifact,
        "source_files": source_hashes,
        "research_controls": config["research_controls"],
    }
    manifest_path = outputs / "FIVE_SPECIALIST_MT5_3M_PACKET_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
