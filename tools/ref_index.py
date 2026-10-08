#!/usr/bin/env python3
"""Index the SH-2 reference objects built by build_ref_sh2.py.
usage: ref_index.py <obj dir> <out.json>
Per function: nums (immediates, literal constants, struct displacements), calls in address order, data symbols used."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elftools.elf.elffile import ELFFile
from sh2 import Image, s12
recs = []
for fn in sorted(os.listdir(sys.argv[1])):
    if not fn.endswith(".o"): continue
    elf = ELFFile(open(os.path.join(sys.argv[1], fn), "rb")); text = elf.get_section_by_name(".text")
    if text is None or not text.data_size: continue
    data = text.data() + b"\x00" * 8; tidx = elf.get_section_index(".text"); symtab = elf.get_section_by_name(".symtab")
    funcs = {}; byaddr = {}
    for sym in symtab.iter_symbols():
        if sym["st_info"]["type"] == "STT_FUNC" and sym["st_shndx"] == tidx:
            funcs[sym.name.lstrip("_")] = sym["st_value"]; byaddr[sym["st_value"]] = sym.name.lstrip("_")
    rel = {}
    rs = elf.get_section_by_name(".rela.text")
    if rs is not None:
        for r in rs.iter_relocations():
            sym = symtab.get_symbol(r["r_info_sym"])
            name = sym.name.lstrip("_") or elf.get_section(sym["st_shndx"]).name if sym["st_shndx"] != "SHN_UNDEF" or sym.name else "?"
            rel[r["r_offset"]] = (name, r["r_addend"], sym["st_shndx"] == tidx)
    img = Image(data, 0, 0, len(data) - 8)
    img.funcs = {a: None for a in funcs.values()}          # so bra to another function counts as a tail call
    for name, addr in funcs.items():
        f = img.analyze(addr)
        calls = []; datas = []
        def target(la):
            if la in rel:
                nm, add, intext = rel[la]
                return byaddr.get(add, nm) if intext and nm == ".text" else nm
            return None
        for pc in sorted(f.insns):
            w = img.u16(pc)
            if w >> 12 == 0xB or (w >> 12 == 0xA and pc + 4 + s12(w & 0xFFF) * 2 in byaddr and pc + 4 + s12(w & 0xFFF) * 2 != addr):
                calls.append(byaddr.get(pc + 4 + s12(w & 0xFFF) * 2, "?"))
            elif w & 0xF0FF in (0x400B, 0x402B):
                reg = (w >> 8) & 0xF; a = pc - 2; t = None; depth = 40
                while a >= addr and depth:
                    if a in f.insns:
                        v = img.u16(a)
                        if v >> 12 == 0xD and (v >> 8) & 0xF == reg: t = target((a & ~3) + 4 + (v & 0xFF) * 4); break
                        depth -= 1
                    a -= 2
                calls.append(t)
        for la, sz in f.lits.items():
            if sz == 4 and la in rel:
                nm, add, intext = rel[la]
                if not intext and not nm.startswith("."): datas.append(nm)
        recs.append(dict(name=name, obj=fn, size=f.end - addr, nums=img.nums(f, lambda la, v: la in rel),
                         calls=calls, data=sorted(set(datas))))
json.dump(recs, open(sys.argv[2], "w"))
print(f"{len(recs)} reference functions; {sum(1 for r in recs if None in r['calls'])} with unresolved calls")
