# sfiii3-cps3-decomp

Work-in-progress decompilation of the CPS-3 arcade program of Street Fighter III: 3rd Strike,
revision 990512 (MAME `sfiii3r1` / `sfiii3nr1`).

This repository contains tooling and notes only. It contains no ROM data and no disassembly;
you must supply your own dump, and everything under `rom/` and `build/` is regenerated from it.

## Status
- 10,442 functions found in the 990512 program (98.8% of the code range)
- 6,786 matched to named functions from the PS2 decompilation (`symbols/sfiii3r1.csv`):
  5,849 high confidence, 879 medium, 58 low
- 220 global variables named (`symbols/sfiii3r1_data.csv`)
- per-function comparison against the PS2 C (`symbols/sfiii3r1_status.csv`):
  5,727 carry over (same calls and constants, allowing block reordering and the button-mask remap),
  361 differ, 698 not yet decidable
- 7 arcade-specific functions written in `src/arcade/`

## Layout
This repo is an overlay on crowded-street/3s-decomp rather than a copy of it. A function whose arcade
code agrees with the PS2 C is taken from 3s-decomp unchanged; only functions that differ in the arcade
build (or exist only there) get C in `src/arcade/`, under the same name.
C in `src/arcade/` is derived from 3s-decomp and is therefore AGPL-3.0.

## Arcade differences found so far
- **Button-mask remap in CPU AI code**: constants passed as lever/button data by the CPU-opponent
  routines use a different bit layout. PS2 value = arcade value with bits >= 0x80 moved up one
  (arcade 0x80/0x100/0x200 = PS2 0x100/0x200/0x400). About 700 functions differ only by this.
  Player command checks (`check_7` in CMD_MAIN.c) use the same masks in both builds.
- **`pass16.c`** (one character's CPU AI): 48 of 167 routines are different in the arcade build.
- **`active10.c`**: its 70-entry routine table could not be placed at all; probably also changed.
These come from automated comparison plus a few functions read by hand; none are confirmed by running the game.

## Requirements
Python 3 with `numpy`, `capstone` (5.x, for SH-2 support), `tree-sitter` and `tree-sitter-c`.

## Pipeline
1. Put `sfiii3-simm1.0-3` and `sfiii3-simm2.0-3` in `rom/sfiii3r1/`
2. `python3 tools/decrypt.py rom/sfiii3r1 build/sfiii3r1.bin`
   joins SIMM1+SIMM2 and decrypts to a 16 MB big-endian image mapped at 0x06000000
3. `python3 tools/split.py build/sfiii3r1.bin build/split --code-hi 0613BDFA`
   function discovery; writes `functions.csv`, `functions.json`, `unknown_regions.csv`, `asm/func_XXXXXXXX.s`
4. `python3 tools/ps2_index.py <3s-decomp checkout> build/ps2_index.json src/arcade`
   indexes the PS2 decompilation: per-function constants and calls, plus function-pointer tables
5. `python3 tools/match.py build/ps2_index.json build/split symbols/sfiii3r1.csv`
   names arcade functions (see below)
6. `python3 tools/globals.py build/ps2_index.json build/split symbols/sfiii3r1.csv symbols/sfiii3r1_data.csv`
   names RAM addresses
7. `python3 tools/compare.py build/ps2_index.json build/split symbols/sfiii3r1.csv symbols/sfiii3r1_status.csv`
   classifies each matched function as same / reordered / remapped / differs / unknown

## How matching works
The PS2 port was built from the arcade source, so most functions exist in both.
- **tables**: the game dispatches through large function-pointer tables. Each PS2 table is placed onto
  the arcade pointer run whose entries have the same shape (call count, size) and repeat pattern.
- **calls**: for a matched pair, the two call sequences are aligned and unmatched callees paired up.
- **order / order-align**: functions keep their source order within a file, so gaps between matched
  neighbours are filled, with an alignment that tolerates functions present on one side only.

- **repair**: tables are first placed by shape alone; once callees are named each placement is re-tested
  on content and moved or dropped if it fails.

Grades in the CSV: `high` = supported by uncommon shared constants or by callee agreement; `low` = some evidence contradicts the match; `medium` = everything else.
Checks so far: about 95% of high-grade matches agree with an independent constant-only matcher, and
about 98% of matched callers with equal call counts have fully consistent callees. Treat `medium`
and `low` rows as candidates, not facts.

Function names come from crowded-street/3s-decomp (AGPL-3.0).

## Findings so far (990512)
- SH-2 big-endian, reset PC 0x06000EA0, SP 0x02008F94, work RAM at 0x02000000
- code 0x06000400..~0x0613BDFA, data after; SIMM2 (0x06800000+) is data and identical to 990608
- 10,442 functions found, 98.8% of the code range covered
- code style suggests Hitachi SHC (shared literal pools, `jmp @rN` tail calls with filled delay slots); unconfirmed

## Known gaps
- ~3,600 arcade functions unnamed; ~3,100 PS2 names unplaced (some are PS2-only: SDK, CRI, renderer)
- ~420 overlapping functions (multiple entry points or false-positive code pointers)
- ~155 functions with unresolved jump tables; 135 small unclassified regions
