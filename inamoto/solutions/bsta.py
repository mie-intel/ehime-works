"""BSTA (binary search the answer): give tours to K vehicles so the slowest vehicle finishes as early as possible."""

import logging
import math

from solutions.dsu_tsp import build_groups, solve_group, tsp_heldkarp
from utils import build_dist_matrix

log = logging.getLogger(__name__)


def bsta_pack(times, K, m, order=None):
    """Can the tours be given to <= K vehicles, each vehicle driving <= m in total?

    Two pointers over tours sorted by time (ll = smallest, rr = largest): if tour ll still fits
    on bundle rr, merge it in, else bundle rr is full and closed. Returns bundles of tour indices, or None.
    order: tour indices sorted by time; pass it in to skip the O(G log G) sort on every call.
    """
    if max(times) > m:
        return None
    if order is None:
        order = sorted(range(len(times)), key=times.__getitem__)
    t = [times[i] for i in order]
    bundles = [[i] for i in order]
    ll, rr = 0, len(t) - 1
    while ll < rr:
        if t[rr] + t[ll] <= m:
            t[rr] += t[ll]
            bundles[rr] += bundles[ll]
            ll += 1
        else:
            rr -= 1
    left = bundles[ll:]  # bundles before ll were merged away
    return left if len(left) <= K else None


def bsta(times, K):
    """Smallest m for which bsta_pack succeeds. Returns (makespan, bundles of tour indices), len(bundles) <= K."""
    times = [int(t) for t in times]  # integer search space only
    order = sorted(range(len(times)), key=times.__getitem__)  # sort once: O(G log G)
    lo, hi = max(times), sum(times)
    best = bsta_pack(times, K, hi, order)  # one vehicle takes everything
    while lo < hi:
        mid = (lo + hi) // 2
        packed = bsta_pack(times, K, mid, order)  # O(G) per check
        if packed is None:
            lo = mid + 1
        else:
            hi, best = mid, packed
    return max(sum(times[i] for i in b) for b in best), best


def solve_dsu_bsta(data, X=math.inf, x_max=10, tsp=None):
    # tsp: function(D) -> tour over local nodes 1..m (D index 0 = depot); default exact Held-Karp
    tsp = tsp or (lambda D: tsp_heldkarp(D, x_max))
    d = build_dist_matrix(data["coords"])

    groups = build_groups(d, data["demands"], data["capacity"], x_max, X)
    trips = [solve_group(d, g, tsp) for g in groups]
    routes, times = [r for r, _ in trips], [t for _, t in trips]
    log.info("%d tours, times=%s", len(trips), times)

    makespan, bundles = bsta(times, data["num_vehicles"])
    for k, b in enumerate(bundles):
        log.info("vehicle %d: tours=%s time=%d", k + 1, [routes[i] for i in b], sum(times[i] for i in b))
    log.info("makespan=%d", makespan)

    return makespan, routes
