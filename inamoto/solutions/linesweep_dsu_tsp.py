"""Scalable DSU + TSP: line-sweep edge generation in doubling distance bands, no n x n matrix."""

import heapq
import logging
import math
from bisect import bisect_left, bisect_right

import numpy as np

from solutions.lkh_solver import tsp_lk

log = logging.getLogger(__name__)


def band_edges(xs, ys, X, lo):
    """Line sweep over x (xs sorted): all position pairs (p, q) with lo < dist <= X."""
    win_y, win_p = [], []  # points within X behind the sweep line, kept sorted by y
    left = 0
    lo2, X2 = (lo * lo if lo >= 0 else -1.0), X * X
    out_d, out_p, out_q = [], [], []
    for p in range(len(xs)):
        x, y = xs[p], ys[p]
        while xs[left] < x - X:
            k = bisect_left(win_y, ys[left])
            while win_p[k] != left:
                k += 1
            del win_y[k], win_p[k]
            left += 1
        for k in range(bisect_left(win_y, y - X), bisect_right(win_y, y + X)):
            q = win_p[k]
            dx, dy = x - xs[q], y - win_y[k]
            d2 = dx * dx + dy * dy
            if lo2 < d2 <= X2:
                out_d.append(d2)
                out_p.append(p)
                out_q.append(q)
        k = bisect_right(win_y, y)
        win_y.insert(k, y)
        win_p.insert(k, p)
    return np.array(out_d), np.array(out_p, dtype=np.int64), np.array(out_q, dtype=np.int64)


def solve_group(xy, g, tsp):
    """Route (customer ids, depot implicit) and its time for one group, using a local distance matrix."""
    P = xy[[0] + g]
    D = np.rint(np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1))).astype(np.int64)
    tour = [1] if len(g) == 1 else tsp(D)
    seq = [0] + tour + [0]
    return [g[i - 1] for i in tour], int(D[seq[:-1], seq[1:]].sum())


def linesweep_groups(xy, demands, Q, x_max):
    """DSU grouping by line sweep, no n x n matrix: lists of customer ids, each within capacity Q and x_max customers."""
    n = len(xy) - 1
    load = [int(q) for q in demands]

    # sweep order: customers sorted by x; position p <-> customer cid[p]
    cid = np.argsort(xy[1:, 0], kind="stable") + 1
    xs, ys = xy[cid, 0].tolist(), xy[cid, 1].tolist()
    cid_l = cid.tolist()

    parent, size = list(range(n + 1)), [1] * (n + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    groups_left = n
    lower_bound = -(-sum(load) // Q)
    W, H = xs[-1] - xs[0], max(ys) - min(ys)
    diag = math.hypot(W, H)
    X = max(1.0, math.sqrt(max(W * H, 1.0) / n))  # about 3 neighbours per point on uniform data
    lo = -1.0
    log.info("sweep: n=%d x_max=%d Q=%d initial X=%.1f", n, x_max, Q, X)

    while True:
        d2, p, q = band_edges(xs, ys, X, lo)
        order = np.lexsort((q, p, d2))  # ascending distance, deterministic ties
        merges = 0
        for pi, qi in zip(p[order].tolist(), q[order].tolist()):
            a, b = find(cid_l[pi]), find(cid_l[qi])
            if a == b or load[a] + load[b] > Q or size[a] + size[b] > x_max:
                continue
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
            load[a] += load[b]
            merges += 1
        groups_left -= merges
        log.info("band (%.1f, %.1f]: %d edges, %d merges, %d groups left", lo, X, len(d2), merges, groups_left)
        if groups_left <= lower_bound or X >= diag or (merges == 0 and len(d2) > 0):
            break
        lo, X = X, X * 2

    members = {}
    for c in range(1, n + 1):
        members.setdefault(find(c), []).append(c)
    log.info("DSU done: %d groups", len(members))
    return list(members.values())


def solve_linesweep_dsu_tsp(data, x_max=10, tsp=tsp_lk):
    xy = np.asarray(data["coords"], dtype=float)
    Q, C = int(data["capacity"]), data["num_vehicles"]

    groups = linesweep_groups(xy, data["demands"], Q, x_max)
    trips = [solve_group(xy, g, tsp) for g in groups]

    # more trips than vehicles: repeatedly give the two lowest-time vehicles' trips to one vehicle
    heap = [(t, k, [r]) for k, (r, t) in enumerate(trips)]
    heapq.heapify(heap)
    k = len(heap)
    while len(heap) > C:
        t1, _, r1 = heapq.heappop(heap)
        t2, _, r2 = heapq.heappop(heap)
        k += 1
        heapq.heappush(heap, (t1 + t2, k, r1 + r2))
    makespan = max(t for t, _, _ in heap)
    log.info("%d trips on %d vehicles, makespan=%d", len(trips), len(heap), makespan)

    return makespan, [r for r, _ in trips]
