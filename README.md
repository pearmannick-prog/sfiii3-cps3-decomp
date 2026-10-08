# sfiii3-cps3-decomp

Work-in-progress decompilation of the CPS-3 arcade program of Street Fighter III: 3rd Strike,
revision 990512 (MAME `sfiii3r1` / `sfiii3nr1`).

This repository contains tooling and notes only. It contains no ROM data and no disassembly;
you must supply your own dump, and everything under `rom/` and `build/` is regenerated from it.

## Status
- 10,442 functions found in the 990512 program (98.8% of the code range)
- 7,091 matched to named functions from the PS2 decompilation (`symbols/sfiii3r1.csv`):
  4,480 exact (every call argument verified), 4 hand-verified, 1,871 high confidence, 687 medium, 49 low
- 247 global variables named (`symbols/sfiii3r1_data.csv`)
- CPU-AI pattern routines (`symbols/sfiii3r1_ai_routines.csv`): 5,167 of 5,204 lifted exactly from the arcade code;
  3,187 identical to PS2, 1,974 differ only by the button-mask layout, 6 really differ
- arcade C: 1,979 generated functions in `src/arcade/generated/`, 2 written by hand in `src/arcade/hand/`
- other matched functions, compared by calls and constants (`symbols/sfiii3r1_status.csv`):
  241 flagged as differing, 757 not yet decidable. A flag means "read this": the ones read so far were a mix
  of wrong names and real differences.

## Layout
This repo is an overlay on crowded-street/3s-decomp rather than a copy of it. A function whose arcade
code agrees with the PS2 C is taken from 3s-decomp unchanged; only functions that differ in the arcade
build (or exist only there) get C in `src/arcade/`, under the same name (`generated/` comes from
`tools/lift_patterns.py --emit`, `hand/` is written from reading the disassembly).
C in `src/arcade/` is derived from 3s-decomp and is therefore AGPL-3.0.

## Arcade differences found so far
- **Button-mask layout in CPU AI data.** The lever/button argument of the AI helpers (`Normal_Attack` arg 2,
  `Lever_Attack` arg 3, `Jump_Attack_Term` args 4 and 8, and similar) uses a different bit layout:
  PS2 value = arcade value with bits 7-14 moved up one (arcade 0x80/0x100/0x200 = PS2 0x100/0x200/0x400).
  1,974 routines differ only by this. Player command checks (`check_7` in CMD_MAIN.c) use the same masks in both builds.
- **Six AI routines with different logic or values**: `Pattern09_0078` (cases 1 and 2 swapped: `Pierce_On` then
  `SA_Term`), `Passive05_0007` and `Pattern05_0002` (power level 8 instead of 9), `Passive11_0237`
  (`Com_Random_Select` argument 6 instead of 5), `Passive00_0062` (one case fewer), `Pattern18_0019`
  (medium-confidence match, may be a mismatch).
- An earlier version of this file claimed 48 routines of `pass16.c` differed and that `active10.c` had changed.
  Both were matching errors (two tables swapped), fixed by placing tables on exact content.
- **Jump input in the standing state** (read by hand): the arcade `check_jump_ready` has no `spmv_ng_flag` tests
  (PS2 tests bits 0x20000 and 0x10000 there), and the standing-state routines call an extra function at
  0x0611CE6C that PS2 does not have: it tests `spmv_ng_flag & 0x10000` and `cp->waza_flag[13]` and enters
  routine 19. PS2 never reads `waza_flag[13]`. Not yet traced further.
- **Struct layout**: `PLW`/`WORK` fields sit at different offsets in the arcade build (for example `cp` is at
  0x3B8 in arcade and 0x388 when the PS2 headers are compiled for SH-2), and `CP_Index` is 16-bit there
  where the PS2 headers make it 8-bit. `WORK_CP` matches.
- Effect routines in the arcade build call `all_cgps_put_back` before `push_effect_work` in many places where
  PS2 does not, and call `char_move` without the PS2 `!EXE_flag && !Game_pause` guard (seen in `eff35_0004`).
These come from static analysis of the program; none are confirmed by running the game.

## Requirements
Python 3 with `numpy`, `capstone` (5.x, for SH-2 support), `tree-sitter`, `tree-sitter-c` and `pyelftools`;
`sh-elf-gcc` for the reading aids.

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
7. `python3 tools/lift_patterns.py build/sfiii3r1.bin <3s-decomp> symbols/sfiii3r1.csv symbols/sfiii3r1_data.csv report.csv`
   lifts the AI pattern routines exactly; with `--split/--ps2/--content` it writes feedback that `match.py --content`
   uses (run match -> globals -> lift a few times until stable); with `--emit src/arcade/generated` it generates arcade C
   Hand-verified names go in `symbols/overrides.csv` and are passed with `match.py --overrides`.
8. `python3 tools/compare.py build/ps2_index.json build/split symbols/sfiii3r1.csv symbols/sfiii3r1_status.csv`
   classifies each matched function as same / reordered / remapped / differs / unknown

## Reading aids
- `tools/build_ref_sh2.py <3s-decomp> build/obj` compiles the PS2 C for SH-2 with GCC (493 of 507 game files build).
  It is a reference to read against, not a matching build. `tools/ref_index.py` indexes it (experimental).
- `tools/structs.py <3s-decomp> <file.c> <Type>` prints field offsets under that build.

## How matching works
The PS2 port was built from the arcade source, so most functions exist in both.
- **tables**: the game dispatches through large function-pointer tables. Each PS2 table is placed onto
  the arcade pointer run whose entries have the same shape (call count, size) and repeat pattern.
- **calls**: for a matched pair, the two call sequences are aligned and unmatched callees paired up.
- **order / order-align**: functions keep their source order within a file, so gaps between matched
  neighbours are filled, with an alignment that tolerates functions present on one side only.

- **repair**: tables are first placed by shape alone; once callees are named each placement is re-tested
  on content and moved or dropped if it fails.

- **content**: AI pattern routines are lifted to (case, callee, arguments) and whole tables are placed where
  the lifted arcade routines equal the PS2 ones.

Grades in the CSV: `exact` = lifted arcade routine equals the PS2 routine argument for argument
(up to the button-mask layout); `high` = supported by uncommon shared constants or by callee agreement; `low` = some evidence contradicts the match; `medium` = everything else.
Checks so far, against an independent constant-only matcher: 49 of 49 `exact` and 57 of 62 `high` matches agree. Treat `medium`
and `low` rows as candidates, not facts.

Function names come from crowded-street/3s-decomp (AGPL-3.0).

## Findings so far (990512)
- SH-2 big-endian, reset PC 0x06000EA0, SP 0x02008F94, work RAM at 0x02000000
- code 0x06000400..~0x0613BDFA, data after; SIMM2 (0x06800000+) is data and identical to 990608
- 10,442 functions found, 98.8% of the code range covered
- code style suggests Hitachi SHC (shared literal pools, `jmp @rN` tail calls with filled delay slots); unconfirmed

## Known gaps
- ~3,400 arcade functions unnamed; ~2,900 PS2 names unplaced (some are PS2-only: SDK, CRI, renderer)
- ~420 overlapping functions (multiple entry points or false-positive code pointers)
- ~155 functions with unresolved jump tables; 135 small unclassified regions
