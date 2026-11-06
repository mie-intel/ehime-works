"""x_max sweep: do longer tours (bigger DSU groups) help dsu_bsta, and what does the TSP cost in time?

Fixed n and k (spec.py), a few capacities, growing x_max. Groups up to HELDKARP_MAX customers are solved
exactly (Held-Karp, 2^m), bigger ones with Lin-Kernighan. pyvrp is run once per capacity as a reference line.
Writes results/xmax.csv and plots/xmax_sweep.png.

    uv run python benchmark_xmax.py              # run, then plot
    uv run python benchmark_xmax.py --plot-only  # re-plot from the saved csv
"""

import csv
import math
import os
import sys
import time

from benchmark import lower_bound, save_figure
from solutions.bsta import solve_dsu_bsta
from solutions.lkh_solver import tsp_lk
from solutions.pyvrp_solver import solve_pyvrp
from spec import SWEEP_K, SWEEP_N
from utils import plt, read_data

Q_VALUES = [320, 1280, 10240]  # instances made by spec.py's capacity sweep
X_MAX_VALUES = [10, 20, 25, 30, 35, 40, 50, 60, 80]
HELDKARP_MAX = 10  # exact TSP up to this group size, Lin-Kernighan beyond
CSV_PATH = "results/xmax.csv"
FIELDS = ["q", "x_max", "solver", "makespan", "seconds", "lower_bound"]  # x_max 0 = not applicable (pyvrp)


def solve_with_xmax(data, x_max):
    return solve_dsu_bsta(data, x_max=x_max, tsp=None if x_max <= HELDKARP_MAX else tsp_lk)


def measure(solve, data, q, x_max, name):
    start = time.perf_counter()
    try:
        makespan, routes = solve(data)
    except Exception as e:  # keep the sweep going
        print(f"{name} failed on q={q} x_max={x_max}: {e}")
        makespan, routes = math.nan, None
    seconds = time.perf_counter() - start
    print(f"q={q:<6} x_max={x_max:<3} {name:<15} makespan={makespan} tours={len(routes) if routes else '-'} time={seconds:.2f}s")
    return {"q": q, "x_max": x_max, "solver": name,
            "makespan": makespan if math.isfinite(makespan) else math.nan, "seconds": seconds,
            "lower_bound": lower_bound(routes, data["coords"], SWEEP_K)}


def run():
    rows = []
    for q in Q_VALUES:
        path = f"data/instance-n{SWEEP_N}-k{SWEEP_K}-q{q}.vrp"
        if not os.path.exists(path):
            print(f"missing {path}, run spec.py first")
            continue
        data = read_data(path)
        for x_max in X_MAX_VALUES:
            rows.append(measure(lambda d: solve_with_xmax(d, x_max), data, q, x_max, "solve_dsu_bsta"))
            save_csv(rows)
        rows.append(measure(solve_pyvrp, data, q, 0, "solve_pyvrp"))
        save_csv(rows)
    return rows


def save_csv(rows):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_csv():
    with open(CSV_PATH) as f:
        return [{"q": int(r["q"]), "x_max": int(r["x_max"]), "solver": r["solver"],
                 "makespan": float(r["makespan"]), "seconds": float(r["seconds"]),
                 "lower_bound": float(r["lower_bound"])}
                for r in csv.DictReader(f)]


def plot(rows):
    qs = sorted({r["q"] for r in rows})
    fig, axes = plt.subplots(2, len(qs), figsize=(4.8 * len(qs), 7.5), squeeze=False)
    for col, q in enumerate(qs):
        ours = sorted((r for r in rows if r["q"] == q and r["solver"] == "solve_dsu_bsta"), key=lambda r: r["x_max"])
        ref = next((r for r in rows if r["q"] == q and r["solver"] == "solve_pyvrp"), None)
        xs = [r["x_max"] for r in ours]
        ax_make, ax_time = axes[0][col], axes[1][col]

        ax_make.plot(xs, [r["makespan"] for r in ours], marker="o", color="tab:blue", label="dsu_bsta")
        ax_make.plot(xs, [r["lower_bound"] for r in ours], linestyle="--", color="gray",
                     label="lower bound (dsu_bsta tours)")
        ax_time.plot(xs, [r["seconds"] for r in ours], marker="o", color="tab:blue", label="dsu_bsta")
        if ref:
            ax_make.axhline(ref["makespan"], linestyle=":", color="tab:orange", label="pyvrp")
            ax_time.axhline(ref["seconds"], linestyle=":", color="tab:orange", label="pyvrp")

        ax_make.set_title(f"n={SWEEP_N}, k={SWEEP_K}, Q={q}")
        ax_make.set_ylabel("makespan")
        ax_time.set_ylabel("seconds")
        ax_time.set_yscale("log")
        for ax in (ax_make, ax_time):
            ax.set_xscale("log", base=2)
            ax.set_xticks(xs, xs)
            ax.set_xlabel("x_max (max customers per group)")
            ax.grid(alpha=0.3, which="both")
            ax.legend()
    fig.tight_layout()
    save_figure(fig, "xmax_sweep")


def main():
    plot(load_csv() if "--plot-only" in sys.argv else run())


if __name__ == "__main__":
    main()
