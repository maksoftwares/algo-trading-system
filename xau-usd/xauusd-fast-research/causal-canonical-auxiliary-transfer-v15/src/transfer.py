from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import QuantileTransformer


CONTINUOUS_FEATURES = (
    "spread_atr",
    "quote_intensity_ratio",
    "dir_return_15m_atr",
    "dir_return_1h_atr",
    "dir_return_4h_atr",
    "dir_return_24h_atr",
    "range_1h_atr",
    "dir_tick_imbalance_5m",
    "dir_tick_imbalance_15m",
    "log_stop_atr",
    "target_r",
    "log_hold_hours",
)

PASSTHROUGH_FEATURES = (
    "direction_sign",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "mechanism_break_and_run",
    "mechanism_impulse_retest",
    "mechanism_opening_reversal",
    "mechanic_out_of_domain",
    "target_absent_flag",
    "barrier_only_flag",
)

TRANSFER_SCORE_FEATURES = (
    "aux_expected_r_linear",
    "aux_expected_r_nonlinear",
    "aux_win_probability",
)


def _finite(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    values = frame[list(columns)].to_numpy(dtype=float)
    if np.isinf(values).any():
        raise ValueError(f"{name} contains infinity")


def auxiliary_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=frame.index)
    for output, source in {
        "spread_atr": "spread_atr",
        "quote_intensity_ratio": "quote_intensity_ratio",
        "dir_return_15m_atr": "dir_return_15m_atr",
        "dir_return_1h_atr": "dir_return_1h_atr",
        "dir_return_4h_atr": "dir_return_4h_atr",
        "dir_return_24h_atr": "dir_return_24h_atr",
        "range_1h_atr": "range_1h_atr",
        "dir_tick_imbalance_5m": "dir_tick_imbalance_5m",
        "dir_tick_imbalance_15m": "dir_tick_imbalance_15m",
        "target_r": "action_target_r",
        "direction_sign": "direction_sign",
        "hour_sin": "hour_sin",
        "hour_cos": "hour_cos",
        "weekday_sin": "weekday_sin",
        "weekday_cos": "weekday_cos",
    }.items():
        result[output] = frame[source].astype(float)
    result["log_stop_atr"] = np.log1p(frame["action_stop_atr"].clip(lower=0.0))
    result["log_hold_hours"] = np.log1p(
        frame["action_hold_hours"].clip(lower=0.0, upper=72.0)
    )
    result["mechanism_break_and_run"] = frame[
        "mechanism_break_and_run"
    ].astype(float)
    result["mechanism_impulse_retest"] = frame[
        "mechanism_downside_impulse_retest"
    ].astype(float)
    result["mechanism_opening_reversal"] = frame[
        "mechanism_opening_range_reversal"
    ].astype(float)
    result["mechanic_out_of_domain"] = 0.0
    result["target_absent_flag"] = 0.0
    result["barrier_only_flag"] = 0.0
    _finite(result, (*CONTINUOUS_FEATURES, *PASSTHROUGH_FEATURES), "Auxiliary features")
    return result


def canonical_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=frame.index)
    for output, source in {
        "spread_atr": "xau_spread_last_atr",
        "quote_intensity_ratio": "xau_quote_intensity_ratio_15m_60m",
        "dir_return_15m_atr": "dir_xau_return_15m_atr",
        "dir_return_1h_atr": "dir_xau_return_60m_atr",
        "dir_return_4h_atr": "dir_xau_return_4h_atr",
        "dir_return_24h_atr": "dir_xau_return_24h_atr",
        "range_1h_atr": "xau_range_60m_atr",
        "dir_tick_imbalance_5m": "dir_xau_tick_imbalance_5m",
        "dir_tick_imbalance_15m": "dir_xau_tick_imbalance_15m",
        "target_r": "target_r_filled",
        "direction_sign": "direction_sign",
        "hour_sin": "utc_hour_sin",
        "hour_cos": "utc_hour_cos",
        "weekday_sin": "utc_weekday_sin",
        "weekday_cos": "utc_weekday_cos",
        "target_absent_flag": "target_absent_flag",
        "barrier_only_flag": "barrier_only_flag",
    }.items():
        result[output] = frame[source].astype(float)
    result["log_stop_atr"] = np.log1p(frame["planned_stop_atr"].clip(lower=0.0))
    hold_hours = (
        np.expm1(frame["log1p_observation_cap_minutes"].astype(float)) / 60.0
    ).clip(lower=0.0, upper=72.0)
    result["log_hold_hours"] = np.log1p(hold_hours)
    mechanic = frame["broad_mechanic"].astype(str)
    result["mechanism_break_and_run"] = mechanic.eq(
        "BREAKOUT_OR_VOLATILITY_EXPANSION"
    ).astype(float)
    result["mechanism_impulse_retest"] = mechanic.isin(
        ("TREND_PULLBACK_OR_CONTINUATION", "HEALTH_GATED_PULLBACK_RETEST")
    ).astype(float)
    result["mechanism_opening_reversal"] = mechanic.eq(
        "CHOP_MEAN_REVERSION"
    ).astype(float)
    result["mechanic_out_of_domain"] = mechanic.eq("TRANSITION").astype(float)
    _finite(result, (*CONTINUOUS_FEATURES, *PASSTHROUGH_FEATURES), "Canonical features")
    return result


def exclude_overlapping_episodes(
    auxiliary: pd.DataFrame, canonical: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, int]]:
    aux = auxiliary.copy()
    canon = canonical.copy()
    aux["signal_time"] = pd.to_datetime(aux["signal_time"], utc=True)
    canon["decision_time"] = pd.to_datetime(canon["decision_time"], utc=True)
    canonical_keys = set(
        zip(canon["decision_time"], canon["direction"].astype(str).str.upper())
    )
    overlap = [
        (time, direction.upper()) in canonical_keys
        for time, direction in zip(aux["signal_time"], aux["direction"].astype(str))
    ]
    overlap_mask = pd.Series(overlap, index=aux.index)
    overlap_episodes = set(
        aux.loc[overlap_mask, "structural_episode_id"].astype(str)
    )
    removed = aux["structural_episode_id"].astype(str).isin(overlap_episodes)
    kept = aux.loc[~removed].copy()
    audit = {
        "exact_overlap_events": int(aux.loc[overlap_mask, "event_id"].nunique()),
        "removed_structural_episodes": int(len(overlap_episodes)),
        "removed_events": int(aux.loc[removed, "event_id"].nunique()),
        "removed_actions": int(removed.sum()),
        "kept_actions": int(len(kept)),
        "kept_events": int(kept["event_id"].nunique()),
        "kept_structural_episodes": int(
            kept["structural_episode_id"].nunique()
        ),
        "kept_winners": int(kept["stress_net_r_positive"].astype(bool).sum()),
        "kept_failures": int(
            (~kept["stress_net_r_positive"].astype(bool)).sum()
        ),
    }
    return kept, audit


@dataclass
class DomainNormalizer:
    medians: np.ndarray
    transformer: QuantileTransformer

    @classmethod
    def fit(cls, frame: pd.DataFrame, *, quantiles: int) -> "DomainNormalizer":
        values = frame[list(CONTINUOUS_FEATURES)].to_numpy(dtype=float)
        medians = np.nanmedian(values, axis=0)
        if np.isnan(medians).any():
            raise ValueError("A transfer feature is entirely missing")
        filled = np.where(np.isnan(values), medians, values)
        transformer = QuantileTransformer(
            n_quantiles=min(int(quantiles), len(frame)),
            output_distribution="normal",
            subsample=None,
            random_state=26072715,
        )
        transformer.fit(filled)
        return cls(medians=medians, transformer=transformer)

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        continuous = frame[list(CONTINUOUS_FEATURES)].to_numpy(dtype=float)
        filled = np.where(np.isnan(continuous), self.medians, continuous)
        transformed = self.transformer.transform(filled)
        passthrough = frame[list(PASSTHROUGH_FEATURES)].to_numpy(dtype=float)
        result = np.concatenate([transformed, passthrough], axis=1)
        if not np.isfinite(result).all():
            raise ValueError("Normalized transfer design is not finite")
        return result


@dataclass
class AuxiliaryTransferBundle:
    auxiliary_normalizer: DomainNormalizer
    canonical_normalizer: DomainNormalizer
    ridge: Ridge
    hgb: HistGradientBoostingRegressor
    logistic: LogisticRegression

    @classmethod
    def fit(
        cls,
        auxiliary: pd.DataFrame,
        canonical_fit: pd.DataFrame,
        settings: Mapping[str, Any],
    ) -> "AuxiliaryTransferBundle":
        aux_features = auxiliary_features(auxiliary)
        canonical_feature_frame = canonical_features(canonical_fit)
        aux_normalizer = DomainNormalizer.fit(
            aux_features, quantiles=int(settings["quantile_count"])
        )
        canonical_normalizer = DomainNormalizer.fit(
            canonical_feature_frame, quantiles=int(settings["quantile_count"])
        )
        design = aux_normalizer.transform(aux_features)
        weights = auxiliary["structural_weight"].to_numpy(dtype=float)
        clip = tuple(float(value) for value in settings["target_clip_r"])
        target = auxiliary["stress_net_r"].clip(clip[0], clip[1]).to_numpy(float)
        binary = auxiliary["stress_net_r_positive"].astype(int).to_numpy()
        ridge = Ridge(alpha=float(settings["ridge_alpha"]), fit_intercept=True)
        ridge.fit(design, target, sample_weight=weights)
        hgb = HistGradientBoostingRegressor(**dict(settings["hgb"]))
        hgb.fit(design, target, sample_weight=weights)
        logistic = LogisticRegression(
            C=float(settings["logistic_c"]),
            max_iter=1000,
            solver="lbfgs",
        )
        logistic.fit(design, binary, sample_weight=weights)
        return cls(
            auxiliary_normalizer=aux_normalizer,
            canonical_normalizer=canonical_normalizer,
            ridge=ridge,
            hgb=hgb,
            logistic=logistic,
        )

    def score_canonical(self, frame: pd.DataFrame) -> pd.DataFrame:
        features = canonical_features(frame)
        design = self.canonical_normalizer.transform(features)
        result = pd.DataFrame(index=frame.index)
        result["aux_expected_r_linear"] = self.ridge.predict(design)
        result["aux_expected_r_nonlinear"] = self.hgb.predict(design)
        result["aux_win_probability"] = self.logistic.predict_proba(design)[:, 1]
        if not np.isfinite(result.to_numpy(dtype=float)).all():
            raise ValueError("Auxiliary transfer scores are not finite")
        return result


def add_transfer_scores(
    frame: pd.DataFrame, bundle: AuxiliaryTransferBundle
) -> pd.DataFrame:
    result = frame.copy()
    scores = bundle.score_canonical(result)
    for column in TRANSFER_SCORE_FEATURES:
        result[column] = scores[column]
    return result
