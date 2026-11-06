"""Poster figures on the tiny instance data/poster-n8-k2.vrp (N=8, K=2).

    python3 poster_viz.py            # writes plots/poster/*.png

1 prune  : one line-sweep step (window, checked edges, kept / pruned)
2 group  : DSU groups, one colour per group
3 solve  : one LK tour per group
4 merge  : binary search strip + Gantt on one shared time axis
No titles: captions go on the poster itself.
"""

import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from solutions.bsta import bsta, bsta_pack  # noqa: E402
from solutions.dsu_tsp import build_groups  # noqa: E402
from solutions.linesweep_dsu_tsp import solve_group  # noqa: E402
from solutions.lkh_solver import tsp_lk  # noqa: E402
from utils import build_dist_matrix, read_data  # noqa: E402

PATH = "data/poster-n8-k2.vrp"
OUT = "plots/poster"
X = 70  # pruning radius: edges longer than X are dropped
X_MAX = 10

# Okabe-Ito colour-blind safe palette, one colour per group
GROUP_COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7"]
MERGE = "#B23A6B"
KEEP, PRUNE, INK, MUTED = "#2E7D32", "#C62828", "#222222", "#8A8A8A"

plt.rcParams.update({"font.size": 15, "axes.titlesize": 19, "axes.titleweight": "bold", "font.family": "DejaVu Sans"})


# ---------------------------------------------------------------- shared drawing
def setup(data):
    xy = np.asarray(data["coords"], dtype=float)
    return xy, build_dist_matrix(data["coords"])


def base_axes(ax, xy, title, labels=True):
    if title:
        ax.set_title(title, pad=10)
    ax.set_aspect("equal")
    ax.set_xlim(-120, 145)
    ax.set_ylim(-118, 118)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#BBBBBB")
    ax.scatter(*xy[0], marker="*", s=420, c="#111111", zorder=6)
    if labels:
        ax.annotate("depot", xy[0], (0, -22), textcoords="offset points", ha="center", fontsize=13)


def draw_nodes(ax, xy, colors=None, demands=None, size=260, ids=True):
    n = len(xy)
    for i in range(1, n):
        c = colors[i] if colors else "#FFFFFF"
        ax.scatter(*xy[i], s=size, c=c, edgecolors=INK, linewidths=1.6, zorder=5)
        if ids:
            ax.text(*xy[i], str(i), ha="center", va="center", fontsize=13, fontweight="bold",
                    color="white" if colors else INK, zorder=7)
        if demands is not None:
            ax.annotate(f"r={demands[i]}", xy[i], (15, -17), textcoords="offset points", ha="left", fontsize=11, color="#555555")


def edge_label(ax, a, b, text, color, fs=13, off=17, frac=0.5, side=1):
    """Label beside the edge midpoint (perpendicular offset), so it never covers the endpoints."""
    v = b - a
    nrm = np.array([-v[1], v[0]]) / (np.hypot(*v) or 1)
    if nrm[0] < 0 or (nrm[0] == 0 and nrm[1] < 0):
        nrm = -nrm
    ax.annotate(text, a + frac * v, tuple(nrm * off * side), textcoords="offset points", ha="center", va="center", fontsize=fs,
                fontweight="bold", color=color, bbox=dict(fc="white", ec="none", pad=1, alpha=0.9), zorder=8)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------- 1. prune (line sweep)
def sweep_frames(xy):
    """Replay the line sweep: for every point, which earlier points are in the window / y-band / kept."""
    n = len(xy)
    order = sorted(range(1, n), key=lambda i: (xy[i, 0], i))
    frames, kept = [], []
    for pos, p in enumerate(order):
        behind = order[:pos]
        window = [q for q in behind if xy[q, 0] >= xy[p, 0] - X]
        band = [q for q in window if abs(xy[q, 1] - xy[p, 1]) <= X]
        checked = [(q, float(np.hypot(*(xy[p] - xy[q])))) for q in band]
        ok = [q for q, d in checked if d <= X]
        kept += [(p, q) for q in ok]
        frames.append({"p": p, "window": window, "band": band, "checked": checked, "kept_so_far": list(kept)})
    return frames, kept


def fig_prune(data):
    xy, d = setup(data)
    n = len(xy)
    frames, kept = sweep_frames(xy)
    brute = {(i, j) for i in range(1, n) for j in range(i + 1, n) if d[i, j] <= X}
    assert {tuple(sorted(e)) for e in kept} == brute, "sweep must equal brute force"

    p = 2  # the one sweep step drawn: customer 2
    f = next(fr for fr in frames if fr["p"] == p)
    fig, ax = plt.subplots(figsize=(6.4, 6))
    base_axes(ax, xy, None)
    x0, y0 = xy[p]
    ax.add_patch(Rectangle((x0 - X, -118), X, 236, color="#7BAFD4", alpha=0.18, lw=0, zorder=0))  # window
    ax.add_patch(Rectangle((x0 - X, y0 - X), X, 2 * X, fill=False, ec="#1F5F99", lw=2.2, ls="--", zorder=1))  # checked box
    ax.axvline(x0, color="#1F5F99", lw=2.8, zorder=1)
    ax.text(x0 - X / 2, 106, "window X", ha="center", color="#1F5F99", fontsize=14, fontweight="bold")
    ax.text(x0 + 3, -110, "sweep line", ha="left", color="#1F5F99", fontsize=12)
    for (a, b) in f["kept_so_far"]:  # edges found at earlier steps, faint
        ax.plot(*zip(xy[a], xy[b]), color=KEEP, lw=1.6, alpha=0.35, zorder=2)
    for ci, (q, dq) in enumerate(f["checked"]):
        good = dq <= X
        ax.plot(*zip(xy[p], xy[q]), color=KEEP if good else PRUNE, lw=3.2 if good else 2.6,
                ls="-" if good else (0, (4, 3)), zorder=3)
        edge_label(ax, xy[p], xy[q], f"{dq:.0f} {'✓' if good else '✗'}", KEEP if good else PRUNE, off=22, side=1 if ci % 2 else -1)
    draw_nodes(ax, xy)
    ax.scatter(*xy[p], s=260, c="#1F5F99", edgecolors=INK, linewidths=1.6, zorder=6)
    ax.text(*xy[p], str(p), ha="center", va="center", fontsize=13, fontweight="bold", color="white", zorder=7)
    save(fig, "1_prune.png")
    d_ = build_dist_matrix(data["coords"])
    return sorted(kept, key=lambda e: (d_[e[0], e[1]], e))


# ---------------------------------------------------------------- 2. group (DSU)
def merge_log(d, demands, Q, kept):
    """Kruskal over kept edges, record accept / reject reason per edge."""
    n = len(d)
    parent, size, load = list(range(n)), [1] * n, [int(q) for q in demands]

    def find(a):
        while parent[a] != a:
            a = parent[a]
        return a

    log = []
    for i, j in sorted(((min(e), max(e)) for e in kept), key=lambda e: (d[e[0], e[1]], e)):
        a, b = find(i), find(j)
        if a == b:
            log.append((i, j, False, "same group"))
        elif load[a] + load[b] > Q:
            log.append((i, j, False, f"load {load[a]}+{load[b]} > Q"))
        elif size[a] + size[b] > X_MAX:
            log.append((i, j, False, "too many nodes"))
        else:
            if size[a] < size[b]:
                a, b = b, a
            parent[b], size[a], load[a] = a, size[a] + size[b], load[a] + load[b]
            log.append((i, j, True, f"load {load[a]}"))
    members = {}
    for c in range(1, n):
        members.setdefault(find(c), []).append(c)
    return log, sorted(members.values(), key=min)


def fig_group(data, kept):
    xy, d = setup(data)
    Q, dem = data["capacity"], data["demands"]
    log, groups = merge_log(d, dem, Q, kept)
    assert sorted(map(sorted, build_groups(d, dem, Q, X_MAX, X))) == groups
    gid = {c: k for k, g in enumerate(groups) for c in g}
    colors = [None] + [GROUP_COLORS[gid[c]] for c in range(1, len(xy))]

    fig, a2 = plt.subplots(figsize=(6.4, 6))
    base_axes(a2, xy, None, labels=False)
    for g in groups:
        for c in g:
            a2.scatter(*xy[c], s=2600, c=colors[c], alpha=0.16, zorder=1)
    for i, j, ok, _ in log:
        if ok:
            a2.plot(*zip(xy[i], xy[j]), color=colors[i], lw=4, zorder=3)
    draw_nodes(a2, xy, colors=colors, demands=dem)
    for k, g in enumerate(groups):
        cx, ymin = xy[g, 0].mean(), xy[g, 1].min()
        a2.text(cx, ymin - 20, f"G{k + 1}: load {sum(dem[c] for c in g)}/{Q}", ha="center", va="top", fontsize=13,
                fontweight="bold", color=GROUP_COLORS[k], zorder=8)

    save(fig, "2_group.png")
    return groups, colors


# ---------------------------------------------------------------- 3. solve (LK per group)
def fig_solve(data, groups):
    xy, d = setup(data)
    trips = [solve_group(xy, g, tsp_lk) for g in groups]  # (route, time)
    fig, ax = plt.subplots(figsize=(6.4, 6))
    base_axes(ax, xy, None)
    for k, (route, t) in enumerate(trips):
        col = GROUP_COLORS[k]
        pts = xy[[0] + route + [0]]
        for a, b in zip(pts[:-1], pts[1:]):
            ax.annotate("", b, a, arrowprops=dict(arrowstyle="-|>", color=col, lw=3.4, shrinkA=14, shrinkB=14, mutation_scale=22,
                                                  connectionstyle="arc3,rad=0.08"), zorder=3)
        c = xy[route].mean(axis=0)
        u = c / np.hypot(*c)
        ax.text(*(c + u * 38), f"T{k + 1} = {t}", ha="center", va="center", fontsize=15, fontweight="bold", color=col,
                bbox=dict(fc="white", ec=col, boxstyle="round,pad=0.25"), zorder=8)
    colors = [None] + [GROUP_COLORS[next(k for k, g in enumerate(groups) if c in g)] for c in range(1, len(xy))]
    draw_nodes(ax, xy, colors=colors)
    save(fig, "3_solve.png")
    return [r for r, _ in trips], [t for _, t in trips]


# ---------------------------------------------------------------- 4. merge (binary search on T)
def bsta_steps(times, K):
    """Same loop as solutions.bsta.bsta, but every probe is recorded."""
    lo, hi = max(times), sum(times)
    steps = []
    while lo < hi:
        mid = (lo + hi) // 2
        ok = bsta_pack(times, K, mid) is not None
        steps.append({"lo": lo, "hi": hi, "mid": mid, "ok": ok})
        lo, hi = (lo, mid) if ok else (mid + 1, hi)
    return steps, lo


def fig_merge(times, K, show=4):
    """One figure, one time axis: binary-search strip on top, final Gantt below, dashed guides from each probe T."""
    steps, t_star = bsta_steps(times, K)
    assert t_star == bsta(times, K)[0]
    _, bundles = bsta(times, K)
    lb0, ub0 = max(times), sum(times)
    probes = steps[:show]

    fig, (st, ax) = plt.subplots(2, 1, figsize=(8, 6.4), sharex=True, gridspec_kw={"height_ratios": [1, 1.25], "hspace": 0.0})
    pad = (ub0 - lb0) * 0.05
    # --- strip
    st.set_xlim(0, ub0 + pad)
    st.set_ylim(-0.9, 1.1)
    st.axis("off")
    st.plot([lb0, ub0], [0, 0], color=INK, lw=4.5, solid_capstyle="butt", zorder=2)
    for v, lab in ((lb0, "LB"), (ub0, "UB")):
        st.plot([v, v], [-0.22, 0.22], color=INK, lw=2.8, zorder=2)
        st.text(v, 0.38, lab, ha="center", fontsize=16, fontweight="bold")
    for r, s_ in enumerate(probes):
        col, mark = (KEEP, "✓") if s_["ok"] else (PRUNE, "✗")
        st.scatter(s_["mid"], 0, s=420, c="white", edgecolors=col, linewidths=2.6, zorder=4)
        st.text(s_["mid"], 0, mark, ha="center", va="center", fontsize=15, fontweight="bold", color=col, zorder=5)
        st.text(s_["mid"], 0.4, str(r + 1), ha="center", va="center", fontsize=13, fontweight="bold", color=col)
    st.text(t_star, 0.82, "T*", ha="center", fontsize=17, fontweight="bold", color=MERGE)
    # --- Gantt
    ncol = {i: GROUP_COLORS[i] for i in range(len(times))}
    for v, b in enumerate(bundles):
        t0 = 0
        for i in b:
            ax.barh(-v, times[i], left=t0, height=0.62, color=ncol[i], ec="white", lw=2, zorder=2)
            ax.text(t0 + times[i] / 2, -v, f"{times[i]}", ha="center", va="center", color="white", fontweight="bold", fontsize=14)
            t0 += times[i]
    ax.set_ylim(-len(bundles) + 0.4, 0.6)
    ax.set_yticks([-v for v in range(len(bundles))])
    ax.set_yticklabels([f"Veh {v + 1}" for v in range(len(bundles))], fontsize=14)
    ax.set_xlabel("time", fontsize=14)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    # --- guides from strip to Gantt (figure-spanning dashed lines)
    for s_ in probes:
        col = KEEP if s_["ok"] else PRUNE
        for a_, y0, y1 in ((st, 0, -0.9), (ax, ax.get_ylim()[1], ax.get_ylim()[0])):
            a_.plot([s_["mid"]] * 2, [y0 - (0.2 if a_ is st else 0), y1], color=col, lw=1.4, ls=(0, (4, 3)), alpha=0.8, zorder=1,
                    clip_on=False)
    for a_, y0, y1 in ((st, 0.7, -0.9), (ax, ax.get_ylim()[1], ax.get_ylim()[0])):
        a_.plot([t_star] * 2, [y0, y1], color=MERGE, lw=3.4, zorder=3, clip_on=False)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.97, bottom=0.12)
    save(fig, "4_merge.png")
    return steps, t_star


def main():
    data = read_data(PATH)
    kept = fig_prune(data)
    groups, colors = fig_group(data, kept)
    routes, times = fig_solve(data, groups)
    steps, t_star = fig_merge(times, data["num_vehicles"])
    print("tour times", times, "T* =", t_star)


if __name__ == "__main__":
    main()
