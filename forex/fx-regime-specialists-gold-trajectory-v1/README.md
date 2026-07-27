# Forex Regime Specialists — Gold-Trajectory V1

Offline, preregistered research applying the Gold lane's regime ownership and standalone-admission discipline to Forex.

It contains:

- a causal direction/volatility/phase classifier;
- two fixed cross-asset specialists;
- a second hash-locked decomposition of the frozen USDJPY London-session seed into four exclusive regime experts;
- exact M5 bid/ask execution with adverse slippage;
- standalone chronological admission;
- a shared one-position router and loss brakes;
- explicit cash states.

Run from the repository root:

```powershell
python run_fx_regime_specialists.py
python run_fx_session_seed_decomposition.py
```

Each runner verifies its preregistration hashes before joining signals to outcomes. Neither calls MT5 or a broker runtime.
