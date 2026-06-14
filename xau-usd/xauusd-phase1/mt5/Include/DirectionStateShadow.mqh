#ifndef DIRECTION_STATE_SHADOW_MQH
#define DIRECTION_STATE_SHADOW_MQH

#define DIRECTION_STATE_DEFAULT_FILE "dirstate_xauusd.csv"

struct DirectionStateShadowSnapshot
{
   bool available;
   string utc_time;
   string dubai_time;
   int direction;
   string regime;
   double strength;
   double ema_fast;
   double ema_slow;
   double er;
};

string DirectionStateShadowTrim(string value)
{
   StringTrimLeft(value);
   StringTrimRight(value);
   return value;
}

string DirectionStateShadowUnquote(string value)
{
   value = DirectionStateShadowTrim(value);
   StringReplace(value, "\r", "");
   StringReplace(value, "\n", "");
   int length = StringLen(value);
   if(length >= 2 && StringSubstr(value, 0, 1) == "\"" && StringSubstr(value, length - 1, 1) == "\"")
   {
      value = StringSubstr(value, 1, length - 2);
      StringReplace(value, "\"\"", "\"");
   }
   return value;
}

void DirectionStateShadowReset(DirectionStateShadowSnapshot &state)
{
   state.available = false;
   state.utc_time = "";
   state.dubai_time = "";
   state.direction = 0;
   state.regime = "UNKNOWN";
   state.strength = 0.0;
   state.ema_fast = 0.0;
   state.ema_slow = 0.0;
   state.er = 0.0;
}

bool DirectionStateShadowReadLatest(DirectionStateShadowSnapshot &state, const string file_name = DIRECTION_STATE_DEFAULT_FILE)
{
   DirectionStateShadowReset(state);
   int handle = FileOpen(file_name, FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return false;

   string last_line = "";
   while(!FileIsEnding(handle))
   {
      string line = DirectionStateShadowTrim(FileReadString(handle));
      if(line == "" || StringFind(line, "utc_time") == 0)
         continue;
      last_line = line;
   }
   FileClose(handle);

   if(last_line == "")
      return false;

   string fields[];
   int count = StringSplit(last_line, ',', fields);
   if(count < 8)
      return false;

   state.utc_time = DirectionStateShadowUnquote(fields[0]);
   state.dubai_time = DirectionStateShadowUnquote(fields[1]);
   state.direction = (int)StringToInteger(DirectionStateShadowUnquote(fields[2]));
   state.regime = DirectionStateShadowUnquote(fields[3]);
   state.strength = StringToDouble(DirectionStateShadowUnquote(fields[4]));
   state.ema_fast = StringToDouble(DirectionStateShadowUnquote(fields[5]));
   state.ema_slow = StringToDouble(DirectionStateShadowUnquote(fields[6]));
   state.er = StringToDouble(DirectionStateShadowUnquote(fields[7]));
   state.available = true;
   return true;
}

void DirectionStateShadowFieldsForLog(
   string &direction_text,
   string &regime_text,
   string &strength_text,
   const string file_name = DIRECTION_STATE_DEFAULT_FILE
)
{
   DirectionStateShadowSnapshot state;
   DirectionStateShadowReset(state);
   if(DirectionStateShadowReadLatest(state, file_name))
   {
      direction_text = IntegerToString(state.direction);
      regime_text = state.regime;
      strength_text = DoubleToString(state.strength, 3);
      return;
   }
   direction_text = "0";
   regime_text = "UNKNOWN";
   strength_text = "0.000";
}

#endif
