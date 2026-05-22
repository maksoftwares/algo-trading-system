#ifndef PHASE1_MAGIC_MQH
#define PHASE1_MAGIC_MQH

class CPhase1MagicNumberAllocator
{
public:
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
      return ShellMagic() != BreakoutRetestMagic()
         && ShellMagic() != SwingBreakoutRetestMagic()
         && BreakoutRetestMagic() != SwingBreakoutRetestMagic();
   }
};

#endif
