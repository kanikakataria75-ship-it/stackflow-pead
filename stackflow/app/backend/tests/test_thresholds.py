"""Ex-ante thresholds: a filing can never see a filing made at or after its own timestamp."""
from datetime import datetime, timedelta

import numpy as np
import pytest

from drift.signal import Thresholds, exante_thresholds, quintile

T = datetime(2026, 11, 10, 16, 5, 0)


def pool(n_before=400, seed=1):
    rng = np.random.default_rng(seed)
    ts = np.array([np.datetime64(T - timedelta(minutes=int(m)), "ns") for m in rng.integers(1, 360 * 24 * 60, n_before)])
    return ts, rng.normal(0, 1, n_before)


def test_later_filings_are_invisible_even_same_day():
    ts, sue = pool()
    base = exante_thresholds(ts, sue, T)
    # add filings LATER the same day, one exactly AT T, and far in the future, all with absurd SUE
    later = np.array([np.datetime64(T, "ns"), np.datetime64(T + timedelta(seconds=1), "ns"),
                      np.datetime64(T + timedelta(hours=3), "ns"), np.datetime64(T + timedelta(days=90), "ns")])
    ts2 = np.concatenate([ts, later])
    sue2 = np.concatenate([sue, [1e6, 1e6, -1e6, 1e6]])
    after = exante_thresholds(ts2, sue2, T)
    assert (after.q20, after.q40, after.q60, after.q80, after.n) == (base.q20, base.q40, base.q60, base.q80, base.n)
    assert after.latest_ts_used < T


@pytest.mark.parametrize("seed", range(20))
def test_random_future_noise_never_moves_thresholds(seed):
    ts, sue = pool(seed=seed)
    rng = np.random.default_rng(100 + seed)
    fut = np.array([np.datetime64(T + timedelta(minutes=int(m)), "ns") for m in rng.integers(0, 10_000, 200)])
    a = exante_thresholds(ts, sue, T)
    b = exante_thresholds(np.concatenate([ts, fut]), np.concatenate([sue, rng.normal(5, 3, 200)]), T)
    assert a.q80 == b.q80 and a.n == b.n


def test_window_is_trailing_365_days():
    ts, sue = pool()
    old = np.array([np.datetime64(T - timedelta(days=365, seconds=1), "ns")])
    edge = np.array([np.datetime64(T - timedelta(days=365), "ns")])
    a = exante_thresholds(ts, sue, T)
    assert exante_thresholds(np.concatenate([ts, old]), np.concatenate([sue, [99.0]]), T).n == a.n   # outside
    assert exante_thresholds(np.concatenate([ts, edge]), np.concatenate([sue, [99.0]]), T).n == a.n + 1  # inclusive


def test_minimum_history_enforced():
    ts, sue = pool(n_before=149)
    th = exante_thresholds(ts, sue, T)
    assert not th.ok and th.n == 149 and quintile(3.0, th) is None


def test_quintile_boundaries_match_research_convention():
    th = Thresholds(-1.0, 0.0, 1.0, 2.0, 500, T)
    assert [quintile(x, th) for x in (-1.0, -0.99, 0.0, 1.0, 2.0, 2.0001)] == [1, 2, 2, 3, 4, 5]
