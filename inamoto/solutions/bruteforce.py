"""Bruteforce solver: try every customer permutation, every way to cut it into tours, every tour-to-vehicle split."""

import itertools
import logging
import math

from utils import route_distance

log = logging.getLogger(__name__)


# Every way to cut a customer order into consecutive tours with load <= capacity
def split_all(order, demands, capacity):
    def cut(start):
        if start == len(order):
            yield []
            return
        load = 0
        for end in range(start, len(order)):
            load += demands[order[end]]
            if load > capacity:
                break
            for rest in cut(end + 1):
                yield [list(order[start:end + 1])] + rest

    yield from cut(0)


# Smallest possible time of the slowest vehicle when the tours are shared among K vehicles
def pack_exact(times, K):
    times = sorted(times, reverse=True)
    best = sum(times)  # one vehicle takes everything
    loads = [0] * K

    def assign(i):
        nonlocal best
        if i == len(times):
            best = min(best, max(loads))
            return
        seen = set()
        for k in range(K):
            if loads[k] in seen:  # vehicles with equal load are interchangeable
                continue
            seen.add(loads[k])
            loads[k] += times[i]
            if loads[k] < best:
                assign(i + 1)
            loads[k] -= times[i]

    assign(0)
    return best


def solve_bruteforce(data):
    coords = data["coords"]
    demands = data["demands"]
    capacity = data["capacity"]
    num_vehicles = data["num_vehicles"]
    customers = list(range(1, len(coords)))

    log.info("starting bruteforce over %d! permutations", len(customers))

    best_makespan = math.inf
    best_routes = None
    checked = 0
    dist_of = {}  # tour -> distance, the same tour shows up in many cuts

    for order in itertools.permutations(customers):
        for routes in split_all(order, demands, capacity):
            checked += 1
            times = []
            for r in routes:
                key = tuple(r)
                if key not in dist_of:
                    dist_of[key] = route_distance(r, coords)
                times.append(dist_of[key])

            makespan = pack_exact(times, num_vehicles)
            if makespan < best_makespan:
                best_makespan = makespan
                best_routes = routes
                log.info("new best: makespan=%d routes=%s", makespan, routes)

    log.info("bruteforce done: checked=%d cuts best_makespan=%s", checked, best_makespan)
    return best_makespan, best_routes
