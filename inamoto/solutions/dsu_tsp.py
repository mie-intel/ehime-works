"""DSU clustering + per-group exact TSP solver."""

import logging
import math

import numpy as np

from utils import build_dist_matrix

log = logging.getLogger(__name__)


def build_groups(d, demands, Q, x_max, X):
    """Kruskal-style DSU clustering over customer edges with d <= X."""
    n = len(d)
    parent = list(range(n))
    size = [1] * n
    load = [int(q) for q in demands]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        a, b = find(a), find(b)
        if a == b or load[a] + load[b] > Q or size[a] + size[b] > x_max:
            return False
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
        load[a] += load[b]
        return True

    # all customer pairs with d <= X, ascending by (d, i, j)
    d = np.asarray(d)
    ei, ej = np.triu_indices(n - 1, k=1)
    ei, ej = ei + 1, ej + 1
    w = d[ei, ej]
    keep = w <= X
    ei, ej, w = ei[keep], ej[keep], w[keep]
    order = np.lexsort((ej, ei, w))
    for i, j in zip(ei[order].tolist(), ej[order].tolist()):
        union(i, j)

    g = {}
    for i in range(1, n):
        g.setdefault(find(i), []).append(i)
    gs = list(g.values())
    log.info("DSU clustering: %d edges <= X, %d groups", len(order), len(gs))
    return gs


def heldkarp_tables(D, limit):
    """Held-Karp tables over every customer subset. D: (m+1)x(m+1), index 0 = depot.

    dp[mask, j] = shortest path depot -> ... -> customer j+1 visiting exactly the customers in mask (bit j = customer j+1).
    """
    m = len(D) - 1
    if m > limit:
        raise ValueError(f"Held-Karp group size {m} exceeds limit {limit}")
    INF = 10**12
    C = D[1:, 1:]
    dp = np.full((1 << m, m), INF, dtype=np.int64)
    par = np.full((1 << m, m), -1, dtype=np.int8)
    js = np.arange(m)
    dp[1 << js, js] = D[0, 1:]

    # masks grouped by popcount: a layer only depends on the previous one, so each (layer, j) is one numpy op
    masks = np.arange(1 << m)
    popcount = np.zeros(1 << m, dtype=np.int64)
    for j in range(m):
        popcount += (masks >> j) & 1
    layers = np.split(masks[np.argsort(popcount, kind="stable")], np.cumsum(np.bincount(popcount))[:-1])

    for layer in layers[2:]:
        for j in range(m):
            sub = layer[((layer >> j) & 1).astype(bool)]
            cand = dp[sub ^ (1 << j)] + C[:, j]
            dp[sub, j] = cand.min(axis=1)
            par[sub, j] = cand.argmin(axis=1)
    return dp, par


def heldkarp_tour(D, dp, par, mask):
    """Best tour (depot implicit) over the customers in mask, read from the tables."""
    j = int((dp[mask] + D[1:, 0]).argmin())
    tour = []
    while j != -1:
        tour.append(j + 1)
        prev_j = int(par[mask, j])
        mask ^= 1 << j
        j = prev_j
    return tour[::-1]


def tsp_heldkarp(D, limit):
    """Exact TSP via Held-Karp. D: (m+1)x(m+1), index 0 = depot. Returns tour over 1..m."""
    dp, par = heldkarp_tables(D, limit)
    return heldkarp_tour(D, dp, par, (1 << (len(D) - 1)) - 1)


def route_time(d, r):
    return int(d[0][r[0]] + sum(d[a][b] for a, b in zip(r, r[1:])) + d[r[-1]][0])


def solve_group(d, g, tsp):
    """Route (global customer ids, depot implicit) and its time for one group."""
    if len(g) == 1:
        route = list(g)
    else:
        nodes = [0] + g
        tour = tsp(d[np.ix_(nodes, nodes)])
        route = [g[i - 1] for i in tour]
    return route, route_time(d, route)


def solve_dsu_tsp(data, X=math.inf, x_max=20, heldkarp_limit=20, tsp=None):
    # tsp: function(D) -> tour over local nodes 1..m (D index 0 = depot); default exact Held-Karp
    tsp = tsp or (lambda D: tsp_heldkarp(D, heldkarp_limit))
    demands = data["demands"]
    Q = data["capacity"]
    C = data["num_vehicles"]

    d = build_dist_matrix(data["coords"])
    log.info("dist matrix built (%d nodes), X=%s x_max=%d", len(d), X, x_max)

    # each group is one trip; a vehicle starts with one trip
    vehicles = []
    for g in build_groups(d, demands, Q, x_max, X):
        route, t = solve_group(d, g, tsp)
        vehicles.append({"trips": [route], "time": t})
        log.info("group %s -> trip %s time=%d", g, route, t)

    # more trips than vehicles: one vehicle drives several trips in turn
    while len(vehicles) > C:
        vehicles.sort(key=lambda v: v["time"])
        a, b = vehicles[0], vehicles[1]
        vehicles = vehicles[2:] + [{"trips": a["trips"] + b["trips"], "time": a["time"] + b["time"]}]
        log.info("same vehicle takes trips %s, time=%d, %d vehicles left", vehicles[-1]["trips"], vehicles[-1]["time"], len(vehicles))

    for i, v in enumerate(vehicles):
        log.info("vehicle %d: trips=%s time=%d", i + 1, v["trips"], v["time"])
    log.info("makespan=%d", max(v["time"] for v in vehicles))

    routes = [trip for v in vehicles for trip in v["trips"]]
    return max(v["time"] for v in vehicles), routes

