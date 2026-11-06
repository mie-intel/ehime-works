"""Ablation: same DSU groups and Held-Karp tours, only the step that shares tours among K vehicles differs.

    greedy = solve_dsu_tsp  (repeatedly give the two lightest vehicles' tours to one vehicle)
    bsta   = solve_dsu_bsta (binary search the answer + two-pointer merge)

    uv run python benchmark_greedy_vs_bsta.py              # run every instance, then plot
    uv run python benchmark_greedy_vs_bsta.py --plot-only  # re-plot from the saved csv
"""

from benchmark import run_benchmark
from solutions.bsta import solve_dsu_bsta
from solutions.dsu_tsp import solve_dsu_tsp

X_MAX = 10  # group size, equal for both so they build identical tours


def solve_greedy(data):
    return solve_dsu_tsp(data, x_max=X_MAX, heldkarp_limit=X_MAX)


def solve_bsta(data):
    return solve_dsu_bsta(data, x_max=X_MAX)


if __name__ == "__main__":
    run_benchmark([solve_greedy, solve_bsta], candidate="solve_bsta", baseline="solve_greedy", name="greedy_vs_bsta")
