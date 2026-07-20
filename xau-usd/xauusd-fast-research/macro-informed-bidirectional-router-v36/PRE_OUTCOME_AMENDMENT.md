# V36 Pre-Outcome Availability Amendment

The first locked dataset build completed before `run_router.py` was executed and
before any V36 model score, policy P&L, gate, ranking, or survivor decision was
calculated. It exposed an input-availability defect: requiring every H1, H4, and
H12 pressure field to be finite dropped all 100,780 action rows.

The causal macro stream contained 137,352 joint M15 timestamps. Finite timestamp
coverage was:

- H1/D2: 99,673 (72.57%);
- H1/D10: 100,691 (73.31%);
- H4/D2: 42,264 (30.77%);
- H4/D10: 39,093 (28.46%);
- H12/D2: 889 (0.65%);
- H12/D10: 0 (0.00%).

The long horizons fail because regular Treasury session gaps violate exact
contiguous-M15 return requirements. No economic outcome was used to make this
determination.

The first availability amendment, before outcomes, was:

- remove H12 fields because their measured input availability is unusable;
- retain the preregistered H1 and H4 DXY/Treasury raw and route-aligned fields;
- require the causal H1/D2 DXY and bond pair and feature age to be finite;
- allow optional H1/D10 and H4 fields to remain missing, which
  HistGradientBoostingRegressor handles natively;
- continue to reject infinity, future timestamps, duplicate actions, and feature
  ages above 15 minutes.

That build retained 60,818 actions and 11,791 events. The subsequent locked router
process stopped before writing any scored artifact or evaluating any policy: the
calibration block beginning 2024-07 had 193 events, below the unchanged minimum of
200. No V36 policy P&L, gate, ranking, or survivor result was calculated or opened.

The second availability amendment does not lower that threshold. It preserves all
frozen V1 action rows and allows every macro field, including feature age, to be
missing when no causal macro observation is available within 15 minutes. Missing
values are native HistGradientBoostingRegressor inputs and therefore require no
imputation. When a macro timestamp is present it must still be no later than the
signal and no older than 15 minutes. Infinity remains prohibited.

All labels, actions, costs, walk-forward boundaries, minimum sample requirements,
model hyperparameters, policies, gates, Core rows, and risk weights remain
unchanged. The amended source and preregistration receive a new contract lock
before `run_router.py` is run again.
