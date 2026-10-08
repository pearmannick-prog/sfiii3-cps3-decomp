#!/usr/bin/env python3
"""Match arcade (CPS-3) functions to named PS2 functions.
usage: match.py <ps2_index.json> <split dir> <out symbols.csv> [--code-hi HEX]

Stages (each later stage only fills what earlier ones left open):
  1 tables  - place each PS2 function-pointer table onto an arcade pointer run (shape score + repeat pattern)
  2 calls   - propagate through call sequences of matched caller pairs
  3 order   - within a source file, fill gaps between matched neighbours when the counts agree
"""
import argparse, collections, csv, itertools, json, math, os
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("ps2"); ap.add_argument("split"); ap.add_argument("out")
ap.add_argument("--code-hi", type=lambda s: int(s, 16), default=0x0613BDFA)
ap.add_argument("-v", action="store_true"); a = ap.parse_args()
PS = json.load(open(a.ps2)); AR = json.load(open(os.path.join(a.split, "functions.json")))
P = {r["name"]: r for r in PS["functions"]}; A = {r["addr"]: r for r in AR["functions"]}
pnames = set(P)
for r in P.values(): r["dcalls"] = [c for c in r["calls"] if c in pnames]
for r in A.values(): r["dcalls"] = [c for c in r["calls"] if c is not None]
RATIO = 0.40                                   # typical SH-2 bytes per PS2 (MIPS) byte

def pfeat(n):
    r = P.get(n)
    return (len(r["dcalls"]), math.log(max(r["size"], 8) * RATIO)) if r else (np.nan, np.nan)
def afeat(x):
    r = A.get(x)
    return (len(r["dcalls"]), math.log(max(r["size"], 4))) if r else (np.nan, np.nan)
def pair_score(pc, ps, ac, as_):
    s = np.exp(-np.abs(pc - ac) / (1 + 0.15 * np.maximum(pc, ac))) * np.exp(-((ps - as_) ** 2) / 0.5)
    return np.nan_to_num(s, nan=0.0)

def canon(c):
    return c if c >= 0 else (c & 0xFFFF if c >= -0x8000 else c & 0xFFFFFFFF)
_df = collections.Counter()
for r in list(P.values()) + list(A.values()):
    r["cset"] = {canon(c) for c in r["consts"] if abs(c) >= 16}; _df.update(r["cset"])
for r in list(P.values()) + list(A.values()): r["rare"] = {c for c in r["cset"] if _df[c] <= 60}
def const_sim(n, x):
    """Overlap of uncommon constants: value in [0,1], or None when either side has none; 0 with >=2 each = contradiction."""
    rp, ra = P[n]["rare"], A[x]["rare"]
    if not rp or not ra: return None
    return len(rp & ra) / min(len(rp), len(ra))
def contradicted(n, x):
    return len(P[n]["rare"]) >= 2 and len(A[x]["rare"]) >= 2 and not (P[n]["rare"] & A[x]["rare"])

M, Minv, how = {}, {}, {}                      # name -> addr, addr -> name, name -> (stage, confidence)
def assign(n, x, stage, conf):
    if n in M or x in Minv or n not in P or x not in A: return False
    M[n] = x; Minv[x] = n; how[n] = (stage, round(float(conf), 3)); return True

# ---- stage 1: tables ------------------------------------------------------------------
runs = [r for r in AR["runs"] if r["addr"] >= a.code_hi]
rfeat = [np.array([afeat(x) for x in r["items"]], dtype=float) for r in runs]

def pattern_ok(items, seg):
    f, g = {}, {}
    for n, x in zip(items, seg):
        if (n is None) != (x == 0) and n is None: continue          # non-function C entry: anything goes
        if n is None: continue
        if x == 0: return False
        if f.setdefault(n, x) != x or g.setdefault(x, n) != n: return False
        if M.get(n, x) != x or Minv.get(x, n) != n: return False
    return True

def place(t):
    items = t["items"]; n = len(items)
    tf = np.array([pfeat(x) for x in items], dtype=float)
    valid = ~np.isnan(tf[:, 0]); cands = []
    for ri, (r, rf) in enumerate(zip(runs, rfeat)):
        m = len(r["items"])
        if m < n: continue
        w = np.lib.stride_tricks.sliding_window_view(rf, (n, 2)).reshape(m - n + 1, n, 2)
        sc = pair_score(tf[None, :, 0], tf[None, :, 1], w[:, :, 0], w[:, :, 1])[:, valid].mean(axis=1)
        for k in np.argsort(sc)[::-1][:8]:
            cands.append((float(sc[k]), ri, int(k)))
    cands.sort(reverse=True)
    good = [(s, ri, k) for s, ri, k in cands[:40] if pattern_ok(items, runs[ri]["items"][k:k + n])]
    return good

tables = sorted(PS["tables"], key=lambda t: -len(t["items"]))
pending = list(tables)

def seg_score(t, ri, k):
    items = t["items"]; tf = np.array([pfeat(x) for x in items], dtype=float); rf = rfeat[ri][k:k + len(items)]
    if len(rf) < len(items) or not pattern_ok(items, runs[ri]["items"][k:k + len(items)]): return -1.0
    v = ~np.isnan(tf[:, 0])
    return float(pair_score(tf[:, 0], tf[:, 1], rf[:, 0], rf[:, 1])[v].mean())

def commit(t, ri, k, sc):
    for nme, x in zip(t["items"], runs[ri]["items"][k:k + len(t["items"])]):
        if nme and x: assign(nme, x, "table", sc)

def stage_tables():
    global pending
    for rnd in range(8):
        still = []; best = {}
        for ti, t in enumerate(pending):
            items = t["items"]; distinct = len({x for x in items if x})
            if all(x in M for x in items if x): continue
            good = place(t)
            if not good: still.append(t); continue
            s0, ri, k = good[0]; seg = runs[ri]["items"][k:k + len(items)]
            known = sum(1 for nme, x in zip(items, seg) if nme and M.get(nme) == x)
            s1 = next((s for s, r2, k2 in good[1:] if runs[r2]["items"][k2:k2 + len(items)] != seg), 0.0)
            margin = s0 - s1
            full = runs[ri]["items"]; e = k + len(items)      # does it exactly fill a hole between placed tables?
            fits = (k == 0 or full[k - 1] == 0 or full[k - 1] in Minv) and (e == len(full) or full[e] == 0 or full[e] in Minv)
            ok = known >= max(1, distinct // 10) or (distinct >= 6 and s0 >= 0.45 and margin >= 0.08) \
                 or (distinct >= 3 and s0 >= 0.6 and margin >= 0.15) or (fits and distinct >= 4 and s0 >= 0.4)
            if a.v: print(f"{'OK ' if ok else '-- '}{t['file']:<28} n={len(items):<4} d={distinct:<4} s={s0:.2f} m={margin:.2f} known={known} run={runs[ri]['addr']:08X}+{k}")
            if ok: commit(t, ri, k, s0)
            else: still.append(t); best[id(t)] = (ri, k)
        # hole packing: several tables that together exactly fill one free stretch of a run
        holes = collections.defaultdict(list)
        for t in still:
            if id(t) not in best: continue
            ri, k = best[id(t)]; full = runs[ri]["items"]; lo = k
            while lo > 0 and full[lo - 1] and full[lo - 1] not in Minv: lo -= 1
            hi = k
            while hi < len(full) and full[hi] and full[hi] not in Minv: hi += 1
            holes[(ri, lo, hi)].append(t)
        for (ri, lo, hi), ts in holes.items():
            if sum(len(t["items"]) for t in ts) != hi - lo or len(ts) < 2: continue
            orders = itertools.permutations(ts) if len(ts) <= 6 else [sorted(ts, key=lambda t: t["file"].lower())]
            scored = []
            for o in orders:
                k = lo; tot = []
                for t in o:
                    tot.append(seg_score(t, ri, k)); k += len(t["items"])
                scored.append((min(tot), sum(tot) / len(tot), o))
            scored.sort(key=lambda z: z[:2], reverse=True)
            if scored[0][0] >= 0.4 and (len(scored) == 1 or scored[0][1] - scored[1][1] >= 0.03):
                k = lo
                for t in scored[0][2]:
                    if a.v: print(f"PACK {t['file']} run={runs[ri]['addr']:08X}+{k}")
                    commit(t, ri, k, scored[0][1]); k += len(t["items"]); still.remove(t)
        if len(still) == len(pending): break
        pending = still

def nw(names, addrs):
    """Global alignment of a name sequence against an address sequence; returns aligned (name, addr, score)."""
    n, m = len(names), len(addrs)
    pf = np.array([pfeat(x) for x in names], dtype=float); af = np.array([afeat(x) for x in addrs], dtype=float)
    S = pair_score(pf[:, None, 0], pf[:, None, 1], af[None, :, 0], af[None, :, 1])
    for i, nme in enumerate(names):
        for j, x in enumerate(addrs):
            if M.get(nme) == x and nme in M: S[i, j] = 3.0
            elif nme in M or x in Minv: S[i, j] = -9.0
    GAP = -0.3; D = np.zeros((n + 1, m + 1)); D[:, 0] = GAP * np.arange(n + 1); D[0, :] = GAP * np.arange(m + 1)
    for i in range(1, n + 1):
        row = D[i - 1, :-1] + S[i - 1] - 0.35; up = D[i - 1, 1:] + GAP
        best = np.maximum(row, up); cur = D[i]
        for j in range(1, m + 1): cur[j] = max(best[j - 1], cur[j - 1] + GAP)
    out = []; i, j = n, m
    while i > 0 and j > 0:
        if abs(D[i, j] - (D[i - 1, j - 1] + S[i - 1, j - 1] - 0.35)) < 1e-9:
            out.append((names[i - 1], addrs[j - 1], float(S[i - 1, j - 1]))); i -= 1; j -= 1
        elif abs(D[i, j] - (D[i - 1, j] + GAP)) < 1e-9: i -= 1
        else: j -= 1
    return out[::-1]

def stage_align():
    """Tables that differ slightly between the two versions: align the unmatched part against the hole it points at."""
    for t in list(pending):
        items = t["items"]; n = len(items)
        if sum(1 for x in items if x and x not in M) < 3: continue
        tf = np.array([pfeat(x) for x in items], dtype=float); valid = ~np.isnan(tf[:, 0]); best = (0, None, None)
        for ri, (r, rf) in enumerate(zip(runs, rfeat)):
            m = len(r["items"]); nn = min(n, m)
            if nn < n * 0.9: continue
            w = np.lib.stride_tricks.sliding_window_view(rf, (nn, 2)).reshape(m - nn + 1, nn, 2)
            sc = pair_score(tf[None, :nn, 0], tf[None, :nn, 1], w[:, :, 0], w[:, :, 1])[:, valid[:nn]].mean(axis=1)
            # prefer positions agreeing with existing matches
            k = int(np.argmax(sc))
            if sc[k] > best[0]: best = (float(sc[k]), ri, k)
        anchors = [(i, x) for i, x in enumerate(items) if x in M]
        s0, ri, k = best
        if ri is None: continue
        full = runs[ri]["items"]; lo, hi = max(0, k - 3), min(len(full), k + n + 3)
        al = nw([x for x in items[:]], full[lo:hi])
        pairs = [(nme, x, sc) for nme, x, sc in al if nme and x]
        if not pairs or len(pairs) < 0.8 * sum(1 for x in items if x): continue
        mean = sum(min(sc, 1) for _, _, sc in pairs) / len(pairs)
        if mean < 0.55: continue
        votes = collections.Counter((nme, x) for nme, x, sc in pairs if nme not in M and x not in Minv)
        byn, byx = collections.Counter(), collections.Counter()
        for (nme, x), v in votes.items(): byn[nme] += v; byx[x] += v
        for (nme, x), v in votes.most_common():
            if v >= 0.7 * byn[nme] and v >= 0.7 * byx[x]: assign(nme, x, "table-align", mean)
        if a.v: print(f"ALIGN {t['file']} n={n} mean={mean:.2f} run={runs[ri]['addr']:08X}+{k}")

# ---- stage 2: call sequences -------------------------------------------------------------
def lcs_align(cs, xs):
    """Align name sequence cs with address sequence xs on already-matched pairs; yield gap pairs."""
    n, m = len(cs), len(xs)
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            L[i][j] = L[i + 1][j + 1] + 1 if M.get(cs[i]) == xs[j] else max(L[i + 1][j], L[i][j + 1])
    i = j = 0; gi, gj = 0, 0; out = []
    while i < n and j < m:
        if M.get(cs[i]) == xs[j]:
            out.append((cs[gi:i], xs[gj:j])); i += 1; j += 1; gi, gj = i, j
        elif L[i + 1][j] >= L[i][j + 1]: i += 1
        else: j += 1
    out.append((cs[gi:], xs[gj:])); return L[0][0], out

def stage_calls():
    for rnd in range(30):
        votes = collections.Counter()
        for nme, x in M.items():
            cs, xs = P[nme]["dcalls"], A[x]["dcalls"]
            if not cs or not xs: continue
            k, gaps = lcs_align(cs, xs)
            for gc, gx in gaps:
                gc = [c for c in gc]; 
                if len(gc) != len(gx) or not gc: continue
                if len(cs) != len(xs) and k == 0: continue          # nothing ties this caller pair together
                for c, y in zip(gc, gx):
                    if c not in M and y not in Minv: votes[(c, y)] += 1
        bestn, bestx = collections.defaultdict(list), collections.defaultdict(list)
        for (c, y), v in votes.items(): bestn[c].append((v, y)); bestx[y].append((v, c))
        new = 0
        for c, lst in bestn.items():
            lst.sort(reverse=True); v, y = lst[0]
            if len(lst) > 1 and lst[1][0] * 2 > v: continue
            ly = sorted(bestx[y], reverse=True)
            if ly[0][1] != c or (len(ly) > 1 and ly[1][0] * 2 > v): continue
            pc, ps = pfeat(c); ac, as_ = afeat(y)
            if contradicted(c, y): continue
            if v < 2 and float(pair_score(pc, ps, ac, as_)) < 0.25 and not const_sim(c, y): continue
            new += assign(c, y, "calls", min(1.0, v / 3))
        if not new: break

# ---- stage 3: order within a source file ------------------------------------------------------
alist = sorted(A); apos = {x: i for i, x in enumerate(alist)}
byfile = collections.defaultdict(list)
for r in sorted(P.values(), key=lambda r: r["order"]):
    if r["addr"]: byfile[r["file"]].append(r["name"])
def stage_order():
    inversions = pairs_checked = 0
    for f, names in byfile.items():
        known = [(i, apos[M[n]]) for i, n in enumerate(names) if n in M]
        for (i0, p0), (i1, p1) in zip(known, known[1:]):
            pairs_checked += 1; inversions += p1 < p0
            if i1 - i0 > 1 and p1 - p0 == i1 - i0:
                for d in range(1, i1 - i0):
                    n, x = names[i0 + d], alist[p0 + d]
                    sc = float(pair_score(*pfeat(n), *afeat(x)))
                    if sc >= 0.2 and not contradicted(n, x): assign(n, x, "order", sc)
    return inversions, pairs_checked
def call_sim(n, x):
    """Agreement between the callees of n (through the current map) and the callees of x; None if no evidence."""
    cs = [M[c] for c in P[n]["dcalls"] if c in M]; xs = [y for y in A[x]["dcalls"] if y in Minv]
    if len(cs) + len(xs) < 2: return None
    ca, cb = collections.Counter(cs), collections.Counter(xs)
    return 2 * sum((ca & cb).values()) / (len(cs) + len(xs))

def stage_order_align():
    """Within a source file, align the unmatched functions between matched neighbours (handles extra/missing ones)."""
    for f, names in byfile.items():
        known = [(i, apos[M[n]]) for i, n in enumerate(names) if n in M]
        if len(known) < 2: continue
        # keep the longest increasing chain of anchors so one bad match cannot derail the file
        best = [1] * len(known); prev = [-1] * len(known)
        for u in range(len(known)):
            for v in range(u):
                if known[v][1] < known[u][1] and best[v] + 1 > best[u]: best[u] = best[v] + 1; prev[u] = v
        u = max(range(len(known)), key=best.__getitem__); chain = []
        while u >= 0: chain.append(known[u]); u = prev[u]
        chain.reverse()
        for (i0, p0), (i1, p1) in zip(chain, chain[1:]):
            ns = [n for n in names[i0 + 1:i1] if n not in M]; xs = [x for x in alist[p0 + 1:p1] if x not in Minv]
            if not ns or not xs or len(xs) > 3 * len(ns) + 4 or len(ns) > 3 * len(xs) + 4 or len(ns) * len(xs) > 40000: continue
            for n, x, sc in nw(ns, xs):
                cs = call_sim(n, x)
                if cs is not None: sc = 0.4 * sc + 0.6 * cs
                elif len(ns) != len(xs): sc *= 0.8
                if sc >= 0.55 and not contradicted(n, x): assign(n, x, "order-align", sc)

for it in range(10):
    n0 = len(M)
    stage_tables(); stage_align(); n1 = len(M); stage_calls(); n2 = len(M)
    if it == 0:        # consistency check before order is used as evidence
        inv0, tot0 = stage_order()
    else: stage_order()
    n3 = len(M); stage_order_align()
    print(f"pass {it + 1}: tables +{n1 - n0}, calls +{n2 - n1}, order +{n3 - n2}, order-align +{len(M) - n3}  (total {len(M)})")
    if len(M) == n0: break
print(f"order check on table+call matches of pass 1: {inv0}/{tot0} adjacent same-file pairs out of order")

def grade(n, x):
    shape = float(pair_score(*pfeat(n), *afeat(x))); cs = const_sim(n, x); cl = call_sim(n, x)
    if contradicted(n, x) or (cl is not None and cl < 0.3 and (cs or 0) < 0.5): g = "low"
    elif (cs is not None and cs >= 0.5) or (cl is not None and cl >= 0.8) or (how[n][0] == "table" and shape >= 0.5): g = "high"
    else: g = "medium"
    return g, round(shape, 2), "" if cs is None else round(cs, 2), "" if cl is None else round(cl, 2)

grades = collections.Counter()
with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "ps2_file", "stage", "grade", "shape", "const_sim", "call_sim"])
    for n, x in sorted(M.items(), key=lambda kv: kv[1]):
        g = grade(n, x); grades[g[0]] += 1
        w.writerow([f"{x:08X}", n, P[n]["file"], how[n][0], *g])
print("grades:", dict(grades))
print(f"matched {len(M)} of {len(A)} arcade functions ({len(P)} PS2 names available) -> {a.out}")
