#!/usr/bin/env python3
"""Name the functions of one source file by aligning them, in source order, against a run of arcade functions
in address order, scoring each pair on its call/argument events. Useful where many functions are near-identical
and only their position tells them apart.
usage: align_file.py <ps2_index.json> <ev_ref.json> <ev_arc.json> <symbols.csv> <file suffix> <lo hex> <hi hex> <out.csv>"""
import csv, json, sys
import numpy as np
P = json.load(open(sys.argv[1]))["functions"]; R = json.load(open(sys.argv[2])); A = json.load(open(sys.argv[3]))
M = {r["name"]: r["arcade_addr"] for r in csv.DictReader(open(sys.argv[4]))}
suffix, lo, hi, out = sys.argv[5], int(sys.argv[6], 16), int(sys.argv[7], 16), sys.argv[8]
names = [r["name"] for r in sorted(P, key=lambda r: r["order"]) if r["file"].endswith(suffix) and r["addr"]]
addrs = sorted(x for x in A if lo <= int(x, 16) < hi)
internal = set(names)
def rs(n):          # calls to functions of this same file are kept by name on both sides only if already consistent
    return frozenset((e[0], M.get(e[1], "?" + e[1])) + tuple(e[2:]) for e in map(tuple, R.get(n, [])) if e[0] in ("call", "carg"))
def as_(x):
    inside = set(addrs)
    return frozenset(tuple(e) for e in map(tuple, A[x]) if e[0] in ("call", "carg") and e[1] != "?")
rsets = [rs(n) for n in names]; asets = [as_(x) for x in addrs]
n, m = len(names), len(addrs)
S = np.zeros((n, m))
for i in range(n):
    for j in range(m):
        a, b = rsets[i], asets[j]
        S[i, j] = 0.05 if not a and not b else 1.0 if a == b else len(a & b) / len(a | b) - 0.6
GAP = -0.4
D = np.zeros((n + 1, m + 1)); D[:, 0] = GAP * np.arange(n + 1); D[0, :] = GAP * np.arange(m + 1)
for i in range(1, n + 1):
    for j in range(1, m + 1):
        D[i, j] = max(D[i - 1, j - 1] + S[i - 1, j - 1], D[i - 1, j] + GAP, D[i, j - 1] + GAP)
i, j = n, m; pairs = []
while i > 0 and j > 0:
    if abs(D[i, j] - (D[i - 1, j - 1] + S[i - 1, j - 1])) < 1e-9: pairs.append((names[i - 1], addrs[j - 1], bool(rsets[i - 1]) and rsets[i - 1] == asets[j - 1])); i -= 1; j -= 1
    elif abs(D[i, j] - (D[i - 1, j] + GAP)) < 1e-9: i -= 1
    else: j -= 1
pairs.reverse()
with open(out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "content_equal", "previous_addr"])
    for nme, x, eq in pairs: w.writerow([x, nme, int(eq), M.get(nme, "")])
eq = sum(1 for p in pairs if p[2]); moved = sum(1 for nme, x, e in pairs if M.get(nme) != x)
print(f"{len(names)} PS2 functions, {len(addrs)} arcade functions; aligned {len(pairs)}: {eq} with equal content, {len(pairs) - eq} differing; {moved} names would move")
