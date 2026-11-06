#!/usr/bin/env python3
"""Logic simulator sederhana untuk file .bench (ISCAS).

Pemakaian:
    python bench_sim.py c17.bench            # tabel kebenaran semua kombinasi input
    python bench_sim.py c17.bench 10101      # satu vektor, urutan = urutan INPUT di file
    python bench_sim.py c17.bench 1gat=1 2gat=0 3gat=1 6gat=0 7gat=1
"""
import itertools
import re
import sys
from collections import deque


# ---------- parser ----------
def parse_bench(path):
    inputs, outputs, gates = [], [], {}  # gates[name] = (type, [fanins])
    with open(path) as f:
        for line in f:
            line = line.split("#")[0].strip()
            if not line:
                continue
            if m := re.match(r"INPUT\s*\(\s*(\S+?)\s*\)", line, re.I):
                inputs.append(m[1])
            elif m := re.match(r"OUTPUT\s*\(\s*(\S+?)\s*\)", line, re.I):
                outputs.append(m[1])
            elif m := re.match(r"(\S+)\s*=\s*(\w+)\s*\((.*)\)", line):
                gtype = m[2].upper()
                if gtype == "DFF":
                    raise ValueError("DFF (sequential) belum didukung, cuma rangkaian combinational.")
                gates[m[1]] = (gtype, [x.strip() for x in m[3].split(",")])
            else:
                raise ValueError(f"Baris tidak dikenali: {line!r}")
    return inputs, outputs, gates


def topo_order(inputs, gates):
    """Urutan topologis (Kahn, iteratif) supaya tiap gerbang muncul setelah fanin-nya."""
    known = set(inputs)
    indeg, fanout = {}, {}
    for g, (_, fanins) in gates.items():
        indeg[g] = 0
        for f in fanins:
            if f not in known and f not in gates:
                raise ValueError(f"Net '{f}' dipakai oleh '{g}' tapi tidak pernah didefinisikan.")
            if f in gates:
                indeg[g] += 1
                fanout.setdefault(f, []).append(g)
    queue = deque(g for g, d in indeg.items() if d == 0)
    order = []
    while queue:
        n = queue.popleft()
        order.append(n)
        for m in fanout.get(n, []):
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    if len(order) != len(gates):
        raise ValueError("Ada loop kombinasional di rangkaian.")
    return order


# ---------- simulator ----------
def eval_gate(gtype, vals):
    if gtype == "AND":
        return int(all(vals))
    if gtype == "NAND":
        return int(not all(vals))
    if gtype == "OR":
        return int(any(vals))
    if gtype == "NOR":
        return int(not any(vals))
    if gtype == "XOR":
        return sum(vals) % 2
    if gtype == "XNOR":
        return 1 - sum(vals) % 2
    if gtype == "NOT":
        return 1 - vals[0]
    if gtype in ("BUFF", "BUF"):
        return vals[0]
    raise ValueError(f"Tipe gerbang tidak didukung: {gtype}")


def simulate(inputs, outputs, gates, order, assignment):
    """assignment: dict nama_input -> 0/1. Return dict nilai semua net."""
    values = dict(assignment)
    for g in order:
        gtype, fanins = gates[g]
        values[g] = eval_gate(gtype, [values[f] for f in fanins])
    return values


# ---------- CLI ----------
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    inputs, outputs, gates = parse_bench(sys.argv[1])
    order = topo_order(inputs, gates)
    print(f"Inputs : {inputs}")
    print(f"Outputs: {outputs}")
    print(f"Gates  : {len(gates)}\n")

    args = sys.argv[2:]
    if not args:
        # tabel kebenaran lengkap
        print(" ".join(inputs), "|", " ".join(outputs))
        for vec in itertools.product([0, 1], repeat=len(inputs)):
            v = simulate(inputs, outputs, gates, order, dict(zip(inputs, vec)))
            print(" ".join(map(str, vec)), "|", " ".join(str(v[o]) for o in outputs))
        return

    if len(args) == 1 and re.fullmatch(r"[01]+", args[0]):
        if len(args[0]) != len(inputs):
            sys.exit(f"Butuh {len(inputs)} bit, dapat {len(args[0])}.")
        assignment = {n: int(b) for n, b in zip(inputs, args[0])}
    else:
        assignment = {}
        for a in args:
            name, _, val = a.partition("=")
            assignment[name] = int(val)
        missing = [i for i in inputs if i not in assignment]
        if missing:
            sys.exit(f"Input belum diisi: {missing}")

    v = simulate(inputs, outputs, gates, order, assignment)
    for i in inputs:
        print(f"{i} = {assignment[i]}")
    print()
    for o in outputs:
        print(f"{o} = {v[o]}")


if __name__ == "__main__":
    main()