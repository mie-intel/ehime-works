# How to read the benchmark data

Each grid script solves every instance **once** with three solvers and plots them side by side:

- **held**: `dsu_bsta` (DSU grouping, TSP per group, BSTA to share the tours among the vehicles) with exact Held-Karp, `x_max = 10`
- **lkh**: `dsu_bsta` with Lin-Kernighan, `x_max = 40`
- **pyvrp**: pure PyVRP (HGS), no time limit: it stops after 20000 iterations without a new best solution

The metric is the **makespan**: the time at which the slowest vehicle gets home (a vehicle may drive several
tours; its time is the sum of its tours).

## Scripts

Run from the project root. Add `--plot-only` to redraw the plots from the saved CSV without solving again.
`run_all.sh` runs all four in a row.

| script | x axis | y axis | fixed | compares |
|---|---|---|---|---|
| `n_vs_k.py` | N customers | K vehicles | Q = 320 | held, lkh, pyvrp |
| `n_vs_q.py` | N | Q capacity | K = 20 | held, lkh, pyvrp |
| `q_vs_k.py` | Q | K | N = 1000 | held, lkh, pyvrp |
| `lkh_vs_pyvrp_xmax_vs_q.py` | `x_max` (group size) | Q | N = 1000, K = 20 | lkh, pyvrp |

The values of every axis, the fixed values, and the two `x_max` settings are constants at the top of
`common.py`. Instances are generated in memory (random points in [-100, 100]², demands 1..10, seed 1).

## Output files

For a script named `<name>`:

- `results/<name>.csv`: the raw numbers, one row per cell of the grid.
- `plots/<name>.png`: the heatmaps described below.

### CSV columns

`n_vs_k`, `n_vs_q`, `q_vs_k` (the three 8 x 8 grids):

| column | meaning |
|---|---|
| `x`, `y` | the two parameters of the cell (see the table above for which is which) |
| `held_makespan`, `lkh_makespan`, `pyvrp_makespan` | makespan of each solver (`nan` = the solver failed or found nothing) |
| `held_seconds`, `lkh_seconds`, `pyvrp_seconds` | wall time of each solver, including building the distance matrix |

`lkh_vs_pyvrp_xmax_vs_q.csv`: `x_max`, `q`, `lkh_makespan`, `lkh_seconds`, `pyvrp_makespan`, `pyvrp_seconds`.
pyvrp does not depend on `x_max`, so the same pyvrp numbers repeat on every row of one `q`.

Quick look at a CSV:

```python
import csv

with open("results/n_vs_k.csv") as f:
    for r in csv.DictReader(f):
        m = {s: float(r[f"{s}_makespan"]) for s in ("held", "lkh", "pyvrp")}
        best = min(m.values())
        print(f'x={r["x"]:>5} y={r["y"]:>4}  ' + "  ".join(f"{s}={v / best:.2f}" for s, v in m.items()))
```

## The plot: 2 x 3 heatmaps, one column per solver

Rows (y) and columns (x) are the two parameters; the smallest values are at the bottom left. Each cell has its
number printed in it. The columns are **held**, **lkh**, **pyvrp**, drawn on the **same colour scale** so the
three can be compared by eye.

1. **Top row, makespan / best of the three.** In every cell the best solver of the three gets `1.00` (palest
   colour); another solver with `1.37` has a makespan 37% longer than the best. Find the pale cells in a panel to
   see where that solver wins.
2. **Bottom row, seconds** of each solver (logarithmic scale, darker = slower).

For `lkh_vs_pyvrp_xmax_vs_q` there are two panels: the makespan gap `(lkh - pyvrp) / pyvrp * 100` (negative = lkh
better) and lkh seconds.

## Things to keep in mind when interpreting

- **Different objectives.** pyvrp minimizes the *total distance* of all tours and does not care how the tours are
  shared among the vehicles. We minimize the *makespan*. A negative gap is partly this difference, not only a
  better route quality. With a large Q pyvrp tends to put everything in one huge tour on one vehicle. With K = 1
  the makespan is the total distance, so there the two objectives agree.
- **held vs lkh is two changes at once.** They differ in the TSP method *and* in `x_max` (10 vs 40), so the gap
  between them cannot be credited to one of the two.
- **pyvrp time is not a fixed budget.** It runs until it stops improving, so its seconds grow with N. The speedup
  against pyvrp is therefore much larger for big N.
- **Makespan limits.** If there are fewer tours than vehicles (large K, or very few customers), the makespan is
  just the longest tour, so the solvers tie or nearly tie.
- **x_max caps the group size.** Groups never exceed `x_max` customers, even when Q would allow more. At large Q
  the cells of one row look alike for that reason.
- **Noise.** One instance (one seed) per cell. Lin-Kernighan has a random start, so it is not fully
  deterministic. Differences of a few percent between neighbouring cells are noise.
- **`nan` cells** are blank in the plot: the solver raised an error (printed in the console) or found no
  solution.
- **Lower bounds are not in these files.** See `benchmark_*.py` in the project root for the version that also
  plots a lower bound.
- **Old files.** `results/` and `plots/` may still hold `held_*` / `lkh_*` files from the earlier version with
  pyvrp stopped at 5 s. They are not read by the current scripts.
