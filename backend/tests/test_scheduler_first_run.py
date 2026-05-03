"""Unit tests for ``_compute_first_run`` — the cadence guard that stops a
quick container restart from triggering redundant scans.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from brand_monitor.scheduler import INITIAL_DELAY_S, _compute_first_run


def _now() -> datetime:
    return datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_never_scanned_keyword_runs_after_grace_delay():
    fr = _compute_first_run(None, frequency_hours=24, now=_now())
    assert fr == _now() + timedelta(seconds=INITIAL_DELAY_S)


def test_recently_scanned_keyword_is_deferred_to_next_due():
    last = _now() - timedelta(hours=2)
    fr = _compute_first_run(last, frequency_hours=24, now=_now())
    # Should fire 22 hours from now, NOT 30 seconds.
    assert fr == last + timedelta(hours=24)
    assert (fr - _now()).total_seconds() > 60


def test_overdue_keyword_falls_back_to_grace_delay():
    last = _now() - timedelta(hours=48)  # 24h overdue
    fr = _compute_first_run(last, frequency_hours=24, now=_now())
    assert fr == _now() + timedelta(seconds=INITIAL_DELAY_S)


def test_naive_last_scan_is_treated_as_utc():
    """``SerpSnapshot.captured_at`` is naive UTC; the helper must align it."""
    naive_last = (_now() - timedelta(hours=10)).replace(tzinfo=None)
    fr = _compute_first_run(naive_last, frequency_hours=24, now=_now())
    expected = _now() - timedelta(hours=10) + timedelta(hours=24)
    assert fr == expected
