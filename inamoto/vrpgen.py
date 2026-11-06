"""Helper library to generate CVRP testcases in VRPLIB (.vrp) format.

Usage pattern mirrors tcframe-python: declare testcases with CASE(...) in a
spec.py, then call generate() to write them all out.
"""

import os
import random

_CASES = []


def CASE(filename, coords, demands, capacity, num_vehicles, comment=""):
    """Register one testcase. coords[0]/demands[0] are the depot (demand must be 0)."""
    assert demands[0] == 0, "depot (index 0) must have demand 0"
    assert len(coords) == len(demands), "coords and demands must have same length"
    _CASES.append({
        "filename": filename,
        "coords": coords,
        "demands": demands,
        "capacity": capacity,
        "num_vehicles": num_vehicles,
        "comment": comment,
    })


def random_customers(n, coord_range=(-50, 50), demand_range=(1, 10), seed=None):
    """Build (coords, demands) for a depot + n random customers."""
    rnd = random.Random(seed)
    coords = [(0, 0)] + [
        (rnd.randint(*coord_range), rnd.randint(*coord_range)) for _ in range(n)
    ]
    demands = [0] + [rnd.randint(*demand_range) for _ in range(n)]
    return coords, demands


def write_vrp(path, name, coords, demands, capacity, comment=""):
    lines = [
        f"NAME : {name}",
        f"COMMENT : {comment}",
        "TYPE : CVRP",
        f"DIMENSION : {len(coords)}",
        "EDGE_WEIGHT_TYPE : EUC_2D",
        f"CAPACITY : {capacity}",
        "NODE_COORD_SECTION",
    ]
    for i, (x, y) in enumerate(coords, start=1):
        lines.append(f"{i} {x} {y}")

    lines.append("DEMAND_SECTION")
    for i, d in enumerate(demands, start=1):
        lines.append(f"{i} {d}")

    lines += ["DEPOT_SECTION", "1", "-1", "EOF"]

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def generate(output_dir="data"):
    """Write every registered CASE() to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    for case in _CASES:
        path = os.path.join(output_dir, case["filename"])
        name = case["filename"].removesuffix(".vrp")
        write_vrp(
            path, name=name,
            coords=case["coords"], demands=case["demands"],
            capacity=case["capacity"], comment=case["comment"],
        )
        n = len(case["coords"]) - 1
        print(f"wrote {path} (n={n}, capacity={case['capacity']}, k={case['num_vehicles']})")
