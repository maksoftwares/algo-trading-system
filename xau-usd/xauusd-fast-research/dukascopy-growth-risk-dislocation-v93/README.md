# V93 Growth-Risk Dislocation Campaign

Run only after the source foundation is complete and the two placeholder source
hashes in the config have been replaced with the audited curated hashes.

```powershell
uv run --with pandas --with numpy --with pyarrow --with scipy python lock_contract.py
uv run --with pandas --with numpy --with pyarrow --with scipy python run_research.py discovery
```

Do not run Confirmation or Final unless the prior advancement lock exists and
contains at least one policy. V93 is additive to V59/V60 and targets `>=2/day`;
it does not claim or retest V60's already completed `>=1/day` milestone.
