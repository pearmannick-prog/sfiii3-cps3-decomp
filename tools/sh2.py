"""SH-2 control-flow analysis: recursive-descent function discovery for a flat big-endian image."""
import collections, struct
from collections import defaultdict
import capstone as cs

def s8(x):  return x - 0x100 if x & 0x80 else x
def s12(x): return x - 0x1000 if x & 0x800 else x

def dest_reg(w):
    """Register written by an instruction (None if it writes no general register, or only restores one)."""
    hi, n, lo4, lo8 = w >> 12, (w >> 8) & 0xF, w & 0xF, w & 0xFF
    if hi in (0xE, 0x7, 0x9, 0xD, 0x5): return n
    if hi == 0x6: return None if lo4 == 6 and (w >> 4) & 0xF == 15 else n
    if hi == 0x3 and lo4 in (0x8, 0xA, 0xB, 0xC, 0xE, 0xF): return n
    if hi == 0x2 and lo4 in (0x9, 0xA, 0xB, 0xD): return n
    if hi == 0x4 and lo8 in (0x00, 0x01, 0x04, 0x05, 0x08, 0x09, 0x10, 0x11, 0x18, 0x19, 0x20, 0x21, 0x24, 0x25, 0x28, 0x29): return n
    if hi == 0x0 and (lo4 in (0xC, 0xD, 0xE, 0xA, 0x2) or lo8 == 0x29): return n
    if w >> 8 in (0xC7, 0xC4, 0xC5, 0xC6, 0x84, 0x85): return 0
    return None

class Func:
    __slots__ = ("addr", "insns", "lits", "calls", "tails", "ind_calls", "ind_jumps", "bad", "end", "sites")
    def __init__(self, addr):
        self.addr = addr; self.insns = set(); self.lits = {}   # lits: addr -> size
        self.calls = set(); self.tails = set(); self.ind_calls = 0; self.ind_jumps = []
        self.bad = None; self.end = addr; self.sites = {}   # call site pc -> target (None = indirect)

class Image:
    def __init__(self, data, base, code_lo=None, code_hi=None):
        self.d = data; self.base = base
        self.lo = code_lo or base; self.hi = code_hi or base + len(data)
        self.md = cs.Cs(cs.CS_ARCH_SH, cs.CS_MODE_SH2 | cs.CS_MODE_BIG_ENDIAN)
        self.funcs = {}
    def in_code(self, a): return self.lo <= a < self.hi and not a & 1
    def u16(self, a): return struct.unpack_from(">H", self.d, a - self.base)[0]
    def u32(self, a): return struct.unpack_from(">I", self.d, a - self.base)[0]
    def valid(self, a):
        o = a - self.base
        return next(self.md.disasm(self.d[o:o + 2], a, 1), None) is not None

    def lit_reg(self, f, pc, reg, depth=24):
        """Find the constant most recently loaded into reg by a PC-relative mov.l before pc."""
        a = pc - 2
        while a >= f.addr and depth:
            if a in f.insns:
                w = self.u16(a)
                if w >> 12 == 0xD and (w >> 8) & 0xF == reg:
                    return self.u32((a & ~3) + 4 + (w & 0xFF) * 4)
                if w >> 12 == 0x9 and (w >> 8) & 0xF == reg: return None
                if w >> 12 in (0x6, 0xE, 0x7) and (w >> 8) & 0xF == reg: return None
                depth -= 1
            a -= 2
        return None

    def analyze(self, entry):
        f = Func(entry); work = [entry]
        while work:
            pc = work.pop()
            while True:
                if pc in f.insns: break
                if not self.in_code(pc) or pc in f.lits or not self.valid(pc):
                    f.bad = f.bad or pc; break
                f.insns.add(pc); w = self.u16(pc); hi = w >> 12; n = (w >> 8) & 0xF
                delay = stop = False
                if hi == 0x9: f.lits[pc + 4 + (w & 0xFF) * 2] = 2
                elif hi == 0xD: f.lits[(pc & ~3) + 4 + (w & 0xFF) * 4] = 4
                elif w >> 8 == 0xC7: pass
                elif w in (0x000B, 0x002B): delay = stop = True
                elif hi == 0xA:
                    t = pc + 4 + s12(w & 0xFFF) * 2; delay = stop = True
                    if self._local(f, t): work.append(t)
                    else: f.tails.add(t); f.sites[pc] = t
                elif hi == 0xB:
                    t = pc + 4 + s12(w & 0xFFF) * 2; f.calls.add(t); f.sites[pc] = t; delay = True
                elif w >> 8 in (0x89, 0x8B, 0x8D, 0x8F):
                    work.append(pc + 4 + s8(w & 0xFF) * 2); delay = w >> 8 in (0x8D, 0x8F)
                elif w & 0xF0FF == 0x400B:
                    t = self.lit_reg(f, pc, n); delay = True
                    if t is not None and self.in_code(t): f.calls.add(t); f.sites[pc] = t
                    else: f.ind_calls += 1; f.sites[pc] = None
                elif w & 0xF0FF == 0x402B:
                    t = self.lit_reg(f, pc, n); delay = stop = True
                    if t is not None and self.in_code(t): f.tails.add(t); f.sites[pc] = t
                    else: f.ind_jumps.append(pc)
                elif w & 0xF0FF == 0x0003: f.ind_calls += 1; f.sites[pc] = None; delay = True
                elif w & 0xF0FF == 0x0023: f.ind_jumps.append(pc); delay = stop = True
                if delay:
                    ds = pc + 2
                    if not self.valid(ds): f.bad = f.bad or ds; break
                    f.insns.add(ds); w2 = self.u16(ds)
                    if w2 >> 12 == 0x9: f.lits[ds + 4 + (w2 & 0xFF) * 2] = 2
                    elif w2 >> 12 == 0xD: f.lits[(ds & ~3) + 4 + (w2 & 0xFF) * 4] = 4
                    pc += 4
                else: pc += 2
                if stop: break
        # calls through a callee-saved register that the function loads once (hoisted function pointer)
        pend = [pc for pc, t in f.sites.items() if t is None and 8 <= (self.u16(pc) >> 8) & 0xF <= 14 and self.u16(pc) & 0xF0FF == 0x400B]
        if pend:
            loads = collections.defaultdict(list); other = set()
            for pc in f.insns:
                w = self.u16(pc); r = dest_reg(w)
                if r is None: continue
                if w >> 12 == 0xD: loads[r].append(self.u32((pc & ~3) + 4 + (w & 0xFF) * 4))
                else: other.add(r)
            for pc in pend:
                r = (self.u16(pc) >> 8) & 0xF
                if len(loads[r]) == 1 and r not in other and self.in_code(loads[r][0]):
                    f.sites[pc] = loads[r][0]; f.calls.add(loads[r][0]); f.ind_calls -= 1
        f.end = max(f.insns) + 2 if f.insns else entry   # code extent; literal pools may be shared
        return f

    def _local(self, f, t):
        # a bra to an address that is already a known function entry is a tail call
        return t not in self.funcs or t == f.addr

    def discover(self, seeds):
        todo = list(seeds)
        while todo:
            a = todo.pop()
            if a in self.funcs or not self.in_code(a): continue
            self.funcs[a] = None
            f = self.analyze(a); self.funcs[a] = f
            todo.extend(f.calls | f.tails)
        return self.funcs

    def text(self, f, stop=None, lits=None):
        out = []; a = f.addr; stop = stop or f.end; lits = lits or f.lits
        labels = set()
        for pc in f.insns:
            w = self.u16(pc)
            if w >> 8 in (0x89, 0x8B, 0x8D, 0x8F): labels.add(pc + 4 + s8(w & 0xFF) * 2)
            elif w >> 12 == 0xA: labels.add(pc + 4 + s12(w & 0xFFF) * 2)
        while a < stop:
            if a in f.insns:
                i = next(self.md.disasm(self.d[a - self.base:a - self.base + 2], a, 1))
                if a in labels and a != f.addr: out.append(f".L{a:08X}:")
                w = self.u16(a); note = ""
                if w >> 12 == 0xD: note = f"  ! {self.u32((a & ~3) + 4 + (w & 0xFF) * 4):#010x}"
                elif w >> 12 == 0x9: note = f"  ! {self.u16(a + 4 + (w & 0xFF) * 2):#06x}"
                out.append(f"  /* {a:08X} {w:04X} */  {i.mnemonic:<8}{i.op_str}{note}"); a += 2
            elif lits.get(a) == 4 and a + 4 <= stop:
                out.append(f"  /* {a:08X} */  .long  {self.u32(a):#010x}"); a += 4
            else:
                out.append(f"  /* {a:08X} */  .word  {self.u16(a):#06x}"); a += 2
        return "\n".join(out)

    def features(self, f):
        """Architecture-neutral-ish features: immediates/constants, ordered call targets, RAM refs."""
        consts, ram = [], []
        for pc in sorted(f.insns):
            w = self.u16(pc); hi = w >> 12; lo = w & 0xFF
            if hi in (0xE, 0x7) or w >> 8 in (0x88, 0xC8, 0xC9, 0xCA, 0xCB):
                consts.append(s8(lo) if hi in (0xE, 0x7) or w >> 8 == 0x88 else lo)
            elif hi == 0x9:
                v = self.u16(pc + 4 + lo * 2); consts.append(v - 0x10000 if v & 0x8000 else v)
            elif hi == 0xD:
                v = self.u32((pc & ~3) + 4 + lo * 4)
                if 0x02000000 <= v < 0x02080000: ram.append(v)
                elif not (self.base <= v < self.base + len(self.d)): consts.append(v - (1 << 32) if v & 0x80000000 else v)
        return dict(addr=f.addr, size=f.end - f.addr, consts=consts, ram=ram, nums=self.nums(f),
                    calls=[f.sites[k] for k in sorted(f.sites)], ind_jumps=len(f.ind_jumps))

    def nums(self, f, is_addr=None):
        """Numbers a function mentions: immediates, literal constants and struct displacements (not stack slots).
        Largely independent of which compiler produced the code."""
        out = []
        for pc in f.insns:
            w = self.u16(pc); hi = w >> 12; n = (w >> 8) & 0xF; m = (w >> 4) & 0xF; lo = w & 0xFF; d = w & 0xF
            if hi == 0xE or w >> 8 == 0x88: out.append(s8(lo))
            elif hi == 0x7 and n != 15: out.append(s8(lo))
            elif w >> 8 in (0xC8, 0xC9, 0xCA, 0xCB): out.append(lo)
            elif hi == 0x9:
                v = self.u16(pc + 4 + lo * 2); out.append(v - 0x10000 if v & 0x8000 else v)
            elif hi == 0xD:
                la = (pc & ~3) + 4 + lo * 4; v = self.u32(la)
                if not (is_addr(la, v) if is_addr else (self.base <= v < self.base + len(self.d) or 0x02000000 <= v < 0x02080000)):
                    out.append(v - (1 << 32) if v & 0x80000000 else v)
            elif hi == 0x1 and n != 15 and d: out.append(d * 4)
            elif hi == 0x5 and m != 15 and d: out.append(d * 4)
            elif w >> 8 in (0x80, 0x84) and d: out.append(d)
            elif w >> 8 in (0x81, 0x85) and d: out.append(d * 2)
        return out
