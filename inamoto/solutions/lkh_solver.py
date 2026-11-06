"""DSU clustering + Lin-Kernighan (lk_heuristic) per group, so groups can be larger than Held-Karp allows."""

import logging
import math

from lk_heuristic.models.node import Node2D
from lk_heuristic.models.tsp import Tsp

from solutions.dsu_tsp import solve_dsu_tsp, tsp_heldkarp

log = logging.getLogger(__name__)


def tsp_lk(D, runs=5):
    """LK tour over local nodes 1..m (D index 0 = depot), cost taken from the integer matrix D."""
    m = len(D) - 1
    if m <= 8:  # LK needs enough nodes to swap; tiny groups are cheap to solve exactly
        return tsp_heldkarp(D, 8)

    nodes = [Node2D(0.0, 0.0) for _ in range(m + 1)]  # Tour assigns node.id = list index
    tsp = Tsp(nodes, lambda a, b: int(D[a.id][b.id]), shuffle=False, tour_type="cycle", logging_level=logging.WARNING)

    best_cost, best = math.inf, None
    for _ in range(runs):
        tsp.tour.shuffle()
        tsp.tour.set_cost(tsp.cost_matrix)
        tsp.lk1_improve()
        if tsp.tour.cost < best_cost:
            best_cost, best = tsp.tour.cost, [n.id for n in tsp.tour.get_nodes()]
        log.info("LK run on %d customers: cost=%s", m, tsp.tour.cost)

    i = best.index(0)  # rotate the cycle so it starts after the depot
    return best[i + 1:] + best[:i]


def solve_dsu_lkh(data, X=math.inf, x_max=200):
    return solve_dsu_tsp(data, X=X, x_max=x_max, tsp=tsp_lk)
