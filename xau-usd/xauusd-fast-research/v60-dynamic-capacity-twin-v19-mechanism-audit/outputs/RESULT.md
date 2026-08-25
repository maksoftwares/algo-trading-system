# V19 replacement-capacity mechanism audit

Decision: `MECHANISM_PARITY_PASS`

Contract: `fdabc9e2997592b06568bb5e405154abdb3888b921a61d70620e06bde2cb4905`

The frozen replay accepted `FIXTURE_INFERIOR_OCCUPANT` under baseline V60 and
then rejected `FIXTURE_BETTER_REPLACEMENT` because the one-position source
capacity was occupied. Baseline net P&L was exactly `-$10.30`.

The frozen V6 policy vetoed `FIXTURE_INFERIOR_OCCUPANT`, left the source slot
available, and accepted `FIXTURE_BETTER_REPLACEMENT`. Challenger net P&L was
exactly `+$19.70`.

All eight parity assertions passed. The fixture is synthetic and exists only
to prove integration behavior. It is not economic evidence, does not count
toward the prospective gate, and does not authorize deployment or broker
action.
