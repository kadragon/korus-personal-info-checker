"""Prove vectorized filter rewrites are output-identical to the originals.

The two dominant costs (_filter_ip_switch, _filter_high_freq_download) iterate
per-row with pandas .iloc + DataFrame boolean masking. The rewrites do the same
window logic on numpy arrays grouped once. Window bounds are kept *bit-identical*:

    original mask:  (t >= t_i) & (t <= t_i + W)
    fast bounds:    lo_i = searchsorted(t, t_i,     "left")    # first t >= t_i
                    hi_i = searchsorted(t, t_i + W, "right")   # first t  > t_i+W
                    window positions = [lo_i, hi_i)

Flag = union of [lo_i, hi_i) over qualifying i (difference-array, vectorized).

Run: uv run python tools/bench_filters_parity.py
"""

from __future__ import annotations

import time
from datetime import datetime

import numpy as np
import pandas as pd

import src.config as cfg
from src.checkers import download_reason_checker as dr
from src.checkers import login_checker as lc
from src.config import DownloadConfig, LoginConfig

RNG = np.random.default_rng(7)


# --------------------------------------------------------------------------- #
# Fast reimplementations                                                       #
# --------------------------------------------------------------------------- #
def _filter_high_freq_fast(df: pd.DataFrame, config: DownloadConfig | None = None):
    if df is None:
        raise ValueError("Input DataFrame cannot be None.")
    if config is None:
        config = DownloadConfig()
    if df.empty:
        return pd.DataFrame(columns=df.columns)

    window = np.timedelta64(1, "h")
    thr = config.frequency_threshold
    flagged: list[np.ndarray] = []

    for _, g in df.groupby(cfg.COL_EMPLOYEE_ID, sort=False):
        oi = g.index.to_numpy()
        raw_t = g[cfg.COL_ACCESS_TIME].to_numpy()
        order = np.argsort(raw_t, kind="mergesort")
        t = raw_t[order]
        oi = oi[order]
        n = t.size
        lo = np.searchsorted(t, t, side="left")
        hi = np.searchsorted(t, t + window, side="right")
        qual = np.nonzero((hi - lo) >= thr)[0]
        if qual.size == 0:
            continue
        diff = np.zeros(n + 1, dtype=np.int64)
        np.add.at(diff, lo[qual], 1)
        np.add.at(diff, hi[qual], -1)
        covered = np.cumsum(diff[:-1]) > 0
        flagged.append(oi[covered])

    if not flagged:
        return pd.DataFrame(columns=df.columns)
    idx = np.sort(np.concatenate(flagged))
    return df.loc[idx].sort_values([cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME])


def _filter_ip_switch_fast(df: pd.DataFrame, config: LoginConfig | None = None):
    if df is None:
        raise ValueError("Input DataFrame cannot be None.")
    if config is None:
        config = LoginConfig()

    window = np.timedelta64(config.ip_switch_window_hours, "h")
    min_ips = config.ip_switch_min_ips
    flagged: list[np.ndarray] = []

    for _, g in df.groupby(cfg.COL_EMPLOYEE_ID, sort=False):
        oi = g.index.to_numpy()
        raw_t = g[cfg.COL_ACCESS_TIME].to_numpy()
        order = np.argsort(raw_t, kind="mergesort")
        t = raw_t[order]
        oi = oi[order]
        ip = g[cfg.COL_IP].to_numpy()[order]
        # factorize IPs; NaN/None -> code -1 (excluded, mirrors .dropna())
        codes, _ = pd.factorize(pd.Series(ip), use_na_sentinel=True)
        n = t.size
        lo = np.searchsorted(t, t, side="left")
        hi = np.searchsorted(t, t + window, side="right")
        diff = np.zeros(n + 1, dtype=np.int64)
        any_q = False
        for i in range(n):
            seg = codes[lo[i]:hi[i]]
            seg = seg[seg >= 0]
            if seg.size and np.unique(seg).size >= min_ips:
                diff[lo[i]] += 1
                diff[hi[i]] -= 1
                any_q = True
        if not any_q:
            continue
        covered = np.cumsum(diff[:-1]) > 0
        flagged.append(oi[covered])

    if not flagged:
        empty_df = pd.DataFrame(columns=df.columns)
        empty_df[cfg.COL_ESTIMATED_REASON] = pd.Series(dtype="str")
        empty_df[cfg.COL_RISK_LEVEL] = pd.Series(dtype="str")
        empty_df[cfg.COL_UNIQUE_IP_COUNT] = pd.Series(dtype="int")
        empty_df[cfg.COL_UNIQUE_SUBNET_COUNT] = pd.Series(dtype="int")
        return empty_df

    idx = np.sort(np.concatenate(flagged))
    result_df = df.loc[idx].sort_values([cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME])
    return lc._estimate_ip_switch_reason(result_df, config)


# --------------------------------------------------------------------------- #
# Fixtures                                                                      #
# --------------------------------------------------------------------------- #
def _ips(n: int) -> np.ndarray:
    a = RNG.choice([192, 10, 172], size=n, p=[0.7, 0.2, 0.1])
    b = np.where(a == 192, 168, RNG.integers(0, 32, n))
    c = RNG.integers(0, 256, n)
    d = RNG.integers(1, 255, n)
    return np.array([f"{w}.{x}.{y}.{z}" for w, x, y, z in zip(a, b, c, d)])


def login_fixture(n_rows: int, n_users: int, burst: bool) -> pd.DataFrame:
    uids = RNG.integers(0, n_users, n_rows)
    base = np.datetime64("2026-05-01T00:00:00")
    if burst:
        # cluster many rows into tight windows to trigger min_ips=3
        offs = (RNG.integers(0, n_users, n_rows) * 60).astype("timedelta64[s]")
    else:
        offs = RNG.integers(0, 31 * 24 * 3600, n_rows).astype("timedelta64[s]")
    ip = _ips(n_rows)
    # inject NaN IPs + duplicate timestamps to stress edge cases
    ip = ip.astype(object)
    nan_idx = RNG.choice(n_rows, size=max(1, n_rows // 50), replace=False)
    ip[nan_idx] = np.nan
    df = pd.DataFrame({
        cfg.COL_EMPLOYEE_ID: np.char.add("E", uids.astype(str)),
        cfg.COL_ACCESS_TIME: base + offs,
        cfg.COL_IP: ip,
    })
    return df


def download_fixture(n_rows: int, n_users: int, burst: bool) -> pd.DataFrame:
    uids = RNG.integers(0, n_users, n_rows)
    base = np.datetime64("2026-05-01T00:00:00")
    if burst:
        offs = (RNG.integers(0, n_users * 4, n_rows) * 30).astype("timedelta64[s]")
    else:
        offs = RNG.integers(0, 31 * 24 * 3600, n_rows).astype("timedelta64[s]")
    df = pd.DataFrame({
        cfg.COL_EMPLOYEE_ID: np.char.add("E", uids.astype(str)),
        cfg.COL_DOWNLOAD_REASON: "x",
        cfg.COL_DOWNLOAD_COUNT: RNG.integers(1, 50, n_rows),
        cfg.COL_ACCESS_TIME: base + offs,
    })
    return df


def _index_set(df: pd.DataFrame) -> set:
    return set(df.index.tolist())


def assert_identical(name: str, a: pd.DataFrame, b: pd.DataFrame, cols=None) -> None:
    sa, sb = _index_set(a), _index_set(b)
    if sa != sb:
        raise AssertionError(
            f"{name}: flagged index sets differ "
            f"(orig={len(sa)} fast={len(sb)} sym_diff={len(sa ^ sb)})")
    if cols:
        a2 = a.sort_index()
        b2 = b.sort_index()
        for c in cols:
            if c in a2.columns and not a2[c].astype(str).equals(b2[c].astype(str)):
                mism = (a2[c].astype(str).values != b2[c].astype(str).values).sum()
                raise AssertionError(f"{name}: column '{c}' differs in {mism} rows")
    print(f"  ✅ {name}: identical ({len(sa)} flagged rows)")


def main() -> None:
    print("=== PARITY: vectorized filters vs originals ===")
    cases = [
        ("high_freq random", lambda: download_fixture(40_000, 1500, False)),
        ("high_freq burst", lambda: download_fixture(40_000, 300, True)),
        ("ip_switch random", lambda: login_fixture(40_000, 1500, False)),
        ("ip_switch burst", lambda: login_fixture(40_000, 200, True)),
    ]
    for name, gen in cases:
        df = gen()
        if name.startswith("high_freq"):
            orig = dr._filter_high_freq_download(df)
            fast = _filter_high_freq_fast(df)
            assert_identical(name, orig, fast)
        else:
            orig = lc._filter_ip_switch(df)
            fast = _filter_ip_switch_fast(df)
            assert_identical(
                name, orig, fast,
                cols=[cfg.COL_ESTIMATED_REASON, cfg.COL_RISK_LEVEL,
                      cfg.COL_UNIQUE_IP_COUNT, cfg.COL_UNIQUE_SUBNET_COUNT])

    # edge cases
    print("\n--- edge cases ---")
    empty = pd.DataFrame({cfg.COL_EMPLOYEE_ID: [], cfg.COL_ACCESS_TIME: [],
                          cfg.COL_IP: []})
    assert_identical("ip empty", lc._filter_ip_switch(empty),
                     _filter_ip_switch_fast(empty))
    single = pd.DataFrame({
        cfg.COL_EMPLOYEE_ID: ["E1"],
        cfg.COL_ACCESS_TIME: [datetime(2026, 5, 1, 9)],
        cfg.COL_IP: ["192.168.1.1"]})
    assert_identical("ip single", lc._filter_ip_switch(single),
                     _filter_ip_switch_fast(single))
    tied = pd.DataFrame({
        cfg.COL_EMPLOYEE_ID: ["E1"] * 4,
        cfg.COL_ACCESS_TIME: [datetime(2026, 5, 1, 9)] * 4,
        cfg.COL_IP: ["1.1.1.1", "2.2.2.2", "3.3.3.3", np.nan]})
    assert_identical("ip tied+nan", lc._filter_ip_switch(tied),
                     _filter_ip_switch_fast(tied),
                     cols=[cfg.COL_ESTIMATED_REASON])

    # speed
    print("\n=== SPEED at 100k rows ===")
    dlf = download_fixture(100_000, 2000, False)
    lf = login_fixture(100_000, 2000, False)
    for name, fn, arg in [
        ("high_freq ORIG", dr._filter_high_freq_download, dlf),
        ("high_freq FAST", _filter_high_freq_fast, dlf),
        ("ip_switch ORIG", lc._filter_ip_switch, lf),
        ("ip_switch FAST", _filter_ip_switch_fast, lf),
    ]:
        t0 = time.perf_counter()
        fn(arg)
        print(f"  {name:<18} {(time.perf_counter()-t0)*1000:>9.1f} ms")

    print("\nALL PARITY CHECKS PASSED ✅")


if __name__ == "__main__":
    main()
