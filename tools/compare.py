#!/usr/bin/env python3
"""Compare each matched arcade function with its PS2 C source and classify it.
usage: compare.py <ps2_index.json> <split dir> <symbols.csv> <out status.csv>
Calls to PS2 functions with an empty body are ignored (stubs the arcade build simply does not call).
  same      - identical call sequence and every notable C constant is present in the arcade code
  reordered - same calls, different order or count (block layout, or the compiler merged identical tail calls)
  remapped  - same, except button-mask constants use the arcade bit layout (PS2 shifts bits >= 0x80 up by one)
  differs   - calls or constants disagree: arcade logic is probably not the PS2 logic (or the match is wrong)
  unknown   - not enough evidence (callees not all named yet, or nothing to compare)"""
import collections, csv, json, os, sys
PS = json.load(open(sys.argv[1])); A = {r["addr"]: r for r in json.load(open(os.path.join(sys.argv[2], "functions.json")))["functions"]}
P = {r["name"]: r for r in PS["functions"]}
rows = list(csv.DictReader(open(sys.argv[3]))); M = {r["name"]: int(r["arcade_addr"], 16) for r in rows}
Minv = {v: k for k, v in M.items()}
def canon(c): return c if c >= 0 else (c & 0xFFFF if c >= -0x8000 else c & 0xFFFFFFFF)
def remap(c): return (c & ~0x7F80) | ((c & 0x7F80) >> 1) & 0x7F80 if c & 0x7F80 else c      # PS2 button mask -> arcade
stat = collections.Counter(); out = []
for r in rows:
    n, x = r["name"], int(r["arcade_addr"], 16)
    cs = [c for c in P[n]["calls"] if c in P and not P[c].get("empty")]; xs = [y for y in A[x]["calls"] if y is not None]
    cm = [M.get(c) for c in cs]; named = [Minv.get(y) for y in xs]
    pc = {canon(c) for c in P[n]["consts"] if abs(c) >= 16}
    ac = {canon(c) for c in A[x]["consts"]} | {c & 0xFF for c in A[x]["consts"]} | {c & 0xFFFF for c in A[x]["consts"]}
    raw = [canon(c) for c in A[x]["consts"]]
    if len(raw) <= 60: ac |= {(u + v) & 0xFFFFFFFF for u in raw for v in raw}      # constants built as base + offset
    missing = sorted(pc - ac); remapped = [c for c in missing if c < 0x10000 and remap(c) in ac]
    missing = [c for c in missing if c not in remapped]
    if None in cm or None in named:
        known_c = collections.Counter(c for c in cm if c); known_x = collections.Counter(y for y, nm in zip(xs, named) if nm)
        calls = "differs" if (known_c - collections.Counter(xs)) or (known_x - collections.Counter(c for c in cm if c)) and None not in cm else "unknown"
    elif cm == xs: calls = "same"
    elif set(cm) == set(xs) and len(xs) <= len(cm): calls = "reordered"
    else: calls = "differs"
    cfrac = len(missing) / len(pc) if pc else 0
    if calls == "differs" or (len(missing) >= 2 and cfrac > 0.5): st = "differs"
    elif calls == "unknown" or (not cs and not pc): st = "unknown"
    elif missing and cfrac > 0.34: st = "unknown"
    else: st = "remapped" if remapped else calls
    stat[st] += 1
    out.append([r["arcade_addr"], n, r["grade"], st, len(cs), len(xs), " ".join(hex(m) for m in missing[:6])])
with open(sys.argv[4], "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "grade", "status", "ps2_calls", "arcade_calls", "ps2_consts_missing"]); w.writerows(out)
print(dict(stat))
