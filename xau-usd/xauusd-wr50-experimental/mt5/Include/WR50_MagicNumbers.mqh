#ifndef WR50_MAGIC_NUMBERS_MQH
#define WR50_MAGIC_NUMBERS_MQH

#define WR50_MAGIC_MIN 930000
#define WR50_MAGIC_MAX 930999

#define WR50_BEV0_MAGIC_START 930000
#define WR50_BEV0_MAGIC_END 930099
#define WR50_BEV0_ACTIVE_MAGIC 930000

#define WR50_BQV0_MAGIC_START 930100
#define WR50_BQV0_MAGIC_END 930199
#define WR50_BQV0_ACTIVE_MAGIC 930100

#define WR50_E1R0_MAGIC_START 930200
#define WR50_E1R0_MAGIC_END 930299
#define WR50_E1R0_ACTIVE_MAGIC 930200

bool WR50_ValidateAssignedMagic(const int active_magic,
                                const int magic_start,
                                const int magic_end,
                                const string ea_name,
                                string &reason)
{
   if(active_magic < WR50_MAGIC_MIN || active_magic > WR50_MAGIC_MAX)
   {
      reason = ea_name + ": active magic outside WR50 namespace";
      return false;
   }
   if(magic_start < WR50_MAGIC_MIN || magic_end > WR50_MAGIC_MAX || magic_start > magic_end)
   {
      reason = ea_name + ": assigned magic range outside WR50 namespace";
      return false;
   }
   if(active_magic < magic_start || active_magic > magic_end)
   {
      reason = ea_name + ": active magic outside assigned EA range";
      return false;
   }
   return true;
}

bool WR50_IsWR50Magic(const long magic)
{
   return magic >= WR50_MAGIC_MIN && magic <= WR50_MAGIC_MAX;
}

string WR50_BuildShortComment(const string short_ea_code, const string run_id)
{
   string comment = "WR50|" + short_ea_code + "|" + run_id;
   if(StringLen(comment) > 31)
      comment = StringSubstr(comment, 0, 31);
   return comment;
}

#endif

