#!/usr/bin/env python3
"""Print struct field offsets as GCC lays them out for SH-2 (same type sizes as the arcade build, so a good
first guess for arcade offsets). usage: structs.py <3s-decomp dir> <c file with the type> <Type> [more types]"""
import os, re, subprocess, sys, tempfile
from elftools.elf.elffile import ELFFile
ref, cfile, types = sys.argv[1], sys.argv[2], sys.argv[3:]
INC = [f"-I{ref}/{d}" for d in ("include", "src/anniversary", "include/sdk", "include/cri", "include/cri/ee", "zlib")]
src = open(cfile, encoding="utf-8", errors="replace").read() + "\n" + "\n".join(f"{t} __probe_{i};" for i, t in enumerate(types))
obj = tempfile.mktemp(suffix=".o")
subprocess.run(["sh-elf-gcc", "-m2", "-mb", "-g", "-w", "-nostdlib", "-Wl,--unresolved-symbols=ignore-all", "-Wl,-e,0", "-DTARGET_PS2", "-DM2CTX", "-D__int128=long long", "-x", "c", "-", "-o", obj] + INC,
               input=re.sub(r"#if defined\(TARGET_PS2\)\n(\s*[\w\s\*]+\([^;{}]*\);\n)+\s*#endif", "", src), text=True, check=True)
dw = ELFFile(open(obj, "rb")).get_dwarf_info()
def attr(d, n): return d.attributes[n].value if n in d.attributes else None
def ref_die(d, n="DW_AT_type"): return d.get_DIE_from_attribute(n) if n in d.attributes else None
def tname(d):
    if d is None: return "void"
    if d.tag == "DW_TAG_pointer_type": return tname(ref_die(d)) + "*"
    if d.tag == "DW_TAG_array_type":
        dims = "".join(f"[{attr(c, 'DW_AT_upper_bound') + 1}]" for c in d.iter_children() if attr(c, "DW_AT_upper_bound") is not None)
        return tname(ref_die(d)) + dims
    if d.tag in ("DW_TAG_const_type", "DW_TAG_volatile_type"): return tname(ref_die(d))
    n = attr(d, "DW_AT_name"); return n.decode() if n else d.tag[7:]
def strip(d):
    while d is not None and d.tag in ("DW_TAG_typedef", "DW_TAG_const_type", "DW_TAG_volatile_type"): d = ref_die(d)
    return d
def dump(d, base, prefix, depth=0):
    d = strip(d)
    if d is None or d.tag not in ("DW_TAG_structure_type", "DW_TAG_union_type"): return
    for m in d.iter_children():
        if m.tag != "DW_TAG_member": continue
        off = base + (attr(m, "DW_AT_data_member_location") or 0); t = ref_die(m); nm = (attr(m, "DW_AT_name") or b"?").decode()
        print(f"  0x{off:03X} {off:5d}  {prefix}{nm}: {tname(t)}")
        inner = strip(t)
        if inner is not None and inner.tag in ("DW_TAG_structure_type", "DW_TAG_union_type") and depth < 3: dump(inner, off, prefix + nm + ".", depth + 1)
for cu in dw.iter_CUs():
    for die in cu.get_top_DIE().iter_children():
        if die.tag == "DW_TAG_variable" and (attr(die, "DW_AT_name") or b"").startswith(b"__probe_"):
            t = ref_die(die); print(f"{tname(t)} (size {attr(strip(t), 'DW_AT_byte_size')})"); dump(t, 0, "")
os.unlink(obj)
