# V30 Post-Lock MT5 Timestamp Adapter

The locked V30 development run failed before candidate generation because the
older MT5 C02 export stores `time_utc` at whole-second precision while preserving
the exact tick timestamp in `time_msc`. The source audit proved all 500,747 rows
in the first populated file have exact same-second agreement and a 0-999 ms
representation difference.

This adapter changes no V30 event, direction, sampling, fill, horizon, cost, or
gate. It accepts a row only when `floor(time_msc / 1000)` exactly equals the UTC
second encoded by `time_utc`, then uses the locked millisecond field. It writes
the original V30 development output names so the unchanged forward verifier can
consume them.

No economic outcome is opened until this adapter is separately locked.
