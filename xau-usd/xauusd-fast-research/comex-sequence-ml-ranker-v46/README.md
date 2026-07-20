# COMEX Sequence ML Ranker V46

V46 trains one fixed, low-capacity Python ranker on the earliest V45 development
labels, chooses its acceptance threshold from score density only, and locks the
model before opening a later internal exam.

```powershell
uv run --with-requirements requirements.txt python train_and_lock.py
uv run --with-requirements requirements.txt python run_internal_exam.py
```

`run_stage.py --stage validation` and `--stage exam` remain sealed until every
earlier gate passes. The package cannot authorize execution.
