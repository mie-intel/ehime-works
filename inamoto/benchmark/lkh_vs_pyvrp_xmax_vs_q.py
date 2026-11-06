"""dsu_bsta with Lin-Kernighan TSP vs pyvrp: x_max (group size) vs Q (capacity), N and K fixed. 8 x 8 grid.

pyvrp does not depend on x_max, so it runs once per Q. Left heatmap: makespan gap of lkh to pyvrp
(negative = lkh better). Right heatmap: lkh seconds.

    uv run python benchmark/lkh_vs_pyvrp_xmax_vs_q.py [--plot-only]
"""

import sys

from common import (K_FIXED, N_FIXED, Q_VALUES, XMAX_VALUES, draw_heatmap, load_csv, log_norm, make_data, np,
                    plt, save_csv, save_figure, solve_lkh, timed)
from matplotlib.colors import TwoSlopeNorm
from solutions.pyvrp_solver import solve_pyvrp

NAME = "lkh_vs_pyvrp_xmax_vs_q"
CSV_PATH = f"results/{NAME}.csv"
FIELDS = ["x_max", "q", "lkh_makespan", "lkh_seconds", "pyvrp_makespan", "pyvrp_seconds"]


def run():
    rows = []
    for q in Q_VALUES:
        data = make_data(N_FIXED, K_FIXED, q)
        pyvrp_makespan, pyvrp_seconds = timed(solve_pyvrp, data)
        for x_max in XMAX_VALUES:
            makespan, seconds = timed(lambda d: solve_lkh(d, x_max), data)
            rows.append({"x_max": x_max, "q": q, "lkh_makespan": makespan, "lkh_seconds": seconds,
                         "pyvrp_makespan": pyvrp_makespan, "pyvrp_seconds": pyvrp_seconds})
            print(f"Q={q:<5} x_max={x_max:<3} lkh={makespan} ({seconds:.2f}s)  pyvrp={pyvrp_makespan} ({pyvrp_seconds:.2f}s)")
        save_csv(CSV_PATH, FIELDS, rows)
    return rows


def plot(rows):
    table = {(r["x_max"], r["q"]): r for r in rows}
    gap = np.array([[(table[(x, q)]["lkh_makespan"] - table[(x, q)]["pyvrp_makespan"]) / table[(x, q)]["pyvrp_makespan"] * 100
                     if (x, q) in table else np.nan for x in XMAX_VALUES] for q in Q_VALUES])
    seconds = np.array([[table[(x, q)]["lkh_seconds"] if (x, q) in table else np.nan for x in XMAX_VALUES]
                        for q in Q_VALUES])

    fig, (ax_gap, ax_time) = plt.subplots(1, 2, figsize=(16, 6.5))
    lim = max(float(np.nanmax(np.abs(gap))), 1.0) if np.isfinite(gap).any() else 1.0
    draw_heatmap(fig, ax_gap, gap, XMAX_VALUES, Q_VALUES, "x_max", "Q", "lkh vs pyvrp: makespan gap", "{:+.0f}%",
                 "RdBu_r", TwoSlopeNorm(0, -lim, lim), "gap % (negative = lkh better)")
    draw_heatmap(fig, ax_time, seconds, XMAX_VALUES, Q_VALUES, "x_max", "Q", "lkh: seconds", "{:.2f}",
                 "YlOrRd", log_norm(seconds), "seconds")
    fig.suptitle(f"n={N_FIXED}, k={K_FIXED}")
    fig.tight_layout()
    save_figure(fig, NAME)


if __name__ == "__main__":
    plot(load_csv(CSV_PATH, {"x_max", "q"}) if "--plot-only" in sys.argv else run())
