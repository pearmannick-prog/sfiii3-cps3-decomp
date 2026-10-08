#!/usr/bin/env python3
"""Discover functions in the decrypted program image; write a function table and per-function asm.
usage: split.py <image.bin> <out_dir> [--code-hi HEX] [--no-asm]

Strategy: exception vectors -> call graph -> code pointers found in data -> linear gap filling
(the compiler lays functions out back to back), then re-analysis so bra-style tail calls
split correctly."""
import argparse, csv, os, struct, sys
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

os.makedirs(a.out, exist_ok=True)
fs = sorted(img.funcs.values(), key=lambda f: f.addr)
with open(os.path.join(a.out, "functions.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow("addr size insns calls ind_calls ind_jumps literals bad".split())
    for f in fs:
        w.writerow([f"{f.addr:08X}", f.end - f.addr, len(f.insns), len(f.calls | f.tails), f.ind_calls,
                    len(f.ind_jumps), len(f.lits), f"{f.bad:08X}" if f.bad else ""])
with open(os.path.join(a.out, "unknown_regions.csv"), "w") as fh:
    fh.write("start,end,size\n"); fh.writelines(f"{s:08X},{e:08X},{e-s}\n" for s, e in unknown)
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
