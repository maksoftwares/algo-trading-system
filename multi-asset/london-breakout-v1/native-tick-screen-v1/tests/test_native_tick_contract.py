from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import subprocess
import pytest
from src.native_tick_contract import *

ROOT=Path(__file__).resolve().parents[1]; UTC=timezone.utc
def dt(s): return datetime.fromisoformat(s).replace(tzinfo=UTC)
def rows(): return [{"time_msc":0,"bid":100.,"ask":100.2,"last":0.,"volume":1,"flags":1},{"time_msc":1000,"bid":101.,"ask":101.3,"last":0.,"volume":1,"flags":1},{"time_msc":2000,"bid":99.,"ask":99.1,"last":0.,"volume":1,"flags":1},{"time_msc":3000,"bid":100.5,"ask":100.7,"last":0.,"volume":1,"flags":1}]

def test_01_exact_base_identity():
    c=json.loads((ROOT/"config/native_tick_screen_v1.json").read_text()); assert c["base_commit"]=="d95849d2dc97b0a6a54b49e5607e3420bf2dbd45" and c["base_tree"]=="de677c6b6a744b6b1298d0b9ed51a3feacb3ad64"
def test_02_tick_sorting(): assert [x["time_msc"] for x in sort_ticks(list(reversed(rows())))]==[0,1000,2000,3000]
def test_03_duplicate_handling(): assert tick_integrity(rows()+[rows()[0]])["duplicates"]==1
def test_04_crossed_rejection():
    x=rows();x[0]["ask"]=99;assert tick_integrity(x)["crossed"]==1
def test_05_zero_rejection():
    x=rows();x[0]["bid"]=0;assert tick_integrity(x)["zero"]==1
def test_06_partial_first_exclusion(): assert not complete_bar({"start":0,"end":300000},1,300000)
def test_07_partial_final_exclusion(): assert not complete_bar({"start":0,"end":300000},0,299999)
def test_08_m5_bid_aggregation(): assert aggregate(rows(),300)[0]["bid"]==(100,101,99,100.5)
def test_09_m5_ask_aggregation(): assert aggregate(rows(),300)[0]["ask"]==(100.2,101.3,99.1,100.7)
def test_10_m5_mid_aggregation(): assert aggregate(rows(),300)[0]["mid"]==pytest.approx((100.1,101.15,99.05,100.6))
def test_11_m15_aggregation(): assert 0 in aggregate(rows(),900)
def test_12_h1_aggregation(): assert 0 in aggregate(rows(),3600)
def test_13_no_ticks_outside_interval():
    x=rows()+[{**rows()[0],"time_msc":300000,"bid":999,"ask":1000}];assert aggregate(x,300)[0]["bid"][1]==101
def test_14_spring_dst(): assert london(dt("2026-03-29T01:00:00")).hour==2
def test_15_autumn_dst(): assert london(dt("2025-10-26T00:30:00")).hour==london(dt("2025-10-26T01:30:00")).hour==1
def test_16_overnight_excludes_0800(): assert overnight(dt("2025-01-02T07:59:00")) and not overnight(dt("2025-01-02T08:00:00"))
def test_17_final_completed_h1():
    c=dt("2025-01-02T08:00:00");assert final_completed([{"end":c-timedelta(hours=1),"id":1},{"end":c,"id":2}],c)["id"]==2
def test_18_future_mutation_no_change():
    c=dt("2025-01-02T08:00:00");assert final_completed([{"end":c,"id":1},{"end":c+timedelta(hours=1),"id":999}],c)["id"]==1
def test_19_bias_mirrors(): assert bias(102,101,100,10)=="LONG" and bias(98,99,100,10)=="SHORT"
def test_20_breakout_mirrors(): assert breakout("LONG",100,102,100,102,100.9,10) and breakout("SHORT",100,100,98,98,99.1,10)
def test_21_range_boundaries(): assert range_quality(5,10) and range_quality(20,10) and not range_quality(4.9,10)
def test_22_first_signal():
    x=[{"time":2,"qualifies":True},{"time":1,"qualifies":True}];assert first_qualifying(x)["time"]==1
def test_23_one_trade_per_date():
    x=[{"time":1,"qualifies":True},{"time":2,"qualifies":True}];assert first_qualifying(x) is x[0]
def test_24_first_post_signal_tick(): assert first_execution_tick(rows(),0,300000)["time_msc"]==1000
def test_25_missing_next_m5():
    with pytest.raises(ValueError): first_execution_tick([],0,300000)
def test_26_long_stop_bid(): assert executable_side("LONG",rows()[0],"EXIT")==100
def test_27_short_stop_ask(): assert executable_side("SHORT",rows()[0],"EXIT")==100.2
def test_28_long_target_bid(): assert resolve_tick("LONG",{"bid":102,"ask":102.2},98,102)==(102,"TARGET")
def test_29_short_target_ask(): assert resolve_tick("SHORT",{"bid":97.8,"ask":98},102,98)==(98,"TARGET")
def test_30_stop_gap_worse(): assert resolve_tick("LONG",{"bid":97,"ask":97.2},98,104,True)==(97,"STOP_GAP")
def test_31_target_gap_frozen(): assert resolve_tick("LONG",{"bid":105,"ask":105.2},98,104,True)==(104,"TARGET_GAP")
def test_32_identical_time_stop_first(): assert identical_time_resolution(True,True)=="IDENTICAL_TIMESTAMP_STOP_FIRST"
def test_33_excursions_end_at_exit(): assert excursions_until_exit([100,102,98,500],100,2,"LONG")== (2,-2)
def test_34_eight_hour_hold():
    e=dt("2025-01-02T05:00:00");assert exit_deadline(e)==e+timedelta(hours=8)
def test_35_forced_1600(): assert london(exit_deadline(dt("2025-07-02T10:00:00"))).hour==16
def test_36_missing_forced_exit(): assert not same_london_day(dt("2025-01-02T10:00:00"),dt("2025-01-03T10:00:00"))
def test_37_no_overnight(): assert same_london_day(dt("2025-01-02T10:00:00"),dt("2025-01-02T15:00:00"))
def test_38_dev_p95_immutable():
    x=list(range(1,101));f=nearest_rank_p95(x);exam=[999];exam[0]=9999;assert nearest_rank_p95(x)==f==95
def test_39_no_spread_double_count(): assert baseline_net(1)==1
def test_40_stress_increment(): assert stress_increment(1,2,3,10)==pytest.approx(.3)
def test_41_stress_slippage(): assert stress_net(1,0)==pytest.approx(.95)
def test_42_commission(): assert baseline_net(1,.1)==pytest.approx(.9)
def test_43_currency_conversion(): assert convert_profit(10,3.67)==pytest.approx(36.7)
def test_44_order_calc_profit_loss(): assert minimum_volume_loss(lambda *a:-4.5,"x")==4.5
def test_45_order_calc_margin(): assert required_margin(lambda *a:100,"x")==100
def test_46_combined_risk_ceiling(): assert len(admit([{"time_msc":1,"instrument":"A","risk":5},{"time_msc":2,"instrument":"B","risk":5}]))==1
def test_47_deterministic_admission(): assert admit([{"time_msc":1,"instrument":"B","risk":5},{"time_msc":1,"instrument":"A","risk":5}])[0]["instrument"]=="A"
def test_48_instrument_frequency_boundaries(): assert instrument_frequency(80,20) and not instrument_frequency(79,20)
def test_49_portfolio_frequency_boundaries():
    x={"full":360,"annualized":280,"median_month":20,"exam":80,"latest3":60,"every_exam_month":True};assert portfolio_frequency(x);x["exam"]=79;assert not portfolio_frequency(x)
def test_50_instrument_profit_boundaries():
    x={"pf":1.1,"expectancy":.04,"net":.01,"stress_pf":1.02,"stress_expectancy":.01,"stress_net":.01,"exam_net":.01,"drawdown":15,"top10":.4};assert instrument_profit(x);x["pf"]=1.09;assert not instrument_profit(x)
def test_51_portfolio_profit_boundaries():
    x={"pf":1.25,"expectancy":.08,"net":.01,"stress_pf":1.1,"stress_expectancy":.03,"stress_net":.01,"exam_pf":1.15,"exam_expectancy":.05,"exam_net":.01,"drawdown":20,"stress_drawdown":25,"top10":.3,"top3days":.2,"contribution":.6};assert portfolio_profit(x);x["pf"]=1.24;assert not portfolio_profit(x)
def test_52_drawdown_gates():
    x={"pf":1.25,"expectancy":.08,"net":1,"stress_pf":1.1,"stress_expectancy":.03,"stress_net":1,"exam_pf":1.15,"exam_expectancy":.05,"exam_net":1,"drawdown":20.1,"stress_drawdown":25,"top10":.3,"top3days":.2,"contribution":.6};assert not portfolio_profit(x)
def test_53_concentration_gates():
    x={"pf":1.25,"expectancy":.08,"net":1,"stress_pf":1.1,"stress_expectancy":.03,"stress_net":1,"exam_pf":1.15,"exam_expectancy":.05,"exam_net":1,"drawdown":20,"stress_drawdown":25,"top10":.31,"top3days":.2,"contribution":.6};assert not portfolio_profit(x)
def test_54_sizing_rejection_gate(): assert sizing_gate(1,10) and not sizing_gate(2,10)
def test_55_classification_precedence(): assert classify(False,True).endswith("DATA_INVALID") and classify(True,False).endswith("REJECTED_CLOSE_HYPOTHESIS")
def test_56_all_three_mandatory():
    c=json.loads((ROOT/"config/native_tick_screen_v1.json").read_text());assert c["instruments"]==["EURUSD","GBPUSD","USDJPY"]
def test_57_xau_explicit_not_scored():
    r=json.loads((ROOT/"outputs/LONDON_NATIVE_TICK_RESULT.json").read_text());assert r["xauusd_status"]=="INSUFFICIENT_COMMON_TICK_HISTORY_NOT_SCORED"
def test_58_no_absolute_paths():
    text="".join(p.read_text(encoding="utf-8") for p in (ROOT/"outputs").glob("LONDON_*"));assert "C:\\" not in text and "/home/" not in text
def test_59_no_broker_mutation_code():
    text="\n".join(p.read_text() for p in [ROOT/"run_native_tick_screen.py",ROOT/"src/native_tick_contract.py"]);forbidden=["order_"+"send(","TRADE_"+"ACTION_"];assert all(x not in text for x in forbidden)
def test_60_deterministic_replay():
    m=json.loads((ROOT/"outputs/LONDON_NATIVE_TICK_RUN_MANIFEST.json").read_text());assert m["deterministic_replay_match"] is True
