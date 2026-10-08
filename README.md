# sfiii3-cps3-decomp

Work-in-progress decompilation of the CPS-3 arcade program of Street Fighter III: 3rd Strike,
revision 990512 (MAME `sfiii3r1` / `sfiii3nr1`).

This repository contains tooling and notes only. It contains no ROM data and no disassembly;
you must supply your own dump, and everything under `rom/` and `build/` is regenerated from it.

## Requirements
Python 3 with `numpy` and `capstone` (5.x, for SH-2 support).

## Pipeline
1. Put `sfiii3-simm1.0-3` and `sfiii3-simm2.0-3` in `rom/sfiii3r1/`
2. `python3 tools/decrypt.py rom/sfiii3r1 build/sfiii3r1.bin`
   joins SIMM1+SIMM2 and decrypts to a 16 MB big-endian image mapped at 0x06000000
3. `python3 tools/split.py build/sfiii3r1.bin build/split --code-hi 0613BDFA`
   function discovery; writes `functions.csv`, `unknown_regions.csv`, `asm/func_XXXXXXXX.s`
4. (next) match functions against the PS2 decompilation (crowded-street/3s-decomp) to carry names over

## Findings so far (990512)
- SH-2 big-endian, reset PC 0x06000EA0, SP 0x02008F94, work RAM at 0x02000000
- code 0x06000400..~0x0613BDFA, data after; SIMM2 (0x06800000+) is data and identical to 990608
- 10,442 functions found, 98.8% of the code range covered
- code style suggests Hitachi SHC (shared literal pools, `jmp @rN` tail calls with filled delay slots); unconfirmed

## Known gaps
- ~420 overlapping functions (multiple entry points or false-positive code pointers)
- ~155 functions with unresolved jump tables; 135 small unclassified regions
