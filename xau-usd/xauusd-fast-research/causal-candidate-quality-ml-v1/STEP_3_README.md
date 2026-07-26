# Step 3: Counterfactual Labels And Causal Features

Step 3 replays every canonical candidate and every registered journey action
against the locked Dukascopy executable bid/ask path. It also materializes the
exact 59-column causal feature surface for the canonical population and applies
the actual label-end purges to the six frozen walk-forward folds.

Mandatory XAU features fail closed when their completed lookback is unavailable.
Every raw hour and COMEX day opened by the build is hash-verified and counted in
the source audit.

Run:

```powershell
uv run --no-project --with-requirements requirements-step3.txt python run_step_3_build.py
```

Verify the completed artifact set without rebuilding it:

```powershell
uv run --no-project --with-requirements requirements-step3.txt python verify_step_3.py
```

The journey ledger remains a separately weighted failure diagnostic. It cannot
enter or rescue the primary V1 fit. Step 3 performs no model fitting, threshold
selection, portfolio simulation, demo attachment, or broker action.
