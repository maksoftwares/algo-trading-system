import pandas as pd


def test_completed_bucket_is_available_only_after_bucket_end() -> None:
    bucket = pd.Timestamp("2024-01-02T13:00:00Z")
    available = pd.Timestamp("2024-01-02T13:05:00Z")

    assert available > bucket
    assert available - bucket == pd.Timedelta(minutes=5)
