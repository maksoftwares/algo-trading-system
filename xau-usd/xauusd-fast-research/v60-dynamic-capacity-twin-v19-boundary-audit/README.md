# V19 clean-boundary audit

This external verifier checks the operative V19 contract, package and input
hashes, runtime self-hashes, prospective timestamps, supervisor health, V60
status, and read-only authorization. It cannot place orders or authorize
deployment.

Run:

```powershell
python verify_boundary.py
```

Before `2026-08-26T00:00:00Z`, a healthy result is
`WAIT_FOR_CLEAN_BOUNDARY`. After the boundary and one hourly-worker grace
period, only `CLEAN_BOUNDARY_OPENED_READ_ONLY_COLLECTION_ACTIVE` is healthy.
