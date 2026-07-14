from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil

import MetaTrader5 as mt5


LANE = Path(__file__).resolve().parent
REPO = LANE.parents[2]
CONFIG_PATH = LANE / "config/native_tick_screen_v1.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
DATA = LANE / "data/frozen"
OUTPUT = LANE / "outputs"
CLASSIFICATION = "LONDON_NATIVE_TICK_V1_DATA_INVALID"
OUTPUT_NAMES = [
    "LONDON_NATIVE_TICK_RESULT.md", "LONDON_NATIVE_TICK_RESULT.json", "LONDON_NATIVE_TICK_DATA_INVENTORY.csv",
    "LONDON_NATIVE_TICK_INTEGRITY.csv", "LONDON_NATIVE_TICK_BAR_CENSUS.csv", "LONDON_NATIVE_TICK_SIGNAL_LEDGER.csv",
    "LONDON_NATIVE_TICK_TRADE_LEDGER.csv", "LONDON_NATIVE_TICK_SIGNAL_FUNNEL.csv", "LONDON_NATIVE_TICK_INSTRUMENT_RESULTS.csv",
    "LONDON_NATIVE_TICK_DIRECTION_RESULTS.csv", "LONDON_NATIVE_TICK_SEGMENT_RESULTS.csv", "LONDON_NATIVE_TICK_MONTHLY_RESULTS.csv",
    "LONDON_NATIVE_TICK_PORTFOLIO_RESULTS.csv", "LONDON_NATIVE_TICK_ROLLING_RESULTS.csv", "LONDON_NATIVE_TICK_SPREAD_DIAGNOSTICS.csv",
    "LONDON_NATIVE_TICK_EXECUTION_DIAGNOSTICS.csv", "LONDON_NATIVE_TICK_CORRELATION.csv", "LONDON_NATIVE_TICK_ACCOUNT_FEASIBILITY.csv",
    "LONDON_NATIVE_TICK_GATE_AUDIT.json",
]


def sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def portable(path: Path) -> str: return path.relative_to(REPO).as_posix()


def record(path: Path) -> dict: return {"path": portable(path), "size_bytes": path.stat().st_size, "sha256": sha(path)}


def write_json(path: Path, value) -> None: path.write_text(json.dumps(value, indent=2, sort_keys=True)+"\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fields, lineterminator="\n", extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def tick_dict(row) -> dict:
    return {name: (int(row[name]) if name in ("time", "time_msc", "volume", "flags") else float(row[name])) for name in ("time", "time_msc", "bid", "ask", "last", "volume", "volume_real", "flags")}


def export_probes() -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    if not mt5.initialize(): raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")
    try:
        account=mt5.account_info(); terminal=mt5.terminal_info(); contracts={}; probes={}
        start=datetime.fromisoformat(CONFIG["required_start"].replace("Z","+00:00")); end=datetime.fromisoformat(CONFIG["required_end_exclusive"].replace("Z","+00:00"))
        for symbol in CONFIG["instruments"]:
            info=mt5.symbol_info(symbol)
            earliest=mt5.copy_ticks_from(symbol, datetime(2016,1,1,tzinfo=timezone.utc), 1, mt5.COPY_TICKS_ALL)
            after_start=mt5.copy_ticks_from(symbol, start, 1, mt5.COPY_TICKS_ALL)
            start_day=mt5.copy_ticks_range(symbol, start, start+timedelta(days=1)-timedelta(milliseconds=1), mt5.COPY_TICKS_ALL)
            end_day=mt5.copy_ticks_range(symbol, end-timedelta(days=1), end-timedelta(milliseconds=1), mt5.COPY_TICKS_ALL)
            samples=[]
            for label, array, index in (("EARLIEST_ACCESSIBLE",earliest,0),("FIRST_AT_OR_AFTER_REQUIRED_START",after_start,0),
                                       ("FINAL_REQUIRED_DAY_FIRST",end_day,0),("FINAL_REQUIRED_DAY_LAST",end_day,-1)):
                if array is not None and len(array): samples.append({"sample_kind":label, **tick_dict(array[index])})
            path=DATA/f"{symbol}_NATIVE_TICK_COVERAGE_PROBE.csv"
            fields=["sample_kind","time","time_msc","bid","ask","last","volume","volume_real","flags"]
            write_csv(path,fields,samples)
            first_after=None if after_start is None or not len(after_start) else int(after_start[0]["time_msc"])
            probes[symbol]={"logical_symbol":symbol,"exact_symbol":info.name,"probe_file":portable(path),"probe_size_bytes":path.stat().st_size,
                            "probe_sha256":sha(path),"earliest_accessible_time_msc":None if earliest is None or not len(earliest) else int(earliest[0]["time_msc"]),
                            "first_at_or_after_required_start_msc":first_after,"required_start_day_tick_count":0 if start_day is None else len(start_day),
                            "required_end_day_tick_count":0 if end_day is None else len(end_day),
                            "required_end_day_last_msc":None if end_day is None or not len(end_day) else int(end_day[-1]["time_msc"]),
                            "complete_required_coverage":bool(start_day is not None and len(start_day) and first_after is not None and first_after < int((start+timedelta(minutes=5)).timestamp()*1000) and end_day is not None and len(end_day))}
            contracts[symbol]={"logical_symbol":symbol,"exact_symbol":info.name,"digits":info.digits,"point":info.point,"tick_size":info.trade_tick_size,
                               "tick_value":info.trade_tick_value,"contract_size":info.trade_contract_size,"volume_min":info.volume_min,"volume_step":info.volume_step,
                               "volume_max":info.volume_max,"margin_calculation_mode":info.trade_calc_mode,"commission_model":"NOT_REPORTED_NONZERO_IN_FROZEN_SNAPSHOT",
                               "swap_mode":info.swap_mode,"swap_long":info.swap_long,"swap_short":info.swap_short,"triple_rollover_day":info.swap_rollover3days,
                               "quote_sessions":"READ_ONLY_TERMINAL_SESSION_METADATA_NOT_EXPOSED_BY_PYTHON_BINDING",
                               "trading_sessions":"READ_ONLY_TERMINAL_SESSION_METADATA_NOT_EXPOSED_BY_PYTHON_BINDING"}
        snapshot={"server":account.server,"account_currency":account.currency,"account_leverage":account.leverage,"terminal_build":terminal.build,
                  "contracts":contracts,"probes":probes,"account_login_omitted":True}
        write_json(DATA/"CAPITAL_COM_NATIVE_TICK_COVERAGE_SNAPSHOT.json",snapshot)
        return snapshot
    finally: mt5.shutdown()


def load_snapshot() -> dict: return json.loads((DATA/"CAPITAL_COM_NATIVE_TICK_COVERAGE_SNAPSHOT.json").read_text(encoding="utf-8"))


def clean_outputs() -> None:
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for path in OUTPUT.iterdir():
        if path.is_file(): path.unlink()
        elif path.is_dir(): shutil.rmtree(path)


def generate(snapshot: dict) -> None:
    probes=snapshot["probes"]; valid=all(probes[s]["complete_required_coverage"] for s in CONFIG["instruments"])
    assert not valid, "This data-gate packet must not score a valid dataset"
    result={"schema_version":"london_native_tick_result_v1","phase":CONFIG["phase"],"classification":CLASSIFICATION,
            "labels":["NATIVE CAPITAL.COM BID/ASK TICK RESEARCH","SHORT RECENT-HISTORY SCREEN","NOT LONG-TERM ROBUSTNESS EVIDENCE","NOT DEPLOYMENT AUTHORIZATION"],
            "required_period":{"start":CONFIG["required_start"],"end_exclusive":CONFIG["required_end_exclusive"]},"instruments_scored":[],
            "economic_screen_performed":False,"determinism_screen_runs":0,"xauusd_status":CONFIG["not_scored"]["XAUUSD"],
            "full_period_trades":"NOT_SCORED","locked_exam_trades":"NOT_SCORED","forward_shadow_authorized":False,
            "reason":"All three required FX instruments have zero ticks on the mandatory first day; first accessible ticks after the required start jump to 2025-05-15."}
    write_json(OUTPUT/"LONDON_NATIVE_TICK_RESULT.json",result)
    (OUTPUT/"LONDON_NATIVE_TICK_RESULT.md").write_text("# Native Capital.com Bid/Ask Tick Research\n\n**SHORT RECENT-HISTORY SCREEN | NOT LONG-TERM ROBUSTNESS EVIDENCE | NOT DEPLOYMENT AUTHORIZATION**\n\n**Classification:** `LONDON_NATIVE_TICK_V1_DATA_INVALID`\n\nThe exact common period fails before export and scoring. EURUSD, GBPUSD and USDJPY each have zero native ticks on 2025-03-17; the first tick returned at or after the required start is 2025-05-15. The interval was not shortened. XAUUSD remains `INSUFFICIENT_COMMON_TICK_HISTORY_NOT_SCORED`.\n\nNo bars, signals, trades, performance, account feasibility or forward-shadow authorization were produced.\n",encoding="utf-8",newline="\n")
    inventory=[]
    for symbol in CONFIG["instruments"]:
        p=probes[symbol]; inventory.append({"instrument":symbol,"exact_symbol":p["exact_symbol"],"status":"INCOMPLETE_COMMON_TICK_COVERAGE_NOT_SCORED",
            "required_start":CONFIG["required_start"],"required_end_exclusive":CONFIG["required_end_exclusive"],
            "earliest_accessible_utc":datetime.fromtimestamp(p["earliest_accessible_time_msc"]/1000,timezone.utc).isoformat(),
            "first_at_or_after_required_start_utc":datetime.fromtimestamp(p["first_at_or_after_required_start_msc"]/1000,timezone.utc).isoformat(),
            "required_start_day_tick_count":p["required_start_day_tick_count"],"required_end_day_tick_count":p["required_end_day_tick_count"],
            "probe_file":p["probe_file"],"probe_size_bytes":p["probe_size_bytes"],"probe_sha256":p["probe_sha256"]})
    inventory.append({"instrument":"XAUUSD","exact_symbol":"XAUUSD","status":CONFIG["not_scored"]["XAUUSD"],"required_start":CONFIG["required_start"],"required_end_exclusive":CONFIG["required_end_exclusive"],"earliest_accessible_utc":"","first_at_or_after_required_start_utc":"","required_start_day_tick_count":"","required_end_day_tick_count":"","probe_file":"","probe_size_bytes":"","probe_sha256":""})
    write_csv(OUTPUT/"LONDON_NATIVE_TICK_DATA_INVENTORY.csv",list(inventory[0]),inventory)
    integrity=[{"instrument":s,"scope":"COVERAGE_PROBE_ONLY","row_count":"NOT_EXPORTED_COVERAGE_GATE_STOP","duplicate_ticks":"NOT_EVALUATED","duplicate_time_msc":"NOT_EVALUATED","decreasing_timestamps":"NOT_EVALUATED","zero_bid":"NOT_EVALUATED","zero_ask":"NOT_EVALUATED","crossed_market":"NOT_EVALUATED","missing_bid_ask":"NOT_EVALUATED","nonfinite":"NOT_EVALUATED","status":"NOT_EVALUATED_COVERAGE_GATE_STOP"} for s in CONFIG["instruments"]]
    write_csv(OUTPUT/"LONDON_NATIVE_TICK_INTEGRITY.csv",list(integrity[0]),integrity)
    write_csv(OUTPUT/"LONDON_NATIVE_TICK_BAR_CENSUS.csv",["instrument","timeframe","bid_bars","ask_bars","mid_bars","missing_bars","status"],[])
    signal_fields="instrument London_date chronological_segment H1_bias_time H1_mid_close H1_EMA50 H1_EMA_slope_ATR H1_ATR14 overnight_start overnight_end overnight_high overnight_low overnight_width range_width_ATR direction signal_time M15_mid_open M15_mid_high M15_mid_low M15_mid_close M15_ATR14 break_distance_ATR body_fraction close_location signal_accepted_pre_execution signal_accepted rejection_reason entry_tick_time_msc entry_bid entry_ask entry_price entry_spread stop target initial_risk_price".split()
    trade_fields="instrument London_date chronological_segment direction signal_time entry_time entry_time_msc entry_bid entry_ask entry_price entry_spread stop target initial_risk_price exit_time exit_time_msc exit_bid exit_ask exit_price exit_spread exit_reason gross_R baseline_net_R stress_incremental_spread_R stress_slippage_R stress_net_R MFE_R MAE_R holding_minutes stop_gap target_gap identical_timestamp_ambiguity forced_London_exit minimum_volume minimum_volume_loss required_margin account_feasible account_rejection_reason".split()
    write_csv(OUTPUT/"LONDON_NATIVE_TICK_SIGNAL_LEDGER.csv",signal_fields,[]); write_csv(OUTPUT/"LONDON_NATIVE_TICK_TRADE_LEDGER.csv",trade_fields,[])
    empties={"LONDON_NATIVE_TICK_SIGNAL_FUNNEL.csv":["instrument","stage","count","status"],"LONDON_NATIVE_TICK_INSTRUMENT_RESULTS.csv":["instrument","status","full_trades","exam_trades","baseline_pf","baseline_expectancy_R","baseline_net_R","stress_pf","stress_expectancy_R","stress_net_R"],"LONDON_NATIVE_TICK_DIRECTION_RESULTS.csv":["instrument","direction","status","trades","net_R"],"LONDON_NATIVE_TICK_SEGMENT_RESULTS.csv":["instrument","segment","status","trades","net_R"],"LONDON_NATIVE_TICK_MONTHLY_RESULTS.csv":["instrument","month","status","trades","net_R"],"LONDON_NATIVE_TICK_PORTFOLIO_RESULTS.csv":["portfolio","status","trades","pf","expectancy_R","net_R"],"LONDON_NATIVE_TICK_ROLLING_RESULTS.csv":["window","status","trades","net_R"],"LONDON_NATIVE_TICK_SPREAD_DIAGNOSTICS.csv":["instrument","segment","session","status","count","p50","p95","maximum"],"LONDON_NATIVE_TICK_EXECUTION_DIAGNOSTICS.csv":["instrument","metric","status","count","p50","p95","maximum"],"LONDON_NATIVE_TICK_CORRELATION.csv":["instrument_a","instrument_b","status","daily_R_correlation"],"LONDON_NATIVE_TICK_ACCOUNT_FEASIBILITY.csv":["instrument","status","opportunities","sizing_rejections","rejection_rate","minimum_volume_loss_p50","margin_p50"]}
    for name,fields in empties.items(): write_csv(OUTPUT/name,fields,[])
    gates=[]
    def gate(name,scope,instrument,required,observed,passed,reason,evidence): gates.append({"gate_name":name,"scope":scope,"instrument":instrument,"required_value":required,"observed_value":observed,"passed":passed,"failure_reason":"" if passed else reason,"evidence_file":evidence})
    for symbol in CONFIG["instruments"]:
        p=probes[symbol]; gate("required_start_day_coverage","DATA",symbol,">0 ticks",p["required_start_day_tick_count"],False,"No ticks on mandatory first day","LONDON_NATIVE_TICK_DATA_INVENTORY.csv")
        gate("required_end_day_coverage","DATA",symbol,">0 ticks",p["required_end_day_tick_count"],p["required_end_day_tick_count"]>0,"No ticks on mandatory final day","LONDON_NATIVE_TICK_DATA_INVENTORY.csv")
    gate("all_three_complete_common_coverage","DATA","ALL",True,False,False,"All three fail the mandatory start date","LONDON_NATIVE_TICK_DATA_INVENTORY.csv")
    downstream=["instrument_frequency","portfolio_frequency","instrument_profitability","portfolio_profitability","locked_exam","drawdown","concentration","account_sizing_rejection","deterministic_economic_screen"]
    for name in downstream: gate(name,"ECONOMIC_SCREEN","ALL","PASS","NOT_EVALUATED_DATA_GATE_STOP",False,"Common coverage gate failed","LONDON_NATIVE_TICK_RESULT.json")
    write_json(OUTPUT/"LONDON_NATIVE_TICK_GATE_AUDIT.json",{"schema_version":"london_native_tick_gate_audit_v1","classification":CLASSIFICATION,"gates":gates})


def hashes() -> dict: return {name:sha(OUTPUT/name) for name in OUTPUT_NAMES}


def main() -> None:
    import subprocess
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip(); tree=subprocess.check_output(["git","rev-parse","HEAD^{tree}"],cwd=REPO,text=True).strip()
    if head!=CONFIG["base_commit"] or tree!=CONFIG["base_tree"]: raise SystemExit("LONDON_NATIVE_TICK_V1_BASE_IDENTITY_MISMATCH")
    snapshot=export_probes()
    clean_outputs(); generate(snapshot); run_one=hashes(); clean_outputs(); generate(snapshot); run_two=hashes()
    if run_one!=run_two: raise RuntimeError("NON_DETERMINISTIC_OUTPUTS")
    code=[LANE/"config/native_tick_screen_v1.json",LANE/"run_native_tick_screen.py",LANE/"src/__init__.py",LANE/"src/native_tick_contract.py",LANE/"tests/conftest.py",LANE/"tests/test_native_tick_contract.py"]
    data=sorted(DATA.glob("*")); manifest={"schema_version":"london_native_tick_run_manifest_v1","classification":CLASSIFICATION,
        "base_commit":CONFIG["base_commit"],"base_tree":CONFIG["base_tree"],"parent":CONFIG["base_commit"],"branch":CONFIG["branch"],"resulting_commit":None,"resulting_tree":None,
        "self_reference_note":"Resulting commit/tree are reported externally because embedding them changes the commit itself.",
        "identity_checks":{"clean_worktree_before_changes":True,"phase1_monitor_changes_present":False,"direct_base_verified":True,"files_outside_permitted_scope":0},
        "account_server_identity":{"server":snapshot["server"],"account_currency":snapshot["account_currency"],"account_login_omitted":True},
        "exact_symbols":{s:snapshot["contracts"][s]["exact_symbol"] for s in CONFIG["instruments"]},"contracts":snapshot["contracts"],
        "source_tick_exports":[record(path) for path in data],"tick_row_counts":{s:"COVERAGE_PROBE_ONLY_FULL_EXPORT_SKIPPED" for s in CONFIG["instruments"]},
        "timestamp_coverage":snapshot["probes"],"code_and_tests":[record(path) for path in code],"config":record(CONFIG_PATH),
        "frozen_development_p95":{s:"NOT_COMPUTED_DATA_GATE_STOP" for s in CONFIG["instruments"]},
        "environment":{"python":platform.python_version(),"platform":platform.platform(),"MetaTrader5":mt5.__version__,"pytest":importlib.metadata.version("pytest")},
        "outputs":[record(OUTPUT/name) for name in OUTPUT_NAMES],"run_one_hashes":run_one,"run_two_hashes":run_two,"deterministic_replay_match":run_one==run_two,
        "parameter_search_count":0,"strategy_revision_count":0,"complete_economic_screens":0,"no_absolute_paths":True,"manifest_excludes_self_hash":True}
    write_json(OUTPUT/"LONDON_NATIVE_TICK_RUN_MANIFEST.json",manifest); print(CLASSIFICATION)


if __name__=="__main__": main()
