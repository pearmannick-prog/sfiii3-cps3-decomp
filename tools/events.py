#!/usr/bin/env python3
"""Semantic events of SH-2 functions: what a function calls, which fields it reads and writes, and which
constants it stores or tests. Extracted by a small abstract interpreter, so two compilers' output for the
same C gives (nearly) the same event set.

usage: events.py arcade <image.bin> <split dir> <out.json>
       events.py ref    <obj dir> <out.json>

Event forms (all tuples, JSON lists on disk):
  ["call", callee]                 callee = function address (arcade) or symbol name (ref)
  ["carg", callee, k, const]       constant passed in r4+k (only registers written since the previous call)
  ["ld", place]                    a field or global was read
  ["st", place]                    a field or global was written
  ["stc", place, const]            ... with a constant
  ["eq", place, const]             compared for equality with a constant
  ["bit", place, const]            tested or masked with a constant
A place is a string: "a0+38" (offset 0x38 from argument 0), "a0+3b8>+2" (through the pointer at a0+0x3b8),
"g:<key>+0" (global; key = address in arcade, symbol in ref).
"""
import json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sh2 import Image, s8, s12, dest_reg

C, P, U = "c", "p", None            # value kinds: ("c", v) constant, ("p", root, off) root+off, None unknown
M32 = 0xFFFFFFFF

def place(root, off):
    """root: ("a", i) | ("g", key) | ("m", root, off). Depth is limited to one dereference."""
    if root[0] == "a": return f"a{root[1]}+{off & M32:x}"
    if root[0] == "g": return f"g:{root[1]}+{off & M32:x}"
    inner = root[1]
    if inner[0] == "m": return None
    return place(inner, root[2]) + f">+{off & M32:x}"

def sx(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) else v

class Interp:
    def __init__(self, img, lit, callee):
        self.img, self.lit, self.callee = img, lit, callee

    def run(self, f):
        """Forward dataflow over the function's instructions (values that differ on two incoming paths become
        unknown), then one pass that records events using the settled states."""
        img = self.img; ev = set(); insns = f.insns
        def step(pc, reg, fresh, emit):
            def addr(base, off):
                return (base[1], base[2] + off) if base and base[0] == P else None
            def load(n, a):
                pl = place(*a) if a else None
                if pl:
                    if emit: ev.add(("ld", pl))
                    reg[n] = (P, ("m", a[0], a[1]), 0)
                else: reg[n] = U
            def store(a, val, size):
                pl = place(*a) if a else None
                if pl and emit:
                    ev.add(("st", pl))
                    if val and val[0] == C: ev.add(("stc", pl, val[1] & ((1 << size * 8) - 1)))
            def test(kind, v, const):
                if not emit or not v or v[0] != P or v[2] != 0: return
                if v[1][0] == "m": d = place(v[1][1], v[1][2])
                elif v[1][0] == "a": d = f"a{v[1][1]}"
                else: d = None
                if d: ev.add((kind, d, const & 0xFFFF))
            w = img.u16(pc); hi, n, m, lo, d = w >> 12, (w >> 8) & 0xF, (w >> 4) & 0xF, w & 0xFF, w & 0xF
            rn, rm, r0 = reg.get(n), reg.get(m), reg.get(0)
            wr = dest_reg(w)
            if wr is not None: fresh.add(wr)
            if hi == 0xE: reg[n] = (C, s8(lo) & M32)
            elif hi == 0x9: reg[n] = (C, sx(img.u16(pc + 4 + lo * 2), 16) & M32)
            elif hi == 0xD: reg[n] = self.lit((pc & ~3) + 4 + lo * 4)
            elif hi == 0x6 and d == 3: reg[n] = rm
            elif hi == 0x7:
                if n == 15: pass
                elif rn and rn[0] == C: reg[n] = (C, (rn[1] + s8(lo)) & M32)
                elif rn and rn[0] == P: reg[n] = (P, rn[1], rn[2] + s8(lo))
                else: reg[n] = U
            elif hi == 0x3 and d in (0xC, 0x8):
                sg = 1 if d == 0xC else -1
                if rn and rm and rn[0] == C and rm[0] == C: reg[n] = (C, (rn[1] + sg * rm[1]) & M32)
                elif rn and rm and rn[0] == P and rm[0] == C: reg[n] = (P, rn[1], rn[2] + sg * sx(rm[1], 32))
                elif rn and rm and rn[0] == C and rm[0] == P and sg == 1: reg[n] = (P, rm[1], rm[2] + sx(rn[1], 32))
                else: reg[n] = U
            elif hi == 0x6 and d in (0, 1, 2): load(n, addr(rm, 0) if m != 15 else None)
            elif hi == 0x6 and d in (4, 5, 6):
                if m == 15:
                    if not 8 <= n <= 14: reg[n] = U                       # epilogue pops restore the caller's value
                else:
                    load(n, addr(rm, 0))
                    if rm and rm[0] == P and n != m: reg[m] = (P, rm[1], rm[2] + (1 << (d - 4)))
            elif hi == 0x2 and d in (0, 1, 2):
                if n != 15: store(addr(rn, 0), rm, 1 << d)
            elif hi == 0x2 and d in (4, 5, 6): pass                                   # push / pre-decrement store
            elif hi == 0x1:
                if n != 15: store(addr(rn, d * 4), rm, 4)
            elif hi == 0x5: load(n, addr(rm, d * 4) if m != 15 else None)
            elif w >> 8 == 0x80:
                if m != 15: store(addr(rm, d), r0, 1)
            elif w >> 8 == 0x81:
                if m != 15: store(addr(rm, d * 2), r0, 2)
            elif w >> 8 == 0x84: load(0, addr(rm, d) if m != 15 else None)
            elif w >> 8 == 0x85: load(0, addr(rm, d * 2) if m != 15 else None)
            elif hi == 0x0 and d in (4, 5, 6, 0xC, 0xD, 0xE):
                other = rn if d < 8 else rm
                a = None
                if r0 and other and r0[0] == C and other[0] == P: a = (other[1], other[2] + sx(r0[1], 32))
                elif r0 and other and r0[0] == P and other[0] == C: a = (r0[1], r0[2] + sx(other[1], 32))
                if (n if d < 8 else m) == 15: a = None
                if d < 8: store(a, rm, 1 << (d - 4))
                else: load(n, a)
            elif hi == 0x6 and d in (0xC, 0xD, 0xE, 0xF):
                if rm and rm[0] == C:
                    v = rm[1]
                    reg[n] = (C, (v & 0xFF if d == 0xC else v & 0xFFFF if d == 0xD else sx(v, 8) if d == 0xE else sx(v, 16)) & M32)
                else: reg[n] = rm
            elif w >> 8 == 0x88: test("eq", r0, s8(lo))
            elif hi == 0x3 and d == 0:
                if rm and rm[0] == C: test("eq", rn, sx(rm[1], 32))
                elif rn and rn[0] == C: test("eq", rm, sx(rn[1], 32))
            elif w >> 8 == 0xC8: test("bit", r0, lo)
            elif w >> 8 == 0xC9: test("bit", r0, lo); reg[0] = U
            elif hi == 0x2 and d in (8, 9):
                if rm and rm[0] == C: test("bit", rn, rm[1])
                elif rn and rn[0] == C: test("bit", rm, rn[1])
                if d == 9: reg[n] = U
            elif wr is not None: reg[wr] = U

        def do_call(t, reg, fresh, emit):
            if emit:
                name = self.callee(t); ev.add(("call", name))
                for k in range(4):
                    v = reg.get(4 + k)
                    if 4 + k in fresh and v and v[0] == C: ev.add(("carg", name, k, v[1] & 0xFFFF))
            for r in range(8): reg.pop(r, None)
            fresh.clear()

        def execute(pc, reg, fresh, emit):
            """Run the instruction at pc (plus its delay slot); return successor pcs."""
            w = img.u16(pc); hi = w >> 12
            if w >> 8 in (0x89, 0x8B): return [pc + 2, pc + 4 + s8(w & 0xFF) * 2]
            if w >> 8 in (0x8D, 0x8F):
                step(pc + 2, reg, fresh, emit); return [pc + 4, pc + 4 + s8(w & 0xFF) * 2]
            if hi in (0xA, 0xB) or w & 0xF0FF in (0x400B, 0x402B, 0x0003, 0x0023) or w in (0x000B, 0x002B):
                tgt = None
                if hi in (0xA, 0xB): tgt = pc + 4 + s12(w & 0xFFF) * 2
                elif w & 0xF0FF in (0x400B, 0x402B): tgt = reg.get((w >> 8) & 0xF)
                step(pc + 2, reg, fresh, emit)
                if hi == 0xB or w & 0xF0FF in (0x400B, 0x0003): do_call(tgt, reg, fresh, emit); return [pc + 4]
                if hi == 0xA:
                    if tgt in insns: return [tgt]
                    do_call(tgt, reg, fresh, emit); return []
                if w & 0xF0FF == 0x402B and tgt and tgt[0] == P and tgt[1][0] == "fn": do_call(tgt, reg, fresh, emit)
                return []
            step(pc, reg, fresh, emit); return [pc + 2]

        entry = (({4 + i: (P, ("a", i), 0) for i in range(4)}), frozenset())
        state = {f.addr: entry}; work = [f.addr]; guard = 0
        while work and guard < 200000:
            guard += 1; pc = work.pop()
            reg = dict(state[pc][0]); fresh = set(state[pc][1])
            for nx in execute(pc, reg, fresh, False):
                if nx not in insns: continue
                if nx not in state: state[nx] = (dict(reg), frozenset(fresh)); work.append(nx)
                else:
                    old, of = state[nx]
                    merged = {r: v for r, v in old.items() if reg.get(r) == v and v is not None}
                    mf = of & fresh
                    if merged != {r: v for r, v in old.items() if v is not None} or mf != of:
                        state[nx] = (merged, mf); work.append(nx)
        for pc in sorted(state): execute(pc, dict(state[pc][0]), set(state[pc][1]), True)
        return sorted(ev, key=str)

def arcade(image, split, out):
    BASE = 0x06000000; d = open(image, "rb").read()
    fj = json.load(open(os.path.join(split, "functions.json")))["functions"]
    hi = max(f["addr"] + f["size"] for f in fj)
    img = Image(d, BASE, BASE + 0x400, hi + 0x100); img.funcs = {f["addr"]: None for f in fj}
    def lit(la):
        v = img.u32(la)
        if 0x02000000 <= v < 0x02080000 or (BASE + 0x13B000 <= v < BASE + len(d)): return (P, ("g", f"{v:08X}"), 0)
        if v in img.funcs: return (P, ("fn", v), 0)
        return (C, v)
    def callee(t):
        if isinstance(t, int): return f"{t:08X}"
        if t and t[0] == P and t[1][0] == "fn": return f"{t[1][1]:08X}"
        return "?"
    it = Interp(img, lit, callee); res = {}
    for f in fj:
        try: res[f"{f['addr']:08X}"] = it.run(img.analyze(f["addr"]))
        except (struct.error, RecursionError): pass
    json.dump(res, open(out, "w")); print(f"{len(res)} arcade functions")

def ref(objdir, out):
    from elftools.elf.elffile import ELFFile
    res = {}
    for fn in sorted(os.listdir(objdir)):
        if not fn.endswith(".o"): continue
        elf = ELFFile(open(os.path.join(objdir, fn), "rb")); text = elf.get_section_by_name(".text")
        if text is None or not text.data_size: continue
        data = text.data() + b"\x00" * 8; tidx = elf.get_section_index(".text"); symtab = elf.get_section_by_name(".symtab")
        funcs, byaddr = {}, {}
        for sym in symtab.iter_symbols():
            if sym["st_info"]["type"] == "STT_FUNC" and sym["st_shndx"] == tidx:
                funcs[sym.name.lstrip("_")] = sym["st_value"]; byaddr[sym["st_value"]] = sym.name.lstrip("_")
        rel = {}; rs = elf.get_section_by_name(".rela.text")
        if rs is not None:
            for r in rs.iter_relocations():
                sym = symtab.get_symbol(r["r_info_sym"]); shn = sym["st_shndx"]
                secname = elf.get_section(shn).name if isinstance(shn, int) else ""
                rel[r["r_offset"]] = (sym.name.lstrip("_"), r["r_addend"], shn == tidx, sym["st_info"]["type"], secname)
        img = Image(data, 0, 0, len(data) - 8); img.funcs = {a: None for a in funcs.values()}
        def lit(la):
            if la in rel:
                nm, add, intext, ty, sec = rel[la]
                if intext: return (P, ("fn", byaddr.get(add if not nm else funcs.get(nm, add), nm or "?")), 0)
                if ty == "STT_FUNC" or nm in ALLFUNCS: return (P, ("fn", nm), 0)
                if not nm: return (P, ("g", f"{fn}{sec}"), add)       # file-local data: key by object + section
                return (P, ("g", nm), add)
            return (C, img.u32(la))
        def callee(t):
            if isinstance(t, int): return byaddr.get(t, "?")
            if t and t[0] == P and t[1][0] == "fn": return str(t[1][1])
            return "?"
        it = Interp(img, lit, callee)
        for name, a in funcs.items():
            try: res[name] = it.run(img.analyze(a))
            except (struct.error, RecursionError): pass
    json.dump(res, open(out, "w")); print(f"{len(res)} reference functions")

ALLFUNCS = set()
if __name__ == "__main__":
    if sys.argv[1] == "arcade": arcade(*sys.argv[2:5])
    else:
        from elftools.elf.elffile import ELFFile
        for fn in os.listdir(sys.argv[2]):                 # every function symbol defined anywhere
            if fn.endswith(".o"):
                st = ELFFile(open(os.path.join(sys.argv[2], fn), "rb")).get_section_by_name(".symtab")
                ALLFUNCS.update(s.name.lstrip("_") for s in st.iter_symbols() if s["st_info"]["type"] == "STT_FUNC")
        ref(sys.argv[2], sys.argv[3])
