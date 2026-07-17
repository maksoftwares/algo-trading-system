from pathlib import Path

import pandas as pd

from data import load_fred_series


def test_release_lag_is_applied_before_observation_is_available(tmp_path: Path) -> None:
    path = tmp_path / "fred.csv"
    pd.DataFrame(
        {"observation_date": ["2024-01-01", "2024-01-02"], "VALUE": [1.0, 2.0]}
    ).to_csv(path, index=False)

    frame = load_fred_series(path, "VALUE", 7)

    assert frame.loc[0, "available_at"] == pd.Timestamp("2024-01-08", tz="UTC")
    assert frame.loc[1, "available_at"] == pd.Timestamp("2024-01-09", tz="UTC")
