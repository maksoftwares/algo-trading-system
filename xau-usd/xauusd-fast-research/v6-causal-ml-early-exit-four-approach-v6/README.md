# V6 Causal ML Early Exit Four-Approach Campaign

This offline campaign evaluates four distinct responses to the failed V5
cross-asset early-exit model:

1. conservative competing-outcome utility;
2. entry-regime-specific competing-outcome utility;
3. a causal 48-step M5 path representation;
4. unanimous agreement among the first three approaches.

All four arms are locked before inspecting their outcomes. They share the
frozen V1 population, V5 base and cross-asset features, annual purge, action
guards, execution costs, routing, windows, and account-risk gates.

Historical success cannot authorize Python prediction, EA consumption, demo,
live, or broker use.

Run:

```powershell
python run_campaign.py
```

Test:

```powershell
python -m pytest -q
```

The locked campaign completed with no qualifying arm. Approach B produced
positive partial evidence but failed the preregistered stability gates. See
`POST_RUN_DECISION.md` and the generated evidence in `outputs/`.
