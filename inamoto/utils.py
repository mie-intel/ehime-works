"""Shared helpers: instance reading, distances, solver timing."""

import logging
import math
import os
import re
import time

import matplotlib
import numpy as np
import vrplib

matplotlib.use("Agg")  # write PNG files, no display needed
import matplotlib.pyplot as plt  # noqa: E402

log = logging.getLogger(__name__)

PLOT_DIR = "plots"
PLOT_MAX_CUSTOMERS = 5000  # beyond this a scatter/route plot is unreadable and slow


def read_data(path):
    log.info("reading instance: %s", path)
    instance = vrplib.read_instance(path, instance_format="vrplib", compute_edge_weights=False)

    match = re.search(r"-k(\d+)", path)
    num_vehicles = int(match.group(1)) if match else 1

    coords = instance["node_coord"]
    demands = instance["demand"]
    capacity = instance["capacity"]

    log.info(
        "loaded %d customers, capacity=%d, vehicles=%d",
        len(coords) - 1, capacity, num_vehicles,
    )
    return {
        "name": os.path.splitext(os.path.basename(path))[0],
        "coords": coords,
        "demands": demands,
        "capacity": capacity,
        "num_vehicles": num_vehicles,
    }


def dist(a, b):
    return round(math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


def build_dist_matrix(coords):
    P = np.asarray(coords, dtype=float)
    dx = P[:, 0, None] - P[None, :, 0]
    dy = P[:, 1, None] - P[None, :, 1]
    return np.rint(np.sqrt(dx * dx + dy * dy)).astype(np.int64)


def route_distance(route, coords):
    depot = coords[0]
    total = 0
    prev = depot
    for customer in route:
        total += dist(prev, coords[customer])
        prev = coords[customer]
    total += dist(prev, depot)
    return total


def _plot_base(data, title):
    xy = np.asarray(data["coords"], dtype=float)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(xy[1:, 0], xy[1:, 1], s=14, c="tab:blue", zorder=2, label="customer")
    ax.scatter(xy[0, 0], xy[0, 1], s=180, c="red", marker="*", zorder=3, label="depot")
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    return fig, ax, xy


def _plot_save(fig, data, suffix):
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, f"{data['name']}_{suffix}.png")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    log.info("saved plot: %s", path)


def plot_instance(data):
    """Depot and customer locations on a cartesian plane."""
    n = len(data["coords"]) - 1
    if n > PLOT_MAX_CUSTOMERS:
        log.info("skip instance plot: %d customers > %d", n, PLOT_MAX_CUSTOMERS)
        return
    fig, ax, _ = _plot_base(data, f"{data['name']}: depot + {n} customers")
    ax.legend()
    _plot_save(fig, data, "instance")


def plot_solution(data, solver_name, makespan, routes):
    """Same plane as plot_instance, every tour drawn depot -> customers -> depot in its own colour."""
    n = len(data["coords"]) - 1
    if routes is None or n > PLOT_MAX_CUSTOMERS:
        log.info("skip solution plot of %s", solver_name)
        return
    fig, ax, xy = _plot_base(data, f"{solver_name}: makespan={makespan}, {len(routes)} tours")
    for i, route in enumerate(routes):
        pts = xy[[0] + list(route) + [0]]
        ax.plot(pts[:, 0], pts[:, 1], color=plt.cm.tab20(i % 20), lw=1.6, zorder=1)
    ax.legend()
    _plot_save(fig, data, solver_name)


def call_solve_function(func, data):
    """Call a solve function and measure its execution time."""
    log.info("\nCALLING %s", func.__name__)
    start = time.perf_counter()
    result = func(data)
    elapsed = time.perf_counter() - start
    plot_solution(data, func.__name__, result[0], result[1])
    log.info("%s took %.3f seconds", func.__name__, elapsed)
    routes = result[1]
    shown = routes if routes is None or len(routes) <= 20 else f"<{len(routes)} routes>"
    log.info("final result: makespan=%s routes=%s", result[0], shown)
    return result, elapsed


def compare_results(results):
    """results: {name: ((makespan, routes), elapsed)}. Log a summary table and a pairwise gap matrix."""
    names = list(results)
    dists = {n: results[n][0][0] for n in names}
    best = min(dists.values())

    def gap(a, b):  # % by which a is above b
        return f"{(a - b) / b * 100:.2f}" if math.isfinite(a) and math.isfinite(b) and b > 0 else "-"

    log.info("=== comparison ===")
    log.info("%-30s %10s %8s %9s %7s", "method", "makespan", "gap%", "time(s)", "routes")
    for n in names:
        (d, routes), t = results[n]
        log.info("%-30s %10s %8s %9.3f %7s", n, d, gap(d, best), t, len(routes) if routes else "-")

    log.info("pairwise gap %% (row is above column by)")
    log.info("%-14s" + " %14s" * len(names), "", *names)
    for a in names:
        log.info("%-14s" + " %14s" * len(names), a, *[gap(dists[a], dists[b]) for b in names])
