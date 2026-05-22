#ifndef PHASE1_LOGGER_MQH
#define PHASE1_LOGGER_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1CsvLogger
{
private:
   string m_decision_file_name;
   string m_startup_file_name;
   string m_shutdown_file_name;
   datetime m_last_decision_write_time;

public:
   void Configure(
      const string decision_file_name,
      const string startup_file_name,
      const string shutdown_file_name
   )
   {
      m_decision_file_name = decision_file_name;
      m_startup_file_name = startup_file_name;
      m_shutdown_file_name = shutdown_file_name;
      m_last_decision_write_time = 0;
   }

   datetime LastDecisionWriteTime() const
   {
      return m_last_decision_write_time;
   }

   bool WriteStartup(
      const string run_id,
      const string symbol_name,
      const bool dry_run_only,
      const bool observe_breakout_retest,
      const bool observe_swing_breakout_retest,
      const double max_spread_points,
      const double max_risk_pct,
      const double daily_loss_limit_pct,
      const double weekly_loss_limit_pct,
      const double monthly_loss_limit_pct,
      const bool manual_risk_lock,
      const bool magic_namespace_ok,
      const Phase1ServerTimeStatus &server_time
   )
   {
      int handle = OpenCsv(m_startup_file_name);
      if(handle == INVALID_HANDLE)
         return false;

      if(FileSize(handle) == 0)
      {
         FileWrite(
            handle,
            "timestamp_broker",
            "timestamp_utc",
            "timestamp_local",
            "run_id",
            "symbol",
            "dry_run_only",
            "observe_breakout_retest",
            "observe_swing_breakout_retest",
            "max_spread_points",
            "max_risk_pct",
            "daily_loss_limit_pct",
            "weekly_loss_limit_pct",
            "monthly_loss_limit_pct",
            "manual_risk_lock",
            "magic_namespace_ok",
            "server_time_status",
            "broker_utc_offset_seconds",
            "local_utc_offset_seconds",
            "local_clock_drift_seconds"
         );
      }

      FileSeek(handle, 0, SEEK_END);
      FileWrite(
         handle,
         TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
         TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
         TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
         run_id,
         symbol_name,
         dry_run_only ? "true" : "false",
         observe_breakout_retest ? "true" : "false",
         observe_swing_breakout_retest ? "true" : "false",
         DoubleToString(max_spread_points, 2),
         DoubleToString(max_risk_pct, 4),
         DoubleToString(daily_loss_limit_pct, 2),
         DoubleToString(weekly_loss_limit_pct, 2),
         DoubleToString(monthly_loss_limit_pct, 2),
         manual_risk_lock ? "true" : "false",
         magic_namespace_ok ? "true" : "false",
         server_time.status_text,
         server_time.broker_utc_offset_seconds,
         server_time.local_utc_offset_seconds,
         server_time.local_clock_drift_seconds
      );
      FileFlush(handle);
      FileClose(handle);
      return true;
   }

   bool WriteShutdown(
      const string run_id,
      const string symbol_name,
      const int reason,
      const datetime last_m5_bar_time
   )
   {
      int handle = OpenCsv(m_shutdown_file_name);
      if(handle == INVALID_HANDLE)
         return false;

      if(FileSize(handle) == 0)
      {
         FileWrite(
            handle,
            "timestamp_broker",
            "timestamp_utc",
            "timestamp_local",
            "run_id",
            "symbol",
            "shutdown_reason",
            "last_m5_bar_time",
            "last_decision_write_time",
            "lifecycle_state"
         );
      }

      FileSeek(handle, 0, SEEK_END);
      FileWrite(
         handle,
         TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
         TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
         TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
         run_id,
         symbol_name,
         reason,
         TimeToString(last_m5_bar_time, TIME_DATE | TIME_SECONDS),
         TimeToString(m_last_decision_write_time, TIME_DATE | TIME_SECONDS),
         "DRY_RUN"
      );
      FileFlush(handle);
      FileClose(handle);
      return true;
   }

   bool WriteDecision(const Phase1Decision &decision)
   {
      int handle = OpenCsv(m_decision_file_name);
      if(handle == INVALID_HANDLE)
         return false;

      if(FileSize(handle) == 0)
      {
         string header = "";
         AppendCell(header, "timestamp_broker");
         AppendCell(header, "timestamp_utc");
         AppendCell(header, "timestamp_local");
         AppendCell(header, "run_id");
         AppendCell(header, "lifecycle_state");
         AppendCell(header, "symbol");
         AppendCell(header, "bid");
         AppendCell(header, "ask");
         AppendCell(header, "spread_points");
         AppendCell(header, "bar_time");
         AppendCell(header, "session");
         AppendCell(header, "regime");
         AppendCell(header, "router_version");
         AppendCell(header, "risk_state");
         AppendCell(header, "requested_risk_pct");
         AppendCell(header, "max_risk_pct");
         AppendCell(header, "simulated_daily_pnl_pct");
         AppendCell(header, "simulated_weekly_pnl_pct");
         AppendCell(header, "simulated_monthly_pnl_pct");
         AppendCell(header, "daily_loss_limit_pct");
         AppendCell(header, "weekly_loss_limit_pct");
         AppendCell(header, "monthly_loss_limit_pct");
         AppendCell(header, "manual_risk_lock");
         AppendCell(header, "risk_ok");
         AppendCell(header, "execution_state");
         AppendCell(header, "news_state");
         AppendCell(header, "expert_lifecycle_state");
         AppendCell(header, "magic_namespace_ok");
         AppendCell(header, "server_time_status");
         AppendCell(header, "broker_utc_offset_seconds");
         AppendCell(header, "local_utc_offset_seconds");
         AppendCell(header, "local_clock_drift_seconds");
         AppendCell(header, "feature_ok");
         AppendCell(header, "atr14_points");
         AppendCell(header, "m5_range_points");
         AppendCell(header, "m5_body_points");
         AppendCell(header, "m5_upper_wick_points");
         AppendCell(header, "m5_lower_wick_points");
         AppendCell(header, "m15_range_points");
         AppendCell(header, "h1_range_points");
         AppendCell(header, "compression_state");
         AppendCell(header, "br_stage");
         AppendCell(header, "br_direction");
         AppendCell(header, "br_would_signal");
         AppendCell(header, "br_reason_code");
         AppendCell(header, "br_level_found");
         AppendCell(header, "br_break_found");
         AppendCell(header, "br_retest_valid");
         AppendCell(header, "br_confirmation_valid");
         AppendCell(header, "br_level_kind");
         AppendCell(header, "br_level_price");
         AppendCell(header, "br_entry_price");
         AppendCell(header, "br_stop_loss");
         AppendCell(header, "br_take_profit");
         AppendCell(header, "br_stop_distance_points");
         AppendCell(header, "br_break_shift");
         AppendCell(header, "sbr_stage");
         AppendCell(header, "sbr_direction");
         AppendCell(header, "sbr_would_signal");
         AppendCell(header, "sbr_reason_code");
         AppendCell(header, "sbr_level_found");
         AppendCell(header, "sbr_break_found");
         AppendCell(header, "sbr_retest_valid");
         AppendCell(header, "sbr_confirmation_valid");
         AppendCell(header, "sbr_level_kind");
         AppendCell(header, "sbr_level_price");
         AppendCell(header, "sbr_entry_price");
         AppendCell(header, "sbr_stop_loss");
         AppendCell(header, "sbr_take_profit");
         AppendCell(header, "sbr_stop_distance_points");
         AppendCell(header, "sbr_break_shift");
         AppendCell(header, "allowed_expert");
         AppendCell(header, "would_have_allowed_experts");
         AppendCell(header, "trade_permission");
         AppendCell(header, "block_reason");
         AppendCell(header, "dry_run");
         AppendCell(header, "tick_ok");
         AppendCell(header, "stale_seconds");
         AppendCell(header, "expert_name");
         AppendCell(header, "magic_number");
         AppendCell(header, "direction");
         AppendCell(header, "entry_price");
         AppendCell(header, "stop_loss");
         AppendCell(header, "take_profit");
         AppendCell(header, "risk_pct");
         AppendCell(header, "reason_code");
         AppendCell(header, "blocked_reason");
         FileWriteString(handle, header + "\r\n");
      }

      FileSeek(handle, 0, SEEK_END);
      string row = "";
      AppendCell(row, TimeToString(decision.market.broker_time, TIME_DATE | TIME_SECONDS));
      AppendCell(row, TimeToString(decision.market.utc_time, TIME_DATE | TIME_SECONDS));
      AppendCell(row, TimeToString(decision.market.local_time, TIME_DATE | TIME_SECONDS));
      AppendCell(row, decision.run_id);
      AppendCell(row, decision.lifecycle_state);
      AppendCell(row, decision.market.symbol_name);
      AppendCell(row, DoubleToString(decision.market.bid, decision.market.digits));
      AppendCell(row, DoubleToString(decision.market.ask, decision.market.digits));
      AppendCell(row, DoubleToString(decision.market.spread_points, 2));
      AppendCell(row, TimeToString(decision.market.m5_bar_time, TIME_DATE | TIME_SECONDS));
      AppendCell(row, Phase1SessionText(decision.session_state));
      AppendCell(row, Phase1RegimeText(decision.regime_state));
      AppendCell(row, "phase1_router_v0.6");
      AppendCell(row, Phase1RiskText(decision.risk_state));
      AppendCell(row, DoubleToString(decision.risk_details.requested_risk_pct, 4));
      AppendCell(row, DoubleToString(decision.risk_details.max_risk_pct, 4));
      AppendCell(row, DoubleToString(decision.risk_details.simulated_daily_pnl_pct, 2));
      AppendCell(row, DoubleToString(decision.risk_details.simulated_weekly_pnl_pct, 2));
      AppendCell(row, DoubleToString(decision.risk_details.simulated_monthly_pnl_pct, 2));
      AppendCell(row, DoubleToString(decision.risk_details.daily_loss_limit_pct, 2));
      AppendCell(row, DoubleToString(decision.risk_details.weekly_loss_limit_pct, 2));
      AppendCell(row, DoubleToString(decision.risk_details.monthly_loss_limit_pct, 2));
      AppendCell(row, decision.risk_details.manual_lock ? "true" : "false");
      AppendCell(row, decision.risk_details.risk_ok ? "true" : "false");
      AppendCell(row, Phase1ExecutionText(decision.execution_state));
      AppendCell(row, Phase1NewsText(decision.news_state));
      AppendCell(row, decision.expert_lifecycle_state);
      AppendCell(row, decision.magic_namespace_ok ? "true" : "false");
      AppendCell(row, decision.server_time.status_text);
      AppendCell(row, IntegerToString(decision.server_time.broker_utc_offset_seconds));
      AppendCell(row, IntegerToString(decision.server_time.local_utc_offset_seconds));
      AppendCell(row, IntegerToString(decision.server_time.local_clock_drift_seconds));
      AppendCell(row, decision.features.feature_ok ? "true" : "false");
      AppendCell(row, DoubleToString(decision.features.atr14_points, 2));
      AppendCell(row, DoubleToString(decision.features.m5_range_points, 2));
      AppendCell(row, DoubleToString(decision.features.m5_body_points, 2));
      AppendCell(row, DoubleToString(decision.features.m5_upper_wick_points, 2));
      AppendCell(row, DoubleToString(decision.features.m5_lower_wick_points, 2));
      AppendCell(row, DoubleToString(decision.features.m15_range_points, 2));
      AppendCell(row, DoubleToString(decision.features.h1_range_points, 2));
      AppendCell(row, decision.features.compression_state ? "true" : "false");
      AppendCell(row, decision.breakout_retest.stage);
      AppendCell(row, decision.breakout_retest.direction_text);
      AppendCell(row, decision.breakout_retest.would_signal ? "true" : "false");
      AppendCell(row, decision.breakout_retest.reason_code);
      AppendCell(row, decision.breakout_retest.level_found ? "true" : "false");
      AppendCell(row, decision.breakout_retest.break_found ? "true" : "false");
      AppendCell(row, decision.breakout_retest.retest_valid ? "true" : "false");
      AppendCell(row, decision.breakout_retest.confirmation_valid ? "true" : "false");
      AppendCell(row, decision.breakout_retest.level_kind);
      AppendCell(row, DoubleToString(decision.breakout_retest.level_price, decision.market.digits));
      AppendCell(row, DoubleToString(decision.breakout_retest.entry_price, decision.market.digits));
      AppendCell(row, DoubleToString(decision.breakout_retest.stop_loss, decision.market.digits));
      AppendCell(row, DoubleToString(decision.breakout_retest.take_profit, decision.market.digits));
      AppendCell(row, DoubleToString(decision.breakout_retest.stop_distance_points, 2));
      AppendCell(row, IntegerToString(decision.breakout_retest.break_shift));
      AppendCell(row, decision.swing_breakout_retest.stage);
      AppendCell(row, decision.swing_breakout_retest.direction_text);
      AppendCell(row, decision.swing_breakout_retest.would_signal ? "true" : "false");
      AppendCell(row, decision.swing_breakout_retest.reason_code);
      AppendCell(row, decision.swing_breakout_retest.level_found ? "true" : "false");
      AppendCell(row, decision.swing_breakout_retest.break_found ? "true" : "false");
      AppendCell(row, decision.swing_breakout_retest.retest_valid ? "true" : "false");
      AppendCell(row, decision.swing_breakout_retest.confirmation_valid ? "true" : "false");
      AppendCell(row, decision.swing_breakout_retest.level_kind);
      AppendCell(row, DoubleToString(decision.swing_breakout_retest.level_price, decision.market.digits));
      AppendCell(row, DoubleToString(decision.swing_breakout_retest.entry_price, decision.market.digits));
      AppendCell(row, DoubleToString(decision.swing_breakout_retest.stop_loss, decision.market.digits));
      AppendCell(row, DoubleToString(decision.swing_breakout_retest.take_profit, decision.market.digits));
      AppendCell(row, DoubleToString(decision.swing_breakout_retest.stop_distance_points, 2));
      AppendCell(row, IntegerToString(decision.swing_breakout_retest.break_shift));
      AppendCell(row, decision.allowed_expert);
      AppendCell(row, decision.would_have_allowed_experts);
      AppendCell(row, decision.trade_permission ? "true" : "false");
      AppendCell(row, decision.block_reason);
      AppendCell(row, decision.dry_run ? "true" : "false");
      AppendCell(row, decision.market.tick_ok ? "true" : "false");
      AppendCell(row, IntegerToString(decision.market.stale_seconds));
      AppendCell(row, decision.signal.expert_name);
      AppendCell(row, IntegerToString(decision.signal.magic_number));
      AppendCell(row, Phase1DirectionText(decision.signal.direction));
      AppendCell(row, DoubleToString(decision.signal.entry_price, decision.market.digits));
      AppendCell(row, DoubleToString(decision.signal.stop_loss, decision.market.digits));
      AppendCell(row, DoubleToString(decision.signal.take_profit, decision.market.digits));
      AppendCell(row, DoubleToString(decision.signal.risk_pct, 4));
      AppendCell(row, decision.signal.reason_code);
      AppendCell(row, decision.signal.blocked_reason);
      FileWriteString(handle, row + "\r\n");
      m_last_decision_write_time = TimeCurrent();
      FileFlush(handle);
      FileClose(handle);
      return true;
   }

private:
   int OpenCsv(const string file_name) const
   {
      int handle = FileOpen(
         file_name,
         FILE_CSV | FILE_READ | FILE_WRITE | FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_ANSI,
         ','
      );
      if(handle == INVALID_HANDLE)
         Print("Phase1 logger could not open file: ", file_name, " error=", GetLastError());
      return handle;
   }

   string CsvCell(const string value) const
   {
      string cell = value;
      StringReplace(cell, "\"", "\"\"");
      if(StringFind(cell, ",") >= 0 || StringFind(cell, "\"") >= 0 || StringFind(cell, "\r") >= 0 || StringFind(cell, "\n") >= 0)
         return "\"" + cell + "\"";
      return cell;
   }

   void AppendCell(string &line, const string value) const
   {
      if(line != "")
         line += ",";
      line += CsvCell(value);
   }
};

#endif
