"""Shared helpers for the scripts in benchmark/: instances made in memory, timed runs, heatmap grids.

Run a script from the project root, e.g.

    uv run python benchmark/n_vs_k.py              # run the grid, then plot
    uv run python benchmark/n_vs_k.py --plot-only  # re-plot from results/<name>.csv
"""

import csv
import math
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # solutions/, utils.py and vrpgen.py live in the project root

import numpy as np  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

from solutions.bsta import solve_dsu_bsta  # noqa: E402
from solutions.lkh_solver import tsp_lk  # noqa: E402
from solutions.pyvrp_solver import solve_pyvrp  # noqa: E402
from utils import PLOT_DIR, plt  # noqa: E402
from vrpgen import random_customers  # noqa: E402

N_VALUES = [10, 20, 50, 100, 200, 400, 700, 1000]  # pyvrp builds n^2 edges, so n stays at 1000
K_VALUES = [1, 2, 3, 5, 10, 20, 50, 100]
Q_VALUES = [10, 20, 40, 80, 160, 320, 640, 1280]  # demands are 1..10, so 10 is the smallest feasible capacity
XMAX_VALUES = [10, 15, 20, 30, 40, 50, 60, 80]

# the value of a parameter that a grid does not vary
N_FIXED, K_FIXED, Q_FIXED = 1000, 20, 320

HELD_X_MAX = 10  # Held-Karp is exact but 2^m per group, so groups stay small
LKH_X_MAX = 40  # Lin-Kernighan copes with bigger groups

SOLVERS = ["held", "lkh", "pyvrp"]
GRID_FIELDS = ["x", "y"] + [f"{s}_{m}" for s in SOLVERS for m in ("makespan", "seconds")]


def make_data(n, k, q, seed=1):
    """Random instance in memory (same points and demands for equal n and seed)."""
    coords, demands = random_customers(n, coord_range=(-100, 100), demand_range=(1, 10), seed=seed)
    return {"name": f"n{n}-k{k}-q{q}", "coords": coords, "demands": demands, "capacity": q, "num_vehicles": k}


def solve_held(data):
    return solve_dsu_bsta(data, x_max=HELD_X_MAX)


def solve_lkh(data, x_max=LKH_X_MAX):
    return solve_dsu_bsta(data, x_max=x_max, tsp=tsp_lk)


SOLVE = {"held": solve_held, "lkh": solve_lkh, "pyvrp": solve_pyvrp}


def timed(solve, data):
    """(makespan, seconds); makespan is nan when the solver fails or finds nothing."""
    random.seed(0)
    start = time.perf_counter()
    try:
        makespan, _ = solve(data)
    except Exception as e:  # keep the grid going
        print(f"  failed: {e}")
        makespan = math.nan
    seconds = time.perf_counter() - start
    return (makespan if math.isfinite(makespan) else math.nan), seconds


def save_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path, int_fields):
    with open(path) as f:
        return [{k: int(v) if k in int_fields else float(v) for k, v in r.items()} for r in csv.DictReader(f)]


def save_figure(fig, name):
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, f"{name}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"saved plot: {path}")


def draw_heatmap(fig, ax, grid, xs, ys, xlabel, ylabel, title, fmt, cmap, norm=None, cbar_label=""):
    """grid[i][j] is the value at x = xs[j], y = ys[i]; small values at the bottom left."""
    im = ax.imshow(grid, origin="lower", aspect="auto", cmap=cmap, norm=norm)
    for i in range(len(ys)):
        for j in range(len(xs)):
            if np.isfinite(grid[i, j]):
                ax.text(j, i, fmt.format(grid[i, j]), ha="center", va="center", fontsize=8)
    ax.set_xticks(range(len(xs)), xs)
    ax.set_yticks(range(len(ys)), ys)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=cbar_label)


def log_norm(grid):
    values = grid[np.isfinite(grid) & (grid > 0)]
    return LogNorm(values.min(), values.max()) if len(values) and values.min() < values.max() else None


def plot_grid(name, xlabel, xs, ylabel, ys, rows):
    table = {(r["x"], r["y"]): r for r in rows}

    def grid_of(value):
        return np.array([[value(table[(x, y)]) if (x, y) in table else np.nan for x in xs] for y in ys])

    makespan = {s: grid_of(lambda r, s=s: r[f"{s}_makespan"]) for s in SOLVERS}
    seconds = {s: grid_of(lambda r, s=s: r[f"{s}_seconds"]) for s in SOLVERS}
    args = (xs, ys, xlabel, ylabel)

    best = np.fmin.reduce(list(makespan.values()))  # best makespan of the three solvers in each cell
    ratio = {s: makespan[s] / best for s in SOLVERS}  # 1.00 = the best solver of that cell
    ratio_norm = log_norm(np.stack(list(ratio.values())))  # one colour scale for all three panels
    seconds_norm = log_norm(np.stack(list(seconds.values())))

    fig, axes = plt.subplots(2, 3, figsize=(21, 12))
    for col, s in enumerate(SOLVERS):
        draw_heatmap(fig, axes[0][col], ratio[s], *args, f"{s}: makespan / best of the three", "{:.2f}", "YlOrRd",
                     ratio_norm, "1.00 = best in the cell")
        draw_heatmap(fig, axes[1][col], seconds[s], *args, f"{s}: seconds", "{:.2f}", "Blues", seconds_norm, "seconds")
    fig.tight_layout()
    save_figure(fig, name)


def run_grid_benchmark(name, xlabel, xs, ylabel, ys, build):
    """Solve every cell once with held, lkh and pyvrp, save results/<name>.csv, plot all three side by side."""
    csv_path = f"results/{name}.csv"
    if "--plot-only" in sys.argv:
        rows = load_csv(csv_path, {"x", "y"})
    else:
        rows = []
        for y in ys:
            for x in xs:
                data = build(x, y)
                row = {"x": x, "y": y}
                for s, solve in SOLVE.items():
                    row[f"{s}_makespan"], row[f"{s}_seconds"] = timed(solve, data)
                rows.append(row)
                print(f"{xlabel}={x:<5} {ylabel}={y:<5} " + "  ".join(
                    f"{s}={row[f'{s}_makespan']} ({row[f'{s}_seconds']:.2f}s)" for s in SOLVERS))
            save_csv(csv_path, GRID_FIELDS, rows)  # keep progress if a later row is interrupted
    plot_grid(name, xlabel, xs, ylabel, ys, rows)
