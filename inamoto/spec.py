"""Testcase spec: declare each .vrp instance here, then run this file.

    python3 spec.py

Add more CASE(...) calls below to extend the testcase set.
"""

from vrpgen import CASE, random_customers, generate

# fixed instance: every variable defined explicitly, used by solve.py
CASE(
    filename="instance-n6-k2.vrp",
    coords=[(0, 0), (10, 5), (5, 15), (-5, 10), (-10, -5), (5, -10), (15, -5)],
    demands=[0, 3, 5, 4, 6, 2, 5],
    capacity=15,
    num_vehicles=2,
    comment="small bruteforce test instance, 6 customers, 2 vehicles",
)

# poster-only instance: 8 customers, 2 vehicles, drawn by poster_viz.py (4 clear clusters, one capacity-rejected cross edge)
CASE(
    filename="poster-n8-k2.vrp",
    coords=[(0, 0), (60, 70), (85, 55), (75, 90), (-70, 60), (-50, 85), (-80, -50), (-55, -75), (95, 5)],
    demands=[0, 3, 3, 4, 5, 5, 4, 5, 6],
    capacity=10,
    num_vehicles=2,
    comment="poster visualization only: 8 customers, 2 vehicles",
)

def create_testcase(n, k, coord_range=(-100, 100), demand_range=(1, 10), seed=None, capacity=None):
    """Random instance with n customers and k vehicles. capacity defaults to 2 * max demand, then it is not in the filename."""
    coords, demands = random_customers(n, coord_range=coord_range, demand_range=demand_range, seed=seed)
    suffix = "" if capacity is None else f"-q{capacity}"
    capacity = capacity or max(demands) * 2
    CASE(
        filename=f"instance-n{n}-k{k}{suffix}.vrp",
        coords=coords,
        demands=demands,
        capacity=capacity,
        num_vehicles=k,
        comment=f"random instance with {n} customers and {k} vehicles, capacity {capacity}",
    )

N_VALUES = [10, 30, 100, 300, 1000]
K_VALUES = [2, 3, 5, 10, 20]


def create_grid(n_values, k_values, coord_range=(-100, 100), demand_range=(1, 10), seed=1):
    """Every (n, k) combination, small to large. Same seed: instances with equal n differ only in k."""
    for n in sorted(n_values):
        for k in sorted(k_values):
            create_testcase(n=n, k=k, coord_range=coord_range, demand_range=demand_range, seed=seed)


SWEEP_N, SWEEP_K = 1000, 20
Q_VALUES = [10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240]  # x2 steps; demands are 1..10 (total ~5500), so Q = 10240 fits everyone in one tour


def create_capacity_sweep(n, k, q_values, coord_range=(-100, 100), demand_range=(1, 10), seed=1):
    """Same customers and demands for every Q: instances differ only in capacity."""
    for q in sorted(q_values):
        create_testcase(n=n, k=k, coord_range=coord_range, demand_range=demand_range, seed=seed, capacity=q)


if __name__ == "__main__":
    create_testcase(n=10, k=3, coord_range=(-1000, 1000), demand_range=(1, 10), seed=1)
    create_testcase(n=15, k=3, coord_range=(-1000, 1000), demand_range=(1, 10), seed=1)
    create_testcase(n=18, k=3, coord_range=(-1000, 1000), demand_range=(1, 10), seed=1)
    create_testcase(n=20, k=3, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_testcase(n=1000, k=3, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_testcase(n=1000, k=20, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_testcase(n=1000, k=50, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_testcase(n=1000, k=100, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_testcase(n=1000, k=500, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_testcase(n=10000, k=5, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_testcase(n=1000000, k=10, coord_range=(-100, 100), demand_range=(1, 10), seed=1)
    create_grid(N_VALUES, K_VALUES)
    create_capacity_sweep(SWEEP_N, SWEEP_K, Q_VALUES)
    generate(output_dir="data")
