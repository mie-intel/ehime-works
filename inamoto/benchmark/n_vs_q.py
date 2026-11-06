"""held, lkh and pyvrp on the same instances: N (customers) vs Q (capacity), K fixed. 8 x 8 grid.

    uv run python benchmark/n_vs_q.py [--plot-only]
"""

from common import K_FIXED, N_VALUES, Q_VALUES, make_data, run_grid_benchmark

if __name__ == "__main__":
    run_grid_benchmark("n_vs_q", "N", N_VALUES, "Q", Q_VALUES, build=lambda n, q: make_data(n, K_FIXED, q))
