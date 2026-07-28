# EURUSD Neutral GDELT coverage-census result

Date: `2026-07-28`

Status: `PASS_SOURCE_CAPACITY_ONLY`

The preregistered 96-file census completed without loading EURUSD prices,
returns, oracle rows, or P&L. Ninety-five archives passed the strict ZIP,
UTF-8, 27-field, and batch-timestamp contract, for a 98.96% success rate.
Twenty-three of 24 entry dates had all four batches.

The strict central-bank filter retained 790 unique documents. Seventeen dates
contained both ECB and Fed coverage. ECB contributed 57 documents from 53
sources; Fed contributed 733 documents from 375 sources. The largest source
shares were only 3.51% and 3.00%, and the duplicate-document share was zero.
All ten frozen capacity gates passed.

The sole failed archive, batch `20260518230000`, contains a byte sequence that
fails strict UTF-8 decoding. It remains failed and was not repaired with a
looser decoder.

This result proves source capacity, not a trading edge. Its only permitted
next step was a separately locked, source-only transform audit. No signal or
broker action was created.

Manifest SHA-256:
`4b279b62cd25d7c0d01927e0a006742606f5ed42d493cff0a74a57ac89b89be3`.
