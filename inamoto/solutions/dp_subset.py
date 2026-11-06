"""Exact ground truth: subset DP for the min-makespan multi-tour CVRP. About K * 3^n work, so small n only.

cost[S] = best single tour over customer set S (inf if load > Q)
g[S]    = best total time for ONE vehicle to cover S with any number of tours
F[k][S] = best makespan covering S with k vehicles
"""

import logging
import math

import numpy as np

from solutions.dsu_tsp import heldkarp_tables, heldkarp_tour
from utils import build_dist_matrix, route_distance

log = logging.getLogger(__name__)

INF = 10**12


def submasks(r):
    """All submasks of bitmask r."""
    subs = np.zeros(1, dtype=np.int64)
    while r:
        bit = r & -r
        subs = np.concatenate([subs, subs | bit])
        r ^= bit
    return subs


def solve_dp_subset(data, limit=18):
    d = build_dist_matrix(data["coords"])
    n, Q, K = len(d) - 1, int(data["capacity"]), data["num_vehicles"]
    demands = [int(q) for q in data["demands"]]
    size = 1 << n

    dp, par = heldkarp_tables(d, limit)
    masks = np.arange(size)
    load = np.zeros(size, dtype=np.int64)
    for c in range(n):  # bit c = customer c + 1
        load += demands[c + 1] * ((masks >> c) & 1)
    cost = (dp + d[1:, 0]).min(axis=1)
    cost[load > Q] = INF
    cost[0] = 0
    log.info("subset DP: n=%d K=%d, %d feasible tours", n, K, int((cost < INF).sum()) - 1)

    g = np.full(size, INF, dtype=np.int64)
    F = np.full((K + 1, size), INF, dtype=np.int64)
    g[0] = F[:, 0] = 0
    tour_of = np.zeros(size, dtype=np.int64)  # tour that holds the lowest customer of S, in g's optimum
    set_of = np.zeros((K + 1, size), dtype=np.int64)  # set of the vehicle that holds the lowest customer of S

    for S in range(1, size):
        low = S & -S  # the vehicle / tour holding the lowest customer is fixed, so each partition is tried once
        r = S ^ low
        sub = submasks(r)
        T, rest = sub | low, r ^ sub

        cand = cost[T] + g[rest]
        i = int(cand.argmin())
        g[S], tour_of[S] = cand[i], T[i]
        F[1, S], set_of[1, S] = g[S], S

        gT = g[T]
        for k in range(2, K + 1):
            cand = np.maximum(gT, F[k - 1, rest])
            i = int(cand.argmin())
            F[k, S], set_of[k, S] = cand[i], T[i]

    best = int(F[K, size - 1])
    if best >= INF:
        log.info("subset DP: infeasible (a customer demand exceeds capacity)")
        return math.inf, None

    routes, S = [], size - 1
    for k in range(K, 0, -1):
        V = int(set_of[k, S])
        S ^= V
        vehicle = []
        while V:
            T = int(tour_of[V])
            vehicle.append(heldkarp_tour(d, dp, par, T))
            V ^= T
        routes += vehicle
        if vehicle:
            log.info("vehicle %d: tours=%s time=%d", K - k + 1, vehicle, sum(route_distance(t, data["coords"]) for t in vehicle))
    log.info("makespan=%d", best)

    return best, routes
