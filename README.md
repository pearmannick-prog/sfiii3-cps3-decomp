# sfiii3-cps3-decomp

Work-in-progress decompilation of the CPS-3 arcade program of Street Fighter III: 3rd Strike,
revision 990512 (MAME `sfiii3r1` / `sfiii3nr1`).

This repository contains tooling and notes only. It contains no ROM data and no disassembly;
you must supply your own dump, and everything under `rom/` and `build/` is regenerated from it.

## Status
- 10,442 functions found in the 990512 program (98.8% of the code range)
- about 7,520 matched to named functions from the PS2 decompilation (`symbols/sfiii3r1.csv`):
  4,480 `exact` (every call argument verified), about 1,680 `events` (same calls, field writes and bit tests as the
  PS2 C compiled for SH-2), 21 `manual` (read by hand), about 850 high, 420 medium, 70 low
- 299 global variables named (`symbols/sfiii3r1_data.csv`); these come from co-occurrence and at least one is
  known to be wrong, so treat them as hints
- CPU-AI pattern routines (`symbols/sfiii3r1_ai_routines.csv`): 5,167 of 5,204 lifted exactly;
  3,187 identical to PS2, 1,974 differ only by the button-mask layout, 6 really differ
- arcade C: 1,978 generated functions in `src/arcade/generated/`, 14 written by hand in `src/arcade/hand/`
- **flagged-function review** (`symbols/sfiii3r1_flagged_review.csv`): every function the comparison flagged
  (402) has a verdict and the evidence it rests on:
  about 30 read line by line;
  103 probably carry the wrong name; 53 differ only by an extra arcade `all_cgps_put_back` call;
  46 are the same once compiler noise is removed; 10 could not be compared (their PS2 file does not build for SH-2);
  170 differ on events but have not been read line by line (37 gameplay, 133 effects/opening/ending/menu code)

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
- **Parry and guard decision** (read by hand, `src/arcade/hand/HITCHECK.c`):
  - `defense_ground`: the arcade build has no auto-parry/auto-guard option flags and no `dead_flag` test; the
    just-guarded thresholds are indexed by attack type only (PS2 also by player); a high parry of a jump attack
    needs `waza_flag[12]` only; guarding always tests the lever unless `auto_guard` is set, where PS2 skips
    that test while `just_now`.
  - `defense_sky`: the arcade build has two air parries (`waza_flag[5]` -> routine 34, `waza_flag[6]` ->
    routine 35); PS2 has one plus a just-guarded path.
  - `check_dm_att_guard` takes two parameters: chip damage is `dm_vital / kezuri_pow`. PS2 adds a third
    (`kom`, 1 on the ground and 2 in the air) and divides by `kezuri_pow / kom`.
  - `blocking_point_count_up` always calls `grade_add_blocking`; PS2 does so only with an option flag set.
- **Parry start** (`Normal_31000`, read by hand): PS2 makes `dm_stop` negative and calls `subtract_dm_vital`
  when a ground parry begins; the arcade build does neither.
- **Extra walk-like states** (read by hand): two more arcade-only functions (0x0611CFDE, 0x0611D150) enter and
  leave player routines 11 and 12 from the lever, gated by `spmv_ng_flag` bits 1 and 2. PS2 keeps table slots
  for routines 11, 12 and 19 but nothing in its source enters them.
- **`subtract_dm_vital`** (read by hand): same damage, death and stun logic; PS2 adds training-mode and
  rumble hooks.
- **`Bonus_Game_Flag`** is compared with 21 in the arcade build wherever PS2 compares it with 20 (about 20
  functions): a renumbered constant, not a behaviour change.
- **More player-code differences read by hand** (details in `symbols/sfiii3r1_flagged_review.csv`):
  `check_cg_cancel_data` does not try `check_full_gauge_attack2` when cancelling and has none of the PS2
  option tests; `nm_38000` does not call `check_sankaku_tobi` or `check_air_jump`; `dm_04000` and the stun
  state `Damage_25000` do not call `setup_kuzureochi`; `Player_normal` does not call `clear_chainex_check`;
  the air-parry start `Normal_35000` matches `Normal_31000` (no `dm_stop` negation, no `subtract_dm_vital`);
  `Att_DENJINHADOUKEN` and `Att_PL08_HEALING` do not call `hoken_muriyari_chakuchi`.
- **Random numbers** (read by hand, `src/arcade/hand/PLS02.c`): the arcade build has four random functions
  (`random_32`, `random_16` and the two `_ex` ones) and none has the PS2 `Debug_w` reset. The PS2 `_com`
  variants, which give CPU-opponent code its own streams when `Play_Mode != 0`, do not exist: arcade
  CPU-opponent code calls `random_32` / `random_16` and shares the stream with everything else.
- **`spmv_ng_flag` is per character in the arcade build** (`set_base_data`, read by hand): it is loaded from a
  table indexed by `player_number` (data at 0x065EA5B0). PS2 loads it from `omop_spmv_ng_table[wk->wu.id]`,
  indexed by player side, and adds `spmv_ng_flag2`. This is why the PS2 "option" tests on that flag look
  different or are missing in arcade functions, and probably what the arcade-only routines 11, 12 and 19 are
  for (character-specific movement); that last part is a guess.
- **Time over** (`time_over_check`): the arcade build also calls `setup_gouki_wins`.
- `PLW` is 0x498 bytes in the arcade build (0x46C in the PS2 headers); `plw` is at 0x02068C6C.
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

## Event comparison
`tools/events.py` abstract-interprets SH-2 functions into events: calls (with constant arguments), field and
global writes, and bit tests. It runs on the arcade program and on the PS2 C compiled for SH-2, so two
compilers' output for the same C gives nearly the same event set. `tools/semdiff.py` learns how PS2-layout
field offsets and global symbols map to arcade ones (`symbols/sfiii3r1_fieldmap.csv`,
`symbols/sfiii3r1_globalmap.csv`), reports per-function differences (`symbols/sfiii3r1_events.csv`) and feeds
names back to the matcher. `tools/pipeline.sh <work dir> <3s-decomp dir>` runs everything in order.
Known noise: one compiler may store a known constant where the other computes it, and labels wrongly split off
as functions show up as calls.

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

Grades in the CSV: `manual` = read by hand; `events` = event sets agree (see Event comparison); `exact` = lifted arcade routine equals the PS2 routine argument for argument
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
