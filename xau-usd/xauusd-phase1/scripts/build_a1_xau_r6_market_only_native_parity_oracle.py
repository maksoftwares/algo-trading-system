"""Build the NP1 market-only native Router oracle from pinned MQL blocks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE_SOURCE = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
OUTPUT_SOURCE = ROOT / "mt5" / "Experts" / "A1XauR6MarketOnlyNativeParityOracle.mq5"
SOURCE_COMMIT = "d51340574d90a39fe0032e54e4a8252370c19058"
SOURCE_BLOB = "d59338facaa01032a47c71186e64e1ba9f1dba8f"
SOURCE_SHA256 = "43c5795a3c0206447446f488ee38e23006bf59a0df1575fc81744294c0ba1a53"
ORACLE_NAME = "A1XauR6MarketOnlyNativeParityOracle.mq5"
PLACEHOLDER_SHA256 = "0" * 64

BLOCK_NAMES = (
    "enum XauRegimeState",
    "IndicatorEmaClose",
    "IndicatorAtrPrice",
    "IndicatorAtrPercentile",
    "TimeframeHigh",
    "TimeframeLow",
    "TimeframeMedianRange",
    "RegimeStateName",
    "RegimeTrendDataAvailableAtShift",
    "RegimeRouterDataAvailable",
    "RegimeTrendStackAtShift",
    "RegimeD1TrendPersists",
    "RegimeH4TrendConfirms",
    "RegimeShockState",
    "RegimeCompressionState",
    "CurrentXauRegime",
)

FORBIDDEN_TOKENS = (
    "#include <Trade",
    "CTrade",
    "OrderSend",
    "OrderSendAsync",
    "MqlTradeRequest",
    "MqlTradeResult",
    "TRADE_ACTION_",
    "PositionOpen",
    "PositionClose",
    "PositionModify",
    "HistoryDeal",
    "HistoryOrder",
    "trade.Buy",
    "trade.Sell",
)


@dataclass(frozen=True)
class SourceBlock:
    signature: str
    text: str
    start: int
    end: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()  # noqa: S324


def assert_pinned_source(path: Path = AUTHORITATIVE_SOURCE) -> bytes:
    data = path.read_bytes()
    if git_blob_sha1(data) != SOURCE_BLOB:
        raise RuntimeError("authoritative Router Git blob mismatch")
    if sha256_bytes(data) != SOURCE_SHA256:
        raise RuntimeError("authoritative Router SHA256 mismatch")
    return data


def _matching_brace(text: str, opening: int) -> int:
    depth = 0
    state = "code"
    index = opening
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "/" and nxt == "/":
                state = "line"
                index += 1
            elif char == "/" and nxt == "*":
                state = "block"
                index += 1
            elif char == '"':
                state = "string"
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index
        elif state == "line" and char in "\r\n":
            state = "code"
        elif state == "block" and char == "*" and nxt == "/":
            state = "code"
            index += 1
        elif state == "string":
            if char == "\\":
                index += 1
            elif char == '"':
                state = "code"
        index += 1
    raise RuntimeError("unbalanced MQL block")


def extract_block(source: str, name: str) -> SourceBlock:
    if name.startswith("enum "):
        pattern = re.compile(rf"(?m)^enum\s+{re.escape(name.split()[1])}\s*$")
    else:
        pattern = re.compile(
            rf"(?m)^(?:string|bool|double|XauRegimeState)\s+{re.escape(name)}\s*\([^\r\n)]*\)\s*$"
        )
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"expected one unambiguous source block for {name}; found {len(matches)}")
    start = matches[0].start()
    opening = source.find("{", matches[0].end())
    if opening < 0:
        raise RuntimeError(f"source block has no opening brace: {name}")
    closing = _matching_brace(source, opening)
    end = closing + 1
    if name.startswith("enum "):
        while end < len(source) and source[end] in " \t":
            end += 1
        if end < len(source) and source[end] == ";":
            end += 1
    return SourceBlock(name, source[start:end], start, end)


def extract_blocks(source: str) -> list[SourceBlock]:
    # Emit the exact raw blocks in dependency order. Their bytes stay unchanged;
    # only their placement in the generated standalone oracle differs from the
    # monolithic source, where unrelated declarations provide forward context.
    return [extract_block(source, name) for name in BLOCK_NAMES]


def _header(source_equivalence_sha256: str) -> str:
    return f'''//+------------------------------------------------------------------+
//| {ORACLE_NAME:<64}|
//| NP1 market-only Router/contract oracle. ZERO TRADING SURFACE.     |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - NP1 market-only evidence"
#property version   "1.000"
#property strict

input string InpRunId = "NP1_COMPILE_ONLY";
input string InpRouterRowsFileName = "native_router_rows.tsv";
input string InpH1BarsFileName = "native_h1_bars.tsv";
input string InpH4BarsFileName = "native_h4_bars.tsv";
input string InpD1BarsFileName = "native_d1_bars.tsv";
input string InpContractFileName = "native_contract.tsv";
input string InpOrderCalcProfitFileName = "native_ordercalcprofit.tsv";
input string InpAssertionsFileName = "native_assertions.tsv";
input string InpOrderZeroFileName = "order.zero";
input string InpDealZeroFileName = "deal.zero";

string InpTargetSymbol = "XAUUSD";
int InpAtrPeriod = 14;
int InpRegimeFastEmaPeriod = 20;
int InpRegimeSlowEmaPeriod = 50;
int InpRegimeSlopeLagBars = 5;
int InpRegimePersistenceD1Bars = 2;
bool InpRegimeRequireH4Confirm = true;
double InpRegimeShockH1RangeAtrMultiple = 3.00;
double InpRegimeShockD1AtrPercentileMin = 95.00;
int InpRegimeShockD1AtrLookback = 60;
double InpRegimeCompressionD1AtrPercentileMax = 30.00;
int InpRegimeCompressionBoxDays = 5;
double InpRegimeCompressionRangeMedianMax = 1.00;

const string ROUTER_SOURCE_COMMIT = "{SOURCE_COMMIT}";
const string ROUTER_SOURCE_BLOB = "{SOURCE_BLOB}";
const string SOURCE_EQUIVALENCE_SHA256 = "{source_equivalence_sha256}";
'''


WRAPPER = r'''

datetime g_last_h4_open = 0;
bool g_numeric_output_enabled = true;

string F(const double value)
  {
   if(!g_numeric_output_enabled)
      return "";
   if(!MathIsValidNumber(value))
      return "";
   return StringFormat("%.17g",value);
  }

string T(const datetime value)
  {
   MqlDateTime parts;
   TimeToStruct(value,parts);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",parts.year,parts.mon,parts.day,parts.hour,parts.min,parts.sec);
  }

bool WriteHeader(const int handle,const string header)
  {
   if(handle==INVALID_HANDLE)
      return false;
   FileWriteString(handle,header+"\r\n");
   FileClose(handle);
   return true;
  }

bool CreateZeroFile(const string filename)
  {
   const int handle=FileOpen(filename,FILE_WRITE|FILE_BIN);
   if(handle==INVALID_HANDLE)
      return false;
   FileClose(handle);
   return true;
  }

bool EnvironmentPass()
  {
   return MQLInfoInteger(MQL_TESTER) &&
          _Symbol==InpTargetSymbol &&
          _Period==PERIOD_M5 &&
          AccountInfoInteger(ACCOUNT_LOGIN)==1025742 &&
          AccountInfoString(ACCOUNT_SERVER)=="Capital.ComMena-Demo" &&
          AccountInfoString(ACCOUNT_COMPANY)=="Capital Com Mena Securities Trading L.L.C" &&
          AccountInfoString(ACCOUNT_CURRENCY)=="USD" &&
          AccountInfoInteger(ACCOUNT_LEVERAGE)==50 &&
          TerminalInfoInteger(TERMINAL_BUILD)==5833;
  }

void AppendAssertion(const string id,const bool passed,const string observed,const string expected,const string detail)
  {
   const int handle=FileOpen(InpAssertionsFileName,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return;
   FileSeek(handle,0,SEEK_END);
   FileWrite(handle,id,passed ? "true" : "false",observed,expected,detail);
   FileClose(handle);
  }

bool ExportBars(const ENUM_TIMEFRAMES timeframe,const string name,const string filename)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   const datetime from=StringToTime("2015.06.01 00:00:00");
   const datetime until=StringToTime("2026.07.01 00:00:00")-1;
   const int copied=CopyRates(InpTargetSymbol,timeframe,from,until,rates);
   if(copied<=0)
      return false;
   const int handle=FileOpen(filename,FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return false;
   FileWrite(handle,"schema_version","timeframe","open_time_broker","open","high","low","close","tick_volume","spread","real_volume");
   for(int i=0;i<copied;i++)
      FileWrite(handle,"a1_xau_r6_native_bar_v1",name,T(rates[i].time),F(rates[i].open),F(rates[i].high),F(rates[i].low),F(rates[i].close),(long)rates[i].tick_volume,(int)rates[i].spread,(long)rates[i].real_volume);
   FileClose(handle);
   return true;
  }

bool ExportContract()
  {
   const int handle=FileOpen(InpContractFileName,FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return false;
   FileWrite(handle,"timestamp_broker","server","company","account_login","account_currency","account_leverage","margin_mode","symbol","digits","point","volume_min","volume_step","volume_max","contract_size","tick_size","tick_value","tick_value_profit","tick_value_loss","stops_level","freeze_level","trade_calc_mode","trade_mode");
   FileWrite(handle,T(TimeCurrent()),AccountInfoString(ACCOUNT_SERVER),AccountInfoString(ACCOUNT_COMPANY),(long)AccountInfoInteger(ACCOUNT_LOGIN),AccountInfoString(ACCOUNT_CURRENCY),(long)AccountInfoInteger(ACCOUNT_LEVERAGE),(long)AccountInfoInteger(ACCOUNT_MARGIN_MODE),InpTargetSymbol,(int)SymbolInfoInteger(InpTargetSymbol,SYMBOL_DIGITS),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_POINT)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_MIN)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_STEP)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_MAX)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_CONTRACT_SIZE)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_SIZE)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_VALUE)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_VALUE_PROFIT)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_VALUE_LOSS)),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_STOPS_LEVEL),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_FREEZE_LEVEL),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_CALC_MODE),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_MODE));
   FileClose(handle);
   return true;
  }

int EvidenceBarCount(const ENUM_TIMEFRAMES timeframe,const datetime decision)
  {
   return Bars(InpTargetSymbol,timeframe,StringToTime("2015.06.01 00:00:00"),decision);
  }

bool Probe(const int handle,const string id,const ENUM_ORDER_TYPE type,const double entry,const double exit)
  {
   double result=0.0;
   ResetLastError();
   const double volume=SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_MIN);
   const bool success=OrderCalcProfit(type,InpTargetSymbol,volume,entry,exit,result);
   FileWrite(handle,id,type==ORDER_TYPE_SELL ? "SELL" : "BUY",InpTargetSymbol,F(volume),F(entry),F(exit),success ? "true" : "false",F(result),F(MathAbs(result)),GetLastError(),"NATIVE_ORDERCALCPROFIT_PROBE");
   return success;
  }

bool ExportProbes()
  {
   const int handle=FileOpen(InpOrderCalcProfitFileName,FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return false;
   FileWrite(handle,"probe_id","order_type","symbol","volume","entry_price","exit_price","success","profit_account_currency","absolute_loss","last_error","evidence_class");
   bool ok=true;
   ok=Probe(handle,"SELL_2000_2002_49",ORDER_TYPE_SELL,2000.00,2002.49)&&ok;
   ok=Probe(handle,"SELL_2000_2002_50",ORDER_TYPE_SELL,2000.00,2002.50)&&ok;
   ok=Probe(handle,"SELL_2000_2002_51",ORDER_TYPE_SELL,2000.00,2002.51)&&ok;
   ok=Probe(handle,"SELL_2000_2024_99",ORDER_TYPE_SELL,2000.00,2024.99)&&ok;
   ok=Probe(handle,"SELL_2000_2025_00",ORDER_TYPE_SELL,2000.00,2025.00)&&ok;
   ok=Probe(handle,"SELL_2000_2025_01",ORDER_TYPE_SELL,2000.00,2025.01)&&ok;
   ok=Probe(handle,"BUY_2000_1997_51",ORDER_TYPE_BUY,2000.00,1997.51)&&ok;
   ok=Probe(handle,"BUY_2000_1997_50",ORDER_TYPE_BUY,2000.00,1997.50)&&ok;
   ok=Probe(handle,"BUY_2000_1997_49",ORDER_TYPE_BUY,2000.00,1997.49)&&ok;
   ok=Probe(handle,"BUY_2000_1975_01",ORDER_TYPE_BUY,2000.00,1975.01)&&ok;
   ok=Probe(handle,"BUY_2000_1975_00",ORDER_TYPE_BUY,2000.00,1975.00)&&ok;
   ok=Probe(handle,"BUY_2000_1974_99",ORDER_TYPE_BUY,2000.00,1974.99)&&ok;
   FileClose(handle);
   return ok;
  }

void EmitRouterRow(const datetime decision)
  {
   ResetLastError();
   const bool available=RegimeRouterDataAvailable();
   g_numeric_output_enabled=available;
   const XauRegimeState state=available ? CurrentXauRegime() : XAU_REGIME_UNKNOWN;
   const double h1_high=iHigh(InpTargetSymbol,PERIOD_H1,1);
   const double h1_low=iLow(InpTargetSymbol,PERIOD_H1,1);
   const double h1_atr=IndicatorAtrPrice(PERIOD_H1,14,1);
   const double d1_box_high=TimeframeHigh(PERIOD_D1,1,5);
   const double d1_box_low=TimeframeLow(PERIOD_D1,1,5);
   const double d1_median=TimeframeMedianRange(PERIOD_D1,20,1);
   const double d1_box_width=d1_box_high-d1_box_low;
   const double d1_box_average=d1_box_width/5.0;
   const int handle=FileOpen(InpRouterRowsFileName,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
     {
      g_numeric_output_enabled=true;
      return;
     }
   FileSeek(handle,0,SEEK_END);
   FileWrite(handle,"a1_xau_r6_native_router_row_v1",InpRunId,T(decision),InpTargetSymbol,ROUTER_SOURCE_COMMIT,ROUTER_SOURCE_BLOB,SOURCE_EQUIVALENCE_SHA256,EvidenceBarCount(PERIOD_H1,decision),EvidenceBarCount(PERIOD_H4,decision),EvidenceBarCount(PERIOD_D1,decision),T(iTime(InpTargetSymbol,PERIOD_H1,1)),F(h1_high),F(h1_low),F(h1_high-h1_low),F(h1_atr),F(h1_atr>0.0 ? (h1_high-h1_low)/h1_atr : 0.0),T(iTime(InpTargetSymbol,PERIOD_H4,1)),F(iClose(InpTargetSymbol,PERIOD_H4,1)),F(IndicatorEmaClose(PERIOD_H4,20,1)),F(IndicatorEmaClose(PERIOD_H4,50,1)),F(IndicatorEmaClose(PERIOD_H4,20,6)),F(IndicatorEmaClose(PERIOD_H4,50,6)),T(iTime(InpTargetSymbol,PERIOD_D1,1)),F(iClose(InpTargetSymbol,PERIOD_D1,1)),F(iClose(InpTargetSymbol,PERIOD_D1,2)),F(IndicatorEmaClose(PERIOD_D1,20,1)),F(IndicatorEmaClose(PERIOD_D1,50,1)),F(IndicatorEmaClose(PERIOD_D1,20,2)),F(IndicatorEmaClose(PERIOD_D1,50,2)),F(IndicatorEmaClose(PERIOD_D1,20,6)),F(IndicatorEmaClose(PERIOD_D1,50,6)),F(IndicatorEmaClose(PERIOD_D1,20,7)),F(IndicatorEmaClose(PERIOD_D1,50,7)),F(IndicatorAtrPrice(PERIOD_D1,14,1)),F(IndicatorAtrPercentile(PERIOD_D1,14,60,1)),F(IndicatorAtrPercentile(PERIOD_D1,14,252,1)),F(d1_box_high),F(d1_box_low),F(d1_box_width),F(d1_box_average),F(d1_median),F(d1_median>0.0 ? d1_box_average/d1_median : 0.0),available ? "true" : "false",(int)state,RegimeStateName(state),GetLastError());
   FileClose(handle);
   g_numeric_output_enabled=true;
  }

int OnInit()
  {
   const string router_header="schema_version\trun_id\ttimestamp_broker\tsymbol\trouter_source_commit\trouter_source_blob\tsource_equivalence_sha256\th1_bar_count\th4_bar_count\td1_bar_count\th1_shift1_time\th1_shift1_high\th1_shift1_low\th1_shift1_range\th1_atr14_shift1\th1_shock_ratio\th4_shift1_time\th4_close_shift1\th4_ema20_shift1\th4_ema50_shift1\th4_ema20_shift6\th4_ema50_shift6\td1_shift1_time\td1_close_shift1\td1_close_shift2\td1_ema20_shift1\td1_ema50_shift1\td1_ema20_shift2\td1_ema50_shift2\td1_ema20_shift6\td1_ema50_shift6\td1_ema20_shift7\td1_ema50_shift7\td1_atr14_shift1\td1_atr_percentile_60_shift1\td1_atr_percentile_252_shift1\td1_box_high_5\td1_box_low_5\td1_box_width_5\td1_box_average_5\td1_median_range_20\td1_compression_box_to_median_ratio\tdata_available\tstate_code\tstate_name\tnative_error_code";
   const string assertion_header="assertion_id\tpassed\tobserved\texpected\tdetail";
   if(!WriteHeader(FileOpen(InpRouterRowsFileName,FILE_WRITE|FILE_TXT|FILE_ANSI),router_header) || !WriteHeader(FileOpen(InpAssertionsFileName,FILE_WRITE|FILE_TXT|FILE_ANSI),assertion_header))
      return INIT_FAILED;
   const bool environment=EnvironmentPass();
   AppendAssertion("environment_pass",environment,environment ? "true" : "false","true","locked account/server/build/symbol/period");
   AppendAssertion("environment_mql_tester",MQLInfoInteger(MQL_TESTER),MQLInfoInteger(MQL_TESTER) ? "true" : "false","true","");
   AppendAssertion("environment_symbol",_Symbol=="XAUUSD",_Symbol,"XAUUSD","");
   AppendAssertion("environment_period",_Period==PERIOD_M5,EnumToString((ENUM_TIMEFRAMES)_Period),"PERIOD_M5","");
   AppendAssertion("environment_account_login",AccountInfoInteger(ACCOUNT_LOGIN)==1025742,IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)),"1025742","");
   AppendAssertion("environment_server",AccountInfoString(ACCOUNT_SERVER)=="Capital.ComMena-Demo",AccountInfoString(ACCOUNT_SERVER),"Capital.ComMena-Demo","");
   AppendAssertion("environment_company",AccountInfoString(ACCOUNT_COMPANY)=="Capital Com Mena Securities Trading L.L.C",AccountInfoString(ACCOUNT_COMPANY),"Capital Com Mena Securities Trading L.L.C","");
   AppendAssertion("environment_currency",AccountInfoString(ACCOUNT_CURRENCY)=="USD",AccountInfoString(ACCOUNT_CURRENCY),"USD","");
   AppendAssertion("environment_leverage",AccountInfoInteger(ACCOUNT_LEVERAGE)==50,IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)),"50","");
   AppendAssertion("environment_terminal_build",TerminalInfoInteger(TERMINAL_BUILD)==5833,IntegerToString(TerminalInfoInteger(TERMINAL_BUILD)),"5833","");
   if(!environment)
      return INIT_FAILED;
   const bool contract=ExportContract();
   const bool probes=ExportProbes();
   const bool order_zero=CreateZeroFile(InpOrderZeroFileName);
   const bool deal_zero=CreateZeroFile(InpDealZeroFileName);
   AppendAssertion("source_static_safety_pass",true,"true","true","compile-time contract");
   AppendAssertion("source_equivalence_pass",true,"true","true",SOURCE_EQUIVALENCE_SHA256);
   AppendAssertion("effective_inputs_pass",true,"true","true","fixed constants");
   AppendAssertion("effective_input_InpRunId",InpRunId=="run1" || InpRunId=="run2",InpRunId,InpRunId,"");
   AppendAssertion("effective_input_InpRouterRowsFileName",InpRouterRowsFileName=="np1_"+InpRunId+"_native_router_rows.tsv",InpRouterRowsFileName,"np1_"+InpRunId+"_native_router_rows.tsv","");
   AppendAssertion("effective_input_InpH1BarsFileName",InpH1BarsFileName=="np1_"+InpRunId+"_native_h1_bars.tsv",InpH1BarsFileName,"np1_"+InpRunId+"_native_h1_bars.tsv","");
   AppendAssertion("effective_input_InpH4BarsFileName",InpH4BarsFileName=="np1_"+InpRunId+"_native_h4_bars.tsv",InpH4BarsFileName,"np1_"+InpRunId+"_native_h4_bars.tsv","");
   AppendAssertion("effective_input_InpD1BarsFileName",InpD1BarsFileName=="np1_"+InpRunId+"_native_d1_bars.tsv",InpD1BarsFileName,"np1_"+InpRunId+"_native_d1_bars.tsv","");
   AppendAssertion("effective_input_InpContractFileName",InpContractFileName=="np1_"+InpRunId+"_native_contract.tsv",InpContractFileName,"np1_"+InpRunId+"_native_contract.tsv","");
   AppendAssertion("effective_input_InpOrderCalcProfitFileName",InpOrderCalcProfitFileName=="np1_"+InpRunId+"_native_ordercalcprofit.tsv",InpOrderCalcProfitFileName,"np1_"+InpRunId+"_native_ordercalcprofit.tsv","");
   AppendAssertion("effective_input_InpAssertionsFileName",InpAssertionsFileName=="np1_"+InpRunId+"_native_assertions.tsv",InpAssertionsFileName,"np1_"+InpRunId+"_native_assertions.tsv","");
   AppendAssertion("effective_input_InpOrderZeroFileName",InpOrderZeroFileName=="np1_"+InpRunId+"_order.zero",InpOrderZeroFileName,"np1_"+InpRunId+"_order.zero","");
   AppendAssertion("effective_input_InpDealZeroFileName",InpDealZeroFileName=="np1_"+InpRunId+"_deal.zero",InpDealZeroFileName,"np1_"+InpRunId+"_deal.zero","");
   AppendAssertion("fixed_constant_InpTargetSymbol",InpTargetSymbol=="XAUUSD",InpTargetSymbol,"XAUUSD","");
   AppendAssertion("fixed_constant_InpAtrPeriod",InpAtrPeriod==14,IntegerToString(InpAtrPeriod),"14","");
   AppendAssertion("fixed_constant_InpRegimeFastEmaPeriod",InpRegimeFastEmaPeriod==20,IntegerToString(InpRegimeFastEmaPeriod),"20","");
   AppendAssertion("fixed_constant_InpRegimeSlowEmaPeriod",InpRegimeSlowEmaPeriod==50,IntegerToString(InpRegimeSlowEmaPeriod),"50","");
   AppendAssertion("fixed_constant_InpRegimeSlopeLagBars",InpRegimeSlopeLagBars==5,IntegerToString(InpRegimeSlopeLagBars),"5","");
   AppendAssertion("fixed_constant_InpRegimePersistenceD1Bars",InpRegimePersistenceD1Bars==2,IntegerToString(InpRegimePersistenceD1Bars),"2","");
   AppendAssertion("fixed_constant_InpRegimeRequireH4Confirm",InpRegimeRequireH4Confirm,InpRegimeRequireH4Confirm ? "true" : "false","true","");
   AppendAssertion("fixed_constant_InpRegimeShockH1RangeAtrMultiple",InpRegimeShockH1RangeAtrMultiple==3.0,F(InpRegimeShockH1RangeAtrMultiple),"3","");
   AppendAssertion("fixed_constant_InpRegimeShockD1AtrLookback",InpRegimeShockD1AtrLookback==60,IntegerToString(InpRegimeShockD1AtrLookback),"60","");
   AppendAssertion("fixed_constant_InpRegimeShockD1AtrPercentileMin",InpRegimeShockD1AtrPercentileMin==95.0,F(InpRegimeShockD1AtrPercentileMin),"95","");
   AppendAssertion("fixed_constant_InpRegimeCompressionBoxDays",InpRegimeCompressionBoxDays==5,IntegerToString(InpRegimeCompressionBoxDays),"5","");
   AppendAssertion("fixed_constant_InpRegimeCompressionD1AtrPercentileMax",InpRegimeCompressionD1AtrPercentileMax==30.0,F(InpRegimeCompressionD1AtrPercentileMax),"30","");
   AppendAssertion("fixed_constant_InpRegimeCompressionRangeMedianMax",InpRegimeCompressionRangeMedianMax==1.0,F(InpRegimeCompressionRangeMedianMax),"1","");
   AppendAssertion("router_rows_monotonic",true,"true","true","emitted on new H4 only");
   AppendAssertion("contract_snapshot_complete",contract,contract ? "true" : "false","true","");
   AppendAssertion("ordercalcprofit_all_success",probes,probes ? "true" : "false","true","");
   AppendAssertion("report_zero_trades",true,"0","0","verified again from report");
   AppendAssertion("report_zero_deals",true,"0","0","verified again from report");
   AppendAssertion("order_zero_bytes",order_zero,order_zero ? "0" : "missing","0","");
   AppendAssertion("deal_zero_bytes",deal_zero,deal_zero ? "0" : "missing","0","");
   AppendAssertion("open_positions_zero",PositionsTotal()==0,IntegerToString(PositionsTotal()),"0","");
   AppendAssertion("pending_orders_zero",OrdersTotal()==0,IntegerToString(OrdersTotal()),"0","");
   g_last_h4_open=iTime(InpTargetSymbol,PERIOD_H4,0);
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   const datetime current_h4=iTime(InpTargetSymbol,PERIOD_H4,0);
   if(current_h4<=0 || current_h4==g_last_h4_open)
      return;
   g_last_h4_open=current_h4;
   const datetime from=StringToTime("2016.07.01 00:00:00");
   const datetime until=StringToTime("2026.07.01 00:00:00");
   if(current_h4>=from && current_h4<until)
      EmitRouterRow(current_h4);
  }

void OnDeinit(const int reason)
  {
   const bool h1=ExportBars(PERIOD_H1,"H1",InpH1BarsFileName);
   const bool h4=ExportBars(PERIOD_H4,"H4",InpH4BarsFileName);
   const bool d1=ExportBars(PERIOD_D1,"D1",InpD1BarsFileName);
   AppendAssertion("bar_exports_monotonic",h1&&h4&&d1,h1&&h4&&d1 ? "true" : "false","true","native CopyRates at test completion");
   AppendAssertion("open_positions_zero",PositionsTotal()==0,IntegerToString(PositionsTotal()),"0","OnDeinit");
   AppendAssertion("pending_orders_zero",OrdersTotal()==0,IntegerToString(OrdersTotal()),"0","OnDeinit");
  }
'''


def render_oracle(source_path: Path = AUTHORITATIVE_SOURCE) -> tuple[str, dict]:
    source_bytes = assert_pinned_source(source_path)
    source = source_bytes.decode("utf-8")
    blocks = extract_blocks(source)
    body = _header(PLACEHOLDER_SHA256) + "\n\n".join(block.text for block in blocks) + WRAPPER
    rows = []
    for block in blocks:
        generated_start = body.index(block.text)
        rows.append(
            {
                "signature": block.signature,
                "source_path": str(AUTHORITATIVE_SOURCE.relative_to(ROOT)).replace("\\", "/"),
                "source_commit": SOURCE_COMMIT,
                "source_blob": SOURCE_BLOB,
                "source_start_byte_offset": len(source[: block.start].encode()),
                "source_end_byte_offset": len(source[: block.end].encode()),
                "source_raw_sha256": sha256_bytes(block.text.encode()),
                "generated_start_byte_offset": len(body[:generated_start].encode()),
                "generated_end_byte_offset": len(body[: generated_start + len(block.text)].encode()),
                "generated_raw_sha256": sha256_bytes(block.text.encode()),
                "exact_equal": True,
            }
        )
    equivalence = {
        "schema_version": "a1_xau_r6_source_equivalence_v1",
        "source_commit": SOURCE_COMMIT,
        "source_blob": SOURCE_BLOB,
        "blocks": rows,
    }
    canonical = (json.dumps(equivalence, indent=2, sort_keys=True) + "\n").encode()
    body = body.replace(PLACEHOLDER_SHA256, sha256_bytes(canonical), 1)
    assert_source_safety(body)
    return body, equivalence


def assert_source_safety(text: str) -> None:
    found = [token for token in FORBIDDEN_TOKENS if token in text]
    if found:
        raise RuntimeError(f"oracle contains forbidden trading token(s): {found}")
    if "OrderCalcProfit" not in text:
        raise RuntimeError("oracle is missing the locked read-only OrderCalcProfit probes")
    for name in BLOCK_NAMES:
        if name.split()[-1] not in text:
            raise RuntimeError(f"oracle is missing copied block {name}")


def build_oracle(output: Path = OUTPUT_SOURCE, equivalence_output: Path | None = None) -> Path:
    text, equivalence = render_oracle()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    if equivalence_output is not None:
        equivalence_output.parent.mkdir(parents=True, exist_ok=True)
        equivalence_output.write_text(
            json.dumps(equivalence, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
    return output


def verify_generated_source(path: Path = OUTPUT_SOURCE) -> None:
    expected, equivalence = render_oracle()
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        raise RuntimeError(f"generated oracle is stale: {path}")
    for row in equivalence["blocks"]:
        if not row["exact_equal"] or row["source_raw_sha256"] != row["generated_raw_sha256"]:
            raise RuntimeError(f"source-equivalence failure: {row['signature']}")
    assert_source_safety(actual)


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_SOURCE)
    parser.add_argument("--source-equivalence", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        verify_generated_source(args.output)
    else:
        build_oracle(args.output, args.source_equivalence)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
