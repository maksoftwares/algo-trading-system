from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")

EA_NAME = "A1XauM5MomentumContinuationExecutor"
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
ACCOUNT_LOGIN = "1025742"
SERVER = "Capital.ComMena-Demo"
SYMBOL = "XAUUSD"

DEFAULT_VARIANT = "rr2_long_only"
VARIANT_CONFIGS: dict[str, dict[str, Any]] = {
    "rr2_long_only": {
        "title": "A1 XAU M5 Momentum RR2 Long-Only Forward Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT / "docs" / "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_2026_07_02.md",
        "spec_sha256": "70f64b6c6a2608659597563aa039279793ed690f4762d8248254463b388c4026",
        "run_id": "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702",
        "magic": 932200,
        "order_comment": "A1_XAU_M5_MOM",
        "kill_switch": "a1_xau_m5_momentum_rr2_kill_switch.txt",
        "compile_tag": "rr2_long_only",
        "backup_tag": "a1_xau_m5_momentum_rr2_long_only_before_update",
        "rule": "rr2_long_only_h1_h4_atr15_no0910",
        "forward_variant": "rr_2p0_long_only_h1_h4_atr15_no0910",
        "direction_rule": "LONG only, H1+H4 EMA20/50 alignment required, server hours 09 and 10 blocked",
        "max_estimated_cost_r": "0.15",
        "max_trades_per_day": "6",
        "cooldown_minutes": "10",
        "min_atr_absolute_for_entry": "1.5",
        "risk_reward": "2.00",
        "blocked_entry_hours": "9,10",
    },
    "freq_v4": {
        "title": "A1 XAU M5 Momentum Frequency-First V4 Forward Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_FORWARD_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_LONG_RR0P7_V4_COMBO_RANK1_FORWARD_2026_07_02.md",
        "spec_sha256": "2b5fe5ba37f5649353534a06f682c328f4c410ebd2ef95a45986e3172b19db3b",
        "run_id": "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_20260702",
        "magic": 932200,
        "order_comment": "A1_XAU_M5_MOM_V4",
        "kill_switch": "a1_xau_m5_momentum_v4_kill_switch.txt",
        "compile_tag": "freq_first_v4",
        "backup_tag": "a1_xau_m5_momentum_freq_v4_before_update",
        "rule": "freq_h1_h4_long_rr0p7_v4_combo_rank1",
        "forward_variant": "freq_h1_h4_long_rr0p7_v4_combo_rank1",
        "direction_rule": (
            "LONG only, H1+H4 EMA20/50 alignment required, cost_R <= 0.05, "
            "server hours 2,9,10,11,12,13,17,19,21,23 blocked"
        ),
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,13,17,19,21,23",
    },
    "clean_long_v5_move12": {
        "title": "A1 XAU M5 Momentum Clean Portfolio Long Lane Forward Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_LONG_FORWARD_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_CLEAN_LONG_SHORT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "e5d7a0fe3283820ac73800bd8562eab9f098d70e5747346c2e8e7cca07d8576a",
        "run_id": "A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_LONG_V5_MOVE12_20260702",
        "magic": 932210,
        "order_comment": "A1_XAU_M5_MOM_CLN_L",
        "kill_switch": "a1_xau_m5_momentum_clean_long_kill_switch.txt",
        "compile_tag": "clean_portfolio_long_v5_move12",
        "backup_tag": "a1_xau_m5_momentum_clean_long_before_update",
        "rule": "clean_portfolio_long_v5_move12",
        "forward_variant": "v5_v4_move12",
        "direction_rule": "LONG only, H1+H4 EMA20/50 alignment, 1.20 ATR minimum 3-bar move",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,13,17,19,21,23",
        "direction_mode": "1",
        "min_three_bar_move_atr": "1.20",
    },
    "clean_short_core": {
        "title": "A1 XAU M5 Momentum Clean Portfolio Short Core Forward Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_SHORT_FORWARD_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_CLEAN_LONG_SHORT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "e5d7a0fe3283820ac73800bd8562eab9f098d70e5747346c2e8e7cca07d8576a",
        "run_id": "A1_XAU_M5_MOMENTUM_CLEAN_PORTFOLIO_SHORT_CORE_20260702",
        "magic": 932211,
        "order_comment": "A1_XAU_M5_MOM_CLN_S",
        "kill_switch": "a1_xau_m5_momentum_clean_short_kill_switch.txt",
        "compile_tag": "clean_portfolio_short_core",
        "backup_tag": "a1_xau_m5_momentum_clean_short_before_update",
        "rule": "clean_portfolio_short_core",
        "forward_variant": "freq_h1_h4_short_rr0p7_v1_core_1_5_15_19",
        "direction_rule": "SHORT only, H1+H4 EMA20/50 alignment, allowed server hours 1-5 plus 15 and 19",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "0,6,7,8,9,10,11,12,13,14,16,17,18,20,21,22,23",
        "direction_mode": "2",
        "min_three_bar_move_atr": "0.70",
    },
    "deep_v6_max2_long": {
        "title": "A1 XAU M5 Momentum Deep Portfolio V6 Max2 Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V6_MAX2_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "8a93950d2aac423f12055780ffa18d359b8d8e6ec687edebf364a6ddb2b5128d",
        "run_id": "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V6_MAX2_LONG_20260702",
        "magic": 932220,
        "order_comment": "A1_XAU_M5_MOM_DP_L1",
        "kill_switch": "a1_xau_m5_momentum_deep_v6_long_kill_switch.txt",
        "compile_tag": "deep_portfolio_v6_max2_long",
        "backup_tag": "a1_xau_m5_momentum_deep_v6_long_before_update",
        "rule": "deep_portfolio_v6_max2_long",
        "forward_variant": "v6_freq_v4_rr0p7_max2",
        "direction_rule": "LONG only, V4 mask, cost_R <= 0.05, up to two own open positions",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "20",
        "cooldown_minutes": "3",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,13,17,19,21,23",
        "direction_mode": "1",
        "one_position_per_magic": "false",
        "max_open_positions_per_magic": "2",
    },
    "deep_v13_both": {
        "title": "A1 XAU M5 Momentum Deep Portfolio V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "8a93950d2aac423f12055780ffa18d359b8d8e6ec687edebf364a6ddb2b5128d",
        "run_id": "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_V13_BOTH_20260702",
        "magic": 932221,
        "order_comment": "A1_XAU_M5_MOM_DP_B",
        "kill_switch": "a1_xau_m5_momentum_deep_v13_both_kill_switch.txt",
        "compile_tag": "deep_portfolio_v13_both",
        "backup_tag": "a1_xau_m5_momentum_deep_v13_both_before_update",
        "rule": "deep_portfolio_v13_both",
        "forward_variant": "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, directional hour masks",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
    },
    "deep_short_core": {
        "title": "A1 XAU M5 Momentum Deep Portfolio Short Core Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SHORT_CORE_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "8a93950d2aac423f12055780ffa18d359b8d8e6ec687edebf364a6ddb2b5128d",
        "run_id": "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SHORT_CORE_20260702",
        "magic": 932222,
        "order_comment": "A1_XAU_M5_MOM_DP_S",
        "kill_switch": "a1_xau_m5_momentum_deep_short_kill_switch.txt",
        "compile_tag": "deep_portfolio_short_core",
        "backup_tag": "a1_xau_m5_momentum_deep_short_before_update",
        "rule": "deep_portfolio_short_core",
        "forward_variant": "freq_h1_h4_short_rr0p7_v1_core_1_5_15_19",
        "direction_rule": "SHORT only, H1+H4 EMA20/50 alignment, allowed server hours 1-5 plus 15 and 19",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "0,6,7,8,9,10,11,12,13,14,16,17,18,20,21,22,23",
        "direction_mode": "2",
        "min_three_bar_move_atr": "0.70",
    },
    "robust_v6_max2_long": {
        "title": "A1 XAU M5 Momentum Robust Portfolio V6 Max2 Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V6_MAX2_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "cf90726599fba100d067fc2af01e6041dbe771bf49c369d5dd639bdf63f7d615",
        "run_id": "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V6_MAX2_LONG_20260702",
        "magic": 932230,
        "order_comment": "A1_XAU_M5_MOM_RB_L1",
        "kill_switch": "a1_xau_m5_momentum_robust_v6_long_kill_switch.txt",
        "compile_tag": "robust_portfolio_v6_max2_long",
        "backup_tag": "a1_xau_m5_momentum_robust_v6_long_before_update",
        "rule": "robust_portfolio_v6_max2_long",
        "forward_variant": "v6_freq_v4_rr0p7_max2",
        "direction_rule": "LONG only, V4 mask, cost_R <= 0.05, up to two own open positions",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "20",
        "cooldown_minutes": "3",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,13,17,19,21,23",
        "direction_mode": "1",
        "one_position_per_magic": "false",
        "max_open_positions_per_magic": "2",
    },
    "robust_v13_long_no_morning": {
        "title": "A1 XAU M5 Momentum Robust Portfolio V13 Long No Morning Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V13_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "cf90726599fba100d067fc2af01e6041dbe771bf49c369d5dd639bdf63f7d615",
        "run_id": "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V13_LONG_NO_MORNING_20260702",
        "magic": 932231,
        "order_comment": "A1_XAU_M5_MOM_RB_L2",
        "kill_switch": "a1_xau_m5_momentum_robust_v13_long_kill_switch.txt",
        "compile_tag": "robust_portfolio_v13_long_no_morning",
        "backup_tag": "a1_xau_m5_momentum_robust_v13_long_before_update",
        "rule": "robust_portfolio_v13_long_no_morning",
        "forward_variant": "v13_ema_trend_h1h4_long_rr0p6_no_morning",
        "direction_rule": "LONG only, M5 EMA trend continuation, H1+H4 aligned, morning long hours blocked",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "1",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "min_three_bar_move_atr": "0.10",
    },
    "robust_short_night_early": {
        "title": "A1 XAU M5 Momentum Robust Portfolio Short Night/Early Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SHORT_NIGHT_EARLY_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "cf90726599fba100d067fc2af01e6041dbe771bf49c369d5dd639bdf63f7d615",
        "run_id": "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SHORT_NIGHT_EARLY_20260702",
        "magic": 932232,
        "order_comment": "A1_XAU_M5_MOM_RB_S",
        "kill_switch": "a1_xau_m5_momentum_robust_short_kill_switch.txt",
        "compile_tag": "robust_portfolio_short_night_early",
        "backup_tag": "a1_xau_m5_momentum_robust_short_before_update",
        "rule": "robust_portfolio_short_night_early",
        "forward_variant": "freq_h1_h4_short_rr0p7_v1_night_early",
        "direction_rule": "SHORT only, H1+H4 EMA20/50 alignment, allowed early-night server hours 1-5",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "0,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23",
        "direction_mode": "2",
    },
    "robust_repair_v6_max2_long": {
        "title": "A1 XAU M5 Momentum Robust Repair V6 Max2 Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V6_MAX2_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "49dcf7bdbc0981ada282b94c730c3b2db4fd35a099ebca7e76ac557facfb1269",
        "run_id": "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V6_MAX2_LONG_20260702",
        "magic": 932240,
        "order_comment": "A1_XAU_M5_MOM_RP_L1",
        "kill_switch": "a1_xau_m5_momentum_robust_repair_v6_long_kill_switch.txt",
        "compile_tag": "robust_repair_v6_max2_long",
        "backup_tag": "a1_xau_m5_momentum_robust_repair_v6_long_before_update",
        "rule": "robust_repair_v6_max2_long",
        "forward_variant": "v6_freq_v4_rr0p7_max2",
        "direction_rule": "LONG only, V4 mask, cost_R <= 0.05, up to two own open positions",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "20",
        "cooldown_minutes": "3",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,13,17,19,21,23",
        "direction_mode": "1",
        "one_position_per_magic": "false",
        "max_open_positions_per_magic": "2",
    },
    "robust_repair_v13_long_no_morning_no18": {
        "title": "A1 XAU M5 Momentum Robust Repair V13 Long No Morning No18 Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V13_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "49dcf7bdbc0981ada282b94c730c3b2db4fd35a099ebca7e76ac557facfb1269",
        "run_id": "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V13_LONG_NO_MORNING_NO18_20260702",
        "magic": 932241,
        "order_comment": "A1_XAU_M5_MOM_RP_L2",
        "kill_switch": "a1_xau_m5_momentum_robust_repair_v13_long_kill_switch.txt",
        "compile_tag": "robust_repair_v13_long_no_morning_no18",
        "backup_tag": "a1_xau_m5_momentum_robust_repair_v13_long_before_update",
        "rule": "robust_repair_v13_long_no_morning_no18",
        "forward_variant": "v13_ema_trend_h1h4_long_rr0p6_no_morning_no18",
        "direction_rule": "LONG only, M5 EMA trend continuation, H1+H4 aligned, morning and hour 18 blocked",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "1",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,18,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "min_three_bar_move_atr": "0.10",
    },
    "robust_repair_short_night_early": {
        "title": "A1 XAU M5 Momentum Robust Repair Short Night/Early Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_SHORT_NIGHT_EARLY_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "49dcf7bdbc0981ada282b94c730c3b2db4fd35a099ebca7e76ac557facfb1269",
        "run_id": "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_SHORT_NIGHT_EARLY_20260702",
        "magic": 932242,
        "order_comment": "A1_XAU_M5_MOM_RP_S",
        "kill_switch": "a1_xau_m5_momentum_robust_repair_short_kill_switch.txt",
        "compile_tag": "robust_repair_short_night_early",
        "backup_tag": "a1_xau_m5_momentum_robust_repair_short_before_update",
        "rule": "robust_repair_short_night_early",
        "forward_variant": "freq_h1_h4_short_rr0p7_v1_night_early",
        "direction_rule": "SHORT only, H1+H4 EMA20/50 alignment, allowed early-night server hours 1-5",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "0,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23",
        "direction_mode": "2",
    },
    "daily_fit_long_weak_hours": {
        "title": "A1 XAU M5 Momentum Daily-Fit Long Weak-Hours Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "511af42042a5d6cfa3bac71a98c572a5a2292f47554a1f7fdfe1cd11094eac3f",
        "run_id": "A1_XAU_M5_MOMENTUM_DAILY_FIT_LONG_WEAK_HOURS_20260702",
        "magic": 932250,
        "order_comment": "A1_XAU_M5_MOM_DF_L",
        "kill_switch": "a1_xau_m5_momentum_daily_fit_long_kill_switch.txt",
        "compile_tag": "daily_fit_long_weak_hours",
        "backup_tag": "a1_xau_m5_momentum_daily_fit_long_before_update",
        "rule": "daily_fit_long_weak_hours",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak server hours blocked",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,22,23",
        "direction_mode": "1",
    },
    "daily_fit_v13_both": {
        "title": "A1 XAU M5 Momentum Daily-Fit V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "511af42042a5d6cfa3bac71a98c572a5a2292f47554a1f7fdfe1cd11094eac3f",
        "run_id": "A1_XAU_M5_MOMENTUM_DAILY_FIT_V13_BOTH_20260702",
        "magic": 932251,
        "order_comment": "A1_XAU_M5_MOM_DF_B",
        "kill_switch": "a1_xau_m5_momentum_daily_fit_v13_both_kill_switch.txt",
        "compile_tag": "daily_fit_v13_both",
        "backup_tag": "a1_xau_m5_momentum_daily_fit_v13_both_before_update",
        "rule": "daily_fit_v13_both",
        "forward_variant": "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, directional hour masks",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
    },
    "daily_fit_repair_long_weak_hours": {
        "title": "A1 XAU M5 Momentum Daily-Fit Repair Long Weak-Hours Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "fe911d1c8fb91ed0712eb272b9e517f0b6ca61582a555a9281507d1f2afe9386",
        "run_id": "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_LONG_WEAK_HOURS_20260702",
        "magic": 932260,
        "order_comment": "A1_XAU_M5_MOM_DFR_L",
        "kill_switch": "a1_xau_m5_momentum_daily_fit_repair_long_kill_switch.txt",
        "compile_tag": "daily_fit_repair_long_weak_hours",
        "backup_tag": "a1_xau_m5_momentum_daily_fit_repair_long_before_update",
        "rule": "daily_fit_repair_long_weak_hours",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak server hours blocked",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,22,23",
        "direction_mode": "1",
    },
    "daily_fit_repair_v13_both": {
        "title": "A1 XAU M5 Momentum Daily-Fit Repair V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "fe911d1c8fb91ed0712eb272b9e517f0b6ca61582a555a9281507d1f2afe9386",
        "run_id": "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_V13_BOTH_20260702",
        "magic": 932261,
        "order_comment": "A1_XAU_M5_MOM_DFR_B",
        "kill_switch": "a1_xau_m5_momentum_daily_fit_repair_v13_both_kill_switch.txt",
        "compile_tag": "daily_fit_repair_v13_both",
        "backup_tag": "a1_xau_m5_momentum_daily_fit_repair_v13_both_before_update",
        "rule": "daily_fit_repair_v13_both",
        "forward_variant": "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning_repair_no18_no22",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, directional hour masks, weak hours 18 and 22 blocked",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,18,19,20,22",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
    },
    "daily_guard_long_weak_hours": {
        "title": "A1 XAU M5 Momentum Daily Guard Long Weak-Hours Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "b5d25b1f2cb109e4aa758b9a4203ec7961d9875000f3589803080a0dd5d26c3c",
        "run_id": "A1_XAU_M5_MOMENTUM_DAILY_GUARD_LONG_WEAK_HOURS_20260702",
        "magic": 932270,
        "order_comment": "A1_XAU_M5_MOM_DG_L",
        "kill_switch": "a1_xau_m5_momentum_daily_guard_long_kill_switch.txt",
        "compile_tag": "daily_guard_long_weak_hours",
        "backup_tag": "a1_xau_m5_momentum_daily_guard_long_before_update",
        "rule": "daily_guard_long_weak_hours",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_daily_guard",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours blocked, shared package daily guard",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932270,932271",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "25.00",
    },
    "daily_guard_v13_both": {
        "title": "A1 XAU M5 Momentum Daily Guard V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "b5d25b1f2cb109e4aa758b9a4203ec7961d9875000f3589803080a0dd5d26c3c",
        "run_id": "A1_XAU_M5_MOMENTUM_DAILY_GUARD_V13_BOTH_20260702",
        "magic": 932271,
        "order_comment": "A1_XAU_M5_MOM_DG_B",
        "kill_switch": "a1_xau_m5_momentum_daily_guard_v13_both_kill_switch.txt",
        "compile_tag": "daily_guard_v13_both",
        "backup_tag": "a1_xau_m5_momentum_daily_guard_v13_both_before_update",
        "rule": "daily_guard_v13_both",
        "forward_variant": "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning_repair_no18_no22_daily_guard",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, weak hours 18 and 22 blocked, shared package daily guard",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,18,19,20,22",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932270,932271",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "25.00",
    },
    "feature_guard_long_weak_hours": {
        "title": "A1 XAU M5 Momentum Feature-Loss Daily Guard Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_GUARD_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "c36778bef2ced45d19fa25b99480722bfc6741cdcadab0755b22aab9737cefb4",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_GUARD_LONG_WEAK_HOURS_20260702",
        "magic": 932280,
        "order_comment": "A1_XAU_M5_MOM_FG_L",
        "kill_switch": "a1_xau_m5_momentum_feature_guard_long_kill_switch.txt",
        "compile_tag": "feature_guard_long_weak_hours",
        "backup_tag": "a1_xau_m5_momentum_feature_guard_long_before_update",
        "rule": "feature_guard_long_weak_hours",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_feature_guard",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours blocked, optimized shared package daily guard",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932280,932281",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "20.00",
    },
    "feature_guard_v13_both": {
        "title": "A1 XAU M5 Momentum Feature-Loss Daily Guard V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_GUARD_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "c36778bef2ced45d19fa25b99480722bfc6741cdcadab0755b22aab9737cefb4",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_GUARD_V13_BOTH_20260702",
        "magic": 932281,
        "order_comment": "A1_XAU_M5_MOM_FG_B",
        "kill_switch": "a1_xau_m5_momentum_feature_guard_v13_both_kill_switch.txt",
        "compile_tag": "feature_guard_v13_both",
        "backup_tag": "a1_xau_m5_momentum_feature_guard_v13_before_update",
        "rule": "feature_guard_v13_both",
        "forward_variant": "v13_feature_loss_short_extreme_rr0p6_feature_guard",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, SHORT close-to-recent-extreme feature-loss block, optimized shared package daily guard",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "feature_loss_filter_enabled": "true",
        "feature_loss_filter_shadow_only": "false",
        "short_close_to_recent_extreme_block_min": "-0.75",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932280,932281",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "20.00",
    },
    "split_be_tp1_v6_max2": {
        "title": "A1 XAU M5 Momentum Split-Entry BE-on-TP1 V6 Max2 Attachment - 2026-07-03",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V6_MAX2_ATTACHMENT_2026_07_03.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_FORWARD_V0_2026_07_03.md",
        "spec_sha256": "e55cf920c68cb070965529f1f426856bb61627920e5f3d31dae790e7a52cd824",
        "run_id": "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V6_MAX2_20260703",
        "magic": 932280,
        "order_comment": "A1_XAU_M5_MOM_SPLIT_BE_V6",
        "kill_switch": "a1_xau_m5_momentum_split_be_tp1_kill_switch.txt",
        "compile_tag": "split_be_tp1_v6_max2",
        "backup_tag": "a1_xau_m5_momentum_split_be_v6_before_update",
        "rule": "split_be_tp1_v6_max2_priority_1",
        "forward_variant": "risk_norm_split20_v6_max2_all8",
        "direction_rule": "LONG only, V4 mask, cost_R <= 0.05, split-entry TP1 0.70R plus runner 2.00R",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "20",
        "cooldown_minutes": "3",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,8,9,10,11,12,13,17,19,21,23",
        "direction_mode": "1",
        "one_position_per_magic": "false",
        "max_open_positions_per_magic": "4",
        "use_risk_normalized_lots": "true",
        "risk_amount_usd": "10.00",
        "max_risk_lots": "0.05",
        "split_entry_enabled": "true",
        "split_entry_shadow_only": "false",
        "split_entry_first_target_r": "0.70",
        "split_entry_runner_target_r": "2.00",
        "split_entry_move_runner_sl_to_be": "true",
        "split_entry_use_min_lot_pair": "true",
        "signal_claim_enabled": "true",
        "signal_claim_namespace": "A1MOM_SPLIT_BE",
        "signal_claim_priority": "1",
        "signal_claim_window_minutes": "4",
        "signal_claim_grace_seconds": "2",
        "allow_shared_magic": True,
    },
    "split_be_tp1_weak_hours": {
        "title": "A1 XAU M5 Momentum Split-Entry BE-on-TP1 Weak-Hours Attachment - 2026-07-03",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_WEAK_HOURS_ATTACHMENT_2026_07_03.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_FORWARD_V0_2026_07_03.md",
        "spec_sha256": "e55cf920c68cb070965529f1f426856bb61627920e5f3d31dae790e7a52cd824",
        "run_id": "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_WEAK_HOURS_20260703",
        "magic": 932280,
        "order_comment": "A1_XAU_M5_MOM_SPLIT_BE_WH",
        "kill_switch": "a1_xau_m5_momentum_split_be_tp1_kill_switch.txt",
        "compile_tag": "split_be_tp1_weak_hours",
        "backup_tag": "a1_xau_m5_momentum_split_be_weak_hours_before_update",
        "rule": "split_be_tp1_weak_hours_priority_2",
        "forward_variant": "risk_norm_split20_freq_weak_hours_all8",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours blocked, split-entry TP1 0.70R plus runner 2.00R",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,8,9,10,11,12,17,22,23",
        "direction_mode": "1",
        "use_risk_normalized_lots": "true",
        "risk_amount_usd": "10.00",
        "max_risk_lots": "0.05",
        "split_entry_enabled": "true",
        "split_entry_shadow_only": "false",
        "split_entry_first_target_r": "0.70",
        "split_entry_runner_target_r": "2.00",
        "split_entry_move_runner_sl_to_be": "true",
        "split_entry_use_min_lot_pair": "true",
        "signal_claim_enabled": "true",
        "signal_claim_namespace": "A1MOM_SPLIT_BE",
        "signal_claim_priority": "2",
        "signal_claim_window_minutes": "4",
        "signal_claim_grace_seconds": "2",
        "allow_shared_magic": True,
    },
    "split_be_tp1_v13": {
        "title": "A1 XAU M5 Momentum Split-Entry BE-on-TP1 V13 Attachment - 2026-07-03",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V13_ATTACHMENT_2026_07_03.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_FORWARD_V0_2026_07_03.md",
        "spec_sha256": "e55cf920c68cb070965529f1f426856bb61627920e5f3d31dae790e7a52cd824",
        "run_id": "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V13_20260703",
        "magic": 932280,
        "order_comment": "A1_XAU_M5_MOM_SPLIT_BE_V13",
        "kill_switch": "a1_xau_m5_momentum_split_be_tp1_kill_switch.txt",
        "compile_tag": "split_be_tp1_v13",
        "backup_tag": "a1_xau_m5_momentum_split_be_v13_before_update",
        "rule": "split_be_tp1_v13_priority_3",
        "forward_variant": "risk_norm_split20_v13_rr0p7_all8_22",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, directional hour masks, split-entry TP1 0.70R plus runner 2.00R",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,8,9,10,11,12,16,19,20,22",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "use_risk_normalized_lots": "true",
        "risk_amount_usd": "10.00",
        "max_risk_lots": "0.05",
        "split_entry_enabled": "true",
        "split_entry_shadow_only": "false",
        "split_entry_first_target_r": "0.70",
        "split_entry_runner_target_r": "2.00",
        "split_entry_move_runner_sl_to_be": "true",
        "split_entry_use_min_lot_pair": "true",
        "signal_claim_enabled": "true",
        "signal_claim_namespace": "A1MOM_SPLIT_BE",
        "signal_claim_priority": "3",
        "signal_claim_window_minutes": "4",
        "signal_claim_grace_seconds": "2",
        "allow_shared_magic": True,
    },
    "feature_band_long_weak_hours": {
        "title": "A1 XAU M5 Momentum Feature-Band Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "2841f87404e085954da5614b43331f5d85884f3170986ccc5cad01bc35271279",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_LONG_WEAK_HOURS_20260702",
        "magic": 932290,
        "order_comment": "A1_XAU_M5_MOM_FB_L",
        "kill_switch": "a1_xau_m5_momentum_feature_band_long_kill_switch.txt",
        "compile_tag": "feature_band_long_weak_hours",
        "backup_tag": "a1_xau_m5_momentum_feature_band_long_before_update",
        "rule": "feature_band_long_weak_hours",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_feature_band",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours blocked, no shared portfolio daily guard",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "false",
    },
    "feature_band_v13_both": {
        "title": "A1 XAU M5 Momentum Feature-Band V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "2841f87404e085954da5614b43331f5d85884f3170986ccc5cad01bc35271279",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_V13_BOTH_20260702",
        "magic": 932291,
        "order_comment": "A1_XAU_M5_MOM_FB_B",
        "kill_switch": "a1_xau_m5_momentum_feature_band_v13_both_kill_switch.txt",
        "compile_tag": "feature_band_v13_both",
        "backup_tag": "a1_xau_m5_momentum_feature_band_v13_before_update",
        "rule": "feature_band_v13_both",
        "forward_variant": "v13_feature_loss_short_extreme_band_m2p51_rr0p6_feature_band",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, SHORT close-to-recent-extreme min/max feature-band blocks, no shared portfolio daily guard",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "feature_loss_filter_enabled": "true",
        "feature_loss_filter_shadow_only": "false",
        "short_close_to_recent_extreme_block_min": "-0.75",
        "short_close_to_recent_extreme_block_max_enabled": "true",
        "short_close_to_recent_extreme_block_max": "-2.51",
        "portfolio_daily_guard_enabled": "false",
    },
    "feature_band_daily_income_long": {
        "title": "A1 XAU M5 Momentum Feature-Band Daily-Income Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "188b3ded97da503ecb43faa38671f7a0b7482df935091f9fa8a91cf9d0f79a1b",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_LONG_20260702",
        "magic": 932292,
        "order_comment": "A1_XAU_M5_MOM_DI_L",
        "kill_switch": "a1_xau_m5_momentum_feature_band_daily_income_long_kill_switch.txt",
        "compile_tag": "feature_band_daily_income_long",
        "backup_tag": "a1_xau_m5_momentum_feature_band_daily_income_long_before_update",
        "rule": "feature_band_daily_income_long",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_feature_band_daily_income",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours blocked, shared +50 USD package target and max 6 package trades/day",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932292,932293",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
    },
    "feature_band_daily_income_v13_both": {
        "title": "A1 XAU M5 Momentum Feature-Band Daily-Income V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "188b3ded97da503ecb43faa38671f7a0b7482df935091f9fa8a91cf9d0f79a1b",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_V13_20260702",
        "magic": 932293,
        "order_comment": "A1_XAU_M5_MOM_DI_B",
        "kill_switch": "a1_xau_m5_momentum_feature_band_daily_income_v13_kill_switch.txt",
        "compile_tag": "feature_band_daily_income_v13",
        "backup_tag": "a1_xau_m5_momentum_feature_band_daily_income_v13_before_update",
        "rule": "feature_band_daily_income_v13_both",
        "forward_variant": "v13_feature_loss_short_extreme_band_m2p51_rr0p6_feature_band_daily_income",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, SHORT close-to-recent-extreme min/max feature-band blocks, shared +50 USD package target and max 6 package trades/day",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "feature_loss_filter_enabled": "true",
        "feature_loss_filter_shadow_only": "false",
        "short_close_to_recent_extreme_block_min": "-0.75",
        "short_close_to_recent_extreme_block_max_enabled": "true",
        "short_close_to_recent_extreme_block_max": "-2.51",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932292,932293",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
    },
    "feature_band_daily_reliability_long": {
        "title": "A1 XAU M5 Momentum Feature-Band Daily-Reliability Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "693d070050666ccd066a834f71b666b3f865829e6a05c8942190be7da9c1729b",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_LONG_20260702",
        "magic": 932294,
        "order_comment": "A1_XAU_M5_MOM_DR_L",
        "kill_switch": "a1_xau_m5_momentum_feature_band_daily_reliability_long_kill_switch.txt",
        "compile_tag": "feature_band_daily_reliability_long",
        "backup_tag": "a1_xau_m5_momentum_feature_band_daily_reliability_long_before_update",
        "rule": "feature_band_daily_reliability_long",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_feature_band_daily_reliability",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours blocked, shared +50 USD package target, max 6 package trades/day, and 15-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932294,932295",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "15",
    },
    "feature_band_daily_reliability_v13_both": {
        "title": "A1 XAU M5 Momentum Feature-Band Daily-Reliability V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "693d070050666ccd066a834f71b666b3f865829e6a05c8942190be7da9c1729b",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_V13_20260702",
        "magic": 932295,
        "order_comment": "A1_XAU_M5_MOM_DR_B",
        "kill_switch": "a1_xau_m5_momentum_feature_band_daily_reliability_v13_kill_switch.txt",
        "compile_tag": "feature_band_daily_reliability_v13",
        "backup_tag": "a1_xau_m5_momentum_feature_band_daily_reliability_v13_before_update",
        "rule": "feature_band_daily_reliability_v13_both",
        "forward_variant": "v13_feature_loss_short_extreme_band_m2p51_rr0p6_feature_band_daily_reliability",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, SHORT close-to-recent-extreme min/max feature-band blocks, shared +50 USD package target, max 6 package trades/day, and 15-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "feature_loss_filter_enabled": "true",
        "feature_loss_filter_shadow_only": "false",
        "short_close_to_recent_extreme_block_min": "-0.75",
        "short_close_to_recent_extreme_block_max_enabled": "true",
        "short_close_to_recent_extreme_block_max": "-2.51",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932294,932295",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "15",
    },
    "feature_band_residual_reliability_long": {
        "title": "A1 XAU M5 Momentum Feature-Band Residual-Reliability Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "1b84b0f7195a79a7cd031118ef54c203a55442027288064bc817da07c2510edd",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_LONG_20260702",
        "magic": 932296,
        "order_comment": "A1_XAU_M5_MOM_RR_L",
        "kill_switch": "a1_xau_m5_momentum_feature_band_residual_reliability_long_kill_switch.txt",
        "compile_tag": "feature_band_residual_reliability_long",
        "backup_tag": "a1_xau_m5_momentum_feature_band_residual_reliability_long_before_update",
        "rule": "feature_band_residual_reliability_long",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_feature_band_residual_reliability",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours plus server hour 18 blocked, shared +50 USD package target, max 6 package trades/day, and 15-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,18,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932296,932297",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "15",
    },
    "feature_band_residual_reliability_v13_both": {
        "title": "A1 XAU M5 Momentum Feature-Band Residual-Reliability V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "1b84b0f7195a79a7cd031118ef54c203a55442027288064bc817da07c2510edd",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_V13_20260702",
        "magic": 932297,
        "order_comment": "A1_XAU_M5_MOM_RR_B",
        "kill_switch": "a1_xau_m5_momentum_feature_band_residual_reliability_v13_kill_switch.txt",
        "compile_tag": "feature_band_residual_reliability_v13",
        "backup_tag": "a1_xau_m5_momentum_feature_band_residual_reliability_v13_before_update",
        "rule": "feature_band_residual_reliability_v13_both",
        "forward_variant": "v13_feature_loss_short_extreme_band_residual_rr0p6_feature_band_daily_reliability",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, LONG hour 18 blocked, SHORT close-to-recent-extreme min tightened to -0.92 with max -2.51, shared +50 USD package target, max 6 package trades/day, and 15-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8,18",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "feature_loss_filter_enabled": "true",
        "feature_loss_filter_shadow_only": "false",
        "short_close_to_recent_extreme_block_min": "-0.92",
        "short_close_to_recent_extreme_block_max_enabled": "true",
        "short_close_to_recent_extreme_block_max": "-2.51",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932296,932297",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "15",
    },
    "feature_band_residual_plus50_cooldown10_long": {
        "title": "A1 XAU M5 Momentum Feature-Band Residual +50 Cooldown10 Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_LONG_20260702",
        "magic": 932298,
        "order_comment": "A1_XAU_M5_MOM_RR10_L",
        "kill_switch": "a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_long_kill_switch.txt",
        "compile_tag": "feature_band_residual_plus50_cooldown10_long",
        "backup_tag": "a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_long_before_update",
        "rule": "feature_band_residual_plus50_cooldown10_long",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_feature_band_residual_plus50_cooldown10",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours plus server hour 18 blocked, shared +50 USD package target, max 6 package trades/day, and 10-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,18,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932298,932299",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "10",
    },
    "feature_band_residual_plus50_cooldown10_v13_both": {
        "title": "A1 XAU M5 Momentum Feature-Band Residual +50 Cooldown10 V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_V13_20260702",
        "magic": 932299,
        "order_comment": "A1_XAU_M5_MOM_RR10_B",
        "kill_switch": "a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_v13_kill_switch.txt",
        "compile_tag": "feature_band_residual_plus50_cooldown10_v13",
        "backup_tag": "a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_v13_before_update",
        "rule": "feature_band_residual_plus50_cooldown10_v13_both",
        "forward_variant": "v13_feature_loss_short_extreme_band_residual_rr0p6_feature_band_plus50_cooldown10",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, LONG hour 18 blocked, SHORT close-to-recent-extreme min tightened to -0.92 with max -2.51, shared +50 USD package target, max 6 package trades/day, and 10-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8,18",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "feature_loss_filter_enabled": "true",
        "feature_loss_filter_shadow_only": "false",
        "short_close_to_recent_extreme_block_min": "-0.92",
        "short_close_to_recent_extreme_block_max_enabled": "true",
        "short_close_to_recent_extreme_block_max": "-2.51",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932298,932299",
        "portfolio_daily_profit_target_usd": "50.00",
        "portfolio_max_trades_per_day": "6",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "10",
    },
    "feature_band_residual_plus75_high_net_long": {
        "title": "A1 XAU M5 Momentum Feature-Band Residual +75 High-Net Long Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_LONG_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_LONG_20260702",
        "magic": 932300,
        "order_comment": "A1_XAU_M5_MOM_RR75_L",
        "kill_switch": "a1_xau_m5_momentum_feature_band_residual_plus75_high_net_long_kill_switch.txt",
        "compile_tag": "feature_band_residual_plus75_high_net_long",
        "backup_tag": "a1_xau_m5_momentum_feature_band_residual_plus75_high_net_long_before_update",
        "rule": "feature_band_residual_plus75_high_net_long",
        "forward_variant": "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1_feature_band_residual_plus75_high_net",
        "direction_rule": "LONG only, H1+H4 EMA20/50 aligned, weak hours plus server hour 18 blocked, shared +75 USD package target, no package max-trade cap, and 10-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "12",
        "cooldown_minutes": "5",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.70",
        "blocked_entry_hours": "2,9,10,11,12,17,18,22,23",
        "direction_mode": "1",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932300,932301",
        "portfolio_daily_profit_target_usd": "75.00",
        "portfolio_max_trades_per_day": "0",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "10",
    },
    "feature_band_residual_plus75_high_net_v13_both": {
        "title": "A1 XAU M5 Momentum Feature-Band Residual +75 High-Net V13 Both Attachment - 2026-07-02",
        "output_json": PHASE1_ROOT
        / "outputs"
        / "reports"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_V13_BOTH_ATTACHMENT_2026_07_02.json",
        "spec_doc": PHASE1_ROOT
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md",
        "spec_sha256": "de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a",
        "run_id": "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_V13_20260702",
        "magic": 932301,
        "order_comment": "A1_XAU_M5_MOM_RR75_B",
        "kill_switch": "a1_xau_m5_momentum_feature_band_residual_plus75_high_net_v13_kill_switch.txt",
        "compile_tag": "feature_band_residual_plus75_high_net_v13",
        "backup_tag": "a1_xau_m5_momentum_feature_band_residual_plus75_high_net_v13_before_update",
        "rule": "feature_band_residual_plus75_high_net_v13_both",
        "forward_variant": "v13_feature_loss_short_extreme_band_residual_rr0p6_feature_band_plus75_high_net",
        "direction_rule": "BOTH directions, M5 EMA trend continuation, H1+H4 aligned, LONG hour 18 blocked, SHORT close-to-recent-extreme min tightened to -0.92 with max -2.51, shared +75 USD package target, no package max-trade cap, and 10-minute package cooldown after any package loss",
        "max_estimated_cost_r": "0.05",
        "max_trades_per_day": "24",
        "cooldown_minutes": "0",
        "min_atr_absolute_for_entry": "0.00",
        "risk_reward": "0.60",
        "signal_mode": "5",
        "direction_mode": "0",
        "blocked_entry_hours": "0,2,4,9,10,11,12,16,19,20",
        "blocked_long_entry_hours": "6,7,8,18",
        "blocked_short_entry_hours": "13,14,15,17,18",
        "m5_trend_ema_fast_period": "8",
        "m5_trend_ema_slow_period": "21",
        "m5_trend_slope_bars": "3",
        "m5_trend_min_slope_atr": "0.03",
        "m5_trend_max_distance_atr": "1.20",
        "min_range_atr": "0.35",
        "min_body_fraction": "0.30",
        "long_close_location": "0.58",
        "short_close_location": "0.42",
        "min_three_bar_move_atr": "0.10",
        "feature_loss_filter_enabled": "true",
        "feature_loss_filter_shadow_only": "false",
        "short_close_to_recent_extreme_block_min": "-0.92",
        "short_close_to_recent_extreme_block_max_enabled": "true",
        "short_close_to_recent_extreme_block_max": "-2.51",
        "portfolio_daily_guard_enabled": "true",
        "portfolio_guard_magic_csv": "932300,932301",
        "portfolio_daily_profit_target_usd": "75.00",
        "portfolio_max_trades_per_day": "0",
        "portfolio_daily_loss_stop_usd": "0.00",
        "portfolio_cooldown_after_loss_minutes": "10",
    },
}


def attach_a1_xau_m5_momentum_continuation(
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    variant: str = DEFAULT_VARIANT,
    launch: bool = True,
) -> dict[str, Any]:
    config = variant_config(variant)
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve()
    metaeditor_exe = metaeditor_exe.resolve()
    output_json = (output_json or config["output_json"]).resolve()
    output_md = output_json.with_suffix(".md")
    output_json.parent.mkdir(parents=True, exist_ok=True)

    profile_dir = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = terminal_data_dir / "MQL5" / "Files"
    require_file(EA_SOURCE)
    require_file(config["spec_doc"])
    require_file(terminal_exe)
    require_file(metaeditor_exe)
    require_dir(profile_dir)
    verify_spec_hash(config)

    account_before = read_account_state(terminal_exe)
    validate_account(account_before)
    symbol_info = read_symbol_info(terminal_exe)
    existing_chart = find_existing_lane(profile_dir, config)
    ensure_no_magic_exposure(terminal_exe, config)
    deployed_source = deploy_source(terminal_data_dir)
    compile_log = compile_ea(metaeditor_exe, terminal_data_dir, config)
    terminal_closed = close_terminal(terminal_exe)
    backup_dir = backup_profile(profile_dir, terminal_data_dir, config)
    chart_path, chart_action = upsert_chart(profile_dir, existing_chart, config)

    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(8.0)

    account_after = read_account_state(terminal_exe)
    startup_tail = read_tail(files_dir / "a1_xau_m5_momentum_startup_log.csv")
    signal_tail = read_tail(files_dir / "a1_xau_m5_momentum_signal_log.csv")
    order_tail = read_tail(files_dir / "a1_xau_m5_momentum_order_log.csv")
    checks = build_checks(config, compile_log, chart_path, startup_tail, account_before, account_after)
    status = "PASS_ATTACHED" if all(check["status"] == "PASS" for check in checks) else "PENDING_RUNTIME_EVIDENCE"
    if any(check["status"] == "FAIL" for check in checks):
        status = "FAIL"

    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": now_utc(),
        "authority": (
            "Owner requested an A1-only XAUUSD M5 momentum-continuation demo lane to catch clean "
            "break-and-run moves that do not retest a broken level. This is demo only, not canonical "
            "Phase 2 approval, not live trading, and not real capital."
        ),
        "boundaries": {
            "account": f"{ACCOUNT_LOGIN} / {SERVER}",
            "a1_only": True,
            "a2_touched": False,
            "a3_touched": False,
            "existing_920101_chart_edited": False,
            "non_920101_lanes_edited": False,
            "broker_action_enabled_for_new_lane": True,
            "fixed_lot": 0.01,
            "rule": config["rule"],
            "spec_doc": str(config["spec_doc"]),
            "spec_sha256": config["spec_sha256"],
        },
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile": "Default",
            "profile_backup_dir": str(backup_dir),
            "terminal_closed_before_profile_append": terminal_closed,
            "terminal_relaunched": launch,
        },
        "ea": {
            "name": EA_NAME,
            "source": str(EA_SOURCE),
            "deployed_source": str(deployed_source),
            "compile_log": str(compile_log),
            "chart": str(chart_path),
            "chart_action": chart_action,
            "run_id": config["run_id"],
            "symbol": SYMBOL,
            "magic": config["magic"],
            "lot": 0.01,
            "order_comment": config["order_comment"],
            "startup_log": str(files_dir / "a1_xau_m5_momentum_startup_log.csv"),
            "signal_log": str(files_dir / "a1_xau_m5_momentum_signal_log.csv"),
            "order_log": str(files_dir / "a1_xau_m5_momentum_order_log.csv"),
        },
        "mechanical_summary": {
            "timeframe": "M5",
            "pattern": "break-and-run momentum, no retest required",
            "forward_variant": config["forward_variant"],
            "direction_rule": config["direction_rule"],
            "breakout_lookback_bars": 12,
            "trigger": "close beyond previous 12-bar high/low by 0.20 ATR, strong body, directional close, and 3-bar impulse",
            "risk": f"0.01 fixed lot, stop=max(2.5*M5 ATR, 350 points), cap 1800 points, TP={config['risk_reward']}R",
            "guards": (
                "demo-only, A1 login allowlist, spread<=75, "
                f"estimated_cost_R<={config['max_estimated_cost_r']}, max {config['max_trades_per_day']}/day, "
                f"{config['cooldown_minutes']} minute cooldown, one own position per magic"
            ),
        },
        "symbol_info": symbol_info,
        "account_before": account_before,
        "account_after": account_after,
        "checks": checks,
        "startup_tail": startup_tail,
        "signal_tail": signal_tail,
        "order_tail": order_tail,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def variant_config(variant: str) -> dict[str, Any]:
    if variant not in VARIANT_CONFIGS:
        allowed = ", ".join(sorted(VARIANT_CONFIGS))
        raise ValueError(f"Unknown momentum variant {variant!r}; allowed: {allowed}")
    return VARIANT_CONFIGS[variant]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def require_dir(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verify_spec_hash(config: dict[str, Any]) -> None:
    spec_doc = Path(config["spec_doc"])
    digest = hashlib.sha256(spec_doc.read_bytes()).hexdigest()
    if digest != config["spec_sha256"]:
        raise RuntimeError(f"Spec hash mismatch for {spec_doc}: {digest} != {config['spec_sha256']}")


def venv_python() -> Path:
    return PHASE1_ROOT.parent / "xauusd-phase0" / ".venv" / "Scripts" / "python.exe"


def read_account_state(terminal_exe: Path) -> dict[str, Any]:
    script = f"""
import json
import MetaTrader5 as mt5
if not mt5.initialize(path=r'{terminal_exe}'):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    account = mt5.account_info()
    positions = mt5.positions_get() or []
    orders = mt5.orders_get() or []
    print(json.dumps({{
        'login': getattr(account, 'login', None),
        'server': getattr(account, 'server', None),
        'balance': getattr(account, 'balance', None),
        'equity': getattr(account, 'equity', None),
        'trade_allowed': bool(getattr(account, 'trade_allowed', False)),
        'positions_total': len(positions),
        'orders_total': len(orders),
        'position_magics': sorted(set(int(getattr(p, 'magic', 0)) for p in positions)),
        'order_magics': sorted(set(int(getattr(o, 'magic', 0)) for o in orders)),
    }}))
finally:
    mt5.shutdown()
"""
    result = subprocess.run([str(venv_python()), "-c", script], text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 account query failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def validate_account(account: dict[str, Any]) -> None:
    if str(account.get("login")) != ACCOUNT_LOGIN:
        raise RuntimeError(f"A1 account mismatch: {account}")
    if str(account.get("server")) != SERVER:
        raise RuntimeError(f"A1 server mismatch: {account}")
    if not account.get("trade_allowed"):
        raise RuntimeError(f"A1 trade_allowed is false: {account}")


def read_symbol_info(terminal_exe: Path) -> dict[str, Any]:
    script = f"""
import json
import MetaTrader5 as mt5
if not mt5.initialize(path=r'{terminal_exe}'):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    mt5.symbol_select('{SYMBOL}', True)
    info = mt5.symbol_info('{SYMBOL}')
    tick = mt5.symbol_info_tick('{SYMBOL}')
    print(json.dumps({{
        'symbol': getattr(info, 'name', None),
        'visible': bool(getattr(info, 'visible', False)) if info else False,
        'trade_mode': getattr(info, 'trade_mode', None) if info else None,
        'digits': getattr(info, 'digits', None) if info else None,
        'point': getattr(info, 'point', None) if info else None,
        'volume_min': getattr(info, 'volume_min', None) if info else None,
        'volume_step': getattr(info, 'volume_step', None) if info else None,
        'tick_present': tick is not None,
        'bid': getattr(tick, 'bid', None) if tick else None,
        'ask': getattr(tick, 'ask', None) if tick else None,
    }}))
finally:
    mt5.shutdown()
"""
    result = subprocess.run([str(venv_python()), "-c", script], text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 symbol query failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    if not payload.get("tick_present"):
        raise RuntimeError(f"{SYMBOL} has no fresh tick: {payload}")
    return payload


def find_existing_lane(profile_dir: Path, config: dict[str, Any]) -> Path | None:
    matches: list[Path] = []
    allow_shared_magic = bool(config.get("allow_shared_magic", False))
    for chart in sorted(profile_dir.glob("chart*.chr")):
        text = read_chart_text(chart)
        if (
            (not allow_shared_magic and f"InpMagicNumber={config['magic']}" in text)
            or f"InpRunId={config['run_id']}" in text
            or f"InpOrderComment={config['order_comment']}" in text
        ):
            matches.append(chart)
    if len(matches) > 1:
        raise RuntimeError(f"Multiple momentum lanes found; refusing to guess: {matches}")
    return matches[0] if matches else None


def ensure_no_magic_exposure(terminal_exe: Path, config: dict[str, Any]) -> None:
    magic = int(config["magic"])
    script = f"""
import json
import MetaTrader5 as mt5
if not mt5.initialize(path=r'{terminal_exe}'):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    positions = [p._asdict() for p in (mt5.positions_get() or []) if getattr(p, 'magic', 0) == {magic}]
    orders = [o._asdict() for o in (mt5.orders_get() or []) if getattr(o, 'magic', 0) == {magic}]
    print(json.dumps({{'positions': len(positions), 'orders': len(orders)}}))
finally:
    mt5.shutdown()
"""
    result = subprocess.run([str(venv_python()), "-c", script], text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 magic exposure query failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    if payload["positions"] or payload["orders"]:
        raise RuntimeError(f"Magic {magic} already has exposure: {payload}")


def deploy_source(terminal_data_dir: Path) -> Path:
    target = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EA_SOURCE, target)
    return target


def compile_ea(metaeditor_exe: Path, terminal_data_dir: Path, config: dict[str, Any]) -> Path:
    scratch = Path("C:/MT5CompileScratchA1M5Momentum")
    scratch_mql5 = scratch / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch_experts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5", scratch_experts / f"{EA_NAME}.mq5")
    log = scratch / f"compile_{EA_NAME}.log"
    subprocess.run(
        [str(metaeditor_exe), f"/compile:{scratch_experts / (EA_NAME + '.mq5')}", f"/log:{log}"],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    ex5 = scratch_experts / f"{EA_NAME}.ex5"
    if not ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce EX5. Log:\n{read_text(log)}")
    target_ex5 = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    target_log = terminal_data_dir / "MQL5" / "Logs" / f"compile_{EA_NAME}_a1_20260702_{config['compile_tag']}.log"
    target_log.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ex5, target_ex5)
    if log.exists():
        shutil.copy2(log, target_log)
    log_text = read_text(target_log).lower()
    if "error(s)" in log_text and "0 error(s)" not in log_text:
        raise RuntimeError(f"MetaEditor compile reported errors:\n{read_text(target_log)}")
    return target_log


def close_terminal(terminal_exe: Path) -> bool:
    ps = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}').Path
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
if(-not $procs) {{ exit 0 }}
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ [void]$p.CloseMainWindow() }}
}}
Start-Sleep -Seconds 5
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ Stop-Process -Id $proc.ProcessId -Force }}
}}
exit 0
"""
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], text=True, capture_output=True, timeout=30)
    return result.returncode == 0


def backup_profile(profile_dir: Path, terminal_data_dir: Path, config: dict[str, Any]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"{config['backup_tag']}_{stamp}"
    shutil.copytree(profile_dir, backup)
    return backup


def upsert_chart(profile_dir: Path, existing_chart: Path | None, config: dict[str, Any]) -> tuple[Path, str]:
    if existing_chart is not None:
        chart = existing_chart
        match = re.fullmatch(r"chart(\d+)\.chr", chart.name)
        if not match:
            raise RuntimeError(f"Unexpected chart file name: {chart}")
        index = int(match.group(1))
        action = "updated_existing_momentum_chart"
    else:
        index = next_chart_index(profile_dir)
        chart = profile_dir / f"chart{index:02d}.chr"
        action = "appended_new_momentum_chart"
    chart.write_text(render_chart(index, config), encoding="utf-8")
    return chart, action


def next_chart_index(profile_dir: Path) -> int:
    indexes: list[int] = []
    for chart in profile_dir.glob("chart*.chr"):
        match = re.fullmatch(r"chart(\d+)\.chr", chart.name)
        if match:
            indexes.append(int(match.group(1)))
    return max(indexes, default=0) + 1


def render_chart(index: int, config: dict[str, Any]) -> str:
    left = 60 + ((index - 1) % 4) * 36
    top = 80 + ((index - 1) // 4) * 28
    value = config_value
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}{index:04d}",
            f"symbol={SYMBOL}",
            "description=Gold",
            "period_type=0",
            "period_size=5",
            "digits=2",
            "tick_size=0.010000",
            "scale_fix=0",
            "scale_fixed_min=0.000000",
            "scale_fixed_max=0.000000",
            "scale=3",
            "mode=1",
            "fore=0",
            "grid=0",
            "volume=0",
            "scroll=1",
            "shift=1",
            "ohlc=0",
            "one_click=0",
            "one_click_btn=0",
            "askline=1",
            "days=0",
            f"window_left={left}",
            f"window_top={top}",
            f"window_right={left + 980}",
            f"window_bottom={top + 720}",
            "windows_total=1",
            "",
            "<expert>",
            f"name={EA_NAME}",
            f"path=Experts\\{EA_NAME}.ex5",
            "expertmode=1",
            "<inputs>",
            f"InpRunId={config['run_id']}",
            "InpAllowDemoTrading=true",
            "InpAllowNonDemoAccounts=false",
            f"InpAllowedAccountLogin={ACCOUNT_LOGIN}",
            "InpExpectedServerMarker=Demo",
            f"InpTargetSymbol={SYMBOL}",
            f"InpMagicNumber={config['magic']}",
            "InpFixedLots=0.01",
            f"InpUseRiskNormalizedLots={value(config, 'use_risk_normalized_lots', 'false')}",
            f"InpRiskAmountUsd={value(config, 'risk_amount_usd', '0.00')}",
            f"InpMaxRiskLots={value(config, 'max_risk_lots', '0.05')}",
            "InpDeviationPoints=80",
            "InpMaxSpreadPoints=75",
            f"InpMaxEstimatedCostR={config['max_estimated_cost_r']}",
            f"InpMaxTradesPerDay={config['max_trades_per_day']}",
            f"InpPortfolioDailyGuardEnabled={value(config, 'portfolio_daily_guard_enabled', 'false')}",
            f"InpPortfolioGuardMagicCsv={value(config, 'portfolio_guard_magic_csv', '')}",
            f"InpPortfolioMaxTradesPerDay={value(config, 'portfolio_max_trades_per_day', '0')}",
            f"InpPortfolioDailyProfitTargetUsd={value(config, 'portfolio_daily_profit_target_usd', '0.00')}",
            f"InpPortfolioDailyLossStopUsd={value(config, 'portfolio_daily_loss_stop_usd', '0.00')}",
            f"InpPortfolioCooldownAfterLossMinutes={value(config, 'portfolio_cooldown_after_loss_minutes', '0')}",
            f"InpCooldownMinutes={config['cooldown_minutes']}",
            f"InpOnePositionPerMagic={value(config, 'one_position_per_magic', 'true')}",
            f"InpMaxOpenPositionsPerMagic={value(config, 'max_open_positions_per_magic', '1')}",
            f"InpKillSwitchFileName={config['kill_switch']}",
            "InpStartupLogFileName=a1_xau_m5_momentum_startup_log.csv",
            "InpSignalLogFileName=a1_xau_m5_momentum_signal_log.csv",
            "InpOrderLogFileName=a1_xau_m5_momentum_order_log.csv",
            "InpManagementLogFileName=a1_xau_m5_momentum_management_log.csv",
            "InpDealLogFileName=a1_xau_m5_momentum_deal_log.csv",
            f"InpOrderComment={config['order_comment']}",
            f"InpSignalMode={value(config, 'signal_mode', '0')}",
            f"InpBreakLookbackBars={value(config, 'break_lookback_bars', '12')}",
            f"InpAtrPeriod={value(config, 'atr_period', '14')}",
            f"InpBreakAtrMultiple={value(config, 'break_atr_multiple', '0.20')}",
            f"InpMinRangeAtr={value(config, 'min_range_atr', '0.60')}",
            f"InpMinBodyFraction={value(config, 'min_body_fraction', '0.45')}",
            f"InpLongCloseLocation={value(config, 'long_close_location', '0.72')}",
            f"InpShortCloseLocation={value(config, 'short_close_location', '0.28')}",
            f"InpMinThreeBarMoveAtr={value(config, 'min_three_bar_move_atr', '0.70')}",
            f"InpMaxThreeBarMoveAtr={value(config, 'max_three_bar_move_atr', '0.00')}",
            f"InpMinAtrAbsoluteForEntry={config['min_atr_absolute_for_entry']}",
            f"InpStopAtrMultiple={value(config, 'stop_atr_multiple', '2.50')}",
            f"InpStopFloorPoints={value(config, 'stop_floor_points', '350')}",
            f"InpStopCeilingPoints={value(config, 'stop_ceiling_points', '1800')}",
            f"InpStopCapPoints={value(config, 'stop_cap_points', '0')}",
            f"InpRiskReward={config['risk_reward']}",
            f"InpBlockedEntryHoursCsv={config['blocked_entry_hours']}",
            f"InpBlockedLongEntryHoursCsv={value(config, 'blocked_long_entry_hours', '')}",
            f"InpBlockedShortEntryHoursCsv={value(config, 'blocked_short_entry_hours', '')}",
            f"InpDirectionMode={value(config, 'direction_mode', '1')}",
            f"InpUseH1TrendFilter={value(config, 'use_h1_trend_filter', 'true')}",
            f"InpH1TrendApplyToLong={value(config, 'h1_apply_to_long', 'true')}",
            f"InpH1TrendApplyToShort={value(config, 'h1_apply_to_short', 'true')}",
            f"InpH1EmaFastPeriod={value(config, 'h1_ema_fast_period', '20')}",
            f"InpH1EmaSlowPeriod={value(config, 'h1_ema_slow_period', '50')}",
            f"InpH1TrendSlopeBars={value(config, 'h1_trend_slope_bars', '3')}",
            f"InpH1TrendMinSlopePoints={value(config, 'h1_trend_min_slope_points', '0')}",
            f"InpUseH4TrendFilter={value(config, 'use_h4_trend_filter', 'true')}",
            f"InpH4TrendApplyToLong={value(config, 'h4_apply_to_long', 'true')}",
            f"InpH4TrendApplyToShort={value(config, 'h4_apply_to_short', 'true')}",
            f"InpH4EmaFastPeriod={value(config, 'h4_ema_fast_period', '20')}",
            f"InpH4EmaSlowPeriod={value(config, 'h4_ema_slow_period', '50')}",
            f"InpH4TrendSlopeBars={value(config, 'h4_trend_slope_bars', '3')}",
            f"InpH4TrendMinSlopePoints={value(config, 'h4_trend_min_slope_points', '0')}",
            f"InpUseDirectionalSessionFilter={value(config, 'use_directional_session_filter', 'false')}",
            f"InpLongSessionStartHour={value(config, 'long_session_start_hour', '0')}",
            f"InpLongSessionEndHour={value(config, 'long_session_end_hour', '24')}",
            f"InpShortSessionStartHour={value(config, 'short_session_start_hour', '0')}",
            f"InpShortSessionEndHour={value(config, 'short_session_end_hour', '24')}",
            f"InpFeatureLossFilterEnabled={value(config, 'feature_loss_filter_enabled', 'false')}",
            f"InpFeatureLossFilterShadowOnly={value(config, 'feature_loss_filter_shadow_only', 'true')}",
            f"InpShortCloseToRecentExtremeBlockMin={value(config, 'short_close_to_recent_extreme_block_min', '-0.75')}",
            f"InpShortCloseToRecentExtremeBlockMaxEnabled={value(config, 'short_close_to_recent_extreme_block_max_enabled', 'false')}",
            f"InpShortCloseToRecentExtremeBlockMax={value(config, 'short_close_to_recent_extreme_block_max', '-2.51')}",
            f"InpM5TrendEmaFastPeriod={value(config, 'm5_trend_ema_fast_period', '8')}",
            f"InpM5TrendEmaSlowPeriod={value(config, 'm5_trend_ema_slow_period', '21')}",
            f"InpM5TrendSlopeBars={value(config, 'm5_trend_slope_bars', '3')}",
            f"InpM5TrendMinSlopeAtr={value(config, 'm5_trend_min_slope_atr', '0.03')}",
            f"InpM5TrendMaxDistanceAtr={value(config, 'm5_trend_max_distance_atr', '1.20')}",
            f"InpSplitEntryEnabled={value(config, 'split_entry_enabled', 'false')}",
            f"InpSplitEntryShadowOnly={value(config, 'split_entry_shadow_only', 'true')}",
            f"InpSplitEntryFirstTargetR={value(config, 'split_entry_first_target_r', '0.70')}",
            f"InpSplitEntryRunnerTargetR={value(config, 'split_entry_runner_target_r', '2.00')}",
            f"InpSplitEntryMoveRunnerSLToBE={value(config, 'split_entry_move_runner_sl_to_be', 'true')}",
            f"InpSplitEntryUseMinLotPair={value(config, 'split_entry_use_min_lot_pair', 'false')}",
            f"InpSignalClaimEnabled={value(config, 'signal_claim_enabled', 'false')}",
            f"InpSignalClaimNamespace={value(config, 'signal_claim_namespace', 'A1MOM_SPLIT_BE')}",
            f"InpSignalClaimPriority={value(config, 'signal_claim_priority', '0')}",
            f"InpSignalClaimWindowMinutes={value(config, 'signal_claim_window_minutes', '4')}",
            f"InpSignalClaimGraceSeconds={value(config, 'signal_claim_grace_seconds', '2')}",
            "</inputs>",
            "</expert>",
            "",
            "<window>",
            "height=100.000000",
            "objects=0",
            "<indicator>",
            "name=Main",
            "path=",
            "apply=1",
            "</indicator>",
            "</window>",
            "</chart>",
            "",
        ]
    )


def config_value(config: dict[str, Any], key: str, default: str) -> str:
    value = config.get(key, default)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_checks(
    config: dict[str, Any],
    compile_log: Path,
    chart_path: Path,
    startup_tail: list[str],
    account_before: dict[str, Any],
    account_after: dict[str, Any],
) -> list[dict[str, str]]:
    startup_seen = any(config["run_id"] in line for line in startup_tail)
    checks = [
        {"name": "compile_log_present", "status": "PASS" if compile_log.exists() else "FAIL", "detail": str(compile_log)},
        {"name": "chart_written", "status": "PASS" if chart_path.exists() else "FAIL", "detail": str(chart_path)},
        {"name": "a1_account_unchanged", "status": "PASS" if account_after.get("login") == account_before.get("login") == int(ACCOUNT_LOGIN) else "FAIL", "detail": json.dumps({"before": account_before.get("login"), "after": account_after.get("login")})},
        {
            "name": "startup_log_seen",
            "status": "PASS" if startup_seen else "PENDING",
            "detail": "Startup log row observed after terminal relaunch."
            if startup_seen
            else "Waiting for EA startup log row after terminal relaunch.",
        },
    ]
    return checks


def read_tail(path: Path, count: int = 5) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]


def read_chart_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['boundaries']['rule']} Attachment - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["authority"],
        "",
        "## Boundary",
        "",
        "- Demo account only.",
        "- A1 only.",
        "- Existing `920101` breakout-retest chart was not edited.",
        "- A2 and A3 were not touched.",
        "- This is not canonical Phase 2 approval, not live trading, and not real capital.",
        f"- Forward spec: `{payload['boundaries']['spec_doc']}`",
        f"- Spec SHA256: `{payload['boundaries']['spec_sha256']}`",
        "",
        "## New Lane",
        "",
        f"- EA: `{payload['ea']['name']}`",
        f"- Account: `{ACCOUNT_LOGIN} / {SERVER}`",
        f"- Symbol: `{SYMBOL}`",
        f"- Magic: `{payload['ea']['magic']}`",
        f"- Lot: `0.01`",
        f"- Chart: `{payload['ea']['chart']}`",
        f"- Chart action: `{payload['ea']['chart_action']}`",
        f"- Compile log: `{payload['ea']['compile_log']}`",
        f"- Profile backup: `{payload['terminal']['profile_backup_dir']}`",
        "",
        "## Mechanical Summary",
        "",
    ]
    for key, value in payload["mechanical_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Checks", ""])
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---:|---|")
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['status']}` | {check['detail']} |")
    lines.extend(["", "## Startup Tail", ""])
    if payload["startup_tail"]:
        lines.extend(f"- `{line}`" for line in payload["startup_tail"])
    else:
        lines.append("- `PENDING_STARTUP_LOG_NOT_SEEN_YET`")
    lines.extend(["", "## Signal Tail", ""])
    if payload["signal_tail"]:
        lines.extend(f"- `{line}`" for line in payload["signal_tail"])
    else:
        lines.append("- `PENDING_FIRST_SIGNAL_ROW`")
    lines.extend(["", "## Order Tail", ""])
    if payload["order_tail"]:
        lines.extend(f"- `{line}`" for line in payload["order_tail"])
    else:
        lines.append("- `PENDING_FIRST_ORDER_OR_GUARD_ROW`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach A1 XAU M5 momentum continuation demo executor.")
    parser.add_argument("--variant", choices=sorted(VARIANT_CONFIGS), default=DEFAULT_VARIANT)
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    args = parser.parse_args()
    payload = attach_a1_xau_m5_momentum_continuation(
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        variant=args.variant,
        launch=not args.no_launch,
    )
    print(payload["status"])
    print(payload["ea"]["chart"])
    print(payload["ea"]["compile_log"])
    return 0 if payload["status"] in {"PASS_ATTACHED", "PENDING_RUNTIME_EVIDENCE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
