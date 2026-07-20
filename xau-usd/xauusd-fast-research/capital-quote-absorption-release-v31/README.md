# Capital Quote Absorption Release V31

V31 tests one tick-path continuation hypothesis: dense, directionally balanced
quote activity that makes little price progress may represent absorption, and a
subsequent release beyond that range may continue over the next 120 seconds.

The July 17 Capital file is used only for outcome-blind frequency calibration.
The unchanged event is then tested on the locked June A1 MT5 tick packet with
real bid/ask execution and fixed slippage. A pass can nominate a separately
frozen forward collector; a failure retires V31 unchanged.

Research only. No model, EA, demo, live, or broker authority is granted.
