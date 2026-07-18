# Dukascopy XAU Tick Extension V2

This resumable data-only job extends the verified XAUUSD bid/ask tick archive
from January 2010 through June 2016. It uses the existing official Dukascopy
validator, writes one integrity manifest per complete month, and freezes raw
partitions after validation.

It does not score strategies, inspect P&L, use Databento, authorize payment,
or interact with a broker.

```powershell
python acquire_xau_extension.py --concurrency 4
```

Progress and logs are written below the external storage root under
`extension-v2/` so the job can resume without repository churn.
