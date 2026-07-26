# Step 2A: Metadata Repair and Candidate Adapters

This stage repairs the causal clocks, frozen action geometry, pre-policy lineage,
and episode identities required before labels or features may be built.

It retains:

- all 3,752 canonical specialist candidates;
- native R1 guard decisions, including guard rejections;
- all 799 R5 pre-policy candidates, including router rejections;
- 117,534 registered historical action rows from the spot and COMEX research;
- a provenance catalog of historical trade ledgers.

Rejected candidates are not labeled as losses. Alternative actions from the same
market event and strategy-version derivatives are not independent training rows.

Run:

```powershell
uv run --no-project --with-requirements requirements.txt python run_step_2a_repair.py
```

No economic outcome is opened, no feature value or model is built, and no demo
or live runtime file is changed by this stage.
