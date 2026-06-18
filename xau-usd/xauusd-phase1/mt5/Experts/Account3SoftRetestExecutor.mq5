// Account 3 soft-retest signal-quality lane. Experimental demo only; not canonical Phase 2.
// A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2: breakout-retest with soft retest geometry filter.
#property strict
#property version   "1.000"
#property description "A3 soft-retest breakout executor. Demo-only, dry-run by committed default."

#define A3_BREAKOUT_DEFAULT_RUN_ID "A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2"
#define A3_BREAKOUT_DEFAULT_MAGIC 933500
#define A3_BREAKOUT_EXPECTED_MAGIC 933500
#define A3_BREAKOUT_DEFAULT_COMMENT "A3_SOFT_RETEST_V2"
#define A3_BREAKOUT_SIGNAL_LOG "a3_soft_retest_v2_signal_log.csv"
#define A3_BREAKOUT_STARTUP_LOG "a3_soft_retest_v2_startup.csv"
#define A3_BREAKOUT_ORDER_LOG "a3_soft_retest_v2_order_log.csv"
#define A3_BREAKOUT_MANAGEMENT_LOG "a3_soft_retest_v2_management_log.csv"
#define A3_BREAKOUT_ATTACHED_STATUS "ATTACHED_A3_SOFT_RETEST_V2"
#define A3_BREAKOUT_TREND_GUARD_DEFAULT false
#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT false
#define A3_BREAKOUT_SESSION_GATE_DEFAULT false
#define A3_BREAKOUT_STOP_FLOOR_DEFAULT true
#define A3_BREAKOUT_TREND_SHADOW_DEFAULT false
#define A3_BREAKOUT_SOFT_RETEST_DEFAULT true

#include <A3BreakoutExecutorBase.mqh>
