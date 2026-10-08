#!/usr/bin/env python3
"""Exact lifter for CPU-AI pattern routines.

Most Pattern*/Passive* routines have one shape:
    switch (CP_Index[wk->wu.id][0]) { case k: Helper(wk, <constants>); break; ... default: End_Pattern(wk); }
This tool recovers that shape from the SH-2 code (cases, callee, every argument value) and compares it
argument by argument with the PS2 C. Functions whose arguments differ get arcade C generated.

usage: lift_patterns.py <image.bin> <3s-decomp dir> <symbols.csv> <data_symbols.csv> <out report.csv>
                        [--emit DIR] [--split DIR --content content.csv]
--content writes feedback for match.py: `verified` pairs (arguments agree exactly), `reject` pairs (weak match whose
content disagrees) and `seed` pairs (unnamed arcade routine whose exact content matches one unplaced PS2 routine).
"""
import argparse, collections, csv, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tree_sitter_c
from tree_sitter import Language, Parser
from sh2 import Image, s8, s12

ap = argparse.ArgumentParser()
for x in ("image", "ref", "symbols", "data", "out"): ap.add_argument(x)
ap.add_argument("--emit"); ap.add_argument("--split"); ap.add_argument("--content"); ap.add_argument("--ps2"); ap.add_argument("--code-hi", type=lambda s: int(s, 16), default=0x0613BDFA)
a = ap.parse_args()
BASE = 0x06000000
d = open(a.image, "rb").read(); img = Image(d, BASE, BASE + 0x400, a.code_hi)
rows = list(csv.DictReader(open(a.symbols)))
NAME = {int(r["arcade_addr"], 16): r["name"] for r in rows}
DATA = {r["name"]: int(r["arcade_addr"], 16) for r in csv.DictReader(open(a.data))}
CP_INDEX = DATA["CP_Index"]
SRC = os.path.join(a.ref, "src/anniversary/sf33rd")
parser = Parser(Language(tree_sitter_c.language()))

# ---------------------------------------------------------------- C side
def cnum(node):
    t = node.text.decode()
    if node.type == "number_literal":
        try: return int(t.rstrip("uUlL"), 0)
        except ValueError: return None
    if node.type == "unary_expression" and t.startswith("-"):
        v = cnum(node.named_children[0]); return None if v is None else -v
    if node.type == "parenthesized_expression": return cnum(node.named_children[0])
    return None

def fname(decl):
    while decl is not None and decl.type != "identifier": decl = decl.child_by_field_name("declarator")
    return decl.text.decode() if decl is not None else None

CFUNC, PROTO = {}, {}          # name -> (file, selector, [(case, [(callee, args)])]) ; name -> [param type text]
def parse_c(path):
    tree = parser.parse(open(path, "rb").read()); st = [tree.root_node]
    while st:
        n = st.pop()
        if n.type != "function_definition": st.extend(n.children); continue
        name = fname(n.child_by_field_name("declarator")); body = n.child_by_field_name("body")
        pl = n.child_by_field_name("declarator").child_by_field_name("parameters")
        if name and pl is not None:
            PROTO[name] = [p.child_by_field_name("type").text.decode() + ("*" if "*" in p.text.decode() else "")
                           for p in pl.named_children if p.type == "parameter_declaration" and p.text != b"void"]
        if not name or body is None: continue
        kids = [k for k in body.named_children if k.type != "comment"]
        if len(kids) != 1 or kids[0].type != "switch_statement": continue
        sw = kids[0]; sel = re.sub(r"\s+", "", sw.child_by_field_name("condition").text.decode())
        cases, ok = [], True
        for cs in sw.child_by_field_name("body").named_children:
            if cs.type == "comment": continue
            if cs.type != "case_statement": ok = False; break
            val = cs.child_by_field_name("value"); key = "default" if val is None else cnum(val)
            calls = []
            for stmt in cs.named_children:
                if (val is not None and stmt.id == val.id) or stmt.type in ("comment", "break_statement"): continue
                e = stmt.named_children[0] if stmt.type == "expression_statement" and stmt.named_children else None
                if e is None or e.type != "call_expression" or e.child_by_field_name("function").type != "identifier": ok = False; break
                args = []
                for arg in e.child_by_field_name("arguments").named_children:
                    if arg.type == "identifier": args.append(arg.text.decode())
                    else:
                        v = cnum(arg)
                        if v is None: ok = False
                        args.append(v)
                calls.append((e.child_by_field_name("function").text.decode(), args))
            if key is None or not ok: ok = False; break
            cases.append((key, calls))
        if ok: CFUNC[name] = (os.path.relpath(path, SRC), sel, cases)

for root, _, files in sorted(os.walk(SRC)):
    for fn in sorted(files):
        if fn.endswith(".c"): parse_c(os.path.join(root, fn))

# ---------------------------------------------------------------- arcade side
class Unsupported(Exception): pass
u16 = img.u16; u32 = img.u32

def step(w, pc, reg, pushes):
    """Execute one non-branch instruction on the constant state. Raises Unsupported for anything else."""
    hi, n, m, lo = w >> 12, (w >> 8) & 0xF, (w >> 4) & 0xF, w & 0xFF
    if w == 0x0009: return
    if hi == 0xE: reg[n] = s8(lo) & 0xFFFFFFFF
    elif hi == 0x9: v = u16(pc + 4 + lo * 2); reg[n] = (v - 0x10000 if v & 0x8000 else v) & 0xFFFFFFFF
    elif hi == 0xD: reg[n] = u32((pc & ~3) + 4 + lo * 4)
    elif hi == 0x7:
        if n == 15:
            if lo & 3 or s8(lo) < 0 or s8(lo) // 4 > len(pushes): raise Unsupported("stack adjust")
            del pushes[len(pushes) - s8(lo) // 4:]
        elif isinstance(reg.get(n), int): reg[n] = (reg[n] + s8(lo)) & 0xFFFFFFFF
        else: raise Unsupported("add to unknown")
    elif hi == 0x6 and w & 0xF == 0x3: reg[n] = reg.get(m)
    elif hi == 0x6 and w & 0xF in (0xC, 0xD, 0xE, 0xF) and isinstance(reg.get(m), int):
        v = reg[m]; k = w & 0xF
        reg[n] = (v & 0xFF if k == 0xC else v & 0xFFFF if k == 0xD else s8(v & 0xFF) & 0xFFFFFFFF if k == 0xE
                  else ((v & 0xFFFF) - 0x10000 if v & 0x8000 else v & 0xFFFF) & 0xFFFFFFFF)
    elif hi == 0x3 and w & 0xF == 0xC and isinstance(reg.get(n), int) and isinstance(reg.get(m), int):
        reg[n] = (reg[n] + reg[m]) & 0xFFFFFFFF
    elif w & 0xFF0F == 0x2F06: pushes.append(reg.get(m))
    elif w == 0x4F26: pass                                         # lds.l @r15+,pr
    elif w & 0xF0FF == 0x60F6:                                     # epilogue pop: restores a saved register
        if pushes: raise Unsupported("pop with arguments pending")
        reg.pop(n, None)
    else: raise Unsupported(f"insn {w:04X}")

def block(pc, reg, limit=200):
    """Run a case body: straight-line code with calls, ending in rts or a tail call."""
    pushes = []; calls = []
    def call(target):
        if target not in NAME: raise Unsupported("call to unnamed function")
        calls.append((NAME[target], [reg.get(r) for r in (4, 5, 6, 7)], pushes[::-1]))
    while limit:
        limit -= 1; w = u16(pc); hi = w >> 12
        if w == 0x000B: step(u16(pc + 2), pc + 2, reg, pushes); return calls
        if hi == 0xA:
            t = pc + 4 + s12(w & 0xFFF) * 2; step(u16(pc + 2), pc + 2, reg, pushes)
            if t in NAME: call(t); return calls
            pc = t; continue
        if hi == 0xB:
            t = pc + 4 + s12(w & 0xFFF) * 2; step(u16(pc + 2), pc + 2, reg, pushes); call(t); pc += 4
            for r in (0, 1, 2, 3, 5, 6, 7): reg.pop(r, None)
            continue
        if w & 0xF0FF in (0x400B, 0x402B):
            t = reg.get((w >> 8) & 0xF); step(u16(pc + 2), pc + 2, reg, pushes)
            if not isinstance(t, int): raise Unsupported("indirect call")
            call(t)
            if w & 0xFF == 0x2B: return calls
            pc += 4
            for r in (0, 1, 2, 3, 5, 6, 7): reg.pop(r, None)
            continue
        if w >> 8 in (0x89, 0x8B, 0x8D, 0x8F) or w & 0xF0FF in (0x0003, 0x0023): raise Unsupported("branch in case body")
        step(w, pc, reg, pushes); pc += 2
    raise Unsupported("too long")

def lift(entry):
    pc = entry; reg = {4: "wk"}; junk = []; sel = []
    while u16(pc) >> 8 != 0x88:                                   # selector: CP_Index[wk->wu.id][0]
        w = u16(pc)
        if pc - entry > 48: raise Unsupported("selector")
        if w in (0x8544, 0x4008, 0x001D): sel.append(w)
        elif w != 0x4F22:
            try: step(w, pc, reg, junk)                           # register saves and values hoisted out of the cases
            except Unsupported: raise Unsupported("selector")
        pc += 2
    if sel != [0x8544, 0x4008, 0x4008, 0x001D] or reg.get(1) != CP_INDEX: raise Unsupported("selector is not CP_Index")
    targets = []
    while True:
        w = u16(pc)
        if w >> 8 == 0x88:
            k = s8(w & 0xFF); b = u16(pc + 2)
            if b >> 8 == 0x89: targets.append((k, pc + 2 + 4 + s8(b & 0xFF) * 2)); pc += 4
            elif b >> 8 == 0x8D:                                  # bt/s: the delay slot runs on every path
                step(u16(pc + 4), pc + 4, reg, junk); targets.append((k, pc + 2 + 4 + s8(b & 0xFF) * 2)); pc += 6
            else: raise Unsupported("case dispatch")
        elif w >> 12 == 0xA:
            step(u16(pc + 2), pc + 2, reg, junk); targets.append(("default", pc + 4 + s12(w & 0xFFF) * 2)); break
        else: targets.append(("default", pc)); break
    return [(k, block(t, dict(reg))) for k, t in targets]

# ---------------------------------------------------------------- compare
def norm(v, ty):
    if not isinstance(v, int): return v
    return v & 0xFFFF if ty in ("s16", "u16") else v & 0xFF if ty in ("s8", "u8") else v & 0xFFFFFFFF
def remap(c): return (c & ~0x7F80) | ((c & 0x7F80) >> 1) & 0x7F80 if c & 0x7F80 else c
def show(v, ty):
    if not isinstance(v, int): return str(v)
    if ty in ("s16", "s8", "s32", "int") or ty is None:
        bits = 16 if ty == "s16" else 8 if ty == "s8" else 32
        v &= (1 << bits) - 1
        if v >> (bits - 1): v -= 1 << bits
        return str(v) if -10 < v < 10 else (f"-0x{-v:X}" if v < 0 else f"0x{v:X}")
    return str(v) if v < 10 else f"0x{v:X}"

stat = collections.Counter(); report = []; emit = collections.defaultdict(list); remap_sites = collections.Counter()
diff_sites = collections.Counter()
for r in rows:
    name, addr = r["name"], int(r["arcade_addr"], 16)
    if name not in CFUNC or CFUNC[name][1] != "(CP_Index[wk->wu.id][0])": continue
    cfile, _, ccases = CFUNC[name]
    try: acases = lift(addr)
    except Unsupported as e:
        stat["not lifted"] += 1; report.append([r["arcade_addr"], name, r["grade"], "not-lifted", str(e)]); continue
    # shape the arcade calls with the callee's prototype
    lifted, ok = [], True
    for k, calls in acases:
        out = []
        for callee, regs, stack in calls:
            ptypes = PROTO.get(callee)
            if ptypes is None: ok = False; break
            vals = (regs + stack)[:len(ptypes)]
            if len(vals) < len(ptypes) or any(v is None for v in vals): ok = False; break
            out.append((callee, vals, ptypes))
        lifted.append((k, out))
    if not ok:
        stat["not lifted"] += 1; report.append([r["arcade_addr"], name, r["grade"], "not-lifted", "argument unknown"]); continue
    same = len(lifted) == len(ccases); only_remap = True; notes = []
    if same:
        for (ka, calla), (kc, callc) in zip(lifted, ccases):
            if ka != kc or len(calla) != len(callc): same = False; notes.append(f"case {kc}: structure"); continue
            for (na, va, ty), (nc, vc) in zip(calla, callc):
                if na != nc or len(va) != len(vc): same = False; only_remap = False; notes.append(f"case {kc}: {nc} -> {na}"); continue
                for i, (x, y, t) in enumerate(zip(va, vc, ty)):
                    if norm(x, t) == norm(y, t): continue
                    same = False
                    if isinstance(y, int) and isinstance(x, int) and norm(remap(norm(y, t)), t) == norm(x, t): remap_sites[(nc, i)] += 1
                    else: only_remap = False; diff_sites[(nc, i)] += 1
                    notes.append(f"case {kc}: {nc} arg{i} {show(y, t)} -> {show(x, t)}")
    else: only_remap = False; notes.append(f"cases {len(ccases)} -> {len(lifted)}")
    status = "identical" if same else "remap-only" if only_remap else "different"
    stat[status] += 1; report.append([r["arcade_addr"], name, r["grade"], status, "; ".join(notes[:6])])
    if not same: emit[cfile].append((addr, name, lifted, notes))

if a.content:
    import json
    REMAP_POS = {k for k, c in remap_sites.items() if c >= 10}
    def sig_c(cases):
        out = []
        for k, calls in cases:
            for callee, args in calls:
                ty = PROTO.get(callee)
                if ty is None or len(ty) != len(args): return None
                out.append((k, callee, tuple(norm(remap(norm(v, t)), t) if (callee, i) in REMAP_POS and isinstance(v, int) else norm(v, t)
                                             for i, (v, t) in enumerate(zip(args, ty)))))
        return tuple(out)
    def sig_a(cases):
        out = []
        for k, calls in cases:
            for callee, regs, stack in calls:
                ty = PROTO.get(callee)
                if ty is None: return None
                vals = (regs + stack)[:len(ty)]
                if len(vals) < len(ty) or any(v is None for v in vals): return None
                out.append((k, callee, tuple(norm(v, t) for v, t in zip(vals, ty))))
        return tuple(out)
    AR = json.load(open(os.path.join(a.split, "functions.json")))
    sigA = {}
    for f in AR["functions"]:
        try: sigA[f["addr"]] = sig_a(lift(f["addr"]))
        except (Unsupported, struct.error): pass
    sigC = {n: sig_c(c) for n, (cf, sel, c) in CFUNC.items() if sel == "(CP_Index[wk->wu.id][0])"}
    # whole tables placed by exact content: count entries whose lifted arcade routine equals the PS2 routine
    runs = [r for r in AR["runs"] if r["addr"] >= a.code_hi]
    placed = {}; taken = {}; ntab = 0
    for t in sorted(json.load(open(a.ps2))["tables"], key=lambda t: -len(t["items"])):
        items = t["items"]; cs = [sigC.get(n) if n else None for n in items]
        have = sum(1 for c in cs if c)
        if have < 4 or have < 0.5 * len(items): continue
        best = (0, None, None); second = 0
        for ri, r in enumerate(runs):
            full = r["items"]
            for k in range(len(full) - len(items) + 1):
                hit = sum(1 for c, x in zip(cs, full[k:k + len(items)]) if c and sigA.get(x) == c)
                if hit > best[0]:
                    if best[1] is not None and full[k:k + len(items)] != runs[best[1]]["items"][best[2]:best[2] + len(items)]: second = best[0]
                    best = (hit, ri, k)
                elif hit > second and full[k:k + len(items)] != runs[best[1]]["items"][best[2]:best[2] + len(items)]: second = hit
        hit, ri, k = best
        if ri is None or hit < 0.6 * have or hit - second < max(2, 0.05 * have): continue
        ntab += 1
        for n, x in zip(items, runs[ri]["items"][k:k + len(items)]):
            if n and x and placed.get(n, x) == x and taken.get(x, n) == n: placed[n] = x; taken[x] = n
    named = {r["name"] for r in rows} | set(placed)
    byc, bya = collections.defaultdict(list), collections.defaultdict(list)
    for name, sg in sigC.items():
        if name not in named and sg and len(sg) >= 2: byc[sg].append(name)
    for x, sg in sigA.items():
        if x not in NAME and x not in taken and sg and len(sg) >= 2: bya[sg].append(x)
    seeds = [(bya[sg][0], names[0]) for sg, names in byc.items() if len(names) == 1 and len(bya.get(sg, ())) == 1]
    with open(a.content, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["arcade_addr", "name", "verdict"])
        for n, x in placed.items(): w.writerow([f"{x:08X}", n, "verified" if sigC.get(n) and sigC[n] == sigA.get(x) else "table"])
        for addr, name, grade, status, detail in report:
            if name in placed or int(addr, 16) in taken: continue
            if status in ("identical", "remap-only"): w.writerow([addr, name, "verified"])
            elif status == "different" and grade != "high": w.writerow([addr, name, "reject"])
        for x, n in seeds: w.writerow([f"{x:08X}", n, "seed"])
    print(f"content feedback: {ntab} tables placed by exact content ({len(placed)} routines), {len(seeds)} single seeds")

with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["arcade_addr", "name", "grade", "status", "detail"]); w.writerows(report)
print(dict(stat))
print("remap positions:", ", ".join(f"{n}[{i}] x{c}" for (n, i), c in remap_sites.most_common(12)))
print("other differing positions:", ", ".join(f"{n}[{i}] x{c}" for (n, i), c in diff_sites.most_common(12)))

if a.emit:
    os.makedirs(a.emit, exist_ok=True); nfun = 0
    for cfile, funcs in sorted(emit.items()):
        base = os.path.basename(cfile); hdr = cfile[:-2] + ".h"
        out = [f"// Arcade (CPS-3, 990512) versions of routines in {cfile} that differ from the PS2 build.",
               "// Generated by tools/lift_patterns.py from the arcade program: every callee and argument below is",
               "// what the arcade code passes. The PS2 value is noted where they differ.",
               f'#include "sf33rd/{hdr}"', '#include "common.h"', '#include "sf33rd/Source/Game/Com_Sub.h"',
               '#include "sf33rd/Source/Game/workuser.h"', ""]
        for addr, name, lifted, notes in sorted(funcs):
            out.append(f"// 0x{addr:08X}"); out += [f"//   PS2 {n}" for n in notes]
            out += [f"void {name}(PLW* wk) {{", "    switch (CP_Index[wk->wu.id][0]) {"]
            for k, calls in lifted:
                out.append("    default:" if k == "default" else f"    case {k}:")
                out += [f"        {c}({', '.join(show(v, t) for v, t in zip(vals, ty))});" for c, vals, ty in calls]
                out += ["        break;", ""]
            out[-1] = "    }"; out += ["}", ""]; nfun += 1
        open(os.path.join(a.emit, base), "w").write("\n".join(out))
    print(f"wrote {nfun} functions in {len(emit)} files to {a.emit}")
