#!/usr/bin/env python3
"""Discover functions in the decrypted program image; write a function table and per-function asm.
usage: split.py <image.bin> <out_dir> [--code-hi HEX] [--no-asm]

Strategy: exception vectors -> call graph -> code pointers found in data -> linear gap filling
(the compiler lays functions out back to back), then re-analysis so bra-style tail calls
split correctly."""
import argparse, csv, json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sh2 import Image
BASE = 0x06000000
ap = argparse.ArgumentParser(); ap.add_argument("image"); ap.add_argument("out")
ap.add_argument("--code-lo", type=lambda s: int(s, 16), default=0x06000400)
ap.add_argument("--code-hi", type=lambda s: int(s, 16), default=0x0613BF00)
ap.add_argument("--no-asm", action="store_true"); a = ap.parse_args()
d = open(a.image, "rb").read()
img = Image(d, BASE, a.code_lo, a.code_hi)
PAD = (0x0000, 0x0009)

def covered():
    c = set()
    for f in img.funcs.values():
        c.update(range(f.addr, f.end, 2))
        for l, n in f.lits.items(): c.update(range(l & ~1, l + n, 2))
    return c

img.discover({v for v in struct.unpack_from(">256I", d, 0) if img.in_code(v)})
n_graph = len(img.funcs)
ptrs = {v for v in struct.unpack_from(f">{len(d)//4}I", d, 0) if img.in_code(v)}
for _ in range(6):                      # pointers in data
    cov = covered(); new = set()
    for v in sorted(ptrs - set(img.funcs) - cov):
        f = img.analyze(v)
        if not f.bad and len(f.insns) >= 2 and not (set(range(f.addr, f.end, 2)) & cov): new.add(v)
    if not new: break
    img.discover(new)
n_ptr = len(img.funcs)
def gap_fill():
    cov = covered(); unknown = []; added = 0; p = a.code_lo
    while p < a.code_hi:
        if p in cov or img.u16(p) in PAD: p += 2; continue
        q = p
        while q < a.code_hi and q not in cov: q += 2
        f = img.analyze(p)
        if not f.bad and f.insns and f.end <= q and p not in img.funcs:
            n0 = set(img.funcs); img.discover({p}); added += 1
            for k in set(img.funcs) - n0:
                g = img.funcs[k]; cov.update(range(g.addr, g.end, 2))
                for l, n in g.lits.items(): cov.update(range(l & ~1, l + n, 2))
        else:
            unknown.append((p, q)); p = q
    return added, unknown
while True:
    added, unknown = gap_fill()
    if not added: break
for _ in range(4):                      # split bra tail calls into known functions
    before = {k: (f.end, len(f.insns)) for k, f in img.funcs.items()}
    for k in list(img.funcs): img.funcs[k] = img.analyze(k)
    img.discover({t for f in img.funcs.values() for t in f.calls | f.tails} - set(img.funcs))
    if before == {k: (f.end, len(f.insns)) for k, f in img.funcs.items()}: break

# Drop false entries: an address inside another function's code that nothing calls is a label or a
# coincidental data value (round numbers like 0x06010000 turn up in data), not a function. Real secondary
# entry points, which something does call, are kept.
called = set()
for f in img.funcs.values():
    for pc, t in f.sites.items():
        w = img.u16(pc)
        if t is not None and (w >> 12 == 0xB or w & 0xF0FF == 0x400B): called.add(t)
seen = set(); labels = []
for f in sorted(img.funcs.values(), key=lambda f: f.addr):       # in address order, against accepted functions only,
    if f.addr in seen and f.addr not in called: labels.append(f.addr); continue      # so a bogus entry cannot evict what follows it
    seen.update(f.insns)
    for l, n in f.lits.items(): seen.update(range(l & ~1, l + n, 2))
# rescue: an overlapping entry listed in a pointer table whose other entries are ordinary functions is a real
# function sharing its tail with a neighbour, not a stray value
lab = set(labels); words = struct.unpack_from(f">{len(d)//4}I", d, 0); i0 = (a.code_hi - BASE) // 4; i = i0
while i < len(words):
    if words[i] in img.funcs:
        j = i
        while j < len(words) and (words[j] in img.funcs or words[j] == 0): j += 1
        ent = [w for w in words[i:j] if w]
        if len(ent) >= 4 and sum(1 for w in ent if w not in lab) >= 0.8 * len(ent): lab.difference_update(ent)
        i = j
    else: i += 1
for f in img.funcs.values():                                     # ... and so is the target of another function's tail jump
    for t in f.tails:
        if t in lab and t not in f.insns: lab.discard(t)
labels = sorted(lab)
for x in labels: del img.funcs[x]
for k in list(img.funcs): img.funcs[k] = img.analyze(k)          # branches into dropped labels are local again
print(f"dropped {len(labels)} labels or data values that had been taken for functions")
os.makedirs(a.out, exist_ok=True)
fs = sorted(img.funcs.values(), key=lambda f: f.addr)
with open(os.path.join(a.out, "functions.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow("addr size insns calls ind_calls ind_jumps literals bad".split())
    for f in fs:
        w.writerow([f"{f.addr:08X}", f.end - f.addr, len(f.insns), len(f.calls | f.tails), f.ind_calls,
                    len(f.ind_jumps), len(f.lits), f"{f.bad:08X}" if f.bad else ""])
with open(os.path.join(a.out, "unknown_regions.csv"), "w") as fh:
    fh.write("start,end,size\n"); fh.writelines(f"{s:08X},{e:08X},{e-s}\n" for s, e in unknown)
# runs of consecutive function pointers anywhere in the image (dispatch tables)
runs = []; cur = None
words = struct.unpack_from(f">{len(d)//4}I", d, 0)
for i, v in enumerate(words):
    ok = v in img.funcs or (v == 0 and cur is not None)
    if ok:
        if cur is None: cur = [BASE + 4 * i, []]
        cur[1].append(v)
    elif cur is not None:
        while cur[1] and cur[1][-1] == 0: cur[1].pop()
        if sum(1 for x in cur[1] if x) >= 2: runs.append(dict(addr=cur[0], items=cur[1]))
        cur = None
json.dump(dict(functions=[img.features(f) for f in fs], runs=runs), open(os.path.join(a.out, "functions.json"), "w"))
print(f"pointer-table runs: {len(runs)} with {sum(len(r['items']) for r in runs)} entries")
lits = {}
for f in fs: lits.update(f.lits)
nxt = {x.addr: max(x.end, y.addr) for x, y in zip(fs, fs[1:])}; nxt[fs[-1].addr] = fs[-1].end
if not a.no_asm:
    os.makedirs(os.path.join(a.out, "asm"), exist_ok=True)
    for f in fs:
        open(os.path.join(a.out, "asm", f"func_{f.addr:08X}.s"), "w").write(f"func_{f.addr:08X}:\n{img.text(f, nxt[f.addr], lits)}\n")
ov = sum(1 for x, y in zip(fs, fs[1:]) if y.addr < x.end)
tot = a.code_hi - a.code_lo; inf = len(covered()) * 2; unk = sum(e - s for s, e in unknown)
print(f"functions: {len(fs)} (call graph {n_graph}, +data pointers {n_ptr-n_graph}, +gap fill {len(fs)-n_ptr})")
print(f"bad: {sum(1 for f in fs if f.bad)}  overlapping: {ov}  with indirect jumps: {sum(1 for f in fs if f.ind_jumps)}")
print(f"code range {tot:#x}: in functions {inf:#x} ({100*inf/tot:.1f}%), unknown {unk:#x} in {len(unknown)} regions")
