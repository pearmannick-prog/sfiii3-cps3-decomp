#!/usr/bin/env python3
"""Run the source-order + content alignment (see align_file.py) over every source file and write pins for
match.py --pins. A pair is pinned when its call/argument/store events are equal and non-trivial, or when it
sits between two such pairs with nothing else in the gap on either side.
usage: align_all.py <ps2_index.json> <ev_ref.json> <ev_arc.json> <symbols.csv> <out pins.csv>"""
import collections, csv, json, sys
import numpy as np
P = json.load(open(sys.argv[1]))["functions"]; R = json.load(open(sys.argv[2])); A = json.load(open(sys.argv[3]))
sym = list(csv.DictReader(open(sys.argv[4]))); M = {r["name"]: r["arcade_addr"] for r in sym}; G = {r["name"]: r["grade"] for r in sym}
allx = sorted(A, key=lambda x: int(x, 16)); pos = {x: i for i, x in enumerate(allx)}
KINDS = ("call", "carg", "stc", "bit")
def rs(n): return frozenset((e[0], M.get(e[1], "?" + e[1])) + tuple(e[2:]) if e[0] in ("call", "carg") else tuple(e) for e in map(tuple, R.get(n, [])) if e[0] in ("call", "carg"))
def as_(x): return frozenset(tuple(e) for e in map(tuple, A[x]) if e[0] in ("call", "carg") and e[1] != "?")
byfile = collections.defaultdict(list)
for r in sorted(P, key=lambda r: r["order"]):
    if r["addr"]: byfile[r["file"]].append(r["name"])
pins = []; stats = collections.Counter()
for f, names in byfile.items():
    have = sorted(pos[M[n]] for n in names if n in M and G[n] != "low" and M[n] in pos)
    if len(have) < 4: continue
    # densest cluster of matched positions: the window of len(names)*1.5 holding the most matches
    width = int(len(names) * 1.5) + 8; best = (0, 0)
    j = 0
    for i in range(len(have)):
        while have[i] - have[j] > width: j += 1
        if i - j + 1 > best[0]: best = (i - j + 1, j)
    cnt, j = best
    if cnt < 0.5 * len(have): continue
    lo = max(0, have[j] - 6); hi = min(len(allx), have[j + cnt - 1] + 7)
    addrs = allx[lo:hi]
    rsets = [rs(n) for n in names]; asets = [as_(x) for x in addrs]
    n, m = len(names), len(addrs)
    if n * m > 400000: continue
    S = np.zeros((n, m))
    for a in range(n):
        ra = rsets[a]
        for b in range(m):
            ab = asets[b]
            S[a, b] = 0.05 if not ra and not ab else 1.0 if ra == ab else len(ra & ab) / len(ra | ab) - 0.6
    GAP = -0.4; D = np.zeros((n + 1, m + 1)); D[:, 0] = GAP * np.arange(n + 1); D[0, :] = 0.0     # free leading arcade gap
    for a in range(1, n + 1):
        up = D[a - 1, 1:] + GAP; diag = D[a - 1, :-1] + S[a - 1]; row = D[a]
        best_ = np.maximum(up, diag)
        for b in range(1, m + 1): row[b] = max(best_[b - 1], row[b - 1] + GAP)
    a = n; b = int(np.argmax(D[n])); pairs = []                                                   # free trailing arcade gap
    while a > 0 and b > 0:
        if abs(D[a, b] - (D[a - 1, b - 1] + S[a - 1, b - 1])) < 1e-9: pairs.append((a - 1, b - 1)); a -= 1; b -= 1
        elif abs(D[a, b] - (D[a - 1, b] + GAP)) < 1e-9: a -= 1
        else: b -= 1
    pairs.reverse()
    strong = [(a, b) for a, b in pairs if rsets[a] and rsets[a] == asets[b] and len(rsets[a]) >= 2]
    sset = set(strong); out = {}
    for a, b in strong: out[a] = (b, 1)
    for (a0, b0), (a1, b1) in zip(strong, strong[1:]):          # exactly one function on each side between two anchors
        if a1 - a0 == 2 and b1 - b0 == 2: out.setdefault(a0 + 1, (b0 + 1, 0))
    for a, (b, eq) in out.items(): pins.append([addrs[b], names[a], eq, f.split("/")[-1]])
    stats["files"] += 1
# drop conflicts (an address or name claimed twice)
ca = collections.Counter(p[0] for p in pins); cn = collections.Counter(p[1] for p in pins)
pins = [p for p in pins if ca[p[0]] == 1 and cn[p[1]] == 1]
with open(sys.argv[5], "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "content_equal", "source"]); w.writerows(sorted(pins))
agree = collections.Counter()
for x, n, eq, f in pins:
    g = G.get(n, "unnamed"); agree[(g, "same" if M.get(n) == x else "moved" if n in M else "new")] += 1
print(f"{len(pins)} pins from {stats['files']} files"); print(sorted(agree.items()))
