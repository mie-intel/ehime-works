"""Both poster grids in one process: N vs K (Q = 320), then N vs Q (K = 20).

The 8 instances with K = 20 and Q = 320 are in both grids; they are solved once (in N vs K) and their
result is reused for N vs Q, so no instance is run twice by the same method.

    uv run python benchmark/poster_grids.py [--plot-only]
"""

from common import K_FIXED, K_VALUES, N_VALUES, Q_FIXED, Q_VALUES, make_data, run_grid_benchmark

if __name__ == "__main__":
    run_grid_benchmark("n_vs_k", "N", N_VALUES, "K", K_VALUES, build=lambda n, k: make_data(n, k, Q_FIXED))
    run_grid_benchmark("n_vs_q", "N", N_VALUES, "Q", Q_VALUES, build=lambda n, q: make_data(n, K_FIXED, q))
