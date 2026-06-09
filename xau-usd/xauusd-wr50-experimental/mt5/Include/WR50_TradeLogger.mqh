#ifndef WR50_TRADE_LOGGER_MQH
#define WR50_TRADE_LOGGER_MQH

#include "WR50_FileUtil.mqh"
#include "WR50_Types.mqh"

string WR50_BaseMetaCsv(const string account,
                        const string server,
                        const string symbol,
                        const string ea_id,
                        const string short_code,
                        const string version,
                        const string strategy_family,
                        const string experiment_id,
                        const string run_id,
                        const int magic)
{
   return account + "," + server + "," + symbol + "," + ea_id + "," + short_code + "," + version + "," +
          strategy_family + "," + experiment_id + "," + run_id + "," + IntegerToString(magic);
}

void WR50_LogStartup(const string ea_id,
                     const string short_code,
                     const string version,
                     const string experiment_id,
                     const string run_id,
                     const int magic,
                     const string status,
                     const string reason)
{
   string values[14];
   values[0] = WR50_TimeBroker();
   values[1] = WR50_TimeUtc();
   values[2] = WR50_TimeLocal();
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = AccountInfoString(ACCOUNT_SERVER);
   values[5] = TerminalInfoString(TERMINAL_DATA_PATH);
   values[6] = _Symbol;
   values[7] = ea_id;
   values[8] = short_code;
   values[9] = version;
   values[10] = experiment_id;
   values[11] = run_id;
   values[12] = IntegerToString(magic);
   values[13] = status + ":" + reason;
   WR50_WriteCsvLine("WR50\\wr50_startup_log.csv",
                     "timestamp_broker,timestamp_utc,timestamp_local,account,server,terminal_path,symbol,ea_id,ea_short_code,ea_version,experiment_id,run_id,magic,status_reason",
                     values);
}

void WR50_LogBlock(const string ea_id,
                   const string short_code,
                   const string version,
                   const string strategy_family,
                   const string experiment_id,
                   const string run_id,
                   const int magic,
                   const string reason_code,
                   const string block_reason,
                   const double spread_points,
                   const double max_spread_points)
{
   string values[17];
   values[0] = WR50_TimeBroker();
   values[1] = WR50_TimeUtc();
   values[2] = WR50_TimeLocal();
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = AccountInfoString(ACCOUNT_SERVER);
   values[5] = _Symbol;
   values[6] = ea_id;
   values[7] = short_code;
   values[8] = version;
   values[9] = strategy_family;
   values[10] = experiment_id;
   values[11] = run_id;
   values[12] = IntegerToString(magic);
   values[13] = reason_code;
   values[14] = block_reason;
   values[15] = DoubleToString(spread_points, 1);
   values[16] = DoubleToString(max_spread_points, 1);
   WR50_WriteCsvLine("WR50\\wr50_block_log.csv",
                     "timestamp_broker,timestamp_utc,timestamp_local,account,server,symbol,ea_id,ea_short_code,ea_version,strategy_family,experiment_id,run_id,magic,reason_code,block_reason,current_spread_points,max_spread_points",
                     values);
}

void WR50_LogSignal(const string ea_id,
                    const string short_code,
                    const string version,
                    const string strategy_family,
                    const string experiment_id,
                    const string run_id,
                    const int magic,
                    const WR50Signal &signal,
                    const string comment)
{
   string values[23];
   values[0] = WR50_TimeBroker();
   values[1] = WR50_TimeUtc();
   values[2] = WR50_TimeLocal();
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = AccountInfoString(ACCOUNT_SERVER);
   values[5] = _Symbol;
   values[6] = ea_id;
   values[7] = short_code;
   values[8] = version;
   values[9] = strategy_family;
   values[10] = experiment_id;
   values[11] = run_id;
   values[12] = IntegerToString(magic);
   values[13] = WR50_DirectionText(signal.direction);
   values[14] = signal.entry_type;
   values[15] = DoubleToString(signal.entry_price, _Digits);
   values[16] = DoubleToString(signal.sl_price, _Digits);
   values[17] = DoubleToString(signal.tp_price, _Digits);
   values[18] = DoubleToString(signal.atr_points, 1);
   values[19] = DoubleToString(signal.entry_spread_points, 1);
   values[20] = signal.session_bucket;
   values[21] = signal.reason_code;
   values[22] = comment;
   WR50_WriteCsvLine("WR50\\wr50_signal_log.csv",
                     "timestamp_broker,timestamp_utc,timestamp_local,account,server,symbol,ea_id,ea_short_code,ea_version,strategy_family,experiment_id,run_id,magic,direction,entry_type,entry_price,sl_price,tp_price,atr_points,entry_spread_points,session_bucket,reason_code,comment",
                     values);
}

void WR50_LogOrder(const string ea_id,
                   const string short_code,
                   const string version,
                   const string strategy_family,
                   const string experiment_id,
                   const string run_id,
                   const int magic,
                   const WR50Signal &signal,
                   const double lot,
                   const ulong order_ticket,
                   const ulong deal_ticket,
                   const uint retcode,
                   const string comment)
{
   string values[29];
   values[0] = WR50_TimeBroker();
   values[1] = WR50_TimeUtc();
   values[2] = WR50_TimeLocal();
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = AccountInfoString(ACCOUNT_SERVER);
   values[5] = _Symbol;
   values[6] = ea_id;
   values[7] = short_code;
   values[8] = version;
   values[9] = strategy_family;
   values[10] = experiment_id;
   values[11] = run_id;
   values[12] = IntegerToString(magic);
   values[13] = IntegerToString((int)order_ticket);
   values[14] = "";
   values[15] = IntegerToString((int)deal_ticket);
   values[16] = WR50_DirectionText(signal.direction);
   values[17] = signal.entry_type;
   values[18] = DoubleToString(lot, 2);
   values[19] = DoubleToString(signal.entry_price, _Digits);
   values[20] = DoubleToString(signal.sl_price, _Digits);
   values[21] = DoubleToString(signal.tp_price, _Digits);
   values[22] = DoubleToString(signal.entry_spread_points, 1);
   values[23] = signal.session_bucket;
   values[24] = signal.reason_code;
   values[25] = IntegerToString((int)retcode);
   values[26] = comment;
   values[27] = "false";
   values[28] = "false";
   WR50_WriteCsvLine("WR50\\wr50_order_log.csv",
                     "timestamp_broker,timestamp_utc,timestamp_local,account,server,symbol,ea_id,ea_short_code,ea_version,strategy_family,experiment_id,run_id,magic,order_ticket,position_id,deal_ticket,direction,entry_type,lot,entry_price,sl_price,tp_price,entry_spread_points,session_bucket,reason_code,retcode,comment,canonical_phase2_evidence,live_authorized",
                     values);
   string ledger_values[37];
   ledger_values[0] = values[0];
   ledger_values[1] = values[1];
   ledger_values[2] = values[2];
   ledger_values[3] = values[3];
   ledger_values[4] = values[4];
   ledger_values[5] = values[5];
   ledger_values[6] = values[6];
   ledger_values[7] = values[7];
   ledger_values[8] = values[8];
   ledger_values[9] = values[9];
   ledger_values[10] = values[10];
   ledger_values[11] = values[11];
   ledger_values[12] = values[12];
   ledger_values[13] = values[13];
   ledger_values[14] = "";
   ledger_values[15] = values[15];
   ledger_values[16] = values[16];
   ledger_values[17] = values[17];
   ledger_values[18] = values[18];
   ledger_values[19] = values[19];
   ledger_values[20] = values[20];
   ledger_values[21] = values[21];
   ledger_values[22] = "";
   ledger_values[23] = values[0];
   ledger_values[24] = "";
   ledger_values[25] = values[22];
   ledger_values[26] = "";
   ledger_values[27] = "";
   ledger_values[28] = "";
   ledger_values[29] = "";
   ledger_values[30] = "";
   ledger_values[31] = "";
   ledger_values[32] = "";
   ledger_values[33] = values[23];
   ledger_values[34] = values[24];
   ledger_values[35] = "";
   ledger_values[36] = values[26];
   WR50_WriteCsvLine("WR50\\wr50_trade_ledger.csv",
                     "timestamp_broker,timestamp_utc,timestamp_local,account,server,symbol,ea_id,ea_short_code,ea_version,strategy_family,experiment_id,run_id,magic,order_ticket,position_id,deal_ticket,direction,entry_type,lot,entry_price,sl_price,tp_price,exit_price,entry_time_broker,exit_time_broker,entry_spread_points,exit_spread_points,commission,swap,profit_account_currency,gross_r,net_r,cost_r,session_bucket,reason_code,block_reason,comment",
                     ledger_values);
}

void WR50_LogError(const string ea_id,
                   const string short_code,
                   const string version,
                   const string experiment_id,
                   const string run_id,
                   const int magic,
                   const string source,
                   const string error_text)
{
   string values[13];
   values[0] = WR50_TimeBroker();
   values[1] = WR50_TimeUtc();
   values[2] = WR50_TimeLocal();
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = AccountInfoString(ACCOUNT_SERVER);
   values[5] = _Symbol;
   values[6] = ea_id;
   values[7] = short_code;
   values[8] = version;
   values[9] = experiment_id;
   values[10] = run_id;
   values[11] = IntegerToString(magic);
   values[12] = source + ":" + error_text;
   WR50_WriteCsvLine("WR50\\wr50_error_log.csv",
                     "timestamp_broker,timestamp_utc,timestamp_local,account,server,symbol,ea_id,ea_short_code,ea_version,experiment_id,run_id,magic,error",
                     values);
}

void WR50_LogImprovementOrder(const string ea_id,
                              const string short_code,
                              const string version,
                              const string strategy_family,
                              const string experiment_id,
                              const string run_id,
                              const int magic,
                              const WR50Signal &signal,
                              const double lot,
                              const double target_r,
                              const double stop_distance_points,
                              const double spread_points,
                              const double estimated_cost_r,
                              const ulong order_ticket,
                              const ulong deal_ticket,
                              const uint retcode,
                              const string comment,
                              const string decision,
                              const string reason)
{
   string values[34];
   values[0] = WR50_TimeBroker();
   values[1] = WR50_TimeUtc();
   values[2] = WR50_TimeLocal();
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = AccountInfoString(ACCOUNT_SERVER);
   values[5] = _Symbol;
   values[6] = ea_id;
   values[7] = short_code;
   values[8] = version;
   values[9] = strategy_family;
   values[10] = experiment_id;
   values[11] = run_id;
   values[12] = IntegerToString(magic);
   values[13] = WR50_DirectionText(signal.direction);
   values[14] = signal.entry_type;
   values[15] = DoubleToString(lot, 2);
   values[16] = DoubleToString(signal.entry_price, _Digits);
   values[17] = DoubleToString(signal.sl_price, _Digits);
   values[18] = DoubleToString(signal.tp_price, _Digits);
   values[19] = DoubleToString(target_r, 2);
   values[20] = DoubleToString(stop_distance_points, 1);
   values[21] = DoubleToString(spread_points, 1);
   values[22] = DoubleToString(estimated_cost_r, 4);
   values[23] = signal.session_bucket;
   values[24] = signal.reason_code;
   values[25] = IntegerToString((int)order_ticket);
   values[26] = IntegerToString((int)deal_ticket);
   values[27] = IntegerToString((int)retcode);
   values[28] = comment;
   values[29] = decision;
   values[30] = reason;
   values[31] = "false";
   values[32] = "false";
   values[33] = "COST_SUSPENDED_CANONICAL";
   WR50_WriteCsvLine("WR50\\wr50_improvement_order_log.csv",
                     "timestamp_broker,timestamp_utc,timestamp_local,account,server,symbol,ea_id,ea_short_code,ea_version,strategy_family,experiment_id,run_id,magic,direction,entry_type,lot,entry_price,sl_price,tp_price,target_r,stop_distance_points,spread_at_signal_points,estimated_cost_r,session_bucket,reason_code,order_ticket,deal_ticket,retcode,comment,decision,reason,canonical_phase2_evidence,live_authorized,family_lifecycle_status",
                     values);
}

#endif
