#!/usr/bin/env python3
"""Compile the PS2 decompilation's C for SH-2 with GCC, as a reference fingerprint (not a matching build).
usage: build_ref_sh2.py <3s-decomp dir> <out obj dir> [overlay dir]
Block-scope prototypes that 3s-decomp wraps in `#if defined(TARGET_PS2)` are stripped: they only exist to
match the PS2 compiler and conflict with the real headers under GCC."""
import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ref, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
FLAGS = ["sh-elf-gcc", "-m2", "-mb", "-O2", "-c", "-w", "-fno-builtin", "-fno-inline", "-fno-optimize-sibling-calls", "-fno-jump-tables",
         "-DTARGET_PS2", "-DM2CTX", "-D__int128=long long", "-x", "c", "-"]
INC = [f"-I{ref}/{d}" for d in ("include", "src/anniversary", "include/sdk", "include/cri", "include/cri/ee", "zlib")]
PROTO = re.compile(r"^\s*[\w\s\*]+\([^;{}]*\);\s*$")
def strip(text):
    lines = text.split("\n"); res = []; i = 0
    while i < len(lines):
        if lines[i].strip() == "#if defined(TARGET_PS2)":
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("#"): j += 1
            inner = [l for l in lines[i + 1:j] if l.strip()]
            if j < len(lines) and lines[j].strip() == "#endif" and inner and all(PROTO.match(l) for l in inner):
                res += [""] * (j - i + 1); i = j + 1; continue
        res.append(lines[i]); i += 1
    return "\n".join(res)
def build(path):
    obj = os.path.join(out, os.path.basename(path)[:-2] + ".o")
    p = subprocess.run(FLAGS + INC + ["-o", obj], input=strip(open(path, encoding="utf-8", errors="replace").read()),
                       capture_output=True, text=True)
    return path, p.returncode, p.stderr
files = []
for root, _, fs in os.walk(os.path.join(ref, "src/anniversary/sf33rd/Source/Game")):
    files += [os.path.join(root, f) for f in fs if f.endswith(".c")]
fails = 0
with ThreadPoolExecutor(4) as ex:
    for path, rc, err in ex.map(build, sorted(files)):
        if rc:
            fails += 1; first = next((l for l in err.split("\n") if "error" in l), "")
            print("FAIL", os.path.basename(path), first[:150])
print(f"compiled {len(files) - fails} of {len(files)} files")
