"""Benchmark: run two solvers on the n x k grid of spec.py, write results/<name>.csv and plots/<name>_*.png.

    uv run python benchmark.py              # run every instance, then plot
    uv run python benchmark.py --plot-only  # re-plot from the saved csv

run_benchmark() is reusable: see benchmark_greedy_vs_bsta.py.
"""

import csv
import math
import os
import sys
import time

import numpy as np
from matplotlib.colors import TwoSlopeNorm

from solutions.bsta import solve_dsu_bsta
from solutions.pyvrp_solver import solve_pyvrp
from spec import K_VALUES, N_VALUES
from utils import PLOT_DIR, plt, read_data, route_distance

FIELDS = ["n", "k", "solver", "makespan", "seconds", "lower_bound"]


def label(solver):
    return solver.removeprefix("solve_")


def lower_bound(routes, coords, k):
    """Best makespan any split of these tours can reach: the longest tour, or an even share of the total."""
    if not routes:
        return math.nan
    times = [route_distance(r, coords) for r in routes]
    return max(max(times), math.ceil(sum(times) / k))


def save_csv(rows, csv_path):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_csv(csv_path):
    with open(csv_path) as f:
        return [
            {"n": int(r["n"]), "k": int(r["k"]), "solver": r["solver"],
             "makespan": float(r["makespan"]), "seconds": float(r["seconds"]),
             "lower_bound": float(r.get("lower_bound", "nan"))}  # csv from before the column existed has none
            for r in csv.DictReader(f)
        ]


def run_grid(solvers, csv_path):
    rows = []
    for n in sorted(N_VALUES):
        for k in sorted(K_VALUES):
            path = f"data/instance-n{n}-k{k}.vrp"
            if not os.path.exists(path):
                print(f"missing {path}, run spec.py first")
                continue
            data = read_data(path)
            for solve in solvers:
                start = time.perf_counter()
                try:
                    makespan, routes = solve(data)
                except Exception as e:  # keep the grid going, e.g. out of memory on a big instance
                    print(f"{solve.__name__} failed on n={n} k={k}: {e}")
                    makespan, routes = math.nan, None
                seconds = time.perf_counter() - start
                rows.append({"n": n, "k": k, "solver": solve.__name__,
                             "makespan": makespan if math.isfinite(makespan) else math.nan, "seconds": seconds,
                             "lower_bound": lower_bound(routes, data["coords"], k)})
                print(f"n={n:<5} k={k:<3} {solve.__name__:<16} makespan={makespan} time={seconds:.2f}s")
            save_csv(rows, csv_path)  # keep progress if a later instance is interrupted
    return rows


def plot_gap_heatmap(table, ns, ks, candidate, baseline, name):
    """Makespan gap of the candidate to the baseline per (n, k); red = candidate worse."""
    gap = np.full((len(ns), len(ks)), np.nan)
    for i, n in enumerate(ns):
        for j, k in enumerate(ks):
            a, b = table.get((candidate, n, k)), table.get((baseline, n, k))
            if a and b and b[0] > 0:
                gap[i, j] = (a[0] - b[0]) / b[0] * 100
    if not np.isfinite(gap).any():
        return
    lim = max(float(np.nanmax(np.abs(gap))), 1.0)

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(gap, cmap="RdBu_r", norm=TwoSlopeNorm(0, -lim, lim), origin="lower", aspect="auto")
    for i in range(len(ns)):
        for j in range(len(ks)):
            if np.isfinite(gap[i, j]):
                ax.text(j, i, f"{gap[i, j]:+.1f}%", ha="center", va="center", fontsize=9)
    ax.set_xticks(range(len(ks)), ks)
    ax.set_yticks(range(len(ns)), ns)
    ax.set_xlabel("k (vehicles)")
    ax.set_ylabel("n (customers)")
    ax.set_title(f"{label(candidate)} vs {label(baseline)}: makespan gap")
    fig.colorbar(im, label="gap % (negative = candidate better)")
    save_figure(fig, f"{name}_gap")


def plot_makespan(table, ns, ks, candidate, baseline, name):
    """Makespan against k, one panel per n."""
    colors = {candidate: "tab:blue", baseline: "tab:orange"}
    fig, axes = plt.subplots(1, len(ns), figsize=(3.6 * len(ns), 3.6), squeeze=False)
    for ax, n in zip(axes[0], ns):
        for solver in (candidate, baseline):
            ys = [table.get((solver, n, k), (math.nan,) * 3)[0] for k in ks]
            ax.plot(ks, ys, marker="o", color=colors[solver], label=label(solver))
        # valid for the candidate's own tours; a solver with other tours (e.g. pyvrp) may sit below it
        lb = [table.get((candidate, n, k), (math.nan,) * 3)[2] for k in ks]
        ax.plot(ks, lb, linestyle="--", color="gray", label=f"lower bound ({label(candidate)} tours)")
        ax.set_title(f"n={n}")
        ax.set_xlabel("k (vehicles)")
        ax.grid(alpha=0.3)
    axes[0][0].set_ylabel("makespan")
    axes[0][0].legend()
    fig.tight_layout()
    save_figure(fig, f"{name}_makespan")


def plot_time(table, ns, ks, candidate, baseline, name):
    """Runtime against n: every k as a faint point, the mean over k as a line."""
    colors = {candidate: "tab:blue", baseline: "tab:orange"}
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for solver in (candidate, baseline):
        mean = []
        for n in ns:
            times = [table[(solver, n, k)][1] for k in ks if (solver, n, k) in table]
            ax.scatter([n] * len(times), times, color=colors[solver], alpha=0.25, s=14)
            mean.append(np.mean(times) if times else math.nan)
        ax.plot(ns, mean, marker="o", color=colors[solver], label=label(solver))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n (customers)")
    ax.set_ylabel("seconds")
    ax.set_title("runtime (line = mean over k)")
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    save_figure(fig, f"{name}_time")


def save_figure(fig, name):
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, f"{name}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"saved plot: {path}")


def plot_all(rows, candidate, baseline, name):
    table = {(r["solver"], r["n"], r["k"]): (r["makespan"], r["seconds"], r["lower_bound"]) for r in rows}
    ns, ks = sorted({r["n"] for r in rows}), sorted({r["k"] for r in rows})
    plot_gap_heatmap(table, ns, ks, candidate, baseline, name)
    plot_makespan(table, ns, ks, candidate, baseline, name)
    plot_time(table, ns, ks, candidate, baseline, name)


def run_benchmark(solvers, candidate, baseline, name):
    """Run `solvers` on the grid (or only re-plot with --plot-only); output files are named after `name`."""
    csv_path = f"results/{name}.csv"
    rows = load_csv(csv_path) if "--plot-only" in sys.argv else run_grid(solvers, csv_path)
    plot_all(rows, candidate, baseline, name)


def main():
    run_benchmark([solve_dsu_bsta, solve_pyvrp], "solve_dsu_bsta", "solve_pyvrp", "benchmark")


if __name__ == "__main__":
    main()
