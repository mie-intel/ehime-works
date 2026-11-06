"""held, lkh and pyvrp on the same instances: N (customers) vs K (vehicles), Q fixed. 8 x 8 grid.

    uv run python benchmark/n_vs_k.py [--plot-only]
"""

from common import K_VALUES, N_VALUES, Q_FIXED, make_data, run_grid_benchmark

if __name__ == "__main__":
    run_grid_benchmark("n_vs_k", "N", N_VALUES, "K", K_VALUES, build=lambda n, k: make_data(n, k, Q_FIXED))
