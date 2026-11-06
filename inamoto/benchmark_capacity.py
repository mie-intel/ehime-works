"""Capacity sweep: fixed n and k (spec.py), growing Q. Writes results/capacity.csv and plots/capacity_sweep.png.

    uv run python benchmark_capacity.py              # run every instance, then plot
    uv run python benchmark_capacity.py --plot-only  # re-plot from the saved csv
"""

import csv
import math
import os
import sys
import time

from benchmark import label, lower_bound, save_figure
from solutions.bsta import solve_dsu_bsta
from solutions.pyvrp_solver import solve_pyvrp
from spec import Q_VALUES, SWEEP_K, SWEEP_N
from utils import plt, read_data

SOLVERS = [solve_dsu_bsta, solve_pyvrp]
COLORS = {"solve_dsu_bsta": "tab:blue", "solve_pyvrp": "tab:orange"}
LOWER_BOUND_OF = "solve_dsu_bsta"  # the bound holds for one solver's tours
CSV_PATH = "results/capacity.csv"
FIELDS = ["q", "solver", "makespan", "seconds", "lower_bound"]


def run():
    rows = []
    for q in sorted(Q_VALUES):
        path = f"data/instance-n{SWEEP_N}-k{SWEEP_K}-q{q}.vrp"
        if not os.path.exists(path):
            print(f"missing {path}, run spec.py first")
            continue
        data = read_data(path)
        for solve in SOLVERS:
            start = time.perf_counter()
            try:
                makespan, routes = solve(data)
            except Exception as e:  # keep the sweep going
                print(f"{solve.__name__} failed on q={q}: {e}")
                makespan, routes = math.nan, None
            seconds = time.perf_counter() - start
            rows.append({"q": q, "solver": solve.__name__,
                         "makespan": makespan if math.isfinite(makespan) else math.nan, "seconds": seconds,
                         "lower_bound": lower_bound(routes, data["coords"], SWEEP_K)})
            print(f"q={q:<4} {solve.__name__:<15} makespan={makespan} tours={len(routes) if routes else '-'} time={seconds:.2f}s")
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
        return [{"q": int(r["q"]), "solver": r["solver"], "makespan": float(r["makespan"]),
                 "seconds": float(r["seconds"]), "lower_bound": float(r["lower_bound"])}
                for r in csv.DictReader(f)]


def plot(rows):
    qs = sorted({r["q"] for r in rows})
    table = {(r["solver"], r["q"]): r for r in rows}

    fig, (ax_make, ax_time) = plt.subplots(1, 2, figsize=(12, 4.5))
    for solver in COLORS:
        make = [table[(solver, q)]["makespan"] if (solver, q) in table else math.nan for q in qs]
        secs = [table[(solver, q)]["seconds"] if (solver, q) in table else math.nan for q in qs]
        ax_make.plot(qs, make, marker="o", color=COLORS[solver], label=label(solver))
        ax_time.plot(qs, secs, marker="o", color=COLORS[solver], label=label(solver))
    lb = [table[(LOWER_BOUND_OF, q)]["lower_bound"] if (LOWER_BOUND_OF, q) in table else math.nan for q in qs]
    ax_make.plot(qs, lb, linestyle="--", color="gray", label=f"lower bound ({label(LOWER_BOUND_OF)} tours)")

    ax_make.set_ylabel("makespan")
    ax_make.set_title(f"n={SWEEP_N}, k={SWEEP_K}: makespan vs capacity")
    ax_time.set_ylabel("seconds")
    ax_time.set_yscale("log")
    ax_time.set_title("runtime vs capacity")
    for ax in (ax_make, ax_time):
        ax.set_xscale("log", base=2)
        ax.set_xticks(qs, qs)
        ax.set_xlabel("Q (capacity)")
        ax.grid(alpha=0.3, which="both")
        ax.legend()
    fig.tight_layout()
    save_figure(fig, "capacity_sweep")


def main():
    plot(load_csv() if "--plot-only" in sys.argv else run())


if __name__ == "__main__":
    main()
