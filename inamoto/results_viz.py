"""One overview figure of the benchmark results, aspect 971:408 (no re-run of the grids).

    .venv/bin/python results_viz.py      # writes plots/results/overview.png

Left  (Part 1, Part 2): 2 x 2 heatmaps read from results/n_vs_k.csv (Q = 320) and results/n_vs_q.csv (K = 20).
      "ours" = the better of held and lkh in each cell (letter H or L in the cell, '=' tie), compared against pyvrp.
      column 1: makespan gap of ours vs pyvrp in %  (negative = ours better)
      column 2: speedup = pyvrp seconds / (held + lkh seconds)  (both of ours are counted, since we take the better one)
      Each column shares one colour scale, so Part 1 and Part 2 compare by eye.
Right (Part 3): one instance solved again (routes are not in the CSV): tours coloured by vehicle, plus its Gantt.
"""

import csv
import math
import os
import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LogNorm, TwoSlopeNorm  # noqa: E402

from solutions.bsta import bsta  # noqa: E402
from solutions.dsu_tsp import build_groups  # noqa: E402
from solutions.linesweep_dsu_tsp import solve_group  # noqa: E402
from solutions.lkh_solver import tsp_lk  # noqa: E402
from utils import build_dist_matrix  # noqa: E402
from vrpgen import random_customers  # noqa: E402

OUT = "plots/results/overview_v2.png"  # v1 (overview.png, bigger fonts) is kept
# A1 poster slot: 971 x 408 px at 72 dpi, so 1 pt of font = 1 px on the poster layout
WIDTH, HEIGHT = 971 / 72, 408 / 72  # inches
DPI = 300  # print resolution; the aspect and font sizes stay those of the 72 dpi layout
CELL_FONT = 9  # 64 numbers per heatmap: the only text below 14 pt
LKH_X_MAX = 40  # same as benchmark/common.py
# Part 3 instance: one cell of the N vs K grid (same generator and seed as benchmark/common.py make_data)
P3_N, P3_K, P3_Q = 200, 3, 320

PARTS = [("n_vs_k", "K (vehicles)", "Part 1: N vs K (Q = 320)"), ("n_vs_q", "Q (capacity)", "Part 2: N vs Q (K = 20)")]
VEHICLE_COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]
MERGE = "#B23A6B"
SPEED_TICKS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000)

plt.rcParams.update({"font.size": 15, "axes.titlesize": 17, "axes.titleweight": "bold", "axes.labelsize": 15,
                     "xtick.labelsize": 12, "ytick.labelsize": 12, "font.family": "DejaVu Sans"})


# ---------------------------------------------------------------- Part 1 and 2 (from CSV)
def grids(name):
    with open(f"results/{name}.csv") as f:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    xs = sorted({int(r["x"]) for r in rows})
    ys = sorted({int(r["y"]) for r in rows})
    gap = np.full((len(ys), len(xs)), np.nan)
    speed = np.full_like(gap, np.nan)
    who = np.full(gap.shape, "", dtype=object)
    for r in rows:
        i, j = ys.index(int(r["y"])), xs.index(int(r["x"]))
        h, l, p = r["held_makespan"], r["lkh_makespan"], r["pyvrp_makespan"]
        who[i, j] = "=" if h == l else ("H" if h < l else "L")
        if math.isfinite(p) and p > 0:
            gap[i, j] = (min(h, l) - p) / p * 100
        speed[i, j] = r["pyvrp_seconds"] / (r["held_seconds"] + r["lkh_seconds"])
    return xs, ys, gap, speed, who


def short(v):
    """1000 -> 1k, 1693 -> 1.7k: keeps 4-digit numbers inside one heatmap cell."""
    if v >= 1000:
        return f"{v / 1000:.0f}k" if v % 1000 == 0 or v >= 9500 else f"{v / 1000:.1f}k"
    return f"{v:.0f}"


def text_color(rgba):
    return "white" if 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2] < 0.5 else "black"


def heatmap(ax, grid, xs, ys, ylabel, cmap, norm, fmt, xlabel=True):
    im = ax.imshow(grid, origin="lower", aspect="auto", cmap=cmap, norm=norm)
    for i in range(len(ys)):
        for j in range(len(xs)):
            v = grid[i, j]
            if not np.isfinite(v):
                continue
            c = text_color(im.cmap(im.norm(v)))
            ax.text(j, i, fmt(v), ha="center", va="center", fontsize=CELL_FONT, color=c, fontweight="bold")
    ax.set_xticks(range(len(xs)), [short(x) for x in xs] if xlabel else [])
    ax.set_yticks(range(len(ys)), ys)
    if xlabel:
        ax.set_xlabel("N (customers)")
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return im


def draw_grids(sub):
    data = [grids(name) for name, _, _ in PARTS]
    lim = max(float(np.nanmax(np.abs(g[2]))) for g in data)
    smin = min(float(np.nanmin(g[3])) for g in data)
    smax = max(float(np.nanmax(g[3])) for g in data)
    gap_norm, speed_norm = TwoSlopeNorm(0, -lim, lim), LogNorm(smin, smax)

    axes = sub.subplots(2, 2)
    for row, ((_, ylabel, _), (xs, ys, gap, speed, _)) in enumerate(zip(PARTS, data)):
        a1, a2 = axes[row]
        last = row == len(PARTS) - 1
        im1 = heatmap(a1, gap, xs, ys, ylabel, "RdBu_r", gap_norm, lambda v: f"{v:+.0f}", xlabel=last)
        im2 = heatmap(a2, speed, xs, ys, None, "Greens", speed_norm, short, xlabel=last)
        print(f"{PARTS[row][2]}: ours better in {int(np.sum(gap < 0))}/{gap.size}, median speedup {np.nanmedian(speed):.0f}x")
    axes[0, 0].set_title("Makespan gap vs PyVRP (%)")
    axes[0, 1].set_title("Speedup vs PyVRP (×)")
    sub.colorbar(im1, ax=axes[:, 0], shrink=0.8, aspect=30, pad=0.02)
    cb = sub.colorbar(im2, ax=axes[:, 1], shrink=0.8, aspect=30, pad=0.02)
    ticks = [t for t in SPEED_TICKS if smin <= t <= smax]
    cb.set_ticks(ticks, labels=[short(t) for t in ticks])
    cb.minorticks_off()


# ---------------------------------------------------------------- Part 3 (one instance)
def solve_instance():
    coords, demands = random_customers(P3_N, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    xy = np.asarray(coords, dtype=float)
    random.seed(0)  # benchmark/common.py timed() seeds the same way before each run
    groups = build_groups(build_dist_matrix(coords), demands, P3_Q, LKH_X_MAX, math.inf)
    trips = [solve_group(xy, g, tsp_lk) for g in groups]
    makespan, bundles = bsta([t for _, t in trips], P3_K)
    print(f"part 3: N={P3_N} K={P3_K} Q={P3_Q}: {len(trips)} tours, makespan={makespan}")
    return xy, trips, makespan, bundles


def draw_routes(sub):
    xy, trips, makespan, bundles = solve_instance()
    am, ag = sub.subplots(2, 1, height_ratios=[2.6, 1])

    for v, b in enumerate(bundles):
        col = VEHICLE_COLORS[v % len(VEHICLE_COLORS)]
        for n_tour, i in enumerate(b):  # a vehicle's 2nd, 4th, ... tour dashed, so its tours stay apart
            route = trips[i][0]
            pts = xy[[0] + route + [0]]
            am.plot(pts[:, 0], pts[:, 1], color=col, lw=1.1, ls="-" if n_tour % 2 == 0 else (0, (4, 2)), zorder=2)
            am.scatter(xy[route, 0], xy[route, 1], s=6, c=col, zorder=3)
    am.scatter(0, 0, marker="*", s=220, c="black", zorder=5)
    am.set_aspect("equal")
    am.set_xticks([])
    am.set_yticks([])
    for s in am.spines.values():
        s.set_color("#BBBBBB")
    am.set_title(f"Routes (N={P3_N}, K={P3_K})", fontsize=16)

    for v, b in enumerate(bundles):
        col = VEHICLE_COLORS[v % len(VEHICLE_COLORS)]
        t0 = 0
        for n_tour, i in enumerate(b):
            t = trips[i][1]
            ag.barh(-v, t, left=t0, height=0.62, color=col, ec="white", lw=1.5, alpha=1 if n_tour % 2 == 0 else 0.7)
            if t > makespan * 0.07:
                ag.text(t0 + t / 2, -v, str(t), ha="center", va="center", fontsize=12, color="white", fontweight="bold")
            t0 += t
    ag.axvline(makespan, color=MERGE, lw=2.2, ls="--")
    ag.text(makespan, 0.45, f"T* = {makespan} ", color=MERGE, fontweight="bold", va="bottom", ha="right")
    ag.set_yticks([-v for v in range(len(bundles))], [f"V{v + 1}" for v in range(len(bundles))])
    ag.set_ylim(-len(bundles) + 0.45, 1.15)
    ag.set_xticks([])
    for s in ("top", "right"):
        ag.spines[s].set_visible(False)


def main():
    fig = plt.figure(figsize=(WIDTH, HEIGHT), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.03, h_pad=0.03, wspace=0.02, hspace=0.02)
    left, right = fig.subfigures(1, 2, width_ratios=[2.6, 1.0], wspace=0.0)
    draw_grids(left)
    draw_routes(right)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=DPI, facecolor="white")  # no bbox_inches="tight": it would change the 971:408 aspect
    plt.close(fig)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
