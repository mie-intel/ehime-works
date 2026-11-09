"""MILP solvers (PuLP + HiGHS): the plain exact model, and the grouped model that keeps TSP edges (see docs/RESPONSE.md).

A vehicle may drive several tours (depot -> customers -> depot) one after another; the objective is the makespan.
"""

import logging
import math

import pulp

from solutions.dsu_tsp import build_groups, solve_group, tsp_heldkarp
from utils import build_dist_matrix

log = logging.getLogger(__name__)


class CvrpMilp:
    """Multi-tour CVRP as a MILP, minimising the makespan (time of the slowest vehicle).

    Customers are partitioned into `groups`; a group is never split across vehicles.
    group_edges[g] = undirected customer-customer edges of the TSP route of group g (depot edges excluded).
    If given, vehicle k must keep at least (edges of its tours - L) of them, i.e. only L edges are free.
    A vehicle with R_k customers on t_k tours drives R_k + t_k edges, so one group on one tour needs L >= 2.
    """

    def __init__(self, d, demands, Q, K, groups, group_edges=None, L=None):
        self.d, self.K, self.groups = d, K, groups
        self.n = len(d)
        self.q = [int(v) for v in demands]
        self.Q = int(Q)
        self.group_edges = group_edges
        self.L = L
        self.prob = pulp.LpProblem("cvrp", pulp.LpMinimize)

        self._add_variables()
        self._add_makespan()
        self._add_assignment()
        self._add_routing()
        if group_edges is not None:
            self._add_retained_edges()
        log.info("MILP built: %d groups, %d vehicles, %d vars, %d constraints",
                 len(groups), K, len(self.prob.variables()), len(self.prob.constraints))

    # --- model -------------------------------------------------------------------------------

    def _add_variables(self):
        nodes, ks = range(self.n), range(self.K)
        # x[i,j,k] = 1: vehicle k drives i -> j
        self.x = pulp.LpVariable.dicts(
            "x", [(i, j, k) for i in nodes for j in nodes if i != j for k in ks], cat="Binary")
        # z[k,g] = 1: group g is served by vehicle k
        self.z = pulp.LpVariable.dicts("z", [(k, g) for k in ks for g in range(len(self.groups))], cat="Binary")
        # load[i]: cumulative load on the current tour after serving customer i (capacity + no sub-tours)
        self.load = {i: pulp.LpVariable(f"load_{i}", self.q[i], self.Q) for i in range(1, self.n)}
        self.makespan = pulp.LpVariable("makespan", 0)
        self.group_of = {i: g for g, members in enumerate(self.groups) for i in members}

    def _out(self, i, k):
        return pulp.lpSum(self.x[i, j, k] for j in range(self.n) if j != i)

    def _in(self, i, k):
        return pulp.lpSum(self.x[j, i, k] for j in range(self.n) if j != i)

    def _add_makespan(self):
        self.prob += self.makespan
        for k in range(self.K):
            self.prob += pulp.lpSum(
                int(self.d[i][j]) * self.x[i, j, k] for i in range(self.n) for j in range(self.n) if i != j
            ) <= self.makespan

    def _add_assignment(self):
        # every group on exactly one vehicle
        for g in range(len(self.groups)):
            self.prob += pulp.lpSum(self.z[k, g] for k in range(self.K)) == 1
        # vehicle k visits customer i exactly when it serves i's group
        for k in range(self.K):
            for i in range(1, self.n):
                zk = self.z[k, self.group_of[i]]
                self.prob += self._out(i, k) == zk
                self.prob += self._in(i, k) == zk

    def _add_routing(self):
        # MTZ on load: i -> j by any vehicle means load[j] >= load[i] + q[j]; the load restarts at the depot
        for i in range(1, self.n):
            for j in range(1, self.n):
                if i != j:
                    used = pulp.lpSum(self.x[i, j, k] for k in range(self.K))
                    self.prob += self.load[j] >= self.load[i] + self.q[j] - self.Q * (1 - used)

    def _add_retained_edges(self):
        edges = [e for es in self.group_edges for e in es]
        for k in range(self.K):
            retained = pulp.lpSum(self.x[i, j, k] + self.x[j, i, k] for i, j in edges)
            customers = pulp.lpSum(len(g) * self.z[k, gi] for gi, g in enumerate(self.groups))
            tour_edges = customers + self._out(0, k)  # R_k customers on t_k tours -> R_k + t_k edges
            self.prob += retained >= tour_edges - self.L

    # --- solve -------------------------------------------------------------------------------

    def solve(self, time_limit=None):
        """Returns (makespan, tours); (inf, None) when the model is infeasible."""
        self.prob.solve(pulp.HiGHS(msg=False, timeLimit=time_limit))
        status = pulp.LpStatus[self.prob.status]
        log.info("MILP status: %s", status)
        if status in ("Infeasible", "Undefined", "Not Solved") or self.makespan.value() is None:
            return math.inf, None
        by_vehicle = [self._tours(k) for k in range(self.K)]
        times = [sum(self._route_dist(t) for t in tours) for tours in by_vehicle]
        for k, (tours, t) in enumerate(zip(by_vehicle, times)):
            log.info("vehicle %d: tours=%s time=%d", k + 1, tours, t)
        return max(times), [t for tours in by_vehicle for t in tours]

    def _tours(self, k):
        """Follow every tour of vehicle k out of the depot."""
        arcs = [(i, j) for (i, j, kk), v in self.x.items() if kk == k and v.value() > 0.5]
        succ = {i: j for i, j in arcs if i != 0}
        tours = []
        for i, j in arcs:
            if i != 0:
                continue
            tour = []
            while j != 0:
                tour.append(j)
                j = succ[j]
            tours.append(tour)
        return tours

    def _route_dist(self, route):
        seq = [0] + route + [0]
        return int(sum(self.d[a][b] for a, b in zip(seq, seq[1:])))


def solve_milp_bruteforce(data, time_limit=None):
    """Exact MILP over all customers: every customer is its own group, no edge is forced."""
    d = build_dist_matrix(data["coords"])
    groups = [[i] for i in range(1, len(d))]
    model = CvrpMilp(d, data["demands"], data["capacity"], data["num_vehicles"], groups)
    return model.solve(time_limit)


def solve_milp_tsp_grouping(data, x_max=5, L=4, X=math.inf, time_limit=None, tsp=None):
    """DSU groups -> TSP per group -> MILP that keeps all but L edges of each vehicle's tours from those TSPs."""
    tsp = tsp or (lambda D: tsp_heldkarp(D, x_max))
    d = build_dist_matrix(data["coords"])
    groups = build_groups(d, data["demands"], data["capacity"], x_max, X)

    group_edges = []
    for g in groups:
        route, _ = solve_group(d, g, tsp)
        group_edges.append(list(zip(route, route[1:])))
        log.info("group %s -> TSP route %s", g, route)

    model = CvrpMilp(d, data["demands"], data["capacity"], data["num_vehicles"], groups, group_edges, L)
    return model.solve(time_limit)
