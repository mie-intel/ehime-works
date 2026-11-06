"""Scalable DSU + TSP + BSTA: line-sweep grouping (no n x n matrix), LK per group, BSTA over the tours."""

import logging

import numpy as np

from solutions.bsta import bsta
from solutions.linesweep_dsu_tsp import linesweep_groups, solve_group
from solutions.lkh_solver import tsp_lk

log = logging.getLogger(__name__)


def solve_linesweep_dsu_tsp_bsta(data, x_max=10, tsp=tsp_lk):
    xy = np.asarray(data["coords"], dtype=float)

    groups = linesweep_groups(xy, data["demands"], int(data["capacity"]), x_max)
    trips = [solve_group(xy, g, tsp) for g in groups]
    routes, times = [r for r, _ in trips], [t for _, t in trips]
    log.info("%d tours, solving BSTA for %d vehicles", len(routes), data["num_vehicles"])

    makespan, bundles = bsta(times, data["num_vehicles"])
    for k, b in enumerate(bundles):
        log.info("vehicle %d: %d tours time=%d", k + 1, len(b), sum(times[i] for i in b))
    log.info("makespan=%d", makespan)

    return makespan, routes
