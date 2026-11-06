Dear Arya-san,
(CC: Higami-sensei)

After listening to today's presentation, I came up with the following MILP formulation as a quasi-optimal solution approach.

The formulation is still incomplete, particularly regarding how the depot should be handled in the group-level partial solutions, but I would appreciate it if you could take a look at the following idea.

## Notation

**Constants:** number of customers $N$, number of vehicles $K$, number of groups $G$, and capacity $Q$.

**Constant** $c_{i,j,g} \in \{0,1\}$: indicates whether edge $i \to j$ is used in the TSP partial solution obtained for group $g$. This is a decision variable when solving the TSP for each group, but once the TSP has been solved, it is treated as a constant in the subsequent formulation.

**Variable** $x_{i,j,k} \in \{0,1\}$: indicates whether edge $i \to j$ is used in the tour of vehicle $k$.

**Variable** $s_{i,j,g} \in \{0,1\}$: indicates whether edge $i \to j$ from the partial solution is retained in the overall solution.

**Variable** $S_g = \sum_{i,j} s_{i,j,g}$: number of edges from the partial solution retained for group $g$.

**Constant** $P_g := \left\{\, i \;\middle|\; \sum_j c_{i,j,g} \ge 1 \,\right\}$: set of customers included in the partial solution for group $g$.

**Variable** $z_{k,g} \in \{0,1\}$: indicates whether group $g$ is handled by vehicle $k$.

## Constraints

**Every group must be handled by one vehicle.**

$$
\sum_{k} z_{k,g} = 1 \qquad \forall g \in \{1,\dots,G\}
$$

**Variable** $R_k := \sum_g |P_g|\, z_{k,g}$: number of customers handled by vehicle $k$.

**The number of customers handled by vehicle $k$ must not exceed its capacity $Q$.**

$$
R_k \le Q \qquad \forall k
$$

**Variable** $S_{k,g}$: number of edges from the partial solution of group $g$ that vehicle $k$ must retain.

**If group $g$ is handled by vehicle $k$, $S_{k,g}$ must be at least $S_g$. Otherwise, it is unrestricted by this constraint.**

$$
S_{k,g} \ge S_g - N\,(1 - z_{k,g})
$$

**Variable** $S_k := \sum_g S_{k,g}$: total number of edges from the group-level solutions that vehicle $k$ must retain.

**Parameter** $L_k \ (\ge 2)$: number of edges that may be freely determined in the partial solution for vehicle $k$.

- If $L_k = 2$, the resulting solution is very close to the group-level solutions, which should shorten the computation time. However, $L_k = 2$ may result in infeasibility.
- If $L_k = N$, the formulation should always be feasible.

**Among the $R_k$ edges of vehicle $k$, at least $(R_k - L_k)$ edges must be retained from the partial solutions.**

$$
S_k \ge R_k - L_k \qquad \forall k \in \{1,\dots,K\}
$$

**In the solution for vehicle $k$, if $s_{i,j,g} = 1$ and $z_{k,g} = 1$, edge $i \to j$ from the partial solution of group $g$ must be used.**

$$
x_{i,j,k} \ge c_{i,j,g}\, z_{k,g} - \bigl(1 - s_{i,j,g}\bigr)
$$

**Customer $i$ must be served by one of the vehicles.**

$$
\sum_{k} x_{i,j,k} = 1 \qquad \forall (i,j) \in \{1,\dots,N\}\times\{1,\dots,N\}
$$

$$
\sum_{k} x_{j,i,k} = 1 \qquad \forall (i,j) \in \{1,\dots,N\}\times\{1,\dots,N\}
$$

## Procedure

- **Step 1:** Partition the customers into groups, and solve a TSP for each group. We refer to the resulting solutions as group-level partial solutions.
- **Step 2:** For each vehicle $k$, specify $L_k$, the number of edges that can be freely determined, as a parameter. If the depot is to be incorporated into each partial tour, then at least $L_k \ge 2$ is necessary.
- **Step 3:** Optimize $x_{i,j,k}$ and $z_{k,g}$. If $z_{k,g} = 1$, the partial solution for group $g$ is incorporated into the partial tour of vehicle $k$.

Step 3 solves an optimization problem to optimality, whereas Steps 1 and 2 do not necessarily seek optimal decisions for the overall problem.

Some further adjustment is needed regarding how the depot should be incorporated into the formulation.
