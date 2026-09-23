# StackFlow Layer 1 — FORWARD RECORD

**Freeze date: 2026-09-21**
**Data file: `forward_record_layer1.csv`** (append-only, machine-written)
**Updater: `scripts/update_forward_record.py`** (idempotent; run monthly)

---

## Status as of 2026-09-21

```
rebalances logged : 0
completed         : 0
pending           : 0
```

**Empty, and correct to be empty.** The panel's last close is 2026-09-18. The first
rebalance under the frozen configuration is **2026-09-30**, which has not yet occurred.

---

## What this file is

This is **the only out-of-sample evidence this project has or will have** until it fills.

Everything else on record — the H1 grid, the overlap-robustness re-run, H1b, and the
temporal split in `results/temporal_split_informative.md` — was generated on data whose
outcomes had already been seen. Those results are **discovery evidence**. They cannot be
upgraded by being re-examined, re-cut, or re-adjudicated, and no amount of additional
analysis on the 2005–2026 panel will change that.

Each row below is generated from a rebalance date that had **not happened** when the
configuration was frozen. That is the entire point, and it is the only property that
distinguishes this file from everything else in the project.

## When it becomes interpretable

**Not for a long time. This is expected, and is not a reason to skip it.**

| milestone | approximate date |
|---|---|
| first rebalance logged (status `pending`) | 2026-09-30 |
| **first completed forward window** (M = 90 sessions) | **~2027-02** |
| ~12 completed windows | ~2028-01 |
| ~22 completed windows (matching the historical fold count) | ~2029-01 |

The frozen M = 90 sessions (~4.3 calendar months) sets the minimum wait before a single
data point is even complete.

**Early entries mean nothing.** One completed window is one observation of a quantity
whose historical cross-sectional dispersion is ~10% — several times larger than the
~0.4% effect being looked for. A handful of rows will be dominated by noise regardless of
which way they point. Do not read the first few entries as evidence in either direction,
and do not modify the frozen configuration in response to them.

## What it will be judged against

Per `results/temporal_split_informative.md` §4, the full-period figure
(**−0.974%**, 72.7% fold consistency) **overstates** what this configuration has delivered
in the last decade. On a dispersion-normalised basis the effect stepped down by roughly
two-thirds after ~2015 and stayed there.

**Judge the forward record against the late-half figures, not the full-sample ones:**

| benchmark | value |
|---|---|
| expected `excluded_vs_universe_pct` | **≈ −0.38%** per rebalance |
| expected share of years negative | **≈ 64%** |
| full-period figure (do **not** use as the expectation) | −0.974%, 72.7% |

A forward record landing near −0.4% would be consistent with the recent decade. Landing
near −1.0% would be better than the recent decade has been. Landing near zero would be
consistent with the effect having decayed further.

## Rules for this file

1. **No backfill, ever.** `update_forward_record.py` enforces a hard guard refusing any
   rebalance date earlier than the freeze date. Pre-freeze history dressed as forward
   data would destroy the file's only value.
2. **No configuration changes in response to what appears here.** The config is frozen
   (`live_config_layer1.md`). Changing it requires a new dated phase with its own
   pre-registration — not an edit.
3. **No re-selection of N/M.** N=20/M=90 was chosen on seen data and is now fixed.
   Adding a second cell later and reporting whichever looks better would reintroduce
   exactly the selection effect this file exists to escape.
4. **Void entries are marked, not deleted** — consistent with `RUN_LOG.md` discipline.

## Column reference (`forward_record_layer1.csv`)

| column | meaning |
|---|---|
| `rebalance_date` | month-end trading date the exclusion was decided on |
| `status` | `pending` until the 90-session window completes, then `complete` |
| `n_live_sectors` | sectors with sufficient data that date (tercile size = `n // 3`) |
| `excluded_sectors` | pipe-separated bottom-tercile sectors — the filter's actual output |
| `forward_window_ends` | trading date 90 sessions after the rebalance |
| `excluded_vs_universe_pct` | **the primary metric.** Negative = filter worked |
| `passed_vs_universe_pct` | pass-through bucket vs universe mean |
| `universe_fwd_vs_nifty500_pct` | equal-weight universe drift vs Nifty 500, for context |
| `logged_at` | date the row was written |

`excluded_sectors` is recorded **at decision time**, before the outcome is known, so the
log also stands as a record of what the filter actually said — not merely how it scored.
