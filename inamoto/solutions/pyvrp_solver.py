"""Baseline: pure PyVRP (Hybrid Genetic Search); K vehicles drive several tours each by reloading at a second depot."""

import logging
import math

from pyvrp import Model
from pyvrp.stop import MaxRuntime, NoImprovement

from utils import build_dist_matrix

log = logging.getLogger(__name__)


def solve_pyvrp(data, max_runtime=None, patience=20000):
    """max_runtime=None: no time limit; HGS stops after `patience` iterations without a new best solution."""
    coords = data["coords"]
    demands = data["demands"]
    n = len(coords) - 1
    d = build_dist_matrix(coords)

    m = Model()
    locs = [m.add_location(x=float(x), y=float(y)) for x, y in coords]
    depot = m.add_depot(location=locs[0])
    reload = m.add_depot(location=locs[0])  # same place: a vehicle returns here, reloads, starts its next tour
    for i in range(1, n + 1):
        m.add_client(location=locs[i], delivery=int(demands[i]))
    m.add_vehicle_type(
        num_available=data["num_vehicles"],
        capacity=int(data["capacity"]),
        start_depot=depot,
        end_depot=depot,
        reload_depots=[reload],
        max_reloads=n,
    )
    for i, a in enumerate(locs):
        for j, b in enumerate(locs):
            m.add_edge(a, b, distance=int(d[i][j]))
    stop = MaxRuntime(max_runtime) if max_runtime else NoImprovement(patience)
    log.info("pyvrp model built, running HGS until %s", f"{max_runtime}s" if max_runtime else f"{patience} iterations without improvement")

    res = m.solve(stop=stop, seed=0, display=False)
    if not res.is_feasible():
        log.info("pyvrp: no feasible solution found")
        return math.inf, None

    problem = m.data()
    tours = []
    for k, route in enumerate(res.best.routes()):
        trip, vehicle_tours = [], []
        for a in route:  # activities: depot, clients..., reload depot, clients..., depot
            if a.is_client():
                trip.append(problem.client(a.idx).location)  # a.idx indexes clients, not locations
            elif trip:
                vehicle_tours.append(trip)
                trip = []
        tours += vehicle_tours
        log.info("vehicle %d: tours=%s time=%d", k + 1, vehicle_tours, route.distance())

    makespan = max(route.distance() for route in res.best.routes())
    log.info("pyvrp done: iterations=%d makespan=%d", res.num_iterations, makespan)
    return makespan, tours
