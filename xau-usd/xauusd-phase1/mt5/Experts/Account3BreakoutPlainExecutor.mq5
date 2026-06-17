// Account 3 breakout A/B lane A. Experimental demo only; not canonical Phase 2.
// Lane A / A3_BREAKOUT_PLAIN: plain breakout-retest control.
#property strict
#property version   "1.000"
#property description "A3 plain breakout executor. Demo-only, dry-run by committed default."

#define A3_BREAKOUT_DEFAULT_RUN_ID "A3_BREAKOUT_PLAIN_V1"
#define A3_BREAKOUT_DEFAULT_MAGIC 933200
#define A3_BREAKOUT_EXPECTED_MAGIC 933200
#define A3_BREAKOUT_DEFAULT_COMMENT "A3_BREAKOUT_PLAIN"
#define A3_BREAKOUT_SIGNAL_LOG "a3_breakout_plain_signal_log.csv"
#define A3_BREAKOUT_STARTUP_LOG "a3_breakout_plain_startup.csv"
#define A3_BREAKOUT_ORDER_LOG "a3_breakout_plain_order_log.csv"
#define A3_BREAKOUT_MANAGEMENT_LOG "a3_breakout_plain_management_log.csv"
#define A3_BREAKOUT_ATTACHED_STATUS "ATTACHED_A3_BREAKOUT_PLAIN"
#define A3_BREAKOUT_TREND_GUARD_DEFAULT false
#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT false

#include <A3BreakoutExecutorBase.mqh>
