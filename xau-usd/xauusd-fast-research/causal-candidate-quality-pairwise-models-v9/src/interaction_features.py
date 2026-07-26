from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


ACTION_DESCRIPTOR_COLUMNS = (
    "action_stop_atr",
    "action_target_r",
    "action_hold_hours",
    "action_fast",
    "action_intraday",
    "action_swing",
)
INTERACTION_ACTIONS = (
    ("intraday", "action_intraday"),
    ("swing", "action_swing"),
)


def event_feature_columns(base_features: Sequence[str]) -> list[str]:
    descriptors = set(ACTION_DESCRIPTOR_COLUMNS)
    result = [feature for feature in base_features if feature not in descriptors]
    missing = sorted(descriptors.difference(base_features))
    if missing:
        raise ValueError(f"Base feature surface is missing action descriptors: {missing}")
    return result


def interaction_feature_columns(base_features: Sequence[str]) -> list[str]:
    event_features = event_feature_columns(base_features)
    return [
        f"ix_{action_name}__{feature}"
        for action_name, _ in INTERACTION_ACTIONS
        for feature in event_features
    ]


def add_action_interactions(
    frame: pd.DataFrame, base_features: Sequence[str]
) -> tuple[pd.DataFrame, list[str]]:
    required = set(base_features)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Interaction source is missing base features: {missing}")
    event_features = event_feature_columns(base_features)
    result = frame.copy()
    interaction_columns = interaction_feature_columns(base_features)
    if set(interaction_columns).intersection(result.columns):
        raise ValueError("Interaction feature names collide with source columns")
    event_values = result[event_features].to_numpy(dtype=float)
    if not np.isfinite(event_values).all():
        raise ValueError("Interaction source contains non-finite event features")
    blocks: list[pd.DataFrame] = []
    for action_name, indicator in INTERACTION_ACTIONS:
        multiplier = result[indicator].to_numpy(dtype=float)[:, None]
        values = event_values * multiplier
        columns = [f"ix_{action_name}__{feature}" for feature in event_features]
        blocks.append(pd.DataFrame(values, index=result.index, columns=columns))
    result = pd.concat([result, *blocks], axis=1)
    if not np.isfinite(result[interaction_columns].to_numpy(dtype=float)).all():
        raise ValueError("Generated action interaction features are non-finite")
    return result, interaction_columns
