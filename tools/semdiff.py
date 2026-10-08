#!/usr/bin/env python3
"""Compare matched functions on semantic events (see events.py): the arcade function against the PS2 C compiled
for SH-2. First learns, from pairs already believed identical, how PS2-layout field offsets and global symbols map
to arcade ones; then reports for every matched function what each side does that the other does not.

usage: semdiff.py <ev_ref.json> <ev_arc.json> <symbols.csv> <status.csv> <out dir> [ps2_index.json split_dir]
writes: fieldmap.csv, globalmap.csv, semdiff.csv (one row per function), semdiff.txt (readable differences),
        feedback.csv for match.py --content: `semeq` (events agree), `seed` (an arcade function whose events equal
        one PS2 function's, uniquely), `reject` (a weak match whose events disagree while another function fits)"""
import collections, csv, json, os, re, sys
R = json.load(open(sys.argv[1])); A = json.load(open(sys.argv[2]))
rows = list(csv.DictReader(open(sys.argv[3]))); status = {r["name"]: r["status"] for r in csv.DictReader(open(sys.argv[4]))}
out = sys.argv[5]; os.makedirs(out, exist_ok=True)
M = {r["name"]: r["arcade_addr"] for r in rows}; Minv = {v: k for k, v in M.items()}; grade = {r["name"]: r["grade"] for r in rows}
PL = re.compile(r"^(a\d|g:[^+]+)\+([0-9a-f]+)(?:>\+([0-9a-f]+))?$")
def parse(pl):
    m = PL.match(pl)
    return (m.group(1), int(m.group(2), 16), None if m.group(3) is None else int(m.group(3), 16)) if m else None
def places(evs):
    return {e[1] for e in evs if e[0] in ("ld", "st", "stc", "eq", "bit") and isinstance(e[1], str)}

trusted = [n for n in M if n in R and M[n] in A and (grade[n] in ("exact", "manual") or (grade[n] in ("high", "events") and status.get(n) in ("same", "reordered", "remapped")))]

# ---- field offsets: struct order is preserved, so equal-sized offset sets pair up by rank
v0 = collections.Counter(); t0 = collections.Counter()
for n in trusted:
    ro = sorted({p[1] for p in map(parse, places(R[n])) if p and p[0][0] == "a"})
    ao = sorted({p[1] for p in map(parse, places(A[M[n]])) if p and p[0][0] == "a"})
    if len(ro) == len(ao):
        for x, y in zip(ro, ao): v0[(x, y)] += 1; t0[x] += 1
F0 = {}
for (x, y), c in v0.most_common():
    if x not in F0 and c >= 2 and c >= 0.6 * t0[x]: F0[x] = y
# children of a pointer field, keyed by the arcade offset of the pointer
v1 = collections.Counter(); t1 = collections.Counter()
for n in trusted:
    rc, ac = collections.defaultdict(set), collections.defaultdict(set)
    for p in map(parse, places(R[n])):
        if p and p[0][0] == "a" and p[2] is not None and p[1] in F0: rc[F0[p[1]]].add(p[2])
    for p in map(parse, places(A[M[n]])):
        if p and p[0][0] == "a" and p[2] is not None: ac[p[1]].add(p[2])
    for par in rc:
        if len(rc[par]) == len(ac.get(par, ())):
            for x, y in zip(sorted(rc[par]), sorted(ac[par])): v1[(par, x, y)] += 1; t1[(par, x)] += 1
F1 = {}
for (par, x, y), c in v1.most_common():
    if (par, x) not in F1 and c >= 2 and c >= 0.6 * t1[(par, x)]: F1[(par, x)] = y

# ---- globals: symbol + offset on one side, absolute address on the other; vote for each symbol's base address
gv = collections.Counter(); gt = collections.Counter()
for n in trusted:
    rg = [p for p in map(parse, places(R[n])) if p and p[0].startswith("g:")]
    ag = [int(p[0][2:], 16) + p[1] for p in map(parse, places(A[M[n]])) if p and p[0].startswith("g:")]
    for sym, off, _ in set((p[0], p[1], None) for p in rg):
        gt[sym] += 1
        for a in set(ag): gv[(sym, a - off)] += 1
G = {}; best = collections.defaultdict(list)
for (sym, base), c in gv.items(): best[sym].append((c, base))
taken = collections.defaultdict(list)
for sym, lst in best.items():
    lst.sort(reverse=True); c, base = lst[0]
    if c >= 2 and c >= 0.6 * gt[sym] and (len(lst) == 1 or lst[1][0] <= 0.7 * c): G[sym] = base

# ---- grow the maps from leftovers: when a pair has the same number of untranslated PS2 fields (or globals)
# as arcade fields nobody accounts for, pair those up too. Repeat until nothing new is learned.
usable = [n for n in M if n in R and M[n] in A and grade[n] != "low"]
for rnd in range(12):
    w0, wt0, w1, wt1, wg, wgt = (collections.Counter() for _ in range(6))
    for n in usable:
        rp = [p for p in map(parse, places(R[n])) if p]; ap = [p for p in map(parse, places(A[M[n]])) if p]
        r0 = {p[1] for p in rp if p[0][0] == "a"}; a0 = {p[1] for p in ap if p[0][0] == "a"}
        un = sorted(x for x in r0 if x not in F0); left = sorted(a0 - {F0[x] for x in r0 if x in F0})
        if un and len(un) == len(left) <= 4:
            for x, y in zip(un, left): w0[(x, y)] += 1
        for x in un: wt0[x] += 1
        rc, ac = collections.defaultdict(set), collections.defaultdict(set)
        for p in rp:
            if p[0][0] == "a" and p[2] is not None and p[1] in F0: rc[F0[p[1]]].add(p[2])
            elif p[0][0] == "g" and p[2] is not None and p[0] in G: rc[f"{G[p[0]] + p[1]:08X}"].add(p[2])
        for p in ap:
            if p[0][0] == "a" and p[2] is not None: ac[p[1]].add(p[2])
            elif p[0][0] == "g" and p[2] is not None: ac[f"{int(p[0][2:], 16) + p[1]:08X}"].add(p[2])
        for par, kids in rc.items():
            un = sorted(x for x in kids if (par, x) not in F1); left = sorted(ac.get(par, set()) - {F1[(par, x)] for x in kids if (par, x) in F1})
            if un and len(un) == len(left) <= 4:
                for x, y in zip(un, left): w1[(par, x, y)] += 1
            for x in un: wt1[(par, x)] += 1
        rg = {(p[0], p[1]) for p in rp if p[0].startswith("g:")}; ag = {int(p[0][2:], 16) + p[1] for p in ap if p[0].startswith("g:")}
        left = ag - {G[sy] + off for sy, off in rg if sy in G}
        unsy = {sy for sy, off in rg if sy not in G}
        for sy in unsy: wgt[sy] += 1
        if 1 <= len(unsy) <= 3 and 1 <= len(left) <= 4:
            for sy in unsy:
                for off in {o for s2, o in rg if s2 == sy}:
                    for x in left: wg[(sy, x - off)] += 1.0 / (len(unsy) * len(left))
    new = 0
    for (x, y), c in w0.most_common():
        if x not in F0 and c >= 3 and c >= 0.5 * wt0[x]: F0[x] = y; v0[(x, y)] = c; new += 1
    for (par, x, y), c in w1.most_common():
        if (par, x) not in F1 and c >= 3 and c >= 0.5 * wt1[(par, x)]: F1[(par, x)] = y; v1[(par, x, y)] = c; new += 1
    for (sy, base), c in wg.most_common():
        if sy not in G and c >= 1.5 and c >= 0.34 * wgt[sy] and base not in G.values(): G[sy] = base; gv[(sy, base)] = round(c, 1); new += 1
    if not new: break

with open(os.path.join(out, "fieldmap.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["via_arcade_ptr_offset", "ps2_offset", "arcade_offset", "votes"])
    for x in sorted(F0): w.writerow(["", f"0x{x:X}", f"0x{F0[x]:X}", v0[(x, F0[x])]])
    for (par, x) in sorted(F1, key=str): w.writerow([par if isinstance(par, str) else f"0x{par:X}", f"0x{x:X}", f"0x{F1[(par, x)]:X}", v1[(par, x, F1[(par, x)])]])
with open(os.path.join(out, "globalmap.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["symbol", "arcade_addr", "votes"])
    for sym in sorted(G): w.writerow([sym[2:], f"{G[sym]:08X}", gv[(sym, G[sym])]])
print(f"learned from {len(trusted)} trusted pairs: {len(F0)} field offsets, {len(F1)} fields behind pointers, {len(G)} globals")

# ---- translate reference events into arcade terms and diff
def tr_place(pl):
    p = parse(pl)
    if not p: return None
    base, off, child = p
    if base[0] == "a":
        if off not in F0: return None
        s = f"{base}+{F0[off]:x}"
        if child is None: return s
        if (F0[off], child) not in F1: return None
        return s + f">+{F1[(F0[off], child)]:x}"
    if base not in G: return None
    s = f"g:{G[base] + off:08X}+0"
    if child is None: return s
    key = (f"{G[base] + off:08X}", child)
    return s + f">+{F1[key]:x}" if key in F1 else None
def norm_arc_place(pl):
    p = parse(pl)
    if p and p[0].startswith("g:"):
        s = f"g:{int(p[0][2:], 16) + p[1]:08X}+0"
        return s if p[2] is None else s + f">+{p[2]:x}"
    return pl
def tr(evs, ref):
    res = set(); unk = 0
    for e in evs:
        e = tuple(e)
        if e[0] in ("call", "carg"):
            c = e[1]
            if ref: c = M.get(c, "?" + c)
            res.add((e[0], c) + e[2:])
        else:
            pl = tr_place(e[1]) if ref else norm_arc_place(e[1])
            if pl is None: unk += 1; continue
            res.add((e[0], pl) + e[2:])
    return res, unk
def pretty(e):
    if e[0] in ("call", "carg"):
        nm = Minv.get(e[1], e[1]); return f"{e[0]} {nm}" + ("" if e[0] == "call" else f" arg{e[2]}={e[3]:#x}")
    return f"{e[0]} {e[1]}" + (f" {e[2]:#x}" if len(e) > 2 else "")
res = []; txt = []
for n in sorted(M, key=lambda n: M[n]):
    if n not in R or M[n] not in A: continue
    r, unk = tr(R[n], True); a, _ = tr(A[M[n]], False)
    # constant arguments are only comparable where both sides recorded one for that callee and position
    rk = {(e[1], e[2]) for e in r if e[0] == "carg"}; ak = {(e[1], e[2]) for e in a if e[0] == "carg"}
    r = {e for e in r if e[0] != "carg" or (e[1], e[2]) in ak}; a = {e for e in a if e[0] != "carg" or (e[1], e[2]) in rk}
    # a constant store is only comparable where both sides store some constant there (one compiler may know
    # the value where the other computes it)
    rs = {e[1] for e in r if e[0] == "stc"}; as_ = {e[1] for e in a if e[0] == "stc"}
    r = {e for e in r if e[0] != "stc" or e[1] in as_}; a = {e for e in a if e[0] != "stc" or e[1] in rs}
    # known systematic difference: button masks passed by AI code use the arcade bit layout
    remap = lambda c: ((c & ~0x7F80) | ((c & 0x7F80) >> 1) & 0x7F80) if c & 0x7F80 else c
    ra = {(e[1], e[2], e[3]) for e in a if e[0] == "carg"}
    r = {(e[0], e[1], e[2], remap(e[3])) if e[0] == "carg" and e[1:] not in ra and (e[1], e[2], remap(e[3])) in ra else e for e in r}
    # reads are weak evidence (compilers reload differently); stores, tests and calls are strong
    strong = lambda s: {e for e in s if e[0] not in ("ld", "eq") and not (e[0] in ("call", "carg") and e[1] in ("?", "??"))}
    ro, ao = strong(r) - strong(a), strong(a) - strong(r)
    inter = len(strong(r) & strong(a)); uni = len(strong(r) | strong(a))
    j = inter / uni if uni else 1.0
    res.append([M[n], n, grade[n], status.get(n, ""), round(j, 2), len(ro), len(ao), unk])
    if ro or ao:
        txt.append(f"## {n} @{M[n]} grade={grade[n]} status={status.get(n, '')} agreement={j:.2f} untranslated_ref_events={unk}")
        txt += [f"  PS2 only: {pretty(e)}" for e in sorted(ro, key=str)] + [f"  arcade only: {pretty(e)}" for e in sorted(ao, key=str)]
# ---- content matching on events
def strong_set(evs, ref, kinds):
    t, unk = tr(evs, ref)
    bad = any(e[0] == "call" and str(e[1]).startswith("?") for e in t)
    t = frozenset(e for e in t if e[0] in kinds and e[1] not in ("?", "??"))
    return t, unk, bad
TIERS = ((("call", "st", "bit"), 4), (("call", "st", "bit", "carg", "stc"), 3))
pairs_found = {}
for kinds, need in TIERS:
    arc_sets = collections.defaultdict(list); ref_sets = collections.defaultdict(list)
    for x, evs in A.items():
        t, _, _ = strong_set(evs, False, kinds)
        if len(t) >= need: arc_sets[t].append(x)
    for n, evs in R.items():
        t, unk, bad = strong_set(evs, True, kinds)
        if len(t) >= need and unk == 0 and not bad: ref_sets[t].append(n)
    for t, names in ref_sets.items():
        xs = arc_sets.get(t, [])
        if len(names) == 1 and len(xs) == 1: pairs_found.setdefault(names[0], xs[0])
fb = []; nseed = nrej = 0
equal_now = {r[1] for r in res if r[5] == 0 and r[6] == 0}
for n in equal_now:
    if grade[n] not in ("exact", "manual", "low"): fb.append([M[n], n, "semeq"])
taken = set()
for n, x in pairs_found.items():
    if M.get(n) == x or x in taken: continue
    if n in M and grade[n] in ("exact", "manual"): continue
    holder = Minv.get(x)
    if holder and (grade[holder] in ("exact", "manual") or holder in equal_now): continue
    if n in M: fb.append([M[n], n, "reject"]); nrej += 1
    if holder: fb.append([x, holder, "reject"]); nrej += 1
    fb.append([x, n, "seed"]); nseed += 1; taken.add(x)
# ---- whole function-pointer tables placed where the arcade entries' events equal the PS2 entries'
ntab = 0
if len(sys.argv) > 7:
    kinds = ("call", "st", "bit", "carg", "stc")
    tables = json.load(open(sys.argv[6]))["tables"]
    AR = json.load(open(os.path.join(sys.argv[7], "functions.json")))
    hi = max(f["addr"] + f["size"] for f in AR["functions"])
    runs = [r for r in AR["runs"] if r["addr"] >= hi]
    sa = {int(x, 16): strong_set(evs, False, kinds)[0] for x, evs in A.items()}
    sr = {}
    for n, evs in R.items():
        t, unk, bad = strong_set(evs, True, kinds)
        if unk == 0 and not bad and len(t) >= 2: sr[n] = t
    for t in sorted(tables, key=lambda t: -len(t["items"])):
        items = t["items"]; cs = [sr.get(n) if n else None for n in items]; have = sum(1 for c in cs if c)
        if have < 4 or have < 0.5 * len(items): continue
        if all((n is None) or (n in M and grade[n] in ("exact", "manual")) for n in items): continue
        best = (0, None, None); second = 0
        for ri, r in enumerate(runs):
            full = r["items"]
            for k in range(len(full) - len(items) + 1):
                seg = full[k:k + len(items)]
                hit = sum(1 for c, x in zip(cs, seg) if c and sa.get(x) == c)
                if hit > best[0]:
                    if best[1] is not None and seg != runs[best[1]]["items"][best[2]:best[2] + len(items)]: second = best[0]
                    best = (hit, ri, k)
                elif hit > second and best[1] is not None and seg != runs[best[1]]["items"][best[2]:best[2] + len(items)]: second = hit
        hit, ri, k = best
        if ri is None or hit < 0.6 * have or hit - second < max(2, 0.1 * have): continue
        ntab += 1
        for n, x in zip(items, runs[ri]["items"][k:k + len(items)]):
            if not n or not x: continue
            xs = f"{x:08X}"
            if M.get(n) == xs or xs in taken or n in pairs_found: continue
            if n in M and grade[n] in ("exact", "manual"): continue
            holder = Minv.get(xs)
            if holder and grade[holder] in ("exact", "manual"): continue
            if n in M: fb.append([M[n], n, "reject"]); nrej += 1
            if holder: fb.append([xs, holder, "reject"]); nrej += 1
            fb.append([xs, n, "seed"]); nseed += 1; taken.add(xs)
    print(f"event tables: {ntab} tables placed by entry events")

# ---- similarity matching for names still unplaced (or weakly placed): weighted overlap of strong events
import math
KINDS = ("call", "st", "bit", "carg", "stc")
def toks(evs, ref):
    t, unk, bad = strong_set(evs, ref, KINDS)
    return {e for e in t if not (e[0] in ("call", "carg") and str(e[1]).startswith("?"))}
atok = {x: toks(evs, False) for x, evs in A.items()}
dfreq = collections.Counter(e for t in atok.values() for e in t)
idf = lambda e: math.log(len(atok) / dfreq[e]) if dfreq.get(e) else 0.0
inv = collections.defaultdict(list)
for x, t in atok.items():
    for e in t:
        if dfreq[e] <= 300: inv[e].append(x)
def wsim(rt, x):
    at = atok[x]; inter = sum(idf(e) for e in rt & at); uni = inter + sum(idf(e) for e in at - rt) + sum(idf(e) if e in dfreq else 6.0 for e in rt - at)
    return inter / uni if uni else 0.0
weak = lambda n: n not in M or grade[n] in ("medium", "low")
cands = {}
for n, evs in R.items():
    if not weak(n): continue
    rt = toks(evs, True)
    if sum(idf(e) for e in rt) < 12: continue                     # too little to go on
    pool = collections.Counter()
    for e in rt:
        for x in inv.get(e, ()): pool[x] += idf(e)
    sc = sorted(((wsim(rt, x), x) for x, _ in pool.most_common(25)), reverse=True)
    if sc and sc[0][0] >= 0.6 and (len(sc) == 1 or sc[0][0] - sc[1][0] >= 0.15): cands[n] = sc[0]
byx = collections.defaultdict(list)
for n, (sc, x) in cands.items(): byx[x].append((sc, n))
nsim = 0
for x, lst in byx.items():
    lst.sort(reverse=True); sc, n = lst[0]
    if len(lst) > 1 and lst[1][0] > sc - 0.15: continue
    if M.get(n) == x or x in taken: continue
    holder = Minv.get(x)
    if holder and not weak(holder): continue
    if holder:
        hs = wsim(toks(R[holder], True), x) if holder in R else 0.0
        if hs > sc - 0.2: continue
        fb.append([x, holder, "reject"]); nrej += 1
    if n in M: fb.append([M[n], n, "reject"]); nrej += 1
    fb.append([x, n, "simseed"]); nsim += 1; taken.add(x)
print(f"event similarity: {nsim} names proposed for unnamed or weakly named arcade functions")
# feedback accumulates across runs: earlier seeds and rejections stay unless a newer row contradicts them
fbp = os.path.join(out, "feedback.csv")
if os.path.exists(fbp):
    new_names = {f[1] for f in fb if f[2] in ("seed", "simseed")}; new_addrs = {f[0] for f in fb if f[2] in ("seed", "simseed")}
    newrej = {(f[0], f[1]) for f in fb if f[2] == "reject"}
    for r in csv.DictReader(open(fbp)):
        if r["verdict"] in ("seed", "simseed") and r["name"] not in new_names and r["arcade_addr"] not in new_addrs \
                and (r["arcade_addr"], r["name"]) not in newrej:
            fb.append([r["arcade_addr"], r["name"], r["verdict"]])
        elif r["verdict"] == "reject" and (r["arcade_addr"], r["name"]) not in newrej:
            fb.append([r["arcade_addr"], r["name"], "reject"])
with open(fbp, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "verdict"]); w.writerows(fb)
print(f"event feedback: {sum(1 for f in fb if f[2] == 'semeq')} matches confirmed by events, {nseed} new seeds, {nrej} rejected")
with open(os.path.join(out, "semdiff.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "grade", "status", "agreement", "ps2_only", "arcade_only", "untranslated"]); w.writerows(res)
open(os.path.join(out, "semdiff.txt"), "w").write("\n".join(txt) + "\n")
c = collections.Counter(("equal" if r[5] == 0 and r[6] == 0 else "differs", r[3]) for r in res)
print(sorted(c.items()))
