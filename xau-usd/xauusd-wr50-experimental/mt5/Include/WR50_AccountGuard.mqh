#ifndef WR50_ACCOUNT_GUARD_MQH
#define WR50_ACCOUNT_GUARD_MQH

#include "WR50_MagicNumbers.mqh"

bool WR50_ServerLooksDemo(const string server)
{
   string lower = server;
   StringToLower(lower);
   return StringFind(lower, "demo") >= 0 || StringFind(lower, "practice") >= 0;
}

bool WR50_SymbolAllowed(const string chart_symbol, const string allowed_symbol, const bool allow_suffix)
{
   if(chart_symbol == allowed_symbol)
      return true;
   if(allow_suffix && StringFind(chart_symbol, allowed_symbol) == 0)
      return true;
   return false;
}

bool WR50_RuntimeRegistryAllows(const string file_name,
                                const string expected_ea_id,
                                const int active_magic,
                                const bool required,
                                string &reason)
{
   if(!required)
   {
      reason = "runtime_registry_not_required";
      return true;
   }
   if(!FileIsExist(file_name))
   {
      reason = "runtime_registry_missing:" + file_name;
      return false;
   }

   int handle = FileOpen(file_name, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
   {
      reason = "runtime_registry_open_failed:" + file_name;
      return false;
   }

   bool first = true;
   bool matched = false;
   while(!FileIsEnding(handle))
   {
      string ea_id = FileReadString(handle);
      string ea_name = FileReadString(handle);
      string version = FileReadString(handle);
      string short_code = FileReadString(handle);
      string magic_start = FileReadString(handle);
      string magic_end = FileReadString(handle);
      string active_magic_text = FileReadString(handle);
      string status = FileReadString(handle);
      string symbol = FileReadString(handle);
      string comment_prefix = FileReadString(handle);
      string enabled = FileReadString(handle);
      string live_authorized = FileReadString(handle);
      string canonical_phase2_authorized = FileReadString(handle);

      if(first)
      {
         first = false;
         if(ea_id == "ea_id")
            continue;
      }
      if(ea_id == expected_ea_id)
      {
         matched = true;
         if((int)StringToInteger(active_magic_text) != active_magic)
         {
            reason = "runtime_registry_magic_mismatch";
            FileClose(handle);
            return false;
         }
         string enabled_lower = enabled;
         string live_lower = live_authorized;
         string phase2_lower = canonical_phase2_authorized;
         StringToLower(enabled_lower);
         StringToLower(live_lower);
         StringToLower(phase2_lower);
         if(enabled_lower != "true")
         {
            reason = "runtime_registry_disabled";
            FileClose(handle);
            return false;
         }
         if(status != "DEMO_EXPERIMENT_ONLY")
         {
            reason = "runtime_registry_status_not_demo_experiment_only";
            FileClose(handle);
            return false;
         }
         if(live_lower == "true" || phase2_lower == "true")
         {
            reason = "runtime_registry_forbidden_authorization";
            FileClose(handle);
            return false;
         }
         reason = "runtime_registry_ok:" + ea_name + ":" + version + ":" + short_code + ":" + symbol + ":" + comment_prefix;
         FileClose(handle);
         return true;
      }
   }
   FileClose(handle);
   if(!matched)
      reason = "runtime_registry_ea_missing:" + expected_ea_id;
   return false;
}

bool WR50_AccountAllowlistAllows(const string file_name,
                                 const bool required,
                                 const string chart_symbol,
                                 string &reason)
{
   if(!required || file_name == "")
   {
      reason = "account_allowlist_not_required";
      return true;
   }
   if(!FileIsExist(file_name))
   {
      reason = "account_allowlist_missing:" + file_name;
      return false;
   }
   const string login = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   const string server = AccountInfoString(ACCOUNT_SERVER);
   int handle = FileOpen(file_name, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
   {
      reason = "account_allowlist_open_failed";
      return false;
   }
   bool first = true;
   while(!FileIsEnding(handle))
   {
      string account = FileReadString(handle);
      string allowed_server = FileReadString(handle);
      string allowed_symbol = FileReadString(handle);
      string enabled = FileReadString(handle);
      string notes = FileReadString(handle);
      if(first)
      {
         first = false;
         if(account == "account")
            continue;
      }
      string enabled_lower = enabled;
      StringToLower(enabled_lower);
      if(account == login && allowed_server == server && allowed_symbol == chart_symbol && enabled_lower == "true")
      {
         reason = "account_allowlist_ok:" + notes;
         FileClose(handle);
         return true;
      }
   }
   FileClose(handle);
   reason = "account_allowlist_no_match";
   return false;
}

bool WR50_ValidateAccountGuard(const bool experimental_demo_only,
                               const bool allow_demo_trading,
                               const string owner_authorization_token,
                               const string required_owner_authorization_token,
                               const string ea_id,
                               const string ea_name,
                               const int active_magic,
                               const int magic_start,
                               const int magic_end,
                               const string allowed_symbol,
                               const bool allow_symbol_suffix,
                               const bool require_demo_server_name,
                               const bool require_runtime_registry_file,
                               const string runtime_registry_file,
                               const string account_allowlist_file,
                               const bool require_account_allowlist,
                               const bool allow_netting_account,
                               string &reason)
{
   if(!experimental_demo_only)
   {
      reason = "InpExperimentalDemoOnly must remain true";
      return false;
   }
   if(!allow_demo_trading)
   {
      reason = "InpAllowDemoTrading is false";
      return false;
   }
   if(required_owner_authorization_token == "" || owner_authorization_token == "" ||
      owner_authorization_token != required_owner_authorization_token)
   {
      reason = "owner authorization token missing or mismatched";
      return false;
   }
   if(!WR50_ValidateAssignedMagic(active_magic, magic_start, magic_end, ea_name, reason))
      return false;

   long trade_mode = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(trade_mode != ACCOUNT_TRADE_MODE_DEMO)
   {
      reason = "non-demo account detected";
      return false;
   }
   string server = AccountInfoString(ACCOUNT_SERVER);
   if(require_demo_server_name && !WR50_ServerLooksDemo(server))
   {
      reason = "server name lacks demo marker:" + server;
      return false;
   }
   if(!WR50_SymbolAllowed(_Symbol, allowed_symbol, allow_symbol_suffix))
   {
      reason = "symbol not allowed:" + _Symbol + " expected " + allowed_symbol;
      return false;
   }
   long margin_mode = AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   if(margin_mode != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING && !allow_netting_account)
   {
      reason = "netting or exchange margin mode blocked for attribution safety";
      return false;
   }

   string registry_reason = "";
   if(!WR50_RuntimeRegistryAllows(runtime_registry_file, ea_id, active_magic, require_runtime_registry_file, registry_reason))
   {
      reason = registry_reason;
      return false;
   }

   string allowlist_reason = "";
   if(!WR50_AccountAllowlistAllows(account_allowlist_file, require_account_allowlist, _Symbol, allowlist_reason))
   {
      reason = allowlist_reason;
      return false;
   }

   reason = "account_guard_ok";
   return true;
}

#endif

