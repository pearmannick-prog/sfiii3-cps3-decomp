#!/usr/bin/env python3
"""Infer names for arcade RAM addresses from matched function pairs.
usage: globals.py <ps2_index.json> <split dir> <symbols.csv> <out data_symbols.csv>
A global name and a RAM address are paired when they are referenced by (nearly) the same set of matched functions."""
import collections, csv, json, os, sys
PS = json.load(open(sys.argv[1])); A = {r["addr"]: r for r in json.load(open(os.path.join(sys.argv[2], "functions.json")))["functions"]}
P = {r["name"]: r for r in PS["functions"]}
rows = [r for r in csv.DictReader(open(sys.argv[3])) if r["grade"] != "low"]
co, cn, ca = collections.Counter(), collections.Counter(), collections.Counter()
for r in rows:
    ids = [i for i in P[r["name"]]["idents"] if i not in P]; rams = set(A[int(r["arcade_addr"], 16)]["ram"])
    cn.update(ids); ca.update(rams)
    for i in ids:
        for x in rams: co[(i, x)] += 1
cand = sorted(((c / (cn[i] + ca[x] - c), c, i, x) for (i, x), c in co.items() if c >= 2), reverse=True)
names, addrs, out = set(), set(), []
for j, c, i, x in cand:
    if j < 0.6: break
    if i in names or x in addrs: continue
    # ambiguous if another candidate for the same name or address is nearly as good
    rival = max((j2 for j2, c2, i2, x2 in cand if (i2 == i) != (x2 == x) and j2 < j + 1e-9), default=0) if j < 0.999 else 0
    names.add(i); addrs.add(x)
    if rival < 0.8 * j: out.append((x, i, c, round(j, 2)))
with open(sys.argv[4], "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "functions", "agreement"])
    for x, i, c, j in sorted(out): w.writerow([f"{x:08X}", i, c, j])
print(f"{len(out)} global variables named ({len(ca)} RAM addresses referenced by matched functions)")
