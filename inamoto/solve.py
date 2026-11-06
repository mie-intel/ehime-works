"""Entry point: read an instance and run the chosen solvers (see problem.md)."""

import logging
import sys

from solutions.bruteforce import solve_bruteforce
from solutions.bsta import solve_dsu_bsta
from solutions.dp_subset import solve_dp_subset
from solutions.dsu_tsp import solve_dsu_tsp
from solutions.linesweep_bsta import solve_linesweep_dsu_tsp_bsta
from solutions.linesweep_dsu_tsp import solve_linesweep_dsu_tsp
from solutions.lkh_solver import solve_dsu_lkh
from solutions.milp_solver import solve_milp_bruteforce, solve_milp_tsp_grouping
from solutions.pyvrp_solver import solve_pyvrp
from utils import call_solve_function, compare_results, plot_instance, read_data

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/instance-n6-k2.vrp"
    data = read_data(path)
    plot_instance(data)

    solvers = [
        # solve_bruteforce,
        # solve_dp_subset,
        # solve_dsu_tsp,   # n^2 matrix: only for small n
        # solve_dsu_lkh,
        # solve_pyvrp,
        # solve_linesweep_dsu_tsp,
        # solve_linesweep_dsu_tsp_bsta,
        # solve_dsu_bsta,
        # solve_milp_bruteforce,
        solve_milp_tsp_grouping,
    ]
    results = {f.__name__: call_solve_function(f, data) for f in solvers}
    compare_results(results)


if __name__ == "__main__":
    main()
