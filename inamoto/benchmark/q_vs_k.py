"""held, lkh and pyvrp on the same instances: Q (capacity) vs K (vehicles), N fixed. 8 x 8 grid.

    uv run python benchmark/q_vs_k.py [--plot-only]
"""

from common import K_VALUES, N_FIXED, Q_VALUES, make_data, run_grid_benchmark

if __name__ == "__main__":
    run_grid_benchmark("q_vs_k", "Q", Q_VALUES, "K", K_VALUES, build=lambda q, k: make_data(N_FIXED, k, q))
