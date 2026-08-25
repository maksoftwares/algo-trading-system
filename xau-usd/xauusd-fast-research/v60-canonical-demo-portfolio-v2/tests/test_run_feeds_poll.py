from __future__ import annotations

from run_feeds import effective_poll_seconds


def test_poll_override_does_not_require_locked_config_change() -> None:
    config = {"runtime": {"feed_poll_seconds": 60}}
    assert effective_poll_seconds(config, None) == 60
    assert effective_poll_seconds(config, 5) == 5
    assert effective_poll_seconds(config, 0) == 1
