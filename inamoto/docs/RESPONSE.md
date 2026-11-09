Dear Arya-san,
(CC: Higami-sensei)

After listening to today's presentation, I came up with the following
MILP formulation as a quasi-optimal solution approach.

The formulation is still incomplete, particularly regarding how the
depot should be handled in the group-level partial solutions, but I
would appreciate it if you could take a look at the following idea.

- Constants: number of customers N, number of vehicles K, number of
  groups G, and capacity Q.

- Constant: c\_{i,j,g} in {0, 1} ... Indicates whether edge i -> j is
  used in the TSP partial solution obtained for group g.
  This is a decision variable when solving the TSP for each group, but
  once the TSP has been solved, it is treated as a constant in the
  subsequent formulation.

- Variable: x\_{i,j,k} in {0, 1} ... Indicates whether edge i -> j is
  used in the tour of vehicle k.

- Variable: s\_{i,j,g} in {0, 1} ... Indicates whether edge i -> j from
  the partial solution is retained in the overall solution.

- Variable: S*g = \sum*{i,j} s\_{i,j,g} ... Number of edges from the
  partial solution retained for group g.

- Constant: P*g := { i | \sum_j c*{i,j,g} >= 1 } ... Set of customers
  included in the partial solution for group g.

- Variable: z\_{k,g} in {0, 1} ... Indicates whether group g is handled
  by vehicle k.

* Constraint: Every group must be handled by one vehicle.
  \sum*k z*{k,g} = 1 \forall g = {1, ..., G}

- Variable: R*k := \sum_g |P_g| z*{k,g} ... Number of customers handled
  by vehicle k.

* Constraint: The number of customers handled by vehicle k must not
  exceed its capacity Q.
  R_k <= Q \forall k

- Variable: S\_{k,g} ... Number of edges from the partial solution of
  group g that vehicle k must retain.

* Constraint: If group g is handled by vehicle k, S*{k,g} must be at
  least S_g. Otherwise, it is unrestricted by this constraint.
  S*{k,g} >= S*g - N (1 - z*{k,g})

- Variable: S*k := \sum_g S*{k,g} ... Total number of edges from the
  group-level solutions that vehicle k must retain.

- Constant (parameter): L_k (>= 2) ... Number of edges that may be
  freely determined in the partial solution for vehicle k.
  If L_k = 2, the resulting solution is very close to the group-level
  solutions, which should shorten the computation time.
  However, L_k = 2 may result in infeasibility. If L_k = N, the
  formulation should always be feasible.

* Constraint: Among the R_k edges of vehicle k, at least (R_k - L_k)
  edges must be retained from the partial solutions.
  S_k >= R_k - L_k \forall k = {1, ..., K}

* Constraint: In the solution for vehicle k, if s*{i,j,g} = 1 and
  z*{k,g} = 1, edge i -> j from the partial solution of group g must be used.
  x*{i,j,k} >= c*{i,j,g} z*{k,g} - (1 - s*{i,j,g})

* Constraint: Customer i must be served by one of the vehicles.
  \sum*k x*{i,j,k} = 1 \forall i, j = {1, ..., N} x {1, ..., N}
  \sum*k x*{j,i,k} = 1 \forall i, j = {1, ..., N} x {1, ..., N}

- Step 1: Partition the customers into groups, and solve a TSP for each
  group. We refer to the resulting solutions as group-level partial solutions.

- Step 2: For each vehicle k, specify L_k, the number of edges that can
  be freely determined, as a parameter. If the depot is to be incorporated
  into each partial tour, then at least L_k >= 2 is necessary.

- Step 3: Optimize x*{i,j,k} and z*{k,g}. If z\_{k,g} = 1, the partial
  solution for group g is incorporated into the partial tour of vehicle k.

Step 3 solves an optimization problem to optimality, whereas Steps 1 and
2 do not necessarily seek optimal decisions for the overall problem.

Some further adjustment is needed regarding how the depot should be
incorporated into the formulation.
