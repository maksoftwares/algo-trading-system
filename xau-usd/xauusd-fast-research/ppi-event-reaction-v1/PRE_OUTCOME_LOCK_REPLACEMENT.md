# PPI V1 Pre-Outcome Lock Replacement

The first contract hash, `adb60bfc20906fdb440cdc602286bc8d72c446a7e4679b5ecd588f0468f31c83`,
was replaced before any outcome marker, exit, P&L, metric, or strategy score was
created.

Its contract-path enumeration included all XAUUSD acquisition manifests present
under the shared storage root, including the concurrently growing 2010-2014
extension. PPI V1 uses only 2016-07 through 2026-06. The replacement restricts
the manifest set to those exact 120 source months, preventing unrelated future
collection from changing contract verification.

No policy, threshold, event, candidate, execution rule, gate, or stage changed.
