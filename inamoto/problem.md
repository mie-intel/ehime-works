# Problem: Capacitated Vehicle Routing Problem (CVRP) with arc pruning

## Given

- 1 depot and n customers. Each location i has 2D coordinates (x_i, y_i).
- Customer i requests R_i units of goods (R_depot = 0).
- The depot has C identical vehicles, each with capacity Q.
- Distance d(i, j) = Euclidean distance between locations i and j, rounded to the
  nearest integer (EUC_2D convention of CVRPLIB). Travel time = distance, no service time.

## Find

Routes: each vehicle starts at the depot, visits some customers, and returns to the depot.

- Every customer is visited exactly once.
- The total demand on one route never exceeds Q.
- At most C vehicles are used.
  Objective: minimise the total distance of all routes.
  (Alternative objective, to be confirmed with Prof. Inamoto: minimise the makespan, i.e.
  the time at which the last vehicle returns to the depot.)

## Decision variables (MILP)

- x[i,j] in {0,1}: 1 if some vehicle drives directly from i to j.
- load[i]: cumulative load after serving customer i (capacity and no sub-tours).

## Research idea (heuristic constraint)

Before solving, delete arcs between customers that are far apart: for each customer keep
only arcs to its k nearest customers (symmetric). All arcs from and to the depot stay.
The pruned problem is smaller, so the solver should be faster, but the best solution may
be lost, or the problem may become infeasible when k is too small.

## Experiment

For the same instance, solve with k in {all (no pruning), 8, 5, 3, ...}.
Record per run:

- number of arcs kept,
- solver status (optimal / time limit / infeasible),
- total distance and the gap to the unpruned optimum (%),
- solver computation time (seconds).
  Goal: find the smallest k that keeps the gap near 0 while cutting solver time.

## Data

- Benchmark instances in VRPLIB format (CVRPLIB, e.g. A-n32-k5.vrp): coordinates,
  demands, capacity. Start with random instances of 10-15 customers.

## Tools

Python, vrplib (reads instances), PuLP 3.x (model) with HiGHS or CBC (solver).

## Sample result (random instance, 15 customers, 3 vehicles, capacity 30)

k=all: 240 arcs, 2.3 s, distance 569 | k=8: 182 arcs, 3.4 s, 569 |
k=5: 126 arcs, 1.1 s, 569 | k=3: 84 arcs, 0.3 s, 573 (+0.7%)
