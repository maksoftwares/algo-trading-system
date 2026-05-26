#ifndef PHASE1_MAGIC_MQH
#define PHASE1_MAGIC_MQH

class CPhase1MagicNumberAllocator
{
public:
   int ReservedRangeMin() const
   {
      return 910000;
   }

   int ReservedRangeMax() const
   {
      return 910999;
   }

   int ShellMagic() const
   {
      return 910000;
   }

   int BreakoutRetestMagic() const
   {
      return 910100;
   }

   int SwingBreakoutRetestMagic() const
   {
      return 910110;
   }

   bool ValidateNamespace() const
   {
      return ValidateReservedRange() && ValidateExternalCollisions();
   }

   bool ValidateReservedRange() const
   {
      return IsReservedPhase1Magic(ShellMagic())
         && IsReservedPhase1Magic(BreakoutRetestMagic())
         && IsReservedPhase1Magic(SwingBreakoutRetestMagic())
         && ShellMagic() != BreakoutRetestMagic()
         && ShellMagic() != SwingBreakoutRetestMagic()
         && BreakoutRetestMagic() != SwingBreakoutRetestMagic();
   }

   bool ValidateExternalCollisions() const
   {
      for(int index = 0; index < PositionsTotal(); index++)
      {
         ulong ticket = PositionGetTicket(index);
         if(ticket == 0)
            continue;
         int magic = (int)PositionGetInteger(POSITION_MAGIC);
         if(IsReservedPhase1Magic(magic) && !IsKnownPhase1Magic(magic))
            return false;
      }

      for(int index = 0; index < OrdersTotal(); index++)
      {
         ulong ticket = OrderGetTicket(index);
         if(ticket == 0)
            continue;
         int magic = (int)OrderGetInteger(ORDER_MAGIC);
         if(IsReservedPhase1Magic(magic) && !IsKnownPhase1Magic(magic))
            return false;
      }

      return true;
   }

   bool IsReservedPhase1Magic(const int magic) const
   {
      return magic >= ReservedRangeMin() && magic <= ReservedRangeMax();
   }

   bool IsKnownPhase1Magic(const int magic) const
   {
      return magic == ShellMagic()
         || magic == BreakoutRetestMagic()
         || magic == SwingBreakoutRetestMagic();
   }
};

#endif
