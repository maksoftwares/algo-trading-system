# XAUUSD Out-of-Era Replication V1

This research-only lane evaluates unchanged candidate mechanisms on the newly
acquired 2010-2016 Dukascopy XAUUSD Bid/Ask tick period.

The lane has three separate jobs:

1. acquire and hash free public BLS and Yahoo GLD inputs;
2. deterministically normalize only Dukascopy months whose raw acquisition
   manifests already pass the foundation validator;
3. lock the candidate and data contract before any P&L is opened.

No script in this lane may request paid data, use Databento, contact a broker,
or authorize Python, EA, demo, or live execution.

